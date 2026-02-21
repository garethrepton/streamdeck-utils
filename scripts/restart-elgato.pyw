"""
Restart Elgato - Full reinitialisation of Stream Deck + Wave Link
Small GUI window shows progress as each step runs.
"""

import tkinter as tk
import subprocess
import threading
import time
import os
import sys
import tempfile
import msvcrt

# ── Configuration ──────────────────────────────────────────────────────────

APPS_TO_RESTART = [
    {"name": "Spotify", "path": os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")},
    # {"name": "Discord", "path": os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"), "args": "--processStart Discord.exe"},
]

WAVE_LINK_PATHS = [
    os.path.expandvars(r"%ProgramFiles%\Elgato\WaveLink\WaveLink.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Elgato\WaveLink\WaveLink.exe"),
]

STREAM_DECK_PATHS = [
    os.path.expandvars(r"%ProgramFiles%\Elgato\StreamDeck\StreamDeck.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\Elgato\StreamDeck\StreamDeck.exe"),
]

OUTPUT_DEVICE_MATCH = "System*Elgato*"
MIC_DEVICE_MATCH = "*MicrophoneFX*"

# ── Colours ────────────────────────────────────────────────────────────────

BG       = "#1e1e2e"
FG       = "#cdd6f4"
ACCENT   = "#89b4fa"
GREEN    = "#a6e3a1"
RED      = "#f38ba8"
DIM      = "#585b70"
SURFACE  = "#313244"

# ── Helpers ────────────────────────────────────────────────────────────────

NO_WINDOW = subprocess.CREATE_NO_WINDOW
LOCK_FILE = os.path.join(tempfile.gettempdir(), "restart-elgato.lock")
SUBPROCESS_TIMEOUT = 30


def acquire_lock():
    """Try to acquire a file lock. Returns the open file handle, or None if already running."""
    try:
        fh = open(LOCK_FILE, "w")
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        return fh
    except (OSError, IOError):
        return None


def release_lock(fh):
    """Release the file lock."""
    if fh is None:
        return
    try:
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        fh.close()
    except (OSError, IOError):
        pass


def find_exe(paths):
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


def kill_processes(*names):
    for name in names:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", f"{name}.exe"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=NO_WINDOW, timeout=SUBPROCESS_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            pass


def is_running(name):
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {name}.exe", "/NH"],
            capture_output=True, text=True,
            creationflags=NO_WINDOW, timeout=SUBPROCESS_TIMEOUT,
        )
        return name.lower() in result.stdout.lower()
    except subprocess.TimeoutExpired:
        return False


def set_audio_devices():
    ps_script = r"""
Import-Module AudioDeviceCmdlets
$devices = Get-AudioDevice -List
$out = $devices | Where-Object { $_.Type -eq 'Playback' -and $_.Name -like '*System*Elgato*' }
if ($out) { Set-AudioDevice -ID $out.ID | Out-Null; Write-Host "output:$($out.Name)" }
$mic = $devices | Where-Object { $_.Type -eq 'Recording' -and $_.Name -like '*MicrophoneFX*' }
if ($mic) { Set-AudioDevice -ID $mic.ID | Out-Null; Write-Host "mic:$($mic.Name)" }
"""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            capture_output=True, text=True,
            creationflags=NO_WINDOW, timeout=SUBPROCESS_TIMEOUT,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ""


# ── GUI ────────────────────────────────────────────────────────────────────

