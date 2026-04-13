FROM python:3.12-slim

WORKDIR /app

# 系统依赖 · cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# cron 任务 · 每天 UTC 0:30 跑 daily_digest
RUN echo "30 0 * * * root cd /app && python -m daily_digest >> /var/log/daily_digest.log 2>&1" > /etc/cron.d/daily-digest \
 && chmod 0644 /etc/cron.d/daily-digest

# 启动命令 · 既跑 cron 也 tail 日志到 stdout
CMD bash -c "cron && tail -f /var/log/daily_digest.log"
