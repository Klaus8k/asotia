import django.db.models.deletion
from django.db import migrations, models


CATEGORIES = {
    "canned": ("Консервы", "консервы", 0),
    "frozen": ("Заморозка", "заморозка", 1),
    "other": ("Другое", "другое", 2),
}

ATTRIBUTES = {
    "product-type": ("Вид продукции", 0),
    "composition": ("Состав", 1),
    "main-ingredient": ("Основной ингредиент", 2),
    "packaging": ("Упаковка", 3),
    "features": ("Особенности", 4),
}

ATTRIBUTE_VALUES = {
    "product-type": {
        "stew": "Тушёнка",
        "pate": "Паштет",
        "fish": "Рыбный продукт",
        "vegetables": "Овощная консерва",
        "ready_meal": "Готовое блюдо",
        "semi_finished": "Полуфабрикат",
        "meat": "Фарш",
        "sauce": "Соус",
        "compote": "Компот",
        "jam": "Варенье",
    },
    "composition": {
        "meat": "Мясо",
        "poultry": "Птица",
        "fish": "Рыба",
        "seafood": "Морепродукты",
        "vegetables": "Овощи",
        "fruit": "Фрукты",
        "dairy": "Молочная продукция",
    },
    "main-ingredient": {
        "beef": "Говядина",
        "pork": "Свинина",
        "chicken": "Курица",
        "turkey": "Индейка",
        "lamb": "Баранина",
        "horse": "Конина",
        "duck": "Утка",
        "tuna": "Тунец",
        "pollock": "Минтай",
        "cod": "Треска",
        "squid": "Кальмар",
    },
    "packaging": {
        "glass-jar": "Стеклянная банка",
        "tin-can": "Жестяная банка",
        "bottle": "Бутылка",
        "vacuum": "Вакуум",
    },
    "features": {"meat-free": "Без мяса"},
}

INGREDIENT_COMPOSITION = {
    "beef": "meat",
    "pork": "meat",
    "lamb": "meat",
    "horse": "meat",
    "chicken": "poultry",
    "turkey": "poultry",
    "duck": "poultry",
    "tuna": "fish",
    "pollock": "fish",
    "cod": "fish",
    "squid": "seafood",
}

OBVIOUS_INGREDIENTS = {
    "конин": "horse",
    "утка": "duck",
    "бараний": "lamb",
    "тун": "tuna",
    "минтая": "pollock",
    "трески": "cod",
    "кальмар": "squid",
}


def classify_product(product):
    assigned = set()
    name = product.name.lower()

    if product.product_type and product.product_type != "other":
        assigned.add(("product-type", product.product_type))
    elif name.startswith("компот"):
        assigned.add(("product-type", "compote"))
    elif name.startswith("варенье"):
        assigned.add(("product-type", "jam"))

    if name.startswith("соус "):
        assigned.add(("product-type", "sauce"))

    ingredient_slugs = set()
    if product.meat_type and product.meat_type != "none":
        ingredient_slugs.add(product.meat_type)
    else:
        for marker, ingredient_slug in OBVIOUS_INGREDIENTS.items():
            if marker in name:
                ingredient_slugs.add(ingredient_slug)

    for ingredient_slug in ingredient_slugs:
        assigned.add(("main-ingredient", ingredient_slug))
        assigned.add(("composition", INGREDIENT_COMPOSITION[ingredient_slug]))

    if product.product_type == "vegetables":
        assigned.add(("composition", "vegetables"))
    elif product.product_type == "fish" or name == "рыбные":
        assigned.add(("composition", "fish"))
    elif product.product_type == "other" and (
        name.startswith("компот") or name.startswith("варенье")
    ):
        assigned.add(("composition", "fruit"))
    elif name == "масло сливочное":
        assigned.add(("composition", "dairy"))
    elif name == "паштет мясной":
        assigned.add(("composition", "meat"))

    return assigned


