FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# 8000: REST API + dashboard data · 5020: Modbus TCP (SCADA)
EXPOSE 8000 5020

# Persistent on-prem data lives in /data — mount a volume here in production
ENV PANOPULSE_DB_PATH=/data/panopulse.db
VOLUME ["/data"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
