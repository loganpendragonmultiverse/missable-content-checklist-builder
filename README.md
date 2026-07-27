# Missable Content Checklist Builder

[![CI](https://github.com/loganpendragonmultiverse/missable-content-checklist-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/loganpendragonmultiverse/missable-content-checklist-builder/actions/workflows/ci.yml)

Missable Content Checklist Builder turns an explicitly authored JSON guide into a reusable, milestone-based checklist. Reports reveal only the entries available through the selected progression point and call out incomplete items whose deadlines have arrived.

## Three-minute start

```bash
python -m pip install .
missable-checklist examples/checklist.json --through "Act 1 Finale"
missable-checklist examples/checklist.json --through "Act 1 Finale" --format json
```

Items support categories, completion states, availability milestones, deadlines, and optional spoiler details. Spoiler details remain hidden unless `--show-details` is supplied. IDs, milestones, ordering, and states are validated.

This project supplies the format and report generator, not a proprietary game database. It cannot discover missables from a game, confirm community-guide accuracy, or know whether a chosen milestone is safe for a particular player. Requires Python 3.10 or newer.

Part of the [Logan Pendragon Forge open-source collection](https://www.loganpendragonforge.com/open-source/). Licensed under the [MIT License](LICENSE).
