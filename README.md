# VIBE Coded!

# Stream Deck Utils

A local-only Stream Deck plugin with two actions:

- **Mic Mute Toggle** — Toggles system microphone mute via Windows Core Audio API (pycaw). Works across Discord, Game Bar, and all apps.
- **Script Runner** — Auto-discovers Python scripts in the `scripts/` folder. Pick one per button via a dropdown in the Stream Deck settings.

## Requirements

- Windows 10+
- Python 3.10+
- Stream Deck 6.0+

## Install

```
python install.py
```

The installer will prompt for admin, stop Stream Deck, copy files, install dependencies, and restart Stream Deck.

To update scripts only (no restart needed), choose option 2 in the installer menu.

## Adding Scripts

Drop any `.py` or `.pyw` file into the `scripts/` folder, then re-run the installer or use the "Update scripts only" option. The new script will appear in the Script Runner dropdown.

## Project Structure

```
com.streamdeckscripts.sdPlugin/   # Stream Deck plugin
  plugin.py                       # Main plugin entry point
  audio_controller.py             # Mic mute via pycaw
  script_scanner.py               # Script auto-discovery
  ui/script-runner.html           # Script picker dropdown
scripts/                          # Your Python scripts go here
install.py                        # TUI installer
```
