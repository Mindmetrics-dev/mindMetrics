from django import forms
from .models import DatasetRegistro

class DatasetForm(forms.ModelForm):
    class Meta:
        model = DatasetRegistro
        fields = ['nombre', 'email', 'edad', 'profesion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'edad': forms.NumberInput(attrs={'class': 'form-control'}),
            'profesion': forms.TextInput(attrs={'class': 'form-control'}),
        }