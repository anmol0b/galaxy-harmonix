"""Additive synthesis helpers: sine waves, overtones, ADSR envelopes and timbre extraction."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.io import wavfile

SAMPLE_RATE = 44_100
AMPLITUDE = 4096

# Default timbre (relative amplitudes of the fundamental and its overtones).
DEFAULT_FACTOR = (0.68, 0.26, 0.03, 0.0, 0.03)
# ADSR stage lengths (fractions of the note), per-stage decay rates and sustain level.
DEFAULT_LENGTH = (0.01, 0.6, 0.29, 0.1)
DEFAULT_DECAY = (0.05, 0.02, 0.005, 0.1)
DEFAULT_SUSTAIN = 0.1


def num_samples(duration: float, sample_rate: int = SAMPLE_RATE) -> int:
    return int(sample_rate * duration)


def map_range(value: float, from_min: float, from_max: float, to_min: float, to_max: float) -> float:
    """Linearly map ``value`` from one range to another (no clamping)."""
    ratio = (value - from_min) / (from_max - from_min)
    return ratio * (to_max - to_min) + to_min


def sine_wave(frequency: float, duration: float, sample_rate: int = SAMPLE_RATE,
              amplitude: float = AMPLITUDE) -> np.ndarray:
    t = np.arange(num_samples(duration, sample_rate)) / sample_rate
    return amplitude * np.sin(2 * np.pi * frequency * t)


def apply_overtones(frequency: float, duration: float, factor, sample_rate: int = SAMPLE_RATE,
                    amplitude: float = AMPLITUDE) -> np.ndarray:
    """Sum the fundamental and its harmonics, weighted by ``factor`` (which must sum to 1).

    Harmonics above the Nyquist frequency are dropped.
    """
    factor = np.asarray(factor, dtype=float)
    if not np.isclose(factor.sum(), 1.0):
        raise ValueError(f"overtone factors must sum to 1, got {factor.sum():.4f}")

    wave = np.zeros(num_samples(duration, sample_rate))
    for harmonic, weight in enumerate(factor, start=1):
        freq = frequency * harmonic
        if weight == 0 or freq >= sample_rate / 2:
            continue
        wave += sine_wave(freq, duration, sample_rate, amplitude * weight)
    return wave


def adsr_envelope(frequency: float, duration: float, length=DEFAULT_LENGTH, decay=DEFAULT_DECAY,
                  sustain_level: float = DEFAULT_SUSTAIN, sample_rate: int = SAMPLE_RATE) -> np.ndarray:
    """Attack/decay/sustain/release envelope with exponential stages.

    The envelope is built at a resolution of one point per wave period, smoothed, then resampled
    to exactly ``num_samples(duration)`` points so it always matches the note it shapes.
    """
    if not np.isclose(sum(length), 1.0):
        raise ValueError("ADSR stage lengths must sum to 1")
    if len(length) != 4 or len(decay) != 4:
        raise ValueError("ADSR needs exactly four stage lengths and decay rates")

    n = num_samples(duration, sample_rate)
    if n == 0:
        return np.zeros(0)

    intervals = max(int(duration * frequency), 8)
    len_a, len_d, len_s, len_r = (max(int(intervals * frac), 1) for frac in length)
    decay_a, decay_d, decay_s, decay_r = decay

    attack = 1 / (1 - decay_a) ** np.arange(len_a)
    attack /= attack.max()
    dec = (1 - decay_d) ** np.arange(len_d) * (1 - sustain_level) + sustain_level
    sustain = (1 - decay_s) ** np.arange(len_s) * sustain_level
    release = (1 - decay_r) ** np.arange(len_r) * sustain[-1]

    weights = np.concatenate((attack, dec, sustain, release))
    smoothing = 0.9 ** np.arange(5)
    weights = np.convolve(weights, smoothing / smoothing.sum(), mode="same")

    src = np.linspace(0, 1, weights.size)
    dst = np.linspace(0, 1, n)
    envelope = np.interp(dst, src, weights)
    envelope[-1] = 0.0  # end silent to avoid clicks between notes
    return envelope


def note(frequency: float, duration: float, factor=DEFAULT_FACTOR,
         amplitude: float = AMPLITUDE) -> np.ndarray:
    """A single enveloped note: overtones shaped by an ADSR envelope."""
    wave = apply_overtones(frequency, duration, factor, amplitude=amplitude)
    return wave * adsr_envelope(frequency, duration)


def timbre_from_wav(path: str | Path, frequency: float, clip: tuple[int, int] | None = None,
                    top_n: int = 100) -> np.ndarray:
    """Estimate overtone weights for ``frequency`` from the spectrum of a recording.

    The ``top_n`` strongest frequency bins are snapped to the nearest harmonic of ``frequency``
    and their magnitudes summed per harmonic.
    """
    sample_rate, data = wavfile.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if clip is not None:
        data = data[clip[0]:clip[1]]

    freqs = np.fft.rfftfreq(data.size, d=1 / sample_rate)[1:]
    spectrum = np.abs(np.fft.rfft(data))[1:]

    strongest = np.argsort(-spectrum)[:top_n]
    harmonics = np.round(freqs[strongest] / frequency).astype(int)
    keep = harmonics >= 1
    harmonics, magnitudes = harmonics[keep], spectrum[strongest][keep]
    if harmonics.size == 0:
        return np.array(DEFAULT_FACTOR)

    factor = np.bincount(harmonics - 1, weights=magnitudes)
    return factor / factor.sum()


def to_int16(signal: np.ndarray, headroom: float = 0.8) -> np.ndarray:
    """Normalise to ``headroom`` of full scale and convert to 16-bit PCM."""
    peak = np.max(np.abs(signal)) if signal.size else 0
    if peak == 0:
        return np.zeros(signal.shape, dtype=np.int16)
    return (signal / peak * headroom * np.iinfo(np.int16).max).astype(np.int16)
