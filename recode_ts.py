import os
import subprocess
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

FFMPEG_PATH = r"C:\Users\Admin\Documents\Teardown\movies\ffmpeg.exe"

def collect_video_files(folder_path, output_dir):
    """Сбор только новых видеофайлов из директории и поддиректорий с сортировкой по именам"""
    video_files = []
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm')
    
    file_pairs = []
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(video_extensions):
                source_path = os.path.join(root, file)
                # Создаем путь выходного файла с расширением .ts
                relative_path = os.path.relpath(source_path, folder_path)
                output_path = os.path.join(output_dir, os.path.splitext(relative_path)[0] + '.ts')
                
                if not os.path.exists(output_path):
                    file_pairs.append((os.path.basename(file), source_path))
    
    file_pairs.sort(key=lambda x: x[0])
    video_files = [pair[1] for pair in file_pairs]
                
    return video_files

def create_output_path(source_path, source_dir, output_dir):
    """Создание пути выходного файла с сохранением структуры папок"""
    relative_path = os.path.relpath(source_path, source_dir)
    # Меняем расширение на .ts
    output_path = os.path.join(output_dir, os.path.splitext(relative_path)[0] + '.ts')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    return output_path

def process_video(source_path, source_dir, output_dir):
    """Обработка одного видео через ffmpeg"""
    try:
        output_path = create_output_path(source_path, source_dir, output_dir)
        
        if os.path.exists(output_path):
            return f"Пропущено (существует): {source_path}"

        command = [
            FFMPEG_PATH,
            '-hwaccel', 'cuda',
            '-hwaccel_device', '0',
            '-i', source_path,
            '-c:v', 'h264_nvenc',
            '-profile:v', 'main',
            '-b:v', '200k',
            '-r', '24',
            '-bf', '0',
            '-vf', 'scale=854:480,setsar=1:1',
            '-c:a', 'aac',
            '-ar', '44100',
            '-b:a', '90k',
            '-channels', '2',
            '-f', 'mpegts',
            '-y',
            output_path
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"\nКоманда завершилась с ошибкой (код {e.returncode}):")
            print(f"Сообщение об ошибке:\n{e.stderr}")
            return f"Ошибка при обработке {source_path}: {e.stderr}"
        
        return f"Успешно обработано: {source_path}"

    except Exception as e:
        return f"Ошибка при обработке {source_path}: {str(e)}"

def process_directory(source_dir, target_dir, output_dir):
    """Обработка всей директории"""
    print("Поиск видеофайлов...")
    video_files = collect_video_files(source_dir, output_dir)
    print(f"Найдено видеофайлов: {len(video_files)}")

    if not video_files:
        print("Видеофайлы не найдены")
        return

    max_workers = min(os.cpu_count(), 4)

    with tqdm(total=len(video_files), 
              desc="Обработка видео",
              unit="файл",
              miniters=1,
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
              ) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for source_path in video_files:
                future = executor.submit(
                    process_video,
                    source_path,
                    source_dir,
                    output_dir
                )
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    print(f"\n{result}")
                except Exception as e:
                    print(f"\nОшибка: {str(e)}")
                finally:
                    pbar.update(1)

def main():
    source_dir = "videos_processed/nums"
    output_dir = "videos_processed_ts/nums"
    
    print(f"Начало обработки директории: {source_dir}")
    print(f"Выходная директория: {output_dir}")
    
    process_directory(source_dir, output_dir, output_dir)
    print("\nОбработка завершена!")

if __name__ == "__main__":
    main()