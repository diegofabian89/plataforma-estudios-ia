# core/forms.py

from django import forms
from django.contrib.auth import authenticate, get_user_model

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django import forms
from .models import Apunte, Categoria
from core.models import PerfilUsuario

User = get_user_model()



class ApunteForm(forms.ModelForm):
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="---------",  # <--- Añade esto para mostrar una opción vacía
    )
    titulo = forms.CharField(
        max_length=200,
        required=False,  # <--- Añade esta línea para que el campo no sea obligatorio en el form
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Apunte
        fields = ['titulo', 'archivo', 'texto', 'categoria']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'texto': forms.Textarea(attrs={'id': 'textApuntes', 'class': 'form-control', 'rows': 5}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        archivo = cleaned_data.get('archivo')
        texto = cleaned_data.get('texto')

        if not archivo and not texto:
            raise forms.ValidationError("Debes subir un archivo o escribir texto.")
        return cleaned_data


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'style': 'background: rgba(255, 255, 255, 0.1); color: white; border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; padding: 8px;font-size: 0.8rem;'
        })
    )
    ESTUDIOS = [
        ('primaria', 'Educación Primaria'),
        ('eso', 'Educación Secundaria Obligatoria (ESO)'),
        ('bachillerato', 'Bachillerato'),
        ('fp', 'Formación Profesional (FP)'),
        ('universidad', 'Universidad'),
        ('master', 'Máster o Postgrado'),
        ('oposiciones', 'Preparando oposiciones'),
        ('idiomas', 'Estudios de idiomas'),
        ('autoformacion', 'Autoformación / Cursos online'),
        ('no_estudia', 'No soy estudiante'),
        ('otro', 'Otro'),
    ]
    estudio_actual = forms.ChoiceField(
        choices=ESTUDIOS,
        widget=forms.Select(attrs={
            'class': 'form-control glass-style'
        }),
        label="¿Qué estás estudiando?"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo ya está registrado.")
        return email


class CustomEmailLoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        from django.contrib.auth import get_user_model
        User = get_user_model()

        if email and password:
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    #  Guardamos en sesión desde aquí
                    if self.request:
                        self.request.session['inactive_email'] = user.email
                    raise forms.ValidationError("Tu cuenta aún no ha sido activada.")
                self.user_cache = authenticate(username=user.username, password=password)
                if self.user_cache is None:
                    raise forms.ValidationError("Contraseña incorrecta.")
            except User.DoesNotExist:
                raise forms.ValidationError("No existe ninguna cuenta con ese correo.")
        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class PerfilForm(forms.ModelForm):
    username = forms.CharField(label='Nombre de usuario')
    email = forms.EmailField(label='Correo electrónico')
    avatar_default = forms.ChoiceField(
        choices=[('', '--- Ningún avatar ---')] + PerfilUsuario._meta.get_field('avatar_default').choices,
        required=False,
        label='selecciona un avatar',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_avatar_default'})
    )
    eliminar_imagen = forms.BooleanField(
        label="Eliminar imagen de perfil",
        required=False
    )

    class Meta:
        model = PerfilUsuario
        fields = ['estudio_actual', 'imagen', 'avatar_default']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Guardamos el usuario si lo necesitas luego
        super().__init__(*args, **kwargs)

        # Personalizamos el widget del input file
        self.fields['imagen'].widget = forms.FileInput(attrs={
            'class': 'form-control mt-2'
        })

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("Este correo ya está en uso.")
        return email

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            if imagen.size > 8 * 1024 * 1024:  # 2MB límite
                raise forms.ValidationError("La imagen no debe superar los 8MB.")
        return imagen
