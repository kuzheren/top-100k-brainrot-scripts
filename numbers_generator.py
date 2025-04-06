from moviepy.editor import *
import moviepy.config as cfg
from PIL import Image, ImageDraw, ImageFont
import os
import numpy as np
import matplotlib.font_manager as fm
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Настройки
VIDEO_WIDTH = 854  # Соответствует 480p с аспектом 16:9
VIDEO_HEIGHT = 480
DURATION = 1  # Длительность каждого видео в секундах
FONT_SIZE = 70
BLUE_COLOR = (21, 99, 165)
WHITE_COLOR = (255, 255, 255)
OUTPUT_DIR = "number_videos"
FPS = 24  # Соответствует параметру -r 24 из ffmpeg

cfg.change_settings({"FFMPEG_BINARY": r"C:\Users\Admin\Documents\Teardown\movies\ffmpeg.exe"})

# Получаем путь к шрифту
def get_font_path(font_name):
    system_fonts = fm.findSystemFonts()
    for font_path in system_fonts:
        if font_name.lower() in font_path.lower():
            return font_path
    return fm.findfont(fm.FontProperties(family='sans-serif'))

FONT = get_font_path('arial')

def create_text_image(text):
    """Создание изображения с текстом"""
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), color=BLUE_COLOR)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, FONT_SIZE)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((VIDEO_WIDTH - text_width) / 2, (VIDEO_HEIGHT - text_height) / 2)
    draw.text(position, text, font=font, fill=WHITE_COLOR)
    return img

def create_video(number):
    """Создание одного видео с номером"""
    try:
        output_path = os.path.join(OUTPUT_DIR, f"number_{number}.mp4")
        
        # Пропускаем если файл уже существует
        if os.path.exists(output_path):
            return f"Пропущено (существует): number_{number}.mp4"

        # Создаем изображение с текстом
        img = create_text_image(f"number {number}")
        
        # Создаем видеоклип
        clip = ImageClip(np.array(img)).set_duration(DURATION)
        
        # Рендерим видео с параметрами, совместимыми с ffmpeg
        clip.write_videofile(
            output_path,
            fps=FPS,
            codec='libx264',
            bitrate='200k',
            audio=False,  # Без звука
            threads=1,    # Один поток на видео
            preset='fast',
            ffmpeg_params=[
                '-aspect', '16:9',
                '-bufsize', '1024k'
            ]
        )
        
        return f"Создано: number_{number}.mp4"
    except Exception as e:
        return f"Ошибка при создании number_{number}.mp4: {str(e)}"

def main():
    # Создаем выходную директорию
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    total_videos = 100000
    max_workers = min(os.cpu_count(), 4)  # Не более 4 параллельных процессов
    
    print(f"Начало создания {total_videos} видео...")
    
    with tqdm(total=total_videos, desc="Создание видео") as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for number in range(1, total_videos + 1):
                future = executor.submit(create_video, number)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    print(f"\n{result}")
                except Exception as e:
                    print(f"\nОшибка: {str(e)}")
                finally:
                    pbar.update(1)
    
    print("\nСоздание видео завершено!")

if __name__ == "__main__":
    main()