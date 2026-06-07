# Codex Transfer v1.0.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight Windows desktop app for browsing, filtering, migrating, copying, and deleting Codex chat history records.

**Architecture:** Three-layer design — UI (tkinter + ttkbootstrap) reads from Data layer (SQLite + JSONL operations), with System layer handling single-instance detection, theme following, and config persistence. The app reads `state_*.sqlite` for thread metadata and operates on JSONL rollout files only when mutations are needed.

**Tech Stack:** Python 3.10+, tkinter, ttkbootstrap, sqlite3 (builtin), Pillow, PyInstaller, ctypes (Windows API)

**Spec:** `docs/superpowers/specs/2026-06-07-codex-transfer-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `main.py` | Entry point: single-instance mutex check, launch UI |
| `core/__init__.py` | Package marker |
| `core/config.py` | Load/save `%APPDATA%/CodexTransfer/config.json`, resolve codex_home |
| `core/database.py` | SQLite read/write: list threads, update provider, delete threads, get distinct values |
| `core/rollout.py` | JSONL file ops: rewrite provider in session_meta, copy rollout file, delete rollout file |
| `ui/__init__.py` | Package marker |
| `ui/theme.py` | Detect Windows light/dark theme from registry, return ttkbootstrap theme name |
| `ui/widgets.py` | `CheckboxTreeview` — Treeview with checkbox column, sort, select-all helpers |
| `ui/app.py` | Main window: path bar, filter bar, table, action bar, status bar, all event wiring |
| `assets/icon.ico` | App icon (converted from PNG) |
| `assets/convert_icon.py` | One-time script to convert PNG → ICO |
| `build.py` | PyInstaller packaging script |
| `requirements.txt` | Runtime + build dependencies |
| `README.md` | Usage documentation |
| `tests/test_config.py` | Tests for config module |
| `tests/test_database.py` | Tests for database module |
| `tests/test_rollout.py` | Tests for rollout module |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `core/__init__.py`
- Create: `ui/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
ttkbootstrap>=1.10
Pillow>=10.0
pyinstaller>=6.0
```

- [ ] **Step 2: Create package markers**

Create empty `__init__.py` in `core/`, `ui/`, and `tests/`.

- [ ] **Step 3: Create directory structure**

```
D:\edge_load\CodexTransfer\
├── main.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   └── rollout.py
├── ui/
│   ├── __init__.py
│   ├── app.py
│   ├── theme.py
│   └── widgets.py
├── assets/
│   └── convert_icon.py
├── tests/
│   └── __init__.py
├── build.py
├── requirements.txt
└── README.md
```

- [ ] **Step 4: Install dependencies**

Run: `pip install ttkbootstrap Pillow`
Expected: Successfully installed ttkbootstrap and Pillow

- [ ] **Step 5: Commit**

```bash
git init && git add -A && git commit -m "chore: project scaffolding"
```

---

### Task 2: Config Module (`core/config.py`)

**Files:**
- Create: `core/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for Config**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL (module `core.config` not found)

- [ ] **Step 3: Implement Config**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_config.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/config.py tests/test_config.py
git commit -m "feat: add config module with persistence"
```

---

### Task 3: Database Module (`core/database.py`)

**Files:**
- Create: `core/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Create test fixture with in-memory SQLite**

```python
# tests/test_database.py
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import CodexDB


@pytest.fixture
def db_path(tmp_path):
    """Create a test SQLite database mimicking Codex state_5.sqlite schema."""
    path = tmp_path / "state_5.sqlite"
    conn = sqlite3.connect(str(path))
    conn.execute("""
        CREATE TABLE threads (
            id TEXT PRIMARY KEY,
            rollout_path TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            source TEXT NOT NULL,
            model_provider TEXT NOT NULL,
            cwd TEXT NOT NULL,
            title TEXT NOT NULL,
            sandbox_policy TEXT NOT NULL,
            approval_mode TEXT NOT NULL,
            tokens_used INTEGER NOT NULL DEFAULT 0,
            has_user_event INTEGER NOT NULL DEFAULT 0,
            archived INTEGER NOT NULL DEFAULT 0,
            archived_at INTEGER,
            first_user_message TEXT NOT NULL DEFAULT '',
            preview TEXT NOT NULL DEFAULT '',
            cli_version TEXT NOT NULL DEFAULT '',
            agent_nickname TEXT,
            agent_role TEXT,
            memory_mode TEXT NOT NULL DEFAULT 'enabled',
            model TEXT,
            reasoning_effort TEXT,
            agent_path TEXT,
            created_at_ms INTEGER,
            updated_at_ms INTEGER,
            thread_source TEXT
        )
    """)
    # Insert test data
    test_rows = [
        ("id-001", "/rollout/001.jsonl", 1780132666, 1780133655, "vscode", "openai",
         "D:\\project1", "帮我写个爬虫", "sandbox", "auto", 0, 0, 0, None, "帮我写个爬虫", "帮我写个爬虫"),
        ("id-002", "/rollout/002.jsonl", 1780132504, 1780132538, "vscode", "openai",
         "D:\\project2", "修复登录bug", "sandbox", "auto", 0, 0, 0, None, "修复登录bug", "修复登录bug"),
        ("id-003", "/rollout/003.jsonl", 1780132333, 1780132366, "vscode", "packycode",
         "D:\\project1", "数据分析脚本", "sandbox", "auto", 0, 0, 1, None, "数据分析脚本", "数据分析脚本"),
        ("id-004", "/rollout/004.jsonl", 1779938390, 1779938398, "vscode", "openai",
         "D:\\project3", "测试标题", "sandbox", "auto", 0, 0, 0, None, "测试标题", "测试标题"),
    ]
    conn.executemany(
        "INSERT INTO threads (id, rollout_path, created_at, updated_at, source, model_provider, "
        "cwd, title, sandbox_policy, approval_mode, tokens_used, has_user_event, archived, "
        "archived_at, first_user_message, preview) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        test_rows,
    )
    conn.commit()
    conn.close()
    return path


class TestCodexDB:
    def test_list_threads_sorted_by_time(self, db_path):
        """Threads should be listed newest first."""
        db = CodexDB(db_path)
        rows = db.list_threads()
        assert len(rows) == 4
        assert rows[0].id == "id-001"  # created_at=1780132666 (newest)
        assert rows[-1].id == "id-004"  # created_at=1779938390 (oldest)
        db.close()

    def test_list_threads_filter_provider(self, db_path):
        """Filter by model_provider."""
        db = CodexDB(db_path)
        rows = db.list_threads(provider="packycode")
        assert len(rows) == 1
        assert rows[0].id == "id-003"
        db.close()

    def test_list_threads_filter_cwd(self, db_path):
        """Filter by cwd."""
        db = CodexDB(db_path)
        rows = db.list_threads(cwd="D:\\project1")
        assert len(rows) == 2
        db.close()

    def test_list_threads_filter_keyword(self, db_path):
        """Filter by title keyword."""
        db = CodexDB(db_path)
        rows = db.list_threads(keyword="爬虫")
        assert len(rows) == 1
        assert rows[0].id == "id-001"
        db.close()

    def test_list_threads_combined_filter(self, db_path):
        """Combined filters should narrow results."""
        db = CodexDB(db_path)
        rows = db.list_threads(provider="openai", cwd="D:\\project1")
        assert len(rows) == 1
        assert rows[0].id == "id-001"
        db.close()

    def test_get_distinct_providers(self, db_path):
        """Should return unique providers."""
        db = CodexDB(db_path)
        providers = db.get_distinct_providers()
        assert set(providers) == {"openai", "packycode"}
        db.close()

    def test_get_distinct_cwds(self, db_path):
        """Should return unique cwds."""
        db = CodexDB(db_path)
        cwds = db.get_distinct_cwds()
        assert set(cwds) == {"D:\\project1", "D:\\project2", "D:\\project3"}
        db.close()

    def test_update_provider(self, db_path):
        """Should update model_provider for given thread."""
        db = CodexDB(db_path)
        db.update_provider("id-001", "newprovider")
        rows = db.list_threads(provider="newprovider")
        assert len(rows) == 1
        assert rows[0].id == "id-001"
        db.close()

    def test_update_provider_batch(self, db_path):
        """Should update multiple threads at once."""
        db = CodexDB(db_path)
        db.update_provider_batch(["id-001", "id-002"], "batchprovider")
        rows = db.list_threads(provider="batchprovider")
        assert len(rows) == 2
        db.close()

    def test_delete_threads(self, db_path):
        """Should delete specified threads."""
        db = CodexDB(db_path)
        db.delete_threads(["id-001", "id-002"])
        rows = db.list_threads()
        assert len(rows) == 2
        db.close()

    def test_insert_thread(self, db_path):
        """Should insert a new thread record."""
        db = CodexDB(db_path)
        db.insert_thread(
            thread_id="id-new",
            rollout_path="/rollout/new.jsonl",
            created_at=1780200000,
            updated_at=1780200000,
            model_provider="copied",
            cwd="D:\\project4",
            title="复制的会话",
        )
        rows = db.list_threads(provider="copied")
        assert len(rows) == 1
        assert rows[0].id == "id-new"
        db.close()

    def test_thread_record_fields(self, db_path):
        """ThreadRecord should have correct fields."""
        db = CodexDB(db_path)
        rows = db.list_threads()
        r = rows[0]
        assert r.id == "id-001"
        assert r.title == "帮我写个爬虫"
        assert r.model_provider == "openai"
        assert r.cwd == "D:\\project1"
        assert r.created_at == 1780132666
        assert r.archived == 0
        db.close()

    def test_find_state_db(self, tmp_path):
        """Should find highest-version state_*.sqlite."""
        # Create multiple state DBs
        for name in ["state_3.sqlite", "state_5.sqlite", "state_1.sqlite"]:
            (tmp_path / name).touch()
        from core.database import find_state_db
        result = find_state_db(tmp_path)
        assert result.name == "state_5.sqlite"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_database.py -v`
