# home/templatetags/form_extras.py
from django import template

register = template.Library()

@register.filter
def get_field_label(form, field_name):
    """
    Retourne le label d'un champ du formulaire à partir de son nom.
    Ex: {{ form|get_field_label:"first_name" }} → "Prénom"
    """
    try:
        return form.fields[field_name].label
    except KeyError:
        return field_name.replace('_', ' ').title()