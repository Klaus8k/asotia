from decimal import Decimal
from uuid import UUID

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.accounts.models import Profile
from apps.cart.cart import Cart

from .forms import CheckoutForm
from .models import Order
from .services import CheckoutError, create_order_from_cart


def checkout(request: HttpRequest) -> HttpResponse:
    cart = Cart(request)
    cart_items = list(cart)

    if not cart_items:
        return redirect("cart:detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            if request.user.is_authenticated:
                order.user = request.user
            try:
                create_order_from_cart(
                    order=order,
                    cart=cart,
                    cart_items=cart_items,
                )
            except CheckoutError as error:
                form.add_error(None, str(error))
            else:
                if request.user.is_authenticated:
                    Profile.objects.update_or_create(
                        user=request.user,
                        defaults={
                            "phone": order.phone,
                            "delivery_address": order.delivery_address,
                        },
                    )
                return redirect("orders:success", public_id=order.public_id)
    else:
        initial = {}
        if request.user.is_authenticated:
            full_name = request.user.get_full_name().strip()
            profile = Profile.objects.filter(user=request.user).first()
            initial = {
                "customer_name": full_name or request.user.username,
                "email": request.user.email,
                "phone": profile.phone if profile else "",
                "delivery_address": (
                    profile.delivery_address if profile else ""
                ),
            }
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart_items": cart_items,
            "cart_total": sum(
                (item["total_price"] for item in cart_items),
                start=Decimal("0.00"),
            ),
        },
    )


def order_success(request: HttpRequest, public_id: UUID) -> HttpResponse:
    try:
        order = Order.objects.prefetch_related("items").get(public_id=public_id)
    except (Order.DoesNotExist, ValueError) as error:
        raise Http404 from error

    return render(request, "orders/success.html", {"order": order})
