import os
import random
from moviepy.editor import *
import moviepy.config as cfg
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.font_manager as fm
from tqdm import tqdm

# Настройки
OUTPUT_WIDTH = 1280
OUTPUT_HEIGHT = 720
TITLE_DURATION = 1  # Длительность заголовка в секундах
PAUSE_DURATION = 0.5  # Длительность паузы после видео
BLUE_COLOR = (21, 99, 165)
WHITE_COLOR = (255, 255, 255)
FONT_SIZE = 70
VIDEOS_FOLDER = 'test_videos'  # Папка с видеофайлами
OUTPUT_FPS = 20  # Желаемый FPS для выходного видео

def get_font_path(font_name):
    system_fonts = fm.findSystemFonts()
    for font_path in system_fonts:
        if font_name.lower() in font_path.lower():
            return font_path
    return fm.findfont(fm.FontProperties(family='sans-serif'))

FONT = get_font_path('arial')

def create_title_image(text):
    img = Image.new('RGB', (OUTPUT_WIDTH, OUTPUT_HEIGHT), color=BLUE_COLOR)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, FONT_SIZE)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((OUTPUT_WIDTH - text_width) // 2, (OUTPUT_HEIGHT - text_height) // 2)
    draw.text(position, text, font=font, fill=WHITE_COLOR)
    return np.array(img)

def get_video_files(folder):
    video_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_files.append(os.path.join(root, file))
    return video_files

def get_video_duration(filepath):
    """Получает длительность видео и проверяет его валидность"""
    try:
        clip = VideoFileClip(filepath)
        duration = clip.duration
        clip.close()
        return duration
    except:
        print(f"Ошибка при проверке файла: {filepath}")
        return None

class VideoInfo:
    def __init__(self, path, duration, start_time):
        self.path = path
        self.duration = duration
        self.start_time = start_time
        self.title_time = start_time - TITLE_DURATION
        self.end_time = start_time + duration
        self.pause_time = self.end_time
        self.segment_end = self.pause_time + PAUSE_DURATION
        self.clip = None

def make_frame(t):
    global video_infos, current_clip_index
    
    # Показываем первый заголовок
    if t < TITLE_DURATION:
        return create_title_image(f"top {total_clips}")
    
    # Находим текущий видеофрагмент
    while current_clip_index < len(video_infos) and t >= video_infos[current_clip_index].segment_end:
        if video_infos[current_clip_index].clip is not None:
            video_infos[current_clip_index].clip.close()
            video_infos[current_clip_index].clip = None
        current_clip_index += 1
    
    if current_clip_index >= len(video_infos):
        return np.zeros((OUTPUT_HEIGHT, OUTPUT_WIDTH, 3), dtype=np.uint8)
    
    video_info = video_infos[current_clip_index]
    
    # Показываем заголовок
    if t >= video_info.title_time and t < video_info.start_time:
        return create_title_image(f"top {total_clips - current_clip_index}")
    
    # Показываем видео
    if t >= video_info.start_time and t < video_info.end_time:
        if video_info.clip is None:
            video_info.clip = VideoFileClip(video_info.path).resize((OUTPUT_WIDTH, OUTPUT_HEIGHT)).set_fps(OUTPUT_FPS)
        return video_info.clip.get_frame(t - video_info.start_time)
    
    # Показываем паузу
    return np.zeros((OUTPUT_HEIGHT, OUTPUT_WIDTH, 3), dtype=np.uint8)

print("Поиск видеофайлов...")
video_files = get_video_files(VIDEOS_FOLDER)
print(f"Найдено файлов: {len(video_files)}")

print("Проверка валидности видеофайлов и получение длительности...")
valid_videos = []
for file in tqdm(video_files, desc="Проверка файлов"):
    duration = get_video_duration(file)
    if duration is not None:
        valid_videos.append((file, duration))

if not valid_videos:
    print("Не найдено корректных видеофайлов!")
    exit()

print(f"Найдено корректных видео: {len(valid_videos)} из {len(video_files)}")

random.shuffle(valid_videos)

# Создаем информацию о расположении видео во времени
current_time = TITLE_DURATION
video_infos = []
for file, duration in valid_videos:
    video_infos.append(VideoInfo(file, duration, current_time))
    current_time += duration + TITLE_DURATION + PAUSE_DURATION

total_clips = len(video_infos)
total_duration = current_time

# ... (предыдущий код остается без изменений до обработки аудио)

# Подготовка аудио
print("Подготовка аудио...")
final_audio_clips = []

# Добавляем тишину для первого заголовка
first_title_silence = AudioClip(lambda t: 0, duration=TITLE_DURATION)
final_audio_clips.append(first_title_silence)

for video_info in tqdm(video_infos, desc="Обработка аудио"):
    # Добавляем тишину для заголовка
    title_silence = AudioClip(lambda t: 0, duration=TITLE_DURATION)
    final_audio_clips.append(title_silence)
    
    # Загружаем видео и получаем аудио
    clip = VideoFileClip(video_info.path)
    if clip.audio is not None:
        # Создаем копию аудио перед закрытием видео
        audio = clip.audio.copy()
        final_audio_clips.append(audio)
    else:
        silence = AudioClip(lambda t: 0, duration=video_info.duration)
        final_audio_clips.append(silence)
    
    # Закрываем видеоклип
    clip.close()
    
    # Добавляем тишину для паузы
    pause_silence = AudioClip(lambda t: 0, duration=PAUSE_DURATION)
    final_audio_clips.append(pause_silence)

# Глобальные переменные для make_frame
current_clip_index = 0

print("Создание итогового видео...")
video_clip = VideoClip(make_frame, duration=total_duration)

print("Объединение аудио...")
final_audio = concatenate_audioclips(final_audio_clips)
video_clip = video_clip.set_audio(final_audio)

print(f"Рендеринг финального видео (ожидаемая длительность: {total_duration:.1f} сек)...")
video_clip.write_videofile("top_videos.mp4", 
                           fps=OUTPUT_FPS,
                           codec='libx264',
                           bitrate="100k",
                           audio_codec='aac',
                           threads=4)

# Очистка памяти
for video_info in video_infos:
    if video_info.clip is not None:
        video_info.clip.close()

for audio_clip in final_audio_clips:
    if hasattr(audio_clip, 'close'):
        audio_clip.close()

print("Видео успешно создано!")