Expected: FAIL (module `core.database` not found)

- [ ] **Step 3: Implement CodexDB**

```python
# core/database.py
"""SQLite operations for Codex threads database."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ThreadRecord:
    """A single thread record from the threads table."""
    id: str
    title: str
    model_provider: str
    cwd: str
    created_at: int
    updated_at: int
    archived: int
    rollout_path: str
    first_user_message: str
    preview: str


def find_state_db(codex_home: Path) -> Path | None:
    """Find the highest-version state_*.sqlite in codex_home."""
    if not codex_home.exists():
        return None
    pattern = re.compile(r"^state_(\d+)\.sqlite$")
    candidates: list[tuple[int, float, Path]] = []
    for path in codex_home.glob("state_*.sqlite"):
        match = pattern.match(path.name)
        if match:
            candidates.append((int(match.group(1)), path.stat().st_mtime, path))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][2]


class CodexDB:
    """Read/write wrapper for Codex state SQLite database."""

    def __init__(self, db_path: Path):
        self._path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self._conn.close()

    def list_threads(
        self,
        provider: str | None = None,
        cwd: str | None = None,
        keyword: str | None = None,
    ) -> list[ThreadRecord]:
        """List threads with optional filters, sorted by created_at DESC."""
        sql = "SELECT id, title, model_provider, cwd, created_at, updated_at, archived, rollout_path, first_user_message, preview FROM threads WHERE 1=1"
        params: list[str] = []

        if provider:
            sql += " AND model_provider = ?"
            params.append(provider)
        if cwd:
            sql += " AND cwd = ?"
            params.append(cwd)
        if keyword:
            sql += " AND title LIKE ?"
            params.append(f"%{keyword}%")

        sql += " ORDER BY created_at DESC"

        rows = self._conn.execute(sql, params).fetchall()
        return [
            ThreadRecord(
                id=row["id"],
                title=row["title"],
                model_provider=row["model_provider"],
                cwd=row["cwd"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                archived=row["archived"],
                rollout_path=row["rollout_path"],
                first_user_message=row["first_user_message"],
                preview=row["preview"],
            )
            for row in rows
        ]

    def get_distinct_providers(self) -> list[str]:
        """Return sorted list of unique model_provider values."""
        rows = self._conn.execute(
            "SELECT DISTINCT model_provider FROM threads ORDER BY model_provider"
        ).fetchall()
        return [row["model_provider"] for row in rows]

    def get_distinct_cwds(self) -> list[str]:
        """Return sorted list of unique cwd values."""
        rows = self._conn.execute(
            "SELECT DISTINCT cwd FROM threads ORDER BY cwd"
        ).fetchall()
        return [row["cwd"] for row in rows]

    def update_provider(self, thread_id: str, new_provider: str) -> None:
        """Update model_provider for a single thread."""
        self._conn.execute(
            "UPDATE threads SET model_provider = ? WHERE id = ?",
            (new_provider, thread_id),
        )
        self._conn.commit()

    def update_provider_batch(self, thread_ids: list[str], new_provider: str) -> None:
        """Update model_provider for multiple threads."""
        self._conn.executemany(
            "UPDATE threads SET model_provider = ? WHERE id = ?",
            [(new_provider, tid) for tid in thread_ids],
        )
        self._conn.commit()

    def delete_threads(self, thread_ids: list[str]) -> None:
        """Delete thread records by ID."""
        self._conn.executemany(
            "DELETE FROM threads WHERE id = ?",
            [(tid,) for tid in thread_ids],
        )
        self._conn.commit()

    def insert_thread(
        self,
        thread_id: str,
        rollout_path: str,
        created_at: int,
        updated_at: int,
        model_provider: str,
        cwd: str,
        title: str,
    ) -> None:
        """Insert a new thread record (for copy operation)."""
        self._conn.execute(
            "INSERT INTO threads (id, rollout_path, created_at, updated_at, source, "
            "model_provider, cwd, title, sandbox_policy, approval_mode) "
            "VALUES (?, ?, ?, ?, 'vscode', ?, ?, ?, 'sandbox', 'auto')",
            (thread_id, rollout_path, created_at, updated_at, model_provider, cwd, title),
        )
        self._conn.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_database.py -v`
