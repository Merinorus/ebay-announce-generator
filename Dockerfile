FROM python:3.10-slim

# Copy script
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY . /app

ENV PYTHONPATH "${PYTHONPATH}:/app"
