"""PayShack API Client.

API returns data in plain JSON format (no encryption required).
Authentication uses JWT token + reseller-id header.
"""

from datetime import datetime, timezone
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


class PayShackAPIError(Exception):
    """PayShack API error."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class PayShackClient:
    """
    PayShack API Client.
    
    Base URL: https://api.payshack.in
    
    Authentication:
    1. POST /indigate-user-svc/api/v1/auth/login → получаем token и clientId
    2. Для запросов используем:
       - Authorization: Bearer {token}
       - reseller-id: {clientId}
    
    Endpoints:
    - Pay-In: GET /indigate-payin-svc/api/v1/payin/transaction/fetch
    - Pay-Out: GET /indigate-payout-svc/api/v1/wallet/transactions
    """

    def __init__(
        self,
        email: str = None,
        password: str = None,
        base_url: str = None,
        timeout: float = 30.0,
    ):
        self.email = email or settings.payshack_email
        self.password = password or settings.payshack_password
        self.base_url = base_url or settings.payshack_api_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        
        # Auth state
        self._token: Optional[str] = None
        self._client_id: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

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

    async def _ensure_auth(self):
        """Ensure we have a valid auth token."""
        if not self._token or self._is_token_expired():
            await self.login()

    def _is_token_expired(self) -> bool:
        """Check if token is expired (with 5 min buffer)."""
        if not self._token_expires_at:
            return True
        from datetime import timedelta
        return datetime.now(timezone.utc) >= (self._token_expires_at - timedelta(minutes=5))

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            "Authorization": f"Bearer {self._token}",
            "reseller-id": self._client_id,
            "Accept": "*/*",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def login(self) -> Dict[str, Any]:
        """
        Login to PayShack API.
        
        Returns:
            Auth data with token and clientId
        """
        url = f"{self.base_url}/indigate-user-svc/api/v1/auth/login"
        
        logger.debug("payshack_login_attempt", email=self.email)
        
        try:
            response = await self.client.post(
                url,
                json={
                    "email": self.email,
                    "password": self.password,
                },
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                raise PayShackAPIError(
                    f"Login failed: {data.get('message', 'Unknown error')}",
                    response=data,
                )
            
            auth_data = data.get("data", {})
            self._token = auth_data.get("token")
            self._client_id = auth_data.get("clientId")
            self._refresh_token = auth_data.get("refreshToken")
            
            # Set token expiry (30 min from now)
            from datetime import timedelta
            self._token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
            
            logger.info(
                "payshack_login_success",
                client_id=self._client_id,
                role=auth_data.get("role"),
            )
            
            return auth_data
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "payshack_login_http_error",
                status_code=e.response.status_code,
                response=e.response.text[:500],
            )
            raise PayShackAPIError(
                f"Login HTTP error: {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error("payshack_login_request_error", error=str(e))
            raise PayShackAPIError(f"Login request failed: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def get_payin_transactions(
        self,
        page: int = 1,
        limit: int = 100,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        order_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch Pay-In (deposit) transactions.
        
        Args:
            page: Page number (1-based)
            limit: Records per page (max 100)
            status: Filter by status (Success, Failed, Initiated, etc.)
            date_from: Start date filter
            date_to: End date filter
            order_id: Filter by order ID
            transaction_id: Filter by transaction ID
            
        Returns:
            Dict with transactions list and pagination info
        """
        await self._ensure_auth()
        
        url = f"{self.base_url}/indigate-payin-svc/api/v1/payin/transaction/fetch"
        
        params = {
            "page": page,
            "limit": min(limit, 100),
        }
        
        if status:
            params["status"] = status
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        if order_id:
            params["orderId"] = order_id
        if transaction_id:
            params["transactionId"] = transaction_id
        
        logger.debug(
            "payshack_payin_request",
            page=page,
            limit=limit,
            status=status,
        )
        
        try:
            response = await self.client.get(
                url,
                params=params,
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                raise PayShackAPIError(
                    f"Fetch pay-in failed: {data.get('message', 'Unknown error')}",
                    response=data,
                )
            
            result = data.get("data", {})
            transactions = result.get("transactions", [])
            
            logger.info(
                "payshack_payin_response",
                count=len(transactions),
                page=page,
                total_pages=result.get("totalPages"),
                total_records=result.get("totalRecords"),
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            # Check if auth error - re-login and retry
            if e.response.status_code in (401, 403):
                logger.warning("payshack_auth_expired, re-login")
                self._token = None
                await self._ensure_auth()
                return await self.get_payin_transactions(
                    page=page, limit=limit, status=status,
                    date_from=date_from, date_to=date_to,
                    order_id=order_id, transaction_id=transaction_id,
                )
            
            logger.error(
                "payshack_payin_http_error",
                status_code=e.response.status_code,
                response=e.response.text[:500],
            )
            raise PayShackAPIError(
                f"Pay-In HTTP error: {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error("payshack_payin_request_error", error=str(e))
            raise PayShackAPIError(f"Pay-In request failed: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def get_payout_transactions(
        self,
        page: int = 1,
        limit: int = 100,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch Pay-Out (withdrawal) transactions.
        
        Args:
            page: Page number (1-based)
            limit: Records per page (max 100)
            status: Filter by status (SUCCESS, FAILED)
            date_from: Start date filter
            date_to: End date filter
            
        Returns:
            Dict with transactions list and pagination info
        """
        await self._ensure_auth()
        
        url = f"{self.base_url}/indigate-payout-svc/api/v1/wallet/transactions"
        
        params = {
            "page": page,
            "limit": min(limit, 100),
        }
        
        if status:
            params["status"] = status
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        
        logger.debug(
            "payshack_payout_request",
            page=page,
            limit=limit,
            status=status,
        )
        
        try:
            response = await self.client.get(
                url,
                params=params,
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                raise PayShackAPIError(
                    f"Fetch payout failed: {data.get('message', 'Unknown error')}",
                    response=data,
                )
            
            result = data.get("data", {})
            transactions = result.get("transactions", [])
            
            logger.info(
                "payshack_payout_response",
                count=len(transactions),
                page=page,
                total_pages=result.get("totalPages"),
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                logger.warning("payshack_auth_expired, re-login")
                self._token = None
                await self._ensure_auth()
                return await self.get_payout_transactions(
                    page=page, limit=limit, status=status,
                    date_from=date_from, date_to=date_to,
                )
            
            logger.error(
                "payshack_payout_http_error",
                status_code=e.response.status_code,
                response=e.response.text[:500],
            )
            raise PayShackAPIError(
                f"Payout HTTP error: {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error("payshack_payout_request_error", error=str(e))
            raise PayShackAPIError(f"Payout request failed: {e}")

    async def get_all_payin_transactions(
        self,
        start_page: int = 1,
        max_pages: int = 100,
        **filters,
    ):
        """
        Iterate through all Pay-In transactions with pagination.
        
        Yields batches of transactions.
        """
        page = start_page
        
        while page <= max_pages:
            result = await self.get_payin_transactions(page=page, **filters)
            
            transactions = result.get("transactions", [])
            if not transactions:
                break
            
            yield transactions
            
            total_pages = result.get("totalPages", 1)
            if page >= total_pages:
                break
            
            page += 1
            
            # Small delay to avoid rate limiting
            import asyncio
            await asyncio.sleep(0.3)

    async def get_all_payout_transactions(
        self,
        start_page: int = 1,
        max_pages: int = 100,
        **filters,
    ):
        """
        Iterate through all Pay-Out transactions with pagination.
        
        Yields batches of transactions.
        """
        page = start_page
        
        while page <= max_pages:
            result = await self.get_payout_transactions(page=page, **filters)
            
            transactions = result.get("transactions", [])
            if not transactions:
                break
            
            yield transactions
            
            total_pages = result.get("totalPages", 1)
            if page >= total_pages:
                break
            
            page += 1
            
            import asyncio
            await asyncio.sleep(0.3)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def get_clients(self) -> List[Dict[str, Any]]:
        """
        Fetch all clients/merchants.
        
        Returns:
            List of client objects with name, id, balance, etc.
        """
        await self._ensure_auth()
        
        url = f"{self.base_url}/indigate-core-svc/api/v1/client/fetch-all-client"
        
        logger.debug("payshack_get_clients_request")
        
        try:
            response = await self.client.get(
                url,
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                raise PayShackAPIError(
                    f"Fetch clients failed: {data.get('message', 'Unknown error')}",
                    response=data,
                )
            
            clients = data.get("data", [])
            
            logger.info(
                "payshack_get_clients_response",
                count=len(clients) if isinstance(clients, list) else 0,
            )
            
            return clients if isinstance(clients, list) else []
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                logger.warning("payshack_auth_expired, re-login")
                self._token = None
                await self._ensure_auth()
                return await self.get_clients()
            
            logger.error(
                "payshack_get_clients_error",
                status_code=e.response.status_code,
                response=e.response.text[:500],
            )
            raise PayShackAPIError(
                f"Get clients HTTP error: {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error("payshack_get_clients_request_error", error=str(e))
            raise PayShackAPIError(f"Get clients request failed: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def get_resellers(self) -> List[Dict[str, Any]]:
        """
        Fetch all resellers.
        
        Returns:
            List of reseller objects
        """
        await self._ensure_auth()
        
        url = f"{self.base_url}/indigate-core-svc/api/v1/reseller/fetch-all-reseller"
        
        logger.debug("payshack_get_resellers_request")
        
        try:
            response = await self.client.get(
                url,
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                raise PayShackAPIError(
                    f"Fetch resellers failed: {data.get('message', 'Unknown error')}",
                    response=data,
                )
            
            resellers = data.get("data", [])
            
            logger.info(
                "payshack_get_resellers_response",
                count=len(resellers) if isinstance(resellers, list) else 0,
            )
            
            return resellers if isinstance(resellers, list) else []
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                self._token = None
                await self._ensure_auth()
                return await self.get_resellers()
            
            logger.error(
                "payshack_get_resellers_error",
                status_code=e.response.status_code,
            )
            raise PayShackAPIError(
                f"Get resellers HTTP error: {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error("payshack_get_resellers_request_error", error=str(e))
            raise PayShackAPIError(f"Get resellers request failed: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def get_service_providers(self) -> List[Dict[str, Any]]:
        """
        Fetch all service providers.
        
        Returns:
            List of service provider objects
        """
        await self._ensure_auth()
        
        url = f"{self.base_url}/indigate-core-svc/api/v1/service-provider/fetch-all-sp"
        
        logger.debug("payshack_get_service_providers_request")
        
        try:
            response = await self.client.get(
                url,
                headers=self._get_auth_headers(),
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data.get("success"):
                raise PayShackAPIError(
                    f"Fetch service providers failed: {data.get('message', 'Unknown error')}",
                    response=data,
                )
            
            providers = data.get("data", [])
            
            logger.info(
                "payshack_get_service_providers_response",
                count=len(providers) if isinstance(providers, list) else 0,
            )
            
            return providers if isinstance(providers, list) else []
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                self._token = None
                await self._ensure_auth()
                return await self.get_service_providers()
            
            logger.error(
                "payshack_get_service_providers_error",
                status_code=e.response.status_code,
            )
            raise PayShackAPIError(
                f"Get service providers HTTP error: {e.response.status_code}",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            logger.error("payshack_get_service_providers_request_error", error=str(e))
            raise PayShackAPIError(f"Get service providers request failed: {e}")

    async def get_balance(self) -> Dict[str, Any]:
        """
        Get current balance information.
        
        Note: Balance info may be included in reseller/client data.
        This is a placeholder that aggregates balance from clients.
        
        Returns:
            Balance summary
        """
        await self._ensure_auth()
        
        # Get balance from clients data
        clients = await self.get_clients()
        
        total_balance = 0
        balances_by_client = []
        
        for client in clients:
            client_id = client.get("clientId") or client.get("id")
            client_name = client.get("name") or client.get("companyName") or "Unknown"
            balance = client.get("balance") or client.get("walletBalance") or 0
            
            balances_by_client.append({
                "client_id": client_id,
                "client_name": client_name,
                "balance": float(balance),
            })
            total_balance += float(balance)
        
        return {
            "total_balance": total_balance,
            "currency": "INR",
            "clients": balances_by_client,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def generate_report(
        self,
        report_type: str,
        date_from: str,
        date_to: str,
        start_time: str = "00:00",
        end_time: str = "23:59",
    ) -> bytes:
        """
        Generate and download a report.
        
        Note: This may require a specific endpoint that triggers report generation.
        Based on the dashboard, reports are generated for 7-day periods.
        
        Args:
            report_type: Type of report (payin, payout)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            start_time: Start time (HH:MM)
            end_time: End time (HH:MM)
            
        Returns:
            Report data as bytes (CSV/Excel)
        """
        await self._ensure_auth()
        
        # The exact endpoint for report generation needs to be discovered
        # This is a placeholder implementation that fetches all data and generates CSV
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        if report_type == "payin":
            # Fetch all payin transactions for the date range
            writer.writerow([
                "Transaction ID", "Order ID", "Amount", "Paid Amount", 
                "Status", "Client", "UTR", "Created At", "Modified At"
            ])
            
            async for batch in self.get_all_payin_transactions(
                date_from=date_from,
                date_to=date_to,
                max_pages=1000,
            ):
                for tx in batch:
                    writer.writerow([
                        tx.get("txnId", ""),
                        tx.get("orderId", ""),
                        tx.get("amount", 0),
                        tx.get("paidAmount", 0),
                        tx.get("txnStatus", ""),
                        tx.get("clientName", ""),
                        tx.get("utr", ""),
                        tx.get("createdAt", ""),
                        tx.get("modifiedAt", ""),
                    ])
        
        elif report_type == "payout":
            writer.writerow([
                "Transaction ID", "Order ID", "Amount", "Status",
                "Beneficiary Name", "Account", "Created At", "Modified At"
            ])
            
            async for batch in self.get_all_payout_transactions(
                date_from=date_from,
                date_to=date_to,
                max_pages=1000,
            ):
                for tx in batch:
                    writer.writerow([
                        tx.get("txnId", ""),
                        tx.get("orderId", ""),
                        tx.get("amount", 0),
                        tx.get("status", ""),
                        tx.get("beneName", ""),
                        tx.get("beneAccount", ""),
                        tx.get("createdAt", ""),
                        tx.get("modifiedAt", ""),
                    ])
        
        logger.info(
            "payshack_report_generated",
            report_type=report_type,
            date_from=date_from,
            date_to=date_to,
        )
        
        return output.getvalue().encode("utf-8")


# Singleton instance
payshack_client = PayShackClient()