Expected: All 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/database.py tests/test_database.py
git commit -m "feat: add database module with thread CRUD operations"
```

---

### Task 4: Rollout Module (`core/rollout.py`)

**Files:**
- Create: `core/rollout.py`
- Create: `tests/test_rollout.py`

- [ ] **Step 1: Write failing tests for RolloutManager**

```python
# tests/test_rollout.py
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rollout import RolloutManager


@pytest.fixture
def rollout_dir(tmp_path):
    """Create a directory with sample JSONL rollout files."""
    sessions = tmp_path / "sessions" / "2026" / "06" / "01"
    sessions.mkdir(parents=True)

    # Create a valid rollout file
    content_lines = [
        json.dumps({
            "type": "session_meta",
            "payload": {
                "id": "019e63db-18df-7ab3-a2b8-0936dcbaa368",
                "timestamp": "2026-05-26T10:36:08.702Z",
                "model_provider": "openai",
                "cwd": "D:\\project1",
            }
        }),
        json.dumps({"type": "user_message", "payload": {"text": "hello"}}),
        json.dumps({"type": "assistant_message", "payload": {"text": "hi there"}}),
    ]
    rollout_path = sessions / "rollout-2026-05-26T18-36-08-019e63db.jsonl"
    rollout_path.write_text("\n".join(content_lines), encoding="utf-8")

    # Create a second file
    content_lines2 = [
        json.dumps({
            "type": "session_meta",
            "payload": {
                "id": "019e782a-62a0-76d3-815b-b67f85459a04",
                "timestamp": "2026-05-30T17:15:04.702Z",
                "model_provider": "packycode",
                "cwd": "D:\\project2",
            }
        }),
    ]
    rollout_path2 = sessions / "rollout-2026-05-30T17-15-04-019e782a.jsonl"
    rollout_path2.write_text("\n".join(content_lines2), encoding="utf-8")

    return tmp_path, rollout_path, rollout_path2


class TestRolloutManager:
    def test_rewrite_provider(self, rollout_dir):
        """Should rewrite model_provider in session_meta."""
        tmp_path, rollout_path, _ = rollout_dir
        mgr = RolloutManager(tmp_path)
        count = mgr.rewrite_providers([str(rollout_path)], "newprovider")
        assert count == 1

        # Verify the file was changed
        lines = rollout_path.read_text(encoding="utf-8").splitlines()
        meta = json.loads(lines[0])
        assert meta["payload"]["model_provider"] == "newprovider"
        # Other lines should be unchanged
        assert json.loads(lines[1])["type"] == "user_message"

    def test_rewrite_provider_preserves_format(self, rollout_dir):
        """Rewrite should preserve JSONL format (one JSON per line)."""
        tmp_path, rollout_path, _ = rollout_dir
        mgr = RolloutManager(tmp_path)
        mgr.rewrite_providers([str(rollout_path)], "x")

        content = rollout_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        assert len(lines) == 3
        for line in lines:
            json.loads(line)  # should not raise

    def test_rewrite_provider_no_session_meta(self, tmp_path):
        """Files without session_meta should be skipped gracefully."""
        bad_file = tmp_path / "bad.jsonl"
        bad_file.write_text('{"type":"other","payload":{}}\n', encoding="utf-8")
        mgr = RolloutManager(tmp_path)
        count = mgr.rewrite_providers([str(bad_file)], "new")
        assert count == 0

    def test_copy_rollout(self, rollout_dir):
        """Should copy rollout file with new ID and provider."""
        tmp_path, rollout_path, _ = rollout_dir
        mgr = RolloutManager(tmp_path)
        new_path, new_id = mgr.copy_rollout(str(rollout_path), "copied_provider")
        assert Path(new_path).exists()
        assert new_id != "019e63db-18df-7ab3-a2b8-0936dcbaa368"

        lines = Path(new_path).read_text(encoding="utf-8").splitlines()
        meta = json.loads(lines[0])
        assert meta["payload"]["model_provider"] == "copied_provider"
        assert meta["payload"]["id"] == new_id

    def test_delete_rollout(self, rollout_dir):
        """Should delete rollout file."""
        tmp_path, rollout_path, _ = rollout_dir
        mgr = RolloutManager(tmp_path)
        mgr.delete_rollout(str(rollout_path))
        assert not rollout_path.exists()

    def test_delete_nonexistent(self, tmp_path):
        """Deleting non-existent file should not raise."""
        mgr = RolloutManager(tmp_path)
        mgr.delete_rollout(str(tmp_path / "nonexistent.jsonl"))  # no error

    def test_rewrite_multiple_files(self, rollout_dir):
        """Should rewrite provider across multiple files."""
        tmp_path, rp1, rp2 = rollout_dir
        mgr = RolloutManager(tmp_path)
        count = mgr.rewrite_providers([str(rp1), str(rp2)], "unified")
        assert count == 2

        for p in [rp1, rp2]:
            lines = p.read_text(encoding="utf-8").splitlines()
            meta = json.loads(lines[0])
            assert meta["payload"]["model_provider"] == "unified"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_rollout.py -v`
Expected: FAIL (module `core.rollout` not found)

- [ ] **Step 3: Implement RolloutManager**

```python
# core/rollout.py
"""JSONL rollout file operations for Codex sessions."""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path


