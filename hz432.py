#!/usr/bin/env python
"""hz432 - retunes MP3 files to A4 = 432 Hz.

1. Measures the actual tuning of the track (A4 in Hz) from spectral analysis.
2. Computes the pitch shift: ref -> 432 Hz.
3. Resamples the track (like slowing down a record: ~2% longer, no artifacts) or, with
   --mode pitch, shifts the pitch only (Rubber Band, tempo unchanged); writes MP3 with tags.

Usage:
    python hz432.py <file.mp3 | folder> [-o OUTPUT] [--analyze-only] ...
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np

__version__ = "1.0.0"

STANDARD_HZ = 440.0
TAG_DESC = "HZ432_CONVERTER"

# The measurement repeats to ~0.5 c (same track, different releases), while real
# recordings deviate from 440 by typically 1-10 c - so we "snap" to 440 only within
# measurement error (~1 c = 0.25 Hz); beyond that we shift from the measured value (closer to 432).
DEFAULT_SNAP_CENTS = 1.0
# A track counts as already-432 when the difference is within measurement error.
ALREADY_TARGET_CENTS = 1.0
# The estimate is only known modulo a semitone (+-50 cents). Above this threshold it is
# unclear whether the track is slightly sharp or slightly flat - the file is skipped.
AMBIGUOUS_CENTS = 35.0
# Minimum estimation "confidence" (see detect_tuning); below it we assume 440.
DEFAULT_MIN_CONFIDENCE = 0.35


def cents(ratio: float) -> float:
    return 1200.0 * math.log2(ratio)


# --------------------------------------------------------------------------- #
# Tuning detection
# --------------------------------------------------------------------------- #
@dataclass
class Tuning:
    a4_hz: float        # measured A4
    deviation: float    # deviation from 440 in cents (-50..+50)
    confidence: float   # 0..1, how much energy "lands" on a single tuning grid


def load_mono(path: Path, sr: int = 22050, max_seconds: float = 150.0) -> np.ndarray:
    """Loads mono audio for analysis; for long tracks takes an excerpt from the middle."""
    from pedalboard.io import AudioFile

    with AudioFile(str(path)) as f:
        total = f.frames
        native_sr = f.samplerate
        take = int(max_seconds * native_sr)
        if total > take:
            f.seek((total - take) // 2)
            audio = f.read(take)
        else:
            audio = f.read(total)
        mono = audio.mean(axis=0)
    import librosa

    return librosa.resample(mono, orig_sr=native_sr, target_sr=sr) if native_sr != sr else mono


def detect_tuning(y: np.ndarray, sr: int = 22050) -> Tuning:
    """Estimates the tuning as the offset of the 12-TET grid relative to A4=440.

    For each STFT frame we take the spectral peaks (piptrack, parabolic interpolation),
    compute their distance in cents from the nearest note of the 440 grid and build an
    amplitude-weighted histogram. The histogram peak = the track's tuning. Confidence is
    the share of energy around the peak (+-10 cents); for noise/percussion the histogram
    is flat (~0.2), for tonal music usually >0.4.
    """
    import librosa

    if y.size < sr * 3 or float(np.max(np.abs(y))) < 1e-4:
        return Tuning(STANDARD_HZ, 0.0, 0.0)

    pitches, mags = librosa.piptrack(
        y=y, sr=sr, n_fft=8192, hop_length=2048, fmin=200.0, fmax=4000.0, threshold=0.1
    )
    mask = pitches > 0
    if not mask.any():
        return Tuning(STANDARD_HZ, 0.0, 0.0)
    # only the stronger peaks (above the median) - as in librosa.estimate_tuning
    mask &= mags >= np.median(mags[mask])
    f = pitches[mask]
    w = mags[mask]

    midi = 69.0 + 12.0 * np.log2(f / STANDARD_HZ)
    resid = (midi - np.round(midi)) * 100.0            # cents, -50..+50
    hist, edges = np.histogram(resid, bins=100, range=(-50, 50), weights=w)
    hist = hist / hist.sum()

    # sliding window of +-10 cents (1-cent bins, circular), peak = center of the best window
    win = 21
    padded = np.concatenate([hist[-(win // 2):], hist, hist[: win // 2]])
    window_sum = np.convolve(padded, np.ones(win), mode="valid")
    k = int(np.argmax(window_sum))
    confidence = float(window_sum[k])

    # refinement: weighted mean within the window around the peak
    centers = (edges[:-1] + edges[1:]) / 2
    offs = (centers - centers[k] + 50) % 100 - 50
    sel = np.abs(offs) <= win // 2
    dev = float(centers[k] + np.average(offs[sel], weights=hist[sel] + 1e-12))
    dev = (dev + 50) % 100 - 50
    return Tuning(STANDARD_HZ * 2 ** (dev / 1200), dev, confidence)


# --------------------------------------------------------------------------- #
# Decision: which reference to use
# --------------------------------------------------------------------------- #
@dataclass
class Plan:
    ref_hz: float
    reason: str
    skip: bool = False

    @property
    def shift_cents(self) -> float:
        return cents(self.target_hz / self.ref_hz)

    target_hz: float = 432.0


def decide(t: Tuning, target: float, policy: str, snap: float, min_conf: float,
           forced_ref: float | None) -> Plan:
    def mk(ref, reason, skip=False):
        return Plan(ref_hz=ref, reason=reason, skip=skip, target_hz=target)

    if forced_ref:
        ref, reason = forced_ref, f"forced --ref-hz {forced_ref:g}"
    elif policy == "assume-440":
        ref, reason = STANDARD_HZ, "policy assume-440"
    elif t.confidence < min_conf:
        ref, reason = STANDARD_HZ, f"low confidence ({t.confidence:.2f}) -> assuming 440"
    elif abs(t.deviation) > AMBIGUOUS_CENTS:
        # ~half a semitone from 440: could be slightly flat or slightly sharp - don't guess
        return mk(t.a4_hz, f"ambiguous ({t.deviation:+.0f} c from 440) - skipping, use --ref-hz",
                  skip=True)
    elif policy == "auto" and abs(t.deviation) <= snap:
        ref, reason = STANDARD_HZ, f"within measurement error ({t.deviation:+.1f} c) -> 440"
    else:
        ref, reason = t.a4_hz, "measured"

    if abs(cents(target / ref)) < ALREADY_TARGET_CENTS:
        return mk(ref, reason + "; already ~432 Hz", skip=True)
    return mk(ref, reason)


# --------------------------------------------------------------------------- #
# Audio processing
# --------------------------------------------------------------------------- #
def shift_audio(audio: np.ndarray, sr: int, ratio: float, mode: str) -> np.ndarray:
    """audio: (channels, samples) float32. ratio = target/ref."""
    if mode == "pitch":
        from pedalboard import time_stretch

        return time_stretch(
            audio, sr, stretch_factor=1.0,
            pitch_shift_in_semitones=12.0 * math.log2(ratio),
            high_quality=True, preserve_formants=False,
        )
    # mode == "speed": like a record - both pitch and tempo change
    import librosa

    return librosa.resample(audio, orig_sr=sr * ratio, target_sr=sr, res_type="soxr_hq")


def nearest_bitrate(bps: int) -> int:
    rates = [32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]
    kbps = bps / 1000
    return min(rates, key=lambda r: abs(r - kbps))


def copy_tags(src: Path, dst: Path, note: str) -> None:
    from mutagen.id3 import ID3, TXXX, ID3NoHeaderError

    try:
        tags = ID3(str(src))
    except ID3NoHeaderError:
        tags = ID3()
    tags.delall(f"TXXX:{TAG_DESC}")
    tags.add(TXXX(encoding=3, desc=TAG_DESC, text=note))
    tags.save(str(dst), v2_version=3)


def already_converted(path: Path) -> str | None:
    from mutagen.id3 import ID3, ID3NoHeaderError

    try:
        frames = ID3(str(path)).getall(f"TXXX:{TAG_DESC}")
    except ID3NoHeaderError:
        return None
    return str(frames[0].text[0]) if frames else None


@dataclass
class Result:
    src: str
    dst: str | None
    status: str          # ok | skipped | analyzed | error
    detail: str


def process_file(src: Path, dst: Path | None, opts: dict) -> Result:
    try:
        prev = already_converted(src)
        if prev and not opts["force"]:
            return Result(str(src), None, "skipped", f"already converted ({prev})")

        t = detect_tuning(load_mono(src))
        plan = decide(t, opts["target"], opts["policy"], opts["snap"],
                      opts["min_conf"], opts["ref_hz"])
        info = (f"A4={t.a4_hz:6.2f} Hz ({t.deviation:+5.1f} c, confidence {t.confidence:.2f}) "
                f"| ref={plan.ref_hz:6.2f} ({plan.reason}) | shift {plan.shift_cents:+.1f} c")

        if opts["analyze_only"]:
            return Result(str(src), None, "analyzed", info)
        if plan.skip:
            return Result(str(src), None, "skipped", info)

        from mutagen.mp3 import MP3
        from pedalboard.io import AudioFile

        bitrate = nearest_bitrate(MP3(str(src)).info.bitrate)
        with AudioFile(str(src)) as f:
            sr, nch = int(f.samplerate), f.num_channels
            audio = f.read(f.frames)
        out = shift_audio(audio, sr, plan.target_hz / plan.ref_hz, opts["mode"])
        out = np.clip(out, -1.0, 1.0)

        assert dst is not None
        dst.parent.mkdir(parents=True, exist_ok=True)
        with AudioFile(str(dst), "w", samplerate=sr, num_channels=nch,
                       quality=f"{bitrate}k") as f:
            f.write(out.astype(np.float32))
        copy_tags(src, dst, f"{t.a4_hz:.2f}Hz->{plan.target_hz:g}Hz ({opts['mode']})")
        return Result(str(src), str(dst), "ok", info)
    except Exception as e:  # noqa: BLE001 - report per file, don't abort the whole run
        return Result(str(src), None, "error", f"{type(e).__name__}: {e}")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def plan_jobs(inp: Path, out: Path | None) -> list[tuple[Path, Path]]:
    if inp.is_file():
        dst = out if out and out.suffix.lower() == ".mp3" else (
            (out or inp.parent) / f"{inp.stem} [432Hz].mp3")
        return [(inp, dst)]
    root_out = out or inp.with_name(inp.name + "_432Hz")
    files = sorted(p for p in inp.rglob("*") if p.is_file() and p.suffix.lower() == ".mp3")
    return [(p, root_out / p.relative_to(inp)) for p in files]


def main(argv: list[str] | None = None) -> int:
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(
        description="Convert MP3 files (a single file or a folder, recursively) to A4 = 432 Hz.")
    ap.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("input", type=Path, help="an .mp3 file or a folder (subfolders included)")
    ap.add_argument("-o", "--output", type=Path,
                    help="output folder, or an exact .mp3 path for a single file (default: <folder>_432Hz, "
                         "or '<name> [432Hz].mp3' next to the file)")
    ap.add_argument("--analyze-only", action="store_true", help="only measure the tuning, write nothing")
    ap.add_argument("--target", type=float, default=432.0, help="target A4 in Hz (default: 432)")
    ap.add_argument("--policy", choices=["auto", "measured", "assume-440"], default="auto",
                    help="auto: measured, but 440 within measurement error or on low confidence; "
                         "measured: always measured (except low confidence); assume-440: always 440")
    ap.add_argument("--ref-hz", type=float, help="force a known source tuning in Hz (skips detection)")
    ap.add_argument("--snap-cents", type=float, default=DEFAULT_SNAP_CENTS,
                    help="with --policy auto, treat deviations <= this many cents as 440 "
                         f"(default: {DEFAULT_SNAP_CENTS:g})")
    ap.add_argument("--min-confidence", type=float, default=DEFAULT_MIN_CONFIDENCE,
                    help=f"assume 440 below this detection confidence (default: {DEFAULT_MIN_CONFIDENCE:g})")
    ap.add_argument("--mode", choices=["speed", "pitch"], default="speed",
                    help="speed: like a slowed-down record - pitch and tempo change (~2%%), no artifacts (default); "
                         "pitch: pitch only, tempo unchanged (Rubber Band; when sync matters)")
    ap.add_argument("-j", "--jobs", type=int, default=max(1, min(4, (os.cpu_count() or 2) // 2)),
                    help="number of parallel worker processes")
    ap.add_argument("--force", action="store_true", help="re-convert files already tagged as converted")
    a = ap.parse_args(argv)

    if not a.input.exists():
        ap.error(f"does not exist: {a.input}")
    jobs = plan_jobs(a.input, a.output)
    if not jobs:
        print("No .mp3 files found.")
        return 1

    opts = dict(target=a.target, policy=a.policy, snap=a.snap_cents, min_conf=a.min_confidence,
                ref_hz=a.ref_hz, mode=a.mode, analyze_only=a.analyze_only, force=a.force)
    print(f"Files: {len(jobs)} | mode: {a.mode} | policy: {a.policy} | jobs: {a.jobs}")

    counts: dict[str, int] = {}
    done = 0

    def report(r: Result) -> None:
        nonlocal done
        done += 1
        counts[r.status] = counts.get(r.status, 0) + 1
        print(f"[{done}/{len(jobs)}] {r.status.upper():8} {Path(r.src).name}\n           {r.detail}")

    if a.jobs <= 1 or len(jobs) == 1:
        for s, d in jobs:
            report(process_file(s, d, opts))
    else:
        with ProcessPoolExecutor(max_workers=a.jobs) as ex:
            futs = [ex.submit(process_file, s, d, opts) for s, d in jobs]
            for fu in as_completed(futs):
                report(fu.result())

    print("Summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 1 if counts.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
