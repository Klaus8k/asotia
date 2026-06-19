from django.test import TestCase
from django.urls import reverse


class PageViewTests(TestCase):
    def test_home_uses_template(self):
        response = self.client.get(reverse("pages:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/home.html")
        self.assertContains(response, "Перейти в каталог")

    def test_information_page_uses_shared_template(self):
        response = self.client.get(reverse("pages:about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/simple.html")
        self.assertContains(response, "О нас")
