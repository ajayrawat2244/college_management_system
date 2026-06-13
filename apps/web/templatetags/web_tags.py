# apps/web/templatetags/web_tags.py
"""
Custom template tags and filters for the web layer.

Usage in templates:
    {% load web_tags %}
    {% active_if 'dashboard' %}
    {% has_role 'college_admin' as is_admin %}{% if is_admin %}...{% endif %}
    {{ value|currency }}
    {{ form|form_field:'email' }}
"""
from django import template
from django.utils.html import format_html, escape
from django.utils.safestring import mark_safe

register = template.Library()


# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------

@register.simple_tag(takes_context=True)
def active_if(context, *url_names):
    """
    Return 'active' CSS class if the current URL name matches any given name.

    Usage: <a class="nav-link {% active_if 'dashboard' 'home' %}" href="...">
    """
    request = context.get("request")
    if not request:
        return ""
    current = getattr(request.resolver_match, "url_name", "")
    return "active" if current in url_names else ""


@register.simple_tag(takes_context=True)
def active_if_namespace(context, namespace):
    """Return 'active' if the current URL app namespace matches."""
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
    Return True if the current user has any of the given role codes.

    Usage:
        {% has_role 'college_admin' as is_admin %}
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
    return {"user_role_code": context.get("user_role_code")}


# ---------------------------------------------------------------------------
# Form helpers — needed by templates that iterate field names
# ---------------------------------------------------------------------------

@register.filter(name="form_field")
def form_field(form, field_name):
    """
    Return a bound field by name from a form.

    Usage: {% with field=form|form_field:'email' %}{{ field }}{% endwith %}
    """
    try:
        return form[field_name]
    except KeyError:
        return None


@register.filter(name="getitem")
def getitem(obj, key):
    """
    Return obj[key] — works for dicts, forms, lists.

    Usage: {{ form|getitem:'email' }}
    """
    try:
        return obj[key]
    except (KeyError, IndexError, TypeError):
        return None


@register.filter(name="split")
def split_filter(value, delimiter=","):
    """
    Split a string by delimiter.

    Usage: {% for x in "a,b,c"|split:"," %}
    """
    if not value:
        return []
    return [v.strip() for v in str(value).split(delimiter)]


# ---------------------------------------------------------------------------
# Formatting filters
# ---------------------------------------------------------------------------

@register.filter
def currency(value, symbol="₹"):
    """Format a number as Indian Rupee: ₹1,23,456.78"""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return f"{symbol}—"
    # Basic comma formatting; full Indian numbering is locale-specific
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


@register.filter
def sub_status_class(status):
    """Map subscription status to CSS badge class."""
    return {
        "trial": "warning",
        "active": "success",
        "past_due": "danger",
        "cancelled": "muted",
        "expired": "danger",
    }.get(status, "muted")


@register.filter
def college_status_class(status):
    """Map college status to CSS badge class."""
    return {
        "active": "success",
        "inactive": "muted",
        "suspended": "danger",
        "archived": "muted",
    }.get(status, "muted")


@register.filter
def user_status_class(status):
    """Map user status to CSS badge class."""
    return {
        "active": "success",
        "inactive": "muted",
        "blocked": "danger",
        "archived": "muted",
    }.get(status, "muted")
