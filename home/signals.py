# home/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Note, Notification

User = get_user_model()

@receiver(post_save, sender=Note)
def creer_notification_nouvelle_note(sender, instance, created, **kwargs):
    """Crée une notification quand une nouvelle note est ajoutée"""
    if not created:
        return
    
    # Récupérer l'élève et ses parents
    eleve = instance.eleve
    parents = eleve.parents.all()
    
    # Créer une notification pour l'élève
    Notification.objects.create(
        utilisateur=eleve.utilisateur,
        type_notification='NOTE',
        objet=f"Nouvelle note en {instance.matiere.nom}",
        message=render_to_string('gestion/notifications/nouvelle_note_eleve.txt', {
            'note': instance,
            'eleve': eleve
        }),
        lien=f"/dashboard/eleve/",
        priorite=2
    )
    
    # Créer des notifications pour chaque parent
    for parent in parents:
        Notification.objects.create(
            utilisateur=parent.utilisateur,
            type_notification='NOTE',
            objet=f"Nouvelle note pour {eleve.utilisateur.get_full_name()} en {instance.matiere.nom}",
            message=render_to_string('gestion/notifications/nouvelle_note_parent.txt', {
                'note': instance,
                'eleve': eleve,
                'parent': parent
            }),
            lien=f"/dashboard/parent/",
            priorite=1
        )
    
    # Optionnel : Envoyer un email aux parents
    if settings.SEND_EMAIL_NOTIFICATIONS:
        for parent in parents:
            subject = f"Nouvelle note pour {eleve.utilisateur.get_full_name()}"
            message = render_to_string('gestion/emails/nouvelle_note.html', {
                'note': instance,
                'eleve': eleve,
                'parent': parent
            })
            plain_message = strip_tags(message)
            from_email = settings.DEFAULT_FROM_EMAIL
            to = parent.utilisateur.email
            
            send_mail(
                subject, 
                plain_message, 
                from_email, 
                [to], 
                html_message=message
            )