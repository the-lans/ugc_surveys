# UGC Surveys

REST API системы опросов. Два типа пользователей: **creator** создаёт опросы и смотрит статистику, **taker** проходит их — по одному вопросу за раз, прогресс сохраняется.

Полная документация по всем эндпоинтам доступна в Swagger: `http://localhost:8000/api/schema/swagger-ui/`

## Под какую нагрузку рассчитано

1 000 000 опросов, 15 000 000 пользователей, ~1 100 000 000 ответов.

Для этого в БД расставлены составные индексы, выборка следующего вопроса использует `NOT EXISTS` (не грузит весь список ответов в память), убраны все N+1 запросы. На проде PostgreSQL настроен с увеличенным пулом соединений и буфером, Gunicorn заменяет каждый воркер после тысячи запросов — воркер сначала дожидается конца текущего запроса, потом выходит, мастер тут же поднимает новый. Остальные воркеры продолжают работать, простоя нет.

## Локальный запуск

**Терминал 1 — бэкенд:**

```bash
git clone git@github.com:the-lans/ugc_surveys.git
cd ugc_surveys/src

python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python manage.py migrate --settings=config.settings.dev
python manage.py seed_dev_data --settings=config.settings.dev
python manage.py runserver --settings=config.settings.dev
```

Бэкенд на `http://localhost:8000`. Тестовые пользователи: `creator / testpass123`, `taker / testpass123`.

**Терминал 2 — фронтенд:**

Фронтенд — статические файлы (HTML + CSS + Vanilla JS), отдельного сборщика нет.

```bash
cd ugc_surveys/src/frontend
python -m http.server 3000
```

Открыть `http://localhost:3000/login.html`. Запросы к `/api/` автоматически уходят на `http://localhost:8000`.

На проде фронтенд раздаётся nginx из директории `frontend/` — отдельный запуск не нужен.

## Тесты

```bash
pytest --cov=apps --cov-fail-under=85
pre-commit run --all-files
```

## Деплой на прод

**Требования:** Docker и Docker Compose (v2+). Установить на Ubuntu/Debian:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Один раз на сервере:

```bash
ssh user@your-server
git clone git@github.com:the-lans/ugc_surveys.git ~/projects/ugc_surveys
cd ~/projects/ugc_surveys/src
cp .env.example .env
nano .env   
# заполнить DJANGO_SECRET_KEY, DB_PASSWORD, DJANGO_ALLOWED_HOSTS
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

Открыть `http://your-server-ip/login.html`.

Обновление после изменений:

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | Обязательна на проде |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Через запятую |
| `DATABASE_URL` | SQLite (dev) | Postgres URL для прода |
| `DB_PASSWORD` | — | Пароль PostgreSQL |
| `DJANGO_SECURE_SSL_REDIRECT` | `False` | `True` при работе за HTTPS |
| `DB_CONN_MAX_AGE` | `60` | Время жизни соединения к БД (сек) |
| `GUNICORN_WORKERS` | `4` | Рекомендуется `2 × кол-во ядер + 1` |
