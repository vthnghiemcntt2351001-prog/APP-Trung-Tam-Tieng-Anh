from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from core.permissions import ROLE_ACADEMIC, ROLE_ADMIN, ROLE_FINANCE


class SystemManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_group, _ = Group.objects.get_or_create(name=ROLE_ADMIN)
        self.academic_group, _ = Group.objects.get_or_create(name=ROLE_ACADEMIC)
        self.finance_group, _ = Group.objects.get_or_create(name=ROLE_FINANCE)

        self.admin_user = User.objects.create_superuser(
            username="system_admin",
            password="adminpassword123",
            email="admin@englishcenter.edu.vn",
        )
        self.admin_user.groups.add(self.admin_group)

        self.academic_user = User.objects.create_user(
            username="staff_academic",
            password="staffpassword123",
            email="academic@englishcenter.edu.vn",
        )
        self.academic_user.groups.add(self.academic_group)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_academic_user_forbidden(self):
        self.client.login(username="staff_academic", password="staffpassword123")
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, 403)

    def test_admin_user_can_access_user_list(self):
        self.client.login(username="system_admin", password="adminpassword123")
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Quản lý tài khoản người dùng")
        self.assertContains(response, "system_admin")
        self.assertContains(response, "staff_academic")

    def test_admin_can_add_user(self):
        self.client.login(username="system_admin", password="adminpassword123")
        response = self.client.post(
            reverse("user_add"),
            {
                "username": "new_finance_user",
                "password": "strongpassword123",
                "first_name": "Linh",
                "last_name": "Tran",
                "email": "linh@englishcenter.edu.vn",
                "role": ROLE_FINANCE,
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username="new_finance_user")
        self.assertEqual(created_user.first_name, "Linh")
        self.assertEqual(created_user.last_name, "Tran")
        self.assertTrue(created_user.groups.filter(name=ROLE_FINANCE).exists())
        self.assertTrue(created_user.is_active)

    def test_admin_can_edit_user(self):
        self.client.login(username="system_admin", password="adminpassword123")
        response = self.client.post(
            reverse("user_edit", kwargs={"user_id": self.academic_user.id}),
            {
                "first_name": "Van",
                "last_name": "Nguyen",
                "email": "vannguyen@englishcenter.edu.vn",
                "role": ROLE_ADMIN,
                "new_password": "newsecretpass123",
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.academic_user.refresh_from_db()
        self.assertEqual(self.academic_user.first_name, "Van")
        self.assertTrue(self.academic_user.groups.filter(name=ROLE_ADMIN).exists())
        self.assertTrue(self.academic_user.check_password("newsecretpass123"))

    def test_admin_cannot_deactivate_self(self):
        self.client.login(username="system_admin", password="adminpassword123")
        response = self.client.post(
            reverse("user_toggle_status", kwargs={"user_id": self.admin_user.id})
        )
        self.assertEqual(response.status_code, 302)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_admin_can_toggle_other_user_status(self):
        self.client.login(username="system_admin", password="adminpassword123")
        response = self.client.post(
            reverse("user_toggle_status", kwargs={"user_id": self.academic_user.id})
        )
        self.assertEqual(response.status_code, 302)
        self.academic_user.refresh_from_db()
        self.assertFalse(self.academic_user.is_active)

    def test_admin_can_access_role_list(self):
        self.client.login(username="system_admin", password="adminpassword123")
        response = self.client.get(reverse("role_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Phân quyền & Vai trò hệ thống (RBAC)")
        self.assertContains(response, "Quản trị viên (Administrator)")
        self.assertContains(response, "Cán bộ Học vụ (Academic Staff)")
        self.assertContains(response, "Cán bộ Tài chính (Finance Staff)")
        self.assertContains(response, "Bảng ma trận phân quyền chi tiết các phân hệ")
