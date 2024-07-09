from django.shortcuts import render,redirect
from processing import video_generator
from processing.utils import *

def home(request):
    return render(request,'home.html')

def about(request):
    return render(request,'about.html')


def videos_page(request):
    videos_list = [
        {
            "id":1,
            "video_src":"./static/one1.mp4".lstrip("./static/"),
            "video_thumbnail":"Cosmic Reef Visualization"
        },
        {
            "id":2,
            "video_src":"./static/four4.mp4".lstrip("./static/"),
            "video_thumbnail":"Carbon Star CW Leonis Dissolve Sequence",
        },
        {
            "id":3,
            "video_src":"./static/three.mp4".lstrip("./static/"),
            "video_thumbnail":"Time-Lapse Video of Didymos-Dimorphos"
        },

    ]
    return render(request,'videos.html',{"videos_list":videos_list})

def video_detail_page(request,video_id):
    if request.method  == "POST":
        threshold_value = request.POST.get('numberInput')
        return redirect("processed_video",video_id, threshold_value)
    else:
        videos_list = [
        {
            "id":1,
            "video_src":"./static/one1.mp4".lstrip("./static/"),
            "video_thumbnail":"Cosmic Reef Visualization",
            "video_caption":"This science visualization presents the dramatic landscape of two nebulas in the Large Magellanic Cloud. The video takes viewers on a close-up tour of the nebulas' three-dimensional structures, as deduced by scientists and artists. The visualization is an interpretation of the nebulas' complex structure and is based on images by NASA's Hubble Space Telescope."
        },
        {
            "id":2,
            "video_src":"./static/four4.mp4".lstrip("./static/"),
            "video_thumbnail":"Carbon Star CW Leonis Dissolve Sequence",
            "video_caption":"This is a time-lapse set of images of the aging red giant star CW Leonis, taken on three dates: 2001, 2011, and 2016. The star is embedded inside gossamer cobwebs of dust encircling the star. These are really shells of carbon dust blown off the star. As they expand into space they change shape, as seen between the Hubble Space Telescope exposures. Brilliant searchlight beams from the star's surface poke through the dust. These beams change orientation through the different dates the Hubble photographs were taken. "
        },
            {
                "id": 3,
                "video_src": "./static/three.mp4".lstrip("./static/"),
                "video_thumbnail": "Time-Lapse Video of Didymos-Dimorphos",
                "video_caption":"This movie captures the breakup of the asteroid Dimorphos when it was deliberately hit by NASA's 1,200-pound Double Asteroid Redirection Test (DART) mission spacecraft on September 26, 2022. The Hubble Space Telescope had a ringside view of the space demolition derby."
            },
    ]

    for video in videos_list:
        if video["id"] == video_id:
            selected_video = video
            break

    return render(request,'video-detail.html',{"selected_video":selected_video})


def processed_video(request,video_id, threshold):
    videos_list = [
        {
            "id": 1,
            "video_src": "./static/one1.mp4".lstrip("./static/"),
            "video_thumbnail": "Cosmic Reef Visualization",
            "video_caption": "This science visualization presents the dramatic landscape of two nebulas in the Large Magellanic Cloud. The video takes viewers on a close-up tour of the nebulas' three-dimensional structures, as deduced by scientists and artists. The visualization is an interpretation of the nebulas' complex structure and is based on images by NASA's Hubble Space Telescope."
        },
        {
            "id": 2,
            "video_src": "./static/four4.mp4".lstrip("./static/"),
            "video_thumbnail": "Carbon Star CW Leonis Dissolve Sequence",
            "video_caption": "This is a time-lapse set of images of the aging red giant star CW Leonis, taken on three dates: 2001, 2011, and 2016. The star is embedded inside gossamer cobwebs of dust encircling the star. These are really shells of carbon dust blown off the star. As they expand into space they change shape, as seen between the Hubble Space Telescope exposures. Brilliant searchlight beams from the star's surface poke through the dust. These beams change orientation through the different dates the Hubble photographs were taken. "
        },
        {
            "id": 3,
            "video_src": "./static/three.mp4".lstrip("./static/"),
            "video_thumbnail": "Time-Lapse Video of Didymos-Dimorphos",
            "video_caption": "This movie captures the breakup of the asteroid Dimorphos when it was deliberately hit by NASA's 1,200-pound Double Asteroid Redirection Test (DART) mission spacecraft on September 26, 2022. The Hubble Space Telescope had a ringside view of the space demolition derby."
        },
    ]

    for video in videos_list:
        if video["id"] == video_id:
            selected_video = video
            break
    path = selected_video.video_src
    video_generator.generate_sound_of_video(path, './static/sound.wav')
    video_generator.merge_audio_video(path, 'sound.wav','./static/output_video.mp4')


    return render(request,'processed-video.html',{"threshold_value":threshold})