from moviepy.editor import *
import os
import random

# Настройки
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
MIN_CLIP_DURATION = 3  # Минимальная длина клипа в секундах
MAX_CLIP_DURATION = 5  # Максимальная длина клипа в секундах
OUTPUT_FILENAME = "final_video.mp4"
VIDEO_FOLDER = 'test_videos'  # Папка с исходными видео

def get_all_video_files(folder):
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv']
    video_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(root, file))
    return video_files

def split_video_into_clips(video_path):
    clips = []
    video = VideoFileClip(video_path)
    duration = video.duration
    start = 0
    while start < duration:
        end = start + random.uniform(MIN_CLIP_DURATION, MAX_CLIP_DURATION)
        if end > duration:
            end = duration
        clip = video.subclip(start, end)
        clips.append(clip)
        start = end
    video.close()
    return clips

def main():
    all_videos = get_all_video_files(VIDEO_FOLDER)
    all_clips = []

    print(f"Найдено {len(all_videos)} видеофайлов.")

    for video_path in all_videos:
        print(f"Обрабатывается: {video_path}")
        clips = split_video_into_clips(video_path)
        all_clips.extend(clips)

    print(f"Всего клипов для финального видео: {len(all_clips)}")

    random.shuffle(all_clips)

    final_video = concatenate_videoclips(all_clips, method="compose")
    final_video.write_videofile(OUTPUT_FILENAME, codec='libx264', audio_codec='aac')

if __name__ == "__main__":
    main()