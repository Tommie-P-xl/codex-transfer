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
        db = CodexDB(db_path)
        rows = db.list_threads()
        assert len(rows) == 4
        assert rows[0].id == "id-001"
        assert rows[-1].id == "id-004"
        db.close()

    def test_list_threads_filter_provider(self, db_path):
        db = CodexDB(db_path)
        rows = db.list_threads(provider="packycode")
        assert len(rows) == 1
        assert rows[0].id == "id-003"
        db.close()

    def test_list_threads_filter_cwd(self, db_path):
        db = CodexDB(db_path)
        rows = db.list_threads(cwd="D:\\project1")
        assert len(rows) == 2
        db.close()

    def test_list_threads_filter_keyword(self, db_path):
        db = CodexDB(db_path)
        rows = db.list_threads(keyword="爬虫")
        assert len(rows) == 1
        assert rows[0].id == "id-001"
        db.close()

    def test_list_threads_combined_filter(self, db_path):
        db = CodexDB(db_path)
        rows = db.list_threads(provider="openai", cwd="D:\\project1")
        assert len(rows) == 1
        assert rows[0].id == "id-001"
        db.close()

    def test_get_distinct_providers(self, db_path):
        db = CodexDB(db_path)
        providers = db.get_distinct_providers()
        assert set(providers) == {"openai", "packycode"}
        db.close()

    def test_get_distinct_cwds(self, db_path):
        db = CodexDB(db_path)
        cwds = db.get_distinct_cwds()
        assert set(cwds) == {"D:\\project1", "D:\\project2", "D:\\project3"}
        db.close()

    def test_update_provider(self, db_path):
        db = CodexDB(db_path)
        db.update_provider("id-001", "newprovider")
        rows = db.list_threads(provider="newprovider")
        assert len(rows) == 1
        assert rows[0].id == "id-001"
        db.close()

    def test_update_provider_batch(self, db_path):
        db = CodexDB(db_path)
        db.update_provider_batch(["id-001", "id-002"], "batchprovider")
        rows = db.list_threads(provider="batchprovider")
        assert len(rows) == 2
        db.close()

    def test_delete_threads(self, db_path):
        db = CodexDB(db_path)
        db.delete_threads(["id-001", "id-002"])
        rows = db.list_threads()
        assert len(rows) == 2
        db.close()

    def test_insert_thread(self, db_path):
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
        for name in ["state_3.sqlite", "state_5.sqlite", "state_1.sqlite"]:
            (tmp_path / name).touch()
        from core.database import find_state_db
        result = find_state_db(tmp_path)
        assert result.name == "state_5.sqlite"
