from moviepy.video.io.VideoFileClip import VideoFileClip

def cut_video(video_file, save_in, clip_duration = 900):
    # Crea un objeto Clip a partir del archivo de video
    clip = VideoFileClip(video_file)

    # Duración del video (en segundos)
    duration = clip.duration
    total = duration
    parts = round(duration / clip_duration)

    print(duration)
    print(parts)

    cuted = 0

    cut_times = []

    for i in range(parts):
        _str = cuted
        _end = cuted + clip_duration

        if (_end > duration):
            _end = duration

        cut_times.append((_str, _end))
        cuted += clip_duration

    # Itera sobre los tiempos de inicio y fin
    for start, end in cut_times:
        # Crea un nuevo clip a partir de un intervalo de tiempo
        new_clip = clip.subclip(start, end)
        # Guarda el nuevo clip con un nombre diferente
        new_clip.write_videofile(save_in+"/clip_part_{}-{}.mp4".format(start, end))