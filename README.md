# anore — Python SDK

Официальный SDK для приёма платежей через [anore](https://anore.cc). Без зависимостей, только stdlib, Python 3.8+.

## Структура

```
python/
├── pyproject.toml
└── anore/
    ├── __init__.py     публичный экспорт
    ├── client.py       AnoreClient — создание платежа, статус
    ├── _transport.py   HTTP с ретраями/бэкоффом
    ├── webhooks.py     verify_webhook / parse_webhook
    ├── models.py       Payment, WebhookEvent
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
)
print(payment.payment_url)   # отправьте клиента на форму оплаты

# 2. проверить статус
status = anore.get_payment(payment.id)
print(status.status, status.paid)   # 'paid', True
```

## Проверка вебхука

При оплате anore шлёт `POST` на ваш URL с заголовком `Anore-Signature`.
Проверяйте подпись по **сырому** телу запроса (не распарсенному JSON):

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
| `create_payment(amount, description, order_id=None, shop_id=None)` | создать счёт → `Payment` |
| `get_payment(id)` | статус → `Payment` (`.status`, `.paid`) |
| `verify_webhook(raw_body, signature, secret)` | проверка подписи → `bool` |
| `parse_webhook(raw_body, signature, secret)` | проверка + разбор → `WebhookEvent` (бросает `SignatureError`) |

Ошибки: `ValidationError` (400), `AuthenticationError` (401), `ForbiddenError` (403), `NotFoundError` (404), `ServerError` (5xx), `APIConnectionError` (сеть), `SignatureError` (подпись). База — `AnoreError`.

Полная документация: https://anore.cc/docs
