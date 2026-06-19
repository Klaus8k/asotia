from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

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
