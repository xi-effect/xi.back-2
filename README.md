# xi.back-2
## How To
### Install
Эта установка нужна для запуска бэкенда локально и запуска форматеров, линтеров и тайп чекеров перед каждым коммитом. Для корректной работы требуется Python 3.12

```sh
pip install poetry==1.8.2
poetry install
pre-commit install
```

### Run
Сначала нужно запустить зависимости (нужен настроенный docker):
```sh
docker compose up -d --wait
```

Запуск бэкенда локально:
```sh
uvicorn app.main:app --port 5000 --reload
```

Остановить зависимости:
```sh
docker compose down
```

### Links
После запуска приложения становятся доступны следующие порты и ссылки:
- `5432`: порт для подключения к базе данных PostgreSQL
- `5672`: порт для подключения к брокеру сообщений RabbitMQ
- [`http://localhost:15672`](http://localhost:15672): management-консоль для RabbitMQ (логин и пароль: guest)
- [`http://localhost:5100`](http://localhost:5100/docs): автоматическая OpenAPI-документация основного приложения

### Tests
#### Terminal
Запуск тестов локально (в виртуальном окружении):
```sh
pytest tests
```
С проверкой покрытия:
```sh
pytest tests --cov=.
```

#### PyCharm
1. Создать новую конфигурацию: Edit Configurations > + > pytest
2. Настроить путь: Script Path > Выбор папки (выбрать папку tests)
3. Настроить рабочую директорию: Environment > Working directory > Выбор папки (выбрать корень проекта)
4. (опционально) В Additional Arguments добавить `--cov=.` для проверки покрытия

Отчёт о покрытии кода можно получить командой:
```sh
coverage report
```

### Migrations
После аппрува задачи, в которой были изменения в БД, нужно написать миграцию. В этом поможет автоматическая генерация миграций через alembic, описанная ниже

Для начала нужно выключить приложение и отчистить базу данных:
```sh
docker compose down
```

Затем можно сбилдить и запустить контейнер для миграций:
```sh
docker compose run --build --rm -ti alembic
```

Должен открыться терминал (sh), в котором уже будет можно запускать команды alembic-а:
```sh
alembic upgrade head
alembic revision --autogenerate -m "<message>" --rev-id "<issue>"
```

## Info
### Stack
- Python 3.12
- FastAPI
- SQLAlchemy 2.0 (async)
- Poetry
- Linters (flake8, wemake-style-guide, mypy)
- Formatters (black, autoflake)
- Pre-commit
- Pytest

Версии можно найти в [pyproject.toml](./pyproject.toml)

### Контейнеры
- `mq`: локальный брокер RabbitMQ, сбрасывается при рестарте
- `db`: локальная база данных PostgreSQL для тестов и проверок, сбрасывается при рестарте
- `alembic`: специальный контейнер для работы с миграциями, работает только с `--profile migration`
- `app`: докеризированное приложение основного API сервиса, сделано для полных проверок и работает только с `--profile app`

### Commands
```sh
# запустить все вспомогательные сервисы для локальной разработки
docker compose up -d
# выключить обратно
docker compose down

# тоже самое, но вместе с докеризированным приложением
docker compose --profile app up -d
docker compose --profile app down

# смотреть логи в реальном времени
docker compose logs --follow <сервис>
docker compose logs --follow mq  # пример

# проверить статусы сервисов
docker compose ps -a

# зайти в какой-то контейнер
docker compose exec -ti <сервис> <shell-команда>
docker compose exec -ti db psql -U test -d test  # пример
```
