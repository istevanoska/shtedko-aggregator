from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class IngredientForm(forms.Form):
    ingredients = forms.CharField(
        label="Што имаш во фрижидерот?",
        widget=forms.Textarea(attrs={"placeholder": "Јајца, млеко, брашно...", "rows": 5})
    )