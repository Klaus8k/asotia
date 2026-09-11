from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse

from apps.cart.cart import attach_cart_quantities
from apps.catalog.models import AttributeValue, Category, Collection, Product


PUBLIC_VALUES = Prefetch(
    "attribute_values",
    queryset=AttributeValue.objects.filter(
        is_active=True,
        attribute__is_active=True,
    ).select_related("attribute"),
    to_attr="public_attribute_values",
)


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
    categories = Category.objects.filter(is_active=True)
    public_products = (
        Product.objects.public()
        .select_related("category")
        .prefetch_related(PUBLIC_VALUES)
    )
    hero_products = list(public_products.order_by("-is_new", "-created_at")[:3])
    showcase_sections = _collection_sections(request)
    existing_titles = {section["title"] for section in showcase_sections}

    fallbacks = [
        (
            "Новое в каталоге",
            "Новинки",
            "Свежие позиции, которые недавно появились на витрине.",
            public_products.filter(is_new=True).order_by("-created_at"),
        ),
        (
            "Для сытного стола",
            "Готовые блюда",
            "Ужин без долгой готовки — разогреть и подать.",
            _products_with_value(public_products, "product-type", "ready_meal"),
        ),
        (
            "Запас в морозилке",
            "Заморозка",
            "Практичные продукты на случай, когда важно приготовить быстро.",
            public_products.filter(category__slug="заморозка"),
        ),
        (
            "Выбор витрины",
            "Рекомендуем",
            "Продукты, с которых удобно начать знакомство с Asotia.",
            public_products.order_by("-is_new", "name"),
        ),
    ]
    for eyebrow, title, description, queryset in fallbacks:
        if title in existing_titles:
            continue
        products = attach_cart_quantities(request, queryset[:8])
        if not products:
            continue
        showcase_sections.append(
            {
                "eyebrow": eyebrow,
                "title": title,
                "description": description,
                "products": products,
                "url": reverse("catalog:index"),
            }
        )
        existing_titles.add(title)
        if len(showcase_sections) >= 4:
            break

    return render(
        request,
        "pages/home.html",
        {
            "categories": categories,
            "category_count": categories.count(),
            "product_count": public_products.count(),
            "hero_products": hero_products,
            "showcase_sections": showcase_sections,
        },
    )


def _collection_sections(request: HttpRequest) -> list[dict]:
    sections = []
    collections = Collection.objects.filter(is_active=True).order_by(
        "sort_order", "name"
    )[:6]
    for collection in collections:
        products = attach_cart_quantities(
            request,
            collection.products()
            .select_related("category")
            .prefetch_related(PUBLIC_VALUES)[:8],
        )
        if products:
            sections.append(
                {
                    "eyebrow": "Подборка Asotia",
                    "title": collection.name,
                    "description": collection.description,
                    "products": products,
                    "url": reverse("catalog:index"),
                }
            )
    return sections


def _products_with_value(products, attribute_slug: str, value_slug: str):
    value = AttributeValue.objects.filter(
        attribute__slug=attribute_slug,
        attribute__is_active=True,
        slug=value_slug,
        is_active=True,
    ).first()
    if value is None:
        return products.none()
    return products.filter_by_attribute_values([value])


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
