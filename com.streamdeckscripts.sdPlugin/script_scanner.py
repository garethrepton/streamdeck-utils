"""Auto-discovers Python scripts in the scripts directory."""

from pathlib import Path


class ScriptScanner:
    def __init__(self, scripts_dir: Path):
        self.scripts_dir = scripts_dir
        self.scripts_dir.mkdir(parents=True, exist_ok=True)

    def get_scripts(self) -> list:
        scripts = []
        for path in self.scripts_dir.rglob("*"):
            if path.suffix not in (".py", ".pyw"):
                continue
            scripts.append({
                "name": path.stem,
                "path": str(path.relative_to(self.scripts_dir)).replace("\\", "/"),
            })
        scripts.sort(key=lambda s: s["name"].lower())
        return scripts
