from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("videos/", views.videos_page, name="videos"),
    path("videos/<int:video_id>/", views.video_detail, name="video_detail"),
    path("videos/<int:video_id>/sonified/<int:threshold>/", views.sonified_video, name="sonified_video"),
]