class RolloutManager:
    """Manages Codex rollout JSONL files: rewrite provider, copy, delete."""

    def __init__(self, codex_home: Path):
        self._codex_home = codex_home

    def _resolve_path(self, rollout_path: str) -> Path:
        """Resolve rollout path (may be absolute or relative to codex_home)."""
        p = Path(rollout_path)
        if p.is_absolute():
            return p
        return self._codex_home / p

    def rewrite_providers(self, rollout_paths: list[str], new_provider: str) -> int:
        """Rewrite model_provider in session_meta for each JSONL file.

        Returns the number of files actually modified.
        """
        modified = 0
        for path_str in rollout_paths:
            path = self._resolve_path(path_str)
            if not path.exists():
                continue
            if self._rewrite_single(path, new_provider):
                modified += 1
        return modified

    def _rewrite_single(self, path: Path, new_provider: str) -> bool:
        """Rewrite a single JSONL file. Returns True if file was changed."""
        original = path.read_text(encoding="utf-8")
        newline_at_end = original.endswith("\n")
        lines = original.splitlines()
        new_lines: list[str] = []
        changed = False

        for line in lines:
            if not line.strip():
                new_lines.append(line)
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                new_lines.append(line)
                continue

            if isinstance(payload, dict) and payload.get("type") == "session_meta":
                session_meta = payload.get("payload")
                if isinstance(session_meta, dict) and "model_provider" in session_meta:
                    session_meta["model_provider"] = new_provider
                    payload["payload"] = session_meta
                    changed = True
                    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

            new_lines.append(line)

        if not changed:
            return False

        result = "\n".join(new_lines)
        if newline_at_end:
            result += "\n"
        path.write_text(result, encoding="utf-8")
        return True

    def copy_rollout(self, source_path: str, new_provider: str) -> tuple[str, str]:
        """Copy a rollout file with a new session ID and provider.

        Returns (new_file_path, new_session_id).
        """
        src = self._resolve_path(source_path)
        new_id = str(uuid.uuid4())
        # Build new filename preserving the original naming convention
        stem = src.stem  # e.g. "rollout-2026-05-26T18-36-08-019e63db"
        new_name = f"{stem}-copy-{new_id[:8]}.jsonl"
        dst = src.parent / new_name

        shutil.copy2(src, dst)

        # Rewrite the copy: new ID and provider
        content = dst.read_text(encoding="utf-8")
        lines = content.splitlines()
        new_lines: list[str] = []
        for line in lines:
            if not line.strip():
                new_lines.append(line)
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                new_lines.append(line)
                continue

            if isinstance(payload, dict) and payload.get("type") == "session_meta":
                session_meta = payload.get("payload")
                if isinstance(session_meta, dict):
                    session_meta["model_provider"] = new_provider
                    session_meta["id"] = new_id
                    payload["payload"] = session_meta
                    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

            new_lines.append(line)

        result = "\n".join(new_lines)
        if content.endswith("\n"):
            result += "\n"
        dst.write_text(result, encoding="utf-8")

        return str(dst), new_id

    def delete_rollout(self, rollout_path: str) -> None:
        """Delete a rollout file. No-op if file doesn't exist."""
        path = self._resolve_path(rollout_path)
        if path.exists():
            path.unlink()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_rollout.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add core/rollout.py tests/test_rollout.py
git commit -m "feat: add rollout module for JSONL file operations"
```

---

### Task 5: Theme Module (`ui/theme.py`)

**Files:**
- Create: `ui/theme.py`

- [ ] **Step 1: Implement theme detection**

```python
# ui/theme.py
"""Detect Windows system theme and map to ttkbootstrap theme."""
from __future__ import annotations

import sys


def detect_system_theme() -> str:
    """Detect if Windows is using light or dark theme.

    Returns:
        "darkly" for dark theme, "cosmo" for light theme.
        Defaults to "cosmo" if detection fails.
    """
    if sys.platform != "win32":
        return "cosmo"

    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return "darkly" if value == 0 else "cosmo"
    except (OSError, FileNotFoundError):
        return "cosmo"


def get_theme_name(preference: str) -> str:
    """Resolve theme name from user preference.

    Args:
        preference: "auto", "dark", or "light"

    Returns:
        ttkbootstrap theme name ("darkly" or "cosmo")
    """
    if preference == "dark":
        return "darkly"
    if preference == "light":
        return "cosmo"
    return detect_system_theme()
