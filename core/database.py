# core/database.py
"""SQLite operations for Codex threads database."""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ThreadRecord:
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
    def __init__(self, db_path: Path):
        self._path = db_path
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self._conn.close()

    def list_threads(self, provider=None, cwd=None, keyword=None) -> list[ThreadRecord]:
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
        return [ThreadRecord(id=row["id"], title=row["title"], model_provider=row["model_provider"], cwd=row["cwd"], created_at=row["created_at"], updated_at=row["updated_at"], archived=row["archived"], rollout_path=row["rollout_path"], first_user_message=row["first_user_message"], preview=row["preview"]) for row in rows]

    def get_distinct_providers(self) -> list[str]:
        rows = self._conn.execute("SELECT DISTINCT model_provider FROM threads ORDER BY model_provider").fetchall()
        return [row["model_provider"] for row in rows]

    def get_distinct_cwds(self) -> list[str]:
        rows = self._conn.execute("SELECT DISTINCT cwd FROM threads ORDER BY cwd").fetchall()
        return [row["cwd"] for row in rows]

    def update_provider(self, thread_id: str, new_provider: str) -> None:
        self._conn.execute("UPDATE threads SET model_provider = ? WHERE id = ?", (new_provider, thread_id))
        self._conn.commit()

    def update_provider_batch(self, thread_ids: list[str], new_provider: str) -> None:
        self._conn.executemany("UPDATE threads SET model_provider = ? WHERE id = ?", [(new_provider, tid) for tid in thread_ids])
        self._conn.commit()

    def delete_threads(self, thread_ids: list[str]) -> None:
        self._conn.executemany("DELETE FROM threads WHERE id = ?", [(tid,) for tid in thread_ids])
        self._conn.commit()

    def insert_thread(self, thread_id: str, rollout_path: str, created_at: int, updated_at: int, model_provider: str, cwd: str, title: str) -> None:
        self._conn.execute(
            "INSERT INTO threads (id, rollout_path, created_at, updated_at, source, model_provider, cwd, title, sandbox_policy, approval_mode) VALUES (?, ?, ?, ?, 'vscode', ?, ?, ?, 'sandbox', 'auto')",
            (thread_id, rollout_path, created_at, updated_at, model_provider, cwd, title),
        )
        self._conn.commit()
