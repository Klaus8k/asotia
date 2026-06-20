import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Product


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новый"
        PROCESSING = "processing", "В обработке"
        COMPLETED = "completed", "Выполнен"
        CANCELED = "canceled", "Отменён"

    public_id = models.UUIDField(
        "публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        related_name="orders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    customer_name = models.CharField("имя покупателя", max_length=150)
    phone = models.CharField("телефон", max_length=30)
    email = models.EmailField("email", blank=True)
    delivery_address = models.CharField("адрес доставки", max_length=500)
    comment = models.TextField("комментарий", blank=True)
    status = models.CharField(
        "статус",
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    total_price = models.DecimalField(
        "итоговая сумма",
        max_digits=12,
        decimal_places=2,
    )
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("дата обновления", auto_now=True)

    class Meta:
        verbose_name = "заказ"
        verbose_name_plural = "заказы"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Заказ №{self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="заказ",
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        verbose_name="товар",
        related_name="order_items",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    product_name = models.CharField("название товара", max_length=255)
    product_price = models.DecimalField(
        "цена товара",
        max_digits=10,
        decimal_places=2,
    )
    quantity = models.PositiveIntegerField("количество")
    total_price = models.DecimalField(
        "сумма",
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        verbose_name = "позиция заказа"
        verbose_name_plural = "позиции заказа"
        ordering = ("pk",)

    def __str__(self) -> str:
        return f"{self.product_name} × {self.quantity}"
