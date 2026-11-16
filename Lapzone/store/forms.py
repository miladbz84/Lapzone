from django import forms
from django.contrib.auth.models import User

from .models import UserProfile


class ProfileUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "نام",
            "last_name": "نام خانوادگی",
            "email": "ایمیل",
        }
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "account-input", "autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"class": "account-input", "autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"class": "account-input", "autocomplete": "email"}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("phone", "city", "postal_code", "address")
        labels = {
            "phone": "شماره تماس",
            "city": "شهر",
            "postal_code": "کد پستی",
            "address": "نشانی کامل",
        }
        widgets = {
            "phone": forms.TelInput(attrs={"class": "account-input", "autocomplete": "tel", "dir": "ltr"}),
            "city": forms.TextInput(attrs={"class": "account-input", "autocomplete": "address-level2"}),
            "postal_code": forms.TextInput(attrs={"class": "account-input", "autocomplete": "postal-code", "dir": "ltr"}),
            "address": forms.Textarea(attrs={"class": "account-input", "autocomplete": "street-address", "rows": 4}),
        }