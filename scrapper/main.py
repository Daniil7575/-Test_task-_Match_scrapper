import time
import asyncio

from scrappers.csgo import CSGO
from scrappers.football import Football
import settings


async def main():
    scrappers = [
        Football("https://football.esportsbattle.com"),
        CSGO("https://csgo.esportsbattle.com"),
    ]

    while True:
        for scrapper in scrappers:
            try:
                await scrapper.run()
            except Exception as e:
                print(f"{scrapper} has failed")
                print(e)
        time.sleep(settings.SLEEP_TIME)


if __name__ == "__main__":
    asyncio.run(main())
