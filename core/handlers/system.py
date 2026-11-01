from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from ..permissions import (
    ROLE_ACADEMIC,
    ROLE_ADMIN,
    ROLE_FINANCE,
    admin_context,
    admin_required,
)


@admin_required
def user_list(request):
    """List system users with search, role filters, and quick stats."""
    # Ensure standard staff role groups exist in the database
    for role_name in (ROLE_ADMIN, ROLE_ACADEMIC, ROLE_FINANCE):
        Group.objects.get_or_create(name=role_name)

    query = request.GET.get("q", "").strip()
    role_filter = request.GET.get("role", "").strip()
    status_filter = request.GET.get("status", "").strip()

    users_qs = User.objects.prefetch_related("groups").order_by("-date_joined")

    if query:
        users_qs = users_qs.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )

    if role_filter:
        if role_filter == "none":
            users_qs = users_qs.filter(groups__isnull=True, is_superuser=False)
        elif role_filter == ROLE_ADMIN:
            users_qs = users_qs.filter(Q(groups__name=ROLE_ADMIN) | Q(is_superuser=True)).distinct()
        else:
            users_qs = users_qs.filter(groups__name=role_filter).distinct()

    if status_filter == "active":
        users_qs = users_qs.filter(is_active=True)
    elif status_filter == "inactive":
        users_qs = users_qs.filter(is_active=False)

    # Compute high-level metrics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    admin_count = User.objects.filter(Q(groups__name=ROLE_ADMIN) | Q(is_superuser=True)).distinct().count()
    academic_count = User.objects.filter(groups__name=ROLE_ACADEMIC).distinct().count()
    finance_count = User.objects.filter(groups__name=ROLE_FINANCE).distinct().count()

    paginator = Paginator(users_qs, 15)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "core/system/users/list.html",
        {
            "users": page_obj,
            "page_obj": page_obj,
            "query": query,
            "role_filter": role_filter,
            "status_filter": status_filter,
            "total_users": total_users,
            "active_users": active_users,
            "admin_count": admin_count,
            "academic_count": academic_count,
            "finance_count": finance_count,
            "available_roles": [ROLE_ADMIN, ROLE_ACADEMIC, ROLE_FINANCE],
            **admin_context(request),
        },
    )


@admin_required
def user_add(request):
    """Create a new system user account."""
    if request.method != "POST":
        return redirect("user_list")

    username = request.POST.get("username", "").strip()
    password = request.POST.get("password", "").strip()
    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip()
    role_name = request.POST.get("role", "").strip()
    is_active = request.POST.get("is_active") == "on"

    if not username or not password:
        messages.error(request, "Tên đăng nhập và mật khẩu không được để trống.")
        return redirect("user_list")

    if User.objects.filter(username=username).exists():
        messages.error(request, f"Tên đăng nhập '{username}' đã tồn tại trong hệ thống.")
        return redirect("user_list")

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
    )

    if role_name:
        group, _ = Group.objects.get_or_create(name=role_name)
        user.groups.add(group)
        if role_name == ROLE_ADMIN:
            user.is_staff = True
            user.save(update_fields=["is_staff"])

    messages.success(request, f"Đã tạo tài khoản '{username}' thành công.")
    return redirect("user_list")


@admin_required
def user_edit(request, user_id):
    """Edit user details, roles, and optionally reset password."""
    user = get_object_or_404(User, pk=user_id)
    if request.method != "POST":
        return redirect("user_list")

    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    email = request.POST.get("email", "").strip()
    role_name = request.POST.get("role", "").strip()
    new_password = request.POST.get("new_password", "").strip()
    is_active = request.POST.get("is_active") == "on"

    user.first_name = first_name
    user.last_name = last_name
    user.email = email

    # Prevent locking out yourself
    if request.user.id == user.id and not is_active:
        messages.warning(request, "Bạn không thể tự khóa tài khoản đang đăng nhập của chính mình.")
    else:
        user.is_active = is_active

    if new_password:
        if len(new_password) < 6:
            messages.error(request, "Mật khẩu mới phải có ít nhất 6 ký tự.")
            return redirect("user_list")
        user.set_password(new_password)
        messages.info(request, f"Đã cập nhật mật khẩu mới cho tài khoản '{user.username}'.")

    # Update role / group
    user.groups.clear()
    if role_name:
        group, _ = Group.objects.get_or_create(name=role_name)
        user.groups.add(group)
        if role_name == ROLE_ADMIN:
            user.is_staff = True
        else:
            if not user.is_superuser:
                user.is_staff = False
    else:
        if not user.is_superuser:
            user.is_staff = False

    user.save()
    messages.success(request, f"Đã cập nhật thông tin tài khoản '{user.username}' thành công.")
    return redirect("user_list")


@admin_required
def user_toggle_status(request, user_id):
    """Toggle active status (lock/unlock) of a user account."""
    if request.method != "POST":
        return redirect("user_list")

    user = get_object_or_404(User, pk=user_id)

    if request.user.id == user.id:
        messages.error(request, "Bạn không thể khóa tài khoản của chính mình.")
        return redirect("user_list")

    if user.is_superuser:
        messages.error(request, "Không thể khóa tài khoản Superuser tối cao.")
        return redirect("user_list")

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    status_str = "mở khóa" if user.is_active else "tạm khóa"
    messages.success(request, f"Đã {status_str} tài khoản '{user.username}'.")
    return redirect("user_list")


