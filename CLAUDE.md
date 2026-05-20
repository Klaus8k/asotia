# CLAUDE.md — asotia.ru (Зерно истины)

> Этот файл — единственный источник правды о проекте.
> Вставляй его в начало каждого нового чата с Claude.

---

## 1. Стек и версии

| Компонент       | Версия     | Примечание                          |
|-----------------|------------|-------------------------------------|
| Python          | 3.11.x     |                                     |
| Django          | 4.2.x LTS  | LTS до апреля 2026                  |
| PostgreSQL      | 15.x       |                                     |
| psycopg2-binary | 2.9.x      |                                     |
| Redis           | 7.x        | Сессии, корзина, кэш                |
| Celery          | 5.3.x      | Асинхронные задачи                  |
| Gunicorn        | 21.x       |                                     |
| Nginx           | 1.24 stable|                                     |
| Ubuntu Server   | 22.04 LTS  |                                     |
| Docker Desktop  | latest     | Локальная разработка (PostgreSQL + Redis) |
| Poetry          | 1.8.x      | Управление зависимостями                  |

---

## 2. Структура проекта

```
project/
  config/
    settings/
      base.py
      dev.py
      prod.py
    urls.py
    wsgi.py
    asgi.py

  apps/
    accounts/      # Личный кабинет, скидочная программа
    catalog/       # Товары, категории, фильтры
    cart/          # Корзина (через Redis/сессии)
    orders/        # Заказы, статусы
    payments/      # Оплата (абстракция над банками)
    delivery/      # Доставка API (СДЭК и др.)
    core/          # Базовые модели, миксины, утилиты
    pages/         # Статичные страницы (о нас, контакты)

  templates/
  static/
  media/
```

---

## 3. Модели БД (схема)

### accounts/models.py
```python
class UserProfile(models.Model):
    user         = OneToOneField(User)
    phone        = CharField
    address      = TextField
    discount_pct = PositiveSmallIntegerField  # % скидки, default=0
    bonus_points = PositiveIntegerField       # default=0
    created_at   = DateTimeField(auto_now_add=True)

class DiscountCard(models.Model):
    user         = OneToOneField(UserProfile)
    card_number  = CharField(unique=True)
    level        = CharField(choices=['bronze','silver','gold'])
    valid_until  = DateField
```

### catalog/models.py
```python
class Category(models.Model):
    name   = CharField
    slug   = SlugField(unique=True)
    parent = ForeignKey('self', null=True)  # вложенные категории

class Tag(models.Model):
    name = CharField
    slug = SlugField(unique=True)

class Product(models.Model):
    name        = CharField
    slug        = SlugField(unique=True)
    category    = ForeignKey(Category)
    tags        = ManyToManyField(Tag)
    price       = DecimalField(max_digits=10, decimal_places=2)
    weight      = DecimalField  # граммы
    description = TextField
    image       = ImageField
    is_active   = BooleanField(default=True)
    in_stock    = BooleanField(default=True)
    created_at  = DateTimeField(auto_now_add=True)
```

### cart/ (Redis, не БД)
```python
# Корзина хранится в Redis как JSON
# Ключ: cart:{session_key} или cart:user:{user_id}
# Структура: {product_id: {qty, price}}
```

### orders/models.py
```python
class Order(models.Model):
    STATUS = ['new','confirmed','cooking','delivering','done','cancelled']
    user        = ForeignKey(User, null=True)  # null = гость
    status      = CharField(choices=STATUS, default='new')
    total_price = DecimalField
    discount    = DecimalField(default=0)
    address     = TextField
    comment     = TextField(blank=True)
    created_at  = DateTimeField(auto_now_add=True)
    updated_at  = DateTimeField(auto_now=True)

class OrderItem(models.Model):
    order    = ForeignKey(Order, related_name='items')
    product  = ForeignKey(Product)
    qty      = PositiveSmallIntegerField
    price    = DecimalField  # цена на момент заказа (!)
```

### payments/models.py
```python
class Payment(models.Model):
    STATUS = ['pending','success','failed','refunded']
    order        = OneToOneField(Order)
    provider     = CharField  # 'yookassa', 'tinkoff', etc.
    external_id  = CharField  # ID платежа у банка
    status       = CharField(choices=STATUS)
    amount       = DecimalField
    paid_at      = DateTimeField(null=True)
    raw_response = JSONField  # ответ банка целиком
```

### delivery/models.py
```python
class DeliveryZone(models.Model):
    name     = CharField
    price    = DecimalField
    min_time = PositiveSmallIntegerField  # минут

class Shipment(models.Model):
    order        = OneToOneField(Order)
    provider     = CharField  # 'cdek', 'own', etc.
    tracking_num = CharField(blank=True)
    zone         = ForeignKey(DeliveryZone)
    address      = TextField
    status       = CharField
    estimated_at = DateTimeField(null=True)
```

