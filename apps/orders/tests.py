from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth import get_user_model

from apps.cart.cart import CART_SESSION_ID, Cart
from apps.catalog.models import Category, Product

from .models import Order, OrderItem
from .services import CheckoutError, create_order_from_cart


User = get_user_model()


class CheckoutViewTests(TestCase):
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
            description="",
            price=Decimal("325.00"),
            stock_quantity=5,
        )

    def setUp(self):
        session = self.client.session
        session[CART_SESSION_ID] = {str(self.product.pk): 2}
        session.save()

    def test_checkout_uses_template_and_shows_cart(self):
        response = self.client.get(reverse("orders:checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/checkout.html")
        self.assertContains(response, self.product.name)
        self.assertContains(response, "650,00")

    def test_empty_cart_redirects_to_cart(self):
        session = self.client.session
        session[CART_SESSION_ID] = {}
        session.save()

        response = self.client.get(reverse("orders:checkout"))

        self.assertRedirects(response, reverse("cart:detail"))

    def test_guest_checkout_creates_order_and_items(self):
        response = self.client.post(
            reverse("orders:checkout"),
            {
                "customer_name": "Иван Петров",
                "phone": "+7 999 123-45-67",
                "email": "ivan@example.com",
                "delivery_address": "Москва, ул. Лесная, д. 10",
                "comment": "Позвонить перед доставкой",
            },
        )

        order = Order.objects.get()
        self.assertRedirects(
            response,
            reverse("orders:success", args=[order.public_id]),
        )
        self.assertEqual(order.customer_name, "Иван Петров")
        self.assertEqual(order.total_price, Decimal("650.00"))
        self.assertEqual(order.status, Order.Status.NEW)

        item = order.items.get()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.product_name, self.product.name)
        self.assertEqual(item.product_price, Decimal("325.00"))
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.total_price, Decimal("650.00"))

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertNotIn(CART_SESSION_ID, self.client.session)

    def test_authenticated_checkout_links_order_to_user(self):
        user = User.objects.create_user(
            username="ivan",
            first_name="Иван",
            email="ivan@example.com",
            password="StrongPass-2026",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("orders:checkout"),
            {
                "customer_name": "Иван",
                "phone": "+7 999 123-45-67",
                "email": "ivan@example.com",
                "delivery_address": "Москва",
                "comment": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.get().user, user)

    def test_checkout_prefills_authenticated_user_data(self):
        user = User.objects.create_user(
            username="ivan",
            first_name="Иван",
            last_name="Петров",
            email="ivan@example.com",
            password="StrongPass-2026",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("orders:checkout"))

        self.assertEqual(
            response.context["form"].initial["customer_name"],
            "Иван Петров",
        )
        self.assertEqual(
            response.context["form"].initial["email"],
            "ivan@example.com",
        )

    def test_invalid_checkout_does_not_create_order(self):
        response = self.client.post(
            reverse("orders:checkout"),
            {
                "customer_name": "",
                "phone": "123",
                "delivery_address": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Введите корректный номер телефона.")
        self.assertFalse(Order.objects.exists())
        self.assertIn(CART_SESSION_ID, self.client.session)

    def test_success_page_uses_public_id_and_lists_snapshot(self):
        order = Order.objects.create(
            customer_name="Анна",
            phone="+79991234567",
            delivery_address="Москва",
            total_price=Decimal("325.00"),
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name="Снимок товара",
            product_price=Decimal("325.00"),
            quantity=1,
            total_price=Decimal("325.00"),
        )

        response = self.client.get(reverse("orders:success", args=[order.public_id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "orders/success.html")
        self.assertContains(response, "Снимок товара")


class CheckoutServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Консервы",
            slug="konservy",
        )
        cls.product = Product.objects.create(
            category=cls.category,
            name="Паштет",
            slug="pashtet",
            description="",
            price=Decimal("145.00"),
            stock_quantity=2,
        )

    def test_stock_change_rolls_back_order_creation(self):
        request = self._request_with_session()
        cart = Cart(request)
        cart.add(self.product, quantity=2)
        cart_items = list(cart)

        self.product.stock_quantity = 1
        self.product.save(update_fields=("stock_quantity",))

        with self.assertRaises(CheckoutError):
            create_order_from_cart(
                order=Order(
                    customer_name="Иван",
                    phone="+79991234567",
                    delivery_address="Москва",
                ),
                cart=cart,
                cart_items=cart_items,
            )

        self.assertFalse(Order.objects.exists())
        self.assertFalse(OrderItem.objects.exists())
        self.assertEqual(cart.cart, {str(self.product.pk): 2})

    def test_order_item_snapshot_survives_product_changes(self):
        request = self._request_with_session()
        cart = Cart(request)
        cart.add(self.product)

        order = create_order_from_cart(
            order=Order(
                customer_name="Иван",
                phone="+79991234567",
                delivery_address="Москва",
            ),
            cart=cart,
            cart_items=list(cart),
        )
        item = order.items.get()

        self.product.name = "Новое название"
        self.product.price = Decimal("999.00")
        self.product.save(update_fields=("name", "price"))
        item.refresh_from_db()

        self.assertEqual(item.product_name, "Паштет")
        self.assertEqual(item.product_price, Decimal("145.00"))

    def _request_with_session(self):
        request = RequestFactory().get("/")
        middleware = SessionMiddleware(lambda current_request: None)
        middleware.process_request(request)
        request.session.save()
        return request
