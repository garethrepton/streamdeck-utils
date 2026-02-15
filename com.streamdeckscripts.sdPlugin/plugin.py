"""Stream Deck Utils — Mic mute toggle and Python script runner plugin."""

import logging
import subprocess
import sys
from pathlib import Path

from streamdeck_sdk import StreamDeck, Action
from streamdeck_sdk.sd_objs import events_received_objs

from audio_controller import AudioController
from script_scanner import ScriptScanner

PLUGIN_DIR = Path(__file__).parent.resolve()
REPO_DIR = PLUGIN_DIR.parent
SCRIPTS_DIR = REPO_DIR / "scripts"
LOG_FILE = PLUGIN_DIR / "logs" / "plugin.log"

logger = logging.getLogger(__name__)


class MicMuteAction(Action):
    UUID = "com.streamdeckscripts.mic-mute"

    def __init__(self):
        super().__init__()
        self.audio = AudioController()

    def on_will_appear(self, obj: events_received_objs.WillAppear) -> None:
        is_muted = self.audio.is_mic_muted()
        self.set_state(obj.context, 1 if is_muted else 0)

    def on_key_down(self, obj: events_received_objs.KeyDown) -> None:
        is_muted = self.audio.toggle_mic_mute()
        self.set_state(obj.context, 1 if is_muted else 0)
        logger.info("Mic %s", "muted" if is_muted else "unmuted")


class ScriptRunnerAction(Action):
    UUID = "com.streamdeckscripts.script-runner"

    def __init__(self):
        super().__init__()
        self.scanner = ScriptScanner(SCRIPTS_DIR)

    def on_property_inspector_did_appear(self, obj: events_received_objs.PropertyInspectorDidAppear) -> None:
        scripts = self.scanner.get_scripts()
        self.send_to_property_inspector(
            action=obj.action,
            context=obj.context,
            payload={"event": "scriptList", "scripts": scripts},
        )

    def on_did_receive_settings(self, obj: events_received_objs.DidReceiveSettings) -> None:
        logger.info("Settings updated: %s", obj.payload.settings)

    def on_key_down(self, obj: events_received_objs.KeyDown) -> None:
        script_path = obj.payload.settings.get("scriptPath")
        if not script_path:
            logger.warning("No script configured")
            self.show_alert(obj.context)
            return

        script_file = (SCRIPTS_DIR / script_path).resolve()
        if not script_file.is_relative_to(SCRIPTS_DIR.resolve()):
            logger.error("Path traversal attempt: %s", script_path)
            self.show_alert(obj.context)
            return
        if not script_file.exists():
            logger.error("Script not found: %s", script_file)
            self.show_alert(obj.context)
            return

        try:
            cmd = [sys.executable, str(script_file)]
            kwargs = {}
            if script_file.suffix == ".pyw":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            subprocess.Popen(cmd, **kwargs)
            self.show_ok(obj.context)
            logger.info("Executed: %s", script_path)
        except Exception:
            logger.exception("Failed to execute: %s", script_path)
            self.show_alert(obj.context)


if __name__ == "__main__":
    StreamDeck(
        actions=[
            MicMuteAction(),
            ScriptRunnerAction(),
        ],
        log_file=LOG_FILE,
        log_level=logging.DEBUG,
    ).run()
