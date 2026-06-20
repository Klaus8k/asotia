from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.catalog.models import Product

from .cart import Cart


def cart_detail(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)
    return render(
        request,
        "cart/detail.html",
        {
            "cart": cart,
            "cart_items": list(cart),
            "cart_total": cart.get_total_price(),
        },
    )


@require_POST
def cart_add(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(
        Product,
        pk=product_id,
        is_active=True,
        stock_quantity__gt=0,
    )
    quantity = _get_quantity(request)
    Cart(request).add(product, quantity)
    messages.success(request, f"«{product.name}» добавлен в корзину.")
    return redirect(_get_redirect_url(request))


@require_POST
def cart_update(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(
        Product,
        pk=product_id,
        is_active=True,
        stock_quantity__gt=0,
    )
    quantity = _get_quantity(request, minimum=0)
    cart = Cart(request)
    if quantity == 0:
        cart.remove(product)
        messages.success(request, f"«{product.name}» удалён из корзины.")
    else:
        cart.update(product, quantity)
        messages.success(request, "Количество товара обновлено.")
    return redirect(_get_redirect_url(request))


@require_POST
def cart_remove(request: HttpRequest, product_id: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=product_id)
    Cart(request).remove(product)
    messages.success(request, f"«{product.name}» удалён из корзины.")
    return redirect("cart:detail")


def _get_quantity(request: HttpRequest, minimum: int = 1) -> int:
    try:
        return max(minimum, int(request.POST.get("quantity", 1)))
    except (TypeError, ValueError):
        return max(minimum, 1)


def _get_redirect_url(request: HttpRequest) -> str:
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("cart:detail")
