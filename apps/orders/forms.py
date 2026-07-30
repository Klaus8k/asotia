import re

from django import forms

from .models import Order


class CheckoutForm(forms.ModelForm):
    phone = forms.CharField(
        label="Телефон",
        max_length=30,
        help_text=(
            "Нужен для подтверждения заказа и согласования деталей. "
            "Рекламу не отправляем."
        ),
        widget=forms.TextInput(
            attrs={
                "autocomplete": "tel",
                "inputmode": "tel",
                "placeholder": "+7 999 123-45-67",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        help_text=(
            "Необязательно. Укажите, если хотите получить информацию о заказе по email."
        ),
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "mail@example.com",
            }
        ),
    )
    delivery_address = forms.CharField(
        label="Адрес доставки",
        max_length=500,
        required=False,
        help_text="Необязательно.",
        widget=forms.TextInput(
            attrs={
                "autocomplete": "street-address",
                "placeholder": "Город, улица, дом, квартира",
            }
        ),
    )

    class Meta:
        model = Order
        fields = (
            "customer_name",
            "phone",
            "email",
            "delivery_address",
            "comment",
        )
        widgets = {
            "customer_name": forms.TextInput(
                attrs={"autocomplete": "name", "placeholder": "Иван"}
            ),
            "comment": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Подъезд, этаж или пожелания к заказу",
                }
            ),
        }

    def clean_phone(self) -> str:
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 10 or len(digits) > 15:
            raise forms.ValidationError("Введите корректный номер телефона.")
        return phone
