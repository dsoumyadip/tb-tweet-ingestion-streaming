FROM python:3.7

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN mkdir -p /app/src

COPY src/ /app/src

CMD ["python", "./src/ingest_tweets_streaming.py"]