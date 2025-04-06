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

def is_in_top_range(number):
    """
    Проверяет, находится ли число в диапазоне первой 1000 с конца (100000-99000).
    """
    return 100000 >= number >= 99000

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

def extract_file_path(line):
    """
    Извлекает путь к файлу из строки вида "file 'path/to/file'".
    """
    if line.startswith("file '") and line.endswith("'"):
        return line[6:-1]  # Извлекаем путь между file ' и '
    return None

def validate_ffmpeg_list(input_file, output_file, tiktok_manual_chunks_dir, yt_manual_chunks_dir):
    """
    Валидирует список файлов FFmpeg, заменяя отсутствующие файлы.
    """
    # Загружаем ручные чанки
    tiktok_manual_pool = load_manual_chunks(tiktok_manual_chunks_dir)
    yt_manual_pool = load_manual_chunks(yt_manual_chunks_dir)
    
    # Объединяем в общий пул
    all_manual_chunks = tiktok_manual_pool + yt_manual_pool
    random.shuffle(all_manual_chunks)
    
    if not all_manual_chunks:
        print("ВНИМАНИЕ: Не найдены ручные чанки из TikTok или YouTube!")
    
    # Создаем пулы для топ-1000 и для остальных
    manual_top_pool = all_manual_chunks.copy() if all_manual_chunks else []
    manual_other_pool = all_manual_chunks.copy() if all_manual_chunks else []
    
    random.shuffle(manual_top_pool)
    random.shuffle(manual_other_pool)
    
    # Индексы для циклического прохода по пулам
    manual_top_idx = 0
    manual_other_idx = 0
    
    # Читаем исходный файл
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Преобразуем в список строк без переносов
    lines = [line.strip() for line in lines]
    
    # Создаем набор безопасных видео (которые существуют)
    safe_pairs = []  # Будем хранить пары (number_line, content_line)
    
    # Первый проход - находим безопасные пары
    i = 0
    while i < len(lines) - 1:  # -1 потому что ищем пары строк
        line = lines[i]
        next_line = lines[i+1]
        
        # Если это строка с номером видео
        if 'number_videos_ts/number_' in line:
            number = extract_number(line)
            
            # Если следующая строка не является номером
            if 'number_videos_ts/number_' not in next_line:
                content_path = extract_file_path(next_line)
                
                # Проверяем существование файла и не входит ли он в топ-1000
                if content_path and os.path.exists(content_path):
                    is_top_1000 = is_in_top_range(number) if number is not None else False
                    if not is_top_1000:
                        safe_pairs.append((line, next_line))
            
                i += 2  # Пропускаем пару строк
                continue
        
        i += 1  # Переходим к следующей строке
    
    # Перемешиваем пул безопасных замен
    random.shuffle(safe_pairs)
    safe_idx = 0
    
    # Второй проход - заменяем отсутствующие файлы
    output_lines = []
    replaced_count = 0
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Если это строка с номером видео
        if 'number_videos_ts/number_' in line and i+1 < len(lines):
            number_line = line
            number = extract_number(line)
            
            # Если следующая строка не является номером
            if 'number_videos_ts/number_' not in lines[i+1]:
                content_line = lines[i+1]
                content_path = extract_file_path(content_line)
                
                # Проверяем существование файла
                exists = content_path and os.path.exists(content_path)
                
                if not exists:
                    # Файл не существует, нужно заменить
                    replaced_count += 1
                    
                    # Проверяем, находится ли видео в первой 1000
                    is_top_1000 = is_in_top_range(number) if number is not None else False
                    
                    if is_top_1000:
                        # Для топ-1000 - только ручные чанки
                        if manual_top_pool:
                            chunk_path = manual_top_pool[manual_top_idx % len(manual_top_pool)]
                            manual_top_idx += 1
                            output_lines.append(number_line)
                            output_lines.append(f"file '{chunk_path}'")
                        else:
                            # Если нет ручных чанков, выводим предупреждение и оставляем как есть
                            print(f"ВНИМАНИЕ: Не найдено замены для топ-1000 видео {content_path}")
                            output_lines.append(number_line)
                            output_lines.append(content_line)
                    else:
                        # Для остальных - сначала ручные чанки, потом safe
                        if manual_other_pool:
                            chunk_path = manual_other_pool[manual_other_idx % len(manual_other_pool)]
                            manual_other_idx += 1
                            output_lines.append(number_line)
                            output_lines.append(f"file '{chunk_path}'")
                        elif safe_pairs:
                            # Берем безопасную пару из пула
                            safe_pair = safe_pairs[safe_idx % len(safe_pairs)]
                            safe_idx += 1
                            output_lines.append(safe_pair[0])  # number_line
                            output_lines.append(safe_pair[1])  # content_line
                        else:
                            # Если нет замен, выводим предупреждение и оставляем как есть
                            print(f"ВНИМАНИЕ: Не найдено замены для {content_path}")
                            output_lines.append(number_line)
                            output_lines.append(content_line)
                else:
                    # Файл существует, оставляем как есть
                    output_lines.append(number_line)
                    output_lines.append(content_line)
                
                i += 2  # Пропускаем пару строк
                continue
        
        # Если это не пара с номером и контентом, просто добавляем строку как есть
        output_lines.append(line)
        i += 1
    
    # Записываем результат в выходной файл
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in output_lines:
            f.write(f"{line}\n")
    
    return replaced_count

if __name__ == '__main__':
    input_file = 'work/list_safe_5_valid_FINAL.txt'
    output_file = 'work/list_safe_4_valid.txt'
    tiktok_manual_chunks_dir = 'F:/Python/TikTokTest/videos_processed_ts/tiktok_manual_brainrot'
    yt_manual_chunks_dir = 'F:/Python/TikTokTest/videos_processed_ts/yt_manual_brainrot'
    
    replaced_count = validate_ffmpeg_list(input_file, output_file, tiktok_manual_chunks_dir, yt_manual_chunks_dir)
    print(f"Валидация завершена. Заменено отсутствующих файлов: {replaced_count}")
    print(f"Результат сохранен в {output_file}")
