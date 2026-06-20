from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order, OrderItem


User = get_user_model()


class AccountViewTests(TestCase):
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "ivan",
                "first_name": "Иван",
                "email": "ivan@example.com",
                "password1": "StrongPass-2026",
                "password2": "StrongPass-2026",
            },
        )

        self.assertRedirects(response, reverse("accounts:cabinet"))
        user = User.objects.get(username="ivan")
        self.assertEqual(user.email, "ivan@example.com")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_registration_rejects_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="user@example.com",
            password="StrongPass-2026",
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new-user",
                "first_name": "Новый",
                "email": "USER@example.com",
                "password1": "StrongPass-2026",
                "password2": "StrongPass-2026",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Пользователь с таким email уже зарегистрирован.",
        )
        self.assertEqual(User.objects.count(), 1)

    def test_login_uses_custom_template(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_cabinet_requires_authentication(self):
        response = self.client.get(reverse("accounts:cabinet"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:cabinet')}",
        )

    def test_cabinet_lists_only_current_user_orders(self):
        user = User.objects.create_user(
            username="ivan",
            password="StrongPass-2026",
        )
        other_user = User.objects.create_user(
            username="anna",
            password="StrongPass-2026",
        )
        own_order = self._create_order(user=user, name="Свой заказ")
        other_order = self._create_order(user=other_user, name="Чужой заказ")
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:cabinet"))

        self.assertContains(response, own_order.items.get().product_name)
        self.assertNotContains(response, other_order.items.get().product_name)

    def test_profile_edit_updates_user(self):
        user = User.objects.create_user(
            username="ivan",
            email="old@example.com",
            password="StrongPass-2026",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "Иван",
                "last_name": "Петров",
                "email": "new@example.com",
            },
        )

        self.assertRedirects(response, reverse("accounts:cabinet"))
        user.refresh_from_db()
        self.assertEqual(user.get_full_name(), "Иван Петров")
        self.assertEqual(user.email, "new@example.com")

    def test_logout_requires_post_and_ends_session(self):
        user = User.objects.create_user(
            username="ivan",
            password="StrongPass-2026",
        )
        self.client.force_login(user)

        get_response = self.client.get(reverse("accounts:logout"))
        post_response = self.client.post(reverse("accounts:logout"))

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(post_response, reverse("pages:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def _create_order(self, *, user, name):
        order = Order.objects.create(
            user=user,
            customer_name=user.username,
            phone="+79991234567",
            delivery_address="Москва",
            total_price=Decimal("100.00"),
        )
        OrderItem.objects.create(
            order=order,
            product_name=name,
            product_price=Decimal("100.00"),
            quantity=1,
            total_price=Decimal("100.00"),
        )
        return order
