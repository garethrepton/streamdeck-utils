"""Checks default audio device assignments via PowerShell AudioDeviceCmdlets."""

import fnmatch
import logging
import subprocess

logger = logging.getLogger(__name__)

OUTPUT_PATTERN = "*System*Elgato*"
MIC_PATTERN = "*MicrophoneFX*"
NO_WINDOW = 0x08000000

PS_SCRIPT = """\
Import-Module AudioDeviceCmdlets
$p = Get-AudioDevice -Playback
$r = Get-AudioDevice -Recording
$pc = Get-AudioDevice -PlaybackCommunication
$rc = Get-AudioDevice -RecordingCommunication
Write-Host "playback:$($p.Name)"
Write-Host "recording:$($r.Name)"
Write-Host "playback_comm:$($pc.Name)"
Write-Host "recording_comm:$($rc.Name)"
"""


def check_audio_status() -> tuple[bool, str]:
    """Return (all_ok, detail_string) for current default audio devices."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", PS_SCRIPT],
            capture_output=True, text=True, creationflags=NO_WINDOW,
        )
    except Exception:
        logger.exception("Failed to run PowerShell audio check")
        return False, "PowerShell error"

    values = {}
    for line in result.stdout.strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            values[key.strip()] = val.strip()

    playback = values.get("playback", "")
    recording = values.get("recording", "")
    playback_comm = values.get("playback_comm", "")
    recording_comm = values.get("recording_comm", "")

    output_ok = fnmatch.fnmatch(playback, OUTPUT_PATTERN)
    mic_ok = fnmatch.fnmatch(recording, MIC_PATTERN)
    comm_out_ok = fnmatch.fnmatch(playback_comm, OUTPUT_PATTERN)
    comm_mic_ok = fnmatch.fnmatch(recording_comm, MIC_PATTERN)

    all_ok = output_ok and mic_ok and comm_out_ok and comm_mic_ok
    detail = (
        f"Playback: {playback or 'N/A'} ({'OK' if output_ok else 'WRONG'}), "
        f"Recording: {recording or 'N/A'} ({'OK' if mic_ok else 'WRONG'}), "
        f"Comm Playback: {playback_comm or 'N/A'} ({'OK' if comm_out_ok else 'WRONG'}), "
        f"Comm Recording: {recording_comm or 'N/A'} ({'OK' if comm_mic_ok else 'WRONG'})"
    )
    logger.debug("Audio check: ok=%s, %s", all_ok, detail)
    return all_ok, detail
