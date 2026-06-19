from django.urls import path

from . import views


app_name = "catalog"

urlpatterns = [
    path("", views.catalog_index, name="index"),
    path(
        "category/<str:category_slug>/",
        views.catalog_index,
        name="category",
    ),
    path(
        "<str:category_slug>/<str:product_slug>/",
        views.product_detail,
        name="product_detail",
    ),
]
