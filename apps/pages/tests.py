from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Product


class PageViewTests(TestCase):
    def test_home_uses_template(self):
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertContains(response, "Перейти в каталог")

    def test_home_links_categories_with_active_products(self):
        category = Category.objects.create(
            name="Паштеты",
            slug="pashtety",
        )
        empty_category = Category.objects.create(
            name="Пустая категория",
            slug="empty",
        )
        Product.objects.create(
            category=category,
            name="Паштет мясной",
            slug="pashtet-myasnoy",
            description="",
            price="300.00",
        )

        response = self.client.get(reverse("pages:home"))

        self.assertContains(
            response,
            reverse("catalog:category", args=[category.slug]),
        )
        self.assertContains(response, category.name)
        self.assertNotContains(response, empty_category.name)

    def test_information_page_uses_shared_template(self):
        response = self.client.get(reverse("pages:about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/simple.html")
        self.assertContains(response, "О нас")
