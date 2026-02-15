# VIBE Coded!

# Stream Deck Utils

A local only stream deck plugin framework, allowing you to add python scripts and they become plugins. Its vibe coded, but a well understood problem.

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
