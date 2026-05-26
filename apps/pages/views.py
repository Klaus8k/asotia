from django.http import HttpRequest, HttpResponse


def home(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Asoti Food Shop")


def about(request: HttpRequest) -> HttpResponse:
    return HttpResponse("О нас")


def contacts(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Контакты")


def delivery(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Доставка и оплата")


def privacy(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Политика конфиденциальности")


def terms(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Пользовательское соглашение")