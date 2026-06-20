import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import send_mail

from .models import Order


logger = logging.getLogger(__name__)


def notify_about_new_order(order_id: int) -> None:
    try:
        order = Order.objects.prefetch_related("items").get(pk=order_id)
        subject = f"Новый заказ №{order.pk} на {order.total_price} ₽"
        message = _build_order_message(order)
    except Exception as error:
        logger.error(
            "Не удалось подготовить уведомление о новом заказе (%s).",
            type(error).__name__,
        )
        return

    _send_email_notification(subject, message)
    _send_telegram_notification(message)


def _build_order_message(order: Order) -> str:
    item_lines = [
        f"• {item.product_name} × {item.quantity} — {item.total_price} ₽"
        for item in order.items.all()
    ]
    customer_lines = [
        f"Имя: {order.customer_name}",
        f"Телефон: {order.phone}",
        f"Email: {order.email or 'не указан'}",
        f"Адрес: {order.delivery_address}",
        f"Комментарий: {order.comment or 'нет'}",
    ]
    return "\n".join(
        [
            f"Новый заказ №{order.pk}",
            "",
            *customer_lines,
            "",
            "Состав заказа:",
            *item_lines,
            "",
            f"Итого: {order.total_price} ₽",
        ]
    )


def _send_email_notification(subject: str, message: str) -> None:
    recipients = settings.ORDER_NOTIFICATION_EMAILS
    if not recipients:
        return

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
        )
    except Exception as error:
        logger.error(
            "Не удалось отправить email-уведомление о новом заказе (%s: %s).",
            type(error).__name__,
            error,
        )


def _send_telegram_notification(message: str) -> None:
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not bot_token or not chat_id:
        return

    request = Request(
        url=f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=urlencode(
            {
                "chat_id": chat_id,
                "text": message,
            }
        ).encode(),
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.TELEGRAM_TIMEOUT_SECONDS):
            pass
    except Exception as error:
        logger.error(
            "Не удалось отправить Telegram-уведомление о новом заказе (%s).",
            type(error).__name__,
        )
