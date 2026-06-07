# core/config.py
"""Configuration management for Codex Transfer."""
from __future__ import annotations

import json
import os
from pathlib import Path


class Config:
    """Manages persistent configuration in %APPDATA%/CodexTransfer/config.json."""

    def __init__(self, appdata_dir: Path | None = None):
        if appdata_dir is None:
            appdata_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "CodexTransfer"
        self._dir = appdata_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "config.json"

        self.codex_home: Path = Path.home() / ".codex"
        self.theme: str = "auto"
        self.window_geometry: str = "1200x700"

        self._load()

    def _load(self) -> None:
        # Priority: config.json > CODEX_HOME env > default
        saved_codex_home = None
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                saved_codex_home = Path(data["codex_home"]) if "codex_home" in data else None
                self.theme = data.get("theme", "auto")
                self.window_geometry = data.get("window_geometry", "1200x700")
            except (json.JSONDecodeError, KeyError):
                pass

        if saved_codex_home is not None:
            self.codex_home = saved_codex_home
        elif os.environ.get("CODEX_HOME"):
            self.codex_home = Path(os.environ["CODEX_HOME"]).expanduser()

    def save(self) -> None:
        data = {
            "codex_home": str(self.codex_home),
            "theme": self.theme,
            "window_geometry": self.window_geometry,
        }
        self._path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
