# /views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json
from decimal import Decimal
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
from .forms import EnseignantForm, FraisForm, PaiementForm, ParentForm, RegisterForm, CycleForm, NiveauForm, ClasseForm, EleveForm
from django.contrib import messages
# home/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count, Q
# home/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q
from datetime import date, timedelta
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from .models import Presence, Eleve


@login_required
def directeur_dashboard(request):
    # Vérifier que l'utilisateur est bien un directeur
    if request.user.role != 'directeur':
        messages.error(request, "Accès refusé : vous n'êtes pas directeur.")
        return redirect('home:login')
    
    # Statistiques globales
    total_eleves = Eleve.objects.count()
    total_enseignants = Utilisateur.objects.filter(role='enseignant').count()
    total_classes = Classe.objects.count()
    
    # Taux de présence global
    total_presences = Presence.objects.count()
    presences_valides = Presence.objects.filter(present=True).count()
    taux_presence_global = round(presences_valides / total_presences * 100, 1) if total_presences > 0 else 100
    
    # Statistiques financières
    annee_en_cours = date.today().year
    trimestre_en_cours = 'T1'  # À adapter selon la date
    
    # Total des frais scolaires pour l'année
    total_frais = Frais.objects.filter(
        Q(date_limite__year=annee_en_cours)
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    # Total des paiements validés
    total_paiements = Paiement.objects.filter(
    statut='VALIDE',
    date__year=annee_en_cours  # Utiliser 'date' au lieu de 'date_paiement'
).aggregate(total=Sum('montant'))['total'] or 0
    
    # Taux de paiement global
    taux_paiement = round(total_paiements / total_frais * 100, 1) if total_frais > 0 else 100
    
    # Statistiques académiques
    # Moyenne générale par niveau
    niveaux_stats = []
    for niveau in Niveau.objects.all():
        notes_niveau = Note.objects.filter(
            eleve__classe_actuelle__niveau=niveau,
            trimestre=trimestre_en_cours
        )
        
        if notes_niveau.exists():
            total = sum(note.valeur * note.coefficient for note in notes_niveau)
            poids = sum(note.coefficient for note in notes_niveau)
            moyenne = total / poids
        else:
            moyenne = Decimal('0.0')
        
        eleves_niveau = Eleve.objects.filter(classe_actuelle__niveau=niveau).count()
        niveaux_stats.append({
            'niveau': niveau,
            'moyenne': float(moyenne),
            'eleves': eleves_niveau
        })
    niveaux_stats = []
    for niveau in Niveau.objects.all():
        notes_niveau = Note.objects.filter(
            eleve__classe_actuelle__niveau=niveau,
            trimestre=trimestre_en_cours
        )
        
        if notes_niveau.exists():
            total = sum(note.valeur * note.coefficient for note in notes_niveau)
            poids = sum(note.coefficient for note in notes_niveau)
            moyenne = total / poids
            pourcentage = (moyenne / 20) * 100  # Calcul du pourcentage ici
        else:
            moyenne = Decimal('0.0')
            pourcentage = 0.0
        
        eleves_niveau = Eleve.objects.filter(classe_actuelle__niveau=niveau).count()
        niveaux_stats.append({
            'niveau': niveau,
            'moyenne': float(moyenne),
            'eleves': eleves_niveau,
            'pourcentage': float(pourcentage)  # Ajout du pourcentage calculé
        })
    
    
    # Performances par matière (top 5)
    matieres_performance = []
    for matiere in Matiere.objects.all():
        notes_matiere = Note.objects.filter(
            matiere=matiere,
            trimestre=trimestre_en_cours
        )
        
        if notes_matiere.exists():
            total = sum(note.valeur * note.coefficient for note in notes_matiere)
            poids = sum(note.coefficient for note in notes_matiere)
            moyenne = total / poids
        else:
            moyenne = Decimal('0.0')
        
        matieres_performance.append({
            'matiere': matiere,
            'moyenne': float(moyenne)
        })
    
    # Trier par moyenne décroissante et prendre les 5 meilleures
    matieres_performance = sorted(
        matieres_performance, 
        key=lambda x: x['moyenne'], 
        reverse=True
    )[:5]
    
    # Élèves en difficulté (moyenne < 10)
    eleves_difficulte = []
    for eleve in Eleve.objects.all():
        notes = eleve.notes.filter(trimestre=trimestre_en_cours)
        if notes.exists():
            total = sum(note.valeur * note.coefficient for note in notes)
            poids = sum(note.coefficient for note in notes)
            moyenne = total / poids
            
            if moyenne < 10:
                eleves_difficulte.append({
                    'eleve': eleve,
                    'moyenne': float(moyenne)
                })
    
    # Trier par moyenne croissante
    eleves_difficulte = sorted(
        eleves_difficulte, 
        key=lambda x: x['moyenne']
    )[:5]  # Top 5 des élèves en difficulté
    
    # Notifications récentes
    notifications_recentes = Notification.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')[:5]
    
    # Événements récents
    evenements_recents = [
        {
            'date': "Aujourd'hui",
            'type': "Réunion",
            'description': "Réunion des directeurs d'établissement"
        },
        {
            'date': "Hier",
            'type': "Examen",
            'description': "Début des examens départementaux"
        },
        {
            'date': "Il y a 3 jours",
            'type': "Administration",
            'description': "Mise à jour des effectifs"
        }
    ]
    
    context = {
        'total_eleves': total_eleves,
        'total_enseignants': total_enseignants,
        'total_classes': total_classes,
        'taux_presence_global': taux_presence_global,
        'total_frais': total_frais,
        'total_paiements': total_paiements,
        'taux_paiement': taux_paiement,
        'niveaux_stats': niveaux_stats,
        'matieres_performance': matieres_performance,
        'eleves_difficulte': eleves_difficulte,
        'notifications_recentes': notifications_recentes,
        'evenements_recents': evenements_recents,
        'trimestre_en_cours': trimestre_en_cours,
        'annee_en_cours': annee_en_cours,
    }
    
    return render(request, 'gestion/dashboards/directeur_dashboard.html', context)

@login_required
def notifications_liste(request):
    """Affiche la liste des notifications de l'utilisateur"""
    # Trier par statut et date
    notifications = request.user.notifications.all().order_by(
        '-statut', '-date_creation'
    )
    
    # Compter les notifications non lues
    non_lues = notifications.filter(statut='NON_LU').count()
    
    context = {
        'notifications': notifications,
        'non_lues': non_lues,
        'title': 'Mes notifications'
    }
    
    return render(request, 'gestion/notifications/liste.html', context)

@login_required
def notification_marquer_comme_lue(request, pk):
    """Marque une notification comme lue"""
    notification = get_object_or_404(
        Notification, 
        pk=pk, 
        utilisateur=request.user
    )
    notification.marquer_comme_lu()
    
    # Rediriger vers le lien associé si présent
    if notification.lien:
        return redirect(notification.lien)
    
    return redirect('home:notifications')

@login_required
def notifications_marquer_tout_comme_lu(request):
    """Marque toutes les notifications comme lues"""
    request.user.notifications.filter(statut='NON_LU').update(
        statut='LU',
        date_lecture=timezone.now()
    )
    return redirect('home:notifications')

@login_required
def notifications_supprimer(request, pk):
    """Supprime une notification"""
    notification = get_object_or_404(
        Notification, 
        pk=pk, 
        utilisateur=request.user
    )
    notification.delete()
    messages.success(request, "Notification supprimée avec succès.")
    return redirect('home:notifications')

@login_required
def notifications_supprimer_tout(request):
    """Supprime toutes les notifications"""
    request.user.notifications.all().delete()
    messages.success(request, "Toutes les notifications ont été supprimées.")
    return redirect('home:notifications')

@login_required
def notifications_api(request):
    """API pour les notifications (pour le système de notification en temps réel)"""
    non_lues = request.user.notifications.filter(statut='NON_LU').count()
    
    return JsonResponse({
        'non_lues': non_lues,
        'total': request.user.notifications.count()
    })
    
# Logger
logger = logging.getLogger(__name__)
User = get_user_model()


# === VUES PUBLIQUES ===

def accueil(request):
    """
    Page d'accueil publique avec modal de login.
    """
    return render(request, 'gestion/accueil.html')


def register(request):
    """
    Inscription d'un nouvel utilisateur.
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Compte créé pour {user.first_name} {user.last_name} ! Vous pouvez maintenant vous connecter."
            )
            return redirect('home:accueil')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = RegisterForm()

    return render(request, 'gestion/register.html', {'form': form})


@csrf_exempt
def login_view(request):
    """
    Connexion via formulaire POST (AJAX ou classique).
    """
    if request.method == 'POST':
        try:
            # Si c'est une requête AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
            else:
                # Requête classique
                username = request.POST.get('username')
                password = request.POST.get('password')

            if not username or not password:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Veuillez remplir tous les champs.'
                    }, status=400)
                messages.error(request, "Veuillez remplir tous les champs.")
                return redirect('home:accueil')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                redirect_url = reverse('home:home')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'redirect_url': redirect_url
                    })
                return redirect(redirect_url)
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Identifiants incorrects.'
                    }, status=401)
                messages.error(request, "Identifiants incorrects.")
                return redirect('home:accueil')

        except Exception as e:
            logger.error(f"Erreur dans login_view : {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Erreur serveur.'
                }, status=500)
            messages.error(request, "Une erreur est survenue.")
            return redirect('home:accueil')

    return redirect('home:accueil')


@login_required
def home(request):
    """
    Redirige l'utilisateur vers son dashboard selon son rôle.
    """
    user = request.user
    print("➡️ Utilisateur connecté :", user.username)
    print("➡️ Rôle :", getattr(user, 'role', 'NON DÉFINI'))

    if not user.is_authenticated:
        return redirect('home:accueil')

    role = getattr(user, 'role', None)
    if not role:
        logger.warning(f"Utilisateur {user.username} connecté sans rôle.")
        messages.error(request, "Votre compte n'a pas de rôle défini.")
        return redirect('admin:index')

    # Tableau de redirection
    urls = {
        'admin': 'home:admin_dashboard',
        'enseignant': 'home:enseignant_dashboard',
        'eleve': 'home:eleve_dashboard',
        'parent': 'home:parent_dashboard',
        'directeur': 'home:directeur_dashboard',
        'secretaire': 'home:secretaire_dashboard',
        'surveillant': 'home:surveillant_dashboard',
    }

    url_name = urls.get(role)
    if not url_name:
        logger.warning(f"Rôle inconnu : {role} pour {user.username}")
        messages.error(request, f"Rôle '{role}' non reconnu.")
        return redirect('admin:index')

    try:
        return redirect(url_name)
    except Exception as e:
        logger.error(f"Erreur de redirection pour le rôle '{role}': {e}")
        messages.error(request, "Erreur de configuration du système.")
        return redirect('admin:index')


# === DASHBOARDS ===

@login_required
def admin_dashboard(request):
    return redirect('admin:index')





@login_required
def eleve_dashboard(request):
    try:
        eleve = request.user.eleve_profile
    except Eleve.DoesNotExist:
        messages.error(request, "Profil élève introuvable.")
        return redirect('home:login')



    # Gestion de l'upload de photo
    if request.method == 'POST' and request.FILES.get('photo'):
        photo = request.FILES['photo']
        
        # Validation du type de fichier
        valid_image_types = ['image/jpeg', 'image/png', 'image/gif']
        if photo.content_type not in valid_image_types:
            return JsonResponse({
                'success': False,
                'error': 'Format d\'image invalide. Formats acceptés: JPEG, PNG, GIF'
            }, status=400)
        
        # Validation de la taille (max 5MB)
        if photo.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'L\'image ne doit pas dépasser 5MB'
            }, status=400)
        
        # Mettre à jour la photo de profil depuis le modèle Utilisateur
        request.user.photo = photo
        request.user.save()
        
        return JsonResponse({
            'success': True,
            'photo_url': request.user.photo.url
        })

    # ... le reste de votre code existant pour le dashboard ...
    
    # Si ce n'est pas une requête AJAX pour la photo
    # Notes triées par trimestre
    notes = eleve.notes.all().select_related('matiere').order_by('trimestre', 'matiere__nom')
    
    # Organiser les notes par trimestre
    trimestres = []
    for trimestre_code, trimestre_nom in Note.TRIMESTRE_CHOICES:
        notes_trimestre = notes.filter(trimestre=trimestre_code)
        
        # Organiser par matière
        matieres_data = []
        total_matiere = Decimal('0.0')
        poids_total = Decimal('0.0')
        
        # Regrouper les notes par matière
        matieres_dict = {}
        for note in notes_trimestre:
            if note.matiere not in matieres_dict:
                matieres_dict[note.matiere] = {
                    'matiere': note.matiere,
                    'notes': [],  # Toutes les notes de la matière
                    'devoir1': None,
                    'devoir2': None,
                    'devoir3': None,
                    'composition': None,
                    'departemental': None
                }
            
            # Ajouter à la liste de toutes les notes
            matieres_dict[note.matiere]['notes'].append(note)
            
            # Classer les notes spécifiques
            if note.type_evaluation == 'DS1':
                matieres_dict[note.matiere]['devoir1'] = note
            elif note.type_evaluation == 'DS2':
                matieres_dict[note.matiere]['devoir2'] = note
            elif note.type_evaluation == 'DS3':
                matieres_dict[note.matiere]['devoir3'] = note
            elif note.type_evaluation == 'COMP':
                matieres_dict[note.matiere]['composition'] = note
            elif note.type_evaluation == 'DEP':
                matieres_dict[note.matiere]['departemental'] = note
        
        # Calculer les moyennes par matière
        for matiere, data in matieres_dict.items():
            notes_list = data['notes']
            if notes_list:
                total = sum(n.valeur * Decimal(str(n.coefficient)) for n in notes_list)
                poids = sum(Decimal(str(n.coefficient)) for n in notes_list)
                moyenne = total / poids
            else:
                moyenne = Decimal('0.0')
                
            data['moyenne'] = moyenne
            total_matiere += moyenne * Decimal(str(matiere.coefficient))
            poids_total += Decimal(str(matiere.coefficient))
            matieres_data.append(data)
        
        # Calculer la moyenne générale du trimestre
        if poids_total > 0:
            moyenne_generale = float(total_matiere / poids_total)
            moyenne_generale = round(moyenne_generale, 2)
        else:
            moyenne_generale = 0.0
        
        trimestres.append({
            'code': trimestre_code,
            'nom': trimestre_nom,
            'matieres': matieres_data,
            'moyenne': moyenne_generale
        })

    # Calculer le taux de présence
    total_presences = eleve.presence_set.count()
    presences_valides = eleve.presence_set.filter(present=True).count()
    taux_presence = round(presences_valides / total_presences * 100, 1) if total_presences > 0 else 100
    absences_count = total_presences - presences_valides

    # Récupérer les présences récentes
    presences = eleve.presence_set.all().order_by('-date')[:10]
    
    # Ajouter ces variables au contexte
    today = timezone.now().date()
    eleve = request.user.eleve_profile
    
    # Vérifier si l'élève peut pointer sa présence aujourd'hui
    peut_pointer = not Presence.objects.filter(eleve=eleve, date=today).exists()
    deja_pointe = not peut_pointer
    presence_aujourdhui = Presence.objects.filter(eleve=eleve, date=today, present=True).exists()

    context = {
        'eleve': eleve,
        'trimestres': trimestres,
        'taux_presence': taux_presence,
        'absences_count': absences_count,
        'presences': presences,
        'notes': notes,
        'peut_pointer': peut_pointer,
        'deja_pointe': deja_pointe,
        'presence_aujourdhui': presence_aujourdhui,
        'today': today,
        
    }

    return render(request, 'gestion/dashboards/eleve.html', context)



@login_required
def enseignant_dashboard(request):
    """
    Dashboard pour enseignant.
    """
    has_unread_notifications = request.user.notifications.filter(statut='NON_LU').exists()
    
    if request.user.role != 'enseignant':
        messages.error(request, "Accès refusé : vous n'êtes pas enseignant.")
        return redirect('home:accueil')

    user = request.user
    enseignements = Enseignement.objects.filter(enseignant=user).select_related('matiere', 'matiere__niveau')
    classes = Classe.objects.filter(niveau__in=[e.matiere.niveau for e in enseignements]).distinct()

    eleves_par_classe = {}
    for classe in classes:
        eleves_par_classe[classe] = Eleve.objects.filter(classe_actuelle=classe).order_by('utilisateur__last_name')

    trimestre_en_cours = 'T1'
    notes_a_saisir = []
    for enseignement in enseignements:
        matiere = enseignement.matiere
        niveau = matiere.niveau
        eleves = Eleve.objects.filter(classe_actuelle__niveau=niveau)
        for eleve in eleves:
            existe = Note.objects.filter(eleve=eleve, matiere=matiere, trimestre=trimestre_en_cours).exists()
            if not existe:
                notes_a_saisir.append({
                    'eleve': eleve,
                    'matiere': matiere,
                    'niveau': niveau
                })

    context = {
        'enseignements': enseignements,
        'classes': classes,
        'eleves_par_classe': eleves_par_classe,
        'notes_a_saisir': notes_a_saisir,
        'trimestre_en_cours': trimestre_en_cours,
        'has_unread_notifications': has_unread_notifications,
    }

    return render(request, 'gestion/dashboards/enseignant.html', context)


# Autres dashboards (exemples)
# @login_required
# def directeur_dashboard(request):
#     return render(request, 'gestion/dashboards/directeur.html')





@login_required
def surveillant_dashboard(request):
    return render(request, 'gestion/dashboards/surveillant.html')


# === AUTRES VUES ===

def logout_view(request):
    """
    Déconnexion de l'utilisateur.
    """
    logout(request)
    return redirect('home:accueil')
# home/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Cycle, Niveau
from .forms import CycleForm, NiveauForm

@login_required
def liste_cycles(request):
    cycles = Cycle.objects.all().order_by('nom')
    return render(request, 'gestion/dashboards/cycle_liste.html', {'cycles': cycles})

@login_required
def ajouter_cycle(request):
    if request.method == 'POST':
        form = CycleForm(request.POST)
        if form.is_valid():
            cycle = form.save()
            messages.success(request, f"Cycle '{cycle.nom}' ajouté avec succès.")
            return redirect('home:liste_cycles')
    else:
        form = CycleForm()
    return render(request, 'gestion/dashboards/cycle_ajouter.html', {'form': form})

@login_required
def modifier_cycle(request, pk):
    cycle = Cycle.objects.get(pk=pk)
    if request.method == 'POST':
        form = CycleForm(request.POST, instance=cycle)
        if form.is_valid():
            cycle = form.save()
            messages.success(request, f"Cycle '{cycle.nom}' mis à jour.")
            return redirect('home:liste_cycles')
    else:
        form = CycleForm(instance=cycle)
    return render(request, 'gestion/dashboards/cycle_modifier.html', {'form': form, 'cycle': cycle})

@login_required
def supprimer_cycle(request, pk):
    cycle = Cycle.objects.get(pk=pk)
    if request.method == 'POST':
        nom = cycle.nom
        cycle.delete()
        messages.success(request, f"Cycle '{nom}' supprimé.")
        return redirect('home:liste_cycles')
    return render(request, 'gestion/dashboards/cycle_confirmer_suppression.html', {'cycle': cycle})


# === NIVEAUX ===

@login_required
def liste_niveaux(request):
    niveaux = Niveau.objects.select_related('cycle').all().order_by('cycle__nom', 'nom')
    return render(request, 'gestion/dashboards/niveau_liste.html', {'niveaux': niveaux})

@login_required
def ajouter_niveau(request):
    if request.method == 'POST':
        form = NiveauForm(request.POST)
        if form.is_valid():
            niveau = form.save()
            messages.success(request, f"Niveau '{niveau.nom}' ajouté avec succès.")
            return redirect('home:liste_niveaux')
    else:
        form = NiveauForm()
    return render(request, 'gestion/dashboards/niveau_ajouter.html', {'form': form})

@login_required
def modifier_niveau(request, pk):
    niveau = Niveau.objects.get(pk=pk)
    if request.method == 'POST':
        form = NiveauForm(request.POST, instance=niveau)
        if form.is_valid():
            niveau = form.save()
            messages.success(request, f"Niveau '{niveau.nom}' mis à jour.")
            return redirect('home:liste_niveaux')
    else:
        form = NiveauForm(instance=niveau)
    return render(request, 'gestion/dashboards/niveau_modifier.html', {'form': form, 'niveau': niveau})

@login_required
def supprimer_niveau(request, pk):
    niveau = Niveau.objects.get(pk=pk)
    if request.method == 'POST':
        nom = niveau.nom
        niveau.delete()
        messages.success(request, f"Niveau '{nom}' supprimé.")
        return redirect('home:liste_niveaux')
    return render(request, 'gestion/dashboards/confirmer_suppression_niveau.html', {'niveau': niveau})


@login_required
def supprimer_classe(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    if request.method == 'POST':
        nom = classe.nom
        classe.delete()
        messages.success(request, f"Classe '{nom}' supprimée avec succès.")
        return redirect('home:liste_classes')
    return render(request, 'gestion/dashboards/supprimer_classe.html', {'classe': classe})


@login_required
def ajouter_classe(request):
    if request.method == 'POST':
        form = ClasseForm(request.POST)
        if form.is_valid():
            classe = form.save()
            messages.success(request, f"Classe '{classe.nom}' ajoutée avec succès.")
            return redirect('home:liste_classes')
    else:
        form = ClasseForm()
    return render(request, 'gestion/dashboards/classe_ajouter.html', {'form': form})



@login_required
def ajouter_eleve(request):
    if request.method == 'POST':
        form = EleveForm(request.POST)
        if form.is_valid():
            eleve = form.save()
            messages.success(request, f"Élève '{eleve.utilisateur.get_full_name()}' ajouté avec succès.")
            return redirect('home:liste_eleves')
    else:
        form = EleveForm()
    return render(request, 'gestion/dashboards/eleve_ajouter.html', {'form': form})


# === MODIFIER UN ÉLÈVE ===
@login_required
def modifier_eleve(request, pk):
    """
    Vue pour modifier un élève existant.
    """
    eleve = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        form = EleveForm(request.POST, instance=eleve)
        if form.is_valid():
            eleve = form.save()
            messages.success(request, f"Élève '{eleve.utilisateur.get_full_name()}' mis à jour.")
            return redirect('home:liste_eleves')
    else:
        form = EleveForm(instance=eleve)
    return render(request, 'gestion/dashboards/eleve_modifier.html', {'form': form, 'eleve': eleve})

# === SUPPRIMER UN ÉLÈVE ===
@login_required
def supprimer_eleve(request, pk):
    """
    Vue pour confirmer et supprimer un élève.
    """
    eleve = get_object_or_404(Eleve, pk=pk)
    if request.method == 'POST':
        nom = eleve.utilisateur.get_full_name()
        eleve.delete()
        messages.success(request, f"Élève '{nom}' supprimé définitivement.")
        return redirect('home:liste_eleves')
    return render(request, 'gestion/dashboards/confirmer_suppression_eleve.html', {'eleve': eleve})


@login_required
def modifier_classe(request, pk):
    classe = Classe.objects.get(pk=pk)
    if request.method == 'POST':
        form = ClasseForm(request.POST, instance=classe)
        if form.is_valid():
            classe = form.save()
            messages.success(request, f"Classe '{classe.nom}' mise à jour.")
            return redirect('home:liste_classes')
    else:
        form = ClasseForm(instance=classe)
    return render(request, 'gestion/classe_form.html', {
        'form': form,
        'title': f'Modifier la Classe : {classe.nom}'
    })
  
@login_required
def ajouter_classe(request):
    if request.method == 'POST':
        form = ClasseForm(request.POST)
        if form.is_valid():
            classe = form.save()
            messages.success(request, f"Classe '{classe.nom}' ajoutée avec succès.")
            return redirect('home:liste_classes')
    else:
        form = ClasseForm()
    return render(request, 'gestion/dashboards/classe_ajouter.html', {'form': form})


# home/views.py
@login_required
def liste_classes(request):
    classes = Classe.objects.select_related('niveau').all().order_by('niveau__cycle__nom', 'niveau__nom', 'nom')
    return render(request, 'gestion/classes_liste.html', {'classes': classes})

@login_required
def liste_eleves(request):
    eleves = Eleve.objects.select_related('utilisateur', 'classe_actuelle').all().order_by('utilisateur__last_name')
    return render(request, 'gestion/dashboards/eleves_liste.html', {'eleves': eleves})




# === VUES : Liste des enseignants ===
@login_required
def liste_enseignants(request):
    """
    Affiche la liste de tous les utilisateurs avec le rôle 'enseignant'
    """
    enseignants = Utilisateur.objects.filter(role='enseignant').order_by('last_name', 'first_name')

    # Optionnel : Ajouter des statistiques
    total = enseignants.count()

    context = {
        'enseignants': enseignants,
        'total': total,
    }
    return render(request, 'gestion/dashboards/enseignants_liste.html', context)


# === VUES : Liste des parents ===
@login_required
def liste_parents(request):
    """
    Affiche la liste de tous les parents et leurs enfants associés.
    """
    parents = Utilisateur.objects.filter(role='parent').select_related('parent_profile').prefetch_related('parent_profile__enfants').order_by('last_name', 'first_name')

    # Structure : parent → liste d'enfants
    parents_data = []
    for user in parents:
        try:
            enfants = user.parent_profile.enfants.all()
        except:
            enfants = []
        parents_data.append({
            'user': user,
            'enfants': enfants,
            'total_enfants': enfants
        })

    context = {
        'parents_data': parents_data,
        'total': len(parents_data)
    }
    return render(request, 'gestion/dashboards/parents_liste.html', context)


@login_required
def liste_enseignants(request):
    enseignants = Utilisateur.objects.filter(role='enseignant').order_by('last_name', 'first_name')
    return render(request, 'gestion/dashboards/enseignants_liste.html', {'enseignants': enseignants})

@login_required
def ajouter_enseignant(request):
    if request.method == 'POST':
        form = EnseignantForm(request.POST)
        if form.is_valid():
            enseignant = form.save()
            messages.success(request, f"Enseignant '{enseignant.get_full_name()}' ajouté avec succès.")
            return redirect('home:liste_enseignants')
    else:
        form = EnseignantForm()
    return render(request, 'gestion/dashboards/enseignant_ajouter.html', {'form': form})

@login_required
def modifier_enseignant(request, pk):
    enseignant = get_object_or_404(Utilisateur, pk=pk, role='enseignant')
    if request.method == 'POST':
        form = EnseignantForm(request.POST, instance=enseignant)
        if form.is_valid():
            enseignant = form.save()
            messages.success(request, f"Enseignant '{enseignant.get_full_name()}' mis à jour.")
            return redirect('home:liste_enseignants')
    else:
        form = EnseignantForm(instance=enseignant)
    return render(request, 'gestion/dashboards/enseignant_modifier.html', {'form': form, 'enseignant': enseignant})

@login_required
def supprimer_enseignant(request, pk):
    enseignant = get_object_or_404(Utilisateur, pk=pk, role='enseignant')
    if request.method == 'POST':
        nom = enseignant.get_full_name()
        enseignant.delete()
        messages.success(request, f"Enseignant '{nom}' supprimé.")
        return redirect('home:liste_enseignants')
    return render(request, 'gestion/dashboards/confirmer_suppression_enseignant.html', {'enseignant': enseignant})

@login_required
def ajouter_parent(request):
    if request.method == 'POST':
        form = ParentForm(request.POST)
        if form.is_valid():
            parent = form.save()
            messages.success(request, f"Parent '{parent.get_full_name()}' ajouté avec succès.")
            return redirect('home:liste_parents')
        else:
            messages.error(request, "Corrigez les erreurs ci-dessous.")
    else:
        form = ParentForm()
    return render(request, 'gestion/dashboards/parent_ajouter.html', {'form': form})


# home/views.py
@login_required
def parent_dashboard(request):
    try:
        parent = request.user.parent_profile
    except Parent.DoesNotExist:
        messages.error(request, "Profil parent introuvable.")
        return redirect('home:login')

    enfants = parent.enfants.all().prefetch_related('notes__matiere', 'classe_actuelle__niveau')
    enfants_avec_notes = []

    # Statistiques globales
    mois_en_cours = date.today().month
    annee_en_cours = date.today().year
    total_absences = 0
    total_retards = 0

    for enfant in enfants:
        # Organiser les notes par trimestre
        trimestres_data = {}
        
        # Pour chaque trimestre
        for trimestre_code, trimestre_nom in Note.TRIMESTRE_CHOICES:
            notes_trimestre = enfant.notes.filter(trimestre=trimestre_code)
            
            # Organiser par matière
            matieres_dict = {}
            for note in notes_trimestre:
                if note.matiere not in matieres_dict:
                    matieres_dict[note.matiere] = {
                        'matiere': note.matiere,
                        'notes': [],
                        'devoir1': None,
                        'devoir2': None,
                        'devoir3': None,
                        'composition': None,
                        'departemental': None
                    }
                
                # Ajouter à la liste de toutes les notes
                matieres_dict[note.matiere]['notes'].append(note)
                
                # Classer les notes spécifiques
                if note.type_evaluation == 'DS1':
                    matieres_dict[note.matiere]['devoir1'] = note
                elif note.type_evaluation == 'DS2':
                    matieres_dict[note.matiere]['devoir2'] = note
                elif note.type_evaluation == 'DS3':
                    matieres_dict[note.matiere]['devoir3'] = note
                elif note.type_evaluation == 'COMP':
                    matieres_dict[note.matiere]['composition'] = note
                elif note.type_evaluation == 'DEP':
                    matieres_dict[note.matiere]['departemental'] = note
            
            # Calculer les moyennes par matière
            matieres_data = []
            total_matiere = Decimal('0.0')
            poids_total = Decimal('0.0')
            
            for matiere, data in matieres_dict.items():
                notes_list = data['notes']
                if notes_list:
                    total = sum(n.valeur * Decimal(str(n.coefficient)) for n in notes_list)
                    poids = sum(Decimal(str(n.coefficient)) for n in notes_list)
                    moyenne = total / poids
                else:
                    moyenne = Decimal('0.0')
                
                data['moyenne'] = moyenne
                total_matiere += moyenne * Decimal(str(matiere.coefficient))
                poids_total += Decimal(str(matiere.coefficient))
                matieres_data.append(data)
            
            # Calculer la moyenne générale du trimestre
            if poids_total > 0:
                moyenne_generale = float(total_matiere / poids_total)
                moyenne_generale = round(moyenne_generale, 2)
            else:
                moyenne_generale = 0.0
            
            trimestres_data[trimestre_code] = {
                'nom': trimestre_nom,
                'matieres': matieres_data,
                'moyenne': moyenne_generale
            }
        
        # CORRECTION ICI : Utiliser le bon nom pour accéder aux présences
        # Si vous avez défini related_name='presences' dans le modèle Presence
        # Sinon, utilisez le nom approprié
        try:
            # Essayer avec différentes possibilités
            if hasattr(enfant, 'presences'):
                presences = enfant.presences
            elif hasattr(enfant, 'presence'):
                presences = enfant.presence
            else:
                # Si rien ne fonctionne, utilisez presence_set
                presences = enfant.presence_set
            
            # Calculer les absences
            absences_enfant = presences.filter(
                present=False,
                date__year=annee_en_cours,
                date__month=mois_en_cours
            ).count()
            
            # Calculer les retards - seulement si le champ retard existe
            try:
                retards_enfant = presences.filter(
                    retard=True,
                    date__year=annee_en_cours,
                    date__month=mois_en_cours
                ).count()
            except FieldError:
                retards_enfant = 0
            
            total_absences += absences_enfant
            total_retards += retards_enfant
            
            # Calculer le taux de présence
            total_presences = presences.count()
            presences_valides = presences.filter(present=True).count()
            taux_presence = round(presences_valides / total_presences * 100, 1) if total_presences > 0 else 100
            
        except Exception as e:
            # En cas d'erreur, utiliser des valeurs par défaut
            absences_enfant = 0
            retards_enfant = 0
            taux_presence = 100
            logger.error(f"Erreur lors de la récupération des présences pour {enfant}: {str(e)}")

        enfants_avec_notes.append({
            'enfant': enfant,
            'trimestre1_data': trimestres_data.get('T1', {
                'matieres': [],
                'moyenne': 0.0
            }),
            'trimestre2_data': trimestres_data.get('T2', {
                'matieres': [],
                'moyenne': 0.0
            }),
            'trimestre3_data': trimestres_data.get('T3', {
                'matieres': [],
                'moyenne': 0.0
            }),
            'moyenne_t1': trimestres_data.get('T1', {}).get('moyenne', 0.0),
            'moyenne_t2': trimestres_data.get('T2', {}).get('moyenne', 0.0),
            'moyenne_t3': trimestres_data.get('T3', {}).get('moyenne', 0.0),
            'absences': absences_enfant,
            'retards': retards_enfant,
            'taux_presence': taux_presence,
            'classe': enfant.classe_actuelle,
            'niveau': enfant.classe_actuelle.niveau if enfant.classe_actuelle else None
        })

    context = {
        'parent': parent,
        'enfants_avec_notes': enfants_avec_notes,
        'total_enfants': enfants.count(),
        'total_absences': total_absences,
        'total_retards': total_retards,
        'mois_en_cours': mois_en_cours,
        'annee_en_cours': annee_en_cours,
    }

    return render(request, 'gestion/dashboards/parent_dashboard.html', context)






@login_required
def modifier_parent(request, pk):
    # 1. Vérifier que l'utilisateur existe, est parent, et que l'utilisateur connecté a le droit de modifier (optionnel)
    utilisateur = get_object_or_404(Utilisateur, pk=pk, role='parent')

    # 2. Accéder au profil parent (via OneToOneField)
    try:
        parent_profile = utilisateur.parent_profile  # Ex: Parent.objects.get(utilisateur=utilisateur)
    except Exception as e:
        messages.error(request, "Ce compte n'a pas de profil parent associé.")
        return redirect('home:liste_parents')

    # 3. Gérer le formulaire
    if request.method == 'POST':
        form = ParentForm(request.POST, instance=utilisateur)  # Supposons que le formulaire modifie l'Utilisateur
        if form.is_valid():
            form.save()
            messages.success(request, f"Le profil de '{utilisateur.get_full_name()}' a été mis à jour avec succès.")
            return redirect('home:liste_parents')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ParentForm(instance=utilisateur)

    return render(request, 'gestion/dashboards/modifier_parent.html', {
        'form': form,
        'parent': parent_profile,
        'utilisateur': utilisateur
    })
    
    
@login_required
def supprimer_parent(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk, role='parent')
    try:
        parent = utilisateur.parent_profile
        enfants = parent.enfants.all()
    except:
        parent = None
        enfants = []

    if request.method == 'POST':
        nom = utilisateur.get_full_name()
        utilisateur.delete()
        messages.success(request, f"Parent '{nom}' supprimé définitivement.")
        return redirect('home:liste_parents')

    return render(request, 'gestion/dashboards/supprimer_parent.html', {
        'parent': parent,
        'enfants': enfants
    })

@login_required
def secretaire_dashboard(request):
    # Vérifier que l'utilisateur est bien un secrétaire
    if request.user.role not in ['secretaire', 'admin', 'directeur']:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à accéder à cette page.")
        return redirect('home:home')
    
    # Statistiques globales
    total_eleves = Eleve.objects.count()
    total_classes = Classe.objects.count()
    total_niveaux = Niveau.objects.count()
    
    # Taux de présence global
    total_presences = Presence.objects.count()
    presences_valides = Presence.objects.filter(present=True).count()
    taux_presence_global = round(presences_valides / total_presences * 100, 1) if total_presences > 0 else 100
    
    # Élèves récemment inscrits
    eleves_recents = Eleve.objects.filter(
        utilisateur__date_joined__gte=date.today() - timedelta(days=30)
    ).order_by('-utilisateur__date_joined')[:5]
    
    # CORRECTION : Utiliser une logique appropriée pour les élèves en attente
    # Si le modèle Eleve n'a pas de champ statut, on considère qu'un élève est en attente s'il n'a pas de classe
    eleves_en_attente = Eleve.objects.filter(classe_actuelle__isnull=True).count()
    
    # Statistiques financières
    annee_en_cours = date.today().year
    trimestre_en_cours = 'T1'  # À adapter selon la date
    
    # Total des frais scolaires pour l'année
    total_frais = Frais.objects.filter(
        Q(date_limite__year=annee_en_cours)
    ).aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
    
    # CORRECTION PRINCIPALE : Utiliser date_paiement au lieu de date et montant_paye au lieu de montant
    # Total des paiements validés
    total_paiements = Paiement.objects.filter(
        date_paiement__year=annee_en_cours,
        status='Payé'
    ).aggregate(total=Sum('montant_paye'))['total'] or Decimal('0.00')
    
    # Taux de paiement global
    taux_paiement = round(total_paiements / total_frais * 100, 1) if total_frais > 0 else 100
    
    # Classes avec leurs effectifs
    classes_data = []
    for classe in Classe.objects.all():
        effectif = Eleve.objects.filter(classe_actuelle=classe).count()
        taux_paiement_classe = 0
        
        # Calculer le taux de paiement pour la classe
        eleves_classe = Eleve.objects.filter(classe_actuelle=classe)
        if eleves_classe.exists():
            total_frais_classe = Frais.objects.filter(
                niveau=classe.niveau,
                date_limite__year=annee_en_cours
            ).aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
            
            # CORRECTION PRINCIPALE : Utiliser date_paiement au lieu de date et montant_paye au lieu de montant
            total_paiements_classe = Paiement.objects.filter(
                eleve__in=eleves_classe,
                date_paiement__year=annee_en_cours,
                status='Payé'
            ).aggregate(total=Sum('montant_paye'))['total'] or Decimal('0.00')
            
            taux_paiement_classe = round(total_paiements_classe / total_frais_classe * 100, 1) if total_frais_classe > 0 else 0
        
        classes_data.append({
            'classe': classe,
            'effectif': effectif,
            'taux_paiement': taux_paiement_classe
        })
    
    # Matières les plus enseignées
    matieres_data = []
    # Utiliser annotate pour compter les notes
    from django.db.models import Count
    
    # Option 1 : Si vous n'avez pas de related_name personnalisé dans le modèle Note
    matieres = Matiere.objects.annotate(note_count=Count('note'))
    
    for matiere in matieres:
        matieres_data.append({
            'matiere': matiere,
            'effectif': matiere.note_count
        })
    
    # Trier par effectif décroissant
    matieres_data = sorted(
        matieres_data, 
        key=lambda x: x['effectif'], 
        reverse=True
    )[:5]
    
    # Presences récentes
    presences_recents = Presence.objects.filter(
        date__gte=date.today() - timedelta(days=7)
    ).order_by('-date')[:10]
    
    # Notifications récentes
    notifications_recentes = Notification.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')[:5]
    
    # Documents en attente
    documents_en_attente = [
        {
            'type': "Fiche d'inscription",
            'nom': "Jean Dupont",
            'date': "2023-08-25",
            'priorite': "haute"
        },
        {
            'type': "Certificat médical",
            'nom': "Marie Martin",
            'date': "2023-08-26",
            'priorite': "moyenne"
        },
        {
            'type': "Attestation de paiement",
            'nom': "Pierre Bernard",
            'date': "2023-08-27",
            'priorite': "haute"
        }
    ]
    
    pourcentage_en_attente = 0
    if total_eleves > 0:
        pourcentage_en_attente = (eleves_en_attente / total_eleves) * 100
    
    context = {
        'total_eleves': total_eleves,
        'total_classes': total_classes,
        'total_niveaux': total_niveaux,
        'taux_presence_global': taux_presence_global,
        'eleves_recents': eleves_recents,
        'eleves_en_attente': eleves_en_attente,
        'total_frais': total_frais,
        'total_paiements': total_paiements,
        'taux_paiement': taux_paiement,
        'classes_data': classes_data,
        'matieres_data': matieres_data,
        'presences_recents': presences_recents,
        'notifications_recentes': notifications_recentes,
        'documents_en_attente': documents_en_attente,
        'trimestre_en_cours': trimestre_en_cours,
        'annee_en_cours': annee_en_cours,
        'pourcentage_en_attente': pourcentage_en_attente,
    }
    
    return render(request, 'gestion/dashboards/secretaire_dashboard.html', context)


@login_required
def surveillant_dashboard(request):
    # Vérifier que l'utilisateur est bien un surveillant
    if request.user.role != 'surveillant':
        messages.error(request, "Accès refusé : vous n'êtes pas surveillant.")
        return redirect('home:login')
    
    # Statistiques globales
    total_eleves = Eleve.objects.count()
    
    # Taux de présence global
    total_presences = Presence.objects.count()
    presences_valides = Presence.objects.filter(present=True).count()
    taux_presence_global = round(presences_valides / total_presences * 100, 1) if total_presences > 0 else 100
    
    # Absences et retards récents
    annee_en_cours = date.today().year
    mois_en_cours = date.today().month
    
    # Total des absences ce mois-ci
    absences_mois = Presence.objects.filter(
        present=False,
        date__year=annee_en_cours,
        date__month=mois_en_cours
    ).count()
    
    # Total des retards ce mois-ci
    retards_mois = Presence.objects.filter(
        retard=True,
        date__year=annee_en_cours,
        date__month=mois_en_cours
    ).count()
    
    # Élèves avec le plus d'absences
    eleves_absences = []
    for eleve in Eleve.objects.all():
        absences = Presence.objects.filter(
            eleve=eleve,
            present=False,
            date__year=annee_en_cours,
            date__month=mois_en_cours
        ).count()
        
        if absences > 0:
            eleves_absences.append({
                'eleve': eleve,
                'absences': absences
            })
    
    # Trier par nombre d'absences décroissant
    eleves_absences = sorted(
        eleves_absences, 
        key=lambda x: x['absences'], 
        reverse=True
    )[:5]
    
    # Élèves avec le plus de retards
    eleves_retards = []
    for eleve in Eleve.objects.all():
        retards = Presence.objects.filter(
            eleve=eleve,
            retard=True,
            date__year=annee_en_cours,
            date__month=mois_en_cours
        ).count()
        
        if retards > 0:
            eleves_retards.append({
                'eleve': eleve,
                'retards': retards
            })
    
    # Trier par nombre de retards décroissant
    eleves_retards = sorted(
        eleves_retards, 
        key=lambda x: x['retards'], 
        reverse=True
    )[:5]
    
   
    
    # Classes avec leurs taux d'absence
    classes_data = []
    for classe in Classe.objects.all():
        eleves_classe = Eleve.objects.filter(classe_actuelle=classe)
        total_presences_classe = Presence.objects.filter(
            eleve__in=eleves_classe,
            date__year=annee_en_cours,
            date__month=mois_en_cours
        ).count()
        
        absences_classe = Presence.objects.filter(
            eleve__in=eleves_classe,
            present=False,
            date__year=annee_en_cours,
            date__month=mois_en_cours
        ).count()
        
        taux_absence = round(absences_classe / total_presences_classe * 100, 1) if total_presences_classe > 0 else 0
        
        classes_data.append({
            'classe': classe,
            'effectif': eleves_classe.count(),
            'absences': absences_classe,
            'taux_absence': taux_absence
        })
    
    # Présences du jour
    presences_du_jour = Presence.objects.filter(
        date=date.today()
    ).order_by('eleve__classe_actuelle__nom', 'eleve__utilisateur__last_name')
    
    # Notifications récentes
    notifications_recentes = Notification.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')[:5]
    
    # Événements récents
    evenements_recents = [
        {
            'date': "Aujourd'hui",
            'type': "Surveillance",
            'description': "Contrôle des présences en cours"
        },
        {
            'date': "Hier",
            'type': "Sanction",
            'description': "3 élèves sanctionnés pour indiscipline"
        },
        {
            'date': "Il y a 3 jours",
            'type': "Réunion",
            'description': "Réunion des surveillants"
        }
    ]
    
    context = {
        'total_eleves': total_eleves,
        'taux_presence_global': taux_presence_global,
        'absences_mois': absences_mois,
        'retards_mois': retards_mois,
        'eleves_absences': eleves_absences,
        'eleves_retards': eleves_retards,
        'classes_data': classes_data,
        'presences_du_jour': presences_du_jour,
        'notifications_recentes': notifications_recentes,
        'evenements_recents': evenements_recents,
        'mois_en_cours': mois_en_cours,
        'annee_en_cours': annee_en_cours,
    }
    
    return render(request, 'gestion/dashboards/surveillant_dashboard.html', context)



# home/views.py


@require_POST
@csrf_protect
@login_required
def pointer_presence(request):
    try:
        # Vérifier que l'utilisateur est un élève
        if not hasattr(request.user, 'eleve_profile'):
            return JsonResponse({
                'success': False,
                'error': 'Vous n\'êtes pas autorisé à pointer votre présence'
            }, status=403)
        
        # Récupérer la date (par défaut aujourd'hui)
        date_str = request.POST.get('date')
        if date_str:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Format de date invalide'
                }, status=400)
        else:
            date = timezone.now().date()
        
        # Vérifier si la présence n'a pas déjà été enregistrée
        eleve = request.user.eleve_profile
        if Presence.objects.filter(eleve=eleve, date=date).exists():
            return JsonResponse({
                'success': False,
                'error': 'Vous avez déjà pointé votre présence pour cette date'
            }, status=400)
        
        # Enregistrer la présence
        presence = Presence.objects.create(
            eleve=eleve,
            date=date,
            present=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Présence enregistrée avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        
        
        
        # paiements 
        
        
# home/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from datetime import date, timedelta
from decimal import Decimal
import logging
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Configuration du logging
logger = logging.getLogger(__name__)
@login_required
def paiement_dashboard(request):
    """Affiche le tableau de bord des paiements selon le rôle de l'utilisateur"""
    role = request.user.role
    
    # Initialiser les variables
    eleve = None
    enfants = []
    frais = None
    paiements = None
    total_a_payer = Decimal('0.00')
    total_paye = Decimal('0.00')
    taux_paiement = 0
    
    # Obtenir l'enfant sélectionné pour les parents
    enfant_id = request.GET.get('enfant_id')
    
    # Cas 1: Élève - voir ses propres paiements
    if role == 'eleve':
        try:
            eleve = request.user.eleve_profile
            frais = Frais.objects.filter(niveau=eleve.classe_actuelle.niveau)
            
            # Calculer les totaux
            for f in frais:
                total_a_payer += f.montant
                total_paye += f.paiements.filter(
                    eleve=eleve, 
                    status='Payé'
                ).aggregate(total=Sum('montant_paye'))['total'] or Decimal('0.00')
            
            if total_a_payer > 0:
                taux_paiement = round(total_paye / total_a_payer * 100, 1)
            else:
                taux_paiement = 100
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de paiement pour l'élève: {str(e)}")
            messages.error(request, "Une erreur est survenue lors de la récupération de vos données de paiement.")
    
    # Cas 2: Parent - voir les paiements de ses enfants
    elif role == 'parent':
        try:
            parent = request.user.parent_profile
            enfants = parent.enfants.all()
            
            # Si un enfant est sélectionné, afficher ses données
            if enfant_id:
                try:
                    eleve = Eleve.objects.get(id=enfant_id, parent=parent)
                    frais = Frais.objects.filter(niveau=eleve.classe_actuelle.niveau)
                    
                    # Calculer les totaux pour l'enfant sélectionné
                    for f in frais:
                        total_a_payer += f.montant
                        total_paye += f.paiements.filter(
                            eleve=eleve, 
                            status='Payé'
                        ).aggregate(total=Sum('montant_paye'))['total'] or Decimal('0.00')
                    
                    if total_a_payer > 0:
                        taux_paiement = round(total_paye / total_a_payer * 100, 1)
                    else:
                        taux_paiement = 100
                        
                except Eleve.DoesNotExist:
                    messages.error(request, "Enfant non trouvé ou non autorisé.")
            else:
                # Calculer les totaux pour tous les enfants
                for enfant in enfants:
                    frais_enfant = Frais.objects.filter(niveau=enfant.classe_actuelle.niveau)
                    for f in frais_enfant:
                        total_a_payer += f.montant
                        total_paye += f.paiements.filter(
                            eleve=enfant, 
                            status='Payé'
                        ).aggregate(total=Sum('montant_paye'))['total'] or Decimal('0.00')
                
                if total_a_payer > 0:
                    taux_paiement = round(total_paye / total_a_payer * 100, 1)
                else:
                    taux_paiement = 100
                    
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de paiement pour le parent: {str(e)}")
            messages.error(request, "Une erreur est survenue lors de la récupération des données de paiement.")
    
    # Cas 3: Administrateur, directeur, secrétaire - voir tous les paiements
    elif role in ['admin', 'directeur', 'secretaire']:
        # Filtrer par classe ou niveau si spécifié
        classe_id = request.GET.get('classe')
        niveau_id = request.GET.get('niveau')
        
        # Obtenir tous les frais et paiements
        frais = Frais.objects.all()
        paiements = Paiement.objects.select_related('eleve__utilisateur', 'frais', 'eleve__classe_actuelle').all()
        
        # Appliquer les filtres si nécessaire
        if classe_id:
            paiements = paiements.filter(eleve__classe_actuelle_id=classe_id)
            frais = frais.filter(niveau__classes__id=classe_id)
        elif niveau_id:
            paiements = paiements.filter(eleve__classe_actuelle__niveau_id=niveau_id)
            frais = frais.filter(niveau_id=niveau_id)
        
        # Calculer les totaux
        total_a_payer = frais.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
        total_paye = paiements.filter(status='Payé').aggregate(total=Sum('montant_paye'))['total'] or Decimal('0.00')
        
        if total_a_payer > 0:
            taux_paiement = round(total_paye / total_a_payer * 100, 1)
        else:
            taux_paiement = 100
    
    # Pagination des paiements
    if role in ['admin', 'directeur', 'secretaire']:
        paiements_list = paiements.order_by('-date_paiement')
    else:
        # Pour élève/parent, on utilise une liste plus simple
        paiements_list = []
        if role == 'eleve':
            for f in frais:
                paiements_list.extend(f.paiements.filter(eleve=eleve).select_related('frais', 'eleve__utilisateur'))
        else:
            if enfant_id:
                try:
                    eleve = Eleve.objects.get(id=enfant_id)
                    for f in frais:
                        paiements_list.extend(f.paiements.filter(eleve=eleve).select_related('frais', 'eleve__utilisateur'))
                except Eleve.DoesNotExist:
                    pass
            else:
                for enfant in enfants:
                    for f in Frais.objects.filter(niveau=enfant.classe_actuelle.niveau):
                        paiements_list.extend(f.paiements.filter(eleve=enfant).select_related('frais', 'eleve__utilisateur'))
        
        # Trier par date décroissante
        paiements_list.sort(key=lambda x: x.date_paiement, reverse=True)
    
    # Configuration de la pagination
    paginator = Paginator(paiements_list, 10)  # 10 paiements par page
    page = request.GET.get('page', 1)
    
    try:
        paginated_paiements = paginator.page(page)
    except PageNotAnInteger:
        paginated_paiements = paginator.page(1)
    except EmptyPage:
        paginated_paiements = paginator.page(paginator.num_pages)
    
    # Ajouter les statistiques pour les graphiques
    stats = {
        'payes': 0,
        'partiels': 0,
        'non_payes': 0
    }
    
    if role in ['admin', 'directeur', 'secretaire']:
        stats['payes'] = paiements.filter(status='Payé').count()
        stats['partiels'] = paiements.filter(status='Partiellement payé').count()
        stats['non_payes'] = paiements.filter(status='Non payé').count()
    else:
        # Pour les élèves et parents, calculer les stats
        for paiement in paiements_list:
            if paiement.status == 'Payé':
                stats['payes'] += 1
            elif paiement.status == 'Partiellement payé':
                stats['partiels'] += 1
            else:
                stats['non_payes'] += 1
    
    context = {
        'role': role,
        'eleve': eleve,
        'enfants': enfants,
        'frais': frais,
        'paiements': paginated_paiements,
        'total_a_payer': total_a_payer,
        'total_paye': total_paye,
        'taux_paiement': taux_paiement,
        'current_year': date.today().year,
        'stats': stats,
        'enfant_id': enfant_id,
    }
    
    return render(request, 'gestion/dashboards/paiement_dashboard.html', context)


# home/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from decimal import Decimal
from datetime import date
from .models import Frais, Paiement, Eleve




# home/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from .models import Paiement, Frais
from .forms import CaisseForm
# home/views.py



# home/views.py
@login_required
def caisse(request):
    """
    Vue simple de caisse enregistreuse comme dans les supermarchés
    """
    # Vérifier que l'utilisateur a le droit d'accéder à la caisse
    if request.user.role not in ['secretaire', 'admin', 'directeur']:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à accéder à la caisse")
        return redirect('home:dashboard')
    
    # Initialiser le formulaire
    form = CaisseForm()
    montant_rendu = None
    paiement_enregistre = None
    
    if request.method == "POST":
        form = CaisseForm(request.POST)
        if form.is_valid():
            # Récupérer les données du formulaire
            eleve = form.cleaned_data['eleve']
            frais = form.cleaned_data['frais']
            montant_paye = form.cleaned_data['montant_paye']
            type_paiement = form.cleaned_data['type_paiement']
            numero_transaction = form.cleaned_data['numero_transaction']
            
            # Calculer le montant dû
            montant_total = frais.montant
            
            # Créer le paiement
            paiement = Paiement(
                eleve=eleve,
                frais=frais,
                montant_total=montant_total,
                montant_paye=montant_paye,
                type_paiement=type_paiement,
                numero_transaction=numero_transaction,
                personnel=request.user
            )
            
            # Calculer la différence rendue
            if montant_paye > montant_total:
                paiement.difference_rendue = montant_paye - montant_total
                montant_rendu = paiement.difference_rendue
            else:
                paiement.difference_rendue = Decimal('0.00')
                montant_rendu = Decimal('0.00')
            
            # Déterminer le statut - UTILISER 'status' AU LIEU DE 'statut'
            if montant_paye >= montant_total:
                paiement.status = 'Payé'
            elif montant_paye > Decimal('0.00'):
                paiement.status = 'Partiellement payé'
            else:
                paiement.status = 'Non payé'
            
            # Sauvegarder le paiement
            paiement.save()
            
            paiement_enregistre = paiement
            messages.success(request, f"Paiement enregistré avec succès ! Différence rendue : {montant_rendu} XAF")
    
    context = {
        'form': form,
        'montant_rendu': montant_rendu,
        'paiement_enregistre': paiement_enregistre,
        'title': "Caisse enregistreuse"
    }
    
    return render(request, 'gestion/caisse/caisse.html', context)



@login_required
def detail_paiement(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérifier que l'utilisateur a le droit de voir ce paiement
    if request.user.role == 'eleve' and paiement.eleve.utilisateur != request.user:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à voir ce paiement")
        return redirect('home:paiement_dashboard')
    elif request.user.role == 'parent':
        try:
            parent = request.user.parent_profile
            if paiement.eleve not in parent.enfants.all():
                messages.error(request, "Accès refusé : vous n'êtes pas autorisé à voir ce paiement")
                return redirect('home:paiement_dashboard')
        except Parent.DoesNotExist:
            messages.error(request, "Profil parent introuvable")
            return redirect('home:paiement_dashboard')
    
    return render(request, 'gestion/paiements/detail_paiement.html', {
        'paiement': paiement
    })


# home/views.py
@login_required
def detail_paiement(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    
    # Vérifier que l'utilisateur a le droit de voir ce paiement
    if request.user.role == 'eleve' and paiement.eleve.utilisateur != request.user:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à voir ce paiement")
        return redirect('home:paiement_dashboard')
    elif request.user.role == 'parent':
        try:
            parent = request.user.parent_profile
            if paiement.eleve not in parent.enfants.all():
                messages.error(request, "Accès refusé : vous n'êtes pas autorisé à voir ce paiement")
                return redirect('home:paiement_dashboard')
        except Parent.DoesNotExist:
            messages.error(request, "Profil parent introuvable")
            return redirect('home:paiement_dashboard')
    
    return render(request, 'gestion/paiements/detail_paiement.html', {
        'paiement': paiement
    })
    
    # home/views.py
@login_required
def liste_paiements(request):
    # Vérifier que l'utilisateur a le droit d'accéder à la liste des paiements
    if request.user.role not in ['secretaire', 'admin', 'directeur', 'parent', 'eleve']:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à voir les paiements")
        return redirect('home:dashboard')

    # Initialiser la liste des paiements
    paiements_list = Paiement.objects.select_related('eleve__utilisateur', 'eleve__classe_actuelle', 'frais')
    
    # Filtrer selon le rôle de l'utilisateur
    if request.user.role == 'eleve':
        paiements_list = paiements_list.filter(eleve__utilisateur=request.user)
    elif request.user.role == 'parent':
        try:
            parent = request.user.parent_profile
            paiements_list = paiements_list.filter(eleve__in=parent.enfants.all())
        except Parent.DoesNotExist:
            paiements_list = Paiement.objects.none()
    
    # Filtre par statut
    status = request.GET.get("status", "").strip()
    if status and status in dict(STATUS_PAIEMENT_CHOICES).keys():
        paiements_list = paiements_list.filter(status=status)

    # Filtre par élève
    eleve_id = request.GET.get("eleve", "").strip()
    if eleve_id and request.user.role in ['secretaire', 'admin', 'directeur']:
        paiements_list = paiements_list.filter(eleve_id=eleve_id)

    # Filtre par période
    periode = request.GET.get("periode", "").strip()
    today = date.today()

    if periode == "today":
        paiements_list = paiements_list.filter(date_paiement=today)
    elif periode == "week":
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        paiements_list = paiements_list.filter(date_paiement__range=[start_week, end_week])
    elif periode == "month":
        paiements_list = paiements_list.filter(date_paiement__month=today.month, date_paiement__year=today.year)

    # Pagination
    paginator = Paginator(paiements_list, 10)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Statistiques
    stats = {
        'total': paiements_list.count(),
        'payes': paiements_list.filter(status='Payé').count(),
        'partiels': paiements_list.filter(status='Partiellement payé').count(),
        'non_payes': paiements_list.filter(status='Non payé').count(),
    }

    # Liste des élèves pour le filtre (réservé aux secrétaires, admins et directeurs)
    eleves = []
    if request.user.role in ['secretaire', 'admin', 'directeur']:
        eleves = Eleve.objects.all().order_by('utilisateur__last_name')

    return render(request, 'gestion/paiements/liste_paiements.html', {
        'paiements': page_obj,
        'stats': stats,
        'filtre_statut': statut,
        'filtre_eleve': eleve_id,
        'filtre_periode': periode,
        'eleves': eleves,
        'STATUS_PAIEMENT_CHOICES': STATUS_PAIEMENT_CHOICES,
    })
    
    
    # home/views.py
@login_required
def caisse_dashboard(request):
    # Vérifier que l'utilisateur a le droit d'accéder à la caisse
    if request.user.role not in ['secretaire', 'admin', 'directeur']:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à accéder à la caisse")
        return redirect('home:dashboard')

    # Frais à payer (non payés ou partiellement payés)
    frais_a_payer = Frais.objects.filter(date_limite__gte=date.today())
    
    # Paiements récents
    paiements = Paiement.objects.all().order_by('-date_paiement')[:20]

    # Statistiques financières
    annee_en_cours = date.today().year
    total_frais = frais_a_payer.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')
    
    paiements_valides = paiements.filter(status='Payé')
    total_paiements = paiements_valides.aggregate(total=Sum('montant_paye'))['total'] or Decimal('0.00')
    
    taux_paiement = round(total_paiements / total_frais * 100, 1) if total_frais > 0 else 100
    
    # Frais en retard
    frais_en_retard = Frais.objects.filter(date_limite__lt=date.today()).exclude(
        paiements__status='Payé'
    ).distinct()

    return render(request, 'gestion/paiements/caisse_dashboard.html', {
        'frais_a_payer': frais_a_payer,
        'paiements': paiements,
        'total_frais': total_frais,
        'total_paiements': total_paiements,
        'taux_paiement': taux_paiement,
        'frais_en_retard': frais_en_retard,
        'annee_en_cours': annee_en_cours,
    })
    
    
    
    
@login_required
def ajouter_frais(request):
    """
    Vue pour ajouter de nouveaux frais scolaires.
    Accessible uniquement aux administrateurs, directeurs et secrétaires.
    """
    # Vérifier que l'utilisateur a le droit d'ajouter des frais
    if request.user.role not in ['admin', 'directeur', 'secretaire']:
        messages.error(request, "Accès refusé : vous n'êtes pas autorisé à ajouter des frais")
        return redirect('home:paiement_dashboard')
    
    if request.method == "POST":
        form = FraisForm(request.POST)
        if form.is_valid():
            frais = form.save()
            messages.success(
                request,
                f"Nouveaux frais ajoutés avec succès : {frais.description} - {frais.montant} XAF"
            )
            return redirect('home:paiement_dashboard')
    else:
        form = FraisForm()

    context = {
        'form': form,
        'title': "Ajouter des frais"
    }
    
    return render(request, 'gestion/paiements/ajouter_frais.html', context)



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
import json

@login_required
def notifications_liste(request):
    """Affiche la liste des notifications"""
    statut = request.GET.get('statut')
    
    # Filtrer les notifications
    notifications = request.user.notifications.all().order_by('-date_creation')
    if statut:
        notifications = notifications.filter(statut=statut)
    
    # Pagination
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    notifications_page = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications_page,
        'statut': statut
    }
    
    return render(request, 'gestion/notifications/liste.html', context)

@login_required
def notifications_archives(request):
    """Affiche les notifications archivées"""
    notifications = request.user.notifications.filter(archive=True).order_by('-date_creation')
    
    # Pagination
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    notifications_page = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications_page,
        'statut': 'ARCHIVE'
    }
    
    return render(request, 'gestion/notifications/liste.html', context)

@login_required
def marquer_notification_lue(request):
    """Marque une notification comme lue"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('id')
            
            if notification_id:
                notification = request.user.notifications.get(id=notification_id)
                notification.statut = 'LU'
                notification.save()
                
                return JsonResponse({'success': True})
            
            return JsonResponse({'success': False, 'error': 'ID de notification manquant'}, status=400)
        
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification non trouvée'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

@login_required
def marquer_tout_lu(request):
    """Marque toutes les notifications comme lues"""
    if request.method == 'POST':
        try:
            request.user.notifications.filter(statut='NON_LU').update(statut='LU')
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

@login_required
def archiver_notification(request):
    """Archive une notification"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('id')
            
            if notification_id:
                notification = request.user.notifications.get(id=notification_id)
                notification.archive = True
                notification.save()
                
                return JsonResponse({'success': True})
            
            return JsonResponse({'success': False, 'error': 'ID de notification manquant'}, status=400)
        
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification non trouvée'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

@login_required
def supprimer_notification(request):
    """Supprime une notification"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('id')
            
            if notification_id:
                request.user.notifications.filter(id=notification_id).delete()
                return JsonResponse({'success': True})
            
            return JsonResponse({'success': False, 'error': 'ID de notification manquant'}, status=400)
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)



# home/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
import json
from .models import Message

@login_required
def messagerie_liste(request):
    """Affiche la liste des messages de l'utilisateur"""
    # Déterminer le type de boîte (inbox ou sent)
    boite = request.GET.get('boite', 'inbox')
    recherche = request.GET.get('q', '')
    
    # Filtrer les messages selon la boîte
    if boite == 'sent':
        # Messages envoyés
        messages_list = request.user.messages_envoyes.filter(
            supprime_expediteur=False
        ).select_related('destinataire')
    else:
        # Messages reçus (inbox par défaut)
        boite = 'inbox'
        messages_list = request.user.messages_recus.filter(
            supprime_destinataire=False
        ).select_related('expediteur')
    
    # Appliquer la recherche si nécessaire
    if recherche:
        if boite == 'sent':
            messages_list = messages_list.filter(
                Q(destinataire__first_name__icontains=recherche) |
                Q(destinataire__last_name__icontains=recherche) |
                Q(objet__icontains=recherche) |
                Q(contenu__icontains=recherche)
            )
        else:
            messages_list = messages_list.filter(
                Q(expediteur__first_name__icontains=recherche) |
                Q(expediteur__last_name__icontains=recherche) |
                Q(objet__icontains=recherche) |
                Q(contenu__icontains=recherche)
            )
    
    # Trier par date
    messages_list = messages_list.order_by('-date_envoi')
    
    # Pagination
    paginator = Paginator(messages_list, 15)
    page_number = request.GET.get('page')
    messages_page = paginator.get_page(page_number)
    
    context = {
        'boite': boite,
        'messages': messages_page,
        'recherche': recherche,
        'total_non_lus': request.user.messages_recus.filter(lu=False, supprime_destinataire=False).count()
    }
    
    return render(request, 'gestion/messagerie/liste.html', context)

@login_required
def messagerie_detail(request, message_id):
    """Affiche un message spécifique"""
    message = get_object_or_404(
        Message,
        id=message_id,
        destinataire=request.user,
        supprime_destinataire=False
    )
    
    # Marquer comme lu si ce n'est pas déjà fait
    if not message.lu:
        message.marquer_comme_lu()
    
    context = {
        'message': message
    }
    
    return render(request, 'gestion/messagerie/detail.html', context)

@login_required
def messagerie_nouveau(request):
    """Affiche le formulaire pour un nouveau message"""
    destinataire_id = request.GET.get('destinataire')
    destinataire = None
    
    if destinataire_id:
        try:
            destinataire = Utilisateur.objects.get(id=destinataire_id)
        except Utilisateur.DoesNotExist:
            messages.error(request, _("Destinataire invalide."))
    
    context = {
        'destinataire': destinataire
    }
    
    return render(request, 'gestion/messagerie/nouveau.html', context)

@require_POST
@csrf_protect
@login_required
def messagerie_envoyer(request):
    """Traite l'envoi d'un nouveau message"""
    try:
        data = json.loads(request.body)
        destinataire_id = data.get('destinataire_id')
        objet = data.get('objet', '').strip()
        contenu = data.get('contenu', '').strip()
        
        # Validation des données
        if not destinataire_id or not objet or not contenu:
            return JsonResponse({
                'success': False,
                'error': _("Veuillez remplir tous les champs requis.")
            }, status=400)
        
        # Vérifier que le destinataire existe
        try:
            destinataire = Utilisateur.objects.get(id=destinataire_id)
        except Utilisateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': _("Destinataire invalide.")
            }, status=400)
        
        # Vérifier que l'expéditeur et le destinataire sont différents
        if request.user == destinataire:
            return JsonResponse({
                'success': False,
                'error': _("Vous ne pouvez pas vous envoyer de message à vous-même.")
            }, status=400)
        
        # Créer le message
        message = Message.objects.create(
            expediteur=request.user,
            destinataire=destinataire,
            objet=objet,
            contenu=contenu
        )
        
        # Créer une notification
        Notification.objects.create(
            utilisateur=destinataire,
            type_notification='MESSAGE',
            objet=_("Nouveau message"),
            message=f"{request.user.get_full_name()} vous a envoyé un message : {objet}",
            lien=f"/messagerie/{message.id}/",
            priorite=2
        )
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'redirect_url': f"/messagerie/{message.id}/"
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': _("Erreur lors de l'envoi du message.")
        }, status=500)

