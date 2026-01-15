# Frontend Development Tasks

## Overview

Этот документ содержит задачи для фронтенд-разработчика с приоритетами и чеклистами.

**Референсы:**
- UI/UX Spec: [FRONTEND_SPEC.md](./FRONTEND_SPEC.md)
- API Contracts: [API_CONTRACTS.md](./API_CONTRACTS.md)

---

## Phase 1: Project Setup & Foundation

### Task 1.1: Initialize Project
**Priority:** HIGH | **Estimate:** 2-4 hours

- [ ] Создать Next.js 14 проект с App Router
- [ ] Настроить TypeScript
- [ ] Установить и настроить Tailwind CSS
- [ ] Установить shadcn/ui
- [ ] Настроить ESLint + Prettier
- [ ] Создать структуру папок (см. FRONTEND_SPEC.md)

```bash
npx create-next-app@latest psp-dashboard --typescript --tailwind --app
cd psp-dashboard
npx shadcn-ui@latest init
```

### Task 1.2: Design System Setup
**Priority:** HIGH | **Estimate:** 4-6 hours

- [ ] Настроить цветовую палитру в `tailwind.config.js`
- [ ] Добавить кастомные цвета (см. Color Palette в FRONTEND_SPEC.md)
- [ ] Подключить шрифты Inter и JetBrains Mono
- [ ] Создать CSS variables для темизации
- [ ] Настроить dark/light theme toggle
- [ ] Создать `globals.css` с базовыми стилями

**tailwind.config.js пример:**
```javascript
theme: {
  extend: {
    colors: {
      background: {
        primary: '#0A0A0F',
        secondary: '#12121A',
        tertiary: '#1A1A24',
        elevated: '#22222E',
      },
      accent: {
        primary: '#6366F1',
        hover: '#818CF8',
      },
      status: {
        success: '#22C55E',
        failed: '#EF4444',
        pending: '#F59E0B',
      }
    },
    fontFamily: {
      sans: ['Inter', 'sans-serif'],
      mono: ['JetBrains Mono', 'monospace'],
    }
  }
}
```

### Task 1.3: Base Layout
**Priority:** HIGH | **Estimate:** 4-6 hours

- [ ] Создать `app/layout.tsx` с providers
- [ ] Создать компонент `Sidebar` (240px width)
- [ ] Создать компонент `Header` (64px height)
- [ ] Создать navigation items
- [ ] Добавить responsive behavior (collapsible sidebar)
- [ ] Добавить theme toggle в header

**Navigation Items:**
```
Dashboard     /dashboard      📊
Transactions  /transactions   💳
Reconciliation /reconciliation 🔄
Sync Status   /sync           ⚡
```

---

## Phase 2: Core Components

### Task 2.1: UI Components (shadcn/ui)
**Priority:** HIGH | **Estimate:** 4-6 hours

Добавить и кастомизировать shadcn/ui компоненты:

- [ ] Button (variants: default, outline, ghost, destructive)
- [ ] Card (с dark theme стилями)
- [ ] Badge (для статусов)
- [ ] Table (с сортировкой)
- [ ] Select / Dropdown
- [ ] DatePicker (range picker)
- [ ] Input
- [ ] Skeleton (для loading states)
- [ ] Dialog / Modal
- [ ] Tooltip
- [ ] Tabs

```bash
npx shadcn-ui@latest add button card badge table select input skeleton dialog tooltip tabs
```

### Task 2.2: Custom Components
**Priority:** HIGH | **Estimate:** 6-8 hours

- [ ] **KPICard** - карточка с метрикой
  - Props: label, value, subtext, trend, icon, color
  - Анимация count-up для чисел
  
- [ ] **StatusBadge** - бейдж статуса
  - Props: status (success/failed/pending)
  - Цвет и иконка по статусу
  
- [ ] **SourceBadge** - бейдж источника
  - Props: source (vima/payshack)
  - Цвет и label по источнику
  
- [ ] **DataTable** - расширенная таблица
  - Сортировка по колонкам
  - Пагинация
  - Row selection
  - Loading skeleton
  - Empty state

- [ ] **FilterPanel** - панель фильтров
  - Source, Project, Status селекты
  - Date range picker
  - Search input
  - Reset / Apply buttons

### Task 2.3: Chart Components
**Priority:** MEDIUM | **Estimate:** 6-8 hours

Установить и настроить Recharts:

- [ ] **TrendChart** - линейный/area график для трендов
  - X: время, Y: количество/сумма
  - Tooltip с деталями
  - Responsive
  
- [ ] **DonutChart** - распределение по статусам
  - Легенда
  - Проценты
  - Кликабельные сегменты
  
