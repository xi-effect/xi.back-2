FROM xieffect/python-base:python-3.12-poetry-2.1.3

WORKDIR /backend
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --only main

COPY ./alembic.ini /backend/alembic.ini
COPY ./alembic /backend/alembic
COPY ./app /backend/app
COPY ./static /backend/static

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
