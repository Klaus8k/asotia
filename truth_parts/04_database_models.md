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
