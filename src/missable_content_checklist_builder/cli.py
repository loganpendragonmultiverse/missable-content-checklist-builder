from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import build_report, load_checklist, render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a spoiler-controlled missables report.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--through", required=True)
    parser.add_argument("--show-details", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = build_report(load_checklist(args.input), args.through, args.show_details)
        rendered = (
            json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            if args.format == "json"
            else render_markdown(report)
        )
        if args.output:
            if args.output.exists():
                raise ValueError(f"output already exists: {args.output}")
            args.output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0
