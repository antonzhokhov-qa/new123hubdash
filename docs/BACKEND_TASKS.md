# Backend Development Tasks

## Overview

Этот документ содержит детальные задачи для backend-разработчика с приоритетами и зависимостями.

---

## Phase 1: Infrastructure (Priority: HIGH)

### Task 1.1: Docker Setup
**Estimate:** 2-4 hours

- [ ] Создать `docker-compose.yml` с PostgreSQL 15 и Redis 7
- [ ] Настроить volumes для персистентности данных
- [ ] Создать `.env.example` с переменными окружения
- [ ] Проверить что контейнеры запускаются

**Acceptance Criteria:**
```bash
docker-compose up -d
# PostgreSQL доступен на localhost:5432
# Redis доступен на localhost:6379
```

### Task 1.2: Project Structure
**Estimate:** 2-4 hours

- [ ] Инициализировать Python проект с Poetry/pip
- [ ] Создать структуру папок (см. ARCHITECTURE.md)
- [ ] Настроить FastAPI приложение
- [ ] Добавить health endpoint `/api/v1/health`

**Dependencies:** Task 1.1

### Task 1.3: Database Setup
**Estimate:** 4-6 hours

- [ ] Настроить SQLAlchemy 2.0 с async
- [ ] Настроить Alembic для миграций
- [ ] Создать миграцию для таблицы `transactions`
- [ ] Создать миграцию для таблицы `sync_state`
- [ ] Создать миграцию для таблицы `reconciliation_results`
- [ ] Создать партиции для текущего месяца

**Dependencies:** Task 1.1, Task 1.2

**Schema:** См. ARCHITECTURE.md, секция "Database Schema"

---

## Phase 2: Vima Integration (Priority: HIGH)

### Task 2.1: Vima API Client
**Estimate:** 4-6 hours

- [ ] Создать `app/integrations/vima/client.py`
- [ ] Реализовать класс `VimaClient` с httpx
- [ ] Поддержка всех параметров фильтрации
- [ ] Поддержка cursor-based пагинации
- [ ] Обработка ошибок и retry logic
- [ ] Unit тесты

**API Reference:** См. VIMA_API.md

```python
class VimaClient:
    async def get_operations(
        self,
        project: str = None,
        status: str = None,
        from_date: date = None,
        to_date: date = None,
        from_operation_create_id: str = None,
        count: int = 100,
        descending: bool = False
    ) -> List[Dict]
```

### Task 2.2: Vima Normalizer
**Estimate:** 3-4 hours

- [ ] Создать `app/integrations/vima/normalizer.py`
- [ ] Маппинг Vima полей -> unified Transaction model
- [ ] Нормализация статусов
- [ ] Парсинг вложенных полей (create_params.params.payment.*)
- [ ] Конвертация amount (minor -> major units)
- [ ] Конвертация timestamps в UTC

**Status Mapping:**
```python
STATUS_MAP = {
    'success': 'success',
    'fail': 'failed',
    'in_process': 'pending',
    'user_input_required': 'pending'
}
```

### Task 2.3: Vima ETL Pipeline
**Estimate:** 6-8 hours

- [ ] Создать `app/etl/vima_sync.py`
- [ ] Реализовать инкрементальную загрузку через cursor
- [ ] Дедупликация по data_hash
- [ ] Upsert логика (ON CONFLICT UPDATE)
- [ ] Обновление sync_state после каждого batch
- [ ] Логирование прогресса

**Algorithm:**
```
1. Get last_create_cursor from sync_state
2. Fetch operations with cursor
3. For each operation:
   - Normalize to Transaction
   - Calculate data_hash
   - Upsert to DB
4. Update cursor in sync_state
5. Repeat until no more data
```

### Task 2.4: Vima Scheduler
**Estimate:** 2-3 hours

- [ ] Создать `app/etl/scheduler.py`
- [ ] Настроить APScheduler
- [ ] Job для Vima sync каждые 5 минут
- [ ] Graceful shutdown
- [ ] Предотвращение concurrent runs

---

## Phase 3: REST API (Priority: HIGH)

### Task 3.1: Transaction Endpoints
**Estimate:** 6-8 hours

- [ ] `GET /api/v1/transactions` - список с фильтрами и пагинацией
- [ ] `GET /api/v1/transactions/{id}` - детали транзакции
- [ ] Фильтры: source, project, status, date range
- [ ] Пагинация: page, limit (max 100)
- [ ] Сортировка: sort_by, order

**Query Parameters:**
```
?source=vima|payshack
&project=monetix|91game
&status=success|failed|pending
&from_date=2026-01-01
&to_date=2026-01-15
&page=1
&limit=50
&sort_by=created_at
&order=desc
```

### Task 3.2: Metrics Endpoints
**Estimate:** 6-8 hours

- [ ] `GET /api/v1/metrics/overview` - общая статистика
- [ ] `GET /api/v1/metrics/by-project` - по проектам
- [ ] `GET /api/v1/metrics/by-status` - по статусам
- [ ] `GET /api/v1/metrics/trends` - тренды по времени
- [ ] Redis кэширование (TTL: 60s - 300s)

**Response Example:**
```json
{
  "period": {"from": "2026-01-01", "to": "2026-01-15"},
  "total": {"count": 15420, "amount": 1542000.00},
  "by_status": {
    "success": {"count": 14200, "amount": 1420000.00},
    "failed": {"count": 1100, "amount": 110000.00}
  },
  "conversion_rate": 92.1,
  "avg_ticket": 100.00
}
```

### Task 3.3: Sync Status Endpoints
**Estimate:** 2-3 hours

