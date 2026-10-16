import numpy as np

from processing.vision import channel_percentages, hot_counts, ring_boxes


def test_ring_boxes_cover_the_ring():
    gray = np.zeros((200, 200), dtype=np.uint8)
    boxes = ring_boxes(gray, distance=40, width=10)
    # Ring is 100x100 outside, 80x80 inside: (100² - 80²) / 10² = 36 boxes.
    assert len(boxes) == 36
    assert all(box.shape == (10, 10) for box in boxes)


def test_ring_boxes_are_clipped_to_the_frame():
    gray = np.zeros((100, 100), dtype=np.uint8)
    boxes = ring_boxes(gray, distance=500, width=10)
    assert all(box.size for box in boxes)


def test_hot_counts_only_reports_bright_boxes():
    boxes = [np.zeros((10, 10)), np.full((10, 10), 200), np.eye(10) * 255]
    assert hot_counts(boxes, threshold=100) == [100, 10]


def test_channel_percentages_reads_bgr():
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    frame[..., 2] = 255  # red in BGR
    assert channel_percentages(frame) == (100.0, 0.0, 0.0)
