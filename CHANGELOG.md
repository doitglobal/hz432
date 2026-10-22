# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Release workflow: builds a standalone Windows executable (`hz432-windows-x64.exe`, attached to the release)
  and publishes the package to PyPI.
- `CODEOWNERS`; link to GitHub Discussions in the issue chooser.

## [1.0.0] - 2026-10-22

### Added
- Conversion of a single MP3 file or a whole folder tree (recursively) to A4 = 432 Hz.
- Per-track tuning detection (spectral peak histogram against the 440 Hz grid) with a confidence score.
- `auto` decision policy: assume 440 Hz on low confidence, snap to 440 Hz within measurement error (1 cent),
  otherwise shift from the measured tuning; skip ambiguous (~±50 cent) and already-432 Hz tracks.
- `speed` mode (default, near-lossless resampling) and `pitch` mode (tempo-preserving, Rubber Band).
- ID3 tag and cover art copying; converted files are tagged `HZ432_CONVERTER` and skipped on re-runs.
- Options: `--analyze-only`, `--ref-hz`, `--policy`, `--target`, `--snap-cents`, `--min-confidence`,
  `--force`, `-o`, `-j`, `--version`.
- `setup.bat` / `setup.sh` scripts that create `.venv` and install dependencies.

[Unreleased]: ../../compare/v1.0.0...HEAD
[1.0.0]: ../../releases/tag/v1.0.0
