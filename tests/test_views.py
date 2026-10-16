from pathlib import Path

import pytest
from django.urls import reverse

from cosmicsounds.catalog import VIDEOS


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.mark.parametrize("name", ["home", "about", "videos"])
def test_static_pages(client, name):
    assert client.get(reverse(name)).status_code == 200


@pytest.mark.parametrize("video", VIDEOS, ids=lambda v: v.slug)
def test_video_detail_pages_and_files_exist(client, video):
    response = client.get(reverse("video_detail", args=[video.id]))
    assert response.status_code == 200
    assert video.title in response.content.decode()
    assert (Path(__file__).parents[1] / "cosmicsounds" / "static" / video.static_path).exists()


def test_unknown_video_is_404(client):
    assert client.get(reverse("video_detail", args=[999])).status_code == 404


def test_valid_threshold_redirects_to_result(client):
    response = client.post(reverse("video_detail", args=[1]), {"threshold": 120})
    assert response.status_code == 302
    assert response.url == reverse("sonified_video", args=[1, 120])


@pytest.mark.parametrize("value", [-1, 256, "bright"])
def test_invalid_threshold_shows_form_error(client, value):
    response = client.post(reverse("video_detail", args=[1]), {"threshold": value})
    assert response.status_code == 200
    assert "errorlist" in response.content.decode()


def test_out_of_range_threshold_url_is_404(client):
    assert client.get(reverse("sonified_video", args=[1, 300])).status_code == 404


def test_result_is_generated_once_then_cached(client, monkeypatch, media_root):
    calls = []

    def fake_sonify(source, output, config):
        calls.append(config.threshold)
        Path(output).write_bytes(b"mp4")

    monkeypatch.setattr("cosmicsounds.views.sonify_video", fake_sonify)
    url = reverse("sonified_video", args=[3, 90])

    for _ in range(2):
        response = client.get(url)
        assert response.status_code == 200
        assert "/media/sonified/dart-dimorphos-t90.mp4" in response.content.decode()

    assert calls == [90]
    assert (media_root / "sonified" / "dart-dimorphos-t90.mp4").exists()


def test_processing_failure_shows_error(client, monkeypatch, media_root):
    def boom(source, output, config):
        Path(output).write_bytes(b"partial")
        raise RuntimeError("ffmpeg exploded")

    monkeypatch.setattr("cosmicsounds.views.sonify_video", boom)
    response = client.get(reverse("sonified_video", args=[2, 80]))

    assert "Something went wrong" in response.content.decode()
    assert not list((media_root / "sonified").iterdir())
