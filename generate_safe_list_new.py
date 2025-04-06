#!/usr/bin/env python3
import os
import re
import random

def extract_number(file_path):
    """
    Извлекает номер из строки вида "number_XXXXX_audio".
    """
    match = re.search(r'number_(\d+)_audio', file_path)
    if match:
        return int(match.group(1))
    return None

def is_in_safe_range(number):
    """
    Проверяет, попадает ли число в один из безопасных диапазонов.
    """
    safe_ranges = [
        (100000, 90000),
        (90000, 85000),
        (80000, 70000),
        (70000, 60000),
        (60000, 50000),
        (50000, 40000),
        (40000, 35000),
        (30000, 29000)
    ]
    for start, end in safe_ranges:
        if start >= number >= end:
            return True
    return False

def is_in_top_range(number):
    """
    Проверяет, находится ли число в диапазоне первой 1000 с конца (100000-99000).
    """
    return 100000 >= number >= 99000

def load_dangerous_ids(dangerous_ids_file):
    """
    Загружает ID запрещённых (опасных) видео из файла.
    """
    dangerous_ids = set()
    try:
        with open(dangerous_ids_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    dangerous_ids.add(int(line.strip()))
                except ValueError:
                    continue
    except FileNotFoundError:
        print(f"Файл {dangerous_ids_file} не найден. Продолжаем без списка опасных ID.")
    return dangerous_ids

def load_manual_chunks(manual_chunks_dir):
    """
    Загружает все файлы .ts из указанной папки, превращая путь в абсолютный с прямыми слэшами,
    перемешивает список и возвращает его.
    """
    manual_files = []
    try:
        for fname in os.listdir(manual_chunks_dir):
            if fname.lower().endswith('.ts'):
                full_path = os.path.abspath(os.path.join(manual_chunks_dir, fname))
                full_path = full_path.replace('\\', '/')
                manual_files.append(full_path)
    except Exception as e:
        print(f"Ошибка при чтении папки {manual_chunks_dir}: {e}")
    random.shuffle(manual_files)
    return manual_files

def file_exists(file_path):
    """
    Проверяет, существует ли файл по указанному пути.
    """
    cleaned_path = file_path
    if cleaned_path.startswith("file '") and cleaned_path.endswith("'"):
        cleaned_path = cleaned_path[6:-1]  # Убираем "file '" и "'"
    
    return os.path.exists(cleaned_path)

def process_ffmpeg_list(input_file, output_file, dangerous_ids_file, tiktok_manual_chunks_dir, yt_manual_chunks_dir):
    dangerous_ids = load_dangerous_ids(dangerous_ids_file)
    
    # Загружаем manual чанки из TikTok и YouTube
    tiktok_manual_pool = load_manual_chunks(tiktok_manual_chunks_dir)
    yt_manual_pool = load_manual_chunks(yt_manual_chunks_dir)
    
    # Создаем общий пул ручных чанков
    all_manual_chunks = tiktok_manual_pool + yt_manual_pool
    random.shuffle(all_manual_chunks)
    
    if not all_manual_chunks:
        print("ВНИМАНИЕ: Не найдены ручные чанки из TikTok или YouTube!")
    
    # Резерв для safe замены
    safe_replacement_pool = []
    
    # Будем сохранять пары вместе с исходным индексом и типом
    entries = []       # (index, number_line, content_line, number, type, is_top_1000, file_exists_flag)
    special_entries = []  # Спец. строки (intro/outro и т.п.)

    # Читаем файл построчно
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    idx = 0
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Если строка спецовая (например, intro/outro), сохраняем её отдельно с индексом
        if 'intro/intro.ts' in line or 'outro/outro.ts' in line:
            special_entries.append((idx, line, "special"))
            idx += 1
            i += 1
            continue

        # Если это строка с номером видео
        if 'number_videos_ts/number_' in line:
            number = extract_number(line)
            if i+1 < len(lines):
                next_line = lines[i+1].strip()
                if 'number_videos_ts/number_' not in next_line:
                    # Проверяем существование файла
                    file_exists_flag = file_exists(next_line)
                    
                    # Определяем тип контента
                    if 'videos_processed_ts/easters/' in next_line:
                        entry_type = "safe" if file_exists_flag else "dangerous"
                    else:
                        if number is not None and is_in_safe_range(number):
                            if number in dangerous_ids or not file_exists_flag:
                                entry_type = "dangerous"
                            else:
                                entry_type = "safe"
                        else:
                            entry_type = "unchecked"
                    
                    # Проверяем, находится ли видео в первой 1000
                    is_top_1000 = is_in_top_range(number) if number is not None else False
                    
                    entries.append((idx, line, next_line, number, entry_type, is_top_1000, file_exists_flag))
                    
                    # Если safe – добавим в резервный пул для safe замены
                    if entry_type == "safe":
                        safe_replacement_pool.append((line, next_line, number, is_top_1000))
                    
                    idx += 1
                    i += 2
                    continue
        
        # Если не удалось распознать пару, сохраняем как спец.
        special_entries.append((idx, line, "unknown"))
        idx += 1
        i += 1

    # Перемешиваем пул безопасных замен
    random.shuffle(safe_replacement_pool)
    
    # Разделим ручные чанки на пулы для топ-1000 и для остальных
    manual_top_pool = all_manual_chunks.copy() if all_manual_chunks else []
    manual_other_pool = all_manual_chunks.copy() if all_manual_chunks else []
    
    random.shuffle(manual_top_pool)
    random.shuffle(manual_other_pool)
    
    # Индексы для циклического прохода по пулам
    manual_top_idx = 0
    manual_other_idx = 0
    safe_idx = 0
    
    # Обрабатываем записи - заменяем опасные/отсутствующие
    processed_entries = []
    unsafe_entries = []
    
    for entry in entries:
        orig_index, number_line, content_line, number, etype, is_top_1000, file_exists_flag = entry
        
        if etype in ("dangerous", "unchecked") or not file_exists_flag:
            # Нужно заменить этот файл
            replacement = None
            
            if is_top_1000:
                # Для топ-1000 используем только ручные чанки
                if manual_top_pool:
                    chunk_path = manual_top_pool[manual_top_idx % len(manual_top_pool)]
                    manual_top_idx += 1
                    replacement = f"file '{chunk_path}'"
            else:
                # Для остальных - сначала ручные чанки, потом safe
                if manual_other_pool:
                    chunk_path = manual_other_pool[manual_other_idx % len(manual_other_pool)]
                    manual_other_idx += 1
                    replacement = f"file '{chunk_path}'"
                elif safe_replacement_pool:
                    safe_replacement = safe_replacement_pool[safe_idx % len(safe_replacement_pool)]
                    safe_idx += 1
                    replacement = safe_replacement[1]  # content_line из пары
            
            # Если не нашли замену, используем оригинал (это маловероятно)
            new_content = replacement if replacement else content_line
            
            processed_entries.append((orig_index, number_line, new_content, number, etype, is_top_1000))
            unsafe_entries.append((orig_index, number_line, new_content, number, etype, is_top_1000))
        else:
            # Для safe – оставляем без изменений
            processed_entries.append((orig_index, number_line, content_line, number, etype, is_top_1000))

    # Перемешиваем unsafe записи и создаем финальный список
    random.shuffle(unsafe_entries)
    
    final_entries = []
    unsafe_counter = 0
    
    for entry in processed_entries:
        orig_index, number_line, content_line, number, etype, is_top_1000 = entry
        if etype in ("dangerous", "unchecked"):
            final_entries.append((orig_index, number_line, unsafe_entries[unsafe_counter][2], number, etype, is_top_1000))
            unsafe_counter += 1
        else:
            final_entries.append(entry)
    
    # Сортируем и объединяем с специальными записями
    final_entries.sort(key=lambda x: x[0])
    combined = final_entries + special_entries
    combined.sort(key=lambda x: x[0])
    
    # Записываем итог в выходной файл
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in combined:
            if len(entry) == 3:
                # спец. строка: (index, line, type)
                f.write(f"{entry[1]}\n")
            else:
                # пара: (index, number_line, content_line, number, etype, is_top_1000)
                f.write(f"{entry[1]}\n")
                f.write(f"{entry[2]}\n")

if __name__ == '__main__':
    input_file = 'work/list.txt'
    output_file = 'work/list_safe_3.txt'
    dangerous_ids_file = 'blacklist/all.txt'
    tiktok_manual_chunks_dir = 'F:/Python/TikTokTest/videos_processed_ts/tiktok_manual_brainrot'
    yt_manual_chunks_dir = 'F:/Python/TikTokTest/videos_processed_ts/yt_manual_brainrot'
    
    process_ffmpeg_list(input_file, output_file, dangerous_ids_file, tiktok_manual_chunks_dir, yt_manual_chunks_dir)
    print(f"Обработка завершена. Результат сохранен в {output_file}")
