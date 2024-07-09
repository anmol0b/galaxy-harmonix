from django.urls import path

from . import views
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path("", views.home, name="home"),
    path("/about", views.about, name="about"),
    path("/videos", views.videos_page, name="videos_page"),
    path("/video-detail/<int:video_id>", views.video_detail_page, name="video_detail_page"),
    path("/video-detail/<int:video_id>/<int:threshold>", views.processed_video, name="processed_video"),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)