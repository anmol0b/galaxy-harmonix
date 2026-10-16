import numpy as np
import pytest
from scipy.io import wavfile

from processing import synth


def test_map_range():
    assert synth.map_range(5, 0, 10, 100, 200) == 150
    assert synth.map_range(0, 0, 10, 100, 200) == 100


def test_sine_wave_length_and_peak():
    wave = synth.sine_wave(440, 0.5, amplitude=1000)
    assert wave.size == 22050
    assert np.max(np.abs(wave)) == pytest.approx(1000, rel=1e-3)


def test_overtones_require_normalised_factor():
    with pytest.raises(ValueError):
        synth.apply_overtones(440, 0.1, [0.5, 0.2])


def test_overtones_drop_harmonics_above_nyquist():
    wave = synth.apply_overtones(15_000, 0.1, [0.5, 0.5])
    # The second harmonic (30 kHz) is above Nyquist and must not alias back in.
    spectrum = np.abs(np.fft.rfft(wave))
    freqs = np.fft.rfftfreq(wave.size, 1 / synth.SAMPLE_RATE)
    assert freqs[np.argmax(spectrum)] == pytest.approx(15_000, abs=20)


@pytest.mark.parametrize("frequency,duration", [(20, 0.5), (500, 0.5), (1800, 0.004), (500, 0.0)])
def test_adsr_envelope_matches_note_length(frequency, duration):
    envelope = synth.adsr_envelope(frequency, duration)
    assert envelope.size == synth.num_samples(duration)
    if envelope.size:
        assert envelope.max() <= 1.0 + 1e-9
        assert envelope[-1] == 0


def test_note_shape():
    assert synth.note(880, 0.25).shape == (synth.num_samples(0.25),)


def test_timbre_from_wav_recovers_harmonics(tmp_path):
    path = tmp_path / "tone.wav"
    tone = synth.apply_overtones(100, 1.0, [0.7, 0.0, 0.3])
    wavfile.write(path, synth.SAMPLE_RATE, tone.astype(np.int16))

    factor = synth.timbre_from_wav(path, 100)
    assert factor.sum() == pytest.approx(1.0)
    assert factor[0] == pytest.approx(0.7, abs=0.05)
    assert factor[2] == pytest.approx(0.3, abs=0.05)


def test_to_int16_normalises_and_handles_silence():
    out = synth.to_int16(np.array([0.0, 2.0, -4.0]))
    assert out.dtype == np.int16
    assert np.abs(out).max() == int(0.8 * 32767)
    assert not synth.to_int16(np.zeros(10)).any()
