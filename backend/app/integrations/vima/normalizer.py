"""Vima data normalizer."""

import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from dateutil import parser as date_parser

import structlog

logger = structlog.get_logger()


class VimaNormalizer:
    """
    Normalize Vima API responses to unified Transaction format.
    
    Key mappings:
    - operation_id -> source_id
    - client_operation_id -> client_operation_id (matching key!)
    - complete_amount -> amount
    - current_status/payment_status -> status (normalized)
    """

    # Status mapping: Vima -> unified
    STATUS_MAP = {
        "success": "success",
        "fail": "failed",
        "failed": "failed",
        "in_process": "pending",
        "in process": "pending",
        "user_input_required": "pending",
        "pending": "pending",
    }

    @classmethod
    def normalize(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize single Vima operation to unified format.
        
        Returns dict ready for Transaction model.
        """
        try:
            # Extract nested payer info
            create_params = raw.get("create_params", {})
            params = create_params.get("params", {})
            payment = params.get("payment", {})
            payer = payment.get("payer", {})
            person = payer.get("person", {})
            amount_data = payment.get("amount", {})
            client_data = payment.get("client", {})
            identifiers = payment.get("identifiers", {})

            # Get amount - prefer complete_amount, fallback to create_params
            amount = raw.get("complete_amount")
            if amount is None:
                # Amount in create_params is in minor units (cents)
                amount_value = amount_data.get("value", 0)
                amount = Decimal(str(amount_value)) / 100
            else:
                amount = Decimal(str(amount))

            # Get currency
            currency = raw.get("complete_currency") or amount_data.get("currency", "INR")

            # Normalize status
            original_status = raw.get("payment_status") or raw.get("current_status", "")
            status = cls.STATUS_MAP.get(
                original_status.lower() if original_status else "",
                "pending"
            )

            # Parse timestamps
            created_at = cls._parse_datetime(raw.get("operation_created_at"))
            updated_at = cls._parse_datetime(raw.get("operation_modified_at"))
            completed_at = cls._parse_datetime(raw.get("complete_created_at"))

            # Build user name
            first_name = person.get("first_name", "")
            last_name = person.get("last_name", "")
            user_name = f"{first_name} {last_name}".strip() or None

            # Get client_operation_id from multiple sources
            client_op_id = (
                raw.get("client_operation_id") or
                str(identifiers.get("c_id", "")) or
                None
            )

            normalized = {
                "source": "vima",
                "source_id": raw.get("operation_id", ""),
                "reference_id": raw.get("reference_id"),
                "client_operation_id": client_op_id,
                "order_id": None,  # PayShack specific
                "project": raw.get("project"),
                "merchant_id": raw.get("credentials_owner"),
                "amount": amount,
                "currency": currency,
                "fee": cls._extract_fee(raw),
                "status": status,
                "original_status": original_status,
                "user_id": raw.get("user_id") or payer.get("customer_account", {}).get("id"),
                "user_email": payer.get("email") or raw.get("contact"),
                "user_phone": payer.get("phone"),
                "user_name": user_name,
                "country": client_data.get("country"),
                "utr": None,  # PayShack specific
                "payment_method": raw.get("payment_method_code"),
                "payment_product": raw.get("payment_product"),
                "created_at": created_at,
                "updated_at": updated_at,
                "completed_at": completed_at,
                "source_create_cursor": raw.get("operation_create_id"),
                "source_update_cursor": raw.get("operation_update_id"),
                "raw_data": raw,
            }

            # Calculate data hash for deduplication
            normalized["data_hash"] = cls._calculate_hash(normalized)

            return normalized

        except Exception as e:
            logger.error(
                "vima_normalize_error",
                error=str(e),
                operation_id=raw.get("operation_id"),
            )
            raise

    @classmethod
    def _parse_datetime(cls, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if not value:
            return None
        
        if isinstance(value, datetime):
            return value
        
        try:
            return date_parser.parse(str(value))
        except Exception:
            return None

    @classmethod
    def _extract_fee(cls, raw: Dict[str, Any]) -> Optional[Decimal]:
        """Extract fee from card_finish if available."""
        card_finish = raw.get("card_finish", [])
        if card_finish and isinstance(card_finish, list) and len(card_finish) > 0:
            fee = card_finish[0].get("charged_fee")
            if fee is not None:
                return Decimal(str(fee))
        return None

    @classmethod
    def _calculate_hash(cls, normalized: Dict[str, Any]) -> str:
        """
        Calculate hash for deduplication.
        
        Uses source + source_id + amount + currency + created_at
        """
        hash_input = (
            f"{normalized['source']}|"
            f"{normalized['source_id']}|"
            f"{normalized['amount']}|"
            f"{normalized['currency']}|"
            f"{normalized['created_at'].isoformat() if normalized['created_at'] else ''}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()[:64]


# Singleton instance
normalizer = VimaNormalizer()
