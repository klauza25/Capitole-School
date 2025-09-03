from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    """Soustraction de deux nombres"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplication de deux nombres"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0