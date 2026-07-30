import re
import uuid

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile


User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "mail@example.com",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Введите пароль",
            }
        ),
    )

    def clean(self) -> dict:
        email = self.cleaned_data.get("username", "").strip()
        password = self.cleaned_data.get("password")

        if email and password:
            user = User.objects.filter(email__iexact=email).first()
            if user is not None:
                self.user_cache = authenticate(
                    self.request,
                    username=user.get_username(),
                    password=password,
                )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        help_text="Email будет использоваться для входа в личный кабинет.",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "mail@example.com",
            }
        ),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=30,
        required=False,
        help_text="Необязательно.",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "+7 999 123-45-67",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "password1", "password2", "phone")

    def clean_email(self) -> str:
        email = User.objects.normalize_email(self.cleaned_data["email"].strip()).lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Пользователь с таким email уже зарегистрирован."
            )
        return email

    def clean_phone(self) -> str:
        phone = self.cleaned_data["phone"].strip()
        if phone:
            digits = re.sub(r"\D", "", phone)
            if len(digits) < 10 or len(digits) > 15:
                raise forms.ValidationError("Введите корректный номер телефона.")
        return phone

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.username = uuid.uuid4().hex
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                phone=self.cleaned_data["phone"],
            )
        return user


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "+7 999 123-45-67",
            }
        ),
    )
    delivery_address = forms.CharField(
        label="Адрес доставки",
        max_length=500,
        required=False,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "street-address",
                "placeholder": "Город, улица, дом, квартира",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "email",
            "phone",
            "delivery_address",
        )
        labels = {
            "first_name": "Имя",
            "email": "Email",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
        }

    def clean_email(self) -> str:
        email = User.objects.normalize_email(self.cleaned_data["email"].strip()).lower()
        existing_users = User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        )
        if existing_users.exists():
            raise forms.ValidationError(
                "Пользователь с таким email уже зарегистрирован."
            )
        return email

    def clean_phone(self) -> str:
        phone = self.cleaned_data["phone"].strip()
        if phone:
            digits = re.sub(r"\D", "", phone)
            if len(digits) < 10 or len(digits) > 15:
                raise forms.ValidationError("Введите корректный номер телефона.")
        return phone

    def save(self, commit: bool = True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "phone": self.cleaned_data["phone"].strip(),
                    "delivery_address": self.cleaned_data["delivery_address"].strip(),
                },
            )
        return user
