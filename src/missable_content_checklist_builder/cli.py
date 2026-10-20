from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import build_report, load_checklist, load_progress, render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a spoiler-controlled missables report.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--through", required=True)
    parser.add_argument("--progress", type=Path, help="Per-playthrough progress overlay")
    parser.add_argument("--show-details", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = build_report(
            load_checklist(args.input),
            args.through,
            args.show_details,
            progress=load_progress(args.progress) if args.progress else None,
        )
        rendered = (
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            if args.format == "json"
            else render_markdown(report)
        )
        if args.output:
            if args.output.exists() or args.output.is_symlink():
                raise ValueError(f"output already exists: {args.output}")
            with args.output.open("x", encoding="utf-8", newline="") as handle:
                handle.write(rendered)
        else:
            sys.stdout.write(rendered)
    except (OSError, UnicodeError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
