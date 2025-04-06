from TikTokApi import TikTokApi
import asyncio
import os

MIN_VIEWS = 20000
BROWSER = r"C:\Program Files\BraveSoftware\Brave-Browser-Nightly\Application\brave.exe"

ms_token = "zNjoEDxXTbWnaVpjEnRci8G1Gc549sWlIfzc2xSTuJgJ0rCVRCWbtSQw--h63l4xPCoMDLU98ojUZ7_PScTPxQtSSiW2pXL9LXKOXc-QmMT14cnEL5S8M7NY2tApLQkB18sME8yFcQPCnPynprf-kwmeFQ=="

async def get_hashtag_videos(hashtag, cycles=5):
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        videos = []

        tag = api.hashtag(name=hashtag)
        for i in range(cycles):
            async for video in tag.videos(count=30, cursor=i*30):
                if int(video.as_dict["statsV2"]["playCount"]) < MIN_VIEWS:
                    continue
                    
                video_description = str(video.as_dict["desc"])
                # if not hashtag in video_description:
                #     continue

                print(video.as_dict["id"], video.as_dict["statsV2"], video.as_dict["desc"])

                videos.append({
                    "id": video.as_dict["id"],
                    "stats": video.as_dict["statsV2"],
                    "author": video.as_dict["author"]["uniqueId"],
                    "description": video.as_dict["desc"]
                })

        return videos

hashtags = [
    "brainrot"
]

async def main():
    for hashtag in hashtags:
        result = await get_hashtag_videos(hashtag, cycles=100)
        print(f"Получено {len(result)} видео для хэштега '{hashtag}'")
        
        file_name = f"{hashtag}.txt"
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