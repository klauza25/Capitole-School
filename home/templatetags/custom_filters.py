from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def naturaltime(value):
    """Convertit une date en format 'il y a X temps'"""
    if not value:
        return ''
    
    now = timezone.now()
    diff = now - value
    
    if diff < timedelta(minutes=1):
        return "à l'instant"
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"il y a {days} jour{'s' if days > 1 else ''}"
    else:
        return value.strftime("%d/%m/%Y")