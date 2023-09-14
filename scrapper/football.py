import asyncio
import re
from datetime import datetime, timedelta

from playwright.async_api import Browser, Page, Route, async_playwright

from utils import GatheringTaskGroup


excluded_resource_types = ["image"]
excluded_url_names = ["facebook"]
DEFAULT_SLEEP_TIME_SEC = 2
DEFAULT_ATTEMPTS_COUNT = 15


async def block_aggressively(route: Route):
    if route.request.resource_type in excluded_resource_types:
        await route.abort(error_code="connectionclosed")
    else:
        await route.continue_()


class Football:
    def __init__(self, base_url: str, game_name: str = "Football") -> None:
        self.base_url = base_url
        self.game_name = game_name
        self.success_tasks = 0
        self.total_tasks = 0

    async def run(self):
        res = {self.game_name: []}
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
        tour_res = {}
        [tour_res.update(elem) for elem in tg.results()]
        res[self.game_name] = tour_res
        print(res)
        # Send to db
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
        urls = [
            "https://football.esportsbattle.com/en/schedule?page=1&dateFrom=2023%2F09%2F14+00%3A00&dateTo=2023%2F09%2F14+23%3A59",
            "https://football.esportsbattle.com/en/schedule?page=1&dateFrom=2023%2F09%2F15+00%3A00&dateTo=2023%2F09%2F15+23%3A59",
        ]
        return urls

    async def _tournament_runner(
        self, page: Page, url: str, browser: Browser, page_number: int = 1
    ):
        # await page.route(
        #     re.compile(r"\.(jpg|png|svg)$"), lambda route: route.abort()
        # )
        await page.route("**/*", block_aggressively)
        if page_number == 1:
            await page.goto(url, wait_until="domcontentloaded")
        # Wait while page is loading
        cnt = await self.wait_until_element_appears(
            page, ".tournaments-schedule-row"
        )
        if not cnt:
            print(f"Cant load resource on {url}")
            return []
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
            for idx, link in enumerate(links[:1]):
                print(link)
                # if (
                #     await page.locator(".tooltip-text.caption-1")
                #     .nth(idx)
                #     .inner_html()
                #     == "Tournament Finished"
                # ):
                #     print("Skipping finished tours")
                #     continue

                print(f"start match {idx}")
                tour_name = (
                    await page.locator(".tournament-title-label")
                    .nth(idx)
                    .inner_text()
                )
                tour_date = (
                    await page.locator(".location-title-date")
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
        res_dict = {}
        [res_dict.update(elem) for elem in res]
        next_page_class = (
            await page.locator(".tournaments-table-pagination")
            .locator(".align-mob-center")
            .nth(1)
            .get_attribute("class")
        )
        if "disable" in next_page_class:
            return res_dict
        await page.locator(".tournaments-table-pagination").locator(
            ".align-mob-center"
        ).nth(1).click()
        res_dict.update(
            await self._tournament_runner(page, url, browser, page_number=2)
        )
        return res_dict

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
        cnt = await self.wait_until_element_appears(
            page, ".tournament-matches-row"
        )

        if not cnt:
            print(f"Cant load resource on {url}")
            return []
        print(f"start data extraction for {number}")
        result = {tour_name: []}

        # for match_number in range(cnt):
        for match_number in range(2):
            row = page.locator(".tournament-matches-row").nth(match_number)
            # if (
            #     await row.locator(".tournament-matches-cell-status")
            #     .locator(".subcaption-1")
            #     .inner_text()
            # ) != "Planned":
            #     print("Match skipped")
            #     continue

            date_ = await row.locator(".tournament-matches-date").inner_text()
            team1, team2 = await row.locator(
                ".text-link.caption-2"
            ).all_inner_texts()
            result[tour_name].append(
                {
                    "date": tour_date.split()[0] + " " + date_,
                    "team_1": team1,
                    "team_2": team2,
                }
            )
        print(f"Data extraction finished for {number}")
        await page.close()
        return result

    async def get_match(self, page: Page, url):
        pass

    async def wait_until_element_appears(
        self,
        page: Page,
        name: str,
        attempts_count: int = DEFAULT_ATTEMPTS_COUNT,
        sleep_time_sec: float = DEFAULT_SLEEP_TIME_SEC,
    ) -> int | None:
        while attempts_count > 0:
            await asyncio.sleep(sleep_time_sec)
            if cnt := (await page.locator(name).count()):
                return cnt
            attempts_count -= 1
        print(f"Element {name} not found.")

    async def load_to_db(self):
        pass


f = Football("https://football.esportsbattle.com")
asyncio.run(f.run())
{
    "Football": {
        "Volta Club World Cup 2023-09-13, F": [
            {
                "date": "2023/09/14 00:10",
                "team_1": "Stryba",
                "team_2": "Soroka23",
            },
            {
                "date": "2023/09/14 00:10",
                "team_1": "Zellia",
                "team_2": "Gula14",
            },
        ],
        "Europa League B 2023-09-14, С1": [
            {
                "date": "2023/09/14 12:50",
                "team_1": "Bomb1to",
                "team_2": "KravaRK",
            },
            {"date": "2023/09/14 12:50", "team_1": "Arcos", "team_2": "Kodak"},
        ],
        "Premier League 2023-09-14, H1": [
            {"date": "2023/09/14 23:50", "team_1": "Zyen", "team_2": "Gbest"},
            {
                "date": "2023/09/14 23:50",
                "team_1": "MakcwellLm",
                "team_2": "Bane",
            },
        ],
        "Volta Club World Cup 2023-09-14, F": [
            {
                "date": "2023/09/15 00:10",
                "team_1": "fantazer",
                "team_2": "Nemo",
            },
            {
                "date": "2023/09/15 00:10",
                "team_1": "Andrew",
                "team_2": "pimchik",
            },
        ],
        "Europa League B 2023-09-15, С1": [
            {
                "date": "2023/09/15 12:50",
                "team_1": "Bomb1to",
                "team_2": "KravaRK",
            },
            {"date": "2023/09/15 12:50", "team_1": "Arcos", "team_2": "Kodak"},
        ],
        "Premier League 2023-09-15, H1": [
            {"date": "2023/09/15 23:50", "team_1": "Zyen", "team_2": "Gbest"},
            {
                "date": "2023/09/15 23:50",
                "team_1": "MakcwellLm",
                "team_2": "Vicmestro",
            },
        ],
    }
}
