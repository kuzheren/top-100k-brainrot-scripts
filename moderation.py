import cv2
import os
import numpy as np
import time
from nudenet import NudeDetector

nsfw_labels = [
    "FEMALE_GENITALIA_COVERED",
    "BUTTOCKS_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_BREAST_EXPOSED",
    "ANUS_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "ANUS_COVERED",
    "BUTTOCKS_COVERED",
]

# Инициализация детектора NudeNet
detector = NudeDetector()

# Директория для сохранения кадров с наготой
output_dir = "nude_frames"
os.makedirs(output_dir, exist_ok=True)  # Создаем директорию, если она не существует

def analyze_video(video_path, batch_size=100):
    # Открываем видео файл
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Ошибка при открытии видео файла")
        return

    frame_count = 0
    nude_frames = []
    frame_batches = []
    batch_number = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Обрабатываем только каждый второй кадр
        if frame_count % 2 == 0:
            # Конвертируем кадр в формат, подходящий для NudeNet
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Конвертируем BGR в RGB
            frame_batches.append((frame, frame_count))

            # Если набрался полный батч, анализируем
            if len(frame_batches) == batch_size:
                batch_number += 1  # Увеличиваем счетчик батчей
                print(f"\nОбработка батча #{batch_number}...")
                analyze_batch(frame_batches, nude_frames, batch_number)
                frame_batches = []

    # Анализируем остатки, если есть
    if frame_batches:
        batch_number += 1
        print(f"\nОбработка последнего батча #{batch_number}...")
        analyze_batch(frame_batches, nude_frames, batch_number)

    # Освобождаем ресурсы
    cap.release()

    return nude_frames

def analyze_batch(frame_batches, nude_frames, batch_number):
    """Функция для анализа батча кадров."""
    start_time = time.time()

    frames = np.array([fb[0] for fb in frame_batches])  # Извлекаем кадры
    frame_counts = [fb[1] for fb in frame_batches]  # Номера кадров

    # Анализируем батч изображений
    results = detector.detect_batch(frames)

    for count, result in zip(frame_counts, results):
        # Проверяем, есть ли хотя бы одно обнаружение с score > 0.5
        nude_detected = any(found["class"] in nsfw_labels and found["score"] > 0.5 for found in result)

        if nude_detected:
            print(f"Кадр {count} - Нагота обнаружена: {result}")
            nude_frames.append(count)

            # Сохраняем кадр с наготой
            # Находим индекс кадра в текущем батче
            frame_index_in_batch = frame_counts.index(count)
            frame_to_save = cv2.cvtColor(frames[frame_index_in_batch], cv2.COLOR_RGB2BGR)  # Конвертируем обратно в BGR
            output_filename = os.path.join(output_dir, f"nude_frame_{count}.jpg")
            cv2.imwrite(output_filename, frame_to_save)  # Сохраняем кадр
        else:
            print(f"Кадр {count} - Нагота не обнаружена")

    end_time = time.time()  # Засекаем время окончания обработки батча
    processing_time = end_time - start_time

    # Выводим информацию о времени обработки батча
    print(f"\nБатч #{batch_number} обработан за {processing_time:.2f} секунд")
    print(f"Среднее время на кадр: {(processing_time/len(frame_batches)):.4f} секунд")

# Пример использования
video_file = r"F:\Python\TikTokTest\output.mp4"
video_file = r"F:\Python\TikTokTest\videos\compilations1\10 h memes\10 hrs of memes for no reason... [i1H581TCc4A].webm"
nude_frames_list = analyze_video(video_file)

print(f"Нагота обнаружена в кадрах: {nude_frames_list}")