# Experiments

Early, exploratory scripts written while designing the sonification approach. They are kept
for reference, are not part of the app, and are not linted or tested. Most expect an
`image.png`, `video.mp4` or `space.wav` file in the working directory.

| Script | What it explores |
| --- | --- |
| `star_detection.py` | Detecting stars with thresholding, morphology and contours |
| `frame_fft.py` | 2D Fourier transform of a single frame |
| `image_sonification.py` | Sweeping a still image column by column into notes |
| `timbre_from_fft.py` | Extracting overtone weights from a recording's spectrum |
| `ring_mask.py` | Selecting pixels in a circular ring |

The other scripts also need `pip install matplotlib pillow`.
