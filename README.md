# hz432 — MP3 to A4 = 432 Hz converter

[![CI](https://github.com/doitglobal/hz432/actions/workflows/ci.yml/badge.svg)](https://github.com/doitglobal/hz432/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Version](https://img.shields.io/badge/version-1.0.0-green.svg)

🇵🇱 [Polska wersja README](README.pl.md)

`hz432` is a command-line tool that retunes MP3 files — a single file or a whole folder tree — to **A4 = 432 Hz**.
Instead of blindly assuming every recording is in 440 Hz, it **measures the actual tuning of each track** first,
so the A in the converted file lands as close to 432 Hz as possible.

- recursive folder conversion with the same directory structure in the output,
- per-track tuning detection with a confidence score,
- near-lossless resampling by default (like slowing down a record), optional tempo-preserving pitch shift,
- ID3 tags and cover art are copied; converted files are tagged and skipped on re-runs,
- no ffmpeg required, parallel processing, originals are never modified.

## Installation

Requires **Python 3.10+** ([python.org](https://www.python.org/)) and internet access on the first run.

**Windows** — run `setup.bat` (double-click or from a console in the project folder).
**Linux / macOS** — run `./setup.sh`.

The script creates a virtual environment in `.venv` (if missing) and installs the dependencies from
`requirements.txt` into it — nothing goes into your system Python. It is safe to run again; it only installs
what is missing. `.venv` is not part of the repository, so re-run the script after cloning or deleting it.

Alternatively, install it as a package (adds an `hz432` command):

```
pip install .
```

## Usage

```
.venv\Scripts\python hz432.py "C:\Music"                 # folder + subfolders -> C:\Music_432Hz\ (same structure)
.venv\Scripts\python hz432.py "C:\Music\a.mp3"           # single file -> "a [432Hz].mp3" next to the original
.venv\Scripts\python hz432.py "C:\Music" --analyze-only  # measure tuning only, write nothing
.venv\Scripts\python hz432.py --version
```

On Linux / macOS use `.venv/bin/python` instead of `.venv\Scripts\python`.

### Options

| Option | Description |
|---|---|
| `-o PATH` | output folder (or an exact `.mp3` path for a single file) |
| `-j N` | number of parallel worker processes |
| `--mode speed` | *(default)* resampling — pitch and tempo change together (~1.8–2.7 %), practically lossless |
| `--mode pitch` | pitch only, tempo unchanged (Rubber Band) — use when sync with video/lyrics matters |
| `--ref-hz HZ` | force a known source tuning (skips detection), e.g. `--ref-hz 440` |
| `--policy` | `auto` *(default)*, `measured` or `assume-440` |
| `--target HZ` | target A4 (default 432) |
| `--snap-cents C` | in `auto`, deviations ≤ C cents are treated as exactly 440 (default 1) |
| `--min-confidence X` | below this detection confidence assume 440 (default 0.35) |
| `--force` | re-convert files already tagged as converted |

## How the decision is made (`auto` policy)

1. **Measurement** — spectral peaks → distance from the 440 Hz equal-temperament grid in cents → histogram →
   track tuning plus a *confidence* score (≈0.2 = noise, ≈1 = clean tonal music).
2. **Confidence < 0.35** (drums, electronic, noise) → assume 440 Hz (the standard).
3. **Within measurement error of 440 (±1 cent ≈ ±0.25 Hz)** → treat as 440. The measurement is repeatable to
   ~0.5 cent (same track across different releases), while real recordings deviate from 440 by 1–10 cents, so a
   wider snap would move the result away from 432.
4. **Otherwise** → shift from the *measured* value (e.g. 437 → 432, 442 → 432). Orchestras often tune to
   442–443 Hz, analog tapes drift; "snapping to 440" would leave such a track several Hz off.
5. **About ±50 cents from 440** (e.g. 428 / 453 Hz) → skipped: tuning is only known modulo a semitone, so the
   direction of the correction is ambiguous. Use `--ref-hz` for those files.
6. Tracks already at ~432 Hz (±1 cent) are skipped.

> **Note:** MP3 is re-encoded (lossy) at the original bitrate. Keep your originals for archival purposes.

## Development

```
pip install -e ".[dev]"
ruff check .
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) ([PL](CONTRIBUTING.pl.md)) for guidelines and [CHANGELOG.md](CHANGELOG.md) for release history.

## License

[MIT](LICENSE) © DO IT GLOBAL LTD
