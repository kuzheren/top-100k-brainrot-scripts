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

def process_ffmpeg_list(input_file, output_file, dangerous_ids_file, tiktok_manual_chunks_dir, yt_manual_chunks_dir):
    dangerous_ids = load_dangerous_ids(dangerous_ids_file)
    # Загружаем manual чанки: сначала тиктока (приоритет), потом YouTube (менее приоритетные)
    tiktok_manual_pool = load_manual_chunks(tiktok_manual_chunks_dir)
    yt_manual_pool = load_manual_chunks(yt_manual_chunks_dir)
    tiktok_manual_index = 0
    yt_manual_index = 0

    def get_next_manual_chunk():
        nonlocal tiktok_manual_index, yt_manual_index
        if tiktok_manual_index < len(tiktok_manual_pool):
            chunk = tiktok_manual_pool[tiktok_manual_index]
            tiktok_manual_index += 1
            return f"file '{chunk}'"
        elif yt_manual_index < len(yt_manual_pool):
            chunk = yt_manual_pool[yt_manual_index]
            yt_manual_index += 1
            return f"file '{chunk}'"
        else:
            return None

    # Резерв для safe замены
    safe_replacement_pool = []  # будем заполнять после разделения, затем перемешаем
    # Будем сохранять пары вместе с исходным индексом и типом
    entries = []       # Каждый элемент: (index, number_line, content_line, number, type)
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
            special_entries.append( (idx, line, "special") )
            idx += 1
            i += 1
            continue

        # Если это строка с номером видео (number_videos_ts)
        if 'number_videos_ts/number_' in line:
            number = extract_number(line)
            if i+1 < len(lines):
                next_line = lines[i+1].strip()
                if 'number_videos_ts/number_' not in next_line:
                    # Определяем тип:
                    # Если контент относится к easters – оставляем safe
                    if 'videos_processed_ts/easters/' in next_line:
                        entry_type = "safe"
                    else:
                        if number is not None and is_in_safe_range(number):
                            # Если номер в safe диапазоне, проверяем blacklist
                            if number in dangerous_ids:
                                entry_type = "dangerous"
                            else:
                                entry_type = "safe"
                        else:
                            entry_type = "unchecked"
                    entries.append( (idx, line, next_line, number, entry_type) )
                    # Если safe – добавим в резервный пул для safe замены
                    if entry_type == "safe":
                        safe_replacement_pool.append( (line, next_line, number) )
                    idx += 1
                    i += 2
                    continue
        # Если не удалось распознать пару, сохраняем строку как спец.
        special_entries.append( (idx, line, "unknown") )
        idx += 1
        i += 1

    # Для безопасных замещающих видео сделаем копию и перемешаем
    safe_replacement_pool_copy = safe_replacement_pool.copy()
    random.shuffle(safe_replacement_pool_copy)
    safe_rep_index = 0
    def get_next_safe_content():
        nonlocal safe_rep_index
        if safe_replacement_pool_copy:
            content = safe_replacement_pool_copy[safe_rep_index]
            safe_rep_index = (safe_rep_index + 1) % len(safe_replacement_pool_copy)
            return content[1]  # возвращаем content_line из safe пары
        return None

    # Пройдем по всем записям и для unsafe (dangerous и unchecked) произведем замену
    # Сохраним новый контент в отдельном поле, которое будем использовать для финального вывода.
    processed_entries = []
    unsafe_entries = []  # будем собирать unsafe записи для перемешивания
    for entry in entries:
        orig_index, number_line, content_line, number, etype = entry
        if etype in ("dangerous", "unchecked"):
            # Замена: сначала manual чанк, если его нет – safe замена
            replacement = get_next_manual_chunk()
            if not replacement:
                replacement = get_next_safe_content()
            new_content = replacement
            processed_entries.append( (orig_index, number_line, new_content, number, etype) )
            unsafe_entries.append( (orig_index, number_line, new_content, number, etype) )
        else:
            # Для safe – оставляем без изменений
            processed_entries.append( (orig_index, number_line, content_line, number, etype) )

    # Определяем индексы unsafe записей
    unsafe_indices = [e[0] for e in processed_entries if e[4] in ("dangerous", "unchecked")]
    # Из unsafe записей создадим список и перемешаем его
    unsafe_list = [e for e in processed_entries if e[4] in ("dangerous", "unchecked")]
    random.shuffle(unsafe_list)

    # Создаем финальный список, в котором safe (и спец.) остаются на своих позициях,
    # а unsafe из processed_entries заменяем элементами из перемешанного unsafe_list,
    # при этом порядок среди safe и спец. сохраняется.
    final_entries = []
    unsafe_counter = 0
    for entry in processed_entries:
        orig_index, number_line, content_line, number, etype = entry
        if etype in ("dangerous", "unchecked"):
            # Берем следующий элемент из перемешанного списка
            final_entries.append( (orig_index, number_line, unsafe_list[unsafe_counter][2], number, etype) )
            unsafe_counter += 1
        else:
            final_entries.append(entry)
    # Сортируем финальный список по исходному индексу
    final_entries.sort(key=lambda x: x[0])
    
    # Объединяем спец. записи со списком пар.
    # Здесь предположим, что спец. записи были сохранены отдельно и будут вставлены как есть (их порядок не меняется).
    # Если спец. строки из оригинального файла должны сохраняться в местах, где они были, то можно объединить по индексу.
    # Для простоты: сначала выведем все спец. записи, потом все пары.
    # Если требуется сохранить точное позиционирование, можно объединить списки и отсортировать по общему индексу.
    combined = final_entries + special_entries
    combined.sort(key=lambda x: x[0])
    
    # Записываем итог в выходной файл.
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in combined:
            # Определяем тип записи
            if len(entry) == 3:
                # спец. строка: (index, line, type)
                f.write(f"{entry[1]}\n")
            else:
                # пара: (index, number_line, content_line, number, etype)
                f.write(f"{entry[1]}\n")
                f.write(f"{entry[2]}\n")

if __name__ == '__main__':
    input_file = 'work/list.txt'
    output_file = 'work/list_safe_2.txt'
    dangerous_ids_file = 'blacklist/all.txt'
    tiktok_manual_chunks_dir = 'F:/Python/TikTokTest/videos_processed_ts/tiktok_manual_brainrot'
    yt_manual_chunks_dir = 'F:/Python/TikTokTest/videos_processed_ts/yt_manual_brainrot'
    
    process_ffmpeg_list(input_file, output_file, dangerous_ids_file, tiktok_manual_chunks_dir, yt_manual_chunks_dir)
    print(f"Обработка завершена. Результат сохранен в {output_file}")
