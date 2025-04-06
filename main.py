import os
import video_downloader
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_single_video(link, prefix):
    try:
        print(f"Скачиваю видео: {link} с префиксом {prefix}")
        if video_downloader.download_video(link, prefix):
            print(f"Успешно скачано видео: {link} с префиксом {prefix}")
            return True
    except Exception as e:
        print(f"Ошибка при скачивании {link}: {str(e)}")
    return False

def process_txt_files():
    # Путь к папке с .txt файлами
    folder_path = 'list'
    
    # Создаем список задач для выполнения
    tasks = []

    # Перебираем все файлы в папке
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            # Получаем имя файла без расширения как префикс
            prefix = os.path.splitext(filename)[0]
            
            # Полный путь к файлу
            file_path = os.path.join(folder_path, filename)
            
            # Читаем ссылки из файла
            with open(file_path, 'r', encoding='utf-8') as file:
                links = file.read().splitlines()
            
            # Добавляем задачи в список
            for link in links:
                tasks.append((link, prefix))

    # Запускаем параллельное скачивание в 4 потока
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(download_single_video, link, prefix) for link, prefix in tasks]
        
        for future in as_completed(futures):
            # Здесь можно добавить дополнительную обработку результатов, если нужно
            pass

if __name__ == "__main__":
    process_txt_files()