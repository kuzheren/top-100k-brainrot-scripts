import cv2
import os
import numpy as np
import time
from nudenet import NudeDetector
import multiprocessing

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

def process_batch(batch_data):
    """Функция для обработки одного батча кадров в отдельном процессе."""
    batch_number, frame_batches = batch_data
    start_time = time.time()
    nude_frames_in_batch = []

    frames = np.array([fb[0] for fb in frame_batches])  # Извлекаем кадры
    frame_counts = [fb[1] for fb in frame_batches]  # Номера кадров

    # Анализируем батч изображений
    results = detector.detect_batch(frames)

    for i, result in enumerate(results):
        count = frame_counts[i]
        # Проверяем, есть ли хотя бы одно обнаружение с score > 0.5
        nude_detected = any(found["class"] in nsfw_labels and found["score"] > 0.5 for found in result)

        if nude_detected:
            print(f"Батч #{batch_number} - Кадр {count} - Нагота обнаружена: {result}")
            nude_frames_in_batch.append(count)

            # Сохраняем кадр с наготой
            frame_to_save = cv2.cvtColor(frames[i], cv2.COLOR_RGB2BGR)  # Конвертируем обратно в BGR
            output_filename = os.path.join(output_dir, f"nude_frame_{count}.jpg")
            cv2.imwrite(output_filename, frame_to_save)  # Сохраняем кадр
        else:
            pass
            # print(f"Батч #{batch_number} - Кадр {count} - Нагота не обнаружена")

    end_time = time.time()  # Засекаем время окончания обработки батча
    processing_time = end_time - start_time

    # Возвращаем результаты обработки батча
    return nude_frames_in_batch, processing_time, len(frame_batches), batch_number

def analyze_video(video_path, batch_size=1000):
    # Открываем видео файл
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Ошибка при открытии видео файла")
        return []

    frame_count = 0
    all_nude_frames = []
    frame_batches = []
    batch_number = 0

    # Считываем все кадры и добавляем их в батчи
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

        # Конвертируем кадр в формат, подходящий для NudeNet
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Конвертируем BGR в RGB
        frame_batches.append((frame, frame_count))

        # Если набрался полный батч, отправляем на обработку
        if len(frame_batches) == batch_size:
            batch_number += 1
            yield (batch_number, frame_batches)
            frame_batches = []

    # Отправляем оставшиеся кадры на обработку
    if frame_batches:
        batch_number += 1
        yield (batch_number, frame_batches)

    # Освобождаем ресурсы
    cap.release()

def main(video_file, batch_size=1000, num_processes=4): # num_processes - количество параллельных процессов
    start_time_total = time.time()
    nude_frames_list = []
    total_frames_processed = 0
    total_processing_time = 0

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.imap_unordered(process_batch, analyze_video(video_file, batch_size=batch_size))
        for nude_frames_batch, processing_time, num_frames, batch_number in results:
            nude_frames_list.extend(nude_frames_batch)
            total_processing_time += processing_time
            total_frames_processed += num_frames
            print(f"\nБатч #{batch_number} обработан за {processing_time:.2f} секунд")
            print(f"Обработано {num_frames} кадров")

    end_time_total = time.time()
    total_time = end_time_total - start_time_total
    average_time_per_frame = total_time / total_frames_processed if total_frames_processed > 0 else 0

    print(f"Общее время обработки: {total_time:.2f} секунд")
    print(f"Всего обработано кадров: {total_frames_processed}")
    print(f"Нагота обнаружена в кадрах: {sorted(nude_frames_list)}")
    print(f"Среднее время обработки кадра (параллельно): {average_time_per_frame:.4f} секунд")

if __name__ == "__main__":
    video_file = r"F:\Python\TikTokTest\output.mp4"
    main(video_file)