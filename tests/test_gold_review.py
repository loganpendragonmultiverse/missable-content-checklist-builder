import copy
import json

import pytest

from missable_content_checklist_builder.core import build_report, render_markdown


def guide():
    return {
        "version": 1,
        "game": "Game",
        "guide_id": "guide",
        "milestones": ["Now", "Later"],
        "items": [
            {
                "id": "a",
                "title": "A",
                "category": "quest",
                "status": "pending",
                "available": "Now",
                "deadline": "Now",
                "details": "SECRET_DETAIL",
                "extra": {"spoiler": "SECRET_EXTRA"},
            },
            {
                "id": "future",
                "title": "FUTURE_TITLE",
                "category": "quest",
                "status": "pending",
                "available": "Later",
            },
        ],
    }


def test_supported_fields_and_progress_boundaries_without_mutation():
    source = guide()
    overlay = {
        "version": 1,
        "guide_id": "guide",
        "playthrough": "Run",
        "states": {"future": "done"},
    }
    before, progress_before = copy.deepcopy(source), copy.deepcopy(overlay)
    report = build_report(source, "Now", progress=overlay)
    rendered = json.dumps(report)
    assert "SECRET_" not in rendered and "FUTURE_" not in rendered
    assert report["overdue_count"] == 1 and report["counts"] == {"pending": 1}
    assert source == before and overlay == progress_before
    detailed = json.dumps(build_report(source, "Now", True))
    assert "SECRET_DETAIL" in detailed and "SECRET_EXTRA" not in detailed


@pytest.mark.parametrize("version", [True, 1.0, "1", None])
def test_strict_guide_version(version):
    data = guide()
    data["version"] = version
    with pytest.raises(ValueError, match="version 1"):
        build_report(data, "Now")


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", ""),
        ("title", "  "),
        ("category", ""),
        ("status", []),
        ("available", {}),
        ("deadline", []),
    ],
)
def test_direct_api_checks_nested_records(field, value):
    data = guide()
    data["items"][0][field] = value
    with pytest.raises((TypeError, ValueError)):
        build_report(data, "Now")


def test_progress_version_and_details_flag_are_strict():
    with pytest.raises(ValueError):
        build_report(guide(), "Now", progress={"version": True})
    with pytest.raises(TypeError):
        build_report(guide(), "Now", show_details="false")
    with pytest.raises(TypeError):
        build_report(guide(), "Now", progress=[])


def test_markdown_displays_supplied_markup_literally():
    data = guide()
    data["game"] = "<script>bad</script>"
    data["items"][0]["title"] = "[click](javascript:bad)"
    data["items"][0]["details"] = "**bold**\nnext"
    output = render_markdown(build_report(data, "Now", True))
    assert "<script>" not in output and "&lt;script&gt;" in output
    assert "\\[click\\]" in output
    assert "**bold**" not in output and "<br>next" in output
