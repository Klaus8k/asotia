import html
import io
import re
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils.text import slugify
from PIL import Image

from apps.catalog.models import Category, Product


CATEGORY_MAP = {
    1: ("Консервы", "Тушёнка"),
    2: ("Заморозка", "Замороженные продукты"),
    3: ("Консервы", "Рыбные продукты"),
    4: ("Консервы", "Готовые блюда"),
    5: ("Консервы", "Овощные продукты"),
    6: ("Заморозка", "Полуфабрикаты"),
    7: ("Консервы", "Паштеты"),
    8: ("Консервы", "Компоты и варенье"),
    9: ("Другое", None),
}

CATEGORY_CLASSIFICATION = {
    1: (Product.StorageType.CANNED, Product.ProductType.STEW),
    2: (Product.StorageType.FROZEN, Product.ProductType.MEAT),
    3: (Product.StorageType.CANNED, Product.ProductType.FISH),
    4: (Product.StorageType.CANNED, Product.ProductType.READY_MEAL),
    5: (Product.StorageType.CANNED, Product.ProductType.VEGETABLES),
    6: (Product.StorageType.FROZEN, Product.ProductType.SEMI_FINISHED),
    7: (Product.StorageType.CANNED, Product.ProductType.PATE),
    8: (Product.StorageType.CANNED, Product.ProductType.OTHER),
    9: (Product.StorageType.OTHER, Product.ProductType.OTHER),
}

ROOT_SORT_ORDER = {
    "Консервы": 0,
    "Заморозка": 1,
    "Другое": 2,
}

MEAT_KEYWORDS = (
    (Product.MeatType.BEEF, ("говядин", "говяж", "теля")),
    (Product.MeatType.PORK, ("свинин", "свин", "рульк")),
    (Product.MeatType.CHICKEN, ("курин", "куриц", "цыпл")),
    (Product.MeatType.TURKEY, ("индейк",)),
    (Product.MeatType.LAMB, ("баранин", "ягнен")),
    (Product.MeatType.MIXED, ("ассорти", "смешан")),
)

WEBLINK_GET_RE = re.compile(r'"weblink_get":\{"count":"\d+","url":"(?P<url>[^"]+)"')
MAX_IMAGE_SIZE = 25 * 1024 * 1024


