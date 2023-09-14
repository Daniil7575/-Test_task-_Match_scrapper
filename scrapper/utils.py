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


excluded_resource_types = ["image"]
# excluded_url_names = ["facebook"]


async def block_aggressively(route: Route):
    if route.request.resource_type in excluded_resource_types:
        await route.abort(error_code="connectionclosed")
    else:
        await route.continue_()
