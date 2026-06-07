# tests/test_rollout.py
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rollout import RolloutManager


@pytest.fixture
def rollout_dir(tmp_path):
    sessions = tmp_path / "sessions" / "2026" / "06" / "01"
    sessions.mkdir(parents=True)

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
        tmp_path, rollout_path, _ = rollout_dir
        mgr = RolloutManager(tmp_path)
        count = mgr.rewrite_providers([str(rollout_path)], "newprovider")
        assert count == 1
        lines = rollout_path.read_text(encoding="utf-8").splitlines()
        meta = json.loads(lines[0])
        assert meta["payload"]["model_provider"] == "newprovider"
        assert json.loads(lines[1])["type"] == "user_message"

    def test_rewrite_provider_preserves_format(self, rollout_dir):
        tmp_path, rollout_path, _ = rollout_dir
        mgr = RolloutManager(tmp_path)
        mgr.rewrite_providers([str(rollout_path)], "x")
        content = rollout_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        assert len(lines) == 3
        for line in lines:
            json.loads(line)

    def test_rewrite_provider_no_session_meta(self, tmp_path):
        bad_file = tmp_path / "bad.jsonl"
        bad_file.write_text('{"type":"other","payload":{}}\n', encoding="utf-8")
        mgr = RolloutManager(tmp_path)
        count = mgr.rewrite_providers([str(bad_file)], "new")
        assert count == 0

    def test_copy_rollout(self, rollout_dir):
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
        tmp_path, rollout_path, _ = rollout_dir
        mgr = RolloutManager(tmp_path)
        mgr.delete_rollout(str(rollout_path))
        assert not rollout_path.exists()

    def test_delete_nonexistent(self, tmp_path):
        mgr = RolloutManager(tmp_path)
        mgr.delete_rollout(str(tmp_path / "nonexistent.jsonl"))

    def test_rewrite_multiple_files(self, rollout_dir):
        tmp_path, rp1, rp2 = rollout_dir
        mgr = RolloutManager(tmp_path)
        count = mgr.rewrite_providers([str(rp1), str(rp2)], "unified")
        assert count == 2
        for p in [rp1, rp2]:
            lines = p.read_text(encoding="utf-8").splitlines()
            meta = json.loads(lines[0])
            assert meta["payload"]["model_provider"] == "unified"
