import os
from tqdm import tqdm

def collect_empty_videos(folder_path):
    """Сбор всех пустых видеофайлов из директории и поддиректорий"""
    empty_files = []
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm')
    
    print("Поиск пустых видеофайлов...")
    for root, _, files in tqdm(list(os.walk(folder_path)), desc="Сканирование директорий"):
        for file in files:
            if file.lower().endswith(video_extensions):
                file_path = os.path.join(root, file)
                if os.path.getsize(file_path) == 0:
                    empty_files.append(file_path)
    
    return empty_files

def delete_files(files):
    """Удаление файлов с подтверждением"""
    if not files:
        print("\nПустых видеофайлов не найдено")
        return

    print(f"\nНайдено пустых видеофайлов: {len(files)}")
    print("\nСписок файлов для удаления:")
    for file in files:
        print(f"- {file}")

    confirmation = input("\nУдалить эти файлы? (y/n): ").lower()
    if confirmation == 'y':
        deleted_count = 0
        with tqdm(total=len(files), desc="Удаление файлов") as pbar:
            for file in files:
                try:
                    os.remove(file)
                    deleted_count += 1
                except Exception as e:
                    print(f"\nОшибка при удалении {file}: {e}")
                finally:
                    pbar.update(1)
        
        print(f"\nУдалено файлов: {deleted_count} из {len(files)}")
    else:
        print("\nУдаление отменено")

def main():
    folder_path = "videos_processed"
    
    print(f"Начало проверки директории: {folder_path}")
    empty_files = collect_empty_videos(folder_path)
    delete_files(empty_files)
    print("\nПроверка завершена!")

if __name__ == "__main__":
    main()