# core/rollout.py
"""JSONL rollout file operations for Codex sessions."""
from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path


class RolloutManager:
    def __init__(self, codex_home: Path):
        self._codex_home = codex_home

    def _resolve_path(self, rollout_path: str) -> Path:
        p = Path(rollout_path)
        if p.is_absolute():
            return p
        return self._codex_home / p

    def rewrite_providers(self, rollout_paths: list[str], new_provider: str) -> int:
        modified = 0
        for path_str in rollout_paths:
            path = self._resolve_path(path_str)
            if not path.exists():
                continue
            if self._rewrite_single(path, new_provider):
                modified += 1
        return modified

    def _rewrite_single(self, path: Path, new_provider: str) -> bool:
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
        src = self._resolve_path(source_path)
        new_id = str(uuid.uuid4())
        # Generate filename in same format as Codex Desktop: rollout-YYYY-MM-DDTHH-MM-SS-THREADID.jsonl
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        new_name = f"rollout-{timestamp}-{new_id}.jsonl"
        dst = src.parent / new_name
        shutil.copy2(src, dst)
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
        path = self._resolve_path(rollout_path)
        if path.exists():
            path.unlink()
