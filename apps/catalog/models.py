from collections import defaultdict
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps


PRODUCT_IMAGE_MAX_SIZE = (1200, 1200)
PRODUCT_IMAGE_QUALITY = 82


class Category(models.Model):
    name = models.CharField("название", max_length=255)
    slug = models.SlugField(
        "слаг", max_length=255, allow_unicode=True, unique=True
    )
    description = models.TextField("описание", blank=True)
    image = models.ImageField("изображение", upload_to="categories/", blank=True)
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

class Attribute(models.Model):
    name = models.CharField("название", max_length=255)
    slug = models.SlugField(
        "слаг", max_length=255, allow_unicode=True, unique=True
    )
    is_active = models.BooleanField("активна", default=True)
    sort_order = models.PositiveIntegerField("порядок сортировки", default=0)

    class Meta:
        verbose_name = "характеристика"
        verbose_name_plural = "характеристики"
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(
        Attribute,
        verbose_name="характеристика",
        related_name="values",
        on_delete=models.PROTECT,
    )
    name = models.CharField("значение", max_length=255)
    slug = models.SlugField("слаг", max_length=255, allow_unicode=True)
    is_active = models.BooleanField("активно", default=True)
    sort_order = models.PositiveIntegerField("порядок сортировки", default=0)

    class Meta:
        verbose_name = "значение характеристики"
        verbose_name_plural = "значения характеристик"
        ordering = ("attribute", "sort_order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("attribute", "name"),
                name="unique_attribute_value_name",
            ),
            models.UniqueConstraint(
                fields=("attribute", "slug"),
                name="unique_attribute_value_slug",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.attribute}: {self.name}"


