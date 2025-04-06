import os
import random
from moviepy.editor import *
from moviepy.video.tools.segmenting import findObjects

def create_text_clip(text, duration=3):
    return TextClip(text, color='white', size=70, method='caption', bg_color='black').set_duration(duration)

def split_video(video, min_duration=3, max_duration=4):
    total_duration = video.duration
    num_segments = int(total_duration / ((min_duration + max_duration) / 2))
    segment_duration = total_duration / num_segments
    return [video.subclip(i * segment_duration, (i + 1) * segment_duration) for i in range(num_segments)]

def process_videos(folder_path, max_clips=20):
    video_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(('.mp4', '.avi', '.mov')):
                video_files.append(os.path.join(root, file))

    random.shuffle(video_files)
    
    segments = []
    for video_file in video_files:
        video = VideoFileClip(video_file)
        segments.extend(split_video(video))
        if len(segments) >= max_clips:
            break

    random.shuffle(segments)
    segments = segments[:max_clips]

    final_clips = []
    welcome_clip = create_text_clip("Добро пожаловать в топ лучших мемов!", 5)
    final_clips.append(welcome_clip)

    for i, segment in enumerate(segments, 1):
        number_clip = create_text_clip(f"Номер {len(segments) - i + 1}")
        final_clips.append(number_clip)
        final_clips.append(segment.resize(height=720))  # Растягиваем видео на весь экран

    final_video = concatenate_videoclips(final_clips)
    final_video.write_videofile("output.mp4", codec="libx264", audio_codec="aac")

# Использование функции
process_videos("videos", max_clips=20)