"""Stream Deck Utils — TUI installer for Windows."""

import ctypes
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_DIR = Path(__file__).parent.resolve()
PLUGIN_NAME = "com.streamdeckscripts.sdPlugin"
SOURCE = REPO_DIR / PLUGIN_NAME
SCRIPTS_SOURCE = REPO_DIR / "scripts"
DEST = Path(os.environ["APPDATA"]) / "Elgato" / "StreamDeck" / "Plugins" / PLUGIN_NAME
SCRIPTS_DEST = DEST.parent / "scripts"
STREAMDECK_EXE = Path(os.environ["ProgramFiles"]) / "Elgato" / "StreamDeck" / "StreamDeck.exe"


# -- TUI helpers (no dependencies) ------------------------------------------

CSI = "\033["
BOLD = f"{CSI}1m"
DIM = f"{CSI}2m"
RESET = f"{CSI}0m"
GREEN = f"{CSI}32m"
RED = f"{CSI}31m"
YELLOW = f"{CSI}33m"
CYAN = f"{CSI}36m"
WHITE = f"{CSI}97m"
BG_BLUE = f"{CSI}44m"

TICK = f"{GREEN}\u2714{RESET}"
CROSS = f"{RED}\u2718{RESET}"
ARROW = f"{CYAN}\u25b6{RESET}"
SPINNER_FRAMES = "\u2807\u2836\u2834\u2826\u280e\u280b\u2819\u2838"


def enable_ansi():
    """Enable ANSI escape processing on Windows 10+."""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    mode = ctypes.c_ulong()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING


def clear():
    os.system("cls")


def banner():
    lines = [
        f"{BG_BLUE}{WHITE}{BOLD}                                          {RESET}",
        f"{BG_BLUE}{WHITE}{BOLD}   Stream Deck Utils — Installer   v1.0   {RESET}",
        f"{BG_BLUE}{WHITE}{BOLD}                                          {RESET}",
    ]
    print()
    for line in lines:
        print(f"  {line}")
    print()


def status(msg: str, state: str = "run"):
    symbols = {"run": ARROW, "ok": TICK, "fail": CROSS, "warn": f"{YELLOW}!{RESET}"}
    sym = symbols.get(state, ARROW)
    print(f"  {sym}  {msg}")


def spin(msg: str, fn, *args, **kwargs):
    """Run *fn* while showing a spinner. Returns fn result."""
    import threading

    result = [None]
    error = [None]

    def worker():
        try:
            result[0] = fn(*args, **kwargs)
        except Exception as exc:
            error[0] = exc

    t = threading.Thread(target=worker, daemon=True)
    t.start()

    i = 0
    while t.is_alive():
        frame = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
        print(f"\r  {CYAN}{frame}{RESET}  {msg}", end="", flush=True)
        time.sleep(0.1)
        i += 1

    print(f"\r  {TICK}  {msg}   ")

    if error[0]:
        raise error[0]
    return result[0]


def divider():
    print(f"  {DIM}{'─' * 40}{RESET}")


def confirm(prompt: str) -> bool:
    answer = input(f"\n  {YELLOW}?{RESET}  {prompt} {DIM}[y/n]{RESET} ").strip().lower()
    return answer in ("", "y", "yes")


