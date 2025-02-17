FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose 8080 (commonly used on Cloud Run)
EXPOSE 8080

# Use $PORT if set, otherwise default to 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "${PORT:-8080}"]
