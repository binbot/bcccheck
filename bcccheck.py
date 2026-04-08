# bcccheck.py

import asyncio
import sys
import json
from pathlib import Path
from playwright.async_api import async_playwright

YUM_URL = "https://bandcamp.com/yum"
CODES_FILE = Path("codes.txt")
COOKIES_FILE = Path("cookies.json")

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

class BCChecker:
    def __init__(self, codes_file=CODES_FILE, cookies_file=COOKIES_FILE, headless=False):
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
                if await loc.count() > 0 and await loc.first().is_visible():
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

    async def check_code(self, page, code: str) -> bool:
        input_loc = await self.find_first_existing(page, SELECTORS["input_candidates"])
        if not input_loc:
            return False
        await input_loc.fill("")
        await input_loc.fill(code)

        # Pressing 'Enter' is much more robust against overlays (like cookie banners)
        # than clicking a button, because it doesn't check for pointer intersections.
        await input_loc.press("Enter")

        # Fallback: if 'Enter' didn't seem to trigger anything, try a forced click
        # (But usually Enter is enough)
        
        return await self.wait_for_success(page)

    async def run(self):
        self.load_codes()
        if not self.codes:
            await self._emit("No codes found in codes.txt.")
            return

        async with async_playwright() as pw:
            if hasattr(sys, '_MEIPASS'):
                pw.browsers_path = Path(sys._MEIPASS) / 'ms-playwright'
            
            # headless=False is needed for the bundled version as per original script
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context()

            if self.cookies_file.exists():
                cookies = json.loads(self.cookies_file.read_text())
                await context.add_cookies(cookies)

            page = await context.new_page()
            await page.goto(YUM_URL, wait_until="domcontentloaded")

            # Handle possible cookie banners or overlays
            try:
                # Look for common "Accept" or "Close" buttons for cookies
                cookie_selectors = [
                    'button:has-text("Accept")',
                    'button:has-text("Agree")',
                    '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
                    '.qc-cmp2-footer button'
                ]
                for sel in cookie_selectors:
                    loc = page.locator(sel)
                    if await loc.count() > 0 and await loc.first().is_visible():
                        await loc.first().click()
                        await page.wait_for_timeout(500)
                        break
            except:
                pass

            try:
                await page.wait_for_selector('input#code-input', timeout=10000)
            except Exception:
                await self._emit("Error: input field not found on Bandcamp.")
                await browser.close()
                return

            for code in self.codes:
                await self._emit(f"Checking {code}...", code=code, status="checking")
                await page.wait_for_timeout(250)

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
                        await page.wait_for_selector('input#code-input', timeout=5000)
                    except:
                        break

            await browser.close()
            if self.found_code:
                await self._emit(f"Finished. Redeemable code found: {self.found_code}")
            else:
                await self._emit("Finished. No redeemable codes found.")

if __name__ == "__main__":
    # If run directly, behave like the original script
    checker = BCChecker(headless=False)
    async def cli_update(msg, code=None, status=None):
        print(msg)
    checker.on_update = cli_update
    asyncio.run(checker.run())
