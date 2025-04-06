import os
import math
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import cv2
import subprocess

FFMPEG_PATH = r"C:\Users\Admin\Documents\Teardown\movies\ffmpeg.exe"

def get_video_duration(video_path):
    """Получение длительности видео с помощью OpenCV"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("Не удалось открыть видео")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        cap.release()
        return duration
    except Exception as e:
        print(f"\nОшибка при обработке файла {video_path}: {str(e)}")
        return 0

def process_video(video_path, output_dir, min_chunk_length, max_chunk_length):
    """Обработка одного видео с использованием CUDA"""
    try:
        # Получаем длительность видео
        duration = get_video_duration(video_path)
        if duration == 0:
            return

        # Проверяем, существует ли выходная директория
        os.makedirs(output_dir, exist_ok=True)

        # Вычисляем оптимальную длину чанка
        chunk_length, num_chunks = calculate_optimal_chunk_length(
            duration, min_chunk_length, max_chunk_length
        )

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        
        for i in range(int(num_chunks)):
            start_time = i * chunk_length
            end_time = min((i + 1) * chunk_length, duration)
            output_path = os.path.join(output_dir, f"{base_name}_chunk_{i+1}.mp4")

            # Формируем команду ffmpeg с использованием CUDA
            command = [
                FFMPEG_PATH,
                '-hwaccel', 'cuda',                    # Включаем аппаратное ускорение CUDA
                '-hwaccel_output_format', 'cuda',      # Указываем формат вывода CUDA
                #'-extra_hw_frames', '2',               # Дополнительные кадры для GPU
                '-ss', str(start_time),                # Время начала
                '-i', video_path,                      # Входной файл
                '-t', str(end_time - start_time),      # Длительность
                '-c:v', 'h264_nvenc',                  # Используем NVIDIA энкодер
                #'-preset', 'fast',                       # Максимальная производительность (p1-p7)
                '-tune', 'hq',                         # Настройка качества
                '-rc', 'vbr',                          # Переменный битрейт
                '-cq', '24',                           # Уровень качества
                '-qmin', '24',                         # Минимальное качество
                '-qmax', '24',                         # Максимальное качество
                '-b:v', '1M',                         # Битрейт видео
                '-bufsize', '20M',                     # Размер буфера
                '-c:a', 'aac',                         # Аудиокодек
                '-b:a', '60k',                        # Битрейт аудио
                '-y',                                  # Перезаписывать существующие файлы
                output_path
            ]

            try:
                subprocess.run(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                print(f"\nОшибка при создании чанка {i+1} для {video_path}: {str(e)}")
                continue

    except Exception as e:
        print(f"\nОшибка при обработке файла {video_path}: {str(e)}")

def calculate_optimal_chunk_length(video_duration, min_chunk_length, max_chunk_length):
    """
    Вычисляет оптимальную длину чанка и количество чанков для разделения видео
    
    Args:
        video_duration (float): Длительность видео в секундах
        min_chunk_length (float): Минимальная допустимая длина чанка
        max_chunk_length (float): Максимальная допустимая длина чанка
    
    Returns:
        tuple: (длина_чанка, количество_чанков)
    """
    if video_duration <= min_chunk_length:
        return video_duration, 1
        
    if video_duration <= max_chunk_length:
        return video_duration, 1
    
    # Находим минимальное количество чанков, при котором длина чанка не превысит max_chunk_length
    min_chunks = math.ceil(video_duration / max_chunk_length)
    
    # Находим максимальное количество чанков, при котором длина чанка не меньше min_chunk_length
    max_chunks = math.floor(video_duration / min_chunk_length)
    
    # Перебираем возможные количества чанков от минимального к максимальному
    for num_chunks in range(min_chunks, max_chunks + 1):
        chunk_length = video_duration / num_chunks
        if min_chunk_length <= chunk_length <= max_chunk_length:
            return chunk_length, num_chunks
            
    # Если не нашли подходящее решение, берем вариант с максимальным количеством чанков
    chunk_length = video_duration / max_chunks
    return chunk_length, max_chunks

def create_directory_structure(source_dir, target_dir):
    """Создание структуры директорий"""
    # if os.path.exists(target_dir):
    #     shutil.rmtree(target_dir)
    
    for root, dirs, _ in os.walk(source_dir):
        for dir_name in dirs:
            source_path = os.path.join(root, dir_name)
            relative_path = os.path.relpath(source_path, source_dir)
            target_path = os.path.join(target_dir, relative_path)
            os.makedirs(target_path, exist_ok=True)

def process_directory(source_dir, target_dir, min_chunk_length, max_chunk_length):
    """Обработка всей директории"""
    create_directory_structure(source_dir, target_dir)
    
    video_files = []
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm')
    
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.lower().endswith(video_extensions):
                source_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, source_dir)
                target_path = os.path.join(target_dir, relative_path)
                video_files.append((source_path, target_path))
    
    # Ограничиваем количество одновременных процессов
    max_workers = min(os.cpu_count(), 4)  # Не более 4 параллельных процессов
    
    with tqdm(total=len(video_files), desc="Обработка видео") as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for source_path, target_path in video_files:
                future = executor.submit(
                    process_video,
                    source_path,
                    target_path,
                    min_chunk_length,
                    max_chunk_length
                )
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"\nОшибка при обработке: {str(e)}")
                finally:
                    pbar.update(1)

def main():
    source_dir = "videos/yt_manual_brainrot"
    target_dir = "videos_chunks/yt_manual_brainrot"
    min_chunk_length = 1.5
    max_chunk_length = 2.5
    
    print(f"Начало обработки директории {source_dir}")
    print(f"Длина чанков: от {min_chunk_length} до {max_chunk_length} секунд")
    
    process_directory(source_dir, target_dir, min_chunk_length, max_chunk_length)
    
    print("\nОбработка завершена!")

if __name__ == "__main__":
    main()