from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

STATUSES = {"pending", "done", "skipped"}


def load_checklist(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return _validate_checklist(data)


def _validate_checklist(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("checklist must be a version 1 object")
    if not isinstance(data.get("game"), str) or not data["game"].strip():
        raise ValueError("checklist requires a game name")
    milestones = data.get("milestones")
    if (
        not isinstance(milestones, list)
        or not milestones
        or any(not isinstance(item, str) or not item.strip() for item in milestones)
    ):
        raise TypeError("milestones must be a non-empty list of names")
    if len(milestones) != len(set(milestones)):
        raise ValueError("milestone names must be unique")
    positions = {name: index for index, name in enumerate(milestones)}
    items = data.get("items")
    if not isinstance(items, list):
        raise TypeError("items must be a list")
    seen: set[str] = set()
    for item in items:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not isinstance(item.get("title"), str)
            or not isinstance(item.get("category"), str)
        ):
            raise TypeError("each item requires string id, title, and category")
        if any(not item[key].strip() for key in ("id", "title", "category")):
            raise ValueError("each item requires nonempty id, title, and category")
        if item["id"] in seen:
            raise ValueError(f"duplicate item id: {item['id']}")
        seen.add(item["id"])
        if not isinstance(item.get("status"), str) or item["status"] not in STATUSES:
            raise ValueError(f"item {item['id']} has an invalid status")
        if not isinstance(item.get("available"), str) or item["available"] not in positions:
            raise ValueError(f"item {item['id']} has an unknown availability milestone")
        deadline = item.get("deadline")
        if deadline is not None and (not isinstance(deadline, str) or deadline not in positions):
            raise ValueError(f"item {item['id']} has an unknown deadline")
        if deadline is not None and positions[deadline] < positions[item["available"]]:
            raise ValueError(f"item {item['id']} deadline precedes availability")
        if "details" in item and not isinstance(item["details"], str):
            raise TypeError(f"item {item['id']} details must be text")
    return data


def load_progress(path: Path) -> dict[str, Any]:
    """Read an explicit per-playthrough overlay; never write the authored guide."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("progress must be an object")
    return value


def progress_states(data: dict[str, Any], progress: dict[str, Any]) -> dict[str, str]:
    if not isinstance(progress, dict):
        raise TypeError("progress must be an object")
    if type(progress.get("version")) is not int or progress["version"] != 1:
        raise ValueError("progress must be version 1")
    if (
        not isinstance(data.get("guide_id"), str)
        or not data["guide_id"].strip()
        or progress.get("guide_id") != data["guide_id"]
    ):
        raise ValueError("progress guide_id must match the authored guide")
    if not isinstance(progress.get("playthrough"), str) or not progress["playthrough"].strip():
        raise ValueError("progress requires a playthrough name")
    states = progress.get("states")
    if not isinstance(states, dict):
        raise TypeError("progress states must be an object")
    known = {item["id"] for item in data["items"]}
    if any(key not in known for key in states):
        raise ValueError("progress contains unknown item IDs")
    if any(not isinstance(state, str) or state not in STATUSES for state in states.values()):
        raise ValueError("progress contains an invalid state")
    return states


def build_report(
    data: dict[str, Any],
    through: str,
    show_details: bool = False,
    *,
    progress: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _validate_checklist(data)
    if not isinstance(show_details, bool):
        raise TypeError("show_details must be a boolean")
    states = progress_states(data, progress) if progress is not None else {}
    milestones = data["milestones"]
    if through not in milestones:
        raise ValueError(f"unknown milestone: {through}")
    boundary = milestones.index(through)
    visible = []
    overdue = 0
    for source in data["items"]:
        if milestones.index(source["available"]) > boundary:
            continue
        item = {
            key: source[key]
            for key in ("id", "title", "category", "status", "available", "deadline", "details")
            if key in source
        }
        item["status"] = states.get(item["id"], item["status"])
        deadline = item.get("deadline")
        item["overdue"] = (
            item["status"] == "pending"
            and deadline is not None
            and milestones.index(deadline) <= boundary
        )
        overdue += int(item["overdue"])
        if not show_details:
            item.pop("details", None)
        visible.append(item)
    counts = Counter(item["status"] for item in visible)
    return {
        **({"playthrough": progress["playthrough"]} if progress is not None else {}),
        "version": 1,
        "game": data["game"],
        "through": through,
        "visible_count": len(visible),
        "overdue_count": overdue,
        "counts": dict(sorted(counts.items())),
        "items": visible,
    }


def _markdown(value: str) -> str:
    escaped = html.escape(value, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", escaped).replace("\n", "<br>")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {_markdown(report['game'])} Missable Checklist",
        "",
        f"Through **{_markdown(report['through'])}** · Visible items: **{report['visible_count']}** · Due and incomplete: **{report['overdue_count']}**",
        "",
    ]
    if "playthrough" in report:
        lines.extend([f"Playthrough: **{_markdown(report['playthrough'])}**", ""])
    categories = sorted({item["category"] for item in report["items"]})
    for category in categories:
        lines.extend([f"## {_markdown(category.title())}", ""])
        for item in report["items"]:
            if item["category"] != category:
                continue
            marker = "x" if item["status"] == "done" else " "
            warning = " · due now" if item["overdue"] else ""
            lines.append(f"- [{marker}] **{_markdown(item['title'])}** — {item['status']}{warning}")
            if item.get("details"):
                lines.append(f"  - {_markdown(item['details'])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
