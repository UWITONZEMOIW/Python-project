from django import template
register = template.Library()

@register.filter(name='abs_val')
def abs_val(value):
    try:
        return abs(float(value))  # ensures it works even if value is string
    except (TypeError, ValueError):
        return 0  # fallback for unexpected input
