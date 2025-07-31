from django.contrib import admin
from .models import *


admin.site.site_header = "Capitole School"
admin.site.site_title = "Capitole School Admin"
admin.site.index_title = "Welcome to Capitole bilingue school Admin"







@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'telephone')
    list_filter = ('role',)
    search_fields = ('first_name', 'last_name', 'username', 'telephone')

@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = ('nom',)

@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ('nom', 'cycle')
    list_filter = ('cycle',)

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau', 'effectif_max')
    list_filter = ('niveau__cycle', 'niveau')

@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'utilisateur', 'classe_actuelle', 'genre')
    list_filter = ('classe_actuelle__niveau__cycle', 'classe_actuelle', 'genre')
    search_fields = ('matricule', 'utilisateur__first_name', 'utilisateur__last_name')

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau', 'coefficient')
    list_filter = ('niveau__cycle', 'niveau')

@admin.register(Enseignement)
class EnseignementAdmin(admin.ModelAdmin):
    list_display = ('matiere', 'enseignant')

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'matiere', 'trimestre', 'note')
    list_filter = ('trimestre', 'matiere', 'eleve__classe_actuelle')

@admin.register(Frais)
class FraisAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau', 'montant', 'date_limite')

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'date', 'montant', 'moyen')
    list_filter = ('date', 'moyen')

@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'date', 'present')
    list_filter = ('date', 'present', 'eleve__classe_actuelle')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('objet', 'expediteur', 'destinataire', 'date_envoi', 'lu')
    list_filter = ('lu', 'date_envoi')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'eleve', 'type', 'date_creation')
    list_filter = ('type',)