from django.db import migrations, models


def prepare_catalog_data(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")

    used_slugs = set()
    for category in Category.objects.order_by("pk"):
        slug = category.slug
        if slug in used_slugs:
            counter = 0
            while True:
                suffix = (
                    f"-{category.pk}" if counter == 0 else f"-{category.pk}-{counter}"
                )
                candidate = f"{slug[: 255 - len(suffix)]}{suffix}"
                if candidate not in used_slugs:
                    slug = candidate
                    Category.objects.filter(pk=category.pk).update(slug=slug)
                    break
                counter += 1
        used_slugs.add(slug)

    Product.objects.filter(stock_quantity__gt=0).update(stock_status="in_stock")
    Product.objects.filter(stock_quantity=0).exclude(stock_status="on_order").update(
        stock_status="out_of_stock"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_allow_unicode_slugs"),
    ]

    operations = [
        migrations.RunPython(prepare_catalog_data, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(
                allow_unicode=True,
                max_length=255,
                unique=True,
                verbose_name="слаг",
            ),
        ),
    ]
