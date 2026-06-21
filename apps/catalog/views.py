from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.cart.cart import CART_SESSION_ID, attach_cart_quantities

from .models import Category, Product


SORT_OPTIONS = {
    "default": ("По умолчанию", "category", "name"),
    "price_asc": ("Сначала дешевле", "price", "name"),
    "price_desc": ("Сначала дороже", "-price", "name"),
    "name": ("По названию", "name"),
    "newest": ("Сначала новые", "-created_at", "name"),
}


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
        return category_detail(request, current_category, products)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    products = attach_cart_quantities(request, products)

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


def category_detail(
    request: HttpRequest,
    current_category: Category,
    products,
) -> HttpResponse:
    product_type = request.GET.get("type", "").strip()
    sort_key = request.GET.get("sort", "default")

    if sort_key not in SORT_OPTIONS:
        sort_key = "default"

    available_type_values = list(
        products.exclude(product_type=Product.ProductType.OTHER)
        .order_by()
        .values_list("product_type", flat=True)
        .distinct()
    )
    product_types = [
        (value, Product.ProductType(value).label)
        for value in Product.ProductType.values
        if value in available_type_values
    ]

    if product_type in available_type_values:
        products = products.filter(product_type=product_type)
    else:
        product_type = ""

    products = attach_cart_quantities(
        request,
        products.order_by(*SORT_OPTIONS[sort_key][1:]),
    )

    return render(
        request,
        "catalog/category.html",
        {
            "current_category": current_category,
            "products": products,
            "product_types": product_types,
            "current_product_type": product_type,
            "sort_options": [
                (value, options[0]) for value, options in SORT_OPTIONS.items()
            ],
            "current_sort": sort_key,
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
    cart_quantities = request.session.get(CART_SESSION_ID, {})
    product.cart_quantity = cart_quantities.get(str(product.pk), 0)
    return render(request, "catalog/product_detail.html", {"product": product})
