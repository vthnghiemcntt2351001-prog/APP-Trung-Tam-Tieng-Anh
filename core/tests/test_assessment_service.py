from decimal import Decimal
import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import (
    Student,
    Course,
    Teacher,
    EnglishClass,
    Enrollment,
    AssessmentPolicy,
    AssessmentComponent,
    AssessmentEvent,
    AssessmentResult,
    FinalResult,
)
from core.services.assessments import calculate_final_result, record_assessment_result


User = get_user_model()


class AssessmentServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="teacher_test",
            password="password123",
            email="teacher@test.com"
        )
        self.course = Course.objects.create(
            name="Khóa Kiểm thử IELTS 6.5",
            tuition=5000000,
            duration=3,
        )
        self.teacher = Teacher.objects.create(
            full_name="Thầy Nguyễn Văn A",
            email="nguyenvana@test.com",
            phone="0912345678"
        )
        self.policy = AssessmentPolicy.objects.create(
            course=self.course,
            name="Quy chế IELTS 3 cột",
            max_score=Decimal("10.0"),
            pass_score=Decimal("5.0"),
            status=AssessmentPolicy.Status.DRAFT,
        )
        self.comp_attendance = AssessmentComponent.objects.create(
            policy=self.policy,
            name="Chuyên cần",
            weight=Decimal("10.0"),
            max_score=Decimal("10.0"),
            aggregation="average",
            required=True,
        )
        self.comp_midterm = AssessmentComponent.objects.create(
            policy=self.policy,
            name="Giữa kỳ",
            weight=Decimal("40.0"),
            max_score=Decimal("10.0"),
            aggregation="latest",
            required=True,
        )
        self.comp_final = AssessmentComponent.objects.create(
            policy=self.policy,
            name="Cuối kỳ",
            weight=Decimal("50.0"),
            max_score=Decimal("10.0"),
            aggregation="highest",
            required=True,
        )

        self.policy.status = AssessmentPolicy.Status.ACTIVE
        self.policy.save()

        self.english_class = EnglishClass.objects.create(
            name="Lớp Test Assessment 01",
            course=self.course,
            teacher=self.teacher,
            assessment_policy=self.policy,
            start_date=datetime.date.today(),
            max_students=20,
        )
        self.student = Student.objects.create(
            full_name="Trần Văn Học Viên",
            email="hocvien_test@test.com",
            phone="0987654321"
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            english_class=self.english_class,
            assessment_policy=self.policy,
            status=Enrollment.Status.STUDYING,
        )

    def test_weighted_final_score_passed(self):
        """Kiểm thử tính đúng điểm tổng kết theo trọng số và đạt chuẩn PASSED."""
        # Tạo các đợt đánh giá (Events)
        ev_att = AssessmentEvent.objects.create(
            english_class=self.english_class,
            component=self.comp_attendance,
            name="Đánh giá chuyên cần",
            assessment_date=timezone.localdate(),
        )
        ev_att.participants.add(self.enrollment)

        ev_mid = AssessmentEvent.objects.create(
            english_class=self.english_class,
            component=self.comp_midterm,
            name="Thi giữa kỳ",
            assessment_date=timezone.localdate(),
        )
        ev_mid.participants.add(self.enrollment)

        ev_fin = AssessmentEvent.objects.create(
            english_class=self.english_class,
            component=self.comp_final,
            name="Thi cuối kỳ",
            assessment_date=timezone.localdate(),
        )
        ev_fin.participants.add(self.enrollment)

        # Nhập điểm: Chuyên cần 10, Giữa kỳ 7, Cuối kỳ 8
        # Trọng số: 10*0.1 + 7*0.4 + 8*0.5 = 1.0 + 2.8 + 4.0 = 7.8
        record_assessment_result(
            enrollment_id=self.enrollment.id,
            event_id=ev_att.id,
            actor=self.user,
            status=AssessmentResult.Status.GRADED,
            score=Decimal("10.0"),
        )
        record_assessment_result(
            enrollment_id=self.enrollment.id,
            event_id=ev_mid.id,
            actor=self.user,
            status=AssessmentResult.Status.GRADED,
            score=Decimal("7.0"),
        )
        record_assessment_result(
            enrollment_id=self.enrollment.id,
            event_id=ev_fin.id,
            actor=self.user,
            status=AssessmentResult.Status.GRADED,
            score=Decimal("8.0"),
        )

        final_result = calculate_final_result(enrollment_id=self.enrollment.id)
        self.assertIsNotNone(final_result.final_score)
        self.assertEqual(final_result.final_score, Decimal("7.8000"))
        self.assertEqual(final_result.status, FinalResult.Status.PASSED)

    def test_weighted_final_score_failed(self):
        """Kiểm thử học viên có điểm dưới điểm chuẩn (5.0) sẽ bị NOT_PASSED."""
        ev_att = AssessmentEvent.objects.create(
            english_class=self.english_class,
            component=self.comp_attendance,
            name="Đánh giá chuyên cần",
            assessment_date=timezone.localdate(),
        )
        ev_att.participants.add(self.enrollment)

        ev_mid = AssessmentEvent.objects.create(
            english_class=self.english_class,
            component=self.comp_midterm,
            name="Thi giữa kỳ",
            assessment_date=timezone.localdate(),
        )
        ev_mid.participants.add(self.enrollment)

        ev_fin = AssessmentEvent.objects.create(
            english_class=self.english_class,
            component=self.comp_final,
            name="Thi cuối kỳ",
            assessment_date=timezone.localdate(),
        )
        ev_fin.participants.add(self.enrollment)

        # Điểm thấp: 4*0.1 + 4*0.4 + 4*0.5 = 4.0 (< 5.0)
        record_assessment_result(
            enrollment_id=self.enrollment.id,
            event_id=ev_att.id,
            actor=self.user,
            status=AssessmentResult.Status.GRADED,
            score=Decimal("4.0"),
        )
        record_assessment_result(
            enrollment_id=self.enrollment.id,
            event_id=ev_mid.id,
            actor=self.user,
            status=AssessmentResult.Status.GRADED,
            score=Decimal("4.0"),
        )
        record_assessment_result(
            enrollment_id=self.enrollment.id,
            event_id=ev_fin.id,
            actor=self.user,
            status=AssessmentResult.Status.GRADED,
            score=Decimal("4.0"),
        )

        final_result = calculate_final_result(enrollment_id=self.enrollment.id)
        self.assertEqual(final_result.final_score, Decimal("4.0000"))
        self.assertEqual(final_result.status, FinalResult.Status.NOT_PASSED)

    def test_missing_required_component_pending(self):
        """Kiểm thử khi thiếu cột điểm bắt buộc thì trạng thái là PENDING_RESULTS."""
        ev_att = AssessmentEvent.objects.create(
            english_class=self.english_class,
            component=self.comp_attendance,
            name="Đánh giá chuyên cần",
            assessment_date=timezone.localdate(),
        )
        ev_att.participants.add(self.enrollment)

        record_assessment_result(
            enrollment_id=self.enrollment.id,
            event_id=ev_att.id,
            actor=self.user,
            status=AssessmentResult.Status.GRADED,
            score=Decimal("9.0"),
        )

        final_result = calculate_final_result(enrollment_id=self.enrollment.id)
        self.assertIsNone(final_result.final_score)
        self.assertEqual(final_result.status, FinalResult.Status.PENDING_RESULTS)
        self.assertIn("Giữa kỳ", final_result.calculation_details.get("missing_required_components", []))
