# bc.py

import asyncio
import sys
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
    # We no longer rely on UI checkmarks; we use navigation + pagedata
    "error_text_candidates": [
        "already been used",
        "invalid",
        "not a valid code",
        "try again",
        "error",
    ],
    "pagedata": '#pagedata',  # the div carrying data-blob with redemption payload on success
}

def url_looks_like_download(url: str) -> bool:
    # Treat any download page reached via code redemption as success
    # e.g. https://bandcamp.com/download?from=code&...
    return url.startswith("https://bandcamp.com/download?from=code")

async def find_first_existing(page, selectors):
    for sel in selectors:
        locator = page.locator(sel)
        if await locator.count() > 0:
            return locator
    return None

async def any_error_visible(page) -> bool:
    # Fall back text scan for error banners/messages on the YUM page
    try:
        full_text_lower = (await page.inner_text("body")).lower()
    except:
        return False
    for phrase in SELECTORS["error_text_candidates"]:
        if phrase in full_text_lower:
            return True
    # Common error roles/classes
    possible_error_selectors = [
        '.error',
        '[role="alert"]',
        '.invalid',
        '.error-message'
    ]
    for sel in possible_error_selectors:
        try:
            loc = page.locator(sel)
            if await loc.count() > 0 and await loc.first().is_visible():
                return True
        except:
            pass
    return False

async def wait_for_success(page) -> bool:
    """
    After submitting a code, wait briefly for either:
    - navigation to the download URL (most reliable)
    - or presence of #pagedata with a data-blob containing payment_type:"code"
    Return True if success detected.
    """
    # 1) Try waiting for navigation to download page
    try:
        # Wait for a URL change that looks like the download page
        await page.wait_for_url(lambda url: url_looks_like_download(url), timeout=3000)
        return True
    except:
        pass

    # 2) Inspect #pagedata data-blob for payment_type:"code"
    try:
        pd = page.locator(SELECTORS["pagedata"])
        if await pd.count() > 0:
            blob_attr = await pd.get_attribute("data-blob")
            if blob_attr and "payment_type" in blob_attr and '"payment_type":"code"' in blob_attr:
                return True
    except:
        pass

    # 3) If neither success signal, check for error
    if await any_error_visible(page):
        return False

    # 4) Final short wait; if nothing appears, treat as failure
    await page.wait_for_timeout(500)
    return False

async def check_code(page, code: str) -> bool:
    # Fill input
    input_loc = await find_first_existing(page, SELECTORS["input_candidates"])
    if not input_loc:
        # If input isn't present, consider failure for this iteration
        return False
    await input_loc.fill("")
    await input_loc.fill(code)

    # Submit
    submit_loc = await find_first_existing(page, SELECTORS["submit_candidates"])
    if submit_loc:
        await submit_loc.click()
    else:
        # Fallback: Enter
        await input_loc.press("Enter")

    # Wait for success or error
    return await wait_for_success(page)

async def run():
    if not CODES_FILE.exists():
        print(f"codes.txt not found at {CODES_FILE.resolve()}")
        return

    codes = [line.strip() for line in CODES_FILE.read_text().splitlines() if line.strip()]
    if not codes:
        print("codes.txt is empty.")
        return

    async with async_playwright() as pw:
        # Set browsers path for bundled version
        if hasattr(sys, '_MEIPASS'):
            pw.browsers_path = Path(sys._MEIPASS) / 'ms-playwright'
        # Use headless=False for both packaged and development versions
        # (headless_shell binary is not included in the bundle)
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()

        # Load cookies if available (must be valid, logged-in session)
        if COOKIES_FILE.exists():
            import json
            cookies = json.loads(COOKIES_FILE.read_text())
            await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto(YUM_URL, wait_until="domcontentloaded")

        # Ensure the input field is present once before processing
        try:
            await page.wait_for_selector('input#code-input', timeout=10000)
        except Exception:
            print("Error: code input field not found on the YUM page after loading.")
            await browser.close()
            return

        found_code = None

        for code in codes:
            # small polite delay
            await page.wait_for_timeout(250)

            try:
                if await check_code(page, code):
                    found_code = code
                    break
            except Exception as e:
                # Log and continue to next code
                print(f"Error checking code {code}: {e}")

            # If we navigated away during a failed attempt, return to YUM
            # (Sometimes Bandcamp can redirect even on some failures; ensure we’re back)
            if page.url != YUM_URL:
                try:
                    await page.goto(YUM_URL, wait_until="domcontentloaded")
                    await page.wait_for_selector('input#code-input', timeout=5000)
                except:
                    # If we can’t get back, abort loop
                    break

        # Close browser before printing final result
        await browser.close()

        if found_code:
            print(f"Found redeemable code: {found_code}")
        else:
            print("No redeemable code found in the list.")

if __name__ == "__main__":
    asyncio.run(run())

