from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


ROLE_ADMIN = "Admin"
ROLE_ACADEMIC = "Học vụ"
ROLE_FINANCE = "Tài chính"


def has_role(user, *roles):
    """Return whether an authenticated user belongs to any requested role."""
    if not user.is_authenticated:
        return False

    if user.is_superuser or user.groups.filter(name=ROLE_ADMIN).exists():
        return True

    return user.groups.filter(name__in=roles).exists()


def role_required(*roles):
    """Restrict a view to staff groups; always enforce authorization server-side."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_role(request.user, *roles):
                messages.error(request, "Bạn không có quyền thực hiện chức năng này.")
                return HttpResponseForbidden("Bạn không có quyền truy cập chức năng này.")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


admin_required = role_required(ROLE_ADMIN)
academic_required = role_required(ROLE_ACADEMIC)
finance_required = role_required(ROLE_FINANCE)
staff_required = role_required(ROLE_ACADEMIC, ROLE_FINANCE)


def is_admin_user(user):
    return has_role(user, ROLE_ADMIN)


def admin_context(request):
    """Expose presentation flags; these never replace view-level authorization."""
    user = request.user
    return {
        "is_admin": is_admin_user(user),
        "is_academic": has_role(user, ROLE_ACADEMIC),
        "is_finance": has_role(user, ROLE_FINANCE),
        "can_manage_academics": has_role(user, ROLE_ACADEMIC),
        "can_manage_finance": has_role(user, ROLE_FINANCE),
        "can_access_django_admin": user.is_active and user.is_staff,
        "role_label": (
            "Quản trị viên" if is_admin_user(user)
            else "Học vụ" if has_role(user, ROLE_ACADEMIC)
            else "Tài chính" if has_role(user, ROLE_FINANCE)
            else "Chưa phân quyền"
        ),
    }
