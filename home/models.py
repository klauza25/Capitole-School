# models.py
from datetime import timezone
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
# home/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    """Modèle pour les notifications des utilisateurs"""
    TYPE_NOTIF = [
        ('NOTE', _('Nouvelle note')),
        ('ABSENCE', _('Nouvelle absence')),
        ('MESSAGE', _('Nouveau message')),
        ('PAIEMENT', _('Paiement enregistré')),
        ('AGENDA', _('Événement agenda')),
        ('AUTRE', _('Autre')),
    ]
    
    STATUT_NOTIF = [
        ('NON_LU', _('Non lu')),
        ('LU', _('Lu')),
        ('ARCHIVE', _('Archivé')),
    ]

    utilisateur = models.ForeignKey(
        'Utilisateur',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_("Utilisateur")
    )
    type_notification = models.CharField(
        _("Type de notification"),
        max_length=20,
        choices=TYPE_NOTIF,
        db_index=True
    )
    objet = models.CharField(_("Objet"), max_length=100)
    message = models.TextField(_("Message"))
    lien = models.CharField(_("Lien associé"), max_length=200, blank=True)
    statut = models.CharField(
        _("Statut"),
        max_length=10,
        choices=STATUT_NOTIF,
        default='NON_LU',
        db_index=True
    )
    date_creation = models.DateTimeField(_("Date de création"), auto_now_add=True)
    date_lecture = models.DateTimeField(_("Date de lecture"), null=True, blank=True)
    priorite = models.PositiveSmallIntegerField(_("Priorité"), default=1)

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['type_notification']),
        ]

    def __str__(self):
        return f"{self.utilisateur} - {self.get_type_notification_display()}: {self.objet}"

    def marquer_comme_lu(self):
        """Marque la notification comme lue"""
        self.statut = 'LU'
        self.date_lecture = timezone.now()
        self.save()

    def get_icone(self):
        """Retourne l'icône Font Awesome correspondante au type de notification"""
        icone_map = {
            'NOTE': 'fas fa-clipboard',
            'ABSENCE': 'fas fa-calendar-times',
            'MESSAGE': 'fas fa-envelope',
            'PAIEMENT': 'fas fa-money-bill-wave',
            'AGENDA': 'fas fa-calendar-alt',
            'AUTRE': 'fas fa-bell'
        }
        return icone_map.get(self.type_notification, 'fas fa-bell')
# ---------------------
# Utilisateurs (compte unique)
# ---------------------
class Utilisateur(AbstractUser):
    ROLES = (
        ('admin', 'Administrateur'),
        ('enseignant', 'Enseignant'),
        ('eleve', 'Élève'),
        ('parent', 'Parent'),
        ('directeur', 'Directeur'),
        ('secretaire', 'Secrétaire'),
        ('surveillant', 'Surveillant'),
    )

    role = models.CharField(_("Rôle"), max_length=20, choices=ROLES, db_index=True)
    telephone = models.CharField(_("Téléphone"), max_length=20, blank=True)
    photo = models.ImageField(_("Photo"), upload_to='utilisateurs/', blank=True, null=True)

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")
        ordering = ['last_name', 'first_name']

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username


# ---------------------
# Cycles, Niveaux, Classes
# ---------------------
class Cycle(models.Model):
    nom = models.CharField(_("Nom du cycle"), max_length=50, unique=True)

    class Meta:
        verbose_name = _("Cycle")
        verbose_name_plural = _("Cycles")

    def __str__(self):
        return self.nom


class Niveau(models.Model):
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name='niveaux', verbose_name=_("Cycle"))
    nom = models.CharField(_("Nom du niveau"), max_length=50)

    class Meta:
        verbose_name = _("Niveau")
        verbose_name_plural = _("Niveaux")
        unique_together = ('cycle', 'nom')
        ordering = ['cycle', 'nom']

    def __str__(self):
        return f"{self.cycle} - {self.nom}"


