# Testing

Use Python 3.10 or later in a clean virtual environment:

```sh
python -m venv .venv
# Activate .venv with the command for your shell.
python -m pip install -e '.[dev]'
ruff format --check .
ruff check .
mypy src
pytest
python -m build
```

The pytest configuration enforces the repository's existing 90% coverage floor. CI covers Python 3.10 and 3.14 on Linux, Windows, and macOS. New feature tests use synthetic input and do not require game files or personal data. Run the full suite before submitting a change; CLI regression tests preserve legacy input/output behavior.

## 1.1.2 acceptance

Run the complete commands above. Regression tests cover strict schema versions,
empty identifiers/text, malformed statuses and milestones, direct API validation,
extra-field omission, literal Markdown, source/overlay immutability and visible
progress/deadline counts. Install each wheel and sdist separately; from outside
the checkout run the whole suite against site-packages, then execute both report
formats on the installed checklist. Verify all four installed document hashes.
Keep the current 90% coverage floor and full protected OS/Python matrix.

`tests/test_output_links.py` checks refusal of existing dangling-link metadata
on every platform and actual dangling symlinks where creation is supported.