class RestartApp:
    STEPS = [
        "Closing audio-sensitive apps",
        "Stopping Wave Link",
        "Stopping Stream Deck",
        "Starting Wave Link",
        "Waiting for Wave Link to initialise",
        "Starting Stream Deck",
        "Restarting audio-sensitive apps",
        "Setting default audio devices",
    ]

    def __init__(self, lock_handle):
        self._lock_handle = lock_handle
        self.root = tk.Tk()
        self.root.title("Restart Elgato")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        width, height = 380, 400
        padding = 20
        x = self.root.winfo_screenwidth() - width - padding
        y = self.root.winfo_screenheight() - height - padding - 48  # 48 for taskbar
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.overrideredirect(True)  # Remove title bar for a cleaner toast look
        self.root.bind("<Escape>", lambda _: self._force_quit())
        self.root.protocol("WM_DELETE_WINDOW", self._force_quit)

        # Title
        tk.Label(
            self.root, text="Restart Elgato", font=("Segoe UI", 16, "bold"),
            bg=BG, fg=ACCENT,
        ).pack(pady=(20, 4))

        tk.Label(
            self.root, text="Reinitialising audio stack", font=("Segoe UI", 9),
            bg=BG, fg=DIM,
        ).pack(pady=(0, 16))

        # Steps frame
        self.step_frame = tk.Frame(self.root, bg=BG)
        self.step_frame.pack(padx=28, fill="x")

        self.step_labels = []
        self.step_icons = []
        for step_text in self.STEPS:
            row = tk.Frame(self.step_frame, bg=BG)
            row.pack(fill="x", pady=3)

            icon = tk.Label(row, text="\u2500", font=("Segoe UI", 11), bg=BG, fg=DIM, width=2)
            icon.pack(side="left")

            label = tk.Label(
                row, text=step_text, font=("Segoe UI", 10),
                bg=BG, fg=DIM, anchor="w",
            )
            label.pack(side="left", padx=(4, 0))

            self.step_icons.append(icon)
            self.step_labels.append(label)

        # Status bar at bottom
        self.status = tk.Label(
            self.root, text="Starting...", font=("Segoe UI", 9),
            bg=SURFACE, fg=DIM, anchor="w", padx=12, pady=6,
        )
        self.status.pack(side="bottom", fill="x")

        self.current_step = -1
        self.apps_restarted = []

        # Run the work in a background thread
        threading.Thread(target=self.run, daemon=True).start()
        self.root.mainloop()

    def set_step(self, index, state="active"):
        def update():
            if state == "active":
                self.step_icons[index].config(text="\u25cb", fg=ACCENT)
                self.step_labels[index].config(fg=FG)
                self.status.config(text=self.STEPS[index] + "...")
            elif state == "done":
                self.step_icons[index].config(text="\u2713", fg=GREEN)
                self.step_labels[index].config(fg=GREEN)
            elif state == "error":
                self.step_icons[index].config(text="\u2717", fg=RED)
                self.step_labels[index].config(fg=RED)
            elif state == "skip":
                self.step_icons[index].config(text="\u2500", fg=DIM)
                self.step_labels[index].config(fg=DIM)
        self.root.after(0, update)

    def begin_step(self, index):
        self.current_step = index
        self.set_step(index, "active")

    def finish_step(self, index, state="done"):
        self.set_step(index, state)

    def _force_quit(self):
        release_lock(self._lock_handle)
        self.root.destroy()
        os._exit(0)

    def finish(self, success=True):
        def update():
            if success:
                self.status.config(text="All done!", fg=GREEN)
            else:
                self.status.config(text="Completed with errors", fg=RED)
            self.root.after(2500, self._force_quit)
        self.root.after(0, update)

    def run(self):
        try:
            # Step 0: Close audio-sensitive apps
            self.begin_step(0)
            for app in APPS_TO_RESTART:
                if is_running(app["name"]):
                    self.apps_restarted.append(app)
                    kill_processes(app["name"])
            self.finish_step(0)

            # Step 1: Stop Wave Link
            self.begin_step(1)
            kill_processes("WaveLink", "WaveLinkEngine")
            time.sleep(2)
            self.finish_step(1)

            # Step 2: Stop Stream Deck
            self.begin_step(2)
            kill_processes("StreamDeck", "StreamDeckHelper")
            time.sleep(3)
            self.finish_step(2)

            # Step 3: Start Wave Link
            self.begin_step(3)
            wl = find_exe(WAVE_LINK_PATHS)
            if wl:
                subprocess.Popen([wl])
                self.finish_step(3)
            else:
                self.finish_step(3, "error")

            # Step 4: Wait for Wave Link
            self.begin_step(4)
            for i in range(8, 0, -1):
                self.root.after(0, lambda s=i: self.status.config(
                    text=f"Waiting for Wave Link to initialise... {s}s"
                ))
                time.sleep(1)
            self.finish_step(4)

            # Step 5: Start Stream Deck
            self.begin_step(5)
            sd = find_exe(STREAM_DECK_PATHS)
            if sd:
                subprocess.Popen([sd])
                self.finish_step(5)
            else:
                self.finish_step(5, "error")

            # Step 6: Restart audio-sensitive apps
            self.begin_step(6)
            if self.apps_restarted:
                for app in self.apps_restarted:
                    if os.path.isfile(app["path"]):
                        args = [app["path"]]
                        if "args" in app:
                            args.extend(app["args"].split())
                        subprocess.Popen(args)
            self.finish_step(6)

            # Step 7: Set default audio devices
            self.begin_step(7)
            result = set_audio_devices()
            if "output:" in result and "mic:" in result:
                self.finish_step(7)
            else:
                self.finish_step(7, "error")

            self.finish(success=True)

        except Exception as e:
            self.root.after(0, lambda: self.status.config(text=f"Error: {e}", fg=RED))
            self.finish(success=False)


if __name__ == "__main__":
    lock = acquire_lock()
    if lock is None:
        sys.exit(0)  # Already running
    try:
        RestartApp(lock)
    finally:
        release_lock(lock)
