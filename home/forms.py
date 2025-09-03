# home/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
from .models import Eleve, Frais, Paiement, Classe, Niveau, Cycle, Parent, Utilisateur

# ===========================
# Formulaire : Caisse enregistreuse
# ===========================
# home/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Frais, Niveau
from decimal import Decimal

# ===========================
# Formulaire : Ajout de frais
# ===========================
class FraisForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier des frais scolaires.
    Optimisé pour le déploiement en production selon les bonnes pratiques Django.
    """
    class Meta:
        model = Frais
        fields = ['niveau', 'categorie', 'description', 'montant', 'date_limite']
        widgets = {
            'niveau': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'categorie': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Frais de scolarité trimestriel'),
                'required': True
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '1',
                'placeholder': '0'
            }),
            'date_limite': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            })
        }
        labels = {
            'niveau': _("Niveau"),
            'categorie': _("Catégorie"),
            'description': _("Description"),
            'montant': _("Montant (XAF)"),
            'date_limite': _("Date limite de paiement")
        }
        help_texts = {
            'montant': _("Montant en Francs CFA - pas de décimales nécessaires"),
            'date_limite': _("Date à laquelle le paiement doit être effectué")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tri des niveaux pour une meilleure performance
        self.fields['niveau'].queryset = Niveau.objects.select_related('cycle').all().order_by(
            'cycle__nom', 'nom'
        )
        
        # Initialiser la date limite à demain par défaut
        if not self.instance.pk:
            tomorrow = date.today() + timedelta(days=1)
            self.fields['date_limite'].initial = tomorrow

    def clean_montant(self):
        """Validation du montant"""
        montant = self.cleaned_data.get('montant')
        
        # Vérifier que le montant est positif
        if montant <= 0:
            raise forms.ValidationError(
                _("Le montant doit être supérieur à zéro")
            )
        
        # Utiliser Decimal pour éviter les problèmes de précision
        return Decimal(str(montant))

    def clean_date_limite(self):
        """Validation de la date limite"""
        date_limite = self.cleaned_data.get('date_limite')
        
        # Vérifier que la date n'est pas dans le passé
        if date_limite < date.today():
            raise forms.ValidationError(
                _("La date limite ne peut pas être dans le passé")
            )
        
        return date_limite

    def clean(self):
        """Validation croisée des champs"""
        cleaned_data = super().clean()
        categorie = cleaned_data.get('categorie')
        description = cleaned_data.get('description')
        
        # Vérifier que la description n'est pas vide
        if description and len(description.strip()) < 5:
            self.add_error('description', 
                          _("La description doit contenir au moins 5 caractères"))
        
        return cleaned_data
    
    


class CaisseForm(forms.Form):
    """Formulaire simplifié pour la caisse enregistreuse (style supermarché)"""
    
    eleve = forms.ModelChoiceField(
        queryset=Eleve.objects.select_related('utilisateur', 'classe_actuelle').all(),
        label=_("Élève"),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'eleve-select'
        }),
        empty_label=_("Sélectionnez un élève")
    )
    
    frais = forms.ModelChoiceField(
        queryset=Frais.objects.select_related('niveau').all(),
        label=_("Frais à payer"),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'frais-select'
        }),
        empty_label=_("Sélectionnez les frais")
    )
    
    montant_paye = forms.DecimalField(
        label=_("Montant payé"),
        max_digits=10,
        decimal_places=0,  # Pas de décimales pour les XAF
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'montant-pay',
            'placeholder': '0',
            'step': '1',
            'autofocus': 'autofocus'
        })
    )
    
    type_paiement = forms.ChoiceField(
        choices=[
            ('Espèces', _('Espèces')),
            ('Carte Bancaire', _('Carte Bancaire (Visa/MasterCard)')),
            ('Mobile Money', _('Mobile Money')),
            ('Airtel Money', _('Airtel Money')),
            ('OnyFast', _('OnyFast')),
            ('Virement', _('Virement bancaire')),
            ('Assurance', _('Paiement par assurance')),
            ('Autre', _('Autre')),
        ],
        label=_("Mode de paiement"),
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'type-paiement'
        })
    )
    
    numero_transaction = forms.CharField(
        label=_("Référence de transaction"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'numero-transaction',
            'placeholder': _('Référence de transaction')
        })
    )
    
    def __init__(self, *args, **kwargs):
        """Initialisation du formulaire avec des données optionnelles"""
        eleve_id = kwargs.pop('eleve_id', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les élèves si nécessaire
        if eleve_id:
            self.fields['eleve'].queryset = Eleve.objects.filter(id=eleve_id).select_related('utilisateur', 'classe_actuelle')
        
        # Si un élève est fourni dans les données initiales
        if 'initial' in kwargs and 'eleve' in kwargs['initial']:
            eleve_id = kwargs['initial']['eleve']
            try:
                eleve = Eleve.objects.get(id=eleve_id)
                self.fields['frais'].queryset = Frais.objects.filter(
                    niveau=eleve.classe_actuelle.niveau
                ).order_by('date_limite')
            except Eleve.DoesNotExist:
                self.fields['frais'].queryset = Frais.objects.none()
    
    def clean_montant_paye(self):
        """Validation du montant payé"""
        montant_paye = self.cleaned_data.get('montant_paye')
        
        # Vérifier que le montant est positif
        if montant_paye <= 0:
            raise ValidationError(
                _("Le montant payé doit être supérieur à zéro")
            )
        
        return montant_paye
    
    def clean(self):
        """Validation croisée des champs"""
        cleaned_data = super().clean()
        eleve = cleaned_data.get('eleve')
        frais = cleaned_data.get('frais')
        montant_paye = cleaned_data.get('montant_paye')
        
        # Vérifier que l'élève et les frais sont sélectionnés
        if eleve and frais:
            # Calculer le montant restant
            montant_restant = frais.get_montant_restant(eleve)
            montant_total = frais.montant
            
            # Vérifier que le montant payé ne dépasse pas le montant total
            if montant_paye > (montant_total + montant_restant):
                self.add_error('montant_paye', 
                              _("Le montant payé ne peut pas dépasser le montant total des frais"))
        
        return cleaned_data


# ===========================
# Formulaire : Paiement
# ===========================
class PaiementForm(forms.ModelForm):
    """Formulaire pour enregistrer un paiement"""
    
    class Meta:
        model = Paiement
        fields = ['eleve', 'frais', 'montant_paye', 'type_paiement', 'numero_transaction', 'notes', 'date_paiement']
        widgets = {
            'eleve': forms.Select(attrs={'class': 'form-select'}),
            'frais': forms.Select(attrs={'class': 'form-select'}),
            'montant_paye': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'type_paiement': forms.Select(attrs={'class': 'form-select'}),
            'numero_transaction': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_paiement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'eleve': _('Élève'),
            'frais': _('Frais'),
            'montant_paye': _('Montant payé (XAF)'),
            'type_paiement': _('Mode de paiement'),
            'numero_transaction': _('Référence de transaction'),
            'notes': _('Notes'),
            'date_paiement': _('Date du paiement'),
        }

    def __init__(self, *args, **kwargs):
        eleve_id = kwargs.pop('eleve_id', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les élèves si nécessaire
        if eleve_id:
            self.fields['eleve'].queryset = Eleve.objects.filter(id=eleve_id).select_related('utilisateur', 'classe_actuelle')
        
        # Initialiser la date à aujourd'hui
        if not self.instance.pk:
            self.fields['date_paiement'].initial = date.today()
        
        # Si un élève est fourni dans les données initiales
        if 'initial' in kwargs and 'eleve' in kwargs['initial']:
            eleve_id = kwargs['initial']['eleve']
            try:
                eleve = Eleve.objects.get(id=eleve_id)
                self.fields['frais'].queryset = Frais.objects.filter(
                    niveau=eleve.classe_actuelle.niveau
                ).select_related('niveau').order_by('date_limite')
            except Eleve.DoesNotExist:
                self.fields['frais'].queryset = Frais.objects.none()
    
    def clean_montant_paye(self):
        """Validation du montant payé"""
        montant_paye = self.cleaned_data.get('montant_paye')
        
        # Vérifier que le montant est positif
        if montant_paye <= 0:
            raise ValidationError(
                _("Le montant payé doit être supérieur à zéro")
            )
        
        return montant_paye
    
    def clean(self):
        """Validation croisée des champs"""
        cleaned_data = super().clean()
        eleve = cleaned_data.get('eleve')
        frais = cleaned_data.get('frais')
        montant_paye = cleaned_data.get('montant_paye')
        
        # Vérifier que l'élève et les frais sont sélectionnés
        if eleve and frais:
            # Calculer le montant restant
            montant_restant = frais.get_montant_restant(eleve)
            
            # Vérifier que le montant payé ne dépasse pas le montant restant
            if montant_paye > montant_restant:
                self.add_error('montant_paye', 
                              _("Le montant ne peut pas dépasser %(montant)s XAF (montant restant)") % 
                              {'montant': montant_restant})
        
        return cleaned_data


# ===========================
# Formulaire : Classe
# ===========================
class ClasseForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une classe.
    Optimisé pour le déploiement en production.
    """
    class Meta:
        model = Classe
        fields = ['niveau', 'nom', 'effectif_max']
        widgets = {
            'niveau': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: A, B, C, D'),
                'required': True
            }),
            'effectif_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '150',
                'placeholder': _('Max: 100')
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
        # Tri des niveaux pour améliorer la performance
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
    Optimisé pour le déploiement en production.
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
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: jdupont')})
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('j.dupont@email.com')})
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
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('EL001')}),
            'date_naissance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'genre': forms.Select(attrs={'class': 'form-select'}),
            'contact_urgence': forms.TextInput(attrs={'class': 'form-control'}),
            'infos_medicaux': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'classe_actuelle': forms.Select(attrs={'class': 'form-select'}),
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

        # Filtrer les classes disponibles avec optimisation des requêtes
        self.fields['classe_actuelle'].queryset = Classe.objects.select_related('niveau').all().order_by('niveau__cycle__nom', 'niveau__nom', 'nom')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            if Utilisateur.objects.filter(username=username).exclude(
                pk=self.instance.utilisateur.pk if self.instance.pk else None
            ).exists():
                raise ValidationError(_("Ce nom d'utilisateur est déjà utilisé."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if Utilisateur.objects.filter(email=email).exclude(
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
            user = Utilisateur(role='eleve')

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


# ===========================
# Formulaire : Inscription
# ===========================
class RegisterForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('exemple@ecole.com')
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Jean')
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Dupont')
        })
    )
    role = forms.ChoiceField(
        choices=Utilisateur.ROLES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('jean_dupont')
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )
    password2 = forms.CharField(
        label=_("Confirmation du mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )

    class Meta:
        model = Utilisateur
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2')
        
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Utilisateur.objects.filter(username=username).exists():
            raise ValidationError(_("Ce nom d'utilisateur est déjà utilisé."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exists():
            raise ValidationError(_("Cet email est déjà utilisé."))
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError(_("Les mots de passe ne correspondent pas."))
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# ===========================
# Formulaire : Cycle
# ===========================
class CycleForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un cycle scolaire.
    Optimisé pour le déploiement en production.
    """
    class Meta:
        model = Cycle
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Primaire, Secondaire, Collège, Lycée'),
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
    Optimisé pour le déploiement en production.
    """
    class Meta:
        model = Niveau
        fields = ['cycle', 'nom']
        widgets = {
            'cycle': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: 6e, 5e, 4e, 3e, 2nd, 1ère, Terminale'),
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
        # Tri des cycles pour améliorer la performance
        self.fields['cycle'].queryset = Cycle.objects.all().order_by('nom')

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


# ===========================
# Formulaire : Enseignant
# ===========================
class EnseignantForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un enseignant.
    Optimisé pour le déploiement en production.
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
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: m_dupont')})
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('m.dupont@email.com')})
    )
    telephone = forms.CharField(
        label=_("Téléphone"),
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('+237 6XX XXX XXX')}),
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
            if Utilisateur.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                raise ValidationError(_("Ce nom d'utilisateur est déjà utilisé."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if Utilisateur.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
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
            user = Utilisateur(role='enseignant')
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


# ===========================
# Formulaire : Parent
# ===========================
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
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: m_kouma')})
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('m.kouma@email.com')})
    )
    telephone = forms.CharField(
        label=_("Téléphone"),
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('+237 6XX XXX XXX')}),
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
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
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
                parent = Parent.objects.get(utilisateur=self.instance)
                self.fields['enfants'].initial = parent.enfants.all()
            except Parent.DoesNotExist:
                pass
        self.fields['enfants'].queryset = Eleve.objects.select_related('utilisateur').all().order_by('utilisateur__last_name')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and Utilisateur.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_("Ce nom d'utilisateur est déjà utilisé."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and Utilisateur.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
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
            user = Utilisateur(role='parent')
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