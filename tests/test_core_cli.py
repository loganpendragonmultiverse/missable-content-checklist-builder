import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from missable_content_checklist_builder.cli import main
from missable_content_checklist_builder.core import build_report, load_checklist, render_markdown


def checklist() -> dict[str, Any]:
    return {
        "version": 1,
        "game": "North Road",
        "milestones": ["Arrival", "Finale", "Pass"],
        "items": [
            {
                "id": "letter",
                "title": "Read letter",
                "category": "lore",
                "available": "Arrival",
                "deadline": "Finale",
                "status": "pending",
                "details": "On the shelf",
            },
            {
                "id": "cache",
                "title": "Open cache",
                "category": "item",
                "available": "Pass",
                "status": "pending",
            },
        ],
    }


def write(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_boundary_deadline_and_details() -> None:
    report = build_report(checklist(), "Finale")
    assert report["visible_count"] == 1
    assert report["overdue_count"] == 1
    assert "details" not in report["items"][0]
    detailed = build_report(checklist(), "Finale", True)
    assert "On the shelf" in render_markdown(detailed)
    with pytest.raises(ValueError, match="unknown milestone"):
        build_report(checklist(), "Missing")


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda data: data.update(version=2), "version 1"),
        (lambda data: data.update(game=""), "game name"),
        (lambda data: data.update(milestones=[]), "non-empty"),
        (lambda data: data["milestones"].append("Arrival"), "unique"),
        (lambda data: data.update(items="bad"), "items must"),
        (lambda data: data["items"].append(data["items"][0].copy()), "duplicate"),
        (lambda data: data["items"][0].update(status="bad"), "invalid status"),
        (lambda data: data["items"][0].update(available="Missing"), "unknown availability"),
        (lambda data: data["items"][0].update(deadline="Missing"), "unknown deadline"),
        (lambda data: data["items"][0].update(available="Pass", deadline="Finale"), "precedes"),
        (lambda data: data["items"][0].update(details=4), "details must"),
    ],
)
def test_validation(tmp_path: Path, change: Callable[[dict[str, Any]], None], message: str) -> None:
    data = checklist()
    change(data)
    path = tmp_path / "checklist.json"
    write(path, data)
    with pytest.raises((TypeError, ValueError), match=message):
        load_checklist(path)


def test_cli_json_and_safe_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "checklist.json"
    write(path, checklist())
    assert main([str(path), "--through", "Arrival", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["visible_count"] == 1
    output = tmp_path / "report.md"
    assert main([str(path), "--through", "Arrival", "--output", str(output)]) == 0
    assert main([str(path), "--through", "Arrival", "--output", str(output)]) == 2
