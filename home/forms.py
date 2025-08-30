# gestion/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Parent, Utilisateur
# home/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Cycle, Niveau
# home/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Classe, Eleve, Niveau

User = get_user_model()


# ===========================
# Formulaire : Classe
# ===========================
class ClasseForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une classe.
    """
    class Meta:
        model = Classe
        fields = ['niveau', 'nom', 'effectif_max']
        widgets = {
            'niveau': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: A, B, C, D',
                'required': True
            }),
            'effectif_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '150',
                'placeholder': 'Max: 100'
            })
        }
        labels = {
            'niveau': _("Niveau"),
            'nom': _("Nom de la classe"),
            'effectif_max': _("Effectif maximum")
        }
        help_texts = {
            'nom': _("Ex: A, B, C, D"),
            'effectif_max': _("Nombre maximum d'élèves autorisés dans cette classe")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionnel : trier les niveaux
        self.fields['niveau'].queryset = Niveau.objects.select_related('cycle').all().order_by('cycle__nom', 'nom')

    def clean(self):
        cleaned_data = super().clean()
        niveau = cleaned_data.get('niveau')
        nom = cleaned_data.get('nom')

        if niveau and nom:
            # Vérifie unicité (niveau, nom)
            if Classe.objects.filter(niveau=niveau, nom__iexact=nom).exclude(pk=self.instance.pk).exists():
                raise ValidationError(
                    _("Une classe avec ce nom existe déjà dans ce niveau.")
                )
        return cleaned_data


# ===========================
# Formulaire : Élève
# ===========================
class EleveForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un élève.
    """
    # Champs liés à l'utilisateur
    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        label=_("Nom d'utilisateur"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: jdupont'})
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'j.dupont@email.com'})
    )
    password1 = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    password2 = forms.CharField(
        label=_("Confirmer le mot de passe"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Eleve
        fields = [
            'utilisateur', 'matricule', 'date_naissance', 'genre',
            'contact_urgence', 'infos_medicaux', 'classe_actuelle'
        ]
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EL001'}),
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'genre': forms.Select(attrs={'class': 'form-control'}),
            'contact_urgence': forms.TextInput(attrs={'class': 'form-control'}),
            'infos_medicaux': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'classe_actuelle': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'matricule': _("Matricule"),
            'date_naissance': _("Date de naissance"),
            'genre': _("Genre"),
            'contact_urgence': _("Contact d'urgence"),
            'infos_medicaux': _("Informations médicales"),
            'classe_actuelle': _("Classe actuelle"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si modification, pré-remplir les champs utilisateur
        if self.instance.pk and hasattr(self.instance, 'utilisateur'):
            user = self.instance.utilisateur
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email

        # Filtrer les classes disponibles
        self.fields['classe_actuelle'].queryset = Classe.objects.select_related('niveau').all().order_by('niveau__cycle__nom', 'niveau__nom', 'nom')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if User.objects.filter(username=username).exclude(
                pk=self.instance.utilisateur.pk if self.instance.pk else None
            ).exists():
                raise ValidationError(_("Ce nom d'utilisateur est déjà utilisé."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exclude(
                pk=self.instance.utilisateur.pk if self.instance.pk else None
            ).exists():
                raise ValidationError(_("Cet email est déjà utilisé."))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        # Vérifie la confirmation du mot de passe
        if password1 or password2:
            if password1 != password2:
                raise ValidationError(_("Les mots de passe ne correspondent pas."))

        return cleaned_data

    def save(self, commit=True):
        # Gestion de l'utilisateur
        if self.instance.pk:
            user = self.instance.utilisateur
        else:
            user = User(role='eleve')

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']

        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        elif not self.instance.pk:
            user.set_password('Capitole123')  # Mot de passe par défaut

        if commit:
            user.save()

        # Enregistre l'élève
        eleve = super().save(commit=False)
        eleve.utilisateur = user
        if commit:
            eleve.save()
        return eleve


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
    

class EnseignantForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un enseignant.
    """
    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        label=_("Nom d'utilisateur"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: m_dupont'})
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'm.dupont@email.com'})
    )
    telephone = forms.CharField(
        label=_("Téléphone"),
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+237 6XX XXX XXX'}),
        required=False
    )
    password1 = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    password2 = forms.CharField(
        label=_("Confirmer le mot de passe"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'username', 'email', 'telephone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['first_name'].initial = self.instance.first_name
            self.fields['last_name'].initial = self.instance.last_name
            self.fields['telephone'].initial = self.instance.telephone

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                raise ValidationError(_("Ce nom d'utilisateur est déjà utilisé."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError(_("Cet email est déjà utilisé."))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                raise ValidationError(_("Les mots de passe ne correspondent pas."))
        return cleaned_data

    def save(self, commit=True):
        if self.instance.pk:
            user = self.instance
        else:
            user = User(role='enseignant')
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.telephone = self.cleaned_data['telephone']
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        elif not self.instance.pk:
            user.set_password('Capitole123')
        if commit:
            user.save()
        return user
    
    



User = get_user_model()

class ParentForm(forms.ModelForm):
    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    username = forms.CharField(
        label=_("Nom d'utilisateur"),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: m_kouma'})
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'm.kouma@email.com'})
    )
    telephone = forms.CharField(
        label=_("Téléphone"),
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+237 6XX XXX XXX'}),
        required=False
    )
    password1 = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    password2 = forms.CharField(
        label=_("Confirmer le mot de passe"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    enfants = forms.ModelMultipleChoiceField(
        queryset=Eleve.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '8'}),
        required=False,
        label=_("Associer des enfants")
    )

    class Meta:
        model = Utilisateur
        fields = ['first_name', 'last_name', 'username', 'email', 'telephone']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            try:
                parent = self.instance.parent_profile
                self.fields['enfants'].initial = parent.enfants.all()
            except Parent.DoesNotExist:
                pass
        self.fields['enfants'].queryset = Eleve.objects.select_related('utilisateur').all().order_by('utilisateur__last_name')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Ce nom d'utilisateur est déjà utilisé."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Cet email est déjà utilisé."))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 or password2:
            if password1 != password2:
                raise ValidationError(_("Les mots de passe ne correspondent pas."))
        return cleaned_data

    def save(self, commit=True):
        if self.instance.pk:
            user = self.instance
        else:
            user = User(role='parent')
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.telephone = self.cleaned_data['telephone']
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        elif not self.instance.pk:
            user.set_password('Capitole123')
        if commit:
            user.save()
            parent, created = Parent.objects.get_or_create(utilisateur=user)
            parent.enfants.set(self.cleaned_data['enfants'])
        return user