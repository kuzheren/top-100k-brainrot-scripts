import json
import subprocess
import os
import re
import ytdlp

def extract_tiktok_id(url):
    pattern = r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/(\d+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def video_exists(prefix, video_id):
    video_path = f'videos/{prefix}/{prefix}_{video_id}.mp4'  # Предполагаем расширение .mp4
    return os.path.exists(video_path)

def download_video(video_url, prefix):
    if video_exists(prefix, extract_tiktok_id(video_url)):
        print(f"Видео {video_url} уже существует. Пропускаем скачивание.")
        return True

    variants = get_available_tracks(video_url)
    if variants == None:
        print("Не удалось получить варианты видеофайла.")
        return

    if len(variants["formats"]) <= 1:
        print("Не удалось получить файл видео. Видимо, по ссылке слайд-шоу")
        return

    variant = variants["formats"][1]["id"]

    code, result = ytdlp.invoke(
        [
            "-f", variant,
            '-o', f"videos/{prefix}/{prefix}_{variants['id']}.%(ext)s",
            video_url
        ], log=False
    )

    if code == 0:
        # print("Видео скачано!")
        return True
    else:
        print(f"Ошибка при скачивании видео. Код возврата: {code}")
        return False

def get_available_tracks(video_url):
    # print("Пытаюсь получить список источников видео.")

    code, result = ytdlp.invoke(
        [
            "-F", video_url
        ], log=False
    )

    if code != 0:
        return print(f"Ошибка при получении списка источников: {code}")

    return parse_yt_dlp_output(result)

def parse_yt_dlp_output(output):
    lines = output.strip().split('\n')
    video_info = {}
    formats = []

    # Извлекаем URL и ID видео
    url_match = re.search(r'Extracting URL: (https://.*)', output)
    if url_match:
        video_info['url'] = url_match.group(1)
    
    id_match = re.search(r'Available formats for (\d+):', output)
    if id_match:
        video_info['id'] = id_match.group(1)

    # Парсим информацию о форматах
    for line in lines[5:]:  # Пропускаем заголовки
        if line.startswith('--'):
            continue
        parts = line.split()
        if len(parts) >= 8:
            format_info = {
                'id': parts[0],
                'ext': parts[1],
                'resolution': parts[2],
                'filesize': parts[4] if parts[4] != '|' else None,
                'tbr': parts[5] if parts[5] != '|' else None,
                'proto': parts[6],
                'vcodec': parts[7],
                'acodec': parts[8],
                'watermarked': 'watermarked' in parts
            }
            formats.append(format_info)

    video_info['formats'] = formats

    return video_info

download_video("https://www.tiktok.com/@yt_.editz/video/7408007076724608261", "jonkler")
