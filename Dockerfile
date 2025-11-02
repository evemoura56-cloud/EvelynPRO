FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libjpeg62-turbo locales && rm -rf /var/lib/apt/lists/*

RUN sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen && locale-gen

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY templates ./templates
COPY static ./static
COPY .env .
RUN mkdir -p data

EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "backend.app:app", "--timeout", "180"]
