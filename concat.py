import os
import random
from moviepy.editor import *
import moviepy.config as cfg
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.font_manager as fm

# Настройки
OUTPUT_WIDTH = 480 // 9 * 16
OUTPUT_HEIGHT = 480
TITLE_DURATION = 1  # Длительность заголовка в секундах
BLUE_COLOR = (21, 99, 165)
WHITE_COLOR = (255, 255, 255)
FONT_SIZE = 70
VIDEOS_FOLDER = 'videos_chunks'  # Папка с видеофайлами
OUTPUT_FPS = 20  # Желаемый FPS для выходного видео

def get_font_path(font_name):
    system_fonts = fm.findSystemFonts()
    for font_path in system_fonts:
        if font_name.lower() in font_path.lower():
            return font_path
    return fm.findfont(fm.FontProperties(family='sans-serif'))

FONT = get_font_path('arial')

def create_title_clip(text):
    img = Image.new('RGB', (OUTPUT_WIDTH, OUTPUT_HEIGHT), color=BLUE_COLOR)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, FONT_SIZE)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((OUTPUT_WIDTH - text_width) // 2, (OUTPUT_HEIGHT - text_height) // 2)
    draw.text(position, text, font=font, fill=WHITE_COLOR)
    return ImageClip(np.array(img)).set_duration(TITLE_DURATION)

def get_video_files(folder):
    video_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                video_files.append(os.path.join(root, file))
    return video_files

def create_video_clip(video_path):
    clip = VideoFileClip(video_path)
    
    # Изменяем FPS видео
    clip = clip.set_fps(OUTPUT_FPS)
    
    # Растягиваем видео на весь экран
    clip = clip.resize((OUTPUT_WIDTH, OUTPUT_HEIGHT))
    
    return clip

# Получаем список всех видеофайлов
video_files = get_video_files(VIDEOS_FOLDER)
random.shuffle(video_files)  # Перемешиваем список для случайного порядка

# Создаем клипы
clips = []
for i, video_file in enumerate(video_files, 1):
    title_clip = create_title_clip(f"top {i}")
    video_clip = create_video_clip(video_file)
    
    # Добавляем паузу после каждого видео
    pause_clip = ColorClip((OUTPUT_WIDTH, OUTPUT_HEIGHT), color=(0, 0, 0), duration=0.5)
    
    clips.append(title_clip)
    clips.append(video_clip)
    clips.append(pause_clip)

# Объединяем все клипы
final_clip = concatenate_videoclips(clips)

# Рендерим итоговое видео
final_clip.write_videofile("top_videos.mp4", 
                           fps=OUTPUT_FPS,
                           codec='libx264',
                           bitrate="100k",
                           audio_bitrate="60k",
                           audio_codec='aac',
                           threads=4)

print("Видео успешно создано!")