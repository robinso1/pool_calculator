FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements_web.txt ./
RUN pip install -r requirements.txt -r requirements_web.txt

COPY . .

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "src.web.app:app"]
