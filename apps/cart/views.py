from django.http import HttpRequest, HttpResponse


def cart_detail(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Корзина")