- [ ] **BarChart** - по проектам
  - Горизонтальный
  - Значения на барах
  - Сортировка

```bash
npm install recharts
```

---

## Phase 3: Pages Implementation

### Task 3.1: Dashboard Page
**Priority:** HIGH | **Estimate:** 8-10 hours

**Route:** `/` или `/dashboard`

- [ ] Period selector (Today, Yesterday, Last 7 days, Custom)
- [ ] 4 KPI Cards row:
  - Total Volume (amount + count)
  - Success (amount + count + trend)
  - Failed (amount + count + trend)
  - Conversion Rate (% + change)
- [ ] Charts grid (2x2):
  - Transaction Trends (line/area)
  - Status Distribution (donut)
  - By Project (horizontal bar)
  - By Source (pie)
- [ ] Recent Transactions table (last 10)
- [ ] Auto-refresh каждую минуту

**API Calls:**
```typescript
GET /api/v1/metrics/overview?from_date=...&to_date=...
GET /api/v1/metrics/trends?from_date=...&to_date=...&granularity=hour
GET /api/v1/metrics/by-project?from_date=...&to_date=...
GET /api/v1/transactions?limit=10&sort_by=created_at&order=desc
```

### Task 3.2: Transactions Page
**Priority:** HIGH | **Estimate:** 8-10 hours

**Route:** `/transactions`

- [ ] Filter Panel:
  - Source dropdown (All, Vima, PayShack)
  - Project dropdown (All, 91game, monetix, caroussel)
  - Status dropdown (All, Success, Failed, Pending)
  - Date range picker
  - Search input
- [ ] Transactions Table:
  - Columns: checkbox, source, ID, c_id, project, amount, status, user, created, actions
  - Sortable columns
  - Pagination (50 per page)
  - Click row → open detail modal
- [ ] Transaction Detail Modal:
  - All transaction fields
  - Copy buttons for IDs
  - Raw JSON viewer (collapsible)
- [ ] Export button (CSV/Excel dropdown)

**API Calls:**
```typescript
GET /api/v1/transactions?source=...&project=...&status=...&from_date=...&to_date=...&page=...&limit=50
GET /api/v1/transactions/{id}
GET /api/v1/export/transactions?format=csv&...
```

### Task 3.3: Reconciliation Page
**Priority:** MEDIUM | **Estimate:** 6-8 hours

**Route:** `/reconciliation`

- [ ] Date selector
- [ ] Summary Cards (4):
  - Total transactions
  - Matched (count + %)
  - Discrepancies (count + %)
  - Missing (count + %)
- [ ] Discrepancies Table:
  - Type, c_id, Vima amount, PayShack amount, Diff
  - Filter by type
  - Pagination
- [ ] Run Reconciliation button
- [ ] Export button

**API Calls:**
```typescript
GET /api/v1/reconciliation/summary?date=...
GET /api/v1/reconciliation/discrepancies?from_date=...&to_date=...&type=...
POST /api/v1/reconciliation/run
GET /api/v1/export/reconciliation?format=csv&date=...
```

### Task 3.4: Sync Status Page
**Priority:** LOW | **Estimate:** 4-6 hours

**Route:** `/sync`

- [ ] 2 Source Cards (Vima, PayShack):
  - Status indicator (dot: green/yellow/red)
  - Last sync time
  - Records synced
  - Next sync time
  - Last cursor
  - Trigger Sync button
- [ ] Sync History Table:
  - Time, Source, Status, Records, Duration
  - Last 20 syncs
- [ ] Global Sync Now button

**API Calls:**
```typescript
GET /api/v1/sync/status
POST /api/v1/sync/trigger
```

---

## Phase 4: Data Fetching & State

### Task 4.1: API Client Setup
**Priority:** HIGH | **Estimate:** 3-4 hours

- [ ] Создать `lib/api.ts` с базовым клиентом
- [ ] Error handling (ApiError class)
- [ ] Request/response logging (dev only)
- [ ] Base URL from env

### Task 4.2: React Query Setup
**Priority:** HIGH | **Estimate:** 4-6 hours

- [ ] Установить TanStack Query
- [ ] Создать QueryClientProvider
- [ ] Настроить default options (staleTime, refetchInterval)
- [ ] Создать hooks:
  - `useTransactions(params)`
  - `useTransaction(id)`
  - `useMetricsOverview(params)`
  - `useMetricsTrends(params)`
  - `useMetricsByProject(params)`
  - `useReconciliationSummary(date)`
  - `useDiscrepancies(params)`
  - `useSyncStatus()`

```bash
npm install @tanstack/react-query
```

### Task 4.3: Global State (Zustand)
**Priority:** MEDIUM | **Estimate:** 2-3 hours

