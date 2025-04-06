from TikTokApi import TikTokApi
import asyncio
import os

MIN_VIEWS = 20000
BROWSER = r"C:\Program Files\BraveSoftware\Brave-Browser-Nightly\Application\brave.exe"

ms_token = "anyway it's expired"

async def get_videos_with_sound(sound_id, cycles=5):
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=4, headless=True, executable_path=BROWSER)
        videos = []

        for i in range(cycles):
            print("Cycle", i+1, "/", cycles)

            async for video in api.sound(id=sound_id).videos(count=100, cursor=i * 100):
                if int(video.as_dict["statsV2"]["playCount"]) < MIN_VIEWS:
                    continue

                print(video.as_dict["id"], video.as_dict["statsV2"])

                videos.append({
                    "id": video.as_dict["id"],
                    "stats": video.as_dict["statsV2"],
                    "author": video.as_dict["author"]["uniqueId"],
                    "description": video.as_dict["desc"]
                })

        return videos

brainrot_sounds = {
    #"still water": "7377251193027889963",
    #"jonkler": "7408557148835236640",
    #"jonkler 2": "7408007093985282822",
    #"jonkler 3": "7341316089869716226",
    #"linganguli": "7413706644167149569",
    #"i just lost my dawg": "7410551613917547296"
    #"bye bye": "7320197342395763499"
    #"hood irony": "7211580519686572806",
    #"hood irony 2": "7202676516210838277",
    #"linganguli 2": "7421706307868150570",
    #"linganguli 3": "7421616616150666016",
    #"linganguli 4": "7429315114211281696",
    # "linganguli 5": "",
    #"what the hell": "7331732109727369986",
    #"baby laugh": "7120594206220879874",
    "don pollo": "7231236179499305755",
    "only in ohio": "7287316920859985922",
    "pavapepe": "7182154147709307654",
    "don pollo 2": "7195235241886616325",
    "swag like ohio": "7188654752585894662"
}

async def main():
    for sound_name, sound_id in brainrot_sounds.items():
        result = await get_videos_with_sound(sound_id, cycles=30)
        print(f"Получено {len(result)} видео для звука '{sound_name}'")
        
        file_name = f"{sound_name}.txt"
        unique_links = set()

        # Чтение существующих ссылок из файла
        if os.path.exists(file_name):
            with open(file_name, "r", encoding="utf-8") as f:
                unique_links = set(f.read().splitlines())

        # Добавление новых уникальных ссылок
        new_links_count = 0
        for video in result:
            link = f"https://www.tiktok.com/@{video['author']}/video/{video['id']}"
            if link not in unique_links:
                unique_links.add(link)
                new_links_count += 1
                print(f"Просмотры: {video['stats']['playCount']} {link}")

        # Запись всех уникальных ссылок обратно в файл
        with open(file_name, "w", encoding="utf-8") as f:
            for link in sorted(unique_links):
                f.write(f"{link}\n")

        print(f"Добавлено {new_links_count} новых уникальных ссылок в файл '{file_name}'")
        print(f"Всего уникальных ссылок в файле: {len(unique_links)}")

# Запуск асинхронной функции
asyncio.run(main())
