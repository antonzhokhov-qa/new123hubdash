# Vima/Finmar Collector API Documentation

## Overview

Vima Collector API - это REST API для получения данных о платежных операциях. API поддерживает фильтрацию, пагинацию и инкрементальную загрузку через cursor-based подход.

---

## Endpoints

### Production
```
https://payment.woozuki.com/collector1/api/v1/operation
```

### Sandbox
```
https://sandbox.finmar.tech/collector/api/v3/operation
```

---

## Authentication

### Option 1: API Key (Query Parameter)
```
?apikey=master-3E193252DE4A4B4C80862F67B2972D3D
```

### Option 2: Basic Auth (Header)
```
Authorization: Basic <base64(username:password)>
```

---

## Request Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `apikey` | string | Yes* | API ключ авторизации | `master-XXXXX` |
| `project` | string | No | ID проекта для фильтрации | `monetix`, `caroussel`, `91game` |
| `status` | enum | No | Статус операции | `success`, `fail`, `in_process`, `user_input_required` |
| `date` | date | No | Конкретная дата (YYYY-MM-DD) | `2026-01-15` |
| `from` | date | No | Начало периода | `2026-01-01` |
| `to` | date | No | Конец периода | `2026-01-15` |
| `count` | int | No | Лимит записей (max 100) | `100` |
| `descending` | bool | No | Сортировка (true = новые первыми) | `true` |
| `from_operation_create_id` | string | No | Cursor для инкрементальной загрузки новых | `1067251098160838656` |
| `from_operation_update_id` | string | No | Cursor для отслеживания обновлений | `1067251098160838656` |

---

## Example Requests

### 1. Последние 100 успешных операций проекта monetix
```bash
GET https://payment.woozuki.com/collector1/api/v1/operation?apikey=master-3E193252DE4A4B4C80862F67B2972D3D&descending=true&project=monetix&status=success&count=100
```

### 2. Все успешные операции за конкретную дату
```bash
GET https://payment.woozuki.com/collector1/api/v1/operation?apikey=master-3E193252DE4A4B4C80862F67B2972D3D&descending=false&project=monetix&status=success&date=2026-01-15
```

### 3. Операции за диапазон дат
```bash
GET https://payment.woozuki.com/collector1/api/v1/operation?apikey=master-3E193252DE4A4B4C80862F67B2972D3D&descending=false&project=caroussel&from=2026-01-01&to=2026-01-15&status=success
```

### 4. Инкрементальная загрузка (новые транзакции после cursor)
```bash
GET https://payment.woozuki.com/collector1/api/v1/operation?apikey=master-3E193252DE4A4B4C80862F67B2972D3D&from_operation_create_id=1067251098160838656&count=100&descending=false
```

---

## Response Format

### Single Transaction Object
```json
{
  "operation_id": "1067250921664811008",
  "reference_id": "019bc256159f72f3b2c27506937517be",
  "client_operation_id": "1768491979464",
  "service": "multihub-api",
  "service_env": "prod-123hub",
  "project": "91game",
  "project_env": "prod",
  "user_id": "16faca55460b41c3a9b46a736c8dbfed",
  "contact": "sumit74360zne@gmail.com",
  "ip_addr": "",
  "create_params": {
    "method": "payment.in",
    "params": {
      "payment": {
        "payer": {
          "email": "sumit74360zne@gmail.com",
          "phone": "9768493341",
          "person": {
            "last_name": "Bhatt",
            "first_name": "Sumit"
          },
          "customer_account": {
            "id": "16faca55460b41c3a9b46a736c8dbfed"
          }
        },
        "amount": {
          "value": 10000,
          "currency": "INR"
        },
        "client": {
          "country": "IN",
          "language": "EN"
        },
        "identifiers": {
          "c_id": 1768491979464
        }
      }
    },
    "service_id": 14701
  },
  "current_status": "success",
  "payment_product": "multihub-api",
  "payment_method_type": "fiat",
  "payment_method_code": "apm",
  "operation_state": "in_process",
  "credentials_owner": "123hub",
  "integration_type": "direct",
  "operation_created_at": "2026-01-15T15:46:20.195Z",
  "operation_modified_at": "2026-01-15T15:46:46.487Z",
  "card_start": [
    {
      "oper_type": "deposit",
      "action_id": "1067250921664811008",
      "payment_id": "1067250921664811008",
      "payment_gate": "paymentgate",
      "user_ref": "16faca55460b41c3a9b46a736c8dbfed",
      "kyc_verification": 0,
      "currency": "INR",
      "amount": 100.00000000,
      "created_at": "2026-01-15 15:46:20.195000",
      "modified_at": "2026-01-15 15:46:22.068000"
    }
  ],
  "card_finish": [
    {
      "action_id": "1067250921664811008",
      "payment_id": "1067250921664811008",
      "currency": "INR",
      "amount": 100.00000000,
      "charged_currency": "INR",
      "charged_amount": 100.00000000,
      "charged_fee": 0.00000000,
      "result": "success",
      "created_at": "2026-01-15 15:46:43.817000",
      "modified_at": "2026-01-15 15:46:46.458000"
    }
  ],
  "complete_amount": 100.00000000,
  "complete_currency": "INR",
  "complete_created_at": "2026-01-15T15:46:43.817Z",
  "complete_modified_at": "2026-01-15T15:46:46.487Z",
  "operation_create_id": "1067250934146775040",
  "operation_update_id": "1067251098160838656",
  "payment_custom_data": {
    "name": "apm"
  }
}
```

