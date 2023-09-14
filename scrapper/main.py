import asyncio
import re
from datetime import datetime, timedelta
import pytz

from playwright.async_api import async_playwright, Page

# Actual max sleep time is
# (MAX_TIMEOUT_ON_SCHEDULE_LOADING_SEC * SCHEDULE_LOAD_SPEEP_TIME_SEC) sec

MAX_TIMEOUT_ON_SCHEDULE_LOADING_SEC = 15
SCHEDULE_LOAD_SPEEP_TIME_SEC = 2
MAX_TIMEOUT_ON_MATCH_LOADING_SEC = 10
MATCH_LOAD_SLEEP_TIME_SEC = 1


class GatheringTaskGroup(asyncio.TaskGroup):
    def __init__(self):
        super().__init__()
        self.__tasks = []

    def create_task(self, coro, *, name=None, context=None):
        task = super().create_task(coro, name=name, context=context)
        self.__tasks.append(task)
        return task

    def results(self):
        return [task.result() for task in self.__tasks]


async def page_run_csgo(page: Page, url: str) -> list[dict[str, str]]:
    await page.route(
        re.compile(r"\.(jpg|png|svg)$"), lambda route: route.abort()
    )
    await page.goto(url)

    game_name = "CS:GO"
    load_schedule_attempts = 0
    data = []
    tour_name = page.locator(".tournaments-cell-game-type")

    while load_schedule_attempts < MAX_TIMEOUT_ON_SCHEDULE_LOADING_SEC:
        print("Loading schedule...")
        await asyncio.sleep(SCHEDULE_LOAD_SPEEP_TIME_SEC)
        # Trying to load schedule
        tournaments_cnt = await page.locator(
            ".tournaments-schedule-row"
        ).count()
        if tournaments_cnt:
            break
        load_schedule_attempts += 1
    else:
        print(f"Cant load schedule on url: {url}")
        return None

    for tour_idx in range(tournaments_cnt):
        # Check if tour is planned

        await page.locator(".tournaments-schedule-row").nth(tour_idx).click()
        # load_matches_attemtps - secs to load a matches
        load_matches_attemtps = 0
        while load_matches_attemtps < MAX_TIMEOUT_ON_MATCH_LOADING_SEC:
            print("Match details are loading...")
            await asyncio.sleep(MATCH_LOAD_SLEEP_TIME_SEC)
            if await page.locator(".participant-photo-logo-team").count():
                print("Teams were founded")
                break
            load_matches_attemtps += 1
        else:
            print("Cant load tour matches")
            continue

        match_date_start = page.locator(".tournament-matches-date")
        matches_count = await page.locator(".tournament-matches-row").count()

        for match_idx in range(matches_count):
            # Check if match is planned
            # if (
            #     await page.locator(".tournament-matches-cell-entitystatus")
            #     .nth(tour_idx)
            #     .inner_text()
            # ) != "Planned":
            #     print("Skipping not planned match")
            #     continue
            teams = await (
                page.locator(".tournament-matches-row")
                .nth(match_idx)
                .locator(".participant-photo-logo-team")
                .all_inner_texts()
            )

            data.append(
                {
                    "game": game_name,
                    "tour": (await tour_name.nth(tour_idx).all_inner_texts())[
                        0
                    ],
                    "date": (
                        await match_date_start.nth(match_idx).all_inner_texts()
                    )[0],
                    "team_1": teams[0],
                    "team_2": teams[1],
                }
            )
        await page.locator(".tournament-matches-close-icon").nth(0).click()

    return data


async def get_url_dates():
    base_url = "https://csgo.esportsbattle.com/en/schedule"
    urls = []
    # timedelta_ = timedelta(days=)
    for i in range(0, 3):
        date_from = datetime.now() + timedelta(days=i)
        date_from = date_from.strftime("%Y/%m/%d")
        # TODO: pep8 on this string
        url = (
            base_url
            + f"?dateFrom={date_from}+00%3A00&dateTo={date_from}+23%3A59&page=1"
        )
        urls.append(url)

    return urls


async def page_main():
    urls = await get_url_dates()
    async with async_playwright() as pw:
        chromium = pw.firefox
        browser = await chromium.launch(timeout=60000)
        async with GatheringTaskGroup() as tg:
            for url in urls:
                page = await browser.new_page()
                tg.create_task(page_run_csgo(page, url))
        print(tg.results())


asyncio.run(page_main())
