import os


if os.getenv("IS_DOCKER"):
    API_URL = "http://api:8000/esportsbattle"
else:
    API_URL = "http://127.0.0.1:8000/esportsbattle"
DEFAULT_SLEEP_TIME_SEC = 2
DEFAULT_ATTEMPTS_COUNT = 15
SLEEP_TIME = 60
