"""Vima Collector API Client."""

from datetime import date
from typing import Optional, List, Dict, Any

import httpx
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import settings

logger = structlog.get_logger()


class VimaAPIError(Exception):
    """Vima API error."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class VimaClient:
    """
    Vima Collector API Client.
    
    Endpoints:
    - Production: https://payment.woozuki.com/collector1/api/v1/operation
    - Sandbox: https://sandbox.finmar.tech/collector/api/v3/operation
    
    Authentication: API Key via query parameter
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or settings.vima_api_key
        self.base_url = base_url or settings.vima_base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def get_operations(
        self,
        project: Optional[str] = None,
        status: Optional[str] = None,
        date_filter: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        count: int = 100,
        descending: bool = False,
        from_operation_create_id: Optional[str] = None,
        from_operation_update_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch operations from Vima API.
        
        Args:
            project: Filter by project (monetix, caroussel, 91game)
            status: Filter by status (success, fail, in_process, user_input_required)
            date_filter: Specific date
            from_date: Start of date range
            to_date: End of date range
            count: Number of records (max 100)
            descending: Sort order (True = newest first)
            from_operation_create_id: Cursor for incremental loading
            from_operation_update_id: Cursor for updates
            
        Returns:
            List of operation dictionaries
        """
        params = {
            "apikey": self.api_key,
            "count": min(count, 100),
            "descending": str(descending).lower(),
        }

        if project:
            params["project"] = project
        if status:
            params["status"] = status
        if date_filter:
            params["date"] = date_filter.isoformat()
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        if from_operation_create_id:
            params["from_operation_create_id"] = from_operation_create_id
        if from_operation_update_id:
            params["from_operation_update_id"] = from_operation_update_id

        url = f"{self.base_url}/operation"
        
        logger.debug(
            "vima_request",
            url=url,
            project=project,
            status=status,
            cursor=from_operation_create_id,
        )

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # API returns list directly
            if isinstance(data, list):
                logger.info(
                    "vima_response",
                    count=len(data),
                    cursor=from_operation_create_id,
                )
                return data
            
            # Or might return wrapped response
            if isinstance(data, dict) and "operations" in data:
                return data["operations"]
            
            return data if isinstance(data, list) else []

        except httpx.HTTPStatusError as e:
            logger.error(
                "vima_http_error",
                status_code=e.response.status_code,
                response=e.response.text[:500],
            )
            raise VimaAPIError(
                f"Vima API error: {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error("vima_request_error", error=str(e))
            raise VimaAPIError(f"Vima request failed: {e}")

    async def get_all_operations(
        self,
        from_operation_create_id: Optional[str] = None,
        batch_size: int = 100,
        max_batches: int = 100,
        **filters,
    ):
        """
        Iterate through all operations using cursor pagination.
        
        Yields batches of operations.
        """
        cursor = from_operation_create_id
        batch_count = 0

        while batch_count < max_batches:
            operations = await self.get_operations(
                from_operation_create_id=cursor,
                count=batch_size,
                descending=False,  # Oldest first for cursor-based loading
                **filters,
            )

            if not operations:
                break

            yield operations

            # Update cursor to last operation's create_id
            last_op = operations[-1]
            new_cursor = last_op.get("operation_create_id")
            
            if not new_cursor or new_cursor == cursor:
                break
            
            cursor = new_cursor
            batch_count += 1

            # Small delay to avoid rate limiting
            import asyncio
            await asyncio.sleep(0.5)


# Singleton instance
vima_client = VimaClient()
