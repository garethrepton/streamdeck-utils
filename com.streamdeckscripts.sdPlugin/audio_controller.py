"""Windows Core Audio API wrapper for microphone mute control via pycaw."""

import logging

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

logger = logging.getLogger(__name__)


class AudioController:
    def __init__(self):
        self._volume = None
        self._init_device()

    def _init_device(self):
        try:
            mic = AudioUtilities.GetMicrophone()
            if mic is None:
                logger.error("No microphone device found")
                return
            interface = mic.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._volume = interface.QueryInterface(IAudioEndpointVolume)
        except Exception:
            logger.exception("Failed to initialise audio device")

    def is_mic_muted(self) -> bool:
        try:
            if self._volume is None:
                self._init_device()
            if self._volume is None:
                return False
            return bool(self._volume.GetMute())
        except Exception:
            logger.exception("Error checking mute state")
            self._volume = None
            return False

    def toggle_mic_mute(self) -> bool:
        try:
            if self._volume is None:
                self._init_device()
            if self._volume is None:
                return False
            new_state = not self._volume.GetMute()
            self._volume.SetMute(int(new_state), None)
            return bool(new_state)
        except Exception:
            logger.exception("Error toggling mute")
            self._volume = None
            return self.is_mic_muted()
