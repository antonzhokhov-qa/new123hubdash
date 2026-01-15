"""Tests for Vima API client."""

import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal

from app.integrations.vima.client import VimaClient, VimaAPIError
from app.integrations.vima.normalizer import VimaNormalizer


class TestVimaClient:
    """Tests for VimaClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test client initialization."""
        client = VimaClient(api_key="test-key")
        assert client.api_key == "test-key"
        await client.close()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_get_operations_success(self, mock_get):
        """Test successful API call."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "operation_id": "123",
                "reference_id": "ref-123",
                "complete_amount": 100.00,
                "complete_currency": "INR",
                "current_status": "success",
            }
        ]
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response

        client = VimaClient(api_key="test-key")
        result = await client.get_operations(count=10)
        
        assert len(result) == 1
        assert result[0]["operation_id"] == "123"
        await client.close()


class TestVimaNormalizer:
    """Tests for VimaNormalizer."""

    def test_normalize_basic(self):
        """Test basic normalization."""
        raw = {
            "operation_id": "123",
            "reference_id": "ref-123",
            "client_operation_id": "c-123",
            "project": "91game",
            "complete_amount": 100.00,
            "complete_currency": "INR",
            "current_status": "success",
            "operation_created_at": "2026-01-15T10:00:00Z",
        }

        result = VimaNormalizer.normalize(raw)

        assert result["source"] == "vima"
        assert result["source_id"] == "123"
        assert result["client_operation_id"] == "c-123"
        assert result["amount"] == Decimal("100.00")
        assert result["status"] == "success"

    def test_normalize_status_mapping(self):
        """Test status normalization."""
        test_cases = [
            ("success", "success"),
            ("fail", "failed"),
            ("in_process", "pending"),
            ("user_input_required", "pending"),
        ]

        for original, expected in test_cases:
            raw = {
                "operation_id": "123",
                "complete_amount": 100,
                "current_status": original,
                "operation_created_at": "2026-01-15T10:00:00Z",
            }
            result = VimaNormalizer.normalize(raw)
            assert result["status"] == expected, f"Expected {expected} for {original}"

    def test_normalize_with_nested_data(self):
        """Test normalization with nested payer data."""
        raw = {
            "operation_id": "123",
            "complete_amount": 100.00,
            "complete_currency": "INR",
            "current_status": "success",
            "operation_created_at": "2026-01-15T10:00:00Z",
            "create_params": {
                "params": {
                    "payment": {
                        "payer": {
                            "email": "test@example.com",
                            "phone": "1234567890",
                            "person": {
                                "first_name": "Test",
                                "last_name": "User",
                            }
                        },
                        "client": {
                            "country": "IN",
                        }
                    }
                }
            }
        }

        result = VimaNormalizer.normalize(raw)

        assert result["user_email"] == "test@example.com"
        assert result["user_phone"] == "1234567890"
        assert result["user_name"] == "Test User"
        assert result["country"] == "IN"

    def test_data_hash_generation(self):
        """Test that data hash is generated."""
        raw = {
            "operation_id": "123",
            "complete_amount": 100,
            "complete_currency": "INR",
            "current_status": "success",
            "operation_created_at": "2026-01-15T10:00:00Z",
        }

        result = VimaNormalizer.normalize(raw)

        assert "data_hash" in result
        assert len(result["data_hash"]) == 64

    def test_data_hash_consistency(self):
        """Test that same data produces same hash."""
        raw = {
            "operation_id": "123",
            "complete_amount": 100,
            "complete_currency": "INR",
            "current_status": "success",
            "operation_created_at": "2026-01-15T10:00:00Z",
        }

        result1 = VimaNormalizer.normalize(raw)
        result2 = VimaNormalizer.normalize(raw)

        assert result1["data_hash"] == result2["data_hash"]
