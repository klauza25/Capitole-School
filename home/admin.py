from django.contrib import admin
from django.contrib.admin.exceptions import AlreadyRegistered
from .models import *

# Configuration de l'administration
admin.site.site_header = "Capitole School"
admin.site.site_title = "Capitole School Admin"
admin.site.index_title = "Welcome to Capitole bilingue school Admin"

# Enregistrement sécurisé pour Utilisateur
try:
    @admin.register(Utilisateur)
    class UtilisateurAdmin(admin.ModelAdmin):
        list_display = ('username', 'first_name', 'last_name', 'role', 'telephone', 'photo_preview')
        list_filter = ('role',)
        search_fields = ('first_name', 'last_name', 'username', 'telephone')
        readonly_fields = ('date_joined', 'last_login')
        list_per_page = 20
        
        def photo_preview(self, obj):
            if obj.photo:
                return f'<img src="{obj.photo.url}" style="width: 30px; height: 30px; border-radius: 50%;">'
            return 'Pas de photo'
        photo_preview.short_description = 'Photo'
        photo_preview.allow_tags = True
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Cycle
try:
    @admin.register(Cycle)
    class CycleAdmin(admin.ModelAdmin):
        list_display = ('nom',)
        search_fields = ('nom',)
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Niveau
try:
    @admin.register(Niveau)
    class NiveauAdmin(admin.ModelAdmin):
        list_display = ('nom', 'cycle')
        list_filter = ('cycle',)
        search_fields = ('nom',)
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Classe
try:
    @admin.register(Classe)
    class ClasseAdmin(admin.ModelAdmin):
        list_display = ('nom', 'niveau', 'effectif_max', 'effectif_actuel')
        list_filter = ('niveau__cycle', 'niveau')
        search_fields = ('nom',)
        readonly_fields = ('effectif_actuel',)
        
        def effectif_actuel(self, obj):
            return obj.eleve_set.count()
        effectif_actuel.short_description = "Effectif actuel"
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Eleve
try:
    @admin.register(Eleve)
    class EleveAdmin(admin.ModelAdmin):
        list_display = ('matricule', 'utilisateur', 'classe_actuelle', 'genre', 'photo_preview')
        list_filter = ('classe_actuelle__niveau__cycle', 'classe_actuelle', 'genre')
        search_fields = ('matricule', 'utilisateur__first_name', 'utilisateur__last_name')
        raw_id_fields = ('utilisateur', 'classe_actuelle', 'parents')
        
        def photo_preview(self, obj):
            if obj.utilisateur.photo:
                return f'<img src="{obj.utilisateur.photo.url}" style="width: 30px; height: 30px; border-radius: 50%;">'
            return 'Pas de photo'
        photo_preview.short_description = 'Photo'
        photo_preview.allow_tags = True
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Matiere
try:
    @admin.register(Matiere)
    class MatiereAdmin(admin.ModelAdmin):
        list_display = ('nom', 'niveau', 'coefficient', 'get_enseignant')
        list_filter = ('niveau__cycle', 'niveau')
        search_fields = ('nom',)
        raw_id_fields = ('niveau',)
        
        def get_enseignant(self, obj):
            """Retourne l'enseignant associé à cette matière"""
            enseignement = Enseignement.objects.filter(matiere=obj).first()
            if enseignement and enseignement.enseignant:
                return enseignement.enseignant.utilisateur.get_full_name()
            return "Non assigné"
        get_enseignant.short_description = 'Enseignant'
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Enseignement
try:
    @admin.register(Enseignement)
    class EnseignementAdmin(admin.ModelAdmin):
        list_display = ('matiere', 'enseignant')
        list_filter = ('matiere__niveau__cycle', 'matiere__niveau')
        search_fields = ('matiere__nom', 'enseignant__utilisateur__first_name', 'enseignant__utilisateur__last_name')
        raw_id_fields = ('matiere', 'enseignant')
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Note
try:
    class NoteAdmin(admin.ModelAdmin):
        list_display = [
            'eleve',
            'matiere',
            'trimestre',
            'type_evaluation',
            'valeur',
            'get_devoir_display',
            'date_evaluation'
        ]
        
        list_filter = [
            'trimestre',
            'type_evaluation',
            'matiere',
            'eleve__classe_actuelle'
        ]
        
        search_fields = [
            'eleve__utilisateur__first_name',
            'eleve__utilisateur__last_name',
            'matiere__nom'
        ]
        
        list_per_page = 25
        date_hierarchy = 'date_evaluation'
        raw_id_fields = ('eleve', 'matiere')
        
        def get_devoir_display(self, obj):
            type_eval = dict(Note.TYPE_EVALUATION)
            return type_eval.get(obj.type_evaluation, obj.type_evaluation)
        get_devoir_display.short_description = 'Type d\'évaluation'
    
    admin.site.register(Note, NoteAdmin)
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Frais - CORRECTION PRINCIPALE
try:
    class FraisAdmin(admin.ModelAdmin):
        # CORRECTION : Suppression du champ 'statut' car il n'existe pas dans le modèle
        list_display = ('description', 'niveau', 'montant', 'date_limite')
        list_filter = ('niveau', 'categorie')
        search_fields = ('description',)
        date_hierarchy = 'date_limite'
        ordering = ['date_limite']
        list_per_page = 20
        raw_id_fields = ('niveau',)
        
        def get_queryset(self, request):
            qs = super().get_queryset(request)
            return qs.select_related('niveau')
    
    admin.site.register(Frais, FraisAdmin)
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Paiement - CORRECTION PRINCIPALE
try:
    class PaiementAdmin(admin.ModelAdmin):
        # CORRECTION : Utilisation des noms de champs corrects du modèle
        list_display = ('eleve', 'frais', 'date_paiement', 'montant_paye', 'type_paiement', 'status', 'numero_transaction')
        list_filter = ('status', 'type_paiement', 'date_paiement')
        search_fields = ('eleve__utilisateur__first_name', 'eleve__utilisateur__last_name', 'numero_transaction')
        date_hierarchy = 'date_paiement'
        ordering = ['-date_paiement']
        list_per_page = 20
        raw_id_fields = ('eleve', 'frais', 'personnel')
        
        def get_queryset(self, request):
            qs = super().get_queryset(request)
            return qs.select_related('eleve__utilisateur', 'eleve__classe_actuelle', 'frais', 'personnel')
    
    admin.site.register(Paiement, PaiementAdmin)
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Presence
try:
    @admin.register(Presence)
    class PresenceAdmin(admin.ModelAdmin):
        list_display = ('eleve', 'date', 'present', 'retard', 'justification_preview')
        list_filter = ('date', 'present', 'retard', 'eleve__classe_actuelle')
        search_fields = ('eleve__utilisateur__first_name', 'eleve__utilisateur__last_name', 'justification')
        date_hierarchy = 'date'
        list_per_page = 20
        raw_id_fields = ('eleve',)
        
        def justification_preview(self, obj):
            if obj.justification and len(obj.justification) > 50:
                return obj.justification[:50] + '...'
            return obj.justification
        justification_preview.short_description = 'Justification'
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Message
try:
    @admin.register(Message)
    class MessageAdmin(admin.ModelAdmin):
        list_display = ('objet', 'expediteur', 'destinataire', 'date_envoi', 'lu')
        list_filter = ('lu', 'date_envoi')
        search_fields = ('objet', 'expediteur__first_name', 'expediteur__last_name', 'destinataire__first_name', 'destinataire__last_name')
        date_hierarchy = 'date_envoi'
        list_per_page = 20
        raw_id_fields = ('expediteur', 'destinataire')
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Document
try:
    @admin.register(Document)
    class DocumentAdmin(admin.ModelAdmin):
        list_display = ('nom', 'eleve', 'type', 'date_creation', 'fichier_preview')
        list_filter = ('type', 'date_creation')
        search_fields = ('nom', 'eleve__utilisateur__first_name', 'eleve__utilisateur__last_name')
        date_hierarchy = 'date_creation'
        list_per_page = 20
        raw_id_fields = ('eleve',)
        
        def fichier_preview(self, obj):
            if obj.fichier:
                return f'<a href="{obj.fichier.url}" target="_blank">Voir</a>'
            return 'Pas de fichier'
        fichier_preview.short_description = 'Fichier'
        fichier_preview.allow_tags = True
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Parent
try:
    @admin.register(Parent)
    class ParentAdmin(admin.ModelAdmin):
        list_display = ('utilisateur', 'get_profession', 'enfants_list')
        search_fields = ('utilisateur__first_name', 'utilisateur__last_name')
        raw_id_fields = ('utilisateur',)
        
        def get_profession(self, obj):
            """Retourne la profession du parent"""
            # Si la profession est stockée dans le modèle Utilisateur
            if hasattr(obj.utilisateur, 'profession'):
                return obj.utilisateur.profession
            # Si la profession est un champ direct du modèle Parent
            elif hasattr(obj, 'profession'):
                return obj.profession
            return "Non spécifiée"
        get_profession.short_description = 'Profession'
        
        def enfants_list(self, obj):
            return ", ".join([str(enfant) for enfant in obj.enfants.all()])
        enfants_list.short_description = 'Enfants'
except AlreadyRegistered:
    pass

# Enregistrement sécurisé pour Transaction
try:
    class TransactionAdmin(admin.ModelAdmin):
        list_display = ('date', 'utilisateur', 'type_transaction', 'objet', 'objet_id')
        list_filter = ('type_transaction', 'date', 'utilisateur__role')
        search_fields = ('utilisateur__first_name', 'utilisateur__last_name', 'details', 'objet')
        date_hierarchy = 'date'
        ordering = ['-date']
        list_per_page = 20
        raw_id_fields = ('utilisateur',)
        
        def has_add_permission(self, request):
            return False
            
        def has_change_permission(self, request, obj=None):
            return False
            
        def has_delete_permission(self, request, obj=None):
            return False
    
    admin.site.register(Transaction, TransactionAdmin)
except AlreadyRegistered:
    pass