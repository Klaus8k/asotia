from django.db.models import Prefetch, Q
from django.http import HttpRequest, HttpResponse, QueryDict
from django.shortcuts import get_object_or_404, render

from apps.cart.cart import CART_SESSION_ID, attach_cart_quantities

from .models import Attribute, AttributeValue, Category, Product


SORT_OPTIONS = {
    "default": ("По умолчанию", "category", "name"),
    "price_asc": ("Сначала дешевле", "price", "name"),
    "price_desc": ("Сначала дороже", "-price", "name"),
    "name": ("По названию", "name"),
    "newest": ("Сначала новые", "-created_at", "name"),
}


PUBLIC_ATTRIBUTE_VALUES = Prefetch(
    "attribute_values",
    queryset=AttributeValue.objects.filter(
        is_active=True,
        attribute__is_active=True,
    )
    .select_related("attribute")
    .order_by("attribute__sort_order", "attribute__name", "sort_order", "name"),
    to_attr="public_attribute_values",
)


def catalog_index(
    request: HttpRequest,
    category_slug: str | None = None,
) -> HttpResponse:
    categories = Category.objects.filter(is_active=True)
    products = (
        Product.objects.public()
        .select_related("category")
        .prefetch_related(PUBLIC_ATTRIBUTE_VALUES)
    )
    current_category = None
    search_query = request.GET.get("q", "").strip()

    if category_slug:
        current_category = get_object_or_404(categories, slug=category_slug)
        products = products.filter(category=current_category)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(attribute_values__name__icontains=search_query)
        ).distinct()

    filter_source = products
    filter_groups = list(
        Attribute.objects.filter(
            is_active=True,
            values__is_active=True,
            values__products__in=filter_source,
        )
        .distinct()
        .prefetch_related(
            Prefetch(
                "values",
                queryset=AttributeValue.objects.filter(
                    is_active=True,
                    products__in=filter_source,
                )
                .distinct()
                .order_by("sort_order", "name"),
                to_attr="public_values",
            )
        )
    )

    available_value_ids = {
        value.pk for group in filter_groups for value in group.public_values
    }
    selected_value_ids = _selected_value_ids(request.GET, available_value_ids)
    selected_values = list(
        AttributeValue.objects.filter(
            pk__in=selected_value_ids,
            is_active=True,
            attribute__is_active=True,
        ).select_related("attribute")
    )

    if selected_values:
        products = products.filter_by_attribute_values(selected_values)

    sort_key = request.GET.get("sort", "default")
    if sort_key not in SORT_OPTIONS:
        sort_key = "default"
    products = products.order_by(*SORT_OPTIONS[sort_key][1:])

    for group in filter_groups:
        for value in group.public_values:
            value.is_selected = value.pk in selected_value_ids

    selected_chips = [
        {
            "label": f"{value.attribute.name}: {value.name}",
            "remove_url": _query_url(
                request.GET,
                attribute_ids=[
                    value_id
                    for value_id in selected_value_ids
                    if value_id != value.pk
                ],
            ),
        }
        for value in selected_values
    ]

    products = attach_cart_quantities(request, products)
    template_name = "catalog/category.html" if current_category else "catalog/index.html"
    return render(
        request,
        template_name,
        {
            "categories": categories,
            "current_category": current_category,
            "products": products,
            "search_query": search_query,
            "filter_groups": filter_groups,
            "selected_value_ids": selected_value_ids,
            "selected_chips": selected_chips,
            "clear_filters_url": _query_url(request.GET, attribute_ids=[]),
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
        Product.objects.public()
        .select_related("category")
        .prefetch_related(PUBLIC_ATTRIBUTE_VALUES),
        category__slug=category_slug,
        slug=product_slug,
    )
    cart_quantities = request.session.get(CART_SESSION_ID, {})
    product.cart_quantity = cart_quantities.get(str(product.pk), 0)
    related_products = attach_cart_quantities(
        request,
        Product.objects.public()
        .filter(category=product.category)
        .exclude(pk=product.pk)
        .select_related("category")
        .prefetch_related(PUBLIC_ATTRIBUTE_VALUES)[:4],
    )
    return render(
        request,
        "catalog/product_detail.html",
        {"product": product, "related_products": related_products},
    )


def _selected_value_ids(query: QueryDict, available_ids: set[int]) -> list[int]:
    selected_ids = []
    for raw_value in query.getlist("attribute"):
        try:
            value_id = int(raw_value)
        except (TypeError, ValueError):
            continue
        if value_id in available_ids and value_id not in selected_ids:
            selected_ids.append(value_id)
    return selected_ids


def _query_url(query: QueryDict, *, attribute_ids: list[int]) -> str:
    updated_query = query.copy()
    updated_query.setlist("attribute", [str(value_id) for value_id in attribute_ids])
    encoded = updated_query.urlencode()
    return f"?{encoded}" if encoded else "?"
