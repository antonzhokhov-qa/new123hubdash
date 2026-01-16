# PayShack API Documentation

## Overview

PayShack - индийский платежный провайдер (UPI/IMPS). API возвращает данные в **открытом JSON формате** (без шифрования).

> **Важно:** Ранее документация указывала на шифрование CryptoJS. Это было некорректно - API возвращает чистый JSON.

---

## Статистика данных

| Метрика | Значение |
|---------|----------|
| **Total Pay-In Records** | ~140,000+ транзакций |
| **Total Pages** | ~14,000 страниц |
| **Records per Page** | max 100 |
| **Интервал синхронизации** | 5 минут |

---

## Base URL

```
https://api.payshack.in
```

## Dashboard URL

```
https://dashboard.payshack.in
```

---

## Authentication

### Credentials

```
Email: psrs1@gmail.com
Password: Payshacksub@123
```

### Login Endpoint

```http
POST /indigate-user-svc/api/v1/auth/login
Content-Type: application/json

{
  "email": "psrs1@gmail.com",
  "password": "Payshacksub@123"
}
```

### Response

```json
{
  "timestamp": "2026-01-15T17:21:01.437Z",
  "statusCode": 200,
  "status": "OK",
  "message": "Login Successfully!",
  "success": true,
  "data": {
    "userId": "01a863d8-38d8-4157-ab3a-ce2f8ec31fb5",
    "clientId": "d5aaa8f6-b825-4c62-9a44-f4608e8fc6b7",
    "role": "Reseller",
    "email": "psrs1@gmail.com",
    "secretKey": "c48b682d-c3c9-4205-9c9c-acc5cb2c251a",
    "token": "...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Using the Token

После логина используйте два заголовка для всех запросов:

```http
Authorization: Bearer {token}
reseller-id: {clientId}
```

> **Важно:** Используйте `clientId` (не `userId`!) для заголовка `reseller-id`.

### Token Lifetime

- **Access Token**: ~30 минут
- **Refresh Token**: длительный срок действия

---

## API Services Architecture

PayShack API разделен на несколько микросервисов:

| Service | Path | Description |
|---------|------|-------------|
| **User Service** | `/indigate-user-svc/` | Авторизация, управление пользователями |
| **Core Service** | `/indigate-core-svc/` | Клиенты, провайдеры, реселлеры, балансы |
| **Pay-In Service** | `/indigate-payin-svc/` | Входящие платежи (deposits) |
| **Pay-Out Service** | `/indigate-payout-svc/` | Исходящие платежи (withdrawals) |

---

## Core Service Endpoints

### Clients List

```http
GET /indigate-core-svc/api/v1/client/fetch-all-client
```

Возвращает список всех клиентов/мерчантов с балансами и настройками.

**Response Fields:**

| Field | Description |
|-------|-------------|
| `clientId` | UUID клиента |
| `name` / `companyName` | Название компании |
| `balance` / `walletBalance` | Текущий баланс |
| `status` | Статус клиента |
| `createdAt` | Дата создания |

### Resellers List

```http
GET /indigate-core-svc/api/v1/reseller/fetch-all-reseller
```

Возвращает список всех реселлеров.

### Service Providers List

```http
GET /indigate-core-svc/api/v1/service-provider/fetch-all-sp
```

Возвращает список всех сервис-провайдеров (банковские шлюзы).

---

## Transaction Endpoints

### Pay-In Transactions (Deposits)

```http
GET /indigate-payin-svc/api/v1/payin/transaction/fetch
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Номер страницы (начиная с 1) |
| `limit` | int | Количество записей на странице (max 100) |
| `status` | string | Фильтр по статусу |
| `dateFrom` | date | Начальная дата |
| `dateTo` | date | Конечная дата |
| `orderId` | string | Фильтр по Order ID |
| `transactionId` | string | Фильтр по Transaction ID |

**Response:**