class Command(BaseCommand):
    help = "Переносит категории и товары из старых таблиц categories/products."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Не скачивать изображения из старых ссылок.",
        )
        parser.add_argument(
            "--refresh-images",
            action="store_true",
            help="Повторно скачать изображения уже импортированных товаров.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Проверить импорт и откатить изменения базы данных.",
        )

    def handle(self, *args, **options):
        categories, products = self._read_legacy_data()
        if not categories:
            raise CommandError("В старой таблице categories нет данных.")

        unknown_category_ids = {
            category["id"]
            for category in categories
            if category["id"] not in CATEGORY_MAP
        }
        if unknown_category_ids:
            ids = ", ".join(map(str, sorted(unknown_category_ids)))
            raise CommandError(f"Не настроено сопоставление категорий: {ids}.")

        missing_category_ids = {product["category_id"] for product in products} - {
            category["id"] for category in categories
        }
        if missing_category_ids:
            ids = ", ".join(map(str, sorted(missing_category_ids)))
            raise CommandError(f"У товаров отсутствуют категории: {ids}.")

        product_slugs = self._build_product_slugs(products)
        image_errors = []
        created_products = 0
        updated_products = 0

        with transaction.atomic():
            category_objects = self._import_categories(categories)

            for legacy_product in products:
                target_category = category_objects[legacy_product["category_id"]]
                storage_type, product_type = CATEGORY_CLASSIFICATION[
                    legacy_product["category_id"]
                ]
                stock_quantity = max(legacy_product["stock"] or 0, 0)
                defaults = {
                    "name": legacy_product["name"].strip(),
                    "description": (legacy_product["description"] or "").strip(),
                    "price": self._decimal_price(legacy_product["price"]),
                    "stock_quantity": stock_quantity,
                    "storage_type": storage_type,
                    "product_type": product_type,
                    "meat_type": self._infer_meat_type(legacy_product["name"]),
                    "is_active": bool(legacy_product["is_active"]),
                }

                product, created = Product.objects.update_or_create(
                    category=target_category,
                    slug=product_slugs[legacy_product["id"]],
                    defaults=defaults,
                )
                product.sync_stock_status()
                product.save(update_fields=("stock_status", "updated_at"))

                if created:
                    created_products += 1
                else:
                    updated_products += 1

                should_download = (
                    not options["skip_images"]
                    and legacy_product["image_url"]
                    and (options["refresh_images"] or not product.image)
                    and not options["dry_run"]
                )
                if should_download:
                    try:
                        self._save_image(
                            product,
                            legacy_product["image_url"],
                            legacy_product["id"],
                        )
                    except Exception as error:
                        image_errors.append(
                            f"{legacy_product['id']} {legacy_product['name']}: {error}"
                        )

            if options["dry_run"]:
                transaction.set_rollback(True)

        action = "Проверено" if options["dry_run"] else "Импортировано"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action}: категорий {len(category_objects)}, "
                f"товаров создано {created_products}, обновлено {updated_products}."
            )
        )
        if image_errors:
            self.stderr.write(
                self.style.WARNING(
                    f"Не удалось скачать изображений: {len(image_errors)}"
                )
            )
            for error in image_errors:
                self.stderr.write(f"- {error}")

    def _read_legacy_data(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT id, name, description, is_active
                    FROM categories
                    ORDER BY id
                    """
                )
            except Exception as error:
                raise CommandError(
                    "Не удалось прочитать старую таблицу categories. "
                    "Убедитесь, что команда запущена в базе со старыми таблицами."
                ) from error
            categories = self._dict_rows(cursor)

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    price,
                    type_product,
                    image_url,
                    stock,
                    category_id,
                    is_active
                FROM products
                ORDER BY id
                """
            )
            products = self._dict_rows(cursor)

        return categories, products

    @staticmethod
    def _dict_rows(cursor) -> list[dict[str, Any]]:
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def _import_categories(
        self,
        legacy_categories: list[dict[str, Any]],
    ) -> dict[int, Category]:
        result = {}
        roots = {}

        for legacy_category in legacy_categories:
            old_id = legacy_category["id"]
            root_name, child_name = CATEGORY_MAP[old_id]
            root = roots.get(root_name)
            if root is None:
                root_slug = slugify(root_name, allow_unicode=True)
                root, _ = Category.objects.update_or_create(
                    parent=None,
                    slug=root_slug,
                    defaults={
                        "name": root_name,
                        "is_active": True,
                        "sort_order": ROOT_SORT_ORDER[root_name],
                    },
                )
                roots[root_name] = root

            if child_name is None:
                result[old_id] = root
                continue

            child, _ = Category.objects.update_or_create(
                parent=root,
                slug=slugify(child_name, allow_unicode=True),
                defaults={
                    "name": child_name,
                    "description": (legacy_category["description"] or "").strip(),
                    "is_active": bool(legacy_category["is_active"]),
                    "sort_order": old_id,
                },
            )
            result[old_id] = child

        return result

    @staticmethod
    def _build_product_slugs(products: list[dict[str, Any]]) -> dict[int, str]:
        base_slugs = {
            product["id"]: slugify(product["name"], allow_unicode=True)
            or f"product-{product['id']}"
            for product in products
        }
        slug_counts = Counter(
            (product["category_id"], base_slugs[product["id"]]) for product in products
        )
        return {
            product["id"]: (
                f"{base_slugs[product['id']]}-{product['id']}"
                if slug_counts[(product["category_id"], base_slugs[product["id"]])] > 1
                else base_slugs[product["id"]]
            )
            for product in products
        }

    @staticmethod
    def _decimal_price(value) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _infer_meat_type(name: str) -> str:
        normalized_name = name.casefold()
        matches = []
        for meat_type, keywords in MEAT_KEYWORDS:
            if any(keyword in normalized_name for keyword in keywords):
                matches.append(meat_type)

        if len(set(matches)) > 1:
            return Product.MeatType.MIXED
        if matches:
            return matches[0]
        return Product.MeatType.NONE

    def _save_image(self, product: Product, public_url: str, legacy_id: int) -> None:
        content, filename = self._download_cloud_mail_image(public_url)
        suffix = Path(filename).suffix.lower() or ".jpg"
        if product.image:
            product.image.delete(save=False)
        product.image.save(
            f"{product.slug}-{legacy_id}{suffix}",
            ContentFile(content),
            save=True,
        )

    @staticmethod
    def _download_cloud_mail_image(public_url: str) -> tuple[bytes, str]:
        page_request = Request(public_url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(page_request, timeout=30) as response:
            page = response.read().decode("utf-8", errors="replace")

        match = WEBLINK_GET_RE.search(page)
        if not match:
            raise ValueError("Cloud Mail не вернул адрес скачивания")

        weblink = urlparse(public_url).path.removeprefix("/public/").strip("/")
        download_url = f"{html.unescape(match.group('url')).rstrip('/')}/{weblink}"
        download_request = Request(
            download_url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urlopen(download_request, timeout=60) as response:
            content_length = int(response.headers.get("Content-Length") or 0)
            if content_length > MAX_IMAGE_SIZE:
                raise ValueError("изображение превышает 25 МБ")
            content = response.read(MAX_IMAGE_SIZE + 1)
            if len(content) > MAX_IMAGE_SIZE:
                raise ValueError("изображение превышает 25 МБ")
            filename = Path(unquote(urlparse(response.geturl()).path)).name

        with Image.open(io.BytesIO(content)) as image:
            image.verify()

        return content, filename
