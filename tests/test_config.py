# tests/test_config.py
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import Config


class TestConfig:
    def test_default_codex_home(self):
        """Default codex_home should be ~/.codex"""
        cfg = Config(appdata_dir=Path(tempfile.mkdtemp()))
        expected = Path.home() / ".codex"
        assert cfg.codex_home == expected

    def test_load_from_env(self, tmp_path):
        """CODEX_HOME env var should override default"""
        env_dir = tmp_path / "env_codex"
        env_dir.mkdir()
        with patch.dict(os.environ, {"CODEX_HOME": str(env_dir)}):
            cfg = Config(appdata_dir=tmp_path)
            assert cfg.codex_home == env_dir

    def test_save_and_load(self, tmp_path):
        """Config should persist codex_home to config.json"""
        custom_dir = tmp_path / "custom_codex"
        custom_dir.mkdir()
        cfg = Config(appdata_dir=tmp_path)
        cfg.codex_home = custom_dir
        cfg.save()

        cfg2 = Config(appdata_dir=tmp_path)
        assert cfg2.codex_home == custom_dir

    def test_config_json_structure(self, tmp_path):
        """config.json should have correct keys"""
        cfg = Config(appdata_dir=tmp_path)
        cfg.codex_home = tmp_path / "test"
        cfg.save()

        data = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert "codex_home" in data
        assert "theme" in data
        assert "window_geometry" in data
        assert data["theme"] == "auto"

    def test_custom_codex_home_overrides_env(self, tmp_path):
        """Saved config should override env var"""
        env_dir = tmp_path / "env_codex"
        env_dir.mkdir()
        saved_dir = tmp_path / "saved_codex"
        saved_dir.mkdir()

        cfg = Config(appdata_dir=tmp_path)
        cfg.codex_home = saved_dir
        cfg.save()

        with patch.dict(os.environ, {"CODEX_HOME": str(env_dir)}):
            cfg2 = Config(appdata_dir=tmp_path)
            assert cfg2.codex_home == saved_dir
