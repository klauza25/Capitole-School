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

# admin.py




class NoteAdmin(admin.ModelAdmin):
    # Afficher uniquement les champs qui existent dans le modèle
    list_display = [
        'eleve',
        'matiere',
        'trimestre',
        'type_evaluation',  # Utilisez ce champ si vous avez ce modèle
        'valeur',
        'get_devoir_display',  # Si vous utilisez un champ personnalisé
        'date_evaluation'  # Utilisez le bon nom de champ
    ]
    
    # Filtres basés sur des champs existants
    list_filter = [
        'trimestre',
        'type_evaluation',  # Utilisez ce champ si vous avez ce modèle
        'matiere',
        'eleve__classe_actuelle'
    ]
    
    # Recherche par champs existants
    search_fields = [
        'eleve__utilisateur__first_name',
        'eleve__utilisateur__last_name',
        'matiere__nom'
    ]
    
    # Pagination
    list_per_page = 25
    
    # Si vous voulez afficher 'devoir' mais que ce n'est pas un champ direct
    def get_devoir_display(self, obj):
        # Si vous avez un champ personnalisé ou une logique spécifique
        if obj.type_evaluation == 'DS1':
            return 'Devoir 1'
        elif obj.type_evaluation == 'DS2':
            return 'Devoir 2'
        elif obj.type_evaluation == 'DS3':
            return 'Devoir 3'
        elif obj.type_evaluation == 'COMP':
            return 'Composition'
        return obj.type_evaluation
    get_devoir_display.short_description = 'Devoir'

admin.site.register(Note, NoteAdmin)
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
    
    
admin.site.register(Parent)