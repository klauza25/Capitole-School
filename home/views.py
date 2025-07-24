# /views.py
from django.shortcuts import render, redirect
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
import logging

from .models import Eleve, Enseignement, Classe, Note, Presence
from .forms import RegisterForm, CycleForm, NiveauForm
from django.contrib import messages

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
    """
    Dashboard pour l'élève connecté.
    """
    if request.user.role != 'eleve':
        messages.error(request, "Accès refusé : vous n'êtes pas un élève.")
        return redirect('home:accueil')

    try:
        eleve = request.user.eleve
        print(f"✅ Profil élève trouvé : {eleve}")
    except Eleve.DoesNotExist:
        messages.error(
            request,
            "Profil élève non trouvé. Contactez l'administration."
        )
        print(f"❌ Aucun profil élève pour {request.user.username}")
        return redirect('admin:index')

    # Informations
    classe = eleve.classe_actuelle
    niveau = classe.niveau if classe else None

    # Notes (T1)
    notes = Note.objects.filter(
        eleve=eleve,
        trimestre='T1'
    ).select_related('matiere').order_by('matiere__nom')

    # Présences (7 derniers jours)
    date_debut = timezone.now().date() - timedelta(days=7)
    presences = Presence.objects.filter(
        eleve=eleve,
        date__gte=date_debut
    ).order_by('-date')

    # Statistiques
    total_presences = presences.count()
    present_count = presences.filter(present=True).count()
    taux_presence = round((present_count / total_presences * 100), 1) if total_presences > 0 else 0

    # Âge
    age = None
    if eleve.date_naissance:
        today = timezone.now().date()
        age = today.year - eleve.date_naissance.year
        if (today.month, today.day) < (eleve.date_naissance.month, eleve.date_naissance.day):
            age -= 1

    context = {
        'eleve': eleve,
        'utilisateur': request.user,
        'classe': classe,
        'niveau': niveau,
        'notes': notes,
        'presences': presences,
        'taux_presence': taux_presence,
        'age': age,
    }

    return render(request, 'gestion/dashboards/eleve.html', context)


@login_required
def enseignant_dashboard(request):
    """
    Dashboard pour enseignant.
    """
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
    }

    return render(request, 'gestion/dashboards/enseignant.html', context)


# Autres dashboards (exemples)
@login_required
def directeur_dashboard(request):
    return render(request, 'gestion/dashboards/directeur.html')

@login_required
def parent_dashboard(request):
    return render(request, 'gestion/dashboards/parent.html')

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
    return render(request, 'gestion/dashboards/confirmer_suppression.html', {'niveau': niveau})