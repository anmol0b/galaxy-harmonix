"""The videos available for sonification. Footage: NASA / ESA / Hubble (public domain)."""

from dataclasses import dataclass

from django.http import Http404


@dataclass(frozen=True)
class Video:
    id: int
    slug: str
    title: str
    caption: str
    suggested_threshold: int = 80  # starting slider value that finds a good number of stars

    @property
    def static_path(self) -> str:
        return f"videos/{self.slug}.mp4"


VIDEOS = (
    Video(
        id=1,
        slug="cosmic-reef",
        title="Cosmic Reef Visualization",
        caption=(
            "A science visualization of two nebulas in the Large Magellanic Cloud, flying through "
            "their three-dimensional structure as interpreted by scientists and artists from "
            "Hubble Space Telescope images."
        ),
    ),
    Video(
        id=2,
        slug="cw-leonis",
        title="Carbon Star CW Leonis",
        caption=(
            "A time-lapse of the aging red giant CW Leonis from Hubble exposures taken in 2001, 2011 "
            "and 2016. Shells of carbon dust blown off the star expand and change shape, while "
            "searchlight beams from the star's surface shift through the dust."
        ),
        suggested_threshold=25,
    ),
    Video(
        id=3,
        slug="dart-dimorphos",
        title="Didymos–Dimorphos After DART",
        caption=(
            "Hubble's view of debris streaming from the asteroid Dimorphos after NASA's Double "
            "Asteroid Redirection Test spacecraft deliberately struck it on 26 September 2022."
        ),
    ),
)


def get_video(video_id: int) -> Video:
    for video in VIDEOS:
        if video.id == video_id:
            return video
    raise Http404("No such video")