@login_required
def messagerie_repondre(request, message_id):
    """Affiche le formulaire de réponse à un message"""
    message_original = get_object_or_404(
        Message,
        id=message_id,
        destinataire=request.user
    )
    
    context = {
        'message_original': message_original,
        'destinataire': message_original.expediteur
    }
    
    return render(request, 'gestion/messagerie/repondre.html', context)

@require_POST
@csrf_protect
@login_required
def messagerie_marquer_lu(request):
    """Marque un message comme lu via AJAX"""
    try:
        data = json.loads(request.body)
        message_id = data.get('id')
        
        if not message_id:
            return JsonResponse({
                'success': False,
                'error': _("ID de message manquant.")
            }, status=400)
        
        message = get_object_or_404(
            Message,
            id=message_id,
            destinataire=request.user
        )
        
        message.marquer_comme_lu()
        
        return JsonResponse({
            'success': True,
            'total_non_lus': request.user.messages_recus.filter(lu=False, supprime_destinataire=False).count()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': _("Erreur lors du marquage du message comme lu.")
        }, status=500)

@require_POST
@csrf_protect
@login_required
def messagerie_supprimer(request):
    """Supprime un message"""
    try:
        data = json.loads(request.body)
        message_id = data.get('id')
        type_suppression = data.get('type', 'destinataire')  # 'destinataire' ou 'expediteur'
        
        if not message_id:
            return JsonResponse({
                'success': False,
                'error': _("ID de message manquant.")
            }, status=400)
        
        if type_suppression == 'expediteur':
            message = get_object_or_404(
                Message,
                id=message_id,
                expediteur=request.user
            )
            message.supprimer_pour_expediteur()
        else:
            message = get_object_or_404(
                Message,
                id=message_id,
                destinataire=request.user
            )
            message.supprimer_pour_destinataire()
        
        return JsonResponse({
            'success': True,
            'message': _("Message supprimé avec succès.")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': _("Erreur lors de la suppression du message.")
        }, status=500)

