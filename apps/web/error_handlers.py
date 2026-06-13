# apps/web/error_handlers.py
"""
Custom error view functions wired up in root urls.py as handler403/404/500.
These render the project's own styled error templates instead of Django defaults.
"""
from django.shortcuts import render


def handler403(request, exception=None):
    return render(request, "403.html", status=403)


def handler404(request, exception=None):
    return render(request, "404.html", status=404)


def handler500(request):
    return render(request, "500.html", status=500)
