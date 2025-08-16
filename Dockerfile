FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends     tesseract-ocr     poppler-utils     libwebp7     libjpeg62-turbo     zlib1g     libopenjp2-7     libpng16-16     libtiff6     libgl1     && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn

ENV PORT=10000
CMD exec gunicorn app:app --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120 --log-level debug
