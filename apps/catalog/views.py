from django.http import HttpRequest, HttpResponse


def catalog_index(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Каталог")