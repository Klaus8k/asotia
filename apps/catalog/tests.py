from decimal import Decimal

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
