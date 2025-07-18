# xi.back-2
## How To
### Install
Эта установка нужна для запуска бэкенда локально и запуска форматеров, линтеров и тайп чекеров перед каждым коммитом. Для корректной работы требуется Python 3.12

```sh
pip install poetry==2.1.3
poetry install
pre-commit install --install-hooks
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
- [`http://localhost:5000/docs`](http://localhost:5000/docs): автоматическая OpenAPI-документация основного приложения


### Run Telegram Bot(s)
Этот раздел для тех, кто хочет запустить одного (или обоих) из наших телеграм-ботов локально. В целом можно использовать стейджинг для тестирования бота, но тогда тестирование станет последним этапом, после миграций и тестов. API можно запускать и без бота, тесты (в том числе тесты бота) будут работать локально даже без настроек ниже

Итак, настроить себе тестовое окружение локально просто:
1. Создать себе бота через [@BotFather](https://t.me/BotFather)
2. Добавить в окружение (файл `.env`, не заливать в git!) токен бота, в переменную `supbot__token` или `notifications_bot__token` в зависимости от нужного бота

Пример `.env`-файла для notifications bot:
```txt
notifications_bot__token=0000000000:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

Для supbot-а требуется дополнительная настройка:
1. Создать приватную группу в телеграмме для тестирования (добавлять туда никого не нужно пока)
2. В настройках группы включить "Темы" ("Topics") и сохранить
3. Разрешить добавлять бота в группы, если не разрешено (BotFather > /mybots > BOT > Bot Settings > Allow Groups? > Turn on)
4. Выключить у бота "Group Privacy", если включена (BotFather > /mybots > BOT > Bot Settings > Group Privacy > Turn off)
5. Добавить бота в группу (важно сделать это именно после шагов 3-4, иначе нужно выгнать бота и добавить заново)
6. Если хочется, можно теперь запретить добавлять бота в группы, т.е. отменить шаг 3 (шаг 4 отменять нельзя)
7. Сделать бота администратором в группе (важно выдать доступ к "управлению темами")
8. Добавить в окружение (файл `.env`, не заливать в git!) переменную `supbot__group_id` с id группы, в которую добавлен supbot (для получения id можно переслать сообщение из группы [боту](https://t.me/get_id_channel_bot) (начинается с -100))

Пример `.env`-файла для supbot:
```txt
supbot__token=0000000000:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
supbot__group_id=-100123456
```

После всех настроек можно запускать приложение, как сказано в [инструкции выше](#run). Важно использовать `--port 5000`, а если хочется использовать иной порт, то его нужно указать в переменной `bridge_base_url` в `.env`, например, так:
```txt
bridge_base_url=http://localhost:{port}
```

### Pochta
Для локального запуска сервиса можно использовать Gmail:
1. Заходим в управление аккаунтом Google
2. Включаем двухэтапную аутентификацию в разделе безопасность (если еще не включена)
3. Находим в строке поиска "пароли приложений" или "app pass"
4. Называем как угодно и копируем полученный пароль
5. Добавляем в .env файл необходимые переменные:

```txt
email__username=your_email@gmail.com
email__password=your_password
email__hostname=smtp.gmail.com
```

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
