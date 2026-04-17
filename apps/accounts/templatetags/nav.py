"""Template tags for sidebar navigation — active-link highlighting."""
from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active(context, *url_names: str) -> str:
    """Return 'active' if the current request path matches any given URL name.

    Matches exact URL for dashboard-like roots, or startswith for section URLs.
    Usage: {% nav_active 'patients:list' 'patients:new' as is_active %}
    """
    request = context.get("request")
    if request is None:
        return ""
    current = request.path
    for name in url_names:
        try:
            target = reverse(name)
        except NoReverseMatch:
            continue
        if target == "/":
            if current == "/":
                return "active"
        elif current.startswith(target):
            return "active"
    return ""