- [ ] Установить Zustand
- [ ] Создать stores:
  - `useFilterStore` - глобальные фильтры (period, source)
  - `useUIStore` - sidebar collapsed, theme

```bash
npm install zustand
```

---

## Phase 5: Polish & UX

### Task 5.1: Loading States
**Priority:** MEDIUM | **Estimate:** 2-3 hours

- [ ] Skeleton screens для всех data-heavy компонентов
- [ ] Spinner для actions (buttons)
- [ ] Progress bar для exports
- [ ] Loading overlay для modals

### Task 5.2: Animations
**Priority:** LOW | **Estimate:** 3-4 hours

- [ ] Page transitions (fade in)
- [ ] Stagger animations для списков
- [ ] Count-up для чисел в KPI cards
- [ ] Hover effects для cards/rows
- [ ] Pulse для real-time updates

### Task 5.3: Error Handling
**Priority:** MEDIUM | **Estimate:** 2-3 hours

- [ ] Error boundary component
- [ ] Toast notifications для ошибок
- [ ] Retry buttons
- [ ] Empty states с helpful messages

### Task 5.4: Responsiveness
**Priority:** MEDIUM | **Estimate:** 4-6 hours

- [ ] Collapsible sidebar для laptop (< 1280px)
- [ ] Hamburger menu для tablet (< 1024px)
- [ ] Адаптивные таблицы (horizontal scroll или card view)
- [ ] Адаптивные charts

---

## Phase 6: Testing & Optimization

### Task 6.1: Testing
**Priority:** MEDIUM | **Estimate:** 4-6 hours

- [ ] Установить Vitest + Testing Library
- [ ] Unit tests для utils/formatters
- [ ] Component tests для ключевых компонентов
- [ ] Integration tests для pages

### Task 6.2: Performance
**Priority:** LOW | **Estimate:** 2-3 hours

- [ ] Lazy loading для charts
- [ ] Virtualized tables для больших списков
- [ ] Image optimization
- [ ] Bundle analysis

---

## Dependencies Summary

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "@tanstack/react-query": "^5.0.0",
    "zustand": "^4.0.0",
    "recharts": "^2.10.0",
    "date-fns": "^3.0.0",
    "lucide-react": "^0.300.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^18.0.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.0.0",
    "autoprefixer": "^10.0.0",
    "eslint": "^8.0.0",
    "prettier": "^3.0.0"
  }
}
```

---

## Estimated Timeline

| Phase | Tasks | Estimate | Can Start |
|-------|-------|----------|-----------|
| 1. Setup | 1.1-1.3 | 2-3 days | Immediately |
| 2. Components | 2.1-2.3 | 3-4 days | After Phase 1 |
| 3. Pages | 3.1-3.4 | 4-5 days | After Phase 2 |
| 4. Data | 4.1-4.3 | 2-3 days | Parallel with Phase 3 |
| 5. Polish | 5.1-5.4 | 2-3 days | After Phase 3 |
| 6. Testing | 6.1-6.2 | 2-3 days | After Phase 5 |

**Total: ~3-4 weeks**

---

## Quick Start

```bash
# 1. Create project
npx create-next-app@latest psp-dashboard --typescript --tailwind --app --src-dir

# 2. Install dependencies
cd psp-dashboard
npm install @tanstack/react-query zustand recharts date-fns lucide-react

# 3. Setup shadcn/ui
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card badge table select input skeleton dialog tooltip tabs

# 4. Create env file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# 5. Start development
npm run dev
```

---

## Mock Data (for development without backend)

Пока backend не готов, используй mock data:

```typescript
// lib/mock-data.ts
export const mockTransactions = [
  {
    id: "550e8400-e29b-41d4-a716-446655440000",
    source: "vima",
    source_id: "1067250921664811008",
    client_operation_id: "1768491979464",
    project: "91game",
    amount: 100.00,
    currency: "INR",
    status: "success",
    user_email: "sumit74360zne@gmail.com",
    created_at: "2026-01-15T15:46:20.195Z",
  },
  // ... more mock data
];

export const mockMetrics = {
  total: { count: 15420, amount: 1542000 },
  by_status: {
    success: { count: 14200, amount: 1420000 },
    failed: { count: 1100, amount: 110000 },
    pending: { count: 120, amount: 12000 },
  },
  conversion_rate: 92.1,
};
```

---

## Notes

- **API Base URL:** Используй `NEXT_PUBLIC_API_URL` env variable
- **Timezone:** Все даты приходят в UTC, конвертируй в локальное время для отображения [[memory:5980312]]
- **Amounts:** Форматируй с символом валюты (₹100.00 для INR)
- **IDs:** Truncate длинные ID, добавь copy-to-clipboard
