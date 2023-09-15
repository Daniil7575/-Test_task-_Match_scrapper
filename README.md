# -Test_task-_Match_scrapper

## launch
1. Clone project to the desired directory with this command:
    ```
    git clone https://github.com/Daniil7575/-Test_task-_Match_scrapper.git
    ```
2. Go to the root folder of *project* (`-Test_task-_Match_scrapper`).
3. Add to `app/` folder a `.env` file and fill it like this:
    ```
    DB_HOST = localhost
    DB_PORT = 5432
    DB_USER = postgres
    DB_PASS = 123
    DB_NAME = scrap
    ```
4. If you want to use docker then you will need to build and up containers with the following commands:
    ```
    sudo docker compose build
    sudo docker compose up
    ```

5. If not then
    1. Make virtual environment with:
        ```
        python -m venv venv
        ```
    2. Activate it.
    3. Install all packages to do this, you need to:
        ```
        pip install -r app/requirements.txt
        pip install -r scrapper/requirements.txt
        ``` 
    4. Launch db and migrate it:
        ```
        cd app
        alembic upgrade head
        cd ..
        ```
    5. Launch api:
        ```
        cd app
        uvicorn src.main:app --host 0.0.0.0 --port 8000
        cd ..
        ```
    6. Launch scrapper:
        ```
        cd scrapper
        python main.py
        ```

