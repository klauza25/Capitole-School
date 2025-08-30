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
from .models import Eleve, Enseignement, Classe, Frais, Matiere, Note, Notification, Paiement, Parent, Presence, Utilisateur, Eleve, Classe
from .forms import EnseignantForm, ParentForm, RegisterForm, CycleForm, NiveauForm, ClasseForm, EleveForm
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

    context = {
        'eleve': eleve,
        'trimestres': trimestres,
        'taux_presence': taux_presence,
        'absences_count': absences_count,
        'presences': presences,
        'notes': notes,
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
def secretaire_dashboard(request):
    return render(request, 'gestion/dashboards/secretaire.html')

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

# views.py

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
        
        enfants_avec_notes.append({
            'enfant': enfant,
            'trimestre1_data': trimestres_data.get('T1', {
                'matieres': [],
                'moyenne': 0.0
            }),
            'moyenne_t1': trimestres_data.get('T1', {}).get('moyenne', 0.0),
            'moyenne_t2': trimestres_data.get('T2', {}).get('moyenne', 0.0),
            'moyenne_t3': trimestres_data.get('T3', {}).get('moyenne', 0.0),
        })

    context = {
        'parent': parent,
        'enfants_avec_notes': enfants_avec_notes,
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
    if request.user.role != 'secretaire':
        messages.error(request, "Accès refusé : vous n'êtes pas secrétaire.")
        return redirect('home:login')
    
     # Statistiques globales
    total_eleves = Eleve.objects.count()
    total_classes = Classe.objects.count()
    total_niveaux = Niveau.objects.count()
    
    # Taux de présence global
    total_presences = Presence.objects.count()
    presences_valides = Presence.objects.filter(present=True).count()
    taux_presence_global = round(presences_valides / total_presences * 100, 1) if total_presences > 0 else 100
    
    # CORRECTION ICI : Remplacer 'statut' par la logique appropriée
    # Option 1 : Si vous n'avez pas de champ statut, peut-être que vous souhaitez compter les élèves sans classe
# home/views.py
    eleves_en_attente = Eleve.objects.filter(statut='EN_ATTENTE').count()    
    # Élèves récemment inscrits
    eleves_recents = Eleve.objects.filter(
        utilisateur__date_joined__gte=date.today() - timedelta(days=30)
    ).order_by('-utilisateur__date_joined')[:5]
    
    
    # Élèves en attente d'inscription
    eleves_en_attente = Eleve.objects.filter(statut='EN_ATTENTE').count()
    
    # Statistiques financières
    annee_en_cours = date.today().year
    trimestre_en_cours = 'T1'  # À adapter selon la date
    
    # Total des frais scolaires pour l'année
    total_frais = Frais.objects.filter(
        Q(date_limite__year=annee_en_cours)
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    # Total des paiements validés
    total_paiements = Paiement.objects.filter(
        date__year=annee_en_cours
    ).aggregate(total=Sum('montant'))['total'] or 0
    
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
            ).aggregate(total=Sum('montant'))['total'] or 0
            
            total_paiements_classe = Paiement.objects.filter(
                eleve__in=eleves_classe,
                date__year=annee_en_cours
            ).aggregate(total=Sum('montant'))['total'] or 0
            
            taux_paiement_classe = round(total_paiements_classe / total_frais_classe * 100, 1) if total_frais_classe > 0 else 0
        
        classes_data.append({
            'classe': classe,
            'effectif': effectif,
            'taux_paiement': taux_paiement_classe
        })
    
    # Matières les plus enseignées
    matieres_data = []
    # CORRECTION ICI : Utiliser annotate pour compter les notes
    from django.db.models import Count
    
    # Option 1 : Si vous n'avez pas de related_name personnalisé dans le modèle Note
    matieres = Matiere.objects.annotate(note_count=Count('note'))
    
    # Option 2 : Si vous avez spécifié un related_name dans le modèle Note
    # matieres = Matiere.objects.annotate(note_count=Count('notes'))
    
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