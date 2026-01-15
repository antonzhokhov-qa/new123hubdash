"""PayShack data normalizer."""

import hashlib
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional

import structlog

from app.services.currency import currency_service

logger = structlog.get_logger()

# India Standard Time offset (UTC+5:30)
IST_OFFSET = timedelta(hours=5, minutes=30)

# Default INR to USD rate (fallback)
DEFAULT_INR_USD_RATE = 0.012


class PayShackNormalizer:
    """
    Normalize PayShack API responses to unified Transaction format.
    
    Key mappings:
    - txnId -> source_id
    - orderId -> client_operation_id (KEY FOR MATCHING with Vima!)
    - amount -> amount
    - txnStatus -> status (normalized)
    - clientName -> project
    """

    # Status mapping: PayShack -> unified
    STATUS_MAP = {
        "success": "success",
        "failed": "failed",
        "initiated": "pending",
        "pending": "pending",
        "in process": "processing",
        "in_process": "processing",
        "incomplete": "pending",
        "refunded": "refunded",
        "cb_refunded": "refunded",
        "tampered": "failed",
    }

    # Client name to project mapping
    CLIENT_PROJECT_MAP = {
        "91G_TECH_PVT_LTD": "91game",
        "91g_tech_pvt_ltd": "91game",
        "IG Indigate P_Out": "indigate_payout",
        "MNCL_M5_Pvt_Ltd": "mncl_m5",
        "Mn CL THREE_PVT_LTD": "mncl_three",
    }

    @classmethod
    def normalize_payin(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize single PayShack Pay-In transaction to unified format.
        
        Returns dict ready for Transaction model.
        """
        try:
            # Parse amount
            amount = Decimal(str(raw.get("amount", 0)))
            paid_amount = raw.get("paidAmount")
            if paid_amount is not None:
                paid_amount = Decimal(str(paid_amount))

            # Normalize status
            original_status = raw.get("txnStatus", "")
            status = cls.STATUS_MAP.get(
                original_status.lower() if original_status else "",
                "pending"
            )

            # Parse timestamps (PayShack uses ISO format, already in UTC)
            created_at = cls._parse_datetime(raw.get("createdAt"))
            updated_at = cls._parse_datetime(raw.get("modifiedAt"))

            # Map client name to project
            client_name = raw.get("clientName", "")
            project = cls.CLIENT_PROJECT_MAP.get(client_name, client_name)

            # Order ID is the key for matching with Vima client_operation_id
            order_id = raw.get("orderId")

            # Convert to USD using sync method (rate from static fallback)
            fee = cls._extract_fee(raw)
            inr_rate = currency_service.STATIC_RATES_TO_USD.get("INR", DEFAULT_INR_USD_RATE)
            amount_usd = currency_service.convert_sync(amount, "INR", inr_rate)
            fee_usd = currency_service.convert_sync(fee, "INR", inr_rate) if fee else None

            normalized = {
                "source": "payshack",
                "source_id": raw.get("txnId", ""),
                "reference_id": raw.get("spTxnId"),  # Service provider txn ID
                "client_operation_id": order_id,  # KEY FOR MATCHING!
                "order_id": order_id,
                "project": project,
                "merchant_id": raw.get("clientId"),
                "amount": amount,
                "currency": "INR",  # PayShack is India-only
                "amount_usd": amount_usd,
                "fee": fee,
                "fee_usd": fee_usd,
                "exchange_rate": Decimal(str(inr_rate)),
                "status": status,
                "original_status": original_status,
                "user_id": None,
                "user_email": None,
                "user_phone": None,
                "user_name": raw.get("payerVpa"),  # UPI VPA as identifier
                "country": "IN",
                "utr": raw.get("utr"),  # Unique Transaction Reference
                "payment_method": raw.get("transactionType", "UPI"),
                "payment_product": "payin",
                "created_at": created_at,
                "updated_at": updated_at,
                "completed_at": updated_at if status == "success" else None,
                "source_create_cursor": None,
                "source_update_cursor": None,
                "raw_data": raw,
            }

            # Calculate data hash for deduplication
            normalized["data_hash"] = cls._calculate_hash(normalized)

            return normalized

        except Exception as e:
            logger.error(
                "payshack_normalize_payin_error",
                error=str(e),
                txn_id=raw.get("txnId"),
            )
            raise

    @classmethod
    def normalize_payout(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize single PayShack Pay-Out transaction to unified format.
        
        Returns dict ready for Transaction model.
        """
        try:
            # Parse amount
            amount = Decimal(str(raw.get("amount", 0)))

            # Normalize status (Pay-Out uses uppercase: SUCCESS, FAILED)
            original_status = raw.get("txnStatus") or raw.get("status", "")
            status = cls.STATUS_MAP.get(
                original_status.lower() if original_status else "",
                "pending"
            )

            # Parse timestamps
            created_at = cls._parse_datetime(raw.get("createdAt"))
            updated_at = cls._parse_datetime(raw.get("modifiedAt"))

            # Map client name to project
            client_name = raw.get("clientName", "")
            project = cls.CLIENT_PROJECT_MAP.get(client_name, client_name)

            order_id = raw.get("orderId")

            # Convert to USD
            fee = cls._extract_fee(raw)
            inr_rate = currency_service.STATIC_RATES_TO_USD.get("INR", DEFAULT_INR_USD_RATE)
            amount_usd = currency_service.convert_sync(amount, "INR", inr_rate)
            fee_usd = currency_service.convert_sync(fee, "INR", inr_rate) if fee else None

            normalized = {
                "source": "payshack",
                "source_id": raw.get("txnId") or raw.get("transactionId", ""),
                "reference_id": None,
                "client_operation_id": order_id,
                "order_id": order_id,
                "project": project,
                "merchant_id": raw.get("clientId"),
                "amount": amount,
                "currency": "INR",
                "amount_usd": amount_usd,
                "fee": fee,
                "fee_usd": fee_usd,
                "exchange_rate": Decimal(str(inr_rate)),
                "status": status,
                "original_status": original_status,
                "user_id": None,
                "user_email": raw.get("beneEmail"),
                "user_phone": None,
                "user_name": raw.get("beneName"),
                "country": "IN",
                "utr": raw.get("utr"),
                "payment_method": "payout",
                "payment_product": "payout",
                "created_at": created_at,
                "updated_at": updated_at,
                "completed_at": updated_at if status == "success" else None,
                "source_create_cursor": None,
                "source_update_cursor": None,
                "raw_data": raw,
            }

            normalized["data_hash"] = cls._calculate_hash(normalized)

            return normalized

        except Exception as e:
            logger.error(
                "payshack_normalize_payout_error",
                error=str(e),
                txn_id=raw.get("txnId") or raw.get("transactionId"),
            )
            raise

    @classmethod
    def _parse_datetime(cls, value: Any) -> Optional[datetime]:
        """Parse datetime from PayShack format (ISO with timezone)."""
        if not value:
            return None

        if isinstance(value, datetime):
            return value

        try:
            from dateutil import parser as date_parser
            dt = date_parser.parse(str(value))
            
            # Ensure timezone aware
            if dt.tzinfo is None:
                # Assume UTC if no timezone
                dt = dt.replace(tzinfo=timezone.utc)
            
            return dt
        except Exception:
            return None

    @classmethod
    def _extract_fee(cls, raw: Dict[str, Any]) -> Optional[Decimal]:
        """Extract fee/commission from transaction."""
        commission = raw.get("totalCommissionAmount")
        if commission is not None:
            return Decimal(str(commission))
        return None

    @classmethod
    def _calculate_hash(cls, normalized: Dict[str, Any]) -> str:
        """
        Calculate hash for deduplication.
        
        Uses source + source_id + amount + currency + created_at
        """
        created_str = ""
        if normalized.get("created_at"):
            created_str = normalized["created_at"].isoformat()
        
        hash_input = (
            f"{normalized['source']}|"
            f"{normalized['source_id']}|"
            f"{normalized['amount']}|"
            f"{normalized['currency']}|"
            f"{created_str}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()[:64]


# Singleton instance
normalizer = PayShackNormalizer()
