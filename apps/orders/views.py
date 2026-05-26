from django.http import HttpRequest, HttpResponse


def checkout(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Оформление заказа")