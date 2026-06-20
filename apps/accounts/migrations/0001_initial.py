import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Profile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        max_length=30,
                        verbose_name="телефон",
                    ),
                ),
                (
                    "delivery_address",
                    models.CharField(
                        blank=True,
                        max_length=500,
                        verbose_name="адрес доставки",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "профиль",
                "verbose_name_plural": "профили",
            },
        ),
    ]
