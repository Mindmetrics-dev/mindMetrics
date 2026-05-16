from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

ESTADO_CIVIL_CHOICES = [
    ('', '---------'),
    ('soltero',      'Soltero/a'),
    ('noviazgo',     'Noviazgo'),
    ('union_libre',  'Unión libre'),
    ('casado',       'Casado/a'),
    ('divorciado',   'Divorciado/a'),
    ('viudo',        'Viudo/a'),
]


class PerfilForm(forms.ModelForm):
    # ── Campos de acceso (del CustomUser) ─────────────────────────────────────
    username = forms.CharField(
        max_length=150,
        label="Nickname",
        widget=forms.TextInput(attrs={'class': 'form-group__input'}),
    )
    email = forms.EmailField(
        label="Email de acceso",
        widget=forms.EmailInput(attrs={'class': 'form-group__input'}),
    )

    # ── Salud mental (también en CustomUser) ──────────────────────────────────
    en_tratamiento = forms.ChoiceField(
        choices=[('', '---------'), ('si', 'Sí'), ('no', 'No')],
        required=False,
        label="¿Empezaste o estás en tratamiento por algún diagnóstico?",
        widget=forms.Select(attrs={'class': 'form-group__input'}),
    )
    detalle_tratamiento = forms.CharField(
        required=False,
        label="Si respondiste Sí, describe brevemente:",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-group__input',
            'placeholder': 'Ej. Terapia cognitivo-conductual, tratamiento farmacológico, etc.',
        }),
    )

    class Meta:
        model = User
        fields = ['edad', 'estado_civil']
        labels = {
            'edad': 'Edad (años)',
            'estado_civil': 'Estado civil',
        }
        widgets = {
            'edad': forms.NumberInput(attrs={
                'class': 'form-group__input',
                'min': 0,
                'max': 120,
                'placeholder': 'Ej. 25',
            }),
            'estado_civil': forms.Select(
                choices=ESTADO_CIVIL_CHOICES,
                attrs={'class': 'form-group__input'},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar campos extra desde la instancia (CustomUser)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.username
            self.fields['email'].initial = self.instance.email
            self.fields['en_tratamiento'].initial = self.instance.en_tratamiento or ''
            self.fields['detalle_tratamiento'].initial = self.instance.detalle_tratamiento or ''

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.en_tratamiento = self.cleaned_data.get('en_tratamiento', '')
        user.detalle_tratamiento = self.cleaned_data.get('detalle_tratamiento', '')
        if commit:
            user.save()
        return user