@login_required
def messagerie_api(request):
    """API pour les fonctionnalités en temps réel de la messagerie"""
    # Nombre de messages non lus
    non_lus = request.user.messages_recus.filter(lu=False, supprime_destinataire=False).count()
    
    # Derniers messages
    derniers_messages = request.user.messages_recus.filter(supprime_destinataire=False).select_related('expediteur')[:5]
    
    data = {
        'non_lus': non_lus,
        'derniers_messages': [{
            'id': msg.id,
            'expediteur': msg.expediteur.get_full_name(),
            'objet': msg.objet,
            'date': msg.date_envoi.isoformat(),
            'lu': msg.lu
        } for msg in derniers_messages]
    }
    
    return JsonResponse(data)




@login_required
def generer_recu(request, paiement_id):
    """
    Génère un reçu PDF pour un paiement
    """
    paiement = get_object_or_404(Paiement, id=paiement_id)
    
    # Vérifier que l'utilisateur a le droit de voir ce reçu
    if request.user.role == 'eleve' and paiement.eleve.utilisateur != request.user:
        messages.error(request, "Vous n'êtes pas autorisé à voir ce reçu.")
        return redirect('home:paiement_dashboard')
    elif request.user.role == 'parent':
        try:
            parent = request.user.parent_profile
            if paiement.eleve not in parent.enfants.all():
                messages.error(request, "Vous n'êtes pas autorisé à voir ce reçu.")
                return redirect('home:paiement_dashboard')
        except Parent.DoesNotExist:
            messages.error(request, "Profil parent introuvable.")
            return redirect('home:paiement_dashboard')
    
    # Créer le PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recu_{paiement.id}.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # En-tête
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "REÇU DE PAIEMENT")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"École: Capitole School")
    # ✅ CORRECTION : Utiliser 'date_paiement' au lieu de 'date'
    p.drawString(50, height - 100, f"Date: {paiement.date_paiement.strftime('%d/%m/%Y')}")
    p.drawString(50, height - 120, f"Référence: {paiement.numero_transaction or 'N/A'}")
    
    # Informations de l'élève
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 160, "Informations de l'élève:")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 180, f"Nom: {paiement.eleve.utilisateur.get_full_name()}")
    p.drawString(50, height - 200, f"Classe: {paiement.eleve.classe_actuelle.nom if paiement.eleve.classe_actuelle else 'Non assignée'}")
    p.drawString(50, height - 220, f"Niveau: {paiement.eleve.classe_actuelle.niveau.nom if paiement.eleve.classe_actuelle else 'Non assigné'}")
    
    # Détails du paiement
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 260, "Détails du paiement:")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 280, f"Frais: {paiement.frais.description}")
    p.drawString(50, height - 300, f"Montant total: {paiement.montant_total:,.0f} XAF")
    p.drawString(50, height - 320, f"Montant payé: {paiement.montant_paye:,.0f} XAF")
    p.drawString(50, height - 340, f"Différence rendue: {paiement.difference_rendue:,.0f} XAF")
    p.drawString(50, height - 360, f"Mode de paiement: {paiement.get_type_paiement_display()}")
    p.drawString(50, height - 380, f"Statut: {paiement.status}")
    
    if paiement.notes:
        p.drawString(50, height - 400, f"Commentaire: {paiement.notes}")
    
    # Pied de page
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 50, "Ce reçu est valable sans cachet ni signature.")
    p.drawString(50, 35, "Capitole School - Contact: contact@capitole-school.cd")
    
    p.showPage()
    p.save()
    
    return response