```

- [ ] **Step 2: Verify it works**

Run: `python -c "from ui.theme import detect_system_theme; print(detect_system_theme())"`
Expected: Prints "darkly" or "cosmo" depending on your system

- [ ] **Step 3: Commit**

```bash
git add ui/theme.py
git commit -m "feat: add Windows system theme detection"
```

---

### Task 6: CheckboxTreeview Widget (`ui/widgets.py`)

**Files:**
- Create: `ui/widgets.py`

- [ ] **Step 1: Implement CheckboxTreeview**

```python
# ui/widgets.py
"""Custom ttk/ttkbootstrap widgets for Codex Transfer."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable


class CheckboxTreeview(ttk.Treeview):
    """Treeview with a checkbox column for multi-selection.

    The first column displays checkboxes (☐ / ☑). Clicking toggles the state.
    Supports select-all, deselect-all, invert-selection, and get checked items.
    """

    def __init__(self, master: Any, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._checked: set[str] = set()  # set of item IDs
        self._checkbox_column: str = "#0"
        self.bind("<Button-1>", self._on_click, add=True)

    def _on_click(self, event: tk.Event) -> None:
        """Handle click to toggle checkbox."""
        region = self.identify_region(event.x, event.y)
        if region != "tree" and region != "cell":
            return

        column = self.identify_column(event.x)
        item = self.identify_row(event.y)
        if not item:
            return

        # Only toggle on first column (checkbox) or any column
        self.toggle_checked(item)

    def toggle_checked(self, item: str) -> None:
        """Toggle checkbox state for an item."""
        if item in self._checked:
            self._checked.discard(item)
            self._update_item_display(item, checked=False)
        else:
            self._checked.add(item)
            self._update_item_display(item, checked=True)

    def _update_item_display(self, item: str, checked: bool) -> None:
        """Update the visual checkbox indicator for an item."""
        values = list(self.item(item, "values"))
        if values:
            values[0] = "☑" if checked else "☐"
            self.item(item, values=values)

    def set_checked(self, item: str, checked: bool) -> None:
        """Explicitly set checked state."""
        if checked:
            self._checked.add(item)
        else:
            self._checked.discard(item)
        self._update_item_display(item, checked)

    def check_all(self) -> None:
        """Check all items."""
        for item in self.get_children():
            self._checked.add(item)
            self._update_item_display(item, checked=True)

    def uncheck_all(self) -> None:
        """Uncheck all items."""
        for item in self.get_children():
            self._checked.discard(item)
            self._update_item_display(item, checked=False)

    def invert_checked(self) -> None:
        """Invert checked state of all items."""
        for item in self.get_children():
            if item in self._checked:
                self._checked.discard(item)
                self._update_item_display(item, checked=False)
            else:
                self._checked.add(item)
                self._update_item_display(item, checked=True)

    def get_checked_ids(self) -> list[str]:
        """Return list of checked item IDs."""
        return [item for item in self._checked if item in self.get_children()]

    def clear_checked(self) -> None:
        """Clear all checked state."""
        for item in list(self._checked):
            if item in self.get_children():
                self._update_item_display(item, checked=False)
        self._checked.clear()

    def insert(self, parent: str, index: str | int = tk.END, **kwargs: Any) -> str:
        """Override insert to prepend checkbox column value."""
        # Ensure first value is the checkbox indicator
        values = kwargs.get("values", ())
        if isinstance(values, (list, tuple)):
            values = ("☐",) + tuple(values)
        kwargs["values"] = values
        return super().insert(parent, index, **kwargs)


class ScrollableFrame(ttk.Frame):
    """A frame with a vertical scrollbar."""

    def __init__(self, master: Any, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._inner = ttk.Frame(self._canvas)

        self._inner.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")
```

- [ ] **Step 2: Verify widget loads**

Run: `python -c "import tkinter; from ui.widgets import CheckboxTreeview; root = tkinter.Tk(); root.destroy(); print('OK')"`
Expected: Prints "OK"

- [ ] **Step 3: Commit**

```bash
git add ui/widgets.py
git commit -m "feat: add CheckboxTreeview and ScrollableFrame widgets"
```

---

### Task 7: Main Application Window (`ui/app.py`)

**Files:**
- Create: `ui/app.py`

This is the largest task. It wires together all modules into the full UI.

- [ ] **Step 1: Implement the main application window**

```python
# ui/app.py
"""Main application window for Codex Transfer."""
from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Any

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from core.config import Config
from core.database import CodexDB, ThreadRecord, find_state_db
from core.rollout import RolloutManager
from ui.widgets import CheckboxTreeview


# Column definitions: (id, header_text, width, anchor)
COLUMNS = [
    ("check", "☐", 40, "center"),
    ("title", "标题", 350, "w"),
    ("time", "时间", 150, "center"),
    ("cwd", "路径", 300, "w"),
    ("provider", "归属", 120, "center"),
    ("archived", "归档", 60, "center"),
]

SORT_COLUMNS = {"title", "time", "cwd", "provider"}  # columns sortable by click


class CodexTransferApp:
    """Main application window."""

    def __init__(self, root: ttk.Window, config: Config) -> None:
        self.root = root
        self.config = config
        self.db: CodexDB | None = None
        self.all_threads: list[ThreadRecord] = []
        self._sort_column: str = "time"
        self._sort_reverse: bool = True  # newest first by default

        self._setup_window()
        self._build_path_bar()
        self._build_filter_bar()
        self._build_table()
        self._build_action_bar()
        self._build_status_bar()
        self._load_data()

    def _setup_window(self) -> None:
        self.root.title("Codex Transfer v1.0.0")
        self.root.geometry(self.config.window_geometry)
        self.root.minsize(800, 500)

        # Save geometry on close
        def on_close() -> None:
            self.config.window_geometry = self.root.geometry()
            self.config.save()
            if self.db:
                self.db.close()
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_close)

    # ── Path bar ──────────────────────────────────────────────
    def _build_path_bar(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Codex 路径", padding=5)
        frame.pack(fill=X, padx=10, pady=(10, 5))

        self._path_var = tk.StringVar(value=str(self.config.codex_home))
        entry = ttk.Entry(frame, textvariable=self._path_var, state="readonly")
        entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))

        ttk.Button(frame, text="更改", command=self._browse_codex_home, bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(frame, text="刷新", command=self._load_data, bootstyle=INFO).pack(side=LEFT, padx=2)

    def _browse_codex_home(self) -> None:
        path = filedialog.askdirectory(title="选择 Codex 数据目录")
        if path:
            self.config.codex_home = __import__("pathlib").Path(path)
            self._path_var.set(path)
            self.config.save()
            self._load_data()

    # ── Filter bar ────────────────────────────────────────────
    def _build_filter_bar(self) -> None:
        frame = ttk.LabelFrame(self.root, text="筛选", padding=5)
        frame.pack(fill=X, padx=10, pady=5)

        # Provider filter
        ttk.Label(frame, text="归属:").pack(side=LEFT, padx=(0, 2))
        self._provider_var = tk.StringVar(value="全部")
        self._provider_combo = ttk.Combobox(frame, textvariable=self._provider_var, state="readonly", width=15)
        self._provider_combo.pack(side=LEFT, padx=(0, 10))
        self._provider_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # CWD filter
        ttk.Label(frame, text="路径:").pack(side=LEFT, padx=(0, 2))
        self._cwd_var = tk.StringVar(value="全部")
        self._cwd_combo = ttk.Combobox(frame, textvariable=self._cwd_var, state="readonly", width=30)
        self._cwd_combo.pack(side=LEFT, padx=(0, 10))
        self._cwd_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Keyword search
        ttk.Label(frame, text="标题:").pack(side=LEFT, padx=(0, 2))
        self._keyword_var = tk.StringVar()
        self._keyword_entry = ttk.Entry(frame, textvariable=self._keyword_var, width=25)
        self._keyword_entry.pack(side=LEFT, padx=(0, 5))
        self._keyword_entry.bind("<Return>", lambda e: self._apply_filters())
        ttk.Button(frame, text="🔍", command=self._apply_filters, bootstyle=SECONDARY, width=3).pack(side=LEFT)

    # ── Table ─────────────────────────────────────────────────
    def _build_table(self) -> None:
        frame = ttk.Frame(self.root)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        col_ids = [c[0] for c in COLUMNS]
        self.tree = CheckboxTreeview(frame, columns=col_ids[1:], show="headings", height=20)

        for col_id, header, width, anchor in COLUMNS:
            if col_id == "check":
                continue
            self.tree.heading(col_id, text=header, command=lambda c=col_id: self._sort_by(c))
            self.tree.column(col_id, width=width, anchor=anchor, minwidth=50)

        # Checkbox column (#0)
        self.tree.column("#0", width=40, anchor="center", stretch=False)
        self.tree.heading("#0", text="☐", command=self._toggle_select_all)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Double-click to copy title
        self.tree.bind("<Double-1>", self._on_double_click)

    def _toggle_select_all(self) -> None:
        """Toggle between select-all and deselect-all."""
        checked = self.tree.get_checked_ids()
        if len(checked) == len(self.tree.get_children()):
            self.tree.uncheck_all()
        else:
            self.tree.check_all()
        self._update_status()

    def _on_double_click(self, event: tk.Event) -> None:
        """Copy title to clipboard on double-click."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, "values")
        if values and len(values) > 1:
            title = values[1]  # title is second column (after checkbox)
            self.root.clipboard_clear()
            self.root.clipboard_append(title)
            self._show_toast(f"已复制: {title}")

    def _show_toast(self, message: str) -> None:
        """Show a brief toast message in status bar."""
        self._status_var.set(message)
        self.root.after(2000, self._update_status)

    # ── Action bar ────────────────────────────────────────────
    def _build_action_bar(self) -> None:
        frame = ttk.LabelFrame(self.root, text="操作", padding=5)
        frame.pack(fill=X, padx=10, pady=5)

        # Selection buttons
        sel_frame = ttk.Frame(frame)
        sel_frame.pack(fill=X, pady=(0, 5))
        ttk.Button(sel_frame, text="全选", command=self.tree.check_all, bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(sel_frame, text="全不选", command=self.tree.uncheck_all, bootstyle=SECONDARY).pack(side=LEFT, padx=2)
        ttk.Button(sel_frame, text="反选", command=self.tree.invert_checked, bootstyle=SECONDARY).pack(side=LEFT, padx=2)

        self._selected_var = tk.StringVar(value="已选 0 条")
        ttk.Label(sel_frame, textvariable=self._selected_var).pack(side=LEFT, padx=10)

        # Action buttons
        act_frame = ttk.Frame(frame)
        act_frame.pack(fill=X)

        # Move to existing provider
        ttk.Label(act_frame, text="移动到已有归属:").pack(side=LEFT, padx=(0, 2))
        self._move_provider_var = tk.StringVar()
        self._move_provider_combo = ttk.Combobox(act_frame, textvariable=self._move_provider_var, state="readonly", width=15)
        self._move_provider_combo.pack(side=LEFT, padx=(0, 5))
        ttk.Button(act_frame, text="移动", command=self._move_to_existing, bootstyle=WARNING).pack(side=LEFT, padx=2)

        ttk.Separator(act_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=5)

        # Move to new provider
        ttk.Button(act_frame, text="移动到新归属", command=self._move_to_new, bootstyle=WARNING).pack(side=LEFT, padx=2)

        ttk.Separator(act_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=5)

        # Copy to existing provider
        ttk.Label(act_frame, text="复制到已有归属:").pack(side=LEFT, padx=(0, 2))
        self._copy_provider_var = tk.StringVar()
        self._copy_provider_combo = ttk.Combobox(act_frame, textvariable=self._copy_provider_var, state="readonly", width=15)
        self._copy_provider_combo.pack(side=LEFT, padx=(0, 5))
        ttk.Button(act_frame, text="复制", command=self._copy_to_existing, bootstyle=SUCCESS).pack(side=LEFT, padx=2)

        ttk.Separator(act_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=5)

        # Copy to new provider
        ttk.Button(act_frame, text="复制到新归属", command=self._copy_to_new, bootstyle=SUCCESS).pack(side=LEFT, padx=2)

        ttk.Separator(act_frame, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=5)

        # Delete
        ttk.Button(act_frame, text="删除选中", command=self._delete_selected, bootstyle=DANGER).pack(side=LEFT, padx=2)

    # ── Status bar ────────────────────────────────────────────
    def _build_status_bar(self) -> None:
        frame = ttk.Frame(self.root)
        frame.pack(fill=X, padx=10, pady=(0, 10))
        self._status_var = tk.StringVar(value="就绪")
        ttk.Label(frame, textvariable=self._status_var, anchor=W).pack(side=LEFT, fill=X, expand=True)

    # ── Data loading ──────────────────────────────────────────
    def _load_data(self) -> None:
        """Load threads from SQLite and populate UI."""
        if self.db:
            self.db.close()
            self.db = None

        codex_home = self.config.codex_home
        db_path = find_state_db(codex_home)
        if db_path is None:
            messagebox.showerror("错误", f"未找到 state_*.sqlite 文件。\n请检查 Codex 路径: {codex_home}")
            return

        try:
            self.db = CodexDB(db_path)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开数据库:\n{e}")
            return

        # Populate filter dropdowns
        providers = self.db.get_distinct_providers()
        self._provider_combo["values"] = ["全部"] + providers
        self._provider_var.set("全部")

        cwds = self.db.get_distinct_cwds()
        self._cwd_combo["values"] = ["全部"] + cwds
        self._cwd_var.set("全部")

        # Populate action dropdowns
        self._move_provider_combo["values"] = providers
        self._copy_provider_combo["values"] = providers
        if providers:
            self._move_provider_var.set(providers[0])
            self._copy_provider_var.set(providers[0])

        self._keyword_var.set("")
        self._apply_filters()

    def _apply_filters(self) -> None:
        """Query DB with current filter settings and refresh table."""
        if not self.db:
            return

        provider = self._provider_var.get()
        cwd = self._cwd_var.get()
        keyword = self._keyword_var.get().strip()

        self.all_threads = self.db.list_threads(
            provider=provider if provider != "全部" else None,
            cwd=cwd if cwd != "全部" else None,
            keyword=keyword if keyword else None,
        )
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Repopulate the Treeview with current data."""
        self.tree.clear_checked()
        for item in self.tree.get_children():
            self.tree.delete(item)

        threads = self._sorted_threads()
        for t in threads:
            time_str = datetime.datetime.fromtimestamp(t.created_at).strftime("%Y-%m-%d %H:%M")
            archived_str = "✓" if t.archived else ""
            self.tree.insert(
                "", END, iid=t.id,
                values=(t.title, time_str, t.cwd, t.model_provider, archived_str),
            )

        self._update_status()

    def _sorted_threads(self) -> list[ThreadRecord]:
        """Sort threads by current sort column."""
        col = self._sort_column
        reverse = self._sort_reverse

        def sort_key(t: ThreadRecord) -> Any:
            if col == "time":
                return t.created_at
            if col == "title":
                return t.title.lower()
            if col == "cwd":
                return t.cwd.lower()
            if col == "provider":
                return t.model_provider.lower()
            return t.created_at

        return sorted(self.all_threads, key=sort_key, reverse=reverse)

    def _sort_by(self, column: str) -> None:
        """Sort table by column. Toggle direction if same column."""
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = True
        self._refresh_table()

    def _update_status(self) -> None:
        """Update status bar text."""
        total = len(self.all_threads)
        checked = len(self.tree.get_checked_ids())
        self._selected_var.set(f"已选 {checked} 条")

        if self.db:
            providers = self.db.get_distinct_providers()
            dist_parts = []
            for p in providers:
                count = sum(1 for t in self.all_threads if t.model_provider == p)
                dist_parts.append(f"{p}({count})")
            dist = ", ".join(dist_parts) if dist_parts else "无数据"
            self._status_var.set(f"共 {total} 条消息 | 归属分布: {dist}")
        else:
            self._status_var.set(f"共 {total} 条消息")

    # ── Operations ────────────────────────────────────────────
    def _get_selected_threads(self) -> list[ThreadRecord]:
        """Get ThreadRecord objects for checked items."""
        checked_ids = self.tree.get_checked_ids()
        id_map = {t.id: t for t in self.all_threads}
        return [id_map[cid] for cid in checked_ids if cid in id_map]

    def _get_rollout_manager(self) -> RolloutManager:
        return RolloutManager(self.config.codex_home)

    def _move_to_existing(self) -> None:
        """Move selected threads to an existing provider."""
        threads = self._get_selected_threads()
        if not threads:
            messagebox.showinfo("提示", "请先选择要移动的消息")
            return

        target = self._move_provider_var.get()
        if not target:
            messagebox.showinfo("提示", "请选择目标归属")
            return

        if not messagebox.askyesno("确认", f"确定将 {len(threads)} 条消息移动到归属 '{target}'？"):
            return

        mgr = self._get_rollout_manager()
        errors = []
        for t in threads:
            try:
                self.db.update_provider(t.id, target)
                mgr.rewrite_providers([t.rollout_path], target)
            except Exception as e:
                errors.append(f"{t.title}: {e}")

        if errors:
            messagebox.showwarning("部分失败", "\n".join(errors[:10]))
        self._load_data()

    def _move_to_new(self) -> None:
        """Move selected threads to a new provider."""
        threads = self._get_selected_threads()
        if not threads:
            messagebox.showinfo("提示", "请先选择要移动的消息")
            return

        new_provider = self._ask_provider_name("移动到新归属")
        if not new_provider:
            return

        # Check if provider already exists
        existing = self.db.get_distinct_providers()
        if new_provider in existing:
            messagebox.showinfo("提示", f"归属 '{new_provider}' 已存在，请使用'移动到已有归属'")
            return

        mgr = self._get_rollout_manager()
        errors = []
        for t in threads:
            try:
                self.db.update_provider(t.id, new_provider)
                mgr.rewrite_providers([t.rollout_path], new_provider)
            except Exception as e:
                errors.append(f"{t.title}: {e}")

        if errors:
            messagebox.showwarning("部分失败", "\n".join(errors[:10]))
        self._load_data()

    def _copy_to_existing(self) -> None:
        """Copy selected threads to an existing provider."""
        threads = self._get_selected_threads()
        if not threads:
            messagebox.showinfo("提示", "请先选择要复制的消息")
            return

        target = self._copy_provider_var.get()
        if not target:
            messagebox.showinfo("提示", "请选择目标归属")
            return

        if not messagebox.askyesno("确认", f"确定将 {len(threads)} 条消息复制到归属 '{target}'？"):
            return

        import time
        mgr = self._get_rollout_manager()
        errors = []
        for t in threads:
            try:
                new_path, new_id = mgr.copy_rollout(t.rollout_path, target)
                now = int(time.time())
                self.db.insert_thread(
                    thread_id=new_id,
                    rollout_path=new_path,
                    created_at=now,
                    updated_at=now,
                    model_provider=target,
                    cwd=t.cwd,
                    title=t.title,
                )
            except Exception as e:
                errors.append(f"{t.title}: {e}")

        if errors:
            messagebox.showwarning("部分失败", "\n".join(errors[:10]))
        self._load_data()

    def _copy_to_new(self) -> None:
        """Copy selected threads to a new provider."""
        threads = self._get_selected_threads()
        if not threads:
            messagebox.showinfo("提示", "请先选择要复制的消息")
            return

        new_provider = self._ask_provider_name("复制到新归属")
        if not new_provider:
            return

        existing = self.db.get_distinct_providers()
        if new_provider in existing:
            messagebox.showinfo("提示", f"归属 '{new_provider}' 已存在，请使用'复制到已有归属'")
            return

        import time
        mgr = self._get_rollout_manager()
        errors = []
        for t in threads:
            try:
                new_path, new_id = mgr.copy_rollout(t.rollout_path, new_provider)
                now = int(time.time())
                self.db.insert_thread(
                    thread_id=new_id,
                    rollout_path=new_path,
                    created_at=now,
                    updated_at=now,
                    model_provider=new_provider,
                    cwd=t.cwd,
                    title=t.title,
                )
            except Exception as e:
                errors.append(f"{t.title}: {e}")

        if errors:
            messagebox.showwarning("部分失败", "\n".join(errors[:10]))
        self._load_data()

    def _delete_selected(self) -> None:
        """Delete selected threads and their rollout files."""
        threads = self._get_selected_threads()
        if not threads:
            messagebox.showinfo("提示", "请先选择要删除的消息")
            return

        if not messagebox.askyesno("确认删除", f"确定删除 {len(threads)} 条消息？\n此操作不可恢复！", icon="warning"):
            return

        mgr = self._get_rollout_manager()
        errors = []
        thread_ids = []
        for t in threads:
            try:
                mgr.delete_rollout(t.rollout_path)
                thread_ids.append(t.id)
            except Exception as e:
                errors.append(f"{t.title}: {e}")

        if thread_ids:
            self.db.delete_threads(thread_ids)

        if errors:
            messagebox.showwarning("部分失败", "\n".join(errors[:10]))
        self._load_data()

    def _ask_provider_name(self, title: str) -> str | None:
        """Show dialog asking user to input a new provider name."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("350x120")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="请输入新的归属名称:").pack(pady=(15, 5))
        var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=var, width=30)
        entry.pack(pady=5)
        entry.focus_set()

        result: list[str | None] = [None]

        def on_ok() -> None:
            name = var.get().strip()
            if name:
                result[0] = name
                dialog.destroy()

        def on_cancel() -> None:
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定", command=on_ok, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=on_cancel, bootstyle=SECONDARY).pack(side=LEFT, padx=5)

        entry.bind("<Return>", lambda e: on_ok())
        dialog.bind("<Escape>", lambda e: on_cancel())

        self.root.wait_window(dialog)
        return result[0]
