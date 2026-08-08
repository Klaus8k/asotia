from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from apps.orders.models import Order

from .forms import ProfileForm, RegistrationForm
from .models import Profile


User = get_user_model()
DUPLICATE_EMAIL_ERROR = "Пользователь с таким email уже зарегистрирован."


def register(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("accounts:cabinet")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
            except IntegrityError:
                if User.objects.filter(
                    email__iexact=form.cleaned_data["email"]
                ).exists():
                    form.add_error("email", DUPLICATE_EMAIL_ERROR)
                else:
                    raise
            else:
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
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                has_conflict = (
                    User.objects.filter(email__iexact=form.cleaned_data["email"])
                    .exclude(pk=request.user.pk)
                    .exists()
                )
                if has_conflict:
                    form.add_error("email", DUPLICATE_EMAIL_ERROR)
                else:
                    raise
            else:
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
