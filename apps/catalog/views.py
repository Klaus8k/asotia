from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Category, Product


def catalog_index(
    request: HttpRequest,
    category_slug: str | None = None,
) -> HttpResponse:
    categories = Category.objects.filter(is_active=True).select_related("parent")
    products = Product.objects.filter(is_active=True).select_related("category")
    current_category = None
    search_query = request.GET.get("q", "").strip()

    if category_slug:
        current_category = get_object_or_404(
            categories,
            slug=category_slug,
        )
        products = products.filter(
            category__in=[
                current_category,
                *current_category.children.filter(is_active=True),
            ]
        )

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    return render(
        request,
        "catalog/index.html",
        {
            "categories": categories,
            "current_category": current_category,
            "products": products,
            "search_query": search_query,
        },
    )


def product_detail(
    request: HttpRequest,
    category_slug: str,
    product_slug: str,
) -> HttpResponse:
    product = get_object_or_404(
        Product.objects.select_related("category"),
        category__slug=category_slug,
        slug=product_slug,
        category__is_active=True,
        is_active=True,
    )
    return render(request, "catalog/product_detail.html", {"product": product})
