# Dockerfile for Python node
FROM python:3.8-slim

WORKDIR /app
COPY . .

RUN pip install xmlrpc

CMD ["python", "main.py"]
