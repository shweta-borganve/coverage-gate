FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src/ ./src/
COPY entrypoint.py ./entrypoint.py

ENTRYPOINT ["python", "/app/entrypoint.py"]
