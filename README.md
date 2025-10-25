# bcccheck

A small, practical, open-source helper that automates checking Bandcamp YUM codes like a careful, efficient human.

bcccheck opens bandcamp.com/yum in a real browser session, enters codes from a list one at a time, and stops at the first redeemable code it finds. It’s intentionally paced with short delays to mimic human interaction, reducing the chance of rate-limits or anti-bot friction. There’s nothing nefarious here—just removing the repetitive hassle of trying codes manually.

> Example: You have a list of codes from a release. bcccheck loads the YUM page, types each code, and when one is redeemable, prints it and stops.

---

## Features

- Automates Bandcamp YUM code entry in a real browser
- Stops at the first redeemable code and prints it
- Uses robust signals (redirect to Bandcamp download, or redemption payload on the page)
- Human-like pacing (short delays, sequential attempts)
- Works with your authenticated session (cookies) so the site behaves just like when you’re logged in
- Simple setup and run

---

## Requirements

- Python 3.9+ (tested on modern Python)
- Playwright (Python bindings)
- Playwright browser binaries (installed via `playwright install`)
- A codes list file: `codes.txt` (one code per line)
- Your Bandcamp cookies (JSON) saved as `cookies.json` for an authenticated session

---

## Installation (Development)

1. Clone the repo
    ```sh
    git clone https://github.com/your-user/bcccheck.git
    cd bcccheck
    ```

2. Create and activate a virtual environment (recommended)
    ```sh
    python -m venv .venv
    source .venv/bin/activate   # macOS/Linux
    # .venv\Scripts\Activate    # Windows (PowerShell)
    ```

3. Install dependencies
    ```sh
    pip install playwright
    ```

4. Install Playwright browsers
    ```sh
    playwright install
    # Optional: if you want Firefox/WebKit too:
    playwright install firefox
    playwright install webkit
    ```

---

## Standalone Package (Easy Installation)

For users who want a simple download-and-run experience without installing Python or dependencies:

