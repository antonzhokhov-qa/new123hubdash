# PSP Dashboard Backend

FastAPI backend для PSP Dashboard с интеграцией Vima и PayShack API, автосверкой и real-time обновлениями.

## Возможности

- **Vima API Integration** - автоматическая синхронизация каждые 60 секунд
- **PayShack API Integration** - синхронизация Pay-In/Pay-Out каждые 5 минут
- **Real-time Updates** - WebSocket для мгновенных обновлений в дашборде
- **REST API** - endpoints для транзакций, метрик, сверки
- **Auto-reconciliation** - автосверка между Vima и PayShack по `client_operation_id`
- **Export** - экспорт в CSV/Excel

## Быстрый старт

### 1. Запуск инфраструктуры

```bash
cd /Users/dasabahtina/123hubuniversal
docker-compose up -d
```

### 2. Установка зависимостей

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Скопируйте `../env.example` в `.env` и настройте:

```bash
cp ../env.example .env
```

### 4. Применение миграций

```bash
alembic upgrade head
```

### 5. Запуск сервера

```bash
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Health
- `GET /health` - проверка состояния

### Transactions
- `GET /api/v1/transactions` - список транзакций
- `GET /api/v1/transactions/{id}` - детали транзакции

### Metrics
- `GET /api/v1/metrics/overview` - KPI метрики
- `GET /api/v1/metrics/by-project` - по проектам
- `GET /api/v1/metrics/trends` - тренды

### Sync
- `GET /api/v1/sync/status` - статус синхронизации
- `POST /api/v1/sync/trigger` - ручной запуск

### Reconciliation
- `GET /api/v1/reconciliation/summary?date=2026-01-15` - сводка
- `GET /api/v1/reconciliation/discrepancies` - расхождения
- `POST /api/v1/reconciliation/run` - запуск сверки

### Export
- `GET /api/v1/export/transactions?format=csv` - экспорт

### WebSocket
- `WS /ws/updates` - real-time обновления

## WebSocket Events

Подключение: `ws://localhost:8000/ws/updates`

Получаемые события:
- `sync_started` - начало синхронизации
- `sync_progress` - прогресс
- `sync_completed` - завершение
- `new_transactions` - новые транзакции
- `metrics_updated` - обновление метрик

## Тестирование

```bash
pytest
```

## Структура проекта

```
backend/
├── app/
│   ├── api/routes/      # API endpoints
│   ├── api/websocket.py # WebSocket
│   ├── db/              # Database connections
│   ├── etl/             # ETL pipeline
│   ├── integrations/    # External APIs
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── main.py          # App entry
├── migrations/          # Alembic migrations
└── tests/               # Tests
```

## Sync интервалы

- **Vima**: каждые 60 секунд (настраивается в .env)
- **PayShack**: каждые 300 секунд (5 минут)

## Переменные окружения

### Database
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

### Vima API
- `VIMA_API_KEY` - API ключ для Vima Collector
- `VIMA_BASE_URL` - базовый URL API

### PayShack API
- `PAYSHACK_EMAIL` - email для авторизации
- `PAYSHACK_PASSWORD` - пароль для авторизации
- `PAYSHACK_API_URL` - базовый URL API (https://api.payshack.in)

### Sync Settings
- `VIMA_SYNC_INTERVAL_SECONDS` - интервал синхронизации Vima (default: 60)
- `PAYSHACK_SYNC_INTERVAL_SECONDS` - интервал синхронизации PayShack (default: 300)

## Интеграции

### Vima API
- Cursor-based инкрементальная загрузка
- Поля: `operation_id`, `client_operation_id`, `amount`, `status`
- Документация: [../docs/VIMA_API.md](../docs/VIMA_API.md)

### PayShack API
- REST API с JWT авторизацией
- Требуется заголовок `reseller-id` (это `clientId` из логина)
- Поля: `txnId`, `orderId` (ключ сверки), `amount`, `txnStatus`
- Документация: [../docs/PAYSHACK_API.md](../docs/PAYSHACK_API.md)
