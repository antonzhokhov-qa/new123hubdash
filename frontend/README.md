# PSP Dashboard Frontend

Universal Payment Service Provider Dashboard - современный дашборд для мониторинга платежных операций.

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui (Radix UI)
- **Charts:** Recharts
- **State Management:** Zustand
- **Data Fetching:** TanStack Query (React Query)
- **Icons:** Lucide React

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

Create `.env.local` file:

```env
# API URL (backend)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Enable mock data (for development without backend)
NEXT_PUBLIC_USE_MOCK=true
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx            # Dashboard (/)
│   │   ├── transactions/       # Transactions page
│   │   ├── reconciliation/     # Reconciliation page
│   │   └── sync/               # Sync Status page
│   │
│   ├── components/
│   │   ├── ui/                 # Base UI components (shadcn/ui)
│   │   ├── layout/             # Layout components (Sidebar, Header)
│   │   ├── dashboard/          # Dashboard-specific components
│   │   ├── transactions/       # Transaction-specific components
│   │   └── charts/             # Chart components
│   │
│   ├── hooks/                  # React Query hooks
│   ├── lib/                    # Utilities, API client
│   └── stores/                 # Zustand stores
│
├── tailwind.config.ts
├── next.config.js
└── package.json
```

## Features

### Dashboard
- KPI cards with animated counters
- Transaction trend charts
- Status distribution donut chart
- Project breakdown bar chart
- Recent transactions table
- Auto-refresh every minute

### Transactions
- Advanced filtering (source, project, status, date range, search)
- Sortable columns
- Pagination
- Copy IDs to clipboard
- Export to CSV/Excel

### Reconciliation
- Daily reconciliation summary
- Match/Discrepancy statistics
- Discrepancies table with filtering
- Manual reconciliation trigger
- Export reports

### Sync Status
- Source status monitoring (Vima, PayShack)
- Last sync times and cursors
- Manual sync trigger
- Error display

## Design System

### Colors

- **Background:** Dark theme with `#0A0A0F` primary
- **Accent:** Indigo `#6366F1`
- **Status:**
  - Success: `#22C55E`
  - Failed: `#EF4444`
  - Pending: `#F59E0B`

### Typography

- **Sans:** Inter
- **Mono:** JetBrains Mono

## Scripts

```bash
npm run dev       # Development server
npm run build     # Production build
npm run start     # Start production server
npm run lint      # Run ESLint
```

## API Integration

The frontend expects a REST API at `NEXT_PUBLIC_API_URL`. See `docs/API_CONTRACTS.md` for full API documentation.

### Mock Mode

Set `NEXT_PUBLIC_USE_MOCK=true` to use mock data without a running backend. This is useful for frontend development and testing.
