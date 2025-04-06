import os
import re
import unicodedata
from pathlib import Path

def is_valid_for_ffmpeg(char):
    # Базовые латинские буквы, цифры и безопасные символы
    return char.isascii() and (char.isalnum() or char in '-._() ')

def sanitize_filename(filename):
    # Получаем имя и расширение отдельно
    name, ext = os.path.splitext(filename)
    
    # Транслитерация русских букв
    trans = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    
    # Преобразуем в NFKD форму и удаляем комбинирующие символы
    name = unicodedata.normalize('NFKD', name)
    
    # Конвертируем строку
    result = ''
    for char in name.lower():
        if is_valid_for_ffmpeg(char):
            result += char
        elif char.lower() in trans:
            result += trans[char.lower()]
        else:
            # Для других символов используем их hex-представление
            result += f'_{ord(char):x}'
    
    # Убираем множественные подчеркивания и пробелы
    result = re.sub(r'[\s_]+', '_', result)
    # Убираем начальные и конечные подчеркивания
    result = result.strip('_')
    
    return result + ext

def rename_files_in_directory(directory):
    # Получаем список всех файлов в директории
    path = Path(directory)
    files = list(path.rglob('*'))
    
    # Словарь для отслеживания использованных имен
    used_names = {}
    
    for file_path in files:
        if file_path.is_file():
            original_name = file_path.name
            new_name = sanitize_filename(original_name)
            
            # Если имя уже существует, добавляем числовой суффикс
            base_new_name = new_name
            counter = 1
            while new_name in used_names:
                name, ext = os.path.splitext(base_new_name)
                new_name = f"{name}_{counter}{ext}"
                counter += 1
            
            if original_name != new_name:
                new_path = file_path.parent / new_name
                try:
                    file_path.rename(new_path)
                    print(f"Переименован: {original_name} -> {new_name}")
                except Exception as e:
                    print(f"Ошибка при переименовании {original_name}: {e}")
            
            used_names[new_name] = True

# Использование
directory_path = "videos_processed_ts/tiktok_manual_brainrot"  # Укажите путь к вашей папке
rename_files_in_directory(directory_path)