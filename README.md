# bcccheck

![bcccheck TUI Screenshot](screenshot.png)

A small, practical, open-source helper that automates checking Bandcamp YUM codes like a careful, efficient human.

bcccheck opens bandcamp.com/yum in a real browser session, enters codes from a list one at a time, and stops at the first redeemable code it finds. It features a modern, "New Retro" TUI (Terminal User Interface) for a beautiful and snappy experience.

> Example: You have a list of codes from a release. bcccheck loads the YUM page, types each code, and when one is redeemable, marks it in the TUI and stops.

---

## Features

- **Integrated TUI**: A terminal interface that follows your terminal's own colors by default, with selectable themes (dracula, tokyo-night, rose-pine).
- **Automated Redemption**: Enters codes in a real browser session via Playwright.
- **Intelligent Detection**: Uses robust signals (navigation redirects or page metadata) to confirm success.
- **Human-like Pacing**: Small delays to mimic natural interaction and avoid rate limits.
- **Session Aware**: Works with your authenticated `cookies.json` for seamless redemption to your account.

---

## Requirements

- [uv](https://docs.astral.sh/uv/) — only needed when running from source; the prebuilt binary requires none of this
- A codes list file: `codes.txt` (one code per line)
- Your Bandcamp cookies: `cookies.json` (optional — only to save redeemed releases to your library)

> The app runs **headless by default** (the TUI is the only thing you see; no browser window). Use `--show-browser` to show the browser for debugging.

---

## Installation

The easiest way is with [uv](https://docs.astral.sh/uv/), which creates a managed
virtual environment and installs dependencies automatically — no manual `venv` or `pip` needed:

```sh
uv run tui.py
```

That's it. The first run downloads the dependencies and the Chromium browser, then launches the TUI.

### Manual install (alternative)
If you prefer not to use uv:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python tui.py
```

The Chromium browser is downloaded automatically the first time you run the app (about 260 MB, one time only). To pre-download it yourself, run `playwright install chromium`.

---

## Download (prebuilt binary)

For most users, grab a prebuilt binary — **no Python or `uv` required**:

- **Linux**: `bcccheck-linux`
- **macOS**: `bcccheck-macos` (universal, arm64 + x86_64)

Download the latest from the [GitHub Releases](https://github.com/binbot/bcccheck/releases) page, then place your `codes.txt` **next to the binary** (recommended — this also makes **double-clicking** the app work, since a double-click runs it from your home folder). You can also run it from a terminal in any folder that contains `codes.txt`. Then:

```sh
ls codes.txt                    # confirm it's here
chmod +x bcccheck-linux          # Linux
# on macOS, if Gatekeeper complains, remove the quarantine flag first:
# xattr -d com.apple.quarantine bcccheck-macos

./bcccheck-linux                 # or: ./bcccheck-macos
```

The app runs **headless** (no browser window appears). On every run it ensures the Chromium browser is available, downloading it (~260 MB) into Playwright's cache only when missing or outdated, then reuses it. If a browser was already installed from a different Playwright version, it is updated automatically — no manual `playwright install` needed. The same flags apply: `--theme dracula`, `--show-browser`.

All activity is also written to `bcccheck.log` in the same folder, so you can inspect what the app did.

### Build from source (contributors)

If you have a Python toolchain ([uv](https://docs.astral.sh/uv/) + Python 3.9+), you can build the binary yourself from a checkout:

```sh
uv run --with pyinstaller pyinstaller bcccheck.spec
```

The result lands at `dist/bcccheck`. This path needs the same `uv`/Python setup as the dev workflow, so casual users should prefer the prebuilt download above.

---

## Usage

### Run the TUI (Recommended)
This launches the modern terminal interface:

```sh
uv run tui.py
# or, if you made the launcher executable:
./run.sh
```
- Press **'s'** to start checking codes.
- Press **'q'** to quit.
- Press **'t'** to cycle color themes (default follows your terminal; also dracula, tokyo-night, rose-pine).
- Pass `--theme dracula` to start in a specific theme.
- Pass `--show-browser` to show the browser window (default is headless/TUI-only).

### Run the CLI
For a classic, text-only experience:

```sh
uv run bcccheck.py --show-browser
```

---

## Preparing `codes.txt`

Create a `codes.txt` file **in the directory you run the binary / `uv run tui.py` from** (the current working directory) with one Bandcamp YUM code per line. Example:

```
abcd-1234
efgh-5678
qdxa-ktw6
```

---

## Authentication (`cookies.json`)

To redeem codes directly to your Bandcamp collection, export your cookies to `cookies.json` in the project root.

- Log in to Bandcamp in your browser.
- Use a cookie export extension (Netscape or JSON format).
- Save as `cookies.json`.

---

## Project structure

- `tui.py` — The TUI application entry point.
- `bcccheck.py` — The core logic and CLI entry point.
- `styles.tcss` — Structural stylesheet for the TUI (colors come from the active theme).
- `run.sh` / `run.command` — Launchers that run the TUI via `uv` (no manual setup).
- `codes.txt` — Your list of codes (ignored by git).
- `cookies.json` — Your Bandcamp session cookies (ignored by git).

---

## Open Source

- License: MIT
- Contributions welcome!

Happy checking!
