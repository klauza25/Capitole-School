# home/templatetags/text_filters.py
from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Remplace toutes les occurrences d'une chaîne par une autre.
    Usage: {{ value|replace:"old,new" }}
    """
    if not isinstance(value, str):
        return value
    
    # L'argument doit être au format "ancien,nouveau"
    try:
        old, new = arg.split(',', 1)
        return value.replace(old, new)
    except ValueError:
        return value

@register.filter
def slugify_status(value):
    """
    Convertit un statut en format slug (minuscules, tirets)
    """
    if not isinstance(value, str):
        return value
    
    return value.lower().replace(' ', '-')