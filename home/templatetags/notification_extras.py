# home/templatetags/notification_extras.py
from django import template


register = template.Library()

@register.filter
def has_unread_notifications(user):
    """Vérifie si l'utilisateur a des notifications non lues"""
    return user.notifications.filter(statut='NON_LU').exists()

register = template.Library()

@register.filter
def has_unread_notifications(user):
    """Vérifie si l'utilisateur a des notifications non lues"""
    return user.notifications.filter(statut='NON_LU').exists()