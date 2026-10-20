# Development

## 1.1.0 - 2026-10-15

Keep authored guide statuses unchanged and supply a separate overlay with `--progress run-two.json`:

```json
{"version":1,"guide_id":"sky-road-guide","playthrough":"Second run","states":{"tower-key":"done","side-quest":"skipped"}}
```

The guide must explicitly define the same non-empty `guide_id`. Overlay keys refer to the guide’s authored item IDs; unknown IDs, wrong guide IDs, and states other than `pending`, `done`, or `skipped` fail validation. Overlay entries take precedence over authored status; omitted entries retain authored status. Progress for future items is accepted but those items stay excluded until their availability milestone. Due/incomplete counts use effective visible statuses. The guide and overlay are read-only; this command does not write progress or inspect game saves.

Merge and release require independent review and the repository CI gates.

## Validation and public report contract

File loading and direct `build_report` calls must apply the same guide validation.
Retain explicit status precedence and guide-bound progress overlays. Whitelist
supported report fields; never copy arbitrary item metadata into an export.
Keep authored details opt-in and escape supplied Markdown. Do not infer game
state, canon, guide accuracy or future availability. Distributions include four
authority documents and a representative checklist. Publication requires source
and installed acceptance, independent review and all existing protected checks.