# home/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Eleve, Frais

@login_required
def api_eleves(request):
    """
    API pour récupérer la liste des élèves
    """
    eleves = Eleve.objects.select_related('utilisateur', 'classe_actuelle').all()
    
    data = []
    for eleve in eleves:
        data.append({
            'id': eleve.id,
            'nom': eleve.utilisateur.last_name,
            'prenom': eleve.utilisateur.first_name,
            'classe': str(eleve.classe_actuelle) if eleve.classe_actuelle else '-'
        })
    
    return JsonResponse({'success': True, 'data': data})

@login_required
def api_frais(request):
    """
    API pour récupérer la liste des frais
    """
    eleve_id = request.GET.get('eleve_id')
    frais_list = Frais.objects.select_related('niveau').all()
    
    # Filtrer par élève si spécifié
    if eleve_id:
        try:
            eleve = Eleve.objects.get(id=eleve_id)
            # Vous pouvez filtrer les frais selon le niveau de l'élève
            frais_list = frais_list.filter(niveau=eleve.classe_actuelle.niveau)
        except Eleve.DoesNotExist:
            frais_list = Frais.objects.none()
    
    data = []
    for frais in frais_list:
        data.append({
            'id': frais.id,
            'description': frais.description,
            'montant': str(frais.montant),
            'date_limite': frais.date_limite.strftime('%d/%m/%Y')
        })
    
    return JsonResponse({'success': True, 'data': data})

