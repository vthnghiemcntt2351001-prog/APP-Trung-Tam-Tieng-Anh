from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Backend đăng nhập bảo mật cho hệ thống:
    1. Hỗ trợ đăng nhập linh hoạt bằng Username hoặc Email (không phân biệt hoa/thường).
    2. Bắt buộc kiểm tra mật khẩu an toàn bằng check_password(password).
    3. Tuân thủ tuyệt đối cơ chế phân quyền RBAC dựa trên nhóm của người dùng.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        clean_username = str(username).strip()

        # Tìm người dùng theo username hoặc email (không phân biệt hoa thường)
        user = User.objects.filter(
            Q(username__iexact=clean_username) | Q(email__iexact=clean_username)
        ).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

