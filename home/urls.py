# home/urls.py

from django.urls import path
from home import views

app_name = 'home'

urlpatterns = [
    # Accueil et authentification
    path('', views.accueil, name='accueil'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/directeur/', views.directeur_dashboard, name='directeur_dashboard'),
    path('dashboard/enseignant/', views.enseignant_dashboard, name='enseignant_dashboard'),
    path('dashboard/eleve/', views.eleve_dashboard, name='eleve_dashboard'),
    path('dashboard/parent/', views.parent_dashboard, name='parent_dashboard'),
    path('dashboard/secretaire/', views.secretaire_dashboard, name='secretaire_dashboard'),
    path('dashboard/surveillant/', views.surveillant_dashboard, name='surveillant_dashboard'),
    # === CYCLES ===
    path('cycles/', views.liste_cycles, name='liste_cycles'),
    path('cycles/ajouter/', views.ajouter_cycle, name='ajouter_cycle'),
    path('cycles/<int:pk>/modifier/', views.modifier_cycle, name='modifier_cycle'),
    path('cycles/<int:pk>/supprimer/', views.supprimer_cycle, name='supprimer_cycle'),

    # === NIVEAUX ===
    path('niveaux/', views.liste_niveaux, name='liste_niveaux'),
    path('niveaux/ajouter/', views.ajouter_niveau, name='ajouter_niveau'),
    path('niveaux/<int:pk>/modifier/', views.modifier_niveau, name='modifier_niveau'),
    path('niveaux/<int:pk>/supprimer/', views.supprimer_niveau, name='supprimer_niveau'),
]