from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "stock_quantity",
        "stock_status",
        "is_active",
        "is_featured",
    )
    list_filter = (
        "category",
        "storage_type",
        "product_type",
        "stock_status",
        "is_active",
        "is_featured",
    )
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
