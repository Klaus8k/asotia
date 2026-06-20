from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product


class PageViewTests(TestCase):
    def test_home_uses_template(self):
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertContains(response, "Перейти в каталог")

    def test_home_links_only_selected_categories(self):
        canned = Category.objects.create(name="Консервы", slug="konservy")
        frozen = Category.objects.create(name="Заморозка", slug="zamorozka")
        stew = Category.objects.create(
            parent=canned,
            name="Тушёнка",
            slug="tushenka",
        )
        pate = Category.objects.create(
            parent=canned,
            name="Паштеты",
            slug="pashtety",
        )
        hidden = Category.objects.create(
            name="Пустая категория",
            slug="empty",
        )

        response = self.client.get(reverse("pages:home"))

        self.assertContains(response, reverse("catalog:index"))
        for category in [canned, frozen, stew, pate]:
            self.assertContains(
                response,
                reverse("catalog:category", args=[category.slug]),
            )
            self.assertContains(response, category.name)
        self.assertNotContains(response, hidden.name)
        self.assertNotContains(response, "Консервы →")

    def test_home_uses_products_from_database(self):
        category = Category.objects.create(
            name="Тушёнка",
            slug="tushenka",
        )
        product = Product.objects.create(
            category=category,
            name="Тушёнка говяжья из БД",
            slug="tushenka-govyazhya",
            description="",
            price="325.00",
            is_featured=True,
        )

        response = self.client.get(reverse("pages:home"))

        self.assertContains(response, product.name)
        self.assertContains(response, "325,00 ₽")
        self.assertContains(
            response,
            reverse(
                "catalog:product_detail",
                args=[category.slug, product.slug],
            ),
        )

    def test_information_page_uses_shared_template(self):
        response = self.client.get(reverse("pages:about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/simple.html")
        self.assertContains(response, "О нас")
