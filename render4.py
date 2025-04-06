from PIL import Image, ImageDraw
from tqdm import tqdm
import numpy as np
import moviepy.editor as mpy
import os
import concurrent.futures
import random
import bisect

FPS = 2
MIN_CHUNK_LEN = 2.0
MAX_CHUNK_LEN = 4.0

video_folder = "test_videos"

video_files = []
for root, dirs, files in os.walk(video_folder):
    for file in files:
        if file.endswith(('.mp4', '.avi', '.mov')):
            video_files.append(os.path.join(root, file))

class VideoChunk:
    chunks = []

    @staticmethod
    def create_chunks(source_path):
        video = mpy.VideoFileClip(source_path)
        total_duration = video.duration
        
        chunk_duration = np.clip(total_duration / np.ceil(total_duration / MAX_CHUNK_LEN), 
                                 MIN_CHUNK_LEN, MAX_CHUNK_LEN)
        
        num_chunks = int(np.ceil(total_duration / chunk_duration))
        
        for i in range(num_chunks):
            start = i * chunk_duration
            end = min((i + 1) * chunk_duration, total_duration)
            VideoChunk.chunks.append(VideoChunk(source_path, start, end))
        
        video.close()

    def __init__(self, source_path, start, end) -> None:
        self.source_path = source_path
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return f"VideoChunk [{self.start}:{self.end}]"

    def __repr__(self) -> str:
        return str(self)

def process_video(video_file):
    VideoChunk.create_chunks(video_file)
    return f"Обработан файл: {video_file}"

with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(process_video, video_file) for video_file in video_files]
    
    for future in tqdm(concurrent.futures.as_completed(futures), total=len(video_files), desc="Обработка видео"):
        print(future.result())

random.shuffle(VideoChunk.chunks)

print(f"Общее количество чанков: {len(VideoChunk.chunks)}")

duration = sum(chunk.end - chunk.start for chunk in VideoChunk.chunks)
print(f"Общая длительность: {duration:.2f} секунд")

def make_frame(t):
    current_time = 0
    for chunk in VideoChunk.chunks:
        chunk_duration = chunk.end - chunk.start
        if current_time <= t < current_time + chunk_duration:
            video = mpy.VideoFileClip(chunk.source_path)
            frame = video.get_frame(chunk.start + (t - current_time))
            video.close()
            return frame
        current_time += chunk_duration
    
    return np.zeros((720, 1280, 3), dtype=np.uint8)

output_path = "output_video.mp4"
clip = mpy.VideoClip(make_frame, duration=duration)

print("Начало рендеринга видео...")
clip.write_videofile(output_path, fps=FPS, codec="libx264", audio=False)
print(f"Видео сохранено в {output_path}")