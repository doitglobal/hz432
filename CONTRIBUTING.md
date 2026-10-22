# Contributing to hz432

🇵🇱 [Wersja polska](CONTRIBUTING.pl.md)

Thanks for your interest in improving hz432! Bug reports, ideas and pull requests are all welcome.

## Reporting bugs and requesting features

- Search the existing issues first — maybe it has already been reported.
- Use the issue templates. For bugs, include your OS, Python version, the exact command and the full output.
  Running with `--analyze-only` and pasting the result helps a lot with tuning-detection problems.
- Please do **not** attach copyrighted audio files. If a specific track is needed, describe it
  (title, release) or share a short sample you are allowed to share.

## Development setup

```
git clone <your fork URL>
cd hz432
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

Run the checks before opening a pull request:

```
ruff check .
pytest
```

The same checks run in CI on Linux and Windows.

## Pull requests

1. Fork the repository and create a branch from `main` (e.g. `fix/ambiguous-detection`).
2. Keep changes focused — one feature or fix per pull request.
3. Add or update tests in `tests/` for behavior changes. Tests must not need real music files;
   generate synthetic signals instead (see `chord()` in `tests/test_hz432.py`).
4. Update `README.md` and `README.pl.md` when you change options or behavior.
5. Add an entry under **[Unreleased]** in `CHANGELOG.md`.
6. Write clear commit messages in the imperative mood ("Add …", "Fix …").

### Changes to the tuning detection or decision policy

These directly affect the output of every conversion. Please describe in the pull request how you validated
the change — ideally the measured tuning before and after on a sample of real recordings, and the effect on the
spread of the resulting A4 around the target.

## Versioning and releases

The project follows [Semantic Versioning](https://semver.org/). The version lives in a single place:
`__version__` in `hz432.py`. A release means: bump `__version__`, move the **[Unreleased]** changelog entries
under the new version, and tag the commit `vX.Y.Z`.

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating you agree to uphold it.
