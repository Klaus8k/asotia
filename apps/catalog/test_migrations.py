from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class CatalogRefactorMigrationTests(TransactionTestCase):
    migrate_from = ("catalog", "0004_category_slug_unique_and_sync_stock")
    migrate_to = ("catalog", "0005_catalog_refactor")

    def test_existing_product_is_preserved_and_classified(self):
        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_from])
        old_apps = executor.loader.project_state([self.migrate_from]).apps

        Category = old_apps.get_model("catalog", "Category")
        Product = old_apps.get_model("catalog", "Product")
        old_category = Category.objects.create(
            name="Полуфабрикаты",
            slug="полуфабрикаты",
        )
        product = Product.objects.create(
            category=old_category,
            name="Филе индейки",
            slug="филе-индейки",
            description="",
            price=Decimal("480.00"),
            storage_type="frozen",
            product_type="semi_finished",
            meat_type="turkey",
            stock_quantity=5,
        )

        executor = MigrationExecutor(connection)
        executor.migrate([self.migrate_to])
        new_apps = executor.loader.project_state([self.migrate_to]).apps

        MigratedProduct = new_apps.get_model("catalog", "Product")
        migrated = MigratedProduct.objects.get(pk=product.pk)
        self.assertEqual(migrated.name, "Филе индейки")
        self.assertEqual(migrated.category.slug, "заморозка")
        self.assertCountEqual(
            migrated.attribute_values.values_list(
                "attribute__slug",
                "slug",
            ),
            [
                ("product-type", "semi_finished"),
                ("composition", "poultry"),
                ("main-ingredient", "turkey"),
            ],
        )
        self.assertFalse(
            new_apps.get_model("catalog", "Category")
            .objects.get(pk=old_category.pk)
            .is_active
        )

        product_columns = {
            column.name
            for column in connection.introspection.get_table_description(
                connection.cursor(),
                "catalog_product",
            )
        }
        self.assertIn("storage_type", product_columns)
        self.assertIn("stock_status", product_columns)
