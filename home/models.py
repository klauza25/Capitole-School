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
class Frais(models.Model):
    nom = models.CharField(_("Nom des frais"), max_length=100)
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, verbose_name=_("Niveau concerné"))
    montant = models.DecimalField(_("Montant"), max_digits=10, decimal_places=2)
    date_limite = models.DateField(_("Date limite"))

    class Meta:
        verbose_name = _("Frais scolaires")
        verbose_name_plural = _("Frais scolaires")

    def __str__(self):
        return f"{self.nom} - {self.montant} XAF"


class Paiement(models.Model):
    """Modèle pour les paiements des frais scolaires"""
    # ... autres champs ...
    
    # Ajoutez un champ statut si ce n'est pas déjà fait
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
        ('REMBOURSE', 'Remboursé'),
    ]
    
    statut = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        db_index=True
    )
    
    # ... autres champs ...
    MOYEN_PAIEMENT = [
        ('especes', _('Espèces')),
        ('mobile_money', _('Mobile Money')),
        ('cheque', _('Chèque')),
        ('virement', _('Virement bancaire')),
    ]

    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name=_("Élève"))
    date = models.DateField(_("Date de paiement"), auto_now_add=True)
    montant = models.DecimalField(_("Montant payé"), max_digits=10, decimal_places=2)
    moyen = models.CharField(_("Mode de paiement"), max_length=50, choices=MOYEN_PAIEMENT)
    description = models.CharField(_("Description"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Paiement")
        verbose_name_plural = _("Paiements")
        indexes = [
            models.Index(fields=['eleve', 'date']),
        ]

    def __str__(self):
        return f"Paiement de {self.montant} XAF par {self.eleve} le {self.date}"


# ---------------------
# Présences
# ---------------------
class Presence(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name=_("Élève"))
    date = models.DateField(_("Date"), db_index=True)
    present = models.BooleanField(_("Présent"))
    justification = models.TextField(_("Justification"), blank=True)

    class Meta:
        verbose_name = _("Présence")
        verbose_name_plural = _("Présences")
        unique_together = ('eleve', 'date')
        ordering = ['-date']

    def __str__(self):
        statut = "Présent" if self.present else "Absent"
        return f"{self.eleve} - {self.date} : {statut}"


# ---------------------
# Messagerie interne
# ---------------------
class Message(models.Model):
    expediteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='messages_envoyes',
        verbose_name=_("Expéditeur")
    )
    destinataire = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='messages_recus',
        verbose_name=_("Destinataire")
    )
    objet = models.CharField(_("Objet"), max_length=100)
    contenu = models.TextField(_("Contenu"))
    date_envoi = models.DateTimeField(_("Date d'envoi"), auto_now_add=True)
    lu = models.BooleanField(_("Lu"), default=False)

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        indexes = [
            models.Index(fields=['expediteur', 'date_envoi']),
            models.Index(fields=['destinataire', 'date_envoi']),
        ]
        ordering = ['-date_envoi']

    def __str__(self):
        return f"{self.objet} → {self.destinataire}"


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