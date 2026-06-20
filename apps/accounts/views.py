from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.orders.models import Order

from .forms import ProfileForm, RegistrationForm
from .models import Profile


def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("accounts:cabinet")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Аккаунт создан.")
            return redirect("accounts:cabinet")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def cabinet(request: HttpRequest) -> HttpResponse:
    profile, _ = Profile.objects.get_or_create(user=request.user)
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related("items")
        .order_by("-created_at")
    )
    return render(
        request,
        "accounts/cabinet.html",
        {
            "orders": orders,
            "profile": profile,
        },
    )


@login_required
def profile_edit(request: HttpRequest) -> HttpResponse:
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            instance=request.user,
            initial={
                "phone": profile.phone,
                "delivery_address": profile.delivery_address,
            },
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Данные профиля обновлены.")
            return redirect("accounts:cabinet")
    else:
        form = ProfileForm(
            instance=request.user,
            initial={
                "phone": profile.phone,
                "delivery_address": profile.delivery_address,
            },
        )

    return render(request, "accounts/profile_edit.html", {"form": form})
