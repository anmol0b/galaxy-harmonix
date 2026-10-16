import logging
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import Http404
from django.shortcuts import redirect, render

from processing import SonifyConfig, sonify_video

from .catalog import VIDEOS, get_video
from .forms import ThresholdForm

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "home.html", {"featured": VIDEOS[0]})


def about(request):
    return render(request, "about.html")


def videos_page(request):
    return render(request, "videos.html", {"videos": VIDEOS})


def video_detail(request, video_id):
    video = get_video(video_id)
    form = ThresholdForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        return redirect("sonified_video", video_id=video.id, threshold=form.cleaned_data["threshold"])
    return render(request, "video-detail.html", {"video": video, "form": form})


def sonified_video(request, video_id, threshold):
    video = get_video(video_id)
    if not 0 <= threshold <= 255:
        raise Http404("Threshold must be between 0 and 255")

    output_name = f"{video.slug}-t{threshold}.mp4"
    output_path = Path(settings.MEDIA_ROOT) / "sonified" / output_name
    error = None

    if not output_path.exists():
        source = finders.find(video.static_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Render to a hidden file and rename when done, so a partial file is never served.
        tmp_path = output_path.with_name(f".{output_name}")
        try:
            sonify_video(source, tmp_path, SonifyConfig(threshold=threshold))
            tmp_path.replace(output_path)
        except Exception:
            logger.exception("Sonifying %s failed", video.slug)
            tmp_path.unlink(missing_ok=True)
            error = "Something went wrong while generating the soundtrack. Please try another threshold."

    return render(request, "sonified-video.html", {
        "video": video,
        "threshold": threshold,
        "output_url": f"{settings.MEDIA_URL}sonified/{output_name}",
        "error": error,
        "form": ThresholdForm(initial={"threshold": threshold}),
    })
