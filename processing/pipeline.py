"""Video → soundtrack pipeline.

Once per second of video, a frame is sampled and turned into one second of audio:

* **Stars** – two square rings around the frame centre are cut into small boxes. Every box with
  pixels brighter than ``threshold`` becomes a short note; brighter boxes play higher pitches.
  Each ring fills half of the second with its notes, so busy rings play faster arpeggios.
* **Drone** – the frame's average redness sets the pitch and loudness of a low background tone
  whose timbre is borrowed from a reference recording (``assets/timbre.wav``).
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np

from . import synth
from .vision import channel_percentages, hot_counts, ring_boxes

TIMBRE_WAV = Path(__file__).parent / "assets" / "timbre.wav"


@dataclass(frozen=True)
class SonifyConfig:
    threshold: int = 80             # grayscale value (0-255) above which a pixel counts as a star
    box_size: int = 10              # ring thickness and box edge length, in pixels
    rings: tuple[float, ...] = (0.55, 0.9)  # ring distances as fractions of half the frame's short side
    seconds_per_frame: float = 1.0  # audio length generated for each sampled frame
    max_notes_per_ring: int = 12    # brightest boxes kept per ring, so notes stay audible
    star_pitch: tuple[float, float] = (500.0, 1800.0)
    drone_pitch: tuple[float, float] = (40.0, 160.0)


DEFAULT_CONFIG = SonifyConfig()


@dataclass(frozen=True)
class SonifyResult:
    frames_analysed: int
    notes_played: int
    duration: float


@lru_cache(maxsize=256)
def _drone_timbre(frequency: int) -> tuple[float, ...]:
    return tuple(synth.timbre_from_wav(TIMBRE_WAV, frequency))


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def ring_audio(counts: list[int], duration: float, config: SonifyConfig) -> np.ndarray:
    """Arpeggiate the hot boxes of one ring across ``duration`` seconds (silence if none)."""
    if not counts:
        return np.zeros(synth.num_samples(duration))

    counts = sorted(counts, reverse=True)[:config.max_notes_per_ring]
    total = synth.num_samples(duration)
    per_note = duration / len(counts)
    max_count = config.box_size ** 2
    notes = [
        synth.note(synth.map_range(c, 1, max_count, *config.star_pitch), per_note)
        for c in counts
    ]
    audio = np.concatenate(notes)
    return np.pad(audio, (0, max(total - audio.size, 0)))[:total]


def drone_audio(frame_bgr: np.ndarray, duration: float, config: SonifyConfig) -> np.ndarray:
    red, _, _ = channel_percentages(frame_bgr)
    freq = round(_clamp(synth.map_range(red, 0, 12, *config.drone_pitch), *config.drone_pitch))
    amplitude = _clamp(synth.map_range(red, 3, 12, 0, synth.AMPLITUDE), 0, synth.AMPLITUDE)
    return synth.apply_overtones(freq, duration, _drone_timbre(freq), amplitude=amplitude)


def frame_audio(frame_bgr: np.ndarray, config: SonifyConfig) -> tuple[np.ndarray, int]:
    """Audio for one sampled frame and the number of star notes it contains."""
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    half_short_side = min(gray.shape) // 2
    slot = config.seconds_per_frame / len(config.rings)

    parts, notes = [], 0
    for fraction in config.rings:
        distance = int(half_short_side * fraction) - config.box_size
        counts = hot_counts(ring_boxes(gray, distance, config.box_size), config.threshold)
        notes += min(len(counts), config.max_notes_per_ring)
        parts.append(ring_audio(counts, slot, config))

    stars = np.concatenate(parts)
    drone = drone_audio(frame_bgr, config.seconds_per_frame, config)
    n = min(stars.size, drone.size)
    return stars[:n] + drone[:n], notes


def sonify(video_path: str | Path, audio_path: str | Path, config: SonifyConfig = DEFAULT_CONFIG,
           progress: Callable[[float], None] | None = None) -> SonifyResult:
    """Generate a WAV soundtrack for ``video_path`` and write it to ``audio_path``."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(round(fps * config.seconds_per_frame), 1)

    chunks, notes, index = [], 0, 0
    try:
        while cap.grab():
            if index % step == 0:
                ok, frame = cap.retrieve()
                if not ok:
                    break
                audio, n = frame_audio(frame, config)
                chunks.append(audio)
                notes += n
                if progress and total_frames:
                    progress(min(index / total_frames, 1.0))
            index += 1
    finally:
        cap.release()

    if not chunks:
        raise ValueError(f"no frames could be read from {video_path}")

    signal = np.concatenate(chunks)
    synth.write_wav(audio_path, synth.SAMPLE_RATE, synth.to_int16(signal))
    if progress:
        progress(1.0)
    return SonifyResult(len(chunks), notes, signal.size / synth.SAMPLE_RATE)


def mux(video_path: str | Path, audio_path: str | Path, output_path: str | Path) -> None:
    """Replace the video's audio track with ``audio_path`` using the bundled ffmpeg binary."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    base = [ffmpeg, "-y", "-loglevel", "error", "-i", str(video_path), "-i", str(audio_path),
            "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart"]
    try:
        subprocess.run([*base, "-c:v", "copy", str(output_path)], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # The source codec can't be copied into MP4; re-encode to H.264 instead.
        subprocess.run([*base, "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path)],
                       check=True, capture_output=True)


def sonify_video(video_path: str | Path, output_path: str | Path, config: SonifyConfig = DEFAULT_CONFIG,
                 progress: Callable[[float], None] | None = None) -> SonifyResult:
    """Full pipeline: write ``output_path`` as ``video_path`` with a generated soundtrack."""
    output_path = Path(output_path)
    audio_path = output_path.with_suffix(".wav")
    try:
        result = sonify(video_path, audio_path, config, progress)
        mux(video_path, audio_path, output_path)
    finally:
        audio_path.unlink(missing_ok=True)
    return result
