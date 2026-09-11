from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Category, Collection, Product


class PageViewTests(TestCase):
    def test_home_uses_template(self):
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertContains(response, "Выбрать продукты")

    def test_home_links_all_active_categories(self):
        canned = Category.objects.create(name="Консервы", slug="konservy")
        frozen = Category.objects.create(name="Заморозка", slug="zamorozka")
        hidden = Category.objects.create(
            name="Пустая категория",
            slug="empty",
            is_active=False,
        )

        response = self.client.get(reverse("pages:home"))

        self.assertContains(response, reverse("catalog:index"))
        for category in [canned, frozen]:
            self.assertContains(
                response,
                reverse("catalog:category", args=[category.slug]),
            )
            self.assertContains(response, category.name)
        self.assertNotContains(response, hidden.name)

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
            is_new=True,
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

    def test_home_prioritizes_active_collection_sections(self):
        category = Category.objects.create(name="Консервы", slug="canned")
        Product.objects.create(
            category=category,
            name="Филе для подборки",
            slug="collection-product",
            price="325.00",
        )
        collection = Collection.objects.create(
            name="Выбор редакции",
            slug="editors-choice",
            description="Отдельная подборка из админки.",
        )
        collection.categories.add(category)

        response = self.client.get(reverse("pages:home"))

        self.assertContains(response, collection.name)
        self.assertContains(response, collection.description)
        self.assertEqual(response.context["showcase_sections"][0]["title"], collection.name)

    def test_information_page_uses_shared_template(self):
        response = self.client.get(reverse("pages:about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/simple.html")
        self.assertContains(response, "О нас")