```json
{
  "timestamp": "2026-01-15T17:26:00.209Z",
  "statusCode": 200,
  "status": "OK",
  "message": "Payin Transactions fetched successfully",
  "success": true,
  "data": {
    "transactions": [
      {
        "_id": 15910368,
        "txnId": "Y7KY0V202611591646",
        "spTxnId": "1003kqTJw77860115211719",
        "orderId": "AGQAMEBYUPHQ4",
        "amount": 100,
        "paidAmount": 100,
        "utr": "983991008838",
        "txnStatus": "Success",
        "clientName": "91G_TECH_PVT_LTD",
        "clientId": "5b12c121-06e7-4b53-a8fa-c5d5b56e33ec",
        "resellerId": "d5aaa8f6-b825-4c62-9a44-f4608e8fc6b7",
        "transactionType": "UPI_INTENT",
        "payerVpa": "9606143313-2@axl",
        "upiId": "hdml61iotatkl70194@hdfcbank",
        "createdAt": "2026-01-15T15:46:46.698Z",
        "modifiedAt": "2026-01-15T15:47:20.139Z"
      }
    ],
    "totalRecords": 140980,
    "perPage": 10,
    "totalPages": 14098,
    "currentPageNo": 1,
    "prevPage": 0,
    "nextPage": 2
  }
}
```

### Pay-Out Transactions (Withdrawals)

```http
GET /indigate-payout-svc/api/v1/wallet/transactions
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Номер страницы |
| `limit` | int | Количество записей |
| `status` | string | Фильтр по статусу (SUCCESS, FAILED) |
| `dateFrom` | date | Начальная дата |
| `dateTo` | date | Конечная дата |

---

## Pay-In Transaction Fields (Детальное описание)

### Идентификаторы

| Field | Description | Example | Mapping to DB |
|-------|-------------|---------|---------------|
| `_id` | Internal DB ID (auto increment) | `15910368` | - |
| `txnId` | PayShack transaction ID | `Y7KY0V202611591646` | `source_id` |
| `orderId` | **🔑 Client order ID (KEY для сверки!)** | `AGQAMEBYUPHQ4` | `client_operation_id` |
| `spTxnId` | Service provider txn ID | `1003kqTJw77860115211719` | `reference_id` |

### Финансовые данные

| Field | Description | Example | Type |
|-------|-------------|---------|------|
| `amount` | Запрошенная сумма | `100` | Decimal |
| `paidAmount` | Фактически оплаченная сумма | `100` | Decimal |
| `totalCommissionAmount` | Комиссия | `2.5` | Decimal |
| `currency` | Валюта (всегда INR) | `INR` | String |

### Банковские данные (UTR)

| Field | Description | Example |
|-------|-------------|---------|
| `utr` | **Unique Transaction Reference** (банковский ref) | `983991008838` |
| `rrn` | Retrieval Reference Number | `123456789012` |

> **UTR** - уникальный номер банковской транзакции. Используется для сверки с банком.

### Участники транзакции

| Field | Description | Example |
|-------|-------------|---------|
| `clientId` | UUID клиента/мерчанта | `5b12c121-06e7-4b53-a8fa-c5d5b56e33ec` |
| `clientName` | Название клиента | `91G_TECH_PVT_LTD` |
| `resellerId` | UUID реселлера | `d5aaa8f6-b825-4c62-9a44-f4608e8fc6b7` |
| `resellerName` | Название реселлера | `PS_Reseller_1` |

### Данные плательщика (Payer Info)

| Field | Description | Example |
|-------|-------------|---------|
| `payerVpa` | UPI VPA плательщика | `9606143313-2@axl` |
| `upiId` | UPI ID получателя | `hdml61iotatkl70194@hdfcbank` |
| `payerName` | Имя плательщика (если доступно) | `John Doe` |
| `payerPhone` | Телефон плательщика | `+919876543210` |

### Типы и методы оплаты

| Field | Description | Values |
|-------|-------------|--------|
| `transactionType` | Тип транзакции | `UPI_INTENT`, `UPI_COLLECT`, `IMPS` |
| `paymentMode` | Режим оплаты | `UPI`, `IMPS`, `NEFT` |

### Временные метки

| Field | Description | Format |
|-------|-------------|--------|
| `createdAt` | Время создания (UTC) | `2026-01-15T15:46:46.698Z` |
| `modifiedAt` | Время последнего изменения | `2026-01-15T15:47:20.139Z` |
| `completedAt` | Время завершения | `2026-01-15T15:47:20.000Z` |

### Дополнительные поля

| Field | Description |
|-------|-------------|
| `callbackUrl` | URL для callback после оплаты |
| `callbackStatus` | Статус callback (sent/pending) |
| `ipAddress` | IP адрес плательщика |
| `deviceInfo` | Информация об устройстве |

---

## Pay-Out Transaction Fields (Детальное описание)

### Идентификаторы

| Field | Description | Example |
|-------|-------------|---------|
| `txnId` / `transactionId` | ID транзакции | `PO202601151234` |
| `orderId` | Client order ID | `PAYOUT_12345` |

### Данные получателя (Beneficiary)

| Field | Description | Example |
|-------|-------------|---------|
| `beneName` | Имя получателя | `Rajesh Kumar` |
| `beneAccount` | Номер счета | `1234567890123456` |
| `beneIfsc` | IFSC код банка | `HDFC0001234` |
| `beneEmail` | Email получателя | `rajesh@example.com` |
| `benePhone` | Телефон получателя | `+919876543210` |

### Финансовые данные

| Field | Description |
|-------|-------------|
| `amount` | Сумма выплаты |
| `txnCharges` | Комиссия за транзакцию |
| `netAmount` | Сумма после комиссии |

---

## Status Values

### Pay-In Statuses

| Status | Description | Normalized |
|--------|-------------|------------|
| `Success` | Payment completed | `success` |
| `Failed` | Payment failed | `failed` |
| `INITIATED` | Payment initiated | `pending` |
| `Pending` | Payment pending | `pending` |
| `In Process` | Being processed | `processing` |
| `Incomplete` | Payment incomplete | `pending` |
| `Refunded` | Payment refunded | `refunded` |
| `Cb_Refunded` | Chargeback refunded | `refunded` |
| `Tampered` | Suspicious transaction | `failed` |

### Pay-Out Statuses

| Status | Description | Normalized |
|--------|-------------|------------|
| `SUCCESS` | Payout completed | `success` |
| `FAILED` | Payout failed | `failed` |

---

## Reconciliation Key

**Vima `client_operation_id` соответствует PayShack `orderId`**

Пример:
- Vima: `client_operation_id: "AGQAMEBYUPHQ4"`
- PayShack: `orderId: "AGQAMEBYUPHQ4"`

---

## Client Mapping (PayShack -> Vima)

| PayShack Client | Vima Project |
|-----------------|--------------|
| `91G_TECH_PVT_LTD` | `91game` |
| `IG Indigate P_Out` | `indigate_payout` |
| `MNCL_M5_Pvt_Ltd` | `mncl_m5` |
| `Mn CL THREE_PVT_LTD` | `mncl_three` |

---

## Python Client Example

```python
import httpx

