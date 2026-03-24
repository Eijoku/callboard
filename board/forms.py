from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from .models import Advertisement, Response


class SignUpForm(forms.Form):
    email = forms.EmailField(label="E-mail")
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтвердите пароль", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("Пользователь с таким e-mail уже зарегистрирован.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Пароли не совпадают.")
        return cleaned_data


class ConfirmationForm(forms.Form):
    email = forms.EmailField(label="E-mail")
    code = forms.CharField(label="Код подтверждения", min_length=6, max_length=6)


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail")


class AdvertisementForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = ("category", "title", "content")


class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ("text",)
        widgets = {
            "text": forms.Textarea(attrs={"rows": 4}),
        }