```

- [ ] **Step 2: Verify app module loads without errors**

Run: `python -c "from ui.app import CodexTransferApp; print('OK')"`
Expected: Prints "OK"

- [ ] **Step 3: Commit**

```bash
git add ui/app.py
git commit -m "feat: add main application window with all UI components"
```

---

### Task 8: Entry Point with Single Instance (`main.py`)

**Files:**
- Create: `main.py`

- [ ] **Step 1: Implement single-instance mutex and app launch**

```python
# main.py
"""Codex Transfer - Entry point with single-instance detection."""
from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from pathlib import Path

# Windows single-instance constants
MUTEX_NAME = "CodexTransfer_SingleInstance"
ERROR_ALREADY_EXISTS = 183


def check_single_instance() -> bool:
    """Check if another instance is already running.

    Returns True if this is the only instance, False if another exists.
    If another instance exists, activates its window and exits.
    """
    if sys.platform != "win32":
        return True

    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = ctypes.windll.kernel32.GetLastError()

    if last_error == ERROR_ALREADY_EXISTS:
        # Another instance is running — try to activate its window
        _activate_existing_window()
        return False

    return True


def _activate_existing_window() -> None:
    """Find and activate the existing Codex Transfer window."""
    try:
        import win32gui
        import win32con

        def enum_callback(hwnd: int, results: list[int]) -> bool:
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if "Codex Transfer" in title:
                    results.append(hwnd)
            return True

        results: list[int] = []
        win32gui.EnumWindows(enum_callback, results)

        if results:
            hwnd = results[0]
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
    except ImportError:
        # win32gui not available; use ctypes fallback
        _activate_with_ctypes()


