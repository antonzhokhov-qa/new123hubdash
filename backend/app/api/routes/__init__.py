"""API routes."""

from fastapi import APIRouter

from app.api.routes.transactions import router as transactions_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.sync import router as sync_router
from app.api.routes.reconciliation import router as reconciliation_router
from app.api.routes.export import router as export_router

router = APIRouter()

router.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])
router.include_router(metrics_router, prefix="/metrics", tags=["Metrics"])
router.include_router(sync_router, prefix="/sync", tags=["Sync"])
router.include_router(reconciliation_router, prefix="/reconciliation", tags=["Reconciliation"])
router.include_router(export_router, prefix="/export", tags=["Export"])
