# PSP Dashboard

Universal dashboard for PSP team to monitor payment transactions, reconcile data between providers, and analyze metrics.

## Features

- **Multi-source Data** - Aggregates transactions from Vima API and PayShack
- **Real-time Updates** - WebSocket-based live data streaming
- **Auto-reconciliation** - Automatic matching between data sources
- **Analytics** - KPIs, trends, charts, project breakdown
- **Export** - CSV/Excel export for reporting

## Quick Start

### 1. Start Infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL and Redis.

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open Dashboard

Navigate to http://localhost:3000

---

## Project Structure

```
123hubuniversal/
├── backend/           # FastAPI backend
├── frontend/          # Next.js frontend
├── docs/              # Documentation
├── PRODUCT_PLAN.md    # Product overview
├── FEATURE_ROADMAP.md # Future features
├── CHANGELOG.md       # Version history
└── docker-compose.yml # Infrastructure
```

## Documentation

| Document | Description |
|----------|-------------|
| [PRODUCT_PLAN.md](PRODUCT_PLAN.md) | Product overview, architecture, status |
| [FEATURE_ROADMAP.md](FEATURE_ROADMAP.md) | Future features roadmap |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [docs/VIMA_API.md](docs/VIMA_API.md) | Vima API documentation |
| [docs/PAYSHACK_API.md](docs/PAYSHACK_API.md) | PayShack API (reversed) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md) | API contracts for frontend |
| [docs/BACKEND_TASKS.md](docs/BACKEND_TASKS.md) | Backend tasks |
| [docs/FRONTEND_SPEC.md](docs/FRONTEND_SPEC.md) | UI/UX specifications |
| [docs/FRONTEND_TASKS.md](docs/FRONTEND_TASKS.md) | Frontend tasks |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 |
| Database | PostgreSQL 15, Redis 7 |
| Frontend | Next.js 14, React 18, TypeScript |
| UI | Tailwind CSS, shadcn/ui, Recharts |
| State | TanStack Query, Zustand |

## API Endpoints

```
GET  /api/v1/transactions
GET  /api/v1/metrics/overview
GET  /api/v1/reconciliation/summary
GET  /api/v1/sync/status
GET  /api/v1/export/transactions
WS   /ws/updates
```

See [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md) for full API documentation.

## Environment Variables

Copy `env.example` to `.env` and configure:

```env
# Database
DATABASE_URL=postgresql+asyncpg://psp_user:psp_password@localhost:5432/psp_dashboard
REDIS_URL=redis://localhost:6379/0

# Vima API
VIMA_API_KEY=your_api_key
VIMA_BASE_URL=https://payment.woozuki.com/collector1/api/v1

# PayShack
PAYSHACK_EMAIL=your_email
PAYSHACK_PASSWORD=your_password
```

## Status

| Component | Status |
|-----------|--------|
| Backend | Production Ready (90%) |
| Frontend | Production Ready (85%) |
| Vima Integration | Complete |
| PayShack Integration | In Progress |

See [PRODUCT_PLAN.md](PRODUCT_PLAN.md) for detailed status.

---

## 🚀 Production Deployment

### Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 1 vCPU | 2 vCPU |
| RAM | 2 GB | 4 GB |
| Disk | 20 GB SSD | 50 GB SSD |
| OS | Ubuntu 22.04 | Ubuntu 22.04 |

### Database Size Estimate

| Period | Expected Size |
|--------|---------------|
| Now | ~1 GB |
| 3 months | ~3-5 GB |
| 1 year | ~15-20 GB |

### Deploy Steps

#### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USER/123hubuniversal.git
cd 123hubuniversal
```

#### 2. Configure Environment

```bash
cp env.example .env
nano .env  # Edit with production values
```

**Production .env:**
```env
# ВАЖНО: Измените пароли!
POSTGRES_USER=psp_prod
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_DB=psp_dashboard

VIMA_API_KEY=your_api_key
PAYSHACK_EMAIL=your_email
PAYSHACK_PASSWORD=your_password

# Frontend URLs
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com/ws

DEBUG=false
```

#### 3. Start Services

```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. Run Migrations

```bash
docker exec psp_backend alembic upgrade head
```

#### 5. Check Status

```bash
docker-compose -f docker-compose.prod.yml ps
docker logs psp_backend -f  # Watch logs
```

### SSL/HTTPS (Recommended)

Use Nginx or Traefik as reverse proxy with Let's Encrypt:

```nginx
# /etc/nginx/sites-available/psp-dashboard
server {
    listen 443 ssl http2;
    server_name dashboard.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Monitoring

```bash
# Check containers
docker-compose -f docker-compose.prod.yml ps

# View logs
docker logs psp_backend --tail 100 -f

# Check database
docker exec psp_postgres psql -U psp_prod -d psp_dashboard -c "SELECT count(*) FROM transactions;"

# Check Redis
docker exec psp_redis redis-cli info stats
```

### Backup

```bash
# Backup PostgreSQL
docker exec psp_postgres pg_dump -U psp_prod psp_dashboard > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i psp_postgres psql -U psp_prod psp_dashboard < backup_20260116.sql
```

---

## License

Private / Internal Use
