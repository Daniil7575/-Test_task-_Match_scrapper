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
