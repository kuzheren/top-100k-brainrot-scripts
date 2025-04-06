import os
import cv2
import numpy as np
import random

# Настройки
video_folder = 'videos'
max_memes = 100  # Ограничитель количества мемов
output_video_name = f'top_{max_memes}_memes.mp4'
welcome_slide_duration = 3  # Длительность приветственного слайда в секундах
number_slide_duration = 2  # Длительность слайда с номером в секундах
welcome_text = "hi guys\nhere's cool memes\nlik+sub"

# Функция для создания слайда с текстом
def create_text_slide(text, size=(1280, 720)):
    img = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    textsize = cv2.getTextSize(text, font, 2, 3)[0]
    text_x = (size[0] - textsize[0]) // 2
    text_y = (size[1] + textsize[1]) // 2
    cv2.putText(img, text, (text_x, text_y), font, 2, (255, 255, 255), 3, cv2.LINE_AA)
    return img

# Функция для разделения видео на отрезки
def split_video_into_segments(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    segment_count = max(1, int(duration // 3))
    segment_length = duration / segment_count

    segments = []
    for i in range(segment_count):
        start = i * segment_length
        end = min((i + 1) * segment_length, duration)
        segments.append((start, end))

    cap.release()
    return segments

# Собираем все видеофайлы
video_files = []
for root, dirs, files in os.walk(video_folder):
    for file in files:
        if file.endswith(('.mp4', '.avi', '.mov')):
            video_files.append(os.path.join(root, file))

# Перемешиваем и ограничиваем количество видео
random.shuffle(video_files)
video_files = video_files[:max_memes]

# Создаем сегменты для всех видео
all_segments = []
for video_file in video_files:
    segments = split_video_into_segments(video_file)
    all_segments.extend([(video_file, start, end) for start, end in segments])

# Перемешиваем сегменты
random.shuffle(all_segments)

# Создаем итоговое видео
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_name, fourcc, 30, (1280, 720))

# Добавляем приветственный слайд
welcome_slide = create_text_slide(welcome_text)
for _ in range(int(welcome_slide_duration * 30)):
    out.write(welcome_slide)

# Добавляем сегменты видео и слайды с номерами
for i, (video_file, start, end) in enumerate(all_segments):
    # Слайд с номером
    number_slide = create_text_slide(f"Number {len(all_segments) - i}")
    for _ in range(int(number_slide_duration * 30)):
        out.write(number_slide)

    # Сегмент видео
    cap = cv2.VideoCapture(video_file)
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    while cap.get(cv2.CAP_PROP_POS_MSEC) < end * 1000:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (1280, 720))
        out.write(frame)
    cap.release()

# Закрываем видеофайл
out.release()

print(f"Видео '{output_video_name}' успешно создано!")