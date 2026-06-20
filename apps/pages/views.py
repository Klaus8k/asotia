from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.catalog.models import Category


def home(request: HttpRequest) -> HttpResponse:
    categories = (
        Category.objects.filter(
            is_active=True,
            products__is_active=True,
        )
        .select_related("parent")
        .distinct()
    )
    return render(
        request,
        "pages/home.html",
        {"categories": categories},
    )


def about(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/simple.html", {"title": "О нас"})


def contacts(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/simple.html", {"title": "Контакты"})


def delivery(request: HttpRequest) -> HttpResponse:
    return render(request, "pages/simple.html", {"title": "Доставка и оплата"})


def privacy(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/simple.html",
        {"title": "Политика конфиденциальности"},
    )


def terms(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "pages/simple.html",
        {"title": "Пользовательское соглашение"},
    )
