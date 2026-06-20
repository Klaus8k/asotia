from collections.abc import Iterator
from decimal import Decimal
from typing import TypedDict

from django.http import HttpRequest

from apps.catalog.models import Product


CART_SESSION_ID = "cart"


class CartItem(TypedDict):
    product: Product
    quantity: int
    total_price: Decimal


class Cart:
    def __init__(self, request: HttpRequest) -> None:
        self.session = request.session
        self.cart: dict[str, int] = self.session.get(CART_SESSION_ID, {})

    def add(self, product: Product, quantity: int = 1) -> None:
        product_id = str(product.pk)
        current_quantity = self.cart.get(product_id, 0)
        self.cart[product_id] = min(
            current_quantity + quantity,
            product.stock_quantity,
        )
        self._save()

    def update(self, product: Product, quantity: int) -> None:
        product_id = str(product.pk)
        self.cart[product_id] = min(quantity, product.stock_quantity)
        self._save()

    def remove(self, product: Product) -> None:
        product_id = str(product.pk)
        if product_id in self.cart:
            del self.cart[product_id]
            self._save()

    def clear(self) -> None:
        self.session.pop(CART_SESSION_ID, None)
        self.session.modified = True

    def __iter__(self) -> Iterator[CartItem]:
        product_ids = self.cart.keys()
        products = Product.objects.filter(
            pk__in=product_ids,
            is_active=True,
            stock_quantity__gt=0,
        ).select_related("category")
        products_by_id = {str(product.pk): product for product in products}

        unavailable_product_ids = set(product_ids) - products_by_id.keys()
        for product_id in unavailable_product_ids:
            del self.cart[product_id]

        if unavailable_product_ids:
            self._save()

        for product_id, quantity in self.cart.items():
            product = products_by_id[product_id]
            actual_quantity = min(quantity, product.stock_quantity)

            if actual_quantity != quantity:
                self.cart[product_id] = actual_quantity
                self._save()

            yield {
                "product": product,
                "quantity": actual_quantity,
                "total_price": product.price * actual_quantity,
            }

    def __len__(self) -> int:
        return sum(self.cart.values())

    def get_total_price(self) -> Decimal:
        return sum(
            (item["total_price"] for item in self),
            start=Decimal("0.00"),
        )

    def _save(self) -> None:
        self.session[CART_SESSION_ID] = self.cart
        self.session.modified = True
