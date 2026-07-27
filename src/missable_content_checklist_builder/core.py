from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

STATUSES = {"pending", "done", "skipped"}


def load_checklist(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
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
        if item["id"] in seen:
            raise ValueError(f"duplicate item id: {item['id']}")
        seen.add(item["id"])
        if item.get("status") not in STATUSES:
            raise ValueError(f"item {item['id']} has an invalid status")
        if item.get("available") not in positions:
            raise ValueError(f"item {item['id']} has an unknown availability milestone")
        deadline = item.get("deadline")
        if deadline is not None and deadline not in positions:
            raise ValueError(f"item {item['id']} has an unknown deadline")
        if deadline is not None and positions[deadline] < positions[item["available"]]:
            raise ValueError(f"item {item['id']} deadline precedes availability")
        if "details" in item and not isinstance(item["details"], str):
            raise TypeError(f"item {item['id']} details must be text")
    return data


def build_report(data: dict[str, Any], through: str, show_details: bool = False) -> dict[str, Any]:
    milestones = data["milestones"]
    if through not in milestones:
        raise ValueError(f"unknown milestone: {through}")
    boundary = milestones.index(through)
    visible = []
    overdue = 0
    for source in data["items"]:
        if milestones.index(source["available"]) > boundary:
            continue
        item = source.copy()
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
        "version": 1,
        "game": data["game"],
        "through": through,
        "visible_count": len(visible),
        "overdue_count": overdue,
        "counts": dict(sorted(counts.items())),
        "items": visible,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['game']} Missable Checklist",
        "",
        f"Through **{report['through']}** · Visible items: **{report['visible_count']}** · Due and incomplete: **{report['overdue_count']}**",
        "",
    ]
    categories = sorted({item["category"] for item in report["items"]})
    for category in categories:
        lines.extend([f"## {category.title()}", ""])
        for item in report["items"]:
            if item["category"] != category:
                continue
            marker = "x" if item["status"] == "done" else " "
            warning = " · due now" if item["overdue"] else ""
            lines.append(f"- [{marker}] **{item['title']}** — {item['status']}{warning}")
            if item.get("details"):
                lines.append(f"  - {item['details']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
