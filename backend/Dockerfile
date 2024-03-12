FROM python:3.8-slim-buster
RUN /usr/local/bin/python -m pip install --upgrade pip
WORKDIR /app/backend
COPY pyproject.toml .
COPY requirements.txt .
COPY requirements_conda.txt .
RUN pip install poetry
RUN poetry config installer.max-workers 10
RUN cat requirements.txt | xargs poetry add
COPY . .