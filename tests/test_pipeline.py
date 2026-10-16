import subprocess

import imageio_ffmpeg
import pytest
from scipy.io import wavfile

from processing import SonifyConfig, sonify, sonify_video
from processing.__main__ import main


def test_sonify_writes_one_second_per_second_of_video(star_video, tmp_path):
    out = tmp_path / "out.wav"
    result = sonify(star_video, out)

    rate, data = wavfile.read(out)
    assert rate == 44_100
    assert result.frames_analysed == 3
    assert data.size / rate == pytest.approx(3.0, abs=0.01)
    assert result.notes_played > 0


def test_threshold_controls_how_many_stars_are_heard(star_video, tmp_path):
    loose = sonify(star_video, tmp_path / "a.wav", SonifyConfig(threshold=50))
    strict = sonify(star_video, tmp_path / "b.wav", SonifyConfig(threshold=255))
    assert loose.notes_played > strict.notes_played == 0


def test_sonify_rejects_missing_video(tmp_path):
    with pytest.raises(FileNotFoundError):
        sonify(tmp_path / "nope.mp4", tmp_path / "out.wav")


def test_sonify_video_produces_mp4_with_audio(star_video, tmp_path):
    out = tmp_path / "out.mp4"
    sonify_video(star_video, out)

    probe = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(out)],
                           capture_output=True, text=True)
    assert "Audio: aac" in probe.stderr
    assert "Video:" in probe.stderr
    assert not out.with_suffix(".wav").exists()


def test_cli(star_video, tmp_path):
    out = tmp_path / "cli.wav"
    assert main([str(star_video), "-o", str(out), "-t", "100"]) == 0
    assert out.exists()
