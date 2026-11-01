import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from core.models import (
    Student,
    Course,
    Teacher,
    EnglishClass,
    Enrollment,
    ClassTransfer,
)
from core.services.class_transfers import (
    request_class_transfer,
    approve_class_transfer,
    reject_class_transfer,
)


User = get_user_model()


class ClassTransferServiceTestCase(TestCase):
    def setUp(self):
        self.actor = User.objects.create_user(
            username="admin_transfer",
            password="password123",
            email="admin_transfer@test.com"
        )
        self.course_a = Course.objects.create(
            name="Khóa IELTS A",
            tuition=4000000,
            duration=3,
        )
        self.course_b = Course.objects.create(
            name="Khóa TOEIC B",
            tuition=3500000,
            duration=3,
        )
        self.teacher = Teacher.objects.create(
            full_name="Cô Lê Thị B",
            email="lethib@test.com",
            phone="0911223344"
        )
        self.class_source = EnglishClass.objects.create(
            name="Lớp IELTS Sáng 2-4-6",
            course=self.course_a,
            teacher=self.teacher,
            start_date=datetime.date.today(),
            max_students=20,
        )
        self.class_target_same_course = EnglishClass.objects.create(
            name="Lớp IELTS Tối 3-5-7",
            course=self.course_a,
            teacher=self.teacher,
            start_date=datetime.date.today(),
            max_students=20,
        )
        self.class_target_diff_course = EnglishClass.objects.create(
            name="Lớp TOEIC Căn Bản",
            course=self.course_b,
            teacher=self.teacher,
            start_date=datetime.date.today(),
            max_students=2,  # Nhỏ để test full
        )

        self.student = Student.objects.create(
            full_name="Nguyễn Văn Chuyển Lớp",
            email="chuyenlop@test.com",
            phone="0909090909"
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            english_class=self.class_source,
            status=Enrollment.Status.STUDYING,
        )

    def test_same_course_transfer_auto_applied(self):
        """Cùng khóa học: Chuyển lớp lập tức, Enrollment cũ TRANSFERRED, Enrollment mới STUDYING."""
        transfer = request_class_transfer(
            student_id=self.student.id,
            source_class_id=self.class_source.id,
            target_class_id=self.class_target_same_course.id,
            reason="Trùng lịch học thêm buổi sáng",
            actor=self.actor,
        )

        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, Enrollment.Status.TRANSFERRED)
        self.assertIsNotNone(self.enrollment.ended_at)

        new_enrollment = Enrollment.objects.get(
            student=self.student,
            english_class=self.class_target_same_course,
        )
        self.assertEqual(new_enrollment.status, Enrollment.Status.STUDYING)
        self.assertEqual(transfer.status, ClassTransfer.Status.COMPLETED)

    def test_diff_course_transfer_pending_and_approve(self):
        """Khác khóa học: Tạo yêu cầu PENDING, sau khi Admin duyệt mới chuyển lớp."""
        transfer = request_class_transfer(
            student_id=self.student.id,
            source_class_id=self.class_source.id,
            target_class_id=self.class_target_diff_course.id,
            reason="Muốn đổi sang học TOEIC",
            actor=self.actor,
        )
        self.assertEqual(transfer.status, ClassTransfer.Status.PENDING)

        # Trạng thái enrollment cũ vẫn là STUDYING khi chưa duyệt
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, Enrollment.Status.STUDYING)

        # Admin duyệt đơn
        approve_class_transfer(
            transfer_id=transfer.id,
            actor=self.actor,
        )

        transfer.refresh_from_db()
        self.assertEqual(transfer.status, ClassTransfer.Status.COMPLETED)

        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, Enrollment.Status.TRANSFERRED)

        new_enrollment = Enrollment.objects.get(
            student=self.student,
            english_class=self.class_target_diff_course,
        )
        self.assertEqual(new_enrollment.status, Enrollment.Status.STUDYING)

    def test_reject_class_transfer(self):
        """Từ chối đơn chuyển lớp: Chuyển sang REJECTED, Enrollment cũ không bị ảnh hưởng."""
        transfer = request_class_transfer(
            student_id=self.student.id,
            source_class_id=self.class_source.id,
            target_class_id=self.class_target_diff_course.id,
            reason="Muốn đổi khóa",
            actor=self.actor,
        )

        reject_class_transfer(
            transfer_id=transfer.id,
            actor=self.actor,
        )

        transfer.refresh_from_db()
        self.assertEqual(transfer.status, ClassTransfer.Status.REJECTED)

        # Học viên vẫn đang học ở lớp cũ bình thường
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.status, Enrollment.Status.STUDYING)

    def test_transfer_blocked_if_target_class_full(self):
        """Không cho phép chuyển lớp nếu lớp đích đã đầy sĩ số tối đa."""
        # Giả lập lớp đích đã có 2 học viên (max_students=2)
        st1 = Student.objects.create(full_name="HV 1", email="hv1@test.com", phone="0111")
        st2 = Student.objects.create(full_name="HV 2", email="hv2@test.com", phone="0222")
        Enrollment.objects.create(student=st1, english_class=self.class_target_diff_course, status=Enrollment.Status.STUDYING)
        Enrollment.objects.create(student=st2, english_class=self.class_target_diff_course, status=Enrollment.Status.STUDYING)

        with self.assertRaises(ValidationError) as ctx:
            request_class_transfer(
                student_id=self.student.id,
                source_class_id=self.class_source.id,
                target_class_id=self.class_target_diff_course.id,
                reason="Xin vào lớp đầy",
                actor=self.actor,
            )
        self.assertIn("đủ sĩ số", str(ctx.exception))
