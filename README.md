# anore — Python SDK

Официальный SDK для приёма платежей через [anore](https://anore.cc). Без зависимостей, только stdlib, Python 3.8+.

## Структура

```
python/
├── pyproject.toml
└── anore/
    ├── __init__.py     публичный экспорт
    ├── client.py       AnoreClient — платежи, баланс и выплаты
    ├── _transport.py   HTTP с ретраями/бэкоффом
    ├── webhooks.py     verify_webhook / parse_webhook
    ├── models.py       модели ответов API и вебхуков
    └── errors.py       иерархия ошибок
```

## Установка

`pip install .` из этой папки, либо скопируйте папку `anore/` в проект.

```python
from anore import AnoreClient, parse_webhook
```

## Быстрый старт

```python
anore = AnoreClient(api_key="an_live_xxxxxxxxxxxxxxxx")

# 1. создать счёт
payment = anore.create_payment(
    amount=1500,
    description="Подписка Pro",
    order_id="order_42",
    shop_id=1,   # обязателен для аккаунтовых ключей (an_live_ / an_test_)
    user_identity={
        "type": "telegram_id",
        "value": "123456789",
        "telegram_username": "@customer_name",
    },
)
print(payment.payment_url)   # отправьте клиента на форму оплаты

# 2. проверить статус
status = anore.get_payment(payment.id)
print(status.status, status.paid)   # 'paid', True

# 3. список платежей и баланс
page = anore.list_payments(shop_id=1, status="paid", limit=20)
balance = anore.get_balance(shop_id=1)

# 4. выплата
payout = anore.create_payout(
    amount=5000,
    method="usdt_ton",
    address="UQ...",
    shop_id=1,
    external_id="payout_42",
)
print(payout.id, payout.status)
```

## Identity и франшиза

`user_identity` сейчас может быть необязательным для конкретной кассы, но скоро станет обязательным. Передавайте его уже сейчас на каждом платеже. Поддерживаемые типы: `telegram_id`, `email`, `username`, `external_id`; `telegram_username` разрешён только для `telegram_id` и служит только display-метаданными. Telegram ID сопоставляется глобально, остальные типы — только внутри исходной кассы.

Если у кассы включён franchise mode, каждый платёж обязан содержать конкретный филиал:

```python
payment = anore.create_payment(
    amount=1500,
    description="Заказ филиала",
    user_identity={"type": "email", "value": "buyer@example.com"},
    franchise={
        "type": "website",
        "address": "https://branch.example.com",
        "owner_telegram_id": "987654321",
        "owner_telegram_username": "branch_owner",
    },
)
```

`franchise` обязателен при включённом franchise mode и запрещён при выключенном. ANORE проверяет оба объекта до сохранения платежа и provider effects. Они принадлежат только ANORE, не передаются Payso и не появляются в публичных ответах, merchant webhooks, обычных логах или exports.

## Рекуррентные платежи

```python
catalog = anore.get_subscription_catalog()
binding = anore.create_subscription(
    plan_id=catalog.shops[0]["plans"][0]["planId"],
    customer_id="customer-42",
    customer_email="buyer@example.com",
    idempotency_key="binding-customer-42",
    shop_id=1,
)
```

SDK никогда автоматически не повторяет subscription POST. При `503 binding_reconciling` provider effect неизвестен: сохраните тот же `idempotency_key` и идентичное тело, не создавайте новый ключ и не запускайте параллельную привязку.

## Проверка вебхука

При оплате anore шлёт `POST` на ваш URL с заголовком `Anore-Signature`.
Проверяйте подпись по **сырому** телу запроса (не распарсенному JSON):

Тот же обработчик принимает `payout.created`, `payout.processing`, `payout.succeeded`, `payout.failed` и `payout.updated` (ручная корректировка статуса, см. `statusRevision`); у события выплаты `event.is_payout == True`.

```python
# Flask
from flask import Flask, request, abort
from anore import parse_webhook, SignatureError
import os

app = Flask(__name__)

@app.post("/webhook")
def webhook():
    raw = request.get_data()  # сырые байты, не request.json
    sig = request.headers.get("Anore-Signature", "")
    try:
        event = parse_webhook(raw, sig, os.environ["ANORE_WEBHOOK_SECRET"])
    except SignatureError:
        abort(403)
    if event.is_succeeded:
        ...  # отгрузить заказ event.id / event.order_id
    return {"ok": True}
```

## Обработка ошибок

```python
from anore import AnoreClient, ValidationError, AuthenticationError, APIConnectionError

try:
    anore.create_payment(amount=1500, description="Заказ")
except ValidationError:      # 400 — кривой запрос
    ...
except AuthenticationError:  # 401 — неверный ключ
    ...
except APIConnectionError:   # сеть недоступна
    ...
```

## Справка

| API | Описание |
|-----|----------|
| `AnoreClient(api_key, secret=None, base_url=..., timeout=30, max_retries=2)` | клиент; `secret` подписывает исходящие запросы |
| `create_payment(..., user_identity=None, franchise=None)` | создать счёт → `Payment`; identity скоро станет обязательным, franchise зависит от режима кассы |
| `get_payment(id)` | статус → `Payment` (`.status`, `.paid`) |
| `list_payments(shop_id=None, status=None, date_from=None, date_to=None, limit=50, offset=0)` | страница платежей → `PaymentList` |
| `get_subscription_catalog()` | доступные кассы и планы → `SubscriptionCatalog` |
| `create_subscription(plan_id, customer_id, customer_email, idempotency_key, shop_id=None)` | QR привязки → `SubscriptionBinding` |
| `charge_subscription(subscription_id, idempotency_key)` | начать списание → `SubscriptionCharge` |
| `get_subscription(subscription_id)` | безопасный статус → `SubscriptionStatus` |
| `get_balance(shop_id=None)` | баланс → `Balance` |
| `get_payout_fees(shop_id=None)` | комиссии → `PayoutFees` |
| `get_payout_rates(shop_id=None)` | курсы → `PayoutRates` |
| `list_payouts(shop_id=None, limit=50, cursor=None)` | история выплат → `PayoutList` |
| `create_payout(amount, method, address, shop_id=None, bank=None, external_id=None)` | заявка → `Payout` |
| `get_payout(id)` | статус выплаты → `Payout` |
| `verify_webhook(raw_body, signature, secret)` | проверка подписи → `bool` |
| `parse_webhook(raw_body, signature, secret)` | проверка + разбор → `WebhookEvent` (бросает `SignatureError`) |

Ошибки: `ValidationError` (400), `AuthenticationError` (401), `ForbiddenError` (403), `NotFoundError` (404), `ServerError` (5xx), `APIConnectionError` (сеть), `SignatureError` (подпись). База — `AnoreError`.

Полная документация: https://anore.cc/docs
