import math
from pathlib import Path

import numpy as np
import pytest

import hz432
from hz432 import STANDARD_HZ, Tuning, cents, decide, detect_tuning, nearest_bitrate, plan_jobs, shift_audio

SR = 22050


def chord(a4_hz: float, seconds: float = 8.0, sr: int = SR) -> np.ndarray:
    """A few notes with harmonics, tuned relative to the given A4."""
    t = np.arange(int(seconds * sr)) / sr
    y = np.zeros_like(t)
    for semitones in (-9, -5, 0, 3, 7, 12):  # C4 E4 A4 C5 E5 A5
        f0 = a4_hz * 2 ** (semitones / 12)
        for h in range(1, 5):
            y += np.sin(2 * math.pi * f0 * h * t) / h
    return (0.3 * y / np.max(np.abs(y))).astype(np.float32)


def test_version():
    assert hz432.__version__ == "1.0.0"


def test_cents():
    assert cents(2.0) == pytest.approx(1200.0)
    assert cents(432 / 440) == pytest.approx(-31.77, abs=0.01)


@pytest.mark.parametrize("bps, kbps", [(128_000, 128), (190_000, 192), (320_500, 320), (10_000, 32)])
def test_nearest_bitrate(bps, kbps):
    assert nearest_bitrate(bps) == kbps


def _decide(t, **kw):
    args = dict(target=432.0, policy="auto", snap=1.0, min_conf=0.35, forced_ref=None)
    args.update(kw)
    return decide(t, **args)


def test_decide_snaps_to_440_within_error():
    plan = _decide(Tuning(440.2, 0.8, 0.9))
    assert plan.ref_hz == STANDARD_HZ and not plan.skip


def test_decide_uses_measured_value():
    plan = _decide(Tuning(442.0, 7.85, 0.9))
    assert plan.ref_hz == 442.0 and not plan.skip


def test_decide_low_confidence_assumes_440():
    plan = _decide(Tuning(445.0, 19.6, 0.2))
    assert plan.ref_hz == STANDARD_HZ


def test_decide_skips_ambiguous():
    assert _decide(Tuning(452.0, 46.6, 0.9)).skip


def test_decide_skips_already_432():
    assert _decide(Tuning(432.1, -31.4, 0.9)).skip


def test_decide_forced_ref_wins():
    plan = _decide(Tuning(452.0, 46.6, 0.9), forced_ref=440.0)
    assert plan.ref_hz == 440.0 and not plan.skip


def test_plan_jobs_folder(tmp_path: Path):
    src = tmp_path / "Album"
    (src / "CD1").mkdir(parents=True)
    (src / "CD1" / "a.mp3").touch()
    (src / "b.MP3").touch()
    (src / "cover.jpg").touch()
    jobs = plan_jobs(src, None)
    # path sort order depends on the OS (case sensitivity), so compare sets
    assert {d for _, d in jobs} == {
        tmp_path / "Album_432Hz" / "CD1" / "a.mp3",
        tmp_path / "Album_432Hz" / "b.MP3",
    }


def test_plan_jobs_single_file(tmp_path: Path):
    f = tmp_path / "a.mp3"
    f.touch()
    assert plan_jobs(f, None) == [(f, tmp_path / "a [432Hz].mp3")]
    assert plan_jobs(f, tmp_path / "x.mp3") == [(f, tmp_path / "x.mp3")]


@pytest.mark.parametrize("a4", [440.0, 436.0, 443.0])
def test_detect_tuning_synthetic(a4):
    t = detect_tuning(chord(a4))
    assert t.confidence > 0.5
    assert t.deviation == pytest.approx(cents(a4 / STANDARD_HZ), abs=1.0)


def test_detect_tuning_silence():
    t = detect_tuning(np.zeros(SR * 5, dtype=np.float32))
    assert t.confidence == 0.0 and t.a4_hz == STANDARD_HZ


def test_speed_shift_lands_on_432():
    y = chord(440.0)
    out = shift_audio(y[np.newaxis, :], SR, 432 / 440, "speed")[0]
    assert len(out) == pytest.approx(len(y) * 440 / 432, rel=1e-3)
    assert detect_tuning(out).deviation == pytest.approx(cents(432 / 440), abs=1.0)