---

## 4. Зависимости
Управление через Poetry. См. раздел 11 (pyproject.toml).
Файл requirements/ не используется.

---

## 5. Ключевые настройки (base.py — скелет)

```python
AUTH_USER_MODEL = 'auth.User'        # стандартный, расширяем через UserProfile
LOGIN_URL       = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/cabinet/'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/0'),
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

CELERY_BROKER_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/1')
```

---

## 6. Нагрузка и деплой

- Ожидаемая нагрузка: **до 200 пользователей в день**
- Деплой: **VPS + Nginx + Gunicorn**
- 2-4 воркера Gunicorn достаточно для данной нагрузки
- Nginx отдаёт static/media напрямую, проксирует остальное

---

## 7. Интеграции (планируемые)

| Назначение  | Сервис / SDK          | Статус   |
|-------------|----------------------|----------|
| Оплата      | ЮКасса (yookassa SDK)| Планируется |
| Оплата alt. | Тинькофф REST API    | Планируется |
| Доставка    | СДЭК API (cdek-sdk2) | Возможно |
| Адреса      | DaData               | Возможно |

---

## 8. Принцип модульности

Этот проект — **шаблон**. Для нового магазина:
1. Форкнуть репозиторий
2. Заменить модели в `catalog/` под новый тип товаров
3. Подключить/отключить нужные `apps/` в `INSTALLED_APPS`
4. Все остальные модули (cart, orders, payments, delivery) — переиспользуются без изменений

---

## 9. Соглашения

- Ветки: `main` (прод), `develop` (разработка), `feature/xxx`
- Миграции коммитить вместе с моделями
- Секреты — только в `.env`, никогда в git
- Для каждого app — свой `urls.py`, подключаем через `include()`
- Все денежные значения — `DecimalField`, никогда `FloatField`

## 10. Локальное окружение (Windows 10)

### Инструменты
- VS Code + расширения: Python, Pylance, Django, DotENV, GitLens
- Windows Terminal — вместо стандартного cmd
- Docker Desktop — только Redis локально
- DBeaver — подключение через SSH tunnel (не открывать порт наружу)
- WinSCP — только для аварийных случаев

### Запуск зависимостей локально
docker-compose.yml лежит в корне проекта.
Команда для старта: docker-compose up -d
Останавливает: docker-compose down

Сервисы:
- Redis 7 → localhost:6379
- PostgreSQL — всегда на VPS (79.133.181.123:5432)

### Параметры docker-compose (dev)
db:
  POSTGRES_DB:       foodshop
  POSTGRES_USER:     задать в .env
  POSTGRES_PASSWORD: задать в .env

### Управление зависимостями — Poetry 1.8.x
Файл зависимостей: pyproject.toml (не редактировать requirements.txt вручную)

Основные команды:
  poetry install          # установить все зависимости
  poetry add <пакет>      # добавить prod-зависимость
  poetry add --group dev <пакет>  # добавить dev-зависимость
  poetry remove <пакет>   # удалить
  poetry shell            # активировать виртуальное окружение
  poetry update           # обновить все пакеты

Группы зависимостей:
  [tool.poetry.dependencies]       — prod (django, celery, redis, ...)
  [tool.poetry.group.dev]          — dev  (debug-toolbar, pytest-django, ...)

На VPS: poetry install --only main  # только prod, без dev


## 11. pyproject.toml (скелет)

```toml
[tool.poetry]
name = "foodshop"
version = "0.1.0"
python = "^3.11"

[tool.poetry.dependencies]
django = "^4.2"
psycopg2-binary = "^2.9"
redis = "^5.0"
celery = "^5.3"
pillow = "^10.0"
django-environ = "^0.11"
django-filter = "^23.0"
gunicorn = "^21.0"

[tool.poetry.group.dev.dependencies]
django-debug-toolbar = "*"
pytest-django = "*"
```


## 12. Инфраструктура

### VPS
- OS:     Ubuntu 22.04 LTS
- Домен:  asotia.ru
- Путь к проекту: /var/www/foodshop

### Nginx
- Config:  /etc/nginx/sites-available/foodshop
- Logs:    /var/log/nginx/foodshop_access.log
           /var/log/nginx/foodshop_error.log

### Gunicorn
- Socket:   /run/foodshop.sock
- Service:  /etc/systemd/system/foodshop.service
- Workers:  3

### Пути на сервере
- Виртуальное окружение: /var/www/foodshop/.venv
- Статика:  /var/www/foodshop/static/
- Медиа:    /var/www/foodshop/media/
- Логи:     /var/www/foodshop/logs/

### .env
- Хранится локально и в облаке (Notion/Bitwarden)
- В git не пушить никогда
- Шаблон: .env.example — пушить в git