class ProductQuerySet(models.QuerySet):
    def public(self):
        return self.filter(is_active=True, category__is_active=True)

    def filter_by_attribute_values(
        self,
        values: Iterable[AttributeValue | int],
    ):
        requested_ids = [
            value.pk if isinstance(value, AttributeValue) else value
            for value in values
        ]
        if not requested_ids:
            return self

        active_values = AttributeValue.objects.filter(
            pk__in=requested_ids,
            is_active=True,
            attribute__is_active=True,
        ).values_list("attribute_id", "pk")
        ids_by_attribute: dict[int, list[int]] = defaultdict(list)
        for attribute_id, value_id in active_values:
            ids_by_attribute[attribute_id].append(value_id)

        if not ids_by_attribute:
            return self.none()

        queryset = self
        for value_ids in ids_by_attribute.values():
            queryset = queryset.filter(attribute_values__in=value_ids)
        return queryset.distinct()


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        verbose_name="категория",
        related_name="products",
        on_delete=models.PROTECT,
    )
    name = models.CharField("название", max_length=255)
    slug = models.SlugField("слаг", max_length=255, allow_unicode=True)
    description = models.TextField("описание", blank=True)
    price = models.DecimalField("цена", max_digits=10, decimal_places=2)
    old_price = models.DecimalField(
        "старая цена",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    weight_grams = models.PositiveIntegerField(
        "вес в граммах", null=True, blank=True
    )
    volume_ml = models.PositiveIntegerField(
        "объём в миллилитрах", null=True, blank=True
    )
    units_count = models.PositiveIntegerField(
        "количество единиц", null=True, blank=True
    )
    image = models.ImageField("изображение", upload_to="products/", blank=True)
    stock_quantity = models.PositiveIntegerField("остаток", default=0)
    is_active = models.BooleanField("активен", default=True)
    is_new = models.BooleanField("новинка", default=False)
    attribute_values = models.ManyToManyField(
        AttributeValue,
        verbose_name="значения характеристик",
        related_name="products",
        through="ProductAttributeValue",
        blank=True,
    )
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("дата обновления", auto_now=True)

    objects = ProductQuerySet.as_manager()

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


    def save(self, *args, **kwargs) -> None:
        has_uploaded_image = bool(self.image and not self.image._committed)
        old_image_name = None
        if self.pk:
            old_image_name = (
                type(self)
                .objects.filter(pk=self.pk)
                .values_list("image", flat=True)
                .first()
            )

        super().save(*args, **kwargs)

        if self.image and has_uploaded_image and self.image.name != old_image_name:
            resized_name = self._resize_product_image()
            if old_image_name and old_image_name != resized_name:
                self.image.storage.delete(old_image_name)

    def _resize_product_image(self) -> str:
        source_name = self.image.name
        try:
            self.image.open("rb")
            with Image.open(self.image) as source:
                image = ImageOps.exif_transpose(source)
                image.thumbnail(PRODUCT_IMAGE_MAX_SIZE, Image.Resampling.LANCZOS)

                if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                    image = image.convert("RGBA")
                    background = Image.new("RGB", image.size, "white")
                    background.paste(image, mask=image.getchannel("A"))
                    image = background
                elif image.mode != "RGB":
                    image = image.convert("RGB")

                buffer = BytesIO()
                image.save(
                    buffer,
                    format="JPEG",
                    quality=PRODUCT_IMAGE_QUALITY,
                    optimize=True,
                    progressive=True,
                )
        finally:
            self.image.close()

        image_path = Path(self.image.name)
        resized_name = str(image_path.with_suffix(".jpg"))
        saved_name = self.image.storage.save(
            resized_name,
            ContentFile(buffer.getvalue()),
        )
        type(self).objects.filter(pk=self.pk).update(image=saved_name)
        self.image.name = saved_name

        if source_name != saved_name:
            self.image.storage.delete(source_name)

        return saved_name


class ProductAttributeValue(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name="товар",
        related_name="attribute_assignments",
        on_delete=models.CASCADE,
    )
    attribute_value = models.ForeignKey(
        AttributeValue,
        verbose_name="значение характеристики",
        related_name="product_assignments",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "характеристика товара"
        verbose_name_plural = "характеристики товара"
        ordering = ("attribute_value__attribute", "attribute_value")
        constraints = [
            models.UniqueConstraint(
                fields=("product", "attribute_value"),
                name="unique_product_attribute_value",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product}: {self.attribute_value}"


class Collection(models.Model):
    name = models.CharField("название", max_length=255)
    slug = models.SlugField(
        "слаг", max_length=255, allow_unicode=True, unique=True
    )
    description = models.TextField("описание", blank=True)
    image = models.ImageField("изображение", upload_to="collections/", blank=True)
    is_active = models.BooleanField("активна", default=True)
    sort_order = models.PositiveIntegerField("порядок сортировки", default=0)
    categories = models.ManyToManyField(
        Category,
        verbose_name="категории",
        related_name="collections",
        blank=True,
    )
    attribute_values = models.ManyToManyField(
        AttributeValue,
        verbose_name="правила по характеристикам",
        related_name="collections",
        through="CollectionRule",
        blank=True,
    )
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("дата обновления", auto_now=True)

    class Meta:
        verbose_name = "подборка"
        verbose_name_plural = "подборки"
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name

    def products(self):
        if not self.is_active:
            return Product.objects.none()

        products = Product.objects.public()
        if self.categories.exists():
            category_ids = self.categories.filter(is_active=True).values_list(
                "pk", flat=True
            )
            products = products.filter(category_id__in=category_ids)

        if self.rules.exists():
            value_ids = self.rules.filter(
                attribute_value__is_active=True,
                attribute_value__attribute__is_active=True,
            ).values_list("attribute_value_id", flat=True)
            if not value_ids.exists():
                return products.none()
            products = products.filter_by_attribute_values(value_ids)
        return products


class CollectionRule(models.Model):
    collection = models.ForeignKey(
        Collection,
        verbose_name="подборка",
        related_name="rules",
        on_delete=models.CASCADE,
    )
    attribute_value = models.ForeignKey(
        AttributeValue,
        verbose_name="значение характеристики",
        related_name="collection_rules",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "правило подборки"
        verbose_name_plural = "правила подборок"
        ordering = ("attribute_value__attribute", "attribute_value")
        constraints = [
            models.UniqueConstraint(
                fields=("collection", "attribute_value"),
                name="unique_collection_attribute_value",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.collection}: {self.attribute_value}"
