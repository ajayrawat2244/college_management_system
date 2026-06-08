# apps/web/templatetags/web_tags.py
"""
Custom template tags and filters for the web layer.

Usage in templates:
    {% load web_tags %}
    {% active_if 'dashboard' %}
    {% has_role 'college_admin' %}
    {{ value|currency }}
"""
from django import template
from django.utils.html import format_html

from apps.platforms.permissions import ROLE_COLLEGE_ADMIN, ROLE_STUDENT, ROLE_TEACHER

register = template.Library()


# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------

@register.simple_tag(takes_context=True)
def active_if(context, *url_names):
    """
    Return 'active' CSS class if the current URL name matches any of the given names.

    Usage: <a class="nav-link {% active_if 'dashboard' 'home' %}" href="...">
    """
    request = context.get("request")
    if not request:
        return ""
    current = getattr(request.resolver_match, "url_name", "")
    return "active" if current in url_names else ""


@register.simple_tag(takes_context=True)
def active_if_namespace(context, namespace):
    """
    Return 'active' if the current URL's app namespace matches.

    Usage: <li class="{% active_if_namespace 'students' %}">
    """
    request = context.get("request")
    if not request or not request.resolver_match:
        return ""
    namespaces = request.resolver_match.namespaces
    return "active" if namespace in namespaces else ""


# ---------------------------------------------------------------------------
# Role / permission helpers
# ---------------------------------------------------------------------------

@register.simple_tag(takes_context=True)
def has_role(context, *role_codes):
    """
    Return True if the current user has any of the given role codes within
    the resolved college tenant.

    Usage: {% has_role 'college_admin' as is_admin %}
           {% if is_admin %}...{% endif %}
    """
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return False
    if request.user.is_superuser:
        return True
    college = getattr(request, "college", None)
    if not college:
        return False
    return request.user.user_roles.filter(
        role__code__in=role_codes,
        college=college,
        status="active",
    ).exists()


@register.inclusion_tag("web/partials/_role_badge.html", takes_context=True)
def role_badge(context):
    """Render a small badge showing the user's current role."""
    return {
        "user_role_code": context.get("user_role_code"),
    }


# ---------------------------------------------------------------------------
# Formatting filters
# ---------------------------------------------------------------------------

@register.filter
def currency(value, symbol="₹"):
    """Format a number as Indian currency: ₹1,23,456.78"""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return f"{symbol}—"
    # Indian numbering: last 3 digits, then groups of 2
    s = f"{value:,.2f}"
    return f"{symbol}{s}"


@register.filter
def initials(value):
    """Return up to 2 initials from a full name string."""
    if not value:
        return "?"
    parts = str(value).split()
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()
