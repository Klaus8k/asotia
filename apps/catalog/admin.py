from django.contrib import admin

from .models import (
    Attribute,
    AttributeValue,
    Category,
    Collection,
    CollectionRule,
    Product,
    ProductAttributeValue,
)


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 0
    fields = ("name", "slug", "is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 0
    autocomplete_fields = ("attribute_value",)


class CollectionRuleInline(admin.TabularInline):
    model = CollectionRule
    extra = 0
    autocomplete_fields = ("attribute_value",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sort_order", "updated_at")
    list_editable = ("is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")
    inlines = (AttributeValueInline,)


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ("name", "attribute", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    list_filter = ("attribute", "is_active")
    search_fields = ("name", "slug", "attribute__name")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("attribute__sort_order", "attribute__name", "sort_order", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "stock_quantity",
        "is_active",
        "is_new",
        "updated_at",
    )
    list_editable = ("stock_quantity", "is_active", "is_new")
    list_filter = (
        "category",
        "is_active",
        "is_new",
        "attribute_values__attribute",
        "attribute_values",
    )
    search_fields = ("name", "description", "attribute_values__name")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("category", "name")
    list_select_related = ("category",)
    inlines = (ProductAttributeValueInline,)


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "sort_order", "updated_at")
    list_editable = ("is_active", "sort_order")
    list_filter = ("is_active", "categories")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("categories",)
    ordering = ("sort_order", "name")
    inlines = (CollectionRuleInline,)
