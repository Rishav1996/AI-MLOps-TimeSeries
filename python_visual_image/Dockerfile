FROM python:3.7-slim-buster
RUN /usr/local/bin/python -m pip install --upgrade pip
WORKDIR /app/visualization
COPY . .
RUN pip install -r requirements.txt --no-cache-dir