FROM python:3.11-slim

WORKDIR /app

COPY app.py .
COPY __init__.py .

RUN pip install --no-cache-dir flask==3.0.0 requests==2.31.0

RUN useradd --create-home appuser
USER appuser

EXPOSE 8002

CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=8002"]
