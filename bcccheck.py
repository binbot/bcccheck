# bcccheck.py

import asyncio
import os
import sys
import json
from pathlib import Path
from playwright.async_api import async_playwright

YUM_URL = "https://bandcamp.com/yum"
CODES_FILE = Path("codes.txt")
COOKIES_FILE = Path("cookies.json")

INTER_CODE_DELAY_MS = 100
COOKIE_DISMISS_WAIT_MS = 250

SELECTORS = {
    "input_candidates": [
        'input#code-input',
        'input[name="code"]',
    ],
    "submit_candidates": [
        'button.redeem-button[name="redeem"]',
        'button:has-text("Redeem")',
    ],
    "error_text_candidates": [
        "already been used",
        "invalid",
        "not a valid code",
        "try again",
        "error",
    ],
    "pagedata": '#pagedata',
}


def _playwright_cache_dir() -> Path:
    """Location Playwright uses for downloaded browsers."""
    env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if env and env != "0":
        return Path(env)
    return Path.home() / ".cache" / "ms-playwright"


def _browser_installed(prefix: str) -> bool:
    base = _playwright_cache_dir()
    if not base.is_dir():
        return False
    return any(p.name.startswith(prefix) for p in base.iterdir())


async def ensure_browser(on_status=None, needs_full=False):
    """Download the browser on first run so end users need zero setup.

    By default only chromium-headless-shell is fetched (~260 MB). When the
    visible browser is requested (--show-browser) the full chromium is also
    fetched. Browsers land in Playwright's default cache and are reused on
    every later run.
    """
    targets = ["chromium_headless_shell-"]
    if needs_full:
        targets.append("chromium-")
    if all(_browser_installed(t) for t in targets):
        return
    if on_status:
        await on_status("Downloading browser (one-time, ~260 MB)…")
    try:
        import runpy
        cmd = ["playwright", "install", "chromium-headless-shell"]
        if needs_full:
            cmd.append("chromium")
        saved_argv = sys.argv
        sys.argv = cmd
        try:
            # Run in a thread so the TUI stays responsive during the one-time download.
            await asyncio.to_thread(runpy.run_module, "playwright", "__main__")
        except SystemExit as e:
            if e.code not in (0, None):
                raise RuntimeError(f"playwright install exited with code {e.code}")
        finally:
            sys.argv = saved_argv
        if on_status:
            await on_status("Browser ready.")
    except Exception as e:
        if on_status:
            await on_status(f"Browser download error: {e}")


