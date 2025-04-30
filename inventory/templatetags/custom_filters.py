from django import template

register = template.Library()

@register.filter
def absolute(value):
    """Returns the absolute value of a number."""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value

@register.filter
def get_item(dictionary, key):
    """Returns the value for the given key from the dictionary."""
    return dictionary.get(key) 