class Classe(models.Model):
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='classes', verbose_name=_("Niveau"))
    nom = models.CharField(_("Nom de la classe"), max_length=50)
    effectif_max = models.PositiveIntegerField(_("Effectif maximum"), null=True, blank=True)

    class Meta:
        verbose_name = _("Classe")
        verbose_name_plural = _("Classes")
        unique_together = ('niveau', 'nom')
        ordering = ['niveau', 'nom']

    def __str__(self):
        return f"{self.niveau} - {self.nom}"


# ---------------------
# Élèves
# ---------------------

class Eleve(models.Model):
    GENRE_CHOICES = [
        ('M', _('Masculin')),
        ('F', _('Féminin')),
        ('Autre', _('Autre')),
    ]

    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'eleve'},
        related_name='eleve_profile',
        verbose_name=_("Utilisateur")
    )
    matricule = models.CharField(_("Matricule"), max_length=20, unique=True)
    date_naissance = models.DateField(_("Date de naissance"))
    genre = models.CharField(_("Genre"), max_length=10, choices=GENRE_CHOICES)
    contact_urgence = models.CharField(_("Contact d'urgence"), max_length=100, blank=True)
    infos_medicaux = models.TextField(_("Informations médicales"), blank=True)
    classe_actuelle = models.ForeignKey(
        Classe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eleves',
        verbose_name=_("Classe actuelle")
    )
    date_inscription = models.DateField(
        _("Date d'inscription"),
        auto_now_add=True,
        null=True,
        blank=True
    )
    STATUT_CHOICES = [
        ('INSCRIT', 'Inscrit'),
        ('EN_ATTENTE', 'En attente'),
        ('SUSPENDU', 'Suspendu'),
        ('EXCLUE', 'Exclu'),
        ('TRANSFERE', 'Transféré'),
    ]
    
    # ... vos autres champs existants ...
    
    # Ajoutez ce champ
    statut = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUT_CHOICES,
        default='INSCRIT',
        db_index=True
    )
    class Meta:
        verbose_name = _("Élève")
        verbose_name_plural = _("Élèves")

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} ({self.matricule})"
    
    # models.py
    def notes_trimestre(self, trimestre):
        """Retourne toutes les notes d'un trimestre spécifique"""
        return self.notes.filter(trimestre=trimestre)

    def moyenne_matiere_trimestre(self, matiere, trimestre):
        """Calcule la moyenne d'une matière pour un trimestre"""
        notes = self.notes.filter(matiere=matiere, trimestre=trimestre)
        if not notes:
            return 0.0
        
        total = sum(note.valeur * note.coefficient for note in notes)
        poids = sum(note.coefficient for note in notes)
        return round(total / poids, 2)

    def moyenne_trimestrielle(self, trimestre):
        """Calcule la moyenne générale du trimestre"""
        """Calcule la moyenne générale du trimestre"""
        matieres = Matiere.objects.filter(niveau=self.classe_actuelle.niveau)
        if not matieres:
            return 0.0
        
        total = 0.0
        poids_total = 0
        
        for matiere in matieres:
            moyenne = self.moyenne_matiere_trimestre(matiere, trimestre)
            total += moyenne * matiere.coefficient
            poids_total += matiere.coefficient
    
        return round(total / poids_total, 2) if poids_total else 0.0

# ---------------------
# Parents
# ---------------------
class Parent(models.Model):
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'parent'},
        related_name='parent_profile',
        verbose_name=_("Utilisateur")
    )
    enfants = models.ManyToManyField(
        Eleve,
        verbose_name=_("Enfants"),
        related_name='parents',
        blank=True
    )

    class Meta:
        verbose_name = _("Parent")
        verbose_name_plural = _("Parents")

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} (Parent)"


# ---------------------
# Matières & Enseignement
# ---------------------
class Matiere(models.Model):
    nom = models.CharField(_("Nom de la matière"), max_length=100)
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='matieres', verbose_name=_("Niveau"))
    coefficient = models.FloatField(_("Coefficient"), default=1.0)

    class Meta:
        verbose_name = _("Matière")
        verbose_name_plural = _("Matières")
        unique_together = ('nom', 'niveau')

    def __str__(self):
        return f"{self.nom} ({self.niveau})"