@admin_required
def user_delete(request, user_id):
    """Delete a user account."""
    if request.method != "POST":
        return redirect("user_list")

    user = get_object_or_404(User, pk=user_id)

    if request.user.id == user.id:
        messages.error(request, "Bạn không thể xóa tài khoản đang đăng nhập của chính mình.")
        return redirect("user_list")

    if user.is_superuser:
        messages.error(request, "Không thể xóa tài khoản Superuser của hệ thống.")
        return redirect("user_list")

    username = user.username
    user.delete()
    messages.success(request, f"Đã xóa tài khoản '{username}' khỏi hệ thống.")
    return redirect("user_list")


@admin_required
def role_list(request):
    """Display system roles, assigned members, and detailed RBAC matrix."""
    for role_name in (ROLE_ADMIN, ROLE_ACADEMIC, ROLE_FINANCE):
        Group.objects.get_or_create(name=role_name)

    roles_data = [
        {
            "name": ROLE_ADMIN,
            "badge_class": "badge-role-admin",
            "icon": "🛡️",
            "title": "Quản trị viên (Administrator)",
            "description": "Toàn quyền quản trị hệ thống, quản lý tài khoản người dùng, phân quyền truy cập, duyệt chuyển lớp khác khóa học và cấu hình quy chế đánh giá.",
            "users": User.objects.filter(Q(groups__name=ROLE_ADMIN) | Q(is_superuser=True)).distinct().order_by("username"),
            "features": [
                "Quản lý toàn bộ tài khoản người dùng và phân quyền",
                "Phê duyệt yêu cầu chuyển lớp khác khóa học",
                "Cấu hình chính sách và quy chế đánh giá học tập",
                "Xem toàn bộ báo cáo đào tạo, điểm số và tài chính",
                "Truy cập các tính năng quản trị cấp cao",
            ],
        },
        {
            "name": ROLE_ACADEMIC,
            "badge_class": "badge-role-academic",
            "icon": "🎓",
            "title": "Cán bộ Học vụ (Academic Staff)",
            "description": "Chịu trách nhiệm quản lý hồ sơ học viên, giáo viên, danh mục khóa học, xếp lớp học, ghi danh, điểm danh chuyên cần, nhập điểm và cấp phát chứng chỉ.",
            "users": User.objects.filter(groups__name=ROLE_ACADEMIC).distinct().order_by("username"),
            "features": [
                "Thêm mới, sửa, quản lý hồ sơ học viên và giáo viên",
                "Quản lý danh sách khóa học và lớp học",
                "Ghi danh học viên và đề xuất chuyển lớp",
                "Tạo lịch buổi học và thực hiện điểm danh chuyên cần",
                "Tổ chức kỳ đánh giá, nhập điểm số học viên",
                "Cấp chứng chỉ và lưu trữ chứng thực trên Blockchain",
            ],
        },
        {
            "name": ROLE_FINANCE,
            "badge_class": "badge-role-finance",
            "icon": "💳",
            "title": "Cán bộ Tài chính (Finance Staff)",
            "description": "Chịu trách nhiệm quản lý học phí, tạo khoản thu, lập phiếu thu thanh toán, theo dõi công nợ học viên và xuất biên lai thanh toán học phí.",
            "users": User.objects.filter(groups__name=ROLE_FINANCE).distinct().order_by("username"),
            "features": [
                "Lập kế hoạch thu học phí theo từng học viên và lớp học",
                "Thu học phí, ghi nhận thanh toán từng đợt",
                "In biên lai thu tiền học phí chính thức",
                "Theo dõi tình trạng công nợ và quá hạn học phí",
                "Xuất danh sách và báo cáo học phí ra định dạng Excel",
            ],
        },
    ]

    # Permission Matrix Definitions
    matrix = [
        {"module": "Bảng điều khiển (Dashboard)", "admin": True, "academic": True, "finance": True},
        {"module": "Quản lý Hồ sơ Học viên", "admin": True, "academic": True, "finance": False},
        {"module": "Quản lý Giáo viên & Khóa học", "admin": True, "academic": True, "finance": False},
        {"module": "Quản lý Lớp học & Ghi danh", "admin": True, "academic": True, "finance": False},
        {"module": "Buổi học & Điểm danh chuyên cần", "admin": True, "academic": True, "finance": False},
        {"module": "Kỳ đánh giá & Nhập bảng điểm", "admin": True, "academic": True, "finance": False},
        {"module": "Cấp phát Chứng chỉ (Blockchain)", "admin": True, "academic": True, "finance": False},
        {"module": "Quản lý Học phí & Thu tiền", "admin": True, "academic": False, "finance": True},
        {"module": "In biên lai & Xuất báo cáo tài chính", "admin": True, "academic": False, "finance": True},
        {"module": "Đề xuất chuyển lớp học viên", "admin": True, "academic": True, "finance": False},
        {"module": "Phê duyệt chuyển lớp (Admin)", "admin": True, "academic": False, "finance": False},
        {"module": "Cấu hình Quy chế đánh giá", "admin": True, "academic": False, "finance": False},
        {"module": "Quản lý Tài khoản & Phân quyền", "admin": True, "academic": False, "finance": False},
    ]

    return render(
        request,
        "core/system/roles/list.html",
        {
            "roles_data": roles_data,
            "matrix": matrix,
            **admin_context(request),
        },
    )
