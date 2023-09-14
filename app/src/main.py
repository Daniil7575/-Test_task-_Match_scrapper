from fastapi import FastAPI
from src.esportsbattle.router import router as esportsbattle_router

app = FastAPI(title="Scrapper")

app.include_router(esportsbattle_router)
