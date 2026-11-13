
FROM python:3.15-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY tests/ ./tests/

ENTRYPOINT ["python", "-m", "src.main"] 