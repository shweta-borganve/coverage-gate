FROM python:3.15-slim

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./

RUN pip install --no-cache-dir -r requirements-dev.txt

COPY src/ ./src/
COPY tests/ ./tests/

ENTRYPOINT ["python", "-m", "src.main"]
