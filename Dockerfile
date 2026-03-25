FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 -r requirements.txt

COPY . .

EXPOSE 80

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:80"]