1. Download the latest release from the [Releases](https://github.com/your-user/bcccheck/releases) page
2. Download `bcccheck-v1.0.0-linux.zip` (or the appropriate version for your platform)
3. Unzip the file to a directory of your choice
4. Place your `codes.txt` and `cookies.json` files in the unzipped directory
5. Run the executable:
   - Linux/macOS: `./bcccheck`
   - Windows: `bcccheck.exe`

The package includes everything needed: Python runtime, Playwright, and Chromium browser.

---

## Preparing `codes.txt`

Create a `codes.txt` file in the project root with one Bandcamp YUM code per line. Example:

```
abcd-1234
efgh-5678
qdxa-ktw6
```

Codes are alphanumeric with a hyphen (usually 4-4 split). bcccheck will try them in order (top to bottom) unless you change the sorting mode.

---

## Authentication (`cookies.json`)

bcccheck needs to behave like an authenticated human. Export your Bandcamp cookies from your browser session and save them to `cookies.json` in the project root.

- Log in to Bandcamp in your browser
- Use a cookie export extension or DevTools to export cookies for the domain `.bandcamp.com`
- Ensure the cookie attributes are compatible with Playwright:
  - `sameSite` must be one of: `"Lax"`, `"Strict"`, `"None"` (capitalized)
  - `secure`, `httpOnly`, `domain`, `path`, `name`, `value` should be present
- Save the exported array to `cookies.json`

Example cookie object (for reference only; do not share your actual cookies publicly):
```json
[
  {
    "name": "identity",
    "value": "REDACTED",
    "domain": ".bandcamp.com",
    "path": "/",
    "expires": 1775495075,
    "httpOnly": true,
    "secure": true,
    "sameSite": "None"
  }
]
```

Security note:
- Do not commit `cookies.json` to version control.
- Treat your cookies like credentials. If cookies stop working, re-export a fresh set.

---

## Usage

### Development Version
Run the checker:

```sh
python bcccheck.py
```

### Standalone Package
After unzipping, run:

```sh
./bcccheck  # Linux/macOS
bcccheck.exe  # Windows
```

What it does:
- Launches a Playwright browser (Chromium by default)
- Loads your cookies to authenticate (if `cookies.json` exists)
- Opens https://bandcamp.com/yum
- Enters codes from `codes.txt` one by one, with small delays
- Stops on success and prints:
  ```
  Found redeemable code: qdxa-ktw6
  ```
- If none redeem, prints:
  ```
  No redeemable code found in the list.
  ```

Tip:
- For debugging, set the script to show the browser window (non-headless). By default this project uses `headless=False` while stabilizing; you can switch to `headless=True` once you’re confident.

---

## Sorting modes (planned updates)

Potential enhancements we can branch:
- Reverse order: attempt codes from bottom to top
- Random order: shuffle codes before attempting
- Custom strategies: prioritize codes based on metadata or heuristics

If you’d like these now, open an issue or PR:
- Reverse:
  - Read lines then reverse the list before iteration
- Random:
  - `import random; random.shuffle(codes)`

We’re happy to integrate clean options such as `--order=forward|reverse|random`.

---

## How it detects success

bcccheck avoids brittle UI signals and looks for robust indicators:
- Navigation to a Bandcamp download URL that starts with:
  ```
  https://bandcamp.com/download?from=code
  ```
- Presence of a `#pagedata` element whose `data-blob` contains `"payment_type":"code"`

If neither appears, it checks the page for common error messages (e.g., “invalid”, “already been used”) and proceeds to the next code.

---

## Notes, ethics, and intent

- This tool automates what a human would do: enter codes one by one on Bandcamp’s YUM page to find a redeemable one.
- It adds short delays and uses a real browser session to behave politely and reliably.
- It does not bypass authentication or probe private APIs; you must be logged in with your own cookies.
- Please use responsibly and in accordance with Bandcamp’s terms of use and local laws.

---

## Building the Standalone Package

To build the standalone executable for distribution:

1. Install PyInstaller: `pip install pyinstaller`
2. Install dependencies: `pip install -r requirements.txt`
3. Install browsers: `playwright install chromium`
4. Build: `pyinstaller bcccheck.spec`
5. The distributable zip will be in `dist/bcccheck-v1.0.0-linux.zip`

## Open Source

- License: MIT (permissive—use, modify, share freely)
- Contributions welcome: issues, PRs, ideas
- Happy to support and evolve bcccheck based on user feedback

Example areas for contribution:
- Sorting strategies and CLI flags
- Better success/failure selectors if the page changes
- Browser context persistence (e.g., using a saved Playwright storage state)
- Logging options and JSON output mode
- CI checks, linting, and packaging

---

## Troubleshooting

- “Error: code input field not found on the YUM page after loading.”:
  - Ensure `cookies.json` is valid and you’re logged in
  - Try `headless=False` to see the page
  - Check for modals or cookie banners and dismiss them if needed
- “No redeemable code found” but you expected one:
  - Ensure the code is present in `codes.txt` exactly as displayed
  - Try slower pacing (increase small delays)
  - Re-export new cookies and retry
- Playwright cookie errors (`sameSite`):
  - Normalize values to `"Strict"`, `"Lax"`, or `"None"` (capitalized)

---

## Project structure

- `bcccheck.py` — main script
- `codes.txt` — your list of codes (not committed)
- `cookies.json` — your Bandcamp cookies (not committed)
- `README.md` — this document

---

## Roadmap

- CLI options (`--order`, `--headless`, `--delay-ms`)
- Storage state instead of raw cookies
- Configurable selectors if Bandcamp updates the YUM UI
- Optional logging to JSON for auditability

---

## Support

Issues welcome!  
If you run into edge cases or want new features, open an issue and we’ll try to help or ship an update. PRs encouraged.

Happy checking!
