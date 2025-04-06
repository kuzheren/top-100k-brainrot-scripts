import os
from moviepy.editor import VideoFileClip
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import cv2

def collect_video_files(folder_path):
    video_files = []
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.ts')
    
    video_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(folder_path)
        for file in files
        if file.lower().endswith(video_extensions)
    ]
    
    return video_files

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
        return duration, video_path, None
    except Exception as e:
        return 0, video_path, str(e)

def calculate_total_duration(video_files, max_workers=None):
    total_duration = 0
    failed_videos = []
    
    with tqdm(total=len(video_files), desc="Обработка видео") as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_video = {
                executor.submit(get_video_duration, video_file): video_file 
                for video_file in video_files
            }
            
            for future in as_completed(future_to_video):
                duration, video_file, error = future.result()
                if error:
                    failed_videos.append((video_file, error))
                else:
                    total_duration += duration
                pbar.update(1)
                pbar.set_description(f"Обработка: {os.path.basename(video_file)}")
                
    return total_duration, failed_videos

def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def delete_files(files):
    """Удаление файлов с подтверждением"""
    if not files:
        return
        
    print(f"\nБудут удалены следующие файлы:")
    for file, error in files:
        print(f"- {file}")
        print(f"  Причина: {error}")
    
    confirmation = input("\nУдалить эти файлы? (y/n): ").lower()
    if confirmation == 'y':
        deleted_count = 0
        for file, _ in files:
            try:
                os.remove(file)
                deleted_count += 1
            except Exception as e:
                print(f"Ошибка при удалении {file}: {e}")
        print(f"\nУдалено файлов: {deleted_count} из {len(files)}")
    else:
        print("\nУдаление отменено")

def main():
    folder_path = "videos/yt_manual_brainrot"
    
    print("Поиск видеофайлов...")
    video_files = collect_video_files(folder_path)
    print(f"Найдено видеофайлов: {len(video_files)}")
    
    if video_files:
        max_workers = os.cpu_count() * 2
        total_duration, failed_videos = calculate_total_duration(video_files, max_workers)
        
        print(f"\nОбщая длительность: {format_duration(total_duration)}")
        
        if failed_videos:
            print(f"\nНайдено сломанных видео: {len(failed_videos)}")
            delete_files(failed_videos)
    else:
        print("Видеофайлы не найдены")

if __name__ == "__main__":
    main()