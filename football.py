import asyncio
import re
from datetime import datetime, timedelta
from utils import GatheringTaskGroup

from playwright.async_api import (
    Locator,
    async_playwright,
    Page,
    Browser,
)


class Football:
    def __init__(self, base_url: str, game_name: str = "Football") -> None:
        self.base_url = base_url
        self.game_name = game_name
        self.success_tasks = 0
        self.total_tasks = 0

    async def run(self):
        urls = await self.get_url_dates()
        async with async_playwright() as pw:
            chromium = pw.chromium
            browser = await chromium.launch(timeout=60000, headless=False)
            async with GatheringTaskGroup() as tg:
                for url in urls:
                    page = await browser.new_page(
                        viewport={"width": 1000, "height": 1000}
                    )
                    tg.create_task(self._tournament_runner(page, url, browser))
        res = tg.results()
        print("\n\n=====DONE=====\n\n")
        print(res)
        return res

    async def get_url_dates(self):
        urls = []
        for i in range(0, 3):
            date_from = datetime.now() + timedelta(days=i)
            date_from = date_from.strftime("%Y/%m/%d")
            # TODO: pep8 to this string
            url = (
                self.base_url
                + f"/en/schedule?dateFrom={date_from}+00%3A00&dateTo={date_from}+23%3A59&page=1"
            )
            urls.append(url)
        urls = [url]
        return urls

    async def _tournament_runner(self, page: Page, url: str, browser: Browser):
        await page.route(
            re.compile(r"\.(jpg|png|svg)$"), lambda route: route.abort()
        )
        await page.goto(url, wait_until="domcontentloaded")
        # Wait while page is loading
        data = await self.wait_until_element_appears(
            page, ".tournaments-schedule-row", sleep_time_sec=2
        )
        if not data:
            print(f"Cant load resource on {url}")
            return []
        # Unpack row count and locator
        cnt, table = data
        # Gather match urls
        links = [
            self.base_url
            + (await table.nth(tour).get_by_role("link").get_attribute("href"))
            for tour in range(cnt)
        ]
        print(links)
        data = []

        async with GatheringTaskGroup() as tg:
            for idx, link in enumerate(links):
                print(f"start match {idx}")
                tour_name = (
                    await table.locator(".tournament-title-label")
                    .nth(idx)
                    .inner_text()
                )
                tour_date = (
                    await table.locator(".location-title-date")
                    .nth(idx)
                    .inner_text()
                )
                match_page = await browser.new_page()
                tg.create_task(
                    self.__get_data_from_match(
                        match_page, link, tour_name, tour_date, idx
                    )
                )
        res = tg.results()
        print(res)

        # base_locator = page.locator(".tournaments-table")
        return res

    async def __get_data_from_match(
        self, page: Page, url, tour_name: str, tour_date: str, number: int = 0
    ):
        await page.route(
            re.compile(r"\.(jpg|png|svg)$"), lambda route: route.abort()
        )
        await page.route(
            re.compile(r"\.facebook"), lambda route: route.abort()
        )
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        data = await self.wait_until_element_appears(
            page, ".tournament-matches-row", sleep_time_sec=2
        )
        if not data:
            print(f"Cant load resource on {url}")
            return []
        print(f"start data extraction... {number}")
        cnt, locator = data
        result = []
        for match_number in range(cnt):
            row = locator.nth(match_number)
            date_ = await row.locator(
                ".tournament-matches-date"
            ).all_inner_texts()
            team1, team2 = await row.locator(
                ".text-link.caption-2"
            ).all_inner_texts()
            result.append(
                {
                    "game": self.game_name,
                    "tour": tour_name,
                    "date": date_,
                    "team_1": team1,
                    "team_2": team2,
                }
            )
        print(result)
        return result

    async def get_match(self, page: Page, url):
        pass

    async def wait_until_element_appears(
        self,
        page: Page,
        name: str,
        attempts_count: int = 10,
        sleep_time_sec: float = 1.5,
    ) -> tuple[int, Locator] | None:
        while attempts_count > 0:
            await asyncio.sleep(sleep_time_sec)
            if cnt := (await page.locator(name).count()):
                return (cnt, page.locator(name))
            attempts_count -= 1
        print(f"Element {name} not found.")

    async def load_to_db(self):
        pass


f = Football("https://football.esportsbattle.com")
asyncio.run(f.run())
