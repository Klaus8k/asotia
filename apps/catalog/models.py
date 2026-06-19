from django.db import models


class Category(models.Model):
    name = models.CharField("название", max_length=255)
    slug = models.SlugField("слаг", max_length=255)
    parent = models.ForeignKey(
        "self",
        verbose_name="родительская категория",
        related_name="children",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    description = models.TextField("описание", blank=True)
    is_active = models.BooleanField("активна", default=True)
    sort_order = models.PositiveIntegerField("порядок сортировки", default=0)
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("дата обновления", auto_now=True)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    class StorageType(models.TextChoices):
        CANNED = "canned", "Консервы"
        FROZEN = "frozen", "Заморозка"
        OTHER = "other", "Другое"

    class ProductType(models.TextChoices):
        STEW = "stew", "Тушёнка"
        PATE = "pate", "Паштет"
        FISH = "fish", "Рыбные продукты"
        VEGETABLES = "vegetables", "Овощные продукты"
        READY_MEAL = "ready_meal", "Готовое блюдо"
        SEMI_FINISHED = "semi_finished", "Полуфабрикат"
        MEAT = "meat", "Мясо"
        OTHER = "other", "Другое"

    class MeatType(models.TextChoices):
        BEEF = "beef", "Говядина"
        PORK = "pork", "Свинина"
        CHICKEN = "chicken", "Курица"
        TURKEY = "turkey", "Индейка"
        LAMB = "lamb", "Баранина"
        MIXED = "mixed", "Смешанное"
        NONE = "none", "Не указано"

    class StockStatus(models.TextChoices):
        IN_STOCK = "in_stock", "В наличии"
        OUT_OF_STOCK = "out_of_stock", "Нет в наличии"
        ON_ORDER = "on_order", "Под заказ"

    category = models.ForeignKey(
        Category,
        verbose_name="категория",
        related_name="products",
        on_delete=models.PROTECT,
    )
    name = models.CharField("название", max_length=255)
    slug = models.SlugField("слаг", max_length=255)
    description = models.TextField("описание")
    price = models.DecimalField("цена", max_digits=10, decimal_places=2)
    old_price = models.DecimalField(
        "старая цена",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    weight_grams = models.PositiveIntegerField(
        "вес в граммах",
        null=True,
        blank=True,
    )
    image = models.ImageField(
        "изображение",
        upload_to="products/",
        blank=True,
    )
    stock_quantity = models.PositiveIntegerField("остаток", default=0)
    storage_type = models.CharField(
        "тип хранения",
        max_length=10,
        choices=StorageType.choices,
        default=StorageType.OTHER,
    )
    product_type = models.CharField(
        "тип продукта",
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.OTHER,
    )
    meat_type = models.CharField(
        "вид мяса",
        max_length=10,
        choices=MeatType.choices,
        default=MeatType.NONE,
        blank=True,
    )
    is_active = models.BooleanField("активен", default=True)
    is_featured = models.BooleanField("рекомендуемый", default=False)
    stock_status = models.CharField(
        "наличие",
        max_length=15,
        choices=StockStatus.choices,
        default=StockStatus.IN_STOCK,
    )
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("дата обновления", auto_now=True)

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ("category", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("category", "slug"),
                name="unique_product_slug_per_category",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def sync_stock_status(self) -> None:
        if self.stock_quantity > 0:
            self.stock_status = self.StockStatus.IN_STOCK
        else:
            self.stock_status = self.StockStatus.OUT_OF_STOCK
