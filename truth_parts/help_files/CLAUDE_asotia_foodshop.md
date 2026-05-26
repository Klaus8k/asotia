# CLAUDE.md — Asoti Food Shop (Зерно истины)

> Этот файл — единый источник правды по проекту интернет-магазина Asoti.
> Вставляй актуальную версию этого файла в начало каждого нового технического чата с Claude/ChatGPT.
> Если решение изменилось — сначала обновляем этот файл, потом пишем код.

---

## 0. Назначение проекта

Проект: интернет-магазин продуктов / товаров Asoti.

Основная цель первого запуска — рабочий сайт, где пользователь может:
1. Посмотреть категории и товары.
2. Открыть карточку товара.
3. Добавить товар в корзину.
4. Оформить заказ без обязательной регистрации.
5. Передать заказ администратору для ручной обработки.

Проект должен быть простым, расширяемым и пригодным для повторного использования как шаблон для других магазинов.

---

## 1. Домены и окружения

### Production-домен

- Основной домен: `asotia.ru`
- Дополнительный домен: `www.asotia.ru`
- Основной вариант для сайта: `asotia.ru`
- Редирект: `www.asotia.ru` → `asotia.ru`

### Окружения

| Окружение | Назначение | Где находится |
|----------|------------|---------------|
| local/dev | локальная разработка | Windows 10 + VS Code + Docker |
| production | рабочий сайт | VPS + Nginx + Gunicorn |

---

## 2. Стек и версии

| Компонент       | Версия / решение | Примечание |
|-----------------|------------------|-----------|
| Python          | 3.12.x | стабильная версия для нового проекта |
| Django          | 5.2.x LTS | LTS-ветка |
| PostgreSQL      | 15.x | стабильная версия, достаточно для проекта |
| Redis           | 7.x | позже: кэш, сессии, Celery; на MVP можно без него |
| Celery          | 5.x | не в первом MVP, добавить позже |
| Gunicorn        | актуальная стабильная | production WSGI-сервер |
| Nginx           | из репозитория Ubuntu | reverse proxy + static/media |
| Ubuntu Server   | 22.04 LTS | текущая целевая ОС VPS |
| Docker Desktop  | latest | локальная разработка PostgreSQL + Redis |
| Poetry          | 1.8.x | управление зависимостями |

---

## 3. Принцип разработки

Главный принцип: сначала простой рабочий MVP, потом расширение.

Не добавлять сложные интеграции раньше времени:
- онлайн-оплата — этап 2;
- СДЭК / доставка API — этап 2;
- Celery — этап 2;
- бонусы и скидочные уровни — после базового заказа;
- сложные фильтры — после наполнения каталога.

Первый релиз должен быть понятным и запускаемым.

---

## 4. MVP первого запуска

В первый релиз входят:

1. Главная страница.
2. Категории товаров.
3. Список товаров.
4. Карточка товара.
5. Корзина.
6. Оформление заказа без обязательной регистрации.
7. Админка товаров.
8. Админка категорий.
9. Админка заказов.
10. Уведомление администратору о новом заказе.
11. Страница “Контакты”.
12. Страница “О нас”.
13. Политика конфиденциальности.
14. Пользовательское соглашение / условия заказа.

Не входит в первый релиз:

1. Онлайн-оплата.
2. Интеграция с доставкой.
3. Личный кабинет со сложной историей заказов.
4. Бонусная программа.
5. Celery-задачи.
6. Сложная аналитика.
7. Многоуровневые промокоды.

---

## 5. Структура проекта

```text
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
    accounts/      # пользователи, профиль, позже скидочная программа
    catalog/       # товары, категории, фильтры
    cart/          # корзина
    orders/        # заказы, статусы
    payments/      # оплата, этап 2
    delivery/      # доставка, этап 2
    core/          # базовые модели, миксины, утилиты
    pages/         # статичные страницы: о нас, контакты, документы

  templates/
  static/
  media/
  locale/
```

---

## 6. Приложения проекта

### accounts