---

## Key Fields Reference

### Identifiers
| Field | Description | Use Case |
|-------|-------------|----------|
| `operation_id` | Internal operation ID | Primary key |
| `reference_id` | UUID reference | External reference |
| `client_operation_id` | Client-provided ID (c_id) | **Matching key with PayShack** |

### Business Data
| Field | Description |
|-------|-------------|
| `project` | Project identifier (monetix, caroussel, 91game) |
| `current_status` | Current operation status |
| `payment_status` | Final payment status (use for reconciliation) |
| `complete_amount` | Final transaction amount |
| `complete_currency` | Transaction currency |

### Timestamps
| Field | Description |
|-------|-------------|
| `operation_created_at` | When operation was created (ISO 8601) |
| `operation_modified_at` | Last modification time (ISO 8601) |
| `complete_created_at` | When payment was completed |

### Cursors (for incremental loading)
| Field | Description |
|-------|-------------|
| `operation_create_id` | Cursor for new operations |
| `operation_update_id` | Cursor for updated operations |

### Payer Information (nested in create_params)
```
create_params.params.payment.payer.email
create_params.params.payment.payer.phone
create_params.params.payment.payer.person.first_name
create_params.params.payment.payer.person.last_name
create_params.params.payment.amount.value (in minor units, divide by 100)
create_params.params.payment.amount.currency
create_params.params.payment.client.country
create_params.params.payment.identifiers.c_id
```

---

## Status Values

| Status | Description |
|--------|-------------|
| `success` | Payment completed successfully |
| `fail` | Payment failed |
| `in_process` | Payment is being processed |
| `user_input_required` | Waiting for user action |

---

## Incremental Loading Strategy

### For New Transactions
1. Store last `operation_create_id` in sync_state table
2. Request with `from_operation_create_id=<last_cursor>&descending=false`
3. Process all returned transactions
4. Update cursor to last `operation_create_id` from response

### For Updated Transactions
1. Store last `operation_update_id` in sync_state table
2. Request with `from_operation_update_id=<last_cursor>&descending=false`
3. Upsert returned transactions (they may already exist)
4. Update cursor to last `operation_update_id` from response

### Recommended Sync Interval
- Every **5 minutes** for near real-time data
- Configurable based on traffic volume

---

## Python Client Example

```python
import httpx
from typing import Optional, List, Dict, Any
from datetime import date

class VimaClient:
    """Vima Collector API Client"""
    
    BASE_URL = "https://payment.woozuki.com/collector1/api/v1/operation"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
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
        Fetch operations from Vima API
        """
        params = {
            "apikey": self.api_key,
            "count": count,
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
        
        response = await self.client.get(self.BASE_URL, params=params)
        response.raise_for_status()
        
        return response.json()
    
    async def close(self):
        await self.client.aclose()


# Usage example
async def main():
    client = VimaClient(api_key="master-3E193252DE4A4B4C80862F67B2972D3D")
    
    # Get latest 100 successful transactions
    transactions = await client.get_operations(
        status="success",
        count=100,
        descending=True
    )
    
    for txn in transactions:
        print(f"{txn['operation_id']}: {txn['complete_amount']} {txn['complete_currency']}")
    
    await client.close()
```

---

## Rate Limits & Best Practices

1. **Batch size**: Use `count=100` for optimal performance
2. **Polling interval**: 5 minutes recommended
3. **Use cursors**: Always use `from_operation_create_id` for incremental sync
4. **Error handling**: Implement exponential backoff for retries
5. **Deduplication**: Use `operation_id` as unique key to prevent duplicates

---

## Projects Reference

| Project ID | Description |
|------------|-------------|
| `monetix` | Monetix payments |
| `caroussel` | Caroussel payments |
| `91game` | 91Game payments (India, works with PayShack) |

---

## Notes

- All timestamps are in **UTC** (ISO 8601 format)
- Amount in `create_params.params.payment.amount.value` is in **minor units** (divide by 100)
- Amount in `complete_amount` is already in **major units** (no conversion needed)
- `client_operation_id` (c_id) is the **matching key** for reconciliation with PayShack
