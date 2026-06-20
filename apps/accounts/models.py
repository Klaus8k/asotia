from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="пользователь",
        related_name="profile",
        on_delete=models.CASCADE,
    )
    phone = models.CharField("телефон", max_length=30, blank=True)
    delivery_address = models.CharField(
        "адрес доставки",
        max_length=500,
        blank=True,
    )

    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self) -> str:
        return f"Профиль {self.user}"