Назначение:
- регистрация и авторизация пользователей;
- профиль пользователя;
- телефон, адрес;
- позже: скидочная карта, бонусы.

В MVP регистрация не обязательна. Заказ можно оформить как гость.

### catalog

Назначение:
- категории;
- товары;
- теги;
- цены;
- наличие;
- изображения товаров.

Модель товара пока оставляем простой. Расширения по товару добавлять позже, когда станет понятна реальная структура каталога.

### cart

Назначение:
- добавление товара в корзину;
- изменение количества;
- удаление товара;
- пересчёт суммы.

Для MVP корзина может храниться в Django sessions.
Redis можно подключить позже, если понадобится.

### orders

Назначение:
- создание заказа;
- хранение состава заказа;
- хранение данных покупателя на момент оформления;
- статусы заказа;
- просмотр и обработка заказа в админке.

### payments

Назначение:
- онлайн-оплата;
- хранение статуса платежа;
- интеграции с ЮКассой / Тинькофф.

Статус: этап 2, не MVP.

### delivery

Назначение:
- зоны доставки;
- стоимость доставки;
- интеграции со службами доставки.

Статус: этап 2, не MVP.

### pages

Назначение:
- “О нас”;
- “Контакты”;
- “Доставка и оплата”;
- “Политика конфиденциальности”;
- “Пользовательское соглашение”.

---

## 7. Модели БД

### accounts/models.py

```python
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)

    # Для будущей скидочной программы
    discount_pct = models.PositiveSmallIntegerField(default=0)
    bonus_points = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile: {self.user}"
```

Скидочную карту можно добавить позже, когда появится реальная логика программы лояльности:

```python
class DiscountCard(models.Model):
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="discount_card",
    )
    card_number = models.CharField(max_length=64, unique=True)
    level = models.CharField(
        max_length=16,
        choices=[
            ("bronze", "Bronze"),
            ("silver", "Silver"),
            ("gold", "Gold"),
        ],
        default="bronze",
    )
    valid_until = models.DateField(null=True, blank=True)
```

---

### catalog/models.py

```python
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Вес в граммах",
    )

    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True)

    is_active = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
```

Примечание:
- модель товара пока специально не усложняем;
- позже можно добавить артикулы, остатки, старую цену, несколько изображений, SEO-поля, единицы измерения и характеристики.

---

### cart

На MVP корзину можно хранить в Django session.

Пример структуры:

```python
{
    "product_id": {
        "qty": 2,
        "price": "350.00"
    }
}
```

Возможный ключ в session:

```python
request.session["cart"]
```

Redis для корзины можно добавить позже, если появится необходимость.

---

### orders/models.py

```python
from django.conf import settings
from django.db import models

from apps.catalog.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        CONFIRMED = "confirmed", "Подтверждён"
        ASSEMBLING = "assembling", "Собирается"
        READY = "ready", "Готов"
        DELIVERING = "delivering", "Доставляется"
        COMPLETED = "completed", "Завершён"
        CANCELLED = "cancelled", "Отменён"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.NEW,
    )

    # Данные покупателя на момент оформления заказа
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=32)
    customer_email = models.EmailField(blank=True)

    # Доставка / самовывоз
    address = models.TextField(blank=True)
    delivery_method = models.CharField(max_length=64, blank=True)
    delivery_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    # Оплата
    payment_method = models.CharField(max_length=64, blank=True)

    # Деньги
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    qty = models.PositiveSmallIntegerField()

    # Цена товара на момент заказа
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product} × {self.qty}"
```

---

### payments/models.py

Этап 2. В MVP можно не создавать.

```python
from django.db import models

from apps.orders.models import Order


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        SUCCESS = "success", "Успешно"
        FAILED = "failed", "Ошибка"
        REFUNDED = "refunded", "Возврат"

    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="payment",
    )
    provider = models.CharField(max_length=64)
    external_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(null=True, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

---

### delivery/models.py

Этап 2. В MVP можно не создавать.

```python
from django.db import models