def migrate_catalog_data(apps, schema_editor):
    Attribute = apps.get_model("catalog", "Attribute")
    AttributeValue = apps.get_model("catalog", "AttributeValue")
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    ProductAttributeValue = apps.get_model("catalog", "ProductAttributeValue")

    # Fresh installations should start with an empty catalog. The seed data is
    # only needed to translate products from the pre-refactor production schema.
    if not Product.objects.exists():
        return

    categories = {}
    for storage_type, (name, slug, sort_order) in CATEGORIES.items():
        categories[storage_type], _ = Category.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "sort_order": sort_order,
                "is_active": True,
            },
        )

    values = {}
    for attribute_slug, (name, sort_order) in ATTRIBUTES.items():
        attribute, _ = Attribute.objects.update_or_create(
            slug=attribute_slug,
            defaults={
                "name": name,
                "sort_order": sort_order,
                "is_active": True,
            },
        )
        for value_order, (value_slug, value_name) in enumerate(
            ATTRIBUTE_VALUES[attribute_slug].items()
        ):
            value, _ = AttributeValue.objects.update_or_create(
                attribute=attribute,
                slug=value_slug,
                defaults={
                    "name": value_name,
                    "sort_order": value_order,
                    "is_active": True,
                },
            )
            values[(attribute_slug, value_slug)] = value

    fallback_category = categories["other"]
    assignments = []
    for product in Product.objects.all().iterator():
        category = categories.get(product.storage_type, fallback_category)
        Product.objects.filter(pk=product.pk).update(
            category=category,
            is_new=False,
        )
        assignments.extend(
            ProductAttributeValue(
                product_id=product.pk,
                attribute_value_id=values[value_key].pk,
            )
            for value_key in classify_product(product)
            if value_key in values
        )

    ProductAttributeValue.objects.bulk_create(assignments)
    active_category_ids = [category.pk for category in categories.values()]
    Category.objects.exclude(pk__in=active_category_ids).update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_category_slug_unique_and_sync_stock"),
    ]

    operations = [
        migrations.CreateModel(
            name="Attribute",
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
                ("name", models.CharField(max_length=255, verbose_name="название")),
                (
                    "slug",
                    models.SlugField(
                        allow_unicode=True,
                        max_length=255,
                        unique=True,
                        verbose_name="слаг",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="активна"),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0, verbose_name="порядок сортировки"
                    ),
                ),
            ],
            options={
                "verbose_name": "характеристика",
                "verbose_name_plural": "характеристики",
                "ordering": ("sort_order", "name"),
            },
        ),
        migrations.AddField(
            model_name="category",
            name="image",
            field=models.ImageField(
                blank=True,
                upload_to="categories/",
                verbose_name="изображение",
            ),
        ),
        migrations.CreateModel(
            name="AttributeValue",
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
                ("name", models.CharField(max_length=255, verbose_name="значение")),
                (
                    "slug",
                    models.SlugField(
                        allow_unicode=True, max_length=255, verbose_name="слаг"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="активно"),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0, verbose_name="порядок сортировки"
                    ),
                ),
                (
                    "attribute",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="values",
                        to="catalog.attribute",
                        verbose_name="характеристика",
                    ),
                ),
            ],
            options={
                "verbose_name": "значение характеристики",
                "verbose_name_plural": "значения характеристик",
                "ordering": ("attribute", "sort_order", "name"),
            },
        ),
        migrations.CreateModel(
            name="Collection",
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
                ("name", models.CharField(max_length=255, verbose_name="название")),
                (
                    "slug",
                    models.SlugField(
                        allow_unicode=True,
                        max_length=255,
                        unique=True,
                        verbose_name="слаг",
                    ),
                ),
                ("description", models.TextField(blank=True, verbose_name="описание")),
                (
                    "image",
                    models.ImageField(
                        blank=True, upload_to="collections/", verbose_name="изображение"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="активна"),
                ),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0, verbose_name="порядок сортировки"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="дата создания"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="дата обновления"),
                ),
                (
                    "categories",
                    models.ManyToManyField(
                        blank=True,
                        related_name="collections",
                        to="catalog.category",
                        verbose_name="категории",
                    ),
                ),
            ],
            options={
                "verbose_name": "подборка",
                "verbose_name_plural": "подборки",
                "ordering": ("sort_order", "name"),
            },
        ),
        migrations.CreateModel(
            name="CollectionRule",
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
                    "attribute_value",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="collection_rules",
                        to="catalog.attributevalue",
                        verbose_name="значение характеристики",
                    ),
                ),
                (
                    "collection",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rules",
                        to="catalog.collection",
                        verbose_name="подборка",
                    ),
                ),
            ],
            options={
                "verbose_name": "правило подборки",
                "verbose_name_plural": "правила подборок",
                "ordering": ("attribute_value__attribute", "attribute_value"),
            },
        ),
        migrations.AddField(
            model_name="collection",
            name="attribute_values",
            field=models.ManyToManyField(
                blank=True,
                related_name="collections",
                through="catalog.CollectionRule",
                to="catalog.attributevalue",
                verbose_name="правила по характеристикам",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="volume_ml",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="объём в миллилитрах",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="units_count",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="количество единиц",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="is_new",
            field=models.BooleanField(default=False, verbose_name="новинка"),
        ),
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(blank=True, verbose_name="описание"),
        ),
        migrations.CreateModel(
            name="ProductAttributeValue",
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
                    "attribute_value",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="product_assignments",
                        to="catalog.attributevalue",
                        verbose_name="значение характеристики",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attribute_assignments",
                        to="catalog.product",
                        verbose_name="товар",
                    ),
                ),
            ],
            options={
                "verbose_name": "характеристика товара",
                "verbose_name_plural": "характеристики товара",
                "ordering": ("attribute_value__attribute", "attribute_value"),
            },
        ),
        migrations.AddField(
            model_name="product",
            name="attribute_values",
            field=models.ManyToManyField(
                blank=True,
                related_name="products",
                through="catalog.ProductAttributeValue",
                to="catalog.attributevalue",
                verbose_name="значения характеристик",
            ),
        ),
        migrations.AddConstraint(
            model_name="attributevalue",
            constraint=models.UniqueConstraint(
                fields=("attribute", "name"),
                name="unique_attribute_value_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="attributevalue",
            constraint=models.UniqueConstraint(
                fields=("attribute", "slug"),
                name="unique_attribute_value_slug",
            ),
        ),
        migrations.AddConstraint(
            model_name="collectionrule",
            constraint=models.UniqueConstraint(
                fields=("collection", "attribute_value"),
                name="unique_collection_attribute_value",
            ),
        ),
        migrations.AddConstraint(
            model_name="productattributevalue",
            constraint=models.UniqueConstraint(
                fields=("product", "attribute_value"),
                name="unique_product_attribute_value",
            ),
        ),
        migrations.RunSQL(
            "ALTER TABLE catalog_product ALTER COLUMN storage_type SET DEFAULT 'other'",
            "ALTER TABLE catalog_product ALTER COLUMN storage_type DROP DEFAULT",
        ),
        migrations.RunSQL(
            "ALTER TABLE catalog_product ALTER COLUMN product_type SET DEFAULT 'other'",
            "ALTER TABLE catalog_product ALTER COLUMN product_type DROP DEFAULT",
        ),
        migrations.RunSQL(
            "ALTER TABLE catalog_product ALTER COLUMN meat_type SET DEFAULT 'none'",
            "ALTER TABLE catalog_product ALTER COLUMN meat_type DROP DEFAULT",
        ),
        migrations.RunSQL(
            "ALTER TABLE catalog_product ALTER COLUMN is_featured SET DEFAULT false",
            "ALTER TABLE catalog_product ALTER COLUMN is_featured DROP DEFAULT",
        ),
        migrations.RunSQL(
            "ALTER TABLE catalog_product "
            "ALTER COLUMN stock_status SET DEFAULT 'out_of_stock'",
            "ALTER TABLE catalog_product ALTER COLUMN stock_status DROP DEFAULT",
        ),
        migrations.RunPython(
            migrate_catalog_data,
            migrations.RunPython.noop,
        ),
        # Keep the legacy columns in PostgreSQL during the first production
        # rollout. Django stops using them, while an emergency code rollback
        # remains possible until a later cleanup migration.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name="category", name="parent"),
                migrations.RemoveField(model_name="product", name="storage_type"),
                migrations.RemoveField(model_name="product", name="product_type"),
                migrations.RemoveField(model_name="product", name="meat_type"),
                migrations.RemoveField(model_name="product", name="is_featured"),
                migrations.RemoveField(model_name="product", name="stock_status"),
            ],
            database_operations=[],
        ),
    ]
