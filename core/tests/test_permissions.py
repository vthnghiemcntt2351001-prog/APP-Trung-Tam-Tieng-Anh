from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from core.permissions import ROLE_ADMIN, ROLE_ACADEMIC, ROLE_FINANCE


User = get_user_model()


class RBACPermissionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Tạo 3 nhóm vai trò chuẩn
        self.group_admin = Group.objects.create(name=ROLE_ADMIN)
        self.group_academic = Group.objects.create(name=ROLE_ACADEMIC)
        self.group_finance = Group.objects.create(name=ROLE_FINANCE)

        # 1. User Học Vụ
        self.academic_user = User.objects.create_user(
            username="user_hocvu",
            password="password123",
            email="hocvu@test.com",
            is_staff=True,
        )
        self.academic_user.groups.add(self.group_academic)

        # 2. User Tài Chính
        self.finance_user = User.objects.create_user(
            username="user_taichinh",
            password="password123",
            email="taichinh@test.com",
            is_staff=True,
        )
        self.finance_user.groups.add(self.group_finance)

        # 3. Superuser / Admin
        self.admin_user = User.objects.create_superuser(
            username="user_admin",
            password="password123",
            email="admin@test.com",
        )

    def test_anonymous_user_redirected_to_login(self):
        """Người dùng chưa đăng nhập luôn bị chuyển hướng về trang login."""
        endpoints = ["/students/", "/tuitions/", "/classes/", "/courses/"]
        for url in endpoints:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 302, f"URL {url} should redirect anonymous user")
            self.assertIn("/accounts/login/", res["Location"])

    def test_academic_role_permissions(self):
        """User Học Vụ: Được xem học viên, lớp học; bị chặn 403 khi vào menu Học phí."""
        self.client.force_login(self.academic_user)

        # Quyền được phép
        res_students = self.client.get("/students/", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_students.status_code, 200)

        res_classes = self.client.get("/classes/", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_classes.status_code, 200)

        # Bị chặn 403 trên phân hệ Tài chính
        res_tuition = self.client.get("/tuitions/", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_tuition.status_code, 403)

    def test_finance_role_permissions(self):
        """User Tài Chính: Được xem và thu học phí; bị chặn 403 khi thao tác đào tạo."""
        self.client.force_login(self.finance_user)

        # Quyền được phép
        res_tuition = self.client.get("/tuitions/", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_tuition.status_code, 200)

        # Bị chặn 403 khi thêm học viên hoặc tạo lớp học
        res_student_add = self.client.get("/students/add/", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_student_add.status_code, 403)

        res_class_add = self.client.get("/classes/add/", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_class_add.status_code, 403)

    def test_admin_full_access(self):
        """Superuser / Admin: Toàn quyền truy cập mọi phân hệ của trung tâm."""
        self.client.force_login(self.admin_user)

        endpoints = [
            "/",
            "/students/",
            "/classes/",
            "/courses/",
            "/teachers/",
            "/tuitions/",
            "/certificates/",
            "/class-transfers/",
        ]
        for url in endpoints:
            res = self.client.get(url, HTTP_HOST="127.0.0.1")
            self.assertEqual(res.status_code, 200, f"Admin should have access to {url}")

    def test_authentication_security(self):
        """Xác thực bảo mật: Đúng mật khẩu thành công, sai mật khẩu luôn bị từ chối."""
        from django.contrib.auth import authenticate

        # 1. Đăng nhập đúng username + password
        user = authenticate(username="user_admin", password="password123")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "user_admin")

        # 2. Đăng nhập đúng email + password
        user_by_email = authenticate(username="admin@test.com", password="password123")
        self.assertIsNotNone(user_by_email)
        self.assertEqual(user_by_email.username, "user_admin")

        # 3. Đăng nhập sai mật khẩu -> Phải bị từ chối (None)
        user_wrong = authenticate(username="user_admin", password="wrong_password")
        self.assertIsNone(user_wrong)

        # 4. Người dùng không tồn tại -> Phải bị từ chối (None)
        user_fake = authenticate(username="nonexistent_user", password="password123")
        self.assertIsNone(user_fake)

    def test_certificate_search_does_not_crash(self):
        """Tìm kiếm chứng chỉ: Không phát sinh lỗi FieldError 500 do student_code."""
        self.client.force_login(self.admin_user)
        res = self.client.get("/certificates/?q=TestSearch", HTTP_HOST="127.0.0.1")
        self.assertEqual(res.status_code, 200)

        res_hv = self.client.get("/certificates/?q=HV-0001", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_hv.status_code, 200)

    def test_tuition_installment_payment_transaction(self):
        """Kiểm tra mô hình thanh toán nhiều đợt (PaymentTransaction) tự động tính toán số dư."""
        from core.models import Student, Course, EnglishClass, Tuition, PaymentTransaction
        from decimal import Decimal
        from datetime import date

        student = Student.objects.create(
            full_name="Nguyễn Văn Test Học Phí",
            date_of_birth=date(2000, 1, 1),
            phone="0911223344",
            email="test_tuition@example.com"
        )
        course = Course.objects.create(name="IELTS Intensive", tuition=Decimal("5000000"))
        english_class = EnglishClass.objects.create(name="IELTS-K1", course=course, start_date=date(2026, 1, 1))

        tuition = Tuition.objects.create(
            student=student,
            english_class=english_class,
            total_fee=Decimal("5000000"),
            paid_amount=Decimal("0"),
        )
        self.assertEqual(tuition.remaining_amount, Decimal("5000000"))
        self.assertFalse(tuition.is_paid)

        # Nộp đợt 1: 2.000.000 VNĐ
        tx1 = PaymentTransaction.objects.create(
            tuition=tuition,
            amount=Decimal("2000000"),
            payment_method=PaymentTransaction.PaymentMethod.CASH,
            collected_by=self.admin_user
        )
        tuition.refresh_from_db()
        self.assertEqual(tuition.paid_amount, Decimal("2000000"))
        self.assertEqual(tuition.remaining_amount, Decimal("3000000"))
        self.assertFalse(tuition.is_paid)

        # Nộp đợt 2: 3.000.000 VNĐ
        tx2 = PaymentTransaction.objects.create(
            tuition=tuition,
            amount=Decimal("3000000"),
            payment_method=PaymentTransaction.PaymentMethod.BANK_TRANSFER,
            collected_by=self.admin_user
        )
        tuition.refresh_from_db()
        self.assertEqual(tuition.paid_amount, Decimal("5000000"))
        self.assertEqual(tuition.remaining_amount, Decimal("0"))
        self.assertTrue(tuition.is_paid)
        self.assertEqual(tuition.transactions.count(), 2)

    def test_certificate_add_flow(self):
        """Kiểm tra cấp chứng chỉ mới từ Web UI (GET và POST)."""
        from core.models import Student, Course, EnglishClass, Certificate
        from decimal import Decimal
        from datetime import date

        student = Student.objects.create(
            full_name="Trần Thị Test Chứng Chỉ",
            date_of_birth=date(2002, 5, 10),
            phone="0988776655",
            email="test_cert@example.com"
        )
        course = Course.objects.create(name="TOEIC Master", tuition=Decimal("3000000"))
        english_class = EnglishClass.objects.create(name="TOEIC-01", course=course, start_date=date(2026, 1, 1))

        self.client.force_login(self.admin_user)

        # GET form
        res_get = self.client.get(f"/certificates/add/?class_id={english_class.id}", HTTP_HOST="127.0.0.1")
        self.assertEqual(res_get.status_code, 200)

        # POST cấp chứng chỉ
        res_post = self.client.post("/certificates/add/", {
            "english_class": str(english_class.id),
            "student": str(student.id),
            "score": "8.5",
            "classification": "Giỏi",
            "issue_date": str(date.today()),
        }, HTTP_HOST="127.0.0.1")
        self.assertEqual(res_post.status_code, 302)

        cert = Certificate.objects.filter(student=student, english_class=english_class).first()
        self.assertIsNotNone(cert)
        self.assertEqual(cert.score, Decimal("8.50"))
        self.assertEqual(cert.classification, "Giỏi")


