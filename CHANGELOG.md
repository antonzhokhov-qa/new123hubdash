# Changelog

All notable changes to PSP Dashboard project.

## [1.0.0] - 2026-01-16

### Added

#### Backend
- FastAPI application with REST API
- Vima API integration with cursor-based incremental loading
- ETL pipeline with APScheduler (60s sync interval)
- WebSocket for real-time updates
- PostgreSQL models: Transaction, SyncState, Reconciliation
- Pydantic schemas for validation
- Reconciliation service with matching by client_operation_id
- Export to CSV/Excel
- Alembic migrations
- Basic test coverage (API, Vima client)
- Docker support (Dockerfile, docker-compose)

#### Frontend
- Next.js 14 application with App Router
- Dashboard page with KPI cards, charts, recent transactions
- Transactions page with filters and pagination
- Reconciliation page with summary view
- Sync status page
- Charts: TrendChart, DonutChart, BarChart (Recharts)
- UI components based on shadcn/ui
- TanStack Query for data fetching
- Zustand for state management
- Tailwind CSS with dark theme

#### Documentation
- VIMA_API.md - Full Vima Collector API documentation
- PAYSHACK_API.md - Reversed PayShack API documentation
- ARCHITECTURE.md - System architecture and database schema
- BACKEND_TASKS.md - Backend development tasks
- FRONTEND_SPEC.md - UI/UX specifications
- FRONTEND_TASKS.md - Frontend development tasks
- API_CONTRACTS.md - API contracts for frontend

#### Infrastructure
- docker-compose.yml with PostgreSQL and Redis
- env.example with all environment variables

### Known Issues
- ClickHouse not yet integrated for analytics optimization

---

## [Unreleased]

### Added

#### Extended Analytics (Phase 2)
- **Гранулярность по минутам**: `/metrics/trends` теперь поддерживает `granularity=minute|5min|15min|hour|day`
- **Разделение по источникам**: Новый эндпоинт `/metrics/by-source` с трендами для vima и payshack отдельно
- **Тепловые карты**: Эндпоинт `/metrics/heatmap` с измерениями:
  - `hour_day` - Час × День недели
  - `merchant_hour` - Мерчант × Час
  - `merchant_day` - Мерчант × День недели
- **Метрики**: Поддержка `metric=amount|count|conversion` для тепловых карт

#### PayShack Deep Integration
- Методы API: `get_clients()`, `get_resellers()`, `get_service_providers()`, `get_balance()`
- Модели: `PayShackClient`, `PayShackReseller`, `PayShackServiceProvider`, `PayShackBalanceSnapshot`
- ETL: Синхронизация метаданных PayShack каждые 30 минут
- Снапшоты балансов для исторического трекинга

#### Export Improvements
- `/export/payshack-report` - Генерация отчетов из PayShack API
- `/export/payshack-clients` - Экспорт списка клиентов PayShack
- `/export/metrics-summary` - Экспорт сводки метрик по проектам и источникам

#### PayShack API
- PayShack API интеграция через HTTPX (без Playwright)
- `PayShackAPIClient` с авторизацией и пагинацией
- `PayShackNormalizer` для унификации транзакций PayShack → Transaction модель
- Поддержка Pay-In и Pay-Out транзакций PayShack
- Инкрементальная синхронизация по `modifiedAt`

#### Historical Sync Improvements
- **Детекция первого запуска**: `check_first_run()` проверяет наличие данных в БД
- **Historical sync для Vima**: Метод `historical_sync(days=7)` загружает данные по датам
- **Historical sync для PayShack**: Полная загрузка с `full_sync=True`
- **Initial sync**: При пустой БД автоматически загружается 7 дней истории из обоих источников
- **Ручной триггер**: `trigger_historical_sync(days=N)` для принудительной загрузки

### Changed
- `TrendPoint` расширен: добавлены `pending_count` и `conversion_rate`
- Убран Playwright из зависимостей (не требуется для PayShack API)
- Обновлена документация PayShack API
- `PAYSHACK_BASE_URL` переименован в `PAYSHACK_API_URL`
- **vima_max_batches**: увеличен до 100 (было 20) для загрузки всех мерчантов
- **Интервалы синхронизации**: Vima 30s, PayShack 60s, PayShack metadata 300s

### Fixed
- Исправлена документация: PayShack API возвращает данные в открытом JSON (не зашифровано)

---

### Planned for v1.1
- Period comparison (Today vs Yesterday, Week vs Week)
- Hourly distribution heatmap
- Multi-select project filter
- Payment method filter

### Planned for v1.2
- Alert system with configurable rules
- Telegram/Email notifications

### Planned for v1.3
- Role-based dashboard views
- Merchant health scores

See [FEATURE_ROADMAP.md](FEATURE_ROADMAP.md) for full roadmap.

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-01-16 | Initial release with Vima integration |
| 0.1.0 | 2026-01-15 | Project planning and documentation |