class PayShackClient:
    BASE_URL = "https://api.payshack.in"
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.token = None
        self.client_id = None
    
    async def login(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/indigate-user-svc/api/v1/auth/login",
                json={"email": self.email, "password": self.password}
            )
            data = response.json()
            self.token = data["data"]["token"]
            self.client_id = data["data"]["clientId"]
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "reseller-id": self.client_id,
        }
    
    async def get_payin_transactions(self, page=1, limit=100):
        await self._ensure_auth()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/indigate-payin-svc/api/v1/payin/transaction/fetch",
                params={"page": page, "limit": limit},
                headers=self._get_headers()
            )
            return response.json()
```

---

## cURL Example

```bash
# Login
curl -X POST 'https://api.payshack.in/indigate-user-svc/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"psrs1@gmail.com","password":"Payshacksub@123"}'

# Get transactions (use token and clientId from login response)
curl 'https://api.payshack.in/indigate-payin-svc/api/v1/payin/transaction/fetch?page=1&limit=10' \
  -H 'Authorization: Bearer {token}' \
  -H 'reseller-id: {clientId}'
```

---

## Transaction Details / Polling Status

### Get Single Transaction by Order ID

```http
GET /indigate-payin-svc/api/v1/payin/transaction/fetch?orderId={order_id}
```

### Get Single Transaction by Transaction ID

```http
GET /indigate-payin-svc/api/v1/payin/transaction/fetch?transactionId={txn_id}
```

### Polling Status (для Vima)

При polling статуса с платформы, **provider id должен передаваться в поле `c_id`**:

```json
{
  "params": {
    "payment": {
      "identifiers": {
        "c_id": 1768491979464
      }
    }
  }
}
```

> **Важно:** `c_id` в Vima = `orderId` в PayShack. Это ключ для сверки между системами.

---

## Получение детальной информации

### Transaction Detail Response

При запросе одной транзакции по `orderId` или `txnId` возвращается полная информация:

```json
{
  "success": true,
  "data": {
    "transaction": {
      "_id": 15910368,
      "txnId": "Y7KY0V202611591646",
      "orderId": "AGQAMEBYUPHQ4",
      "spTxnId": "1003kqTJw77860115211719",
      "amount": 100,
      "paidAmount": 100,
      "utr": "983991008838",
      "rrn": "123456789012",
      "txnStatus": "Success",
      
      // Client Info
      "clientId": "5b12c121-06e7-4b53-a8fa-c5d5b56e33ec",
      "clientName": "91G_TECH_PVT_LTD",
      "resellerId": "d5aaa8f6-b825-4c62-9a44-f4608e8fc6b7",
      
      // Payer Info
      "payerVpa": "9606143313-2@axl",
      "payerName": "User Name",
      "payerPhone": "9876543210",
      
      // Bank Info
      "upiId": "hdml61iotatkl70194@hdfcbank",
      "bankName": "HDFC Bank",
      
      // Payment Details
      "transactionType": "UPI_INTENT",
      "paymentMode": "UPI",
      
      // Commission
      "totalCommissionAmount": 2.5,
      "clientCommission": 2.0,
      "resellerCommission": 0.5,
      
      // Callback
      "callbackUrl": "https://merchant.com/callback",
      "callbackStatus": "sent",
      "callbackResponse": {"status": "received"},
      
      // Timestamps
      "createdAt": "2026-01-15T15:46:46.698Z",
      "modifiedAt": "2026-01-15T15:47:20.139Z",
      "completedAt": "2026-01-15T15:47:20.000Z"
    }
  }
}
```

---

## Отчеты и экспорт

### Доступные форматы

| Format | Endpoint | Description |
|--------|----------|-------------|
| API JSON | `/transaction/fetch` | Пагинированный список |
| CSV | Generate manually | Экспорт через клиент |

### Генерация отчета

В dashboard есть функция генерации отчетов за период (7 дней max):

1. **Date Range**: Выбор периода `dateFrom` - `dateTo`
2. **Time Range**: Опционально `startTime` - `endTime`
3. **Format**: CSV/Excel

> **Note**: Точный endpoint для скачивания отчетов требует дополнительного исследования.

---

## Data Sync Strategy

### Инкрементальная синхронизация

```
1. Запомнить last_sync_timestamp
2. Запрос: GET /transaction/fetch?dateFrom={last_sync}&dateTo={now}
3. Обработать все страницы
4. Обновить last_sync_timestamp
```

### Backfill (оконная загрузка)

Для контролируемой догрузки истории используем оконный подход:

```
1. Разбить диапазон на окна (например, 1 день)
2. Для каждого окна: GET /transaction/fetch?dateFrom={start}&dateTo={end}
3. Обработать все страницы окна
4. Логировать прогресс: pages / totalRecords / inserted / updated
```

### Интервалы синхронизации

| Data Type | Interval | Strategy |
|-----------|----------|----------|
| Pay-In Transactions | 5 min | dateFrom/dateTo filter |
| Pay-Out Transactions | 5 min | dateFrom/dateTo filter |
| Clients/Metadata | 30 min | Full refresh |

---

## Notes

1. **Time Zone**: Timestamps в ответах уже в UTC
2. **Pagination**: Стандартная пагинация с `page` и `limit`
3. **Rate Limits**: Неизвестны, рекомендуется делать паузы 300ms между запросами
4. **Session**: Токен действует ~30 минут, используйте `refreshToken` для обновления
5. **Total Records**: ~140,000+ Pay-In транзакций, ~14,000 страниц
6. **Currency**: Только INR (индийские рупии)
7. **Country**: Только IN (Индия)
8. **Response Format**: В некоторых ответах `success` может отсутствовать, ориентируйтесь на `statusCode: 200`, `status: "OK"` и наличие поля `data`.
