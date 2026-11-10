from django import template

register = template.Library()


@register.filter
def get_item(value, key):
    return (value or {}).get(key, [])
