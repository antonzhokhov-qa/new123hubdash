"""Reconciliation service for matching transactions between sources."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any

import structlog
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.transaction import Transaction
from app.models.reconciliation import ReconciliationRun, ReconciliationResult

logger = structlog.get_logger()


class ReconciliationService:
    """
    Service for reconciling transactions between Vima and PayShack.
    
    Matching key: client_operation_id (Vima) = order_id (PayShack)
    """

    # Tolerance for amount matching
    AMOUNT_TOLERANCE = Decimal("0.01")  # 1 paisa
    AMOUNT_TOLERANCE_PERCENT = Decimal("0.001")  # 0.1%

    async def run_for_date(self, recon_date: date) -> Dict[str, Any]:
        """
        Run reconciliation for a specific date.
        
        Algorithm:
        1. Load Vima transactions for date
        2. Load PayShack transactions for date
        3. Build index by client_operation_id / order_id
        4. Match and compare
        5. Save results
        """
        async with async_session_maker() as session:
            # Create reconciliation run
            run = ReconciliationRun(
                recon_date=recon_date,
                status="running",
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)

            try:
                logger.info("reconciliation_started", date=recon_date.isoformat())

                # Load Vima transactions
                vima_txns = await self._load_transactions(
                    session,
                    source="vima",
                    date=recon_date,
                )
                
                # Load PayShack transactions
                payshack_txns = await self._load_transactions(
                    session,
                    source="payshack",
                    date=recon_date,
                )

                logger.info(
                    "reconciliation_data_loaded",
                    vima_count=len(vima_txns),
                    payshack_count=len(payshack_txns),
                )

                # Build PayShack index by order_id
                payshack_index: Dict[str, Transaction] = {}
                for txn in payshack_txns:
                    if txn.order_id:
                        payshack_index[txn.order_id] = txn
                    elif txn.client_operation_id:
                        payshack_index[txn.client_operation_id] = txn

                # Process matching
                results = []
                matched_payshack_ids = set()

                for vima_txn in vima_txns:
                    matching_key = vima_txn.client_operation_id
                    
                    if not matching_key:
                        # No matching key - cannot reconcile
                        continue

                    payshack_txn = payshack_index.get(matching_key)

                    if payshack_txn:
                        # Found match - compare
                        matched_payshack_ids.add(payshack_txn.id)
                        result = self._compare_transactions(
                            run.id, recon_date, vima_txn, payshack_txn
                        )
                    else:
                        # Missing in PayShack
                        result = ReconciliationResult(
                            recon_run_id=run.id,
                            recon_date=recon_date,
                            vima_txn_id=vima_txn.id,
                            payshack_txn_id=None,
                            client_operation_id=matching_key,
                            match_status="missing_payshack",
                            discrepancy_type="missing",
                            vima_amount=vima_txn.amount,
                            vima_status=vima_txn.status,
                        )

                    results.append(result)

                # Find PayShack transactions not in Vima
                for payshack_txn in payshack_txns:
                    if payshack_txn.id not in matched_payshack_ids:
                        result = ReconciliationResult(
                            recon_run_id=run.id,
                            recon_date=recon_date,
                            vima_txn_id=None,
                            payshack_txn_id=payshack_txn.id,
                            client_operation_id=payshack_txn.order_id or payshack_txn.client_operation_id,
                            match_status="missing_vima",
                            discrepancy_type="missing",
                            payshack_amount=payshack_txn.amount,
                            payshack_status=payshack_txn.status,
                        )
                        results.append(result)

                # Save results
                session.add_all(results)

                # Update run summary
                matched_count = sum(1 for r in results if r.match_status == "matched")
                discrepancy_count = sum(1 for r in results if r.match_status == "discrepancy")
                missing_vima = sum(1 for r in results if r.match_status == "missing_vima")
                missing_payshack = sum(1 for r in results if r.match_status == "missing_payshack")

                run.total_vima = len(vima_txns)
                run.total_payshack = len(payshack_txns)
                run.matched = matched_count
                run.discrepancies = discrepancy_count
                run.missing_vima = missing_vima
                run.missing_payshack = missing_payshack
                run.status = "completed"
                run.completed_at = datetime.now(timezone.utc)

                await session.commit()

                logger.info(
                    "reconciliation_completed",
                    date=recon_date.isoformat(),
                    matched=matched_count,
                    discrepancies=discrepancy_count,
                    missing_vima=missing_vima,
                    missing_payshack=missing_payshack,
                )

                return {
                    "status": "completed",
                    "run_id": str(run.id),
                    "matched": matched_count,
                    "discrepancies": discrepancy_count,
                    "missing_vima": missing_vima,
                    "missing_payshack": missing_payshack,
                }

            except Exception as e:
                logger.error("reconciliation_failed", error=str(e))
                
                run.status = "failed"
                run.error_message = str(e)[:500]
                await session.commit()

                return {
                    "status": "failed",
                    "error": str(e),
                }

    async def _load_transactions(
        self,
        session: AsyncSession,
        source: str,
        date: date,
    ) -> List[Transaction]:
        """Load transactions for a source and date."""
        from datetime import datetime as dt

        start = dt.combine(date, dt.min.time())
        end = dt.combine(date, dt.max.time())

        result = await session.execute(
            select(Transaction).where(
                and_(
                    Transaction.source == source,
                    Transaction.created_at >= start,
                    Transaction.created_at <= end,
                )
            )
        )
        return list(result.scalars().all())

    def _compare_transactions(
        self,
        run_id: uuid.UUID,
        recon_date: date,
        vima: Transaction,
        payshack: Transaction,
    ) -> ReconciliationResult:
        """Compare two matched transactions and return result."""
        discrepancies = []
        
        # Compare amount
        amount_diff = abs(vima.amount - payshack.amount)
        tolerance = max(
            self.AMOUNT_TOLERANCE,
            vima.amount * self.AMOUNT_TOLERANCE_PERCENT,
        )
        
        if amount_diff > tolerance:
            discrepancies.append("amount")

        # Compare status
        if vima.status != payshack.status:
            discrepancies.append("status")

        if discrepancies:
            return ReconciliationResult(
                recon_run_id=run_id,
                recon_date=recon_date,
                vima_txn_id=vima.id,
                payshack_txn_id=payshack.id,
                client_operation_id=vima.client_operation_id,
                match_status="discrepancy",
                discrepancy_type=discrepancies[0],  # Primary discrepancy
                vima_amount=vima.amount,
                payshack_amount=payshack.amount,
                amount_diff=amount_diff if "amount" in discrepancies else None,
                vima_status=vima.status,
                payshack_status=payshack.status,
                details={"discrepancies": discrepancies},
            )
        else:
            return ReconciliationResult(
                recon_run_id=run_id,
                recon_date=recon_date,
                vima_txn_id=vima.id,
                payshack_txn_id=payshack.id,
                client_operation_id=vima.client_operation_id,
                match_status="matched",
                vima_amount=vima.amount,
                payshack_amount=payshack.amount,
                vima_status=vima.status,
                payshack_status=payshack.status,
            )


# Helper function for API routes
async def run_reconciliation_for_date(recon_date: date):
    """Run reconciliation (for background task)."""
    service = ReconciliationService()
    return await service.run_for_date(recon_date)
