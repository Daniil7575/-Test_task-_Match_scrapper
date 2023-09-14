import asyncio
import aiohttp
import re
from datetime import datetime, timedelta

from playwright.async_api import Browser, Page, async_playwright

import settings
from utils import GatheringTaskGroup, Scrapper, block_aggressively


class CSGO(Scrapper):
    def __init__(self, base_url: str, game_name: str = "CS:GO") -> None:
        super().__init__(base_url, game_name)

    async def run(self):
        res = {self.game_name: []}
        urls = await self.get_url_dates()
        async with async_playwright() as pw:
            chromium = pw.chromium
            browser = await chromium.launch(timeout=60000)
            async with GatheringTaskGroup() as tg:
                for url in urls:
                    page = await browser.new_page(
                        viewport={"width": 1280, "height": 1000}
                    )
                    tg.create_task(self._tournament_runner(page, url, browser))
        tour_res = {}
        [tour_res.update(elem) for elem in tg.results()]
        res[self.game_name] = tour_res
        async with aiohttp.ClientSession() as session:
            url = settings.API_URL
            async with session.post(url, json={"data": res}) as resp:
                print(await resp.text())
        return res

    async def _tournament_runner(
        self, page: Page, url: str, browser: Browser, page_number: int = 1
    ) -> dict[str, list[dict[str, str]]]:
        await page.route("**/*", block_aggressively)
        if page_number == 1:
            await page.goto(url, wait_until="domcontentloaded")
        # Wait while page is loading
        cnt = await self.wait_until_element_appears(
            page, ".tournaments-schedule-row"
        )
        if not cnt:
            print(f"Cant load resource on {url}")
            return {}
        # Gather match urls
        links = [
            self.base_url
            + (
                await page.locator(".tournaments-schedule-row")
                .nth(tour)
                .get_by_role("link")
                .get_attribute("href")
            )
            for tour in range(cnt)
        ]

        async with GatheringTaskGroup() as tg:
            for idx, link in enumerate(links):
                if (
                    await page.locator(".tournament-title-label")
                    .nth(idx)
                    .inner_html()
                    == "Finished"
                ):
                    continue

                print(f"start match {idx}")
                tour_name = (
                    await page.locator(".tournaments-cell-game-type")
                    .nth(idx)
                    .inner_text()
                )
                tour_date = (
                    await page.locator(".tournaments-cell-date")
                    .nth(idx)
                    .inner_text()
                )
                match_page = await browser.new_page()
                tg.create_task(
                    self._get_data_from_match(
                        match_page, link, tour_name, tour_date, idx
                    )
                )
        res = tg.results()
        res_dict = {}
        [res_dict.update(elem) for elem in res]
        # Check if there any pagination
        if not (
            await page.locator(".tournaments-table-pagination")
            .locator(".align-mob-center")
            .count()
        ):
            return res_dict

        next_page_class = (
            await page.locator(".tournaments-table-pagination")
            .locator(".align-mob-center")
            .nth(1)
            .get_attribute("class")
        )
        # Check if can go to next page
        if "disable" in next_page_class:
            return res_dict

        await page.locator(".tournaments-table-pagination").locator(
            ".align-mob-center"
        ).nth(1).click()
        res_dict.update(
            await self._tournament_runner(page, url, browser, page_number=2)
        )
        return res_dict

    async def _get_data_from_match(
        self, page: Page, url, tour_name: str, tour_date: str, number: int = 0
    ) -> dict[str, list[dict[str, str]]]:
        await page.route(
            re.compile(r"\.(jpg|png|svg)$"), lambda route: route.abort()
        )
        await page.route(
            re.compile(r"\.facebook"), lambda route: route.abort()
        )
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        cnt = await self.wait_until_element_appears(
            page, ".tournament-matches-row"
        )

        if not cnt:
            print(f"Cant load resource on {url}")
            return []

        result = {tour_name: []}
        print(f"Start data extraction on {url}")

        for match_number in range(cnt):
            row = page.locator(".tournament-matches-row").nth(match_number)
            if (
                await row.locator(".tournament-title-label").inner_text()
            ) != "Planned":
                continue

            date_ = await row.locator(".tournament-matches-date").inner_text()
            team1, team2 = await row.locator(
                ".participant-photo-logo-team"
            ).all_inner_texts()
            result[tour_name].append(
                {
                    "date": date_,
                    "team_1": team1,
                    "team_2": team2,
                }
            )
        print(f"Data extraction finished for {url}")
        await page.close()
        return result

    async def wait_until_element_appears(
        self,
        page: Page,
        name: str,
        attempts_count: int = settings.DEFAULT_ATTEMPTS_COUNT,
        sleep_time_sec: float = settings.DEFAULT_SLEEP_TIME_SEC,
    ) -> int | None:
        while attempts_count > 0:
            await asyncio.sleep(sleep_time_sec)
            if cnt := (await page.locator(name).count()):
                return cnt
            attempts_count -= 1
        print(f"Element {name} not found.")

    async def get_url_dates(self) -> list[str]:
        urls = []
        for i in range(0, 3):
            date_from = datetime.now() + timedelta(days=i)
            date_from = date_from.strftime("%Y/%m/%d")
            url = (
                self.base_url
                + f"/en/schedule?dateFrom={date_from}+00%3A00"
                + f"&dateTo={date_from}+23%3A59&page=1"
            )
            urls.append(url)
        print(urls)
        return urls