class BCChecker:
    def __init__(self, codes_file=CODES_FILE, cookies_file=COOKIES_FILE, headless=True):
        self.codes_file = codes_file
        self.cookies_file = cookies_file
        self.headless = headless
        self.codes = []
        self.found_code = None
        self.on_update = None # Callback function for TUI or CLI to receive updates

    def load_codes(self):
        """Read codes from codes.txt"""
        if not self.codes_file.exists():
            return []
        self.codes = [line.strip() for line in self.codes_file.read_text().splitlines() if line.strip()]
        return self.codes

    async def _emit(self, msg, code=None, status=None):
        """Send an update message to the UI callback"""
        if self.on_update:
            await self.on_update(msg, code, status)

    def url_looks_like_download(self, url: str) -> bool:
        return url.startswith("https://bandcamp.com/download?from=code")

    async def find_first_existing(self, page, selectors):
        for sel in selectors:
            locator = page.locator(sel)
            if await locator.count() > 0:
                return locator
        return None

    async def any_error_visible(self, page) -> bool:
        try:
            full_text_lower = (await page.inner_text("body")).lower()
        except:
            return False
        for phrase in SELECTORS["error_text_candidates"]:
            if phrase in full_text_lower:
                return True
        possible_error_selectors = ['.error', '[role="alert"]', '.invalid', '.error-message']
        for sel in possible_error_selectors:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0 and await loc.first.is_visible():
                    return True
            except:
                pass
        return False

    async def wait_for_success(self, page) -> bool:
        try:
            await page.wait_for_url(lambda url: self.url_looks_like_download(url), timeout=3000)
            return True
        except:
            pass

        try:
            pd = page.locator(SELECTORS["pagedata"])
            if await pd.count() > 0:
                blob_attr = await pd.get_attribute("data-blob")
                if blob_attr and "payment_type" in blob_attr and '"payment_type":"code"' in blob_attr:
                    return True
        except:
            pass

        if await self.any_error_visible(page):
            return False

        await page.wait_for_timeout(500)
        return False

    async def dismiss_cookie_banner(self, page) -> bool:
        """Dismiss a cookie-consent popover if present.

        Prefers rejecting/denying consent (privacy-friendly) and falls back
        to accepting. Clicks programmatically, so it works headless too.
        Returns True if a button was clicked.
        """
        deny_selectors = [
            'button:has-text("Reject")',
            'button:has-text("Deny")',
            'button:has-text("Decline")',
            'button:has-text("Necessary only")',
            '#CybotCookiebotDialogBodyButtonDecline',
            '#CybotCookiebotDialogBodyLevelButtonLevelOptinDecline',
            '.qc-cmp2-footer button:has-text("Reject")',
        ]
        accept_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Agree")',
            'button:has-text("Allow")',
            '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
            '.qc-cmp2-footer button',
        ]
        for sel in deny_selectors + accept_selectors:
            try:
                loc = page.locator(sel)
                if await loc.count() > 0 and await loc.first.is_visible():
                    await loc.first.click()
                    await page.wait_for_timeout(COOKIE_DISMISS_WAIT_MS)
                    await self._emit(f"Dismissed cookie banner ({sel}).")
                    return True
            except Exception as e:
                await self._emit(f"Cookie dismiss selector failed ({sel}): {e}")
        return False

    async def check_code(self, page, code: str) -> bool:
        input_loc = await self.find_first_existing(page, SELECTORS["input_candidates"])
        if not input_loc:
            return False
        await self.dismiss_cookie_banner(page)
        await input_loc.fill(code)

        # Pressing 'Enter' is much more robust against overlays (like cookie banners)
        # than clicking a button, because it doesn't check for pointer intersections.
        await input_loc.press("Enter")

        return await self.wait_for_success(page)

    async def run(self):
        self.load_codes()
        if not self.codes:
            await self._emit("No codes found in codes.txt.")
            return

        await ensure_browser(self._emit, needs_full=not self.headless)

        async with async_playwright() as pw:
            if hasattr(sys, '_MEIPASS'):
                bundled = Path(sys._MEIPASS) / 'ms-playwright'
                if bundled.exists():
                    pw.browsers_path = bundled
            
            # Headless by default (TUI-only); --show-browser forces a visible browser for debugging.
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context()

            if self.cookies_file.exists():
                cookies = json.loads(self.cookies_file.read_text())
                await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(YUM_URL, wait_until="domcontentloaded")

            # Handle possible cookie banners or overlays
            await self.dismiss_cookie_banner(page)

            try:
                await page.wait_for_selector('input#code-input', timeout=10000)
            except Exception:
                await self._emit("Error: input field not found on Bandcamp.")
                await browser.close()
                return

            for code in self.codes:
                await self._emit(f"Checking {code}...", code=code, status="checking")
                await page.wait_for_timeout(INTER_CODE_DELAY_MS)

                try:
                    if await self.check_code(page, code):
                        self.found_code = code
                        await self._emit(f"SUCCESS: {code}", code=code, status="success")
                        break
                    else:
                        await self._emit(f"Invalid: {code}", code=code, status="failed")
                except Exception as e:
                    await self._emit(f"Error checking {code}: {e}", code=code, status="error")

                # Return to YUM page if navigated away
                if page.url != YUM_URL:
                    try:
                        await page.goto(YUM_URL, wait_until="domcontentloaded")
                        await self.dismiss_cookie_banner(page)
                        await page.wait_for_selector('input#code-input', timeout=5000)
                    except Exception as e:
                        await self._emit(f"Error returning to YUM page: {e}")
                        break

            await browser.close()
            if self.found_code:
                await self._emit(f"Finished. Redeemable code found: {self.found_code}")
            else:
                await self._emit("Finished. No redeemable codes found.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="bcccheck CLI")
    parser.add_argument("--show-browser", action="store_true",
                        help="Show the browser window (default is headless/TUI-only)")
    args = parser.parse_args()
    # If run directly, behave like the original script
    checker = BCChecker(headless=not args.show_browser)
    async def cli_update(msg, code=None, status=None):
        print(msg)
    checker.on_update = cli_update
    asyncio.run(checker.run())
