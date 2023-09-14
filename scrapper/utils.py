import asyncio

from playwright.async_api import Route


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


class Scrapper:
    def __init__(self, base_url: str, game_name: str) -> None:
        self.base_url = base_url
        self.game_name = game_name
        self.success_tasks = 0
        self.total_tasks = 0

    async def run():
        raise NotImplementedError("Scrapper should implement 'run' function!")

    def __str__(self) -> str:
        return f"{self.game_name} scrapper"


excluded_resource_types = ["image"]
# excluded_url_names = ["facebook"]


async def block_aggressively(route: Route):
    if route.request.resource_type in excluded_resource_types:
        await route.abort(error_code="connectionclosed")
    else:
        await route.continue_()
