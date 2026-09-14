FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render/Koyeb/Heroku-style platforms set PORT automatically and route
# health checks to it - the bot's dummy web server (bot/webserver.py)
# binds to it. Telegram itself is still reached via long polling.
ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["python", "run.py"]
CMD ["--config", "config.yaml"]
