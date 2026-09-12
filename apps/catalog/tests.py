import json
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import (
    Attribute,
    AttributeValue,
    Category,
    Collection,
    CollectionRule,
    Product,
    ProductAttributeValue,
)


class CatalogModelTests(TestCase):
    def test_unicode_slugs_pass_validation(self):
        category = Category(name="Консервы", slug="консервы")
        category.full_clean()
        category.save()

        product = Product(
            category=category,
            name="Филе индейки",
            slug="филе-индейки",
            price=Decimal("480.00"),
        )
        product.full_clean()

    def test_product_slug_is_unique_inside_category(self):
        first = Category.objects.create(name="Консервы", slug="canned")
        second = Category.objects.create(name="Заморозка", slug="frozen")
        Product.objects.create(
            category=first,
            name="Товар",
            slug="product",
            price=Decimal("100.00"),
        )
        Product.objects.create(
            category=second,
            name="Товар",
            slug="product",
            price=Decimal("100.00"),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.create(
                category=first,
                name="Дубликат",
                slug="product",
                price=Decimal("100.00"),
            )

    def test_stock_quantity_cannot_be_negative(self):
        category = Category.objects.create(name="Консервы", slug="canned")
        product = Product(
            category=category,
            name="Товар",
            slug="product",
            price=Decimal("100.00"),
            stock_quantity=-1,
        )

        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_attribute_value_is_unique_inside_attribute(self):
        attribute = Attribute.objects.create(name="Состав", slug="composition")
        AttributeValue.objects.create(
            attribute=attribute,
            name="Мясо",
            slug="meat",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            AttributeValue.objects.create(
                attribute=attribute,
                name="Мясо",
                slug="different",
            )

    def test_product_attribute_link_cannot_be_duplicated(self):
        category = Category.objects.create(name="Консервы", slug="canned")
        product = Product.objects.create(
            category=category,
            name="Товар",
            slug="product",
            price=Decimal("100.00"),
        )
        attribute = Attribute.objects.create(name="Состав", slug="composition")
        value = AttributeValue.objects.create(
            attribute=attribute,
            name="Мясо",
            slug="meat",
        )
        ProductAttributeValue.objects.create(
            product=product,
            attribute_value=value,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductAttributeValue.objects.create(
                product=product,
                attribute_value=value,
            )


class ProductImageTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.settings_override.enable()
        self.category = Category.objects.create(name="Фото", slug="photo")

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_image_is_oriented_resized_and_saved_as_jpeg(self):
        source = Image.new("RGB", (1600, 800), "red")
        exif = Image.Exif()
        exif[274] = 6
        image = self._uploaded_image("phone.jpg", source, "JPEG", exif=exif)

        product = self._create_product("phone", image)
        product.refresh_from_db()

        self.assertTrue(product.image.name.endswith(".jpg"))
        with Image.open(product.image.path) as stored:
            self.assertEqual(stored.format, "JPEG")
            self.assertEqual(stored.mode, "RGB")
            self.assertEqual(stored.size, (600, 1200))

    def test_replacing_image_removes_previous_file(self):
        first = self._uploaded_image(
            "first.png",
            Image.new("RGBA", (1400, 700), (255, 0, 0, 100)),
            "PNG",
        )
        product = self._create_product("replace", first)
        old_name = product.image.name

        product.image = self._uploaded_image(
            "second.png",
            Image.new("RGB", (800, 800), "blue"),
            "PNG",
        )
        product.save(update_fields=("image",))
        product.refresh_from_db()

        self.assertNotEqual(product.image.name, old_name)
        self.assertFalse(product.image.storage.exists(old_name))
        self.assertTrue(product.image.storage.exists(product.image.name))

    def _create_product(self, slug, image):
        return Product.objects.create(
            category=self.category,
            name=slug,
            slug=slug,
            description="",
            price=Decimal("100.00"),
            image=image,
        )

    @staticmethod
    def _uploaded_image(name, image, image_format, **save_kwargs):
        buffer = BytesIO()
        image.save(buffer, format=image_format, **save_kwargs)
        return SimpleUploadedFile(
            name,
            buffer.getvalue(),
            content_type=f"image/{image_format.lower()}",
        )


class ProductFilteringTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.canned = Category.objects.create(name="Консервы", slug="canned")
        cls.frozen = Category.objects.create(name="Заморозка", slug="frozen")
        cls.ingredient = Attribute.objects.create(
            name="Основной ингредиент",
            slug="main-ingredient",
        )
        cls.kind = Attribute.objects.create(
            name="Вид продукции",
            slug="product-type",
        )
        cls.chicken = AttributeValue.objects.create(
            attribute=cls.ingredient,
            name="Курица",
            slug="chicken",
        )
        cls.turkey = AttributeValue.objects.create(
            attribute=cls.ingredient,
            name="Индейка",
            slug="turkey",
        )
        cls.beef = AttributeValue.objects.create(
            attribute=cls.ingredient,
            name="Говядина",
            slug="beef",
        )
        cls.ready = AttributeValue.objects.create(
            attribute=cls.kind,
            name="Готовое блюдо",
            slug="ready-meal",
        )
        cls.stew = AttributeValue.objects.create(
            attribute=cls.kind,
            name="Тушёнка",
            slug="stew",
        )
        cls.chicken_ready = cls.make_product(
            "Куриный болоньезе", cls.canned, cls.chicken, cls.ready
        )
        cls.chicken_stew = cls.make_product(
            "Куриное филе", cls.canned, cls.chicken, cls.stew
        )
        cls.turkey_ready = cls.make_product(
            "Индейка с гречкой", cls.frozen, cls.turkey, cls.ready
        )
        cls.beef_ready = cls.make_product(
            "Гречка с говядиной", cls.canned, cls.beef, cls.ready
        )

    @classmethod
    def make_product(cls, name, category, *values):
        product = Product.objects.create(
            category=category,
            name=name,
            slug=name.lower().replace(" ", "-"),
            price=Decimal("100.00"),
            stock_quantity=5,
        )
        product.attribute_values.add(*values)
        return product

    def test_values_of_one_attribute_are_combined_with_or(self):
        products = Product.objects.public().filter_by_attribute_values(
            [self.chicken, self.turkey]
        )

        self.assertCountEqual(
            products,
            [self.chicken_ready, self.chicken_stew, self.turkey_ready],
        )

    def test_different_attributes_are_combined_with_and(self):
        products = Product.objects.public().filter_by_attribute_values(
            [self.chicken, self.ready]
        )

        self.assertEqual(list(products), [self.chicken_ready])

    def test_results_are_distinct_for_multiple_matching_values(self):
        self.chicken_ready.attribute_values.add(self.turkey)

        products = Product.objects.public().filter_by_attribute_values(
            [self.chicken, self.turkey]
        )

        self.assertEqual(products.filter(pk=self.chicken_ready.pk).count(), 1)

    def test_inactive_values_do_not_participate(self):
        self.chicken.is_active = False
        self.chicken.save(update_fields=("is_active",))

        products = Product.objects.public().filter_by_attribute_values(
            [self.chicken]
        )

        self.assertFalse(products.exists())

    def test_public_excludes_inactive_product_and_category(self):
        self.chicken_ready.is_active = False
        self.chicken_ready.save(update_fields=("is_active",))
        self.frozen.is_active = False
        self.frozen.save(update_fields=("is_active",))

        self.assertCountEqual(
            Product.objects.public(),
            [self.chicken_stew, self.beef_ready],
        )


class CollectionTests(ProductFilteringTests):
    def test_collection_uses_or_and_and_rules(self):
        collection = Collection.objects.create(
            name="Птица в готовых блюдах",
            slug="poultry-ready",
        )
        CollectionRule.objects.create(
            collection=collection,
            attribute_value=self.chicken,
        )
        CollectionRule.objects.create(
            collection=collection,
            attribute_value=self.turkey,
        )
        CollectionRule.objects.create(
            collection=collection,
            attribute_value=self.ready,
        )

        self.assertCountEqual(
            collection.products(),
            [self.chicken_ready, self.turkey_ready],
        )

    def test_collection_categories_are_combined_with_or(self):
        collection = Collection.objects.create(name="В двух разделах", slug="two")
        collection.categories.add(self.canned, self.frozen)

        self.assertCountEqual(
            collection.products(),
            [
                self.chicken_ready,
                self.chicken_stew,
                self.turkey_ready,
                self.beef_ready,
            ],
        )

    def test_collection_without_categories_uses_whole_catalog(self):
        collection = Collection.objects.create(name="Курица", slug="chicken")
        CollectionRule.objects.create(
            collection=collection,
            attribute_value=self.chicken,
        )

        self.assertCountEqual(
            collection.products(),
            [self.chicken_ready, self.chicken_stew],
        )

    def test_inactive_rule_does_not_make_collection_match_everything(self):
        collection = Collection.objects.create(name="Скрытое правило", slug="hidden")
        self.chicken.is_active = False
        self.chicken.save(update_fields=("is_active",))
        CollectionRule.objects.create(
            collection=collection,
            attribute_value=self.chicken,
        )

        self.assertFalse(collection.products().exists())


class CatalogViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Консервы", slug="консервы")
        cls.product = Product.objects.create(
            category=cls.category,
            name="Тушёнка говяжья",
            slug="тушёнка-говяжья",
            description="Тушёнка из говядины.",
            price=Decimal("399.90"),
            stock_quantity=2,
        )
        kind = Attribute.objects.create(
            name="Вид продукции",
            slug="product-type",
        )
        cls.stew = AttributeValue.objects.create(
            attribute=kind,
            name="Тушёнка",
            slug="stew",
        )
        cls.product.attribute_values.add(cls.stew)

    def test_catalog_lists_product_and_add_form(self):
        response = self.client.get(reverse("catalog:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertContains(response, reverse("cart:add", args=[self.product.pk]))

    def test_category_uses_database_attribute_filter(self):
        other = Product.objects.create(
            category=self.category,
            name="Соус",
            slug="sauce",
            price=Decimal("200.00"),
        )

        response = self.client.get(
            reverse("catalog:category", args=[self.category.slug]),
            {"attribute": self.stew.pk},
        )

        self.assertContains(response, self.product.name)
        self.assertNotContains(response, other.name)
        self.assertContains(response, "Вид продукции: Тушёнка")

    def test_catalog_exposes_active_attribute_groups(self):
        response = self.client.get(reverse("catalog:index"))

        self.assertContains(response, "Вид продукции")
        self.assertContains(response, "Тушёнка")
        self.assertEqual(response.context["filter_groups"][0].slug, "product-type")

    def test_search_and_unicode_detail_url(self):
        search_response = self.client.get(reverse("catalog:index"), {"q": "говяж"})
        detail_response = self.client.get(
            reverse(
                "catalog:product_detail",
                args=[self.category.slug, self.product.slug],
            )
        )

        self.assertContains(search_response, self.product.name)
        self.assertEqual(detail_response.status_code, 200)

    def test_inactive_product_is_not_public(self):
        self.product.is_active = False
        self.product.save(update_fields=("is_active",))

        response = self.client.get(
            reverse(
                "catalog:product_detail",
                args=[self.category.slug, self.product.slug],
            )
        )

        self.assertEqual(response.status_code, 404)


class CatalogSnapshotImportTests(TestCase):
    def test_imports_current_catalog_shape_and_is_repeatable(self):
        payload = [
            {
                "model": "catalog.product",
                "pk": 65,
                "fields": {
                    "name": "Говядина",
                    "slug": "говядина",
                    "description": "Описание",
                    "price": "480.00",
                    "old_price": None,
                    "weight_grams": 338,
                    "image": "products/говядина-1.jpg",
                    "stock_quantity": 12,
                    "storage_type": "canned",
                    "product_type": "stew",
                    "meat_type": "beef",
                    "is_active": True,
                    "created_at": "2026-01-01T10:00:00Z",
                    "updated_at": "2026-01-02T10:00:00Z",
                },
            },
            {
                "model": "catalog.product",
                "pk": 66,
                "fields": {
                    "name": "Ваш иммунитет",
                    "slug": "ваш-иммунитет",
                    "description": "",
                    "price": "300.00",
                    "old_price": None,
                    "weight_grams": None,
                    "image": "",
                    "stock_quantity": 2,
                    "storage_type": "other",
                    "product_type": "other",
                    "meat_type": "none",
                    "is_active": True,
                    "created_at": "2026-01-01T10:00:00Z",
                    "updated_at": "2026-01-02T10:00:00Z",
                },
            },
        ]
        with TemporaryDirectory() as directory:
            snapshot = Path(directory, "catalog.json")
            report = Path(directory, "report.md")
            snapshot.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )

            call_command("import_catalog_snapshot", snapshot, report=report)
            call_command("import_catalog_snapshot", snapshot, report=report)

            self.assertIn("Ваш иммунитет", report.read_text(encoding="utf-8"))

        product = Product.objects.get(pk=65)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(product.category.name, "Консервы")
        self.assertEqual(product.price, Decimal("480.00"))
        self.assertEqual(product.stock_quantity, 12)
        self.assertEqual(product.image.name, "products/говядина-1.jpg")
        self.assertTrue(
            product.attribute_values.filter(
                attribute__slug="main-ingredient",
                slug="beef",
            ).exists()
        )
        self.assertFalse(
            Product.objects.get(pk=66).attribute_values.filter(
                attribute__slug="features",
                slug="meat-free",
            ).exists()
        )
