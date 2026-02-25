from django import forms
from .models import Contacto
from captcha.fields import CaptchaField

class ContactoForm(forms.ModelForm):
    
    captcha = CaptchaField()  # Campo personalizado fuera de Meta
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['captcha'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Escribe el texto que ves en la imagen',

        })


    class Meta:
        model = Contacto
        fields = ['nombre', 'email', 'asunto', 'mensaje','captcha']  # Agrega 'captcha' aquí
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'tu@email.com'}),
            'asunto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asunto del mensaje'}),
            'mensaje': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Tu mensaje aquí...'}),

        }
