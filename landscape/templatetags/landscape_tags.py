from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def sort_url(context, field):
    """Build a URL that sorts by `field`, toggling asc/desc if already sorted by it."""
    params = context['request'].GET.copy()
    if params.get('sort') == field:
        params['order'] = 'desc' if params.get('order') == 'asc' else 'asc'
    else:
        params['sort'] = field
        params['order'] = 'asc'
    return '?' + params.urlencode()
