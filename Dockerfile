FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MARGELIS_HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd --create-home --uid 10001 demo \
    && mkdir -p /app/.demo-data \
    && chown -R demo:demo /app

USER demo
EXPOSE 8000

CMD ["python", "server.py"]