from apps.orders.models import Order


class DeliveryZone(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    min_time = models.PositiveSmallIntegerField(
        help_text="Минимальное время доставки в минутах",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Shipment(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name="shipment",
    )
    provider = models.CharField(max_length=64, blank=True)
    tracking_num = models.CharField(max_length=255, blank=True)
    zone = models.ForeignKey(
        DeliveryZone,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    address = models.TextField()
    status = models.CharField(max_length=64, blank=True)
    estimated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 8. Настройки Django

### config/settings/base.py

```python
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Project apps
    "apps.accounts",
    "apps.catalog",
    "apps.cart",
    "apps.orders",
    "apps.pages",

    # Stage 2
    # "apps.payments",
    # "apps.delivery",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "auth.User"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/cabinet/"
LOGOUT_REDIRECT_URL = "/"

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

### config/settings/dev.py

```python
from .base import *

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="postgres://foodshop:foodshop@127.0.0.1:5432/foodshop",
    )
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

### config/settings/prod.py

```python
from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "asotia.ru",
    "www.asotia.ru",
]

CSRF_TRUSTED_ORIGINS = [
    "https://asotia.ru",
    "https://www.asotia.ru",
]

DATABASES = {
    "default": env.db("DATABASE_URL")
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False

X_FRAME_OPTIONS = "DENY"
```

---

## 9. Зависимости

Управление зависимостями — через Poetry.

Файл `requirements.txt` вручную не редактировать.
Если он понадобится для деплоя, генерировать из Poetry.

### Основные команды

```bash
poetry install
poetry add <package>
poetry add --group dev <package>
poetry remove <package>
poetry update
poetry shell
```

На VPS:

```bash
poetry install --only main
```

---

## 10. pyproject.toml

```toml
[tool.poetry]
name = "asoti-foodshop"
version = "0.1.0"
description = "Asoti food shop"
authors = ["Asoti"]
package-mode = false

[tool.poetry.dependencies]
python = "^3.12"
django = "^5.2"
psycopg2-binary = "^2.9"
pillow = "^10.0"
django-environ = "^0.11"
gunicorn = "^21.0"

# Stage 2
# redis = "^5.0"
# celery = "^5.3"
# django-filter = "^24.0"

[tool.poetry.group.dev.dependencies]
django-debug-toolbar = "*"
pytest = "*"
pytest-django = "*"
ruff = "*"
```

---

## 11. Локальное окружение Windows 10

### Инструменты

- VS Code
- Расширения VS Code:
  - Python
  - Pylance
  - Django
  - DotENV
  - GitLens
- Windows Terminal
- Docker Desktop
- DBeaver
- Git
- WinSCP только для аварийных случаев

### Локальные сервисы

Локально через Docker запускаются:

- PostgreSQL
- Redis, если понадобится

Django запускается локально через Poetry.

---

## 12. docker-compose.yml для dev

```yaml
services:
  db:
    image: postgres:15
    container_name: asoti_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-foodshop}
      POSTGRES_USER: ${POSTGRES_USER:-foodshop}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-foodshop}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    container_name: asoti_redis
    restart: unless-stopped
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

Запуск:

```bash
docker compose up -d
```

Остановка:

```bash
docker compose down
```

---

## 13. .env

### .env.example

```env
DEBUG=True
SECRET_KEY=change-me

ALLOWED_HOSTS=127.0.0.1,localhost

DATABASE_URL=postgres://foodshop:foodshop@127.0.0.1:5432/foodshop

POSTGRES_DB=foodshop
POSTGRES_USER=foodshop
POSTGRES_PASSWORD=foodshop

REDIS_URL=redis://127.0.0.1:6379/0
```

### Production .env

```env
DEBUG=False
SECRET_KEY=strong-production-secret-key

ALLOWED_HOSTS=asotia.ru,www.asotia.ru

DATABASE_URL=postgres://db_user:db_password@127.0.0.1:5432/asoti_foodshop

REDIS_URL=redis://127.0.0.1:6379/0
```

Правила:
- `.env` никогда не пушить в git;
- `.env.example` можно и нужно хранить в git;
- реальные пароли хранить в Bitwarden / другом менеджере паролей;
- не хранить production `.env` в открытом облаке.

---

## 14. Production-инфраструктура

### VPS

- OS: Ubuntu 22.04 LTS
- Домен: `asotia.ru`
- Путь к проекту: `/var/www/asoti-foodshop`

### Nginx

- Config: `/etc/nginx/sites-available/asoti-foodshop`
- Symlink: `/etc/nginx/sites-enabled/asoti-foodshop`
- Logs:
  - `/var/log/nginx/asoti_access.log`
  - `/var/log/nginx/asoti_error.log`

### Gunicorn

- Socket: `/run/asoti-foodshop.sock`
- Service: `/etc/systemd/system/asoti-foodshop.service`
- Workers: 2–3 для текущей нагрузки достаточно

### Пути на сервере

- Проект: `/var/www/asoti-foodshop`
- Виртуальное окружение: `/var/www/asoti-foodshop/.venv`
- Статика: `/var/www/asoti-foodshop/staticfiles/`
- Медиа: `/var/www/asoti-foodshop/media/`
- Логи приложения: `/var/www/asoti-foodshop/logs/`

---

## 15. Nginx — базовая схема

```nginx
server {
    listen 80;
    server_name asotia.ru www.asotia.ru;

    location /static/ {
        alias /var/www/asoti-foodshop/staticfiles/;
    }

    location /media/ {
        alias /var/www/asoti-foodshop/media/;
    }

    location / {
        proxy_pass http://unix:/run/asoti-foodshop.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

После подключения SSL через Certbot основной конфиг должен работать по HTTPS.

---

## 16. systemd service

```ini
[Unit]
Description=Asoti Food Shop Gunicorn Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/asoti-foodshop
Environment="DJANGO_SETTINGS_MODULE=config.settings.prod"
ExecStart=/var/www/asoti-foodshop/.venv/bin/gunicorn config.wsgi:application \
    --workers 3 \
    --bind unix:/run/asoti-foodshop.sock

Restart=always

[Install]
WantedBy=multi-user.target
```

Команды:

```bash
sudo systemctl daemon-reload
sudo systemctl enable asoti-foodshop
sudo systemctl start asoti-foodshop
sudo systemctl restart asoti-foodshop
sudo systemctl status asoti-foodshop
```

---

## 17. Безопасность production

Обязательно:

1. `DEBUG=False`.
2. Сильный `SECRET_KEY`.
3. `ALLOWED_HOSTS=asotia.ru,www.asotia.ru`.
4. `CSRF_TRUSTED_ORIGINS=https://asotia.ru,https://www.asotia.ru`.
5. Секреты только в `.env`.
6. `.env` не хранить в git.
7. PostgreSQL не открывать наружу.
8. Доступ к VPS только по SSH.
9. SSL-сертификат через Certbot.
10. Регулярные backup PostgreSQL.
11. Регулярные backup директории `media/`.

Желательно:

1. Отдельный Linux-пользователь под проект.
2. Ограниченные права на директории.
3. Логи приложения отдельно от nginx-логов.
4. Мониторинг свободного места на диске.
5. Проверка срока действия SSL.

---

## 18. Backup

Минимальная схема backup:

```bash
pg_dump asoti_foodshop > /backup/asoti_foodshop_$(date +%F).sql
tar -czf /backup/asoti_media_$(date +%F).tar.gz /var/www/asoti-foodshop/media/
```

Что бэкапить:
- базу PostgreSQL;
- папку `media/`;
- production `.env`;
- nginx config;
- systemd service.

Что не обязательно бэкапить:
- `.venv`;
- `staticfiles`;
- кэш;
- временные файлы.

---

## 19. Админка

В MVP админка Django используется как основной рабочий интерфейс администратора.

Нужно настроить:

1. Категории.
2. Товары.
3. Заказы.
4. Позиции заказа.
5. Страницы сайта.

Для заказов в админке нужны:
- фильтр по статусу;
- поиск по телефону;
- поиск по имени;
- список товаров в заказе;
- дата создания;
- итоговая сумма;
- быстрые действия по смене статуса.

---

## 20. Уведомления о заказе

Для MVP достаточно одного варианта:

1. Email админу.
2. Или Telegram-уведомление админу.

Лучше начать с email, потому что проще.
Telegram можно добавить позже.

Пример события:
- пользователь оформил заказ;
- заказ сохранился в БД;
- админу ушло уведомление;
- пользователь увидел страницу “Спасибо за заказ”.

---

## 21. URL-структура

Рекомендуемая структура:

```text
/                         # главная
/catalog/                 # каталог
/catalog/<category-slug>/  # категория
/product/<product-slug>/   # товар

/cart/                    # корзина
/cart/add/<product-id>/    # добавить товар
/cart/update/              # обновить количество
/cart/remove/<product-id>/ # удалить товар

/checkout/                # оформление заказа
/order/success/<order-id>/ # успешное оформление

/about/                   # о нас
/contacts/                # контакты
/delivery/                # доставка и оплата
/privacy/                 # политика конфиденциальности
/terms/                   # условия использования
```

Для каждого app — свой `urls.py`, подключение через `include()`.

---

## 22. Соглашения по коду

1. Секреты — только в `.env`.
2. Денежные значения — только `DecimalField`, не `FloatField`.
3. Миграции коммитить вместе с моделями.
4. Для каждого app — свой `urls.py`.
5. Бизнес-логику не раздувать во views.
6. Повторяющийся код выносить в services/selectors.
7. Не добавлять сложные абстракции раньше необходимости.
8. Перед деплоем проверять `python manage.py check --deploy`.

---

## 23. Git

Ветки:

- `main` — production;
- `develop` — разработка;
- `feature/xxx` — отдельные задачи.

Правила:
- в `main` не коммитить напрямую;
- сначала проверка локально;
- потом merge в `develop`;
- после проверки — merge в `main`;
- миграции коммитить вместе с изменением моделей.

---

## 24. Этапы развития

### Этап 1 — MVP

- структура проекта;
- настройки dev/prod;
- каталог;
- товары;
- корзина;
- оформление заказа;
- админка;
- базовый frontend;
- деплой на VPS;
- SSL;
- backup.

### Этап 2 — улучшения магазина

- онлайн-оплата;
- доставка;
- личный кабинет;
- история заказов;
- email/Telegram-уведомления;
- Redis;
- Celery;
- расширенная карточка товара;
- несколько изображений товара;
- SEO-поля.

### Этап 3 — масштабирование шаблона

- возможность быстро форкать проект под другой магазин;
- отключаемые модули;
- улучшенная система настроек;
- универсальные компоненты корзины и заказов;
- документация по запуску нового магазина.

---

## 25. Что не делать без отдельного решения

Не добавлять без необходимости:

1. DRF.
2. Vue/React.
3. Celery.
4. Сложную систему ролей.
5. Сложные промокоды.
6. Микросервисы.
7. Отдельную админ-панель вместо Django admin.
8. Многоуровневую систему складов.
9. Интеграцию с 1С.
10. Сложную аналитику.

Сначала простой рабочий магазин, потом расширение.

---

## 26. Краткое резюме решений

- Проект: интернет-магазин Asoti.
- Домен: `asotia.ru`.
- Backend: Django 5.2 LTS.
- Python: 3.12.x.
- БД: PostgreSQL 15.x.
- MVP: каталог, карточка товара, корзина, оформление заказа, админка.
- Корзина на MVP: Django sessions.
- Оплата: этап 2.
- Доставка API: этап 2.
- Celery: этап 2.
- Redis: можно подключить позже.
- Деплой: VPS + Nginx + Gunicorn.
- Секреты: только `.env`.
- Основная цель: простой рабочий магазин, который можно быстро запустить и развивать.
