from django.db.models import Case, IntegerField, Value, When
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.cart.cart import attach_cart_quantities
from apps.catalog.models import Category, Product


def render_information_page(
    request: HttpRequest,
    *,
    title: str,
    content_template: str,
) -> HttpResponse:
    return render(
        request,
        "pages/simple.html",
        {
            "title": title,
            "content_template": content_template,
        },
    )


def home(request: HttpRequest) -> HttpResponse:
    category_names = ["Консервы", "Заморозка", "Тушёнка", "Паштеты"]
    categories = (
        Category.objects.filter(
            is_active=True,
            name__in=category_names,
        )
        .annotate(
            home_order=Case(
                *[
                    When(name=name, then=Value(position))
                    for position, name in enumerate(category_names)
                ],
                output_field=IntegerField(),
            )
        )
        .order_by("home_order")
    )
    popular_products = attach_cart_quantities(
        request,
        Product.objects.filter(
            is_active=True,
            category__is_active=True,
        )
        .select_related("category")
        .order_by("-is_featured", "-created_at")[:4],
    )
    return render(
        request,
        "pages/home.html",
        {
            "categories": categories,
            "popular_products": popular_products,
        },
    )


def about(request: HttpRequest) -> HttpResponse:
    return render_information_page(
        request,
        title="О нас",
        content_template="pages/information/about.html",
    )


def contacts(request: HttpRequest) -> HttpResponse:
    return render_information_page(
        request,
        title="Контакты",
        content_template="pages/information/contacts.html",
    )


def delivery(request: HttpRequest) -> HttpResponse:
    return render_information_page(
        request,
        title="Доставка и оплата",
        content_template="pages/information/delivery.html",
    )


def privacy(request: HttpRequest) -> HttpResponse:
    return render_information_page(
        request,
        title="Политика конфиденциальности",
        content_template="pages/information/privacy.html",
    )


def terms(request: HttpRequest) -> HttpResponse:
    return render_information_page(
        request,
        title="Пользовательское соглашение",
        content_template="pages/information/terms.html",
    )
