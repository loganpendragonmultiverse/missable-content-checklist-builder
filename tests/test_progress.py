import copy
import json

import pytest

from missable_content_checklist_builder.cli import main
from missable_content_checklist_builder.core import build_report, load_progress, render_markdown


def guide():
    return {
        "version": 1,
        "guide_id": "guide-one",
        "game": "Game",
        "milestones": ["Now", "Later"],
        "items": [
            {
                "id": "a",
                "title": "A",
                "category": "quest",
                "status": "done",
                "available": "Now",
                "deadline": "Now",
                "details": "secret",
            },
            {
                "id": "future",
                "title": "Future",
                "category": "quest",
                "status": "pending",
                "available": "Later",
            },
        ],
    }


def overlay(states):
    return {"version": 1, "guide_id": "guide-one", "playthrough": "Second", "states": states}


def test_overlay_precedence_future_exclusion_due_counts_and_no_mutation():
    data = guide()
    original = copy.deepcopy(data)
    report = build_report(data, "Now", progress=overlay({"a": "pending", "future": "done"}))
    assert report["visible_count"] == 1 and report["overdue_count"] == 1
    assert report["counts"] == {"pending": 1}
    assert "details" not in report["items"][0]
    assert data == original
    assert "Second" in render_markdown(report)
    assert build_report(data, "Now")["counts"] == {"done": 1}
    for state in ("done", "skipped"):
        assert build_report(data, "Now", progress=overlay({"a": state}))["overdue_count"] == 0


@pytest.mark.parametrize(
    "change",
    [
        {"guide_id": "wrong"},
        {"version": 2},
        {"playthrough": ""},
        {"states": {"unknown": "done"}},
        {"states": {"a": "invalid"}},
        {"states": []},
        {"states": {"a": []}},
    ],
)
def test_invalid_progress_rejected(change):
    with pytest.raises((ValueError, TypeError)):
        build_report(guide(), "Now", progress={**overlay({}), **change})


def test_progress_cli_keeps_source_unchanged(tmp_path, capsys):
    source, progress = tmp_path / "guide.json", tmp_path / "progress.json"
    source.write_text(json.dumps(guide()))
    progress.write_text(json.dumps(overlay({"a": "pending"})))
    before = source.read_bytes()
    assert (
        main([str(source), "--through", "Now", "--progress", str(progress), "--format", "json"])
        == 0
    )
    assert json.loads(capsys.readouterr().out)["overdue_count"] == 1
    assert source.read_bytes() == before
    progress.write_text("[]")
    with pytest.raises((ValueError, TypeError)):
        load_progress(progress)
