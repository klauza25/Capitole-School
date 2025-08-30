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
    path('parent/', views.parent_dashboard, name='parent_dashboard'),
    path('parent/', views.ajouter_parent, name='ajouter_parent'),
    path('parents/<int:pk>/modifier/', views.modifier_parent, name='modifier_parent'),
    path('parents/<int:pk>/supprimer_parent/', views.supprimer_parent, name='supprimer_parent'),
    
    
   
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
    
    path('classes/ajouter/', views.ajouter_classe, name='ajouter_classe'),
    path('classes/<int:pk>/modifier/', views.modifier_classe, name='modifier_classe'),
    path('classes/', views.liste_classes, name='liste_classes'),
    path('classes/<int:pk>/supprimer/', views.supprimer_classe, name='supprimer_classe'),
    
    path('cycles/', views.liste_cycles, name='liste_cycles'),
    path('niveaux/', views.liste_niveaux, name='liste_niveaux'),
    path('classes/', views.liste_classes, name='liste_classes'),
    path('eleves/', views.liste_eleves, name='liste_eleves'),
    path('enseignants/', views.liste_enseignants, name='liste_enseignants'),
    path('parents/', views.liste_parents, name='liste_parents'),
    # === ÉLÈVES ===
    path('eleves/', views.liste_eleves, name='liste_eleves'),
    path('eleves/ajouter/', views.ajouter_eleve, name='ajouter_eleve'),
    path('eleves/<int:pk>/modifier/', views.modifier_eleve, name='modifier_eleve'),
    path('eleves/<int:pk>/supprimer/', views.supprimer_eleve, name='supprimer_eleve'),
    path('enseignants/', views.liste_enseignants, name='liste_enseignants'),
    path('enseignants/ajouter/', views.ajouter_enseignant, name='ajouter_enseignant'),
    path('enseignants/<int:pk>/modifier/', views.modifier_enseignant, name='modifier_enseignant'),
    path('enseignants/<int:pk>/supprimer/', views.supprimer_enseignant, name='supprimer_enseignant'),
    
    # notifications
    path('notifications/', views.notifications_liste, name='notifications'),
    path('notifications/<int:pk>/lu/', views.notification_marquer_comme_lue, name='notification_marquer_comme_lue'),
    path('notifications/tout-lu/', views.notifications_marquer_tout_comme_lu, name='notifications_marquer_tout_comme_lu'),
    path('notifications/<int:pk>/supprimer/', views.notifications_supprimer, name='notifications_supprimer'),
    path('notifications/tout-supprimer/', views.notifications_supprimer_tout, name='notifications_supprimer_tout'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
]