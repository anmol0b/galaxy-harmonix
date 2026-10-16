import cv2
import numpy as np
import pytest


@pytest.fixture
def star_video(tmp_path):
    """A 3-second 30 fps video of a dark sky with a few bright 'stars' on the inner ring."""
    path = tmp_path / "stars.mp4"
    h, w = 360, 640
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 30, (w, h))
    frame = np.full((h, w, 3), 10, dtype=np.uint8)
    frame[..., 2] = 40  # a little red for the drone
    distance = int(h // 2 * 0.55) - 10  # inner ring of the default config
    cy, cx = h // 2, w // 2
    for x in (cx - 40, cx, cx + 40):
        frame[cy - distance - 8:cy - distance - 2, x:x + 6] = 255
    for _ in range(90):
        writer.write(frame)
    writer.release()
    return path
