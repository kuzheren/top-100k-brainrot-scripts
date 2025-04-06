from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
import numpy as np
import moviepy.editor as mpy
import os
import concurrent.futures
import random
import bisect
import tempfile
import shutil

FPS = 20
MIN_CHUNK_LEN = 2.0
MAX_CHUNK_LEN = 4.0
TEXT_DURATION = 1  # Длительность показа текста перед каждым чанком

TARGET_RESOLUTION = (1280, 720)
FONT_SIZE = 100
FONT = "arial.ttf"  # Убедитесь, что у вас есть этот шрифт или замените на другой
BLUE_COLOR = (21, 99, 165)
WHITE_COLOR = (255, 255, 255)

video_folder = "videos"
temp_folder = "temp_audio_files"

# Создаем временную папку для аудио файлов
os.makedirs(temp_folder, exist_ok=True)

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

def create_text_image(text):
    img = Image.new('RGB', TARGET_RESOLUTION, color=BLUE_COLOR)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, FONT_SIZE)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((TARGET_RESOLUTION[0] - text_width) / 2, (TARGET_RESOLUTION[1] - text_height) / 2)
    draw.text(position, text, font=font, fill=WHITE_COLOR)
    return np.array(img)

class FrameGenerator:
    def __init__(self, chunks, target_resolution):
        self.chunks = chunks
        self.target_resolution = target_resolution
        self.cumulative = []
        total = 0
        for i, chunk in enumerate(self.chunks):
            text_duration = TEXT_DURATION
            chunk_duration = chunk.end - chunk.start
            self.cumulative.append((total, total + text_duration, f"number {len(chunks) - i}"))
            total += text_duration
            self.cumulative.append((total, total + chunk_duration, chunk))
            total += chunk_duration
        self.current_chunk_index = -1
        self.current_video = None
        self.current_chunk = None

    def __call__(self, t):
        if t >= self.cumulative[-1][1] or t < 0:
            return np.zeros((self.target_resolution[1], self.target_resolution[0], 3), dtype=np.uint8)
        
        i = bisect.bisect_right(self.cumulative, (t,)) - 1
        
        if i < 0:
            return np.zeros((self.target_resolution[1], self.target_resolution[0], 3), dtype=np.uint8)
        
        item = self.cumulative[i][2]
        
        if isinstance(item, str):  # Это текст
            return create_text_image(item)
        
        if i != self.current_chunk_index:
            if self.current_video:
                self.current_video.close()
            chunk = item
            self.current_video = mpy.VideoFileClip(chunk.source_path)
            self.current_chunk_index = i
            self.current_chunk = chunk
        else:
            chunk = self.current_chunk
        
        frame_time = chunk.start + (t - self.cumulative[i][0])
        frame = self.current_video.get_frame(frame_time)
        
        resized_frame = mpy.vfx.resize(mpy.ImageClip(frame), self.target_resolution).get_frame(0)
        
        return resized_frame

frame_generator = FrameGenerator(VideoChunk.chunks, TARGET_RESOLUTION)

duration = sum(chunk[1] - chunk[0] for chunk in frame_generator.cumulative)
print(f"Общая длительность: {duration:.2f} секунд")

video_clip = mpy.VideoClip(frame_generator, duration=duration)

# Создаем аудио клипы для каждого чанка
audio_clips = []
for i, (start, end, item) in enumerate(frame_generator.cumulative):
    if isinstance(item, VideoChunk):
        video = mpy.VideoFileClip(item.source_path)
        audio = video.audio.subclip(item.start, item.end)
        temp_audio_file = os.path.join(temp_folder, f"temp_audio_{i}.mp3")
        audio.write_audiofile(temp_audio_file)
        audio_clip = mpy.AudioFileClip(temp_audio_file).set_start(start)
        audio_clips.append(audio_clip)
        video.close()
    else:
        # Добавляем тишину для текстовых частей
        silence = mpy.AudioClip(lambda t: 0, duration=end-start).set_start(start)
        audio_clips.append(silence)

# Объединяем все аудио клипы
final_audio = mpy.CompositeAudioClip(audio_clips)

# Добавляем аудио к видео
video_clip = video_clip.set_audio(final_audio)

output_path = "output_video.mp4"

print("Начало рендеринга видео...")
video_clip.write_videofile(output_path, fps=FPS, bitrate="220k", audio_bitrate="32k")
print(f"Видео сохранено в {output_path}")

# Удаляем временные аудио файлы
shutil.rmtree(temp_folder)