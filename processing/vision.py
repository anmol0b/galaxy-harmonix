"""Frame analysis: sample square rings around the frame centre and find bright ("hot") boxes."""

from __future__ import annotations

import numpy as np


def ring_boxes(gray: np.ndarray, distance: int, width: int) -> list[np.ndarray]:
    """Split a square ring around the centre of ``gray`` into ``width`` x ``width`` boxes.

    ``distance`` is the gap between the centre and the inner edge of the ring. The ring is
    clipped to the frame, so it is safe to pass distances larger than the frame allows.
    """
    h, w = gray.shape
    cy, cx = h // 2, w // 2
    outer = distance + width

    def clip(y1, y2, x1, x2):
        return gray[max(y1, 0):min(y2, h), max(x1, 0):min(x2, w)]

    sides = (
        clip(cy - outer, cy - distance, cx - outer, cx + outer),     # top (with corners)
        clip(cy + distance, cy + outer, cx - outer, cx + outer),     # bottom (with corners)
        clip(cy - distance, cy + distance, cx - outer, cx - distance),  # left
        clip(cy - distance, cy + distance, cx + distance, cx + outer),  # right
    )

    boxes = []
    for side in sides:
        for y in range(0, side.shape[0], width):
            for x in range(0, side.shape[1], width):
                box = side[y:y + width, x:x + width]
                if box.size:
                    boxes.append(box)
    return boxes


def hot_counts(boxes: list[np.ndarray], threshold: int) -> list[int]:
    """Number of pixels brighter than ``threshold`` in each box, keeping only non-empty boxes."""
    counts = (int(np.count_nonzero(box > threshold)) for box in boxes)
    return [c for c in counts if c]


def channel_percentages(frame_bgr: np.ndarray) -> tuple[float, float, float]:
    """Mean red, green and blue intensity of a BGR frame, each as a percentage of 255."""
    b, g, r = (frame_bgr[..., i].mean() / 255 * 100 for i in range(3))
    return float(r), float(g), float(b)
