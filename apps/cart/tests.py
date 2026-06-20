from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product

from .cart import CART_SESSION_ID


class CartViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Консервы",
            slug="konservy",
        )
        cls.product = Product.objects.create(
            category=cls.category,
            name="Тушёнка говяжья",
            slug="tushenka-govyazhya",
            description="",
            price=Decimal("325.00"),
            stock_quantity=3,
        )

    def test_cart_detail_uses_template(self):
        response = self.client.get(reverse("cart:detail"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cart/detail.html")
        self.assertContains(response, "Корзина пока пуста")

    def test_add_product_to_session_cart(self):
        response = self.client.post(
            reverse("cart:add", args=[self.product.pk]),
            {"quantity": 2},
        )

        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(
            self.client.session[CART_SESSION_ID],
            {str(self.product.pk): 2},
        )

    def test_add_product_uses_safe_next_url(self):
        catalog_url = reverse("catalog:index")

        response = self.client.post(
            reverse("cart:add", args=[self.product.pk]),
            {"quantity": 1, "next": catalog_url},
        )

        self.assertRedirects(response, catalog_url)

    def test_add_product_rejects_external_next_url(self):
        response = self.client.post(
            reverse("cart:add", args=[self.product.pk]),
            {"quantity": 1, "next": "https://example.com/"},
        )

        self.assertRedirects(response, reverse("cart:detail"))

    def test_add_quantity_is_limited_by_stock(self):
        self.client.post(
            reverse("cart:add", args=[self.product.pk]),
            {"quantity": 20},
        )

        self.assertEqual(
            self.client.session[CART_SESSION_ID],
            {str(self.product.pk): self.product.stock_quantity},
        )

    def test_update_product_quantity(self):
        session = self.client.session
        session[CART_SESSION_ID] = {str(self.product.pk): 1}
        session.save()

        response = self.client.post(
            reverse("cart:update", args=[self.product.pk]),
            {"quantity": 2},
        )

        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(
            self.client.session[CART_SESSION_ID],
            {str(self.product.pk): 2},
        )

    def test_remove_product(self):
        session = self.client.session
        session[CART_SESSION_ID] = {str(self.product.pk): 1}
        session.save()

        response = self.client.post(
            reverse("cart:remove", args=[self.product.pk]),
        )

        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(self.client.session[CART_SESSION_ID], {})

    def test_cart_detail_calculates_total(self):
        session = self.client.session
        session[CART_SESSION_ID] = {str(self.product.pk): 2}
        session.save()

        response = self.client.get(reverse("cart:detail"))

        self.assertContains(response, self.product.name)
        self.assertEqual(response.context["cart_total"], Decimal("650.00"))

    def test_unavailable_product_is_removed_from_cart(self):
        session = self.client.session
        session[CART_SESSION_ID] = {str(self.product.pk): 1}
        session.save()
        self.product.is_active = False
        self.product.save(update_fields=("is_active",))

        response = self.client.get(reverse("cart:detail"))

        self.assertContains(response, "Корзина пока пуста")
        self.assertEqual(self.client.session[CART_SESSION_ID], {})

    def test_cart_mutations_require_post(self):
        urls = [
            reverse("cart:add", args=[self.product.pk]),
            reverse("cart:update", args=[self.product.pk]),
            reverse("cart:remove", args=[self.product.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 405)

    def test_out_of_stock_product_cannot_be_added(self):
        self.product.stock_quantity = 0
        self.product.save(update_fields=("stock_quantity",))

        response = self.client.post(
            reverse("cart:add", args=[self.product.pk]),
            {"quantity": 1},
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotIn(CART_SESSION_ID, self.client.session)
