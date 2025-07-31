from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# ---------------------
# Utilisateurs (compte unique)
# ---------------------
# models.py
from django.contrib.auth.models import AbstractUser

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

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


# ---------------------
# Cycles, Niveaux, Classes
# ---------------------
class Parent(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='parent_profile')
    enfants = models.ManyToManyField('Eleve', verbose_name="Enfants", related_name='parents')

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} (Parent)"

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

    def __str__(self):
        return f"{self.cycle} - {self.nom}"


class Classe(models.Model):
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, related_name='classes', verbose_name=_("Niveau"))
    nom = models.CharField(_("Nom de la classe"), max_length=50)
    effectif_max = models.PositiveIntegerField(_("Effectif maximum"))

    class Meta:
        verbose_name = _("Classe")
        verbose_name_plural = _("Classes")
        unique_together = ('niveau', 'nom')

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
        verbose_name=_("Classe actuelle")
    )

    class Meta:
        verbose_name = _("Élève")
        verbose_name_plural = _("Élèves")

    def __str__(self):
        return f"{self.utilisateur.first_name} {self.utilisateur.last_name} ({self.matricule})"


# ---------------------
# Matières & Enseignement
# ---------------------
class Matiere(models.Model):
    nom = models.CharField(_("Nom de la matière"), max_length=100)
    niveau = models.ForeignKey(Niveau, on_delete=models.CASCADE, verbose_name=_("Niveau"))
    coefficient = models.FloatField(_("Coefficient"))

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
        verbose_name=_("Enseignant")
    )

    class Meta:
        verbose_name = _("Enseignement")
        verbose_name_plural = _("Enseignements")
        unique_together = ('matiere', 'enseignant')  # Un enseignant ne peut enseigner qu'une fois la même matière

    def __str__(self):
        return f"{self.matiere} - {self.enseignant}"


# ---------------------
# Notes & Évaluations
# ---------------------
class Note(models.Model):
    TRIMESTRE_CHOICES = [
        ('T1', _('Trimestre 1')),
        ('T2', _('Trimestre 2')),
        ('T3', _('Trimestre 3')),
    ]

    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, verbose_name=_("Élève"))
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, verbose_name=_("Matière"))
    trimestre = models.CharField(_("Trimestre"), max_length=10, choices=TRIMESTRE_CHOICES)
    note = models.DecimalField(_("Note"), max_digits=5, decimal_places=2)
    commentaire = models.TextField(_("Commentaire"), blank=True)

    class Meta:
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")
        unique_together = ('eleve', 'matiere', 'trimestre')
        indexes = [
            models.Index(fields=['eleve', 'trimestre']),
        ]

    def __str__(self):
        return f"{self.eleve} - {self.matiere} : {self.note} ({self.trimestre})"


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