from .permissions import admin_context


def navigation(request):
    """Expose the same role-aware navigation flags on every rendered page."""
    return admin_context(request)
