FROM python:3.11

WORKDIR /scrapper

COPY . /scrapper/
RUN pip install -r requirements.txt
RUN playwright install chromium