def menu(title: str, options: list[tuple[str, str]]) -> str:
    """Show a numbered menu. Returns the key of the selected option."""
    print(f"\n  {YELLOW}?{RESET}  {title}\n")
    for i, (_key, label) in enumerate(options, 1):
        print(f"     {CYAN}{i}{RESET}  {label}")
    while True:
        choice = input(f"\n  {DIM}Enter choice [1-{len(options)}]:{RESET} ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1][0]
        print(f"  {RED}Invalid choice{RESET}")


# -- Installer steps ---------------------------------------------------------

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def elevate():
    """Re-launch this script as admin."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{__file__}"', None, 1
    )


def stop_streamdeck():
    subprocess.run(["taskkill", "/F", "/IM", "StreamDeck.exe"], capture_output=True)
    # Kill the plugin's pythonw process that Stream Deck spawned
    subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe"], capture_output=True)
    time.sleep(3)


def remove_old_install():
    for path in (DEST, SCRIPTS_DEST):
        if not path.exists():
            continue
        for attempt in range(5):
            try:
                shutil.rmtree(path)
                break
            except PermissionError:
                time.sleep(1)


IGNORE = shutil.ignore_patterns("nul", "__pycache__", "*.pyc", "logs")


def copy_plugin():
    shutil.copytree(SOURCE, DEST, dirs_exist_ok=True, ignore=IGNORE)


def copy_scripts():
    shutil.copytree(SCRIPTS_SOURCE, SCRIPTS_DEST, dirs_exist_ok=True, ignore=IGNORE)


def install_deps():
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "-r", str(DEST / "requirements.txt")],
        capture_output=True,
    )


def start_streamdeck():
    if STREAMDECK_EXE.exists():
        subprocess.Popen([str(STREAMDECK_EXE)])


# -- Main --------------------------------------------------------------------

def main():
    enable_ansi()
    clear()
    banner()

    # Preflight checks
    divider()

    if not SOURCE.exists():
        status(f"Plugin folder not found: {SOURCE}", "fail")
        input("\n  Press Enter to exit...")
        sys.exit(1)

    if not SCRIPTS_SOURCE.exists():
        status(f"Scripts folder not found: {SCRIPTS_SOURCE}", "fail")
        input("\n  Press Enter to exit...")
        sys.exit(1)

    status(f"Plugin source   {DIM}{SOURCE}{RESET}", "ok")
    status(f"Scripts source   {DIM}{SCRIPTS_SOURCE}{RESET}", "ok")
    status(f"Install target   {DIM}{DEST}{RESET}", "ok")

    has_old = DEST.exists() or SCRIPTS_DEST.exists()
    if has_old:
        status("Previous installation found", "warn")

    divider()

    options = [
        ("full", "Full install (plugin + scripts + dependencies)"),
        ("scripts", "Update scripts only"),
    ]
    if has_old:
        options.append(("remove", "Remove previous installation"))
    options.append(("quit", "Quit"))

    action = menu("What would you like to do?", options)

    if action == "quit":
        print(f"\n  {DIM}Cancelled.{RESET}\n")
        input(f"  {DIM}Press Enter to exit...{RESET}")
        sys.exit(0)

    print()

    if action == "remove":
        spin("Stopping Stream Deck", stop_streamdeck)
        spin("Removing installation", remove_old_install)
        print()
        divider()
        print(f"  {GREEN}{BOLD}Done!{RESET}  Previous installation removed.")
        print()
        input(f"  {DIM}Press Enter to exit...{RESET}")
        return

    if action == "scripts":
        spin("Copying scripts", copy_scripts)
        print()
        divider()
        print(f"  {GREEN}{BOLD}Done!{RESET}  Scripts updated. No restart needed.")
        print()
        input(f"  {DIM}Press Enter to exit...{RESET}")
        return

    # Full install
    if has_old and confirm("Remove previous installation first?"):
        print()
        spin("Stopping Stream Deck", stop_streamdeck)
        spin("Removing previous install", remove_old_install)
    else:
        spin("Stopping Stream Deck", stop_streamdeck)

    spin("Copying plugin files", copy_plugin)
    spin("Copying scripts", copy_scripts)
    spin("Installing Python dependencies", install_deps)
    spin("Starting Stream Deck", start_streamdeck)

    print()
    divider()
    print(f"  {GREEN}{BOLD}Done!{RESET}  Look for {CYAN}Utilities{RESET} in the Stream Deck action list.")
    print()
    input(f"  {DIM}Press Enter to exit...{RESET}")


if __name__ == "__main__":
    if not is_admin():
        elevate()
        sys.exit(0)
    try:
        main()
    except Exception as exc:
        print(f"\n  {RED}ERROR: {exc}{RESET}\n")
        input("  Press Enter to exit...")
        sys.exit(1)
