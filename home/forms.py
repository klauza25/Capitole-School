# gestion/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur
# home/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Cycle, Niveau


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@ecole.com'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Jean'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dupont'
        })
    )
    role = forms.ChoiceField(
        choices=Utilisateur.ROLES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'jean_dupont'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )

    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2')
        
        

# ===========================
# Formulaire : Cycle
# ===========================
class CycleForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un cycle scolaire.
    """
    class Meta:
        model = Cycle
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Primaire, Secondaire, Collège, Lycée',
                'required': True
            })
        }
        labels = {
            'nom': _("Nom du cycle")
        }
        help_texts = {
            'nom': _("Ex: Primaire, Secondaire, Collège, Lycée")
        }

    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if nom:
            nom = nom.strip().title()  # Format propre
            # Vérifie l'unicité (insensible à la casse)
            if Cycle.objects.filter(nom__iexact=nom).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError(
                    _("Un cycle avec ce nom existe déjà.")
                )
        return nom


# ===========================
# Formulaire : Niveau
# ===========================
class NiveauForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un niveau scolaire.
    Le cycle est sélectionnable, et le nom est unique par cycle.
    """
    class Meta:
        model = Niveau
        fields = ['cycle', 'nom']
        widgets = {
            'cycle': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 6e, 5e, 4e, 3e, 2nd, 1ère, Terminale',
                'required': True
            })
        }
        labels = {
            'cycle': _("Cycle"),
            'nom': _("Nom du niveau")
        }
        help_texts = {
            'nom': _("Ex: 6e, 5e, 4e, 3e, 2nd, 1ère, Terminale")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionnel : trier les cycles par nom
        self.fields['cycle'].queryset = Cycle.objects.all().order_by('nom')
        if self.instance.pk:
            # Si modification, affiche le cycle actuel même s'il est désactivé
            pass

    def clean(self):
        cleaned_data = super().clean()
        cycle = cleaned_data.get('cycle')
        nom = cleaned_data.get('nom')

        if cycle and nom:
            nom = nom.strip().title()
            cleaned_data['nom'] = nom

            # Vérifie l'unicité combinée (cycle, nom)
            if Niveau.objects.filter(cycle=cycle, nom__iexact=nom).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError(
                    _("Un niveau avec ce nom existe déjà dans ce cycle.")
                )
        return cleaned_data

    def clean_nom(self):
        nom = self.cleaned_data.get('nom')
        if nom:
            return nom.strip().title()
        return nom