def _activate_with_ctypes() -> None:
    """Fallback: activate window using ctypes."""
    try:
        user32 = ctypes.windll.user32

        # Find window by title
        hwnd = user32.FindWindowW(None, "Codex Transfer v1.0.0")
        if hwnd:
            # SW_RESTORE = 9
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def main() -> None:
    """Application entry point."""
    # Single-instance check
    if not check_single_instance():
        sys.exit(0)

    # Late imports to speed up single-instance check
    import ttkbootstrap as ttk

    from core.config import Config
    from ui.theme import get_theme_name
    from ui.app import CodexTransferApp

    # Load config
    config = Config()

    # Resolve theme
    theme_name = get_theme_name(config.theme)

    # Create main window
    root = ttk.Window(themename=theme_name)

    # Set window icon if available
    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    if icon_path.exists():
        root.iconbitmap(str(icon_path))

    # Launch app
    app = CodexTransferApp(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify entry point loads**

Run: `python -c "from main import check_single_instance; print('Import OK')"`
Expected: Prints "Import OK"

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add entry point with single-instance mutex detection"
```

---

### Task 9: Icon Conversion

**Files:**
- Create: `assets/convert_icon.py`
- Create: `assets/icon.ico` (generated)

- [ ] **Step 1: Create icon conversion script**

```python
# assets/convert_icon.py
"""Convert PNG icon to multi-size ICO for PyInstaller."""
from pathlib import Path
from PIL import Image


def convert_png_to_ico(png_path: str, ico_path: str) -> None:
    """Convert a PNG file to ICO with multiple sizes."""
    img = Image.open(png_path)

    # Generate multiple sizes for Windows icon
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    icons = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icons.append(resized)

    # Save as ICO
    icons[0].save(
        ico_path,
        format="ICO",
        sizes=[(icon.width, icon.height) for icon in icons],
        append_images=icons[1:],
    )
    print(f"Created {ico_path} with sizes: {[s for s in sizes]}")


if __name__ == "__main__":
    source = r"D:\edge_load\ChatGPT_Image_2026年6月7日_11_17_53.png"
    target = str(Path(__file__).parent / "icon.ico")
    convert_png_to_ico(source, target)
```

- [ ] **Step 2: Run the conversion**

Run: `python assets/convert_icon.py`
Expected: `Created assets/icon.ico with sizes: [(16, 16), (32, 32), (48, 48), (256, 256)]`

- [ ] **Step 3: Verify icon file exists**

Run: `python -c "from pathlib import Path; p = Path('assets/icon.ico'); print(f'Exists: {p.exists()}, Size: {p.stat().st_size}')"`
Expected: `Exists: True, Size: <some bytes>`

- [ ] **Step 4: Commit**

```bash
git add assets/convert_icon.py assets/icon.ico
git commit -m "feat: add app icon converted from PNG"
```

---

### Task 10: Build Script (`build.py`)

**Files:**
- Create: `build.py`

- [ ] **Step 1: Create PyInstaller build script**

```python
# build.py
"""Build Codex Transfer into a standalone .exe using PyInstaller."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def build() -> None:
    """Run PyInstaller to create a single-file windowed exe."""
    project_dir = Path(__file__).parent
    icon_path = project_dir / "assets" / "icon.ico"
    main_script = project_dir / "main.py"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "CodexTransfer",
        "--clean",
    ]

    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    # Add hidden imports that PyInstaller might miss
    cmd.extend([
        "--hidden-import", "ttkbootstrap",
        "--hidden-import", "PIL",
        "--hidden-import", "sqlite3",
    ])

    cmd.append(str(main_script))

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(project_dir))

    if result.returncode == 0:
        exe_path = project_dir / "dist" / "CodexTransfer.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\nBuild successful: {exe_path} ({size_mb:.1f} MB)")
        else:
            print("\nBuild completed but exe not found at expected path")
    else:
        print(f"\nBuild failed with exit code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()
```

- [ ] **Step 2: Verify build script loads**

Run: `python -c "from build import build; print('OK')"`
Expected: Prints "OK"

- [ ] **Step 3: Commit**

```bash
git add build.py
git commit -m "feat: add PyInstaller build script"
```

---

### Task 11: README Documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

```markdown
# Codex Transfer v1.0.0

轻量级 Windows 桌面应用，用于管理 Codex 聊天历史记录。

## 功能

- 📋 浏览所有 Codex 聊天记录（标题、时间、路径、归属）
- 🔍 按归属、项目路径、标题关键字筛选
- 📦 批量移动消息归属（修改 model_provider）
- 📋 批量复制消息到新归属（复制 JSONL 文件 + 新建记录）
- 🗑️ 批量删除消息（同时删除文件和记录）
- 🌙 暗色/亮色主题跟随系统
- 🔒 防止软件多开

## 使用

### 直接运行（开发模式）

```bash
pip install ttkbootstrap Pillow
python main.py
```

### 构建 exe

```bash
pip install -r requirements.txt
python build.py
```

构建完成后，exe 文件位于 `dist/CodexTransfer.exe`。

## 配置

- 配置文件位置：`%APPDATA%/CodexTransfer/config.json`
- 默认 Codex 路径：`~/.codex`
- 可通过 UI 更改 Codex 路径

## 数据说明

- 读取 `state_*.sqlite` 中的 `threads` 表
- 修改归属时同时更新 SQLite 和 JSONL 文件
- 复制时创建新的 JSONL 文件和 SQLite 记录
- 删除时同时移除文件和记录

## 版本历史

- v1.0.0 (2026-06-07) — 初始版本
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with usage instructions"
```

---

### Task 12: Integration Verification

**Files:**
- None (verification only)

- [ ] **Step 1: Run all unit tests**

Run: `python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 2: Verify app launches (smoke test)**

Run: `timeout 5 python main.py || true`
Expected: App window appears briefly (may timeout, that's OK)

- [ ] **Step 3: Verify imports are clean**

Run: `python -c "from main import main; from ui.app import CodexTransferApp; from core.database import CodexDB; from core.rollout import RolloutManager; from core.config import Config; print('All imports OK')"`
Expected: `All imports OK`

- [ ] **Step 4: Build the exe**

Run: `python build.py`
Expected: `Build successful: dist/CodexTransfer.exe (~25-35 MB)`

- [ ] **Step 5: Verify exe runs**

Run: `.\dist\CodexTransfer.exe` (double-click or from terminal)
Expected: App window opens with correct icon and theme

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "chore: final integration verification complete"
```

---

## Summary

| Task | Component | Files | Tests |
|------|-----------|-------|-------|
| 1 | Scaffolding | requirements.txt, __init__.py × 3 | — |
| 2 | Config | core/config.py | 5 tests |
| 3 | Database | core/database.py | 13 tests |
| 4 | Rollout | core/rollout.py | 7 tests |
| 5 | Theme | ui/theme.py | — |
| 6 | Widgets | ui/widgets.py | — |
| 7 | App Window | ui/app.py | — |
| 8 | Entry Point | main.py | — |
| 9 | Icon | assets/convert_icon.py, icon.ico | — |
| 10 | Build | build.py | — |
| 11 | Docs | README.md | — |
| 12 | Verification | — | smoke test |