@login_required
def api_paiements(request):
    """
    API pour enregistrer un nouveau paiement
    """
    if request.method == 'POST':
        # Ici vous implémenteriez la logique d'enregistrement du paiement
        # Pour l'exemple, on retourne un succès
        return JsonResponse({
            'success': True, 
            'message': 'Paiement enregistré avec succès'
        })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

@login_required
def api_paiement_detail(request, paiement_id):
    """
    API pour récupérer les détails d'un paiement
    """
    try:
        paiement = Paiement.objects.select_related(
            'eleve__utilisateur', 
            'frais',
            'eleve__classe_actuelle'
        ).get(id=paiement_id)
        
        data = {
            'success': True,
            'eleve_nom': paiement.eleve.utilisateur.get_full_name(),
            'classe': str(paiement.eleve.classe_actuelle) if paiement.eleve.classe_actuelle else '-',
            'frais_description': paiement.frais.description,
            'frais_montant': f"{paiement.frais.montant:,.0f} XAF",
            'frais_date_limite': paiement.frais.date_limite.strftime('%d/%m/%Y'),
            'date': paiement.date_paiement.strftime('%d/%m/%Y'),
            'montant': f"{paiement.montant_paye:,.0f} XAF",
            'moyen': paiement.get_type_paiement_display(),
            'reference': paiement.numero_transaction or '-',
            'statut': paiement.status,
            'statut_couleur': 'success' if paiement.status == 'Payé' else 'warning' if paiement.status == 'Partiellement payé' else 'danger',
            'commentaire': paiement.notes or ''
        }
        
        return JsonResponse(data)
    except Paiement.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Paiement non trouvé'})
    
    
    