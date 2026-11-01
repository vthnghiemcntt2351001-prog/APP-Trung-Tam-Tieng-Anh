from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from core.models import Attendance, ClassSession, Course, EnglishClass, Enrollment, Student, Teacher

User = get_user_model()


class AttendanceTests(TestCase):
    def setUp(self):
        # Tạo nhóm quyền Academic (Học vụ)
        self.academic_group, _ = Group.objects.get_or_create(name="Học vụ")
        self.user = User.objects.create_user(
            username="academic_user",
            password="password123",
            email="academic@example.com",
        )
        self.user.groups.add(self.academic_group)

        # Tạo dữ liệu học vụ
        self.course = Course.objects.create(
            name="IELTS Intensive",
            tuition=4500000,
            duration=3,
        )
        self.teacher = Teacher.objects.create(
            full_name="Nguyễn Văn A",
            email="teacher.a@example.com",
            phone="0911222333",
        )
        self.english_class = EnglishClass.objects.create(
            name="IELTS-K01",
            course=self.course,
            teacher=self.teacher,
            start_date=date(2026, 11, 1),
            max_students=20,
        )

        self.student1 = Student.objects.create(
            full_name="Trần Văn Học",
            email="hoc.tran@example.com",
            phone="0901000001",
        )
        self.student2 = Student.objects.create(
            full_name="Lê Thị Chăm",
            email="cham.le@example.com",
            phone="0901000002",
        )

        Enrollment.objects.create(
            student=self.student1,
            english_class=self.english_class,
            status=Enrollment.Status.STUDYING,
        )
        Enrollment.objects.create(
            student=self.student2,
            english_class=self.english_class,
            status=Enrollment.Status.STUDYING,
        )

    def test_create_class_session(self):
        """Kiểm tra tạo buổi học thành công."""
        session = ClassSession.objects.create(
            english_class=self.english_class,
            session_number=1,
            session_date=date(2026, 11, 2),
            room="P.101",
            topic="Unit 1: Introduction",
        )
        self.assertEqual(session.session_number, 1)
        self.assertEqual(session.english_class, self.english_class)
        self.assertFalse(session.is_completed)

    def test_session_list_view(self):
        """Kiểm tra view danh sách buổi học."""
        self.client.login(username="academic_user", password="password123")
        ClassSession.objects.create(
            english_class=self.english_class,
            session_number=1,
            session_date=date(2026, 11, 2),
        )

        url = reverse("session_list", args=[self.english_class.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "IELTS-K01")
        self.assertContains(response, "#1")

    def test_session_add_view(self):
        """Kiểm tra form thêm buổi học qua HTTP POST."""
        self.client.login(username="academic_user", password="password123")
        url = reverse("session_add", args=[self.english_class.id])

        post_data = {
            "session_number": "1",
            "session_date": "2026-11-05",
            "start_time": "18:00",
            "end_time": "19:30",
            "room": "P.205",
            "topic": "Grammar Review",
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)

        session = ClassSession.objects.filter(
            english_class=self.english_class,
            session_number=1,
        ).first()
        self.assertIsNotNone(session)
        self.assertEqual(session.room, "P.205")
        self.assertEqual(session.topic, "Grammar Review")

    def test_session_attendance_flow(self):
        """Kiểm tra luồng điểm danh nhanh nhiều học viên cùng lúc."""
        session = ClassSession.objects.create(
            english_class=self.english_class,
            session_number=1,
            session_date=date(2026, 11, 2),
        )

        self.client.login(username="academic_user", password="password123")
        url = reverse("session_attendance", args=[session.id])

        # GET trang điểm danh
        get_res = self.client.get(url)
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, "Trần Văn Học")
        self.assertContains(get_res, "Lê Thị Chăm")

        # POST lưu điểm danh: student1 có mặt, student2 đi muộn
        post_data = {
            f"status_{self.student1.id}": "present",
            f"note_{self.student1.id}": "Đúng giờ",
            f"status_{self.student2.id}": "late",
            f"note_{self.student2.id}": "Muộn 15 phút",
        }
        post_res = self.client.post(url, post_data)
        self.assertEqual(post_res.status_code, 302)

        # Kiểm tra bản ghi Attendance
        att1 = Attendance.objects.get(session=session, student=self.student1)
        att2 = Attendance.objects.get(session=session, student=self.student2)

        self.assertEqual(att1.status, Attendance.AttendanceStatus.PRESENT)
        self.assertEqual(att1.note, "Đúng giờ")
        self.assertEqual(att2.status, Attendance.AttendanceStatus.LATE)
        self.assertEqual(att2.note, "Muộn 15 phút")

        # Session phải được đánh dấu hoàn thành
        session.refresh_from_db()
        self.assertTrue(session.is_completed)

    def test_attendance_report_view(self):
        """Kiểm tra báo cáo chuyên cần tính tỷ lệ chính xác."""
        session1 = ClassSession.objects.create(
            english_class=self.english_class,
            session_number=1,
            session_date=date(2026, 11, 2),
            is_completed=True,
        )
        session2 = ClassSession.objects.create(
            english_class=self.english_class,
            session_number=2,
            session_date=date(2026, 11, 4),
            is_completed=True,
        )

        # Student 1: 2 buổi có mặt -> 100%
        Attendance.objects.create(session=session1, student=self.student1, status=Attendance.AttendanceStatus.PRESENT)
        Attendance.objects.create(session=session2, student=self.student1, status=Attendance.AttendanceStatus.PRESENT)

        # Student 2: 1 buổi có mặt, 1 buổi vắng không phép -> 50%
        Attendance.objects.create(session=session1, student=self.student2, status=Attendance.AttendanceStatus.PRESENT)
        Attendance.objects.create(session=session2, student=self.student2, status=Attendance.AttendanceStatus.ABSENT_UNEXCUSED)

        self.client.login(username="academic_user", password="password123")
        url = reverse("class_attendance_report", args=[self.english_class.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "100.0%")
        self.assertContains(response, "50.0%")
        self.assertContains(response, "Vắng quá 20%")
