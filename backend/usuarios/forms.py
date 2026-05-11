from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
import pyotp

class CustomUserCreationForm(UserCreationForm):
    phone = forms.CharField(max_length=15, required=False)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone', 'password1', 'password2')

class CustomAuthenticationForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

class TOTPForm(forms.Form):
    token = forms.CharField(max_length=6)