class Enseignement(models.Model):
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, verbose_name=_("Matière"))
    enseignant = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'enseignant'},
        related_name='enseignements',
        verbose_name=_("Enseignant")
    )

    class Meta:
        verbose_name = _("Enseignement")
        verbose_name_plural = _("Enseignements")
        unique_together = ('matiere', 'enseignant')

    def __str__(self):
        return f"{self.matiere} - {self.enseignant}"


# ---------------------
# Notes & Évaluations
# ---------------------
# Modèle Note adapté au système congolais
# home/models.py
class Note(models.Model):
    TYPE_EVALUATION = [
        ('DS1', 'Devoir 1'),
        ('DS2', 'Devoir 2'),
        ('DS3', 'Devoir 3'),
        ('COMP', 'Composition Trimestrielle'),
        ('DEP', 'Devoir Départemental')
    ]
    
    TRIMESTRE_CHOICES = [
        ('T1', 'Trimestre 1'),
        ('T2', 'Trimestre 2'),
        ('T3', 'Trimestre 3')
    ]

    eleve = models.ForeignKey('Eleve', on_delete=models.CASCADE, related_name='notes')
    matiere = models.ForeignKey('Matiere', on_delete=models.CASCADE)
    trimestre = models.CharField(max_length=2, choices=TRIMESTRE_CHOICES)
    type_evaluation = models.CharField(max_length=4, choices=TYPE_EVALUATION)
    valeur = models.DecimalField(max_digits=4, decimal_places=2)
    date_evaluation = models.DateField(auto_now_add=True)  # Notez le nom exact

    # Le coefficient est déterminé automatiquement
    coefficient = models.DecimalField(
        _("Coefficient"),
        max_digits=3,
        decimal_places=1,
        default=Decimal('1.0')
    )
# ---------------------
# Paiements & Finances
# ---------------------
# home/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
# home/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date

