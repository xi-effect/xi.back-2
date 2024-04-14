FROM python:3.12-alpine

WORKDIR /backend
RUN pip install --upgrade pip

RUN pip install poetry==1.8.2
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --only main
