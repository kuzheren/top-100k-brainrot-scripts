import os
from tqdm import tqdm

def create_videos_list(folder_path, output_file):
    """Создание файла списка видео для ffmpeg"""
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm')
    
    print("Поиск видеофайлов...")
    video_files = []
    for root, _, files in tqdm(list(os.walk(folder_path))):
        for file in files:
            if file.lower().endswith(video_extensions):
                # Получаем полный путь к файлу
                full_path = os.path.abspath(os.path.join(root, file))
                video_files.append(full_path)
    
    if not video_files:
        print("Видеофайлы не найдены")
        return 0
        
    print(f"\nНайдено видеофайлов: {len(video_files)}")
    print(f"\nСоздание файла списка {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for video_path in video_files:
            f.write(f"{video_path}\n")
    
    return len(video_files)

def main():
    # Параметры
    videos_dir = "number_videos"  # Директория с видео
    output_file = "work/numbers.txt"  # Выходной файл списка
    
    print(f"Начало создания списка видео из {videos_dir}")
    
    # Создаем директорию для выходного файла если её нет
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Создаем список для конкатенации
    total_videos = create_videos_list(videos_dir, output_file)
    
    if total_videos > 0:
        print(f"\nСоздан файл списка для {total_videos} видео")
        print(f"Путь к файлу списка: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()