- [ ] `GET /api/v1/sync/status` - статус синхронизации
- [ ] `POST /api/v1/sync/trigger` - ручной запуск

---

## Phase 4: PayShack Integration (Priority: MEDIUM)

### Task 4.1: PayShack Browser Client
**Estimate:** 8-10 hours

- [ ] Создать `app/integrations/payshack/client.py`
- [ ] Использовать Playwright для browser automation
- [ ] Реализовать login flow
- [ ] Session management (сохранение в Redis)
- [ ] Парсинг Pay-In transactions из DOM
- [ ] Парсинг Pay-Out transactions из DOM
- [ ] Обработка пагинации

**API Reference:** См. PAYSHACK_API.md

### Task 4.2: PayShack Normalizer
**Estimate:** 3-4 hours

- [ ] Создать `app/integrations/payshack/normalizer.py`
- [ ] Маппинг PayShack полей -> unified Transaction
- [ ] Парсинг amount (убрать ₹ символ)
- [ ] Нормализация статусов
- [ ] Парсинг дат (IST -> UTC)

**Status Mapping:**
```python
PAYSHACK_STATUS_MAP = {
    'Success': 'success',
    'SUCCESS': 'success',
    'Failed': 'failed',
    'FAILED': 'failed',
    'Initiated': 'pending',
    'INITIATED': 'pending',
    'Pending': 'pending',
    'In Process': 'pending'
}
```

### Task 4.3: PayShack ETL Pipeline
**Estimate:** 6-8 hours

- [ ] Создать `app/etl/payshack_sync.py`
- [ ] Пагинация через все страницы
- [ ] Дедупликация
- [ ] Upsert логика
- [ ] Scheduler job каждые 10 минут

---

## Phase 5: Reconciliation (Priority: MEDIUM)

### Task 5.1: Reconciliation Engine
**Estimate:** 8-10 hours

- [ ] Создать `app/services/reconciliation_service.py`
- [ ] Matching по client_operation_id / order_id
- [ ] Сравнение amount, status
- [ ] Определение типа расхождения
- [ ] Сохранение результатов

**Match Types:**
- `matched` - полное совпадение
- `discrepancy_amount` - разница в сумме
- `discrepancy_status` - разный статус
- `missing_vima` - нет в Vima
- `missing_payshack` - нет в PayShack

### Task 5.2: Reconciliation Endpoints
**Estimate:** 4-6 hours

- [ ] `GET /api/v1/reconciliation/summary` - сводка за дату
- [ ] `GET /api/v1/reconciliation/discrepancies` - список расхождений
- [ ] `POST /api/v1/reconciliation/run` - запуск сверки

### Task 5.3: Export Functionality
**Estimate:** 4-6 hours

- [ ] `GET /api/v1/export/transactions` - CSV/Excel
- [ ] `GET /api/v1/export/reconciliation` - CSV/Excel
- [ ] Streaming для больших файлов

---

## Phase 6: Optimization (Priority: LOW)

### Task 6.1: ClickHouse Integration (Optional)
**Estimate:** 8-10 hours

- [ ] Настроить ClickHouse
- [ ] Создать таблицу hourly_metrics
- [ ] Materialized view для агрегаций
- [ ] Синхронизация PostgreSQL -> ClickHouse

### Task 6.2: Performance Tuning
**Estimate:** 4-6 hours

- [ ] Analyze и optimize SQL queries
- [ ] Добавить недостающие индексы
- [ ] Tune PostgreSQL settings
- [ ] Профилирование bottlenecks

---

## Development Guidelines

### Code Style
- Python 3.11+
- Type hints обязательны
- Docstrings для public методов
- Black + isort + flake8

### Testing
- Unit тесты для всех сервисов
- Integration тесты для API
- Minimum 80% coverage

### Logging
```python
import structlog
logger = structlog.get_logger()

logger.info("sync_started", source="vima")
logger.error("sync_failed", source="vima", error=str(e))
```

### Error Handling
```python
from fastapi import HTTPException

class VimaAPIError(Exception):
    pass

# В endpoints
try:
    data = await vima_client.get_operations()
except VimaAPIError as e:
    raise HTTPException(status_code=502, detail=str(e))
```

---

## Estimated Timeline

| Phase | Tasks | Estimate | Can Start |
|-------|-------|----------|-----------|
| 1. Infrastructure | 1.1-1.3 | 1-2 days | Immediately |
| 2. Vima Integration | 2.1-2.4 | 3-4 days | After Phase 1 |
| 3. REST API | 3.1-3.3 | 2-3 days | After Phase 2 |
| 4. PayShack | 4.1-4.3 | 3-4 days | After Phase 1 |
| 5. Reconciliation | 5.1-5.3 | 3-4 days | After Phase 2 & 4 |
| 6. Optimization | 6.1-6.2 | 2-3 days | After Phase 5 |

**Total: ~3-4 weeks**

---

## Quick Start for Developer

```bash
# 1. Clone and setup
cd /Users/dasabahtina/123hubuniversal
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 2. Start infrastructure
docker-compose up -d

# 3. Run migrations
cd backend
alembic upgrade head

# 4. Start development server
uvicorn app.main:app --reload --port 8000

# 5. Test Vima API
curl "https://payment.woozuki.com/collector1/api/v1/operation?apikey=master-3E193252DE4A4B4C80862F67B2972D3D&count=5"
```

---

## Contact / Questions

При возникновении вопросов по:
- **Vima API** - см. VIMA_API.md
- **PayShack API** - см. PAYSHACK_API.md  
- **Архитектура** - см. ARCHITECTURE.md
