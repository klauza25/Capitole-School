# home/templatetags/note_extras.py
from django import template

register = template.Library()

@register.filter
def filter(queryset, **kwargs):
    """
    Filtre un QuerySet dans un template.
    Usage : {{ notes|filter:type_evaluation="DS1" }}
    """
    return queryset.filter(**kwargs)