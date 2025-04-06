import os
import random
from tqdm import tqdm

def collect_video_files(folder_path):
    """Сбор всех видеофайлов из директории и поддиректорий"""
    video_files = []
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.ts')
    
    print("Поиск видеофайлов...")
    for root, _, files in tqdm(list(os.walk(folder_path))):
        for file in files:
            if file.lower().endswith(video_extensions):
                full_path = os.path.abspath(os.path.join(root, file))
                video_files.append(full_path)
    
    return video_files

def create_concat_list(video_files, number_videos, numbers_dir, intro_path, output_file, fixed_positions):
    """Создание файла списка для конкатенации с фиксированными позициями"""
    if len(video_files) < number_videos:
        print(f"Предупреждение: найдено только {len(video_files)} видео")
        number_videos = len(video_files)
    
    # Фильтруем fixed_positions, оставляя только валидные позиции
    valid_fixed_positions = {
        pos: path for pos, path in fixed_positions.items() 
        if pos <= number_videos and os.path.exists(path)
    }
    
    if len(fixed_positions) != len(valid_fixed_positions):
        print("\nНекоторые фиксированные позиции были пропущены:")
        for pos in fixed_positions:
            if pos not in valid_fixed_positions:
                if pos > number_videos:
                    print(f"Позиция {pos} больше, чем количество видео ({number_videos})")
                elif not os.path.exists(fixed_positions[pos]):
                    print(f"Файл не найден: {fixed_positions[pos]}")
    
    # Создаем список всех позиций
    all_positions = list(range(number_videos))
    
    # Удаляем фиксированные позиции из списка для рандомного выбора
    available_positions = [pos for pos in all_positions if number_videos - pos not in valid_fixed_positions]
    
    # Выбираем случайные видео для оставшихся позиций
    needed_random_videos = len(available_positions)
    random_videos = random.sample([v for v in video_files if v not in valid_fixed_positions.values()], needed_random_videos)
    
    # Создаем финальный список видео
    final_videos = []
    for position in range(number_videos):
        number = number_videos - position  # Обратный порядок номеров
        if number in valid_fixed_positions:
            final_videos.append(valid_fixed_positions[number])
        else:
            final_videos.append(random_videos.pop())
    
    print(f"\nСоздание файла списка {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"file '{intro_path}'\n")
        
        for i, video_path in enumerate(final_videos):
            video_path = video_path.replace("\\", "/")
            number = number_videos - i  # Обратный порядок номеров
            number_path = os.path.abspath(os.path.join(numbers_dir, f"number_{number}_audio.ts"))
            number_path = number_path.replace("\\", "/")
            f.write(f"file '{number_path}'\n")
            f.write(f"file '{video_path}'\n")
    
    return len(final_videos)

def main():
    # Параметры
    videos_dir = "videos_processed_ts"
    numbers_dir = r"F:\Python\TikTokTest\number_videos_ts"
    intro_path = "F:/Python/TikTokTest/videos_processed_ts/intro/intro.ts"
    output_file = "work/list.txt"
    number_videos = 100000  # Например, всего 100 видео
    
    # Словарь фиксированных позиций
    fixed_positions = {
        100000: r"F:\Python\TikTokTest\videos_processed_ts\compilations\1 hour brainrot\1_hour_of_brainrot_memes_v1_5b9q6el3isatm_5d_chunk_1.ts",
        99999: r"F:\Python\TikTokTest\videos_processed_ts\compilations\brainrot 2\10_minutes_of_brainrot_memes_v8_5behfpymqqyx4_5d_chunk_2.ts",
        99998: r"F:\Python\TikTokTest\videos_processed_ts\!linganguli\21linganguli_7413293813885717793_chunk_2.ts",
        99997: r"F:\Python\TikTokTest\videos_processed_ts\hood irony\hood_irony_7220668858837912837_chunk_3.ts",
        99996: r"F:\Python\TikTokTest\videos_processed_ts\jonkler 3\jonkler_3_7402023581858729248_chunk_2.ts",
        99995: r"F:\Python\TikTokTest\videos_processed_ts\compilations\mango\winter_arc_1f976_2b_mango_mango_1f96d_2b_still_water_1f4a7_3d_those_who_know_2620_fe0f_1f608_(tiktok_meme_compilation)_5bnbtsnnew34a_5d_chunk_36.ts",
        99994: r"F:\Python\TikTokTest\videos_processed_ts\compilations\mango\winter_arc_1f976_2b_mango_mango_1f96d_2b_still_water_1f4a7_3d_those_who_know_2620_fe0f_1f608_(tiktok_meme_compilation)_5bnbtsnnew34a_5d_chunk_67.ts",
        99993: r"F:\Python\TikTokTest\videos_processed_ts\still water\still_water_7420273584284732678_chunk_2.ts",
        99992: r"F:\Python\TikTokTest\videos_processed_ts\compilations1\arabfnuy\arabfunny_4_64a_648_645_636_62d_1f601_pig_1f632_1f922_1f922halal_revenge_1f600_1f600_amogus_coffin_dance_631_628_64a_1f923_1f923_5b1iepeec4mhy_5d_chunk_5.ts",
        99991: r"F:\Python\TikTokTest\videos_processed_ts\compilations1\brainrot comp\brainrot_compilation_239_5bzvgor9csij0_5d_chunk_8.ts",
        99990: r"F:\Python\TikTokTest\videos_processed_ts\compilations1\10m brainrot\10_minutes_of_brainrot_memes_5biobehzfexom_5d_chunk_6.ts",
        99989: r"F:\Python\TikTokTest\videos_processed_ts\compilations1\fire\the_fire_in_the_holes_revolving_5bizrtaioqqvo_5d_chunk_8.ts",
        99988: r"F:\Python\TikTokTest\videos_processed_ts\linganguli 2\linganguli_2_7422141336297557254_chunk_1.ts",
        99987: r"F:\Python\TikTokTest\videos_processed_ts\compilations3\top_5_mewing_5b4xz1j1cadlq_5d_chunk_11.ts",
        99986: r"F:\Python\TikTokTest\videos_processed_ts\compilations3\senator_delivers_27brainrot_27_speech_in_parliament_3a_22skibidi_21_22_7c_6_news_5btji0qwglttk_5d_chunk_44.ts",
        99985: r"F:\Python\TikTokTest\videos_processed_ts\i just lost my dawg\i_just_lost_my_dawg_7410752861698641185_chunk_3.ts",
        99985: r"F:\Python\TikTokTest\videos_processed_ts\fillers 2\1f976_trollface_coldest_moments_of_all_time_1f976_troll_face_phonk_tiktoks_1f976_edits_trollface_1f976_pt.36_5ba5lqwceoevk_5d_chunk_440.ts",
        99984: r"F:\Python\TikTokTest\videos_processed_ts\compilations\nugget\1_hour_of_gegagedigedagedago_5bbu4ddjo3ad8_5d_chunk_53.ts",
        99983: r"F:\Python\TikTokTest\videos_processed_ts\compilations\mango\winter_arc_1f976_2b_mango_mango_1f96d_2b_still_water_1f4a7_3d_those_who_know_2620_fe0f_1f608_(tiktok_meme_compilation)_5bnbtsnnew34a_5d_chunk_29.ts",
        99982: r"F:\Python\TikTokTest\videos_processed_ts\compilations1\brainrot comp\brainrot_compilation_239_5bzvgor9csij0_5d_chunk_201.ts",
        99981: r"F:\Python\TikTokTest\videos_processed_ts\compilations1\memes1\offensive_memes_that_if_ylyl_-_greatest_funniest_tiktok_brainrot_meme_compilation_5bur8kfcdzizo_5d_chunk_50.ts",
        99980: r"F:\Python\TikTokTest\videos_processed_ts\compilations1\troll 32432\trollface_aura_compilation_1f976_7c_phonk_tik_toks_2339_5bq3fcqm72kfu_5d_chunk_10.ts",
        99979: r"F:\Python\TikTokTest\videos_processed_ts\still water\still_water_7422353055070391594_chunk_2.ts",
        99978: r"F:\Python\TikTokTest\videos_processed_ts\compilations4\one_hour_of_dank_memes_5b8wkc1shbpgi_5d_chunk_358.ts",

        78787: r"F:\Python\TikTokTest\videos_processed_ts\fillers 3\2024-11-27_22-30-21_chunk_11.ts",
        78: r"F:\Python\TikTokTest\videos_processed_ts\fillers\2024-11-26_20-30-41_chunk_1.ts",
        7: r"F:\Python\TikTokTest\videos_processed_ts\hood irony\hood_irony_7222344707970534661_chunk_14.ts",
        6: r"F:\Python\TikTokTest\videos_processed_ts\!linganguli\21linganguli_7416896299934567687_chunk_1.ts",
        5: r"F:\Python\TikTokTest\videos_processed_ts\compilations\mango\winter_arc_1f976_2b_mango_mango_1f96d_2b_still_water_1f4a7_3d_those_who_know_2620_fe0f_1f608_(tiktok_meme_compilation)_5bnbtsnnew34a_5d_chunk_50.ts",
        4: r"F:\Python\TikTokTest\videos_processed_ts\jonkler\jonkler_7408007076724608261_chunk_1.ts",
        3: r"F:\Python\TikTokTest\videos_processed_ts\i just lost my dawg\i_just_lost_my_dawg_7410551609266015520_chunk_1.ts",
        2: r"F:\Python\TikTokTest\videos_processed_ts\linganguli 4\linganguli_4_7429315102416882977_chunk_3.ts",

        2019: r"F:\Python\TikTokTest\videos_processed_ts\easters\2019.ts",
        1987: r"F:\Python\TikTokTest\videos_processed_ts\easters\1987.ts",
        1984: r"F:\Python\TikTokTest\videos_processed_ts\easters\1984.ts",
        1488: r"F:\Python\TikTokTest\videos_processed_ts\easters\1488.ts",
        404: r"F:\Python\TikTokTest\videos_processed_ts\easters\404.ts",
        98: r"F:\Python\TikTokTest\videos_processed_ts\easters\98.ts",
        87: r"F:\Python\TikTokTest\videos_processed_ts\easters\87.ts",
        34: r"F:\Python\TikTokTest\videos_processed_ts\easters\34.ts",
        21: r"F:\Python\TikTokTest\videos_processed_ts\easters\21.ts",
        1: r"F:\Python\TikTokTest\videos_processed_ts\easters\1.ts",
    }
    
    print(f"Начало создания списка для {number_videos} видео")
    
    # Собираем все видео
    video_files = collect_video_files(videos_dir)
    print(f"\nНайдено видеофайлов: {len(video_files)}")
    
    if not video_files:
        print("Видеофайлы не найдены")
        return
    
    # Создаем список для конкатенации
    total_videos = create_concat_list(video_files, number_videos, numbers_dir, 
                                    intro_path, output_file, fixed_positions)
    print(f"\nСоздан файл списка для {total_videos} видео")
    print(f"Путь к файлу списка: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()