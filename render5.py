from PIL import Image, ImageDraw
from tqdm import tqdm
import numpy as np
import moviepy.editor as mpy
import os
import concurrent.futures
import random
import bisect

FPS = 30
MIN_CHUNK_LEN = 2.0
MAX_CHUNK_LEN = 4.0

# Задаем желаемое разрешение
TARGET_RESOLUTION = (1920, 1080)  # Ширина, Высота

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

class FrameGenerator:
    def __init__(self, chunks, target_resolution):
        self.chunks = chunks
        self.target_resolution = target_resolution
        self.cumulative = []
        total = 0
        for chunk in self.chunks:
            duration = chunk.end - chunk.start
            self.cumulative.append((total, total + duration, chunk))
            total += duration
        self.current_chunk_index = -1
        self.current_video = None
        self.current_chunk = None

    def __call__(self, t):
        if t >= self.cumulative[-1][1] or t < 0:
            return np.zeros((self.target_resolution[1], self.target_resolution[0], 3), dtype=np.uint8)
        
        i = bisect.bisect_right(self.cumulative, (t,)) - 1
        
        if i < 0:
            return np.zeros((self.target_resolution[1], self.target_resolution[0], 3), dtype=np.uint8)
        
        if i != self.current_chunk_index:
            if self.current_video:
                self.current_video.close()
            chunk = self.cumulative[i][2]
            self.current_video = mpy.VideoFileClip(chunk.source_path)
            self.current_chunk_index = i
            self.current_chunk = chunk
        else:
            chunk = self.current_chunk
        
        frame_time = chunk.start + (t - self.cumulative[i][0])
        frame = self.current_video.get_frame(frame_time)
        
        # Изменяем размер кадра до целевого разрешения
        resized_frame = mpy.vfx.resize(mpy.ImageClip(frame), self.target_resolution).get_frame(0)
        
        return resized_frame

# Создаем экземпляр генератора кадров с целевым разрешением
frame_generator = FrameGenerator(VideoChunk.chunks, TARGET_RESOLUTION)

# Создаем видеоклип с использованием генератора кадров
clip = mpy.VideoClip(frame_generator, duration=duration)

output_path = "output_video.mp4"

print("Начало рендеринга видео...")
clip.write_videofile(output_path, fps=FPS)
print(f"Видео сохранено в {output_path}")