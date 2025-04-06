import os
from pathlib import Path

# Конфигурация - укажите здесь нужные папки
SELECTED_FOLDERS = ['swag like ohio', 'don pollo', 'hood irony']  # Папки, которые нужно обработать
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mkv']  # Расширения видеофайлов

def get_all_videos(base_path, selected_folders):
    """Получает все видеофайлы из выбранных папок и их подпапок"""
    video_files = []
    
    for folder in selected_folders:
        folder_path = base_path / folder
        if not folder_path.exists():
            print(f"Предупреждение: папка {folder_path} не найдена")
            continue
            
        # Рекурсивный обход всех подпапок
        for root, _, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                    # Используем относительный путь от корня проекта
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(base_path)
                    video_files.append(str(rel_path))
    
    return sorted(video_files)  # Сортируем файлы для последовательности

def create_concat_file(video_files, output_file, base_path):
    """Создает файл со списком видео для FFmpeg"""
    with open(output_file, 'w', encoding='utf-8') as f:
        for video in video_files:
            # Получаем абсолютный путь и заменяем разделители
            full_path = str(base_path / video).replace('\\', '/')
            f.write(f"file '{full_path}'\n")

def main():
    # Получаем путь к корневой директории проекта
    project_root = Path(__file__).parent
    video_chunks_path = project_root / 'videos_processed'
    work_path = project_root / 'work'
    
    # Создаем work директорию если её нет
    work_path.mkdir(exist_ok=True)
    
    # Получаем список всех видео
    videos = get_all_videos(video_chunks_path, SELECTED_FOLDERS)
    
    # Выводим найденные файлы
    print(f"Найдено {len(videos)} видеофайлов:")
    for video in videos:
        print(f"- {video}")
    
    # Создаем файл для FFmpeg
    output_file = work_path / 'list.txt'
    create_concat_file(videos, output_file, video_chunks_path)
    print(f"\nСоздан файл списка: {output_file}")

if __name__ == "__main__":
    main()