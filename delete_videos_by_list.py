import os

def read_numbers_to_delete(filename):
    """Чтение списка номеров из файла."""
    with open(filename, 'r') as f:
        # Считываем строки и разбиваем по пробелам, чтобы обработать несколько чисел в одной строке
        numbers = []
        for line in f:
            numbers.extend(line.strip().split())
        return [num for num in numbers if num]  # Удаляем пустые строки

def read_video_list(filename):
    """Чтение списка путей к видео из файла."""
    with open(filename, 'r') as f:
        video_paths = [line.strip() for line in f if line.strip().startswith('file ')]
    return video_paths

def find_videos_to_delete(numbers, video_paths):
    """Поиск видео для удаления на основе указанных номеров."""
    videos_to_delete = []
    for number in numbers:
        for i, path in enumerate(video_paths):
            if f"number_{number}_audio.ts" in path and i + 1 < len(video_paths):
                videos_to_delete.append(video_paths[i + 1])
                break
    return videos_to_delete

def main():
    # Запрос путей к файлам
    numbers_file = input("Введите путь к файлу с номерами для удаления (по умолчанию: raw.txt_processed.txt): ") or "raw.txt_processed.txt"
    videos_file = input("Введите путь к файлу со списком видео: ")
    
    # Чтение данных
    try:
        numbers = read_numbers_to_delete(numbers_file)
    except Exception as e:
        print(f"Ошибка при чтении файла с номерами: {e}")
        return
    
    try:
        video_paths = read_video_list(videos_file)
    except Exception as e:
        print(f"Ошибка при чтении файла со списком видео: {e}")
        return
    
    # Поиск видео для удаления
    videos_to_delete = find_videos_to_delete(numbers, video_paths)
    
    # Вывод списка видео для удаления
    if not videos_to_delete:
        print("\nНет видео для удаления.")
        return
    
    print("\nВидео для удаления:")
    for video in videos_to_delete:
        print(video)
    
    # Запрос подтверждения
    confirm = input("\nВы уверены, что хотите удалить эти видео? (да/нет): ")
    
    # Удаление при подтверждении
    if confirm.lower() in ['да', 'yes', 'y']:
        for video in videos_to_delete:
            # Извлечение фактического пути (удаление префикса 'file ' и кавычек)
            path = video.replace('file ', '').strip("'\"")
            if os.path.exists(path):
                os.remove(path)
                print(f"Удалено: {path}")
            else:
                print(f"Файл не найден: {path}")
        print("Удаление завершено.")
    else:
        print("Удаление отменено.")

if __name__ == "__main__":
    main()
