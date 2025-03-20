from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def add_class(value, arg):
    """Añade una clase CSS al valor del campo."""
    return value.as_widget(attrs={'class': arg})
