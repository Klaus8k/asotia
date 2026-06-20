from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.cart.cart import Cart, CartItem
from apps.catalog.models import Product

from .models import Order, OrderItem


class CheckoutError(Exception):
    pass


@transaction.atomic
def create_order_from_cart(
    *,
    order: Order,
    cart: Cart,
    cart_items: list[CartItem],
) -> Order:
    if not cart_items:
        raise CheckoutError("Корзина пуста.")

    product_ids = [item["product"].pk for item in cart_items]
    locked_products = Product.objects.select_for_update().filter(
        pk__in=product_ids,
        is_active=True,
    )
    products_by_id = {product.pk: product for product in locked_products}

    total_price = Decimal("0.00")
    prepared_items: list[tuple[Product, int, Decimal]] = []

    for cart_item in cart_items:
        product_id = cart_item["product"].pk
        product = products_by_id.get(product_id)
        quantity = cart_item["quantity"]

        if product is None or product.stock_quantity < quantity:
            product_name = cart_item["product"].name
            raise CheckoutError(
                f"Товар «{product_name}» закончился или доступен "
                "в меньшем количестве. Обновите корзину."
            )

        item_total = product.price * quantity
        total_price += item_total
        prepared_items.append((product, quantity, item_total))

    order.total_price = total_price
    try:
        order.full_clean(exclude=("public_id",))
    except ValidationError as error:
        raise CheckoutError("Не удалось проверить данные заказа.") from error
    order.save()

    order_items = []
    for product, quantity, item_total in prepared_items:
        order_items.append(
            OrderItem(
                order=order,
                product=product,
                product_name=product.name,
                product_price=product.price,
                quantity=quantity,
                total_price=item_total,
            )
        )
        product.stock_quantity -= quantity
        product.sync_stock_status()
        product.save(update_fields=("stock_quantity", "stock_status"))

    OrderItem.objects.bulk_create(order_items)
    cart.clear()
    return order
