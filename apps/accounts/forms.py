import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile


User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "username",
                "placeholder": "Введите логин",
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


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "mail@example.com",
            }
        ),
    )
    first_name = forms.CharField(
        label="Имя",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "given-name",
                "placeholder": "Иван",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "email", "password1", "password2")
        labels = {"username": "Логин"}
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "autocomplete": "username",
                    "placeholder": "Придумайте логин",
                }
            )
        }

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Пользователь с таким email уже зарегистрирован."
            )
        return email


class ProfileForm(forms.ModelForm):
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
            "last_name",
            "email",
            "phone",
            "delivery_address",
        )
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "email": "Email",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def clean_email(self) -> str:
        email = self.cleaned_data["email"].strip().lower()
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
                raise forms.ValidationError(
                    "Введите корректный номер телефона."
                )
        return phone

    def save(self, commit: bool = True):
        user = super().save(commit=commit)
        if commit:
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "phone": self.cleaned_data["phone"].strip(),
                    "delivery_address": self.cleaned_data[
                        "delivery_address"
                    ].strip(),
                },
            )
        return user
