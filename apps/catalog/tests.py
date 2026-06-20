from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product


class CategoryModelTests(TestCase):
    def test_create_category(self):
        category = Category.objects.create(name="Консервы", slug="konservy")

        self.assertEqual(category.name, "Консервы")
        self.assertTrue(category.is_active)

    def test_create_nested_category(self):
        parent = Category.objects.create(name="Консервы", slug="konservy")
        child = Category.objects.create(
            name="Тушёнка",
            slug="tushenka",
            parent=parent,
        )

        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())


class ProductModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Тушёнка",
            slug="tushenka",
        )

    def test_create_product(self):
        product = Product.objects.create(
            category=self.category,
            name="Тушёнка говяжья",
            slug="tushenka-govyazhya",
            description="Тушёнка из говядины.",
            price=Decimal("399.90"),
            storage_type=Product.StorageType.CANNED,
            product_type=Product.ProductType.STEW,
            meat_type=Product.MeatType.BEEF,
        )

        self.assertEqual(product.category, self.category)
        self.assertEqual(product.stock_status, Product.StockStatus.IN_STOCK)

    def test_product_string_representation(self):
        product = Product.objects.create(
            category=self.category,
            name="Паштет мясной",
            slug="pashtet-myasnoy",
            description="Мясной паштет.",
            price=Decimal("249.00"),
        )

        self.assertEqual(str(product), "Паштет мясной")

    def test_price_is_stored_as_decimal(self):
        product = Product.objects.create(
            category=self.category,
            name="Тушёнка свиная",
            slug="tushenka-svinaya",
            description="Тушёнка из свинины.",
            price=Decimal("349.50"),
        )
        product.refresh_from_db()

        self.assertIsInstance(product.price, Decimal)
        self.assertEqual(product.price, Decimal("349.50"))

    def test_sync_stock_status(self):
        product = Product(
            category=self.category,
            name="Товар",
            slug="tovar",
            description="",
            price=Decimal("100.00"),
            stock_quantity=5,
            stock_status=Product.StockStatus.OUT_OF_STOCK,
        )

        product.sync_stock_status()
        self.assertEqual(product.stock_status, Product.StockStatus.IN_STOCK)

        product.stock_quantity = 0
        product.sync_stock_status()
        self.assertEqual(product.stock_status, Product.StockStatus.OUT_OF_STOCK)


class CatalogViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Тушёнка",
            slug="tushenka",
        )
        cls.product = Product.objects.create(
            category=cls.category,
            name="Тушёнка говяжья",
            slug="tushenka-govyazhya",
            description="Тушёнка из говядины.",
            price=Decimal("399.90"),
        )

    def test_catalog_uses_template_and_lists_product(self):
        response = self.client.get(reverse("catalog:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/index.html")
        self.assertContains(response, self.product.name)

    def test_catalog_has_add_to_cart_form_for_available_product(self):
        self.product.stock_quantity = 2
        self.product.save(update_fields=("stock_quantity",))

        response = self.client.get(reverse("catalog:index"))

        self.assertContains(
            response,
            reverse("cart:add", args=[self.product.pk]),
        )

    def test_category_page_filters_products(self):
        other_category = Category.objects.create(
            name="Рыба",
            slug="fish",
        )
        Product.objects.create(
            category=other_category,
            name="Скумбрия",
            slug="skumbriya",
            description="",
            price=Decimal("200.00"),
        )

        response = self.client.get(
            reverse("catalog:category", args=[self.category.slug])
        )

        self.assertContains(response, self.product.name)
        self.assertNotContains(response, "Скумбрия")

    def test_parent_category_page_lists_child_products(self):
        parent = Category.objects.create(
            name="Консервы",
            slug="konservy",
        )
        self.category.parent = parent
        self.category.save(update_fields=("parent",))

        response = self.client.get(
            reverse("catalog:category", args=[parent.slug])
        )

        self.assertContains(response, self.product.name)

    def test_product_detail_uses_category_and_product_slugs(self):
        response = self.client.get(
            reverse(
                "catalog:product_detail",
                args=[self.category.slug, self.product.slug],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/product_detail.html")
        self.assertContains(response, self.product.name)

    def test_unicode_slugs_are_supported(self):
        category = Category.objects.create(
            name="Консервы",
            slug="консервы",
        )
        product = Product.objects.create(
            category=category,
            name="Говядина",
            slug="говядина",
            description="",
            price=Decimal("480.00"),
        )

        category_response = self.client.get(
            reverse("catalog:category", args=[category.slug])
        )
        product_response = self.client.get(
            reverse(
                "catalog:product_detail",
                args=[category.slug, product.slug],
            )
        )

        self.assertEqual(category_response.status_code, 200)
        self.assertContains(category_response, product.name)
        self.assertEqual(product_response.status_code, 200)

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


class LegacyCatalogImportTests(TestCase):
    @patch(
        "apps.catalog.management.commands.import_legacy_catalog."
        "Command._read_legacy_data"
    )
    def test_imports_legacy_catalog(self, read_legacy_data):
        read_legacy_data.return_value = (
            [
                {
                    "id": 1,
                    "name": "🍖🥫 Мясные консервы",
                    "description": "Мясные консервы",
                    "is_active": True,
                },
            ],
            [
                {
                    "id": 10,
                    "name": "Говядина",
                    "description": "Тушёная говядина",
                    "price": 480.0,
                    "type_product": "meat",
                    "image_url": "",
                    "stock": 12,
                    "category_id": 1,
                    "is_active": True,
                },
            ],
        )

        call_command("import_legacy_catalog", skip_images=True)

        product = Product.objects.get()
        self.assertEqual(product.category.name, "Тушёнка")
        self.assertEqual(product.category.parent.name, "Консервы")
        self.assertEqual(product.price, Decimal("480.00"))
        self.assertEqual(product.stock_quantity, 12)
        self.assertEqual(product.stock_status, Product.StockStatus.IN_STOCK)
        self.assertEqual(product.storage_type, Product.StorageType.CANNED)
        self.assertEqual(product.product_type, Product.ProductType.STEW)
        self.assertEqual(product.meat_type, Product.MeatType.BEEF)

    @patch(
        "apps.catalog.management.commands.import_legacy_catalog."
        "Command._read_legacy_data"
    )
    def test_import_is_repeatable(self, read_legacy_data):
        read_legacy_data.return_value = (
            [
                {
                    "id": 9,
                    "name": "Другое",
                    "description": "",
                    "is_active": True,
                },
            ],
            [
                {
                    "id": 64,
                    "name": "Соус",
                    "description": "",
                    "price": 200.0,
                    "type_product": None,
                    "image_url": "",
                    "stock": 0,
                    "category_id": 9,
                    "is_active": True,
                },
            ],
        )

        call_command("import_legacy_catalog", skip_images=True)
        call_command("import_legacy_catalog", skip_images=True)

        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Product.objects.count(), 1)
