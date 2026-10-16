"""Sweep a still image column by column; bright 10x10 blocks in each column become notes."""

import numpy as np
from PIL import Image
from scipy.io import wavfile

from processing import synth

lum = np.array(Image.open("image.png").convert("L"))

final = synth.sine_wave(100, 0.1)
for col in range(0, lum.shape[1], 10):
    counts = []
    for row in range(0, lum.shape[0], 10):
        hot = np.count_nonzero(lum[row:row + 10, col:col + 10] > 248)
        if hot:
            counts.append(hot)

    duration = 0.5 / max(len(counts), 1)
    for count in counts or [0]:
        freq = synth.map_range(count, 1, 100, 500, 1800) if count else 20
        final = np.concatenate((final, synth.note(freq, duration)))

print(f"{len(final) / synth.SAMPLE_RATE:.1f}s of audio")
wavfile.write("imgseq.wav", synth.SAMPLE_RATE, synth.to_int16(final))