class Frais(models.Model):
    """Modèle pour les frais scolaires"""
    CATEGORIES = [
        ('INSCRIPTION', _('Frais d\'inscription')),
        ('SCOLARITE', _('Frais de scolarité')),
        ('EXAMEN', _('Frais d\'examen')),
        ('LIVRE', _('Frais de livres')),
        ('AUTRE', _('Autre')),
    ]

    niveau = models.ForeignKey(
        'Niveau',
        on_delete=models.CASCADE,
        related_name='frais_niveau',
        verbose_name=_("Niveau")
    )
    categorie = models.CharField(
        _("Catégorie"),
        max_length=20,
        choices=CATEGORIES,
        db_index=True
    )
    description = models.CharField(_("Description"), max_length=100)
    montant = models.DecimalField(
        _("Montant"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')  # CORRECTION : Utiliser Decimal au lieu de float
    )
    date_limite = models.DateField(_("Date limite"), db_index=True)
    
    class Meta:
        verbose_name = _("Frais")
        verbose_name_plural = _("Frais")
        ordering = ['date_limite']
        indexes = [
            models.Index(fields=['niveau', 'date_limite']),
        ]

    def __str__(self):
        return f"{self.description} - {self.niveau} - {self.montant} XAF"
    
    def get_montant_restant(self, eleve):
        """Retourne le montant restant à payer pour cet élève"""
        total_paye = self.paiements.filter(
            eleve=eleve,
            status='Payé'
        ).aggregate(total=models.Sum('montant_paye'))['total'] or Decimal('0.00')
        
        return max(Decimal('0.00'), self.montant - total_paye)
    
    def get_statut(self, eleve):
        """Retourne le statut de paiement pour cet élève (calculé dynamiquement)"""
        montant_restant = self.get_montant_restant(eleve)
        
        if montant_restant <= 0:
            return 'PAYE'
        elif montant_restant < self.montant:
            return 'PARTIEL'
        else:
            return 'EN_ATTENTE'
    
    def get_statut_couleur(self, eleve):
        """Retourne la classe CSS correspondant au statut"""
        statut = self.get_statut(eleve)
        couleurs = {
            'EN_ATTENTE': 'danger',
            'PARTIEL': 'warning',
            'PAYE': 'success',
            'EXEMPT': 'info'
        }
        return couleurs.get(statut, 'secondary')
    
    def get_montant_display(self):
        """Retourne le montant formaté avec XAF"""
        return f"{self.montant:,.0f} XAF"
    
    
    
# home/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from datetime import date

# Types de paiement adaptés au contexte congolais
TYPE_PAIEMENT_CHOICES = [
    ('Espèces', _('Espèces')),
    ('Mobile Money', _('Mobile Money')),
    ('Airtel Money', _('Airtel Money')),
    ('Orange Money', _('Orange Money')),
    ('Moov Money', _('Moov Money')),
    ('Virement', _('Virement bancaire')),
    ('Chèque', _('Chèque')),
    ('Autre', _('Autre')),
]

# Statuts de paiement pour le contexte scolaire
STATUS_PAIEMENT_CHOICES = [
    ('Non payé', _('Non payé')),
    ('Partiellement payé', _('Partiellement payé')),
    ('Payé', _('Payé')),
    ('Exempté', _('Exempté')),
    ('En attente de validation', _('En attente de validation')),
]

class Frais(models.Model):
    """Modèle pour les frais scolaires"""
    CATEGORIES = [
        ('INSCRIPTION', _('Frais d\'inscription')),
        ('SCOLARITE', _('Frais de scolarité')),
        ('EXAMEN', _('Frais d\'examen')),
        ('LIVRE', _('Frais de livres')),
        ('AUTRE', _('Autre')),
    ]
    
    niveau = models.ForeignKey(
        'Niveau',
        on_delete=models.CASCADE,
        related_name='frais_niveau',
        verbose_name=_("Niveau"),
        db_index=True
    )
    categorie = models.CharField(
        _("Catégorie"),
        max_length=20,
        choices=CATEGORIES,
        db_index=True
    )
    description = models.CharField(_("Description"), max_length=100)
    montant = models.DecimalField(
        _("Montant"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    date_limite = models.DateField(_("Date limite"), db_index=True)
    
    class Meta:
        verbose_name = _("Frais")
        verbose_name_plural = _("Frais")
        ordering = ['date_limite']
        indexes = [
            models.Index(fields=['niveau', 'date_limite']),
        ]

    def __str__(self):
        return f"{self.description} - {self.niveau} - {self.montant} XAF"
    
    def get_montant_restant(self, eleve):
        """Retourne le montant restant à payer pour cet élève"""
        total_paye = self.paiements.filter(
            eleve=eleve,
            statut='Payé'
        ).aggregate(total=models.Sum('montant'))['total'] or Decimal('0.00')
        
        return max(Decimal('0.00'), self.montant - total_paye)
    
    def get_statut(self, eleve):
        """Retourne le statut de paiement pour cet élève"""
        montant_restant = self.get_montant_restant(eleve)
        
        if montant_restant <= 0:
            return 'PAYE'
        elif montant_restant < self.montant:
            return 'PARTIEL'
        else:
            return 'EN_ATTENTE'
    
    def get_statut_couleur(self, eleve):
        """Retourne la classe CSS correspondant au statut"""
        statut = self.get_statut(eleve)
        couleurs = {
            'EN_ATTENTE': 'danger',
            'PARTIEL': 'warning',
            'PAYE': 'success',
            'EXEMPT': 'info'
        }
        return couleurs.get(statut, 'secondary')


class Paiement(models.Model):
    """
    Enregistre chaque paiement effectué par un élève.
    Lié à un ou plusieurs frais scolaires.
    """
    eleve = models.ForeignKey(
        'Eleve',
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name=_("Élève"),
        db_index=True
    )
    frais = models.ForeignKey(
        'Frais',
        on_delete=models.CASCADE,
        related_name='paiements',
        verbose_name=_("Frais"),
        db_index=True
    )
    montant_total = models.DecimalField(
        _("Montant total dû"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    montant_paye = models.DecimalField(
        _("Montant payé"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    difference_rendue = models.DecimalField(
        _("Différence rendue"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    type_paiement = models.CharField(
        _("Mode de paiement"),
        max_length=30,
        choices=TYPE_PAIEMENT_CHOICES,
        default='Espèces'
    )
    numero_transaction = models.CharField(
        _("Numéro de transaction"),
        max_length=100,
        blank=True,
        null=True
    )
    status = models.CharField(
        _("Statut du paiement"),
        max_length=30,
        choices=STATUS_PAIEMENT_CHOICES,
        default='Non payé',
        db_index=True
    )
    personnel = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Personnel qui a enregistré le paiement"),
        limit_choices_to={'role__in': ['secretaire', 'admin', 'directeur']}
    )
    notes = models.TextField(
        _("Notes supplémentaires"),
        blank=True,
        null=True
    )
    date_paiement = models.DateField(
        _("Date de paiement"),
        default=date.today,
        db_index=True
    )

    def __str__(self):
        return f"Paiement {self.montant_paye} XAF - {self.get_type_paiement_display()}"

    def get_montant_du(self):
        """Retourne le montant total dû selon les frais"""
        return self.frais.montant

    def update_status(self):
        montant_paye = self.montant_paye
        montant_total = self.montant_total
        
        if montant_paye >= montant_total:
            self.status = 'Payé'
        elif montant_paye > Decimal('0.00'):
            self.status = 'Partiellement payé'
        else:
            self.status = 'Non payé'
        
        # Mettre à jour le statut des frais associés
        self.frais.paiements.filter(eleve=self.eleve).update(statut=self.status)
        
        self.save(update_fields=['status'])

    def calculer_difference(self):
        if self.montant_paye > self.montant_total:
            self.difference_rendue = self.montant_paye - self.montant_total
        else:
            self.difference_rendue = Decimal('0.00')
        self.save(update_fields=['difference_rendue'])

    def save(self, *args, **kwargs):
        # Initialiser le montant total si non spécifié
        if self.montant_total == Decimal('0.00'):
            self.montant_total = self.frais.montant
        
        # Calculer la différence rendue
        self.calculer_difference()
        
        # Mettre à jour le statut
        self.update_status()
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        ordering = ['-date_paiement']
        indexes = [
            models.Index(fields=['eleve', 'date_paiement']),
            models.Index(fields=['status']),
        ]
        
        
class Transaction(models.Model):
    """Modèle pour les transactions (pour l'audit)"""
    TYPE_TRANSACTION = [
        ('CREATION', _('Création')),
        ('MODIFICATION', _('Modification')),
        ('SUPPRESSION', _('Suppression')),
    ]
    
    utilisateur = models.ForeignKey(
        'Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Utilisateur")
    )
    type_transaction = models.CharField(
        _("Type de transaction"),
        max_length=20,
        choices=TYPE_TRANSACTION,
        db_index=True
    )
    objet = models.CharField(_("Objet"), max_length=100)
    objet_id = models.IntegerField(_("ID de l'objet"), null=True)
    details = models.TextField(_("Détails"), blank=True)
    date = models.DateTimeField(_("Date"), auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-date']
        indexes = [
            models.Index(fields=['utilisateur', 'date']),
            models.Index(fields=['type_transaction']),
        ]

    def __str__(self):
        return f"{self.utilisateur} - {self.type_transaction} - {self.objet}"
    
    
# ---------------------
# Présences
# ---------------------
class Presence(models.Model):
    """Modèle pour la gestion des présences des élèves"""
    eleve = models.ForeignKey(
        'Eleve',
        on_delete=models.CASCADE,
        related_name='presences'  # Ce related_name détermine comment accéder aux présences depuis Eleve
    )
    date = models.DateField(_("Date"), db_index=True)
    present = models.BooleanField(_("Présent"), default=True)
    justification = models.TextField(_("Justification"), blank=True, null=True)
    
    # Si vous voulez suivre les retards, ajoutez ce champ
    retard = models.BooleanField(_("Retard"), default=False)
    
    class Meta:
        verbose_name = _("Présence")
        verbose_name_plural = _("Présences")
        unique_together = ('eleve', 'date')
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['present']),
        ]
        ordering = ['-date']

    def __str__(self):
        return f"{self.eleve} - {self.date} - {'Présent' if self.present else 'Absent'}"
# ---------------------
# Messagerie interne
# ---------------------
class Message(models.Model):
    expediteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='messages_envoyes',
        verbose_name=_("Expéditeur"),
        db_index=True  # Important pour les performances
    )
    destinataire = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='messages_recus',
        verbose_name=_("Destinataire"),
        db_index=True  # Important pour les performances
    )
    objet = models.CharField(_("Objet"), max_length=100, db_index=True)
    contenu = models.TextField(_("Contenu"))
    date_envoi = models.DateTimeField(_("Date d'envoi"), auto_now_add=True, db_index=True)
    lu = models.BooleanField(_("Lu"), default=False, db_index=True)
    archive = models.BooleanField(_("Archivé"), default=False, db_index=True)
    supprime_expediteur = models.BooleanField(_("Supprimé par l'expéditeur"), default=False, db_index=True)
    supprime_destinataire = models.BooleanField(_("Supprimé par le destinataire"), default=False, db_index=True)

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        indexes = [
            models.Index(fields=['expediteur', 'date_envoi']),
            models.Index(fields=['destinataire', 'date_envoi']),
            models.Index(fields=['expediteur', 'lu', 'date_envoi']),
            models.Index(fields=['destinataire', 'lu', 'date_envoi']),
        ]
        ordering = ['-date_envoi']
        constraints = [
            models.CheckConstraint(
                check=~models.Q(expediteur=models.F('destinataire')),
                name='expediteur_destinataire_different'
            )
        ]

    def __str__(self):
        return f"{self.objet} → {self.destinataire}"
    
    def save(self, *args, **kwargs):
        """Vérifie que l'expéditeur et le destinataire sont différents"""
        if self.expediteur == self.destinataire:
            raise ValidationError(_("L'expéditeur et le destinataire ne peuvent pas être identiques."))
        super().save(*args, **kwargs)
    
    def marquer_comme_lu(self):
        """Marque le message comme lu"""
        if not self.lu:
            self.lu = True
            self.save(update_fields=['lu'])
    
    def supprimer_pour_expediteur(self):
        """Supprime le message pour l'expéditeur"""
        self.supprime_expediteur = True
        self.save(update_fields=['supprime_expediteur'])
        # Si les deux ont supprimé le message, on le supprime définitivement
        if self.supprime_destinataire:
            self.delete()
    
    def supprimer_pour_destinataire(self):
        """Supprime le message pour le destinataire"""
        self.supprime_destinataire = True
        self.save(update_fields=['supprime_destinataire'])
        # Si les deux ont supprimé le message, on le supprime définitivement
        if self.supprime_expediteur:
            self.delete()

# ---------------------
# Certificats & Bulletins
# ---------------------
class Document(models.Model):
    TYPE_DOCUMENT = [
        ('bulletin', _('Bulletin')),
        ('certificat', _('Certificat')),
        ('autre', _('Autre')),
    ]

    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name=_("Élève"))
    nom = models.CharField(_("Nom du document"), max_length=100)
    fichier = models.FileField(_("Fichier"), upload_to='documents/')
    date_creation = models.DateTimeField(_("Date de création"), auto_now_add=True)
    type = models.CharField(_("Type"), max_length=50, choices=TYPE_DOCUMENT)

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self):
        return f"{self.nom} - {self.eleve}"
    
    
    
    
class Presence(models.Model):
    """Modèle pour la gestion des présences des élèves"""
    eleve = models.ForeignKey(
        'Eleve',
        on_delete=models.CASCADE,
        related_name='presence'
    )
    date = models.DateField(_("Date"), db_index=True)
    present = models.BooleanField(_("Présent"), default=True)
    justification = models.TextField(_("Justification"), blank=True, null=True)
    
    # AJOUTEZ CETTE LIGNE POUR AJOUTER LE CHAMP RETARD
    retard = models.BooleanField(_("Retard"), default=False)
    
    class Meta:
        verbose_name = _("Présence")
        verbose_name_plural = _("Présences")
        unique_together = ('eleve', 'date')
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['present']),
        ]
        ordering = ['-date']

    def __str__(self):
        return f"{self.eleve} - {self.date} - {'Présent' if self.present else 'Absent'}"