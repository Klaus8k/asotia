import json
from collections import defaultdict
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from apps.catalog.models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductAttributeValue,
)


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


class Command(BaseCommand):
    help = "Импортирует актуальный каталог из JSON-снимка старой схемы."

    def add_arguments(self, parser):
        parser.add_argument("snapshot", type=Path)
        parser.add_argument("--report", type=Path)

    @transaction.atomic
    def handle(self, *args, **options):
        snapshot_path: Path = options["snapshot"]
        report_path: Path | None = options["report"]
        try:
            payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise CommandError(f"Не удалось прочитать снимок: {error}") from error

        product_rows = [
            row for row in payload if row.get("model") == "catalog.product"
        ]
        if not product_rows:
            raise CommandError("В снимке нет записей catalog.product.")

        categories = self._create_categories()
        values = self._create_attributes_and_values()
        manual_review = []

        for row in product_rows:
            fields = row["fields"]
            storage_type = fields.get("storage_type", "other")
            category = categories.get(storage_type, categories["other"])
            product, _ = Product.objects.update_or_create(
                pk=row["pk"],
                defaults={
                    "category": category,
                    "name": fields["name"],
                    "slug": fields["slug"],
                    "description": fields.get("description", ""),
                    "price": fields["price"],
                    "old_price": fields.get("old_price"),
                    "weight_grams": fields.get("weight_grams"),
                    "volume_ml": fields.get("volume_ml"),
                    "units_count": fields.get("units_count"),
                    "image": fields.get("image", ""),
                    "stock_quantity": fields.get("stock_quantity", 0),
                    "is_active": fields.get("is_active", True),
                    "is_new": False,
                },
            )
            ProductAttributeValue.objects.filter(product=product).delete()
            assigned, reasons = self._classify(fields)
            ProductAttributeValue.objects.bulk_create(
                [
                    ProductAttributeValue(
                        product=product,
                        attribute_value=values[attribute_slug][value_slug],
                    )
                    for attribute_slug, value_slugs in assigned.items()
                    for value_slug in value_slugs
                ]
            )
            Product.objects.filter(pk=product.pk).update(
                created_at=parse_datetime(fields["created_at"]),
                updated_at=parse_datetime(fields["updated_at"]),
            )
            if reasons:
                manual_review.append((product.pk, product.name, reasons))

        if report_path:
            self._write_report(report_path, manual_review)

        self.stdout.write(
            self.style.SUCCESS(
                f"Импортировано товаров: {len(product_rows)}; "
                f"требуют ручной проверки: {len(manual_review)}."
            )
        )

    @staticmethod
    def _create_categories() -> dict[str, Category]:
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
        return categories

    @staticmethod
    def _create_attributes_and_values():
        result = defaultdict(dict)
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
                result[attribute_slug][value_slug] = value
        return result

    @staticmethod
    def _classify(fields):
        assigned = defaultdict(set)
        reasons = []
        name = fields["name"].lower()
        product_type = fields.get("product_type")
        meat_type = fields.get("meat_type")

        if product_type and product_type != "other":
            assigned["product-type"].add(product_type)
        elif name.startswith("компот"):
            assigned["product-type"].add("compote")
        elif name.startswith("варенье"):
            assigned["product-type"].add("jam")
        else:
            reasons.append("вид продукции не определён однозначно")

        if name.startswith("соус "):
            assigned["product-type"].add("sauce")

        ingredient_slugs = set()
        if meat_type and meat_type != "none":
            ingredient_slugs.add(meat_type)
        else:
            for marker, ingredient_slug in OBVIOUS_INGREDIENTS.items():
                if marker in name:
                    ingredient_slugs.add(ingredient_slug)

        assigned["main-ingredient"].update(ingredient_slugs)
        assigned["composition"].update(
            INGREDIENT_COMPOSITION[slug] for slug in ingredient_slugs
        )

        if product_type == "vegetables":
            assigned["composition"].add("vegetables")
        elif product_type == "fish" or name == "рыбные":
            assigned["composition"].add("fish")
        elif product_type == "other" and (
            name.startswith("компот") or name.startswith("варенье")
        ):
            assigned["composition"].add("fruit")
        elif name == "масло сливочное":
            assigned["composition"].add("dairy")
        elif name == "паштет мясной":
            assigned["composition"].add("meat")

        if meat_type == "none" and not ingredient_slugs:
            reasons.append("основной ингредиент не назначен автоматически")

        return assigned, reasons

    @staticmethod
    def _write_report(report_path: Path, rows) -> None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Ручная проверка характеристик каталога",
            "",
            "Автоматический импорт намеренно не назначает спорные значения и не "
            "выводит признак «Без мяса» из отсутствия мясного ингредиента.",
            "Упаковку и особенности нужно при необходимости проверить для всех "
            "товаров по первичным данным.",
            "",
            f"Товаров для проверки: {len(rows)}.",
            "",
            "| ID | Товар | Причина |",
            "| ---: | --- | --- |",
        ]
        lines.extend(
            f"| {pk} | {name.replace('|', '\\|')} | {'; '.join(reasons)} |"
            for pk, name, reasons in rows
        )
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
