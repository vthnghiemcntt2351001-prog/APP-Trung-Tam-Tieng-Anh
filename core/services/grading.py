import logging
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from core.models import (
    Student,
    EnglishClass,
    Grade,
    Enrollment,
    AssessmentPolicy,
    AssessmentComponent,
    AssessmentEvent,
    AssessmentResult,
    FinalResult,
)
from core.services.assessments import record_assessment_result, calculate_final_result

logger = logging.getLogger(__name__)

SKILL_MAPPING = [
    ("oral_score", "Kỹ năng Nói (Speaking)", Decimal("25")),
    ("listening_score", "Kỹ năng Nghe (Listening)", Decimal("25")),
    ("reading_score", "Kỹ năng Đọc (Reading)", Decimal("25")),
    ("writing_score", "Kỹ năng Viết (Writing)", Decimal("25")),
]


def get_or_create_default_policy(course):
    """
    Tìm hoặc tạo quy chế đánh giá 4 kỹ năng mặc định cho khóa học.
    Mỗi kỹ năng chiếm 25% tỷ trọng, điểm tối đa 10, điểm đạt 5.0.
    """
    policy = AssessmentPolicy.objects.filter(
        course=course,
        name="Quy chế 4 kỹ năng Chuẩn",
        status=AssessmentPolicy.Status.ACTIVE,
    ).first()

    if policy:
        return policy

    # Kiểm tra xem có bản nháp hoặc version trước đó không
    latest_version = AssessmentPolicy.objects.filter(
        course=course,
        name="Quy chế 4 kỹ năng Chuẩn",
    ).order_by("-version").values_list("version", flat=True).first() or 0

    policy = AssessmentPolicy.objects.create(
        course=course,
        name="Quy chế 4 kỹ năng Chuẩn",
        version=latest_version + 1,
        scale=AssessmentPolicy.Scale.NUMERIC,
        max_score=Decimal("10"),
        pass_score=Decimal("5.0"),
        rounding_precision=1,
        status=AssessmentPolicy.Status.DRAFT,
    )

    for _, comp_name, weight in SKILL_MAPPING:
        AssessmentComponent.objects.create(
            policy=policy,
            name=comp_name,
            weight=weight,
            max_score=Decimal("10"),
            required=True,
            minimum_score=Decimal("0"),
        )

    # Kích hoạt quy chế sau khi đã đủ 100% tỷ trọng
    policy.status = AssessmentPolicy.Status.ACTIVE
    policy.save()

    return policy


@transaction.atomic
def sync_grade_to_assessment(grade: Grade, actor=None):
    """
    Đồng bộ dữ liệu điểm từ bảng Grade (4 kỹ năng) sang hệ thống AssessmentPolicy /
    AssessmentEvent / AssessmentResult / FinalResult.
    """
    try:
        student = grade.student
        english_class = grade.english_class
        course = english_class.course

        # 1. Đảm bảo Enrollment tồn tại
        enrollment, _ = Enrollment.objects.get_or_create(
            student=student,
            english_class=english_class,
            defaults={
                "status": Enrollment.Status.STUDYING,
                "enrolled_at": grade.exam_date or timezone.localdate(),
            },
        )

        # 2. Đảm bảo EnglishClass có AssessmentPolicy
        if not english_class.assessment_policy:
            policy = get_or_create_default_policy(course)
            english_class.assessment_policy = policy
            english_class.save(update_fields=["assessment_policy"])
        else:
            policy = english_class.assessment_policy

        if not enrollment.assessment_policy:
            enrollment.assessment_policy = policy
            enrollment.save(update_fields=["assessment_policy"])

        # 3. Đồng bộ từng kỹ năng vào AssessmentEvent & AssessmentResult
        components = {c.name: c for c in policy.components.all()}

        # Nếu quy chế của lớp có các thành phần khác, ánh xạ tương thích hoặc dùng components có sẵn
        for field_name, comp_name, weight in SKILL_MAPPING:
            component = components.get(comp_name)
            if not component:
                # Tìm component tương đồng nếu tên khác (ví dụ: "Nói", "Speaking")
                for c in components.values():
                    if comp_name.split()[1].lower() in c.name.lower():
                        component = c
                        break

            if not component:
                continue

            score = getattr(grade, field_name, None)
            if score is None:
                continue

            # Tìm hoặc tạo AssessmentEvent cho đợt thi này của lớp
            event_name = f"Đánh giá {component.name} ({grade.exam_date})"
            event, _ = AssessmentEvent.objects.get_or_create(
                english_class=english_class,
                component=component,
                name=event_name,
                defaults={
                    "assessment_date": grade.exam_date,
                    "max_score": component.max_score,
                    "created_by": actor,
                },
            )

            # Thêm enrollment vào danh sách tham gia event
            if not event.participants.filter(pk=enrollment.pk).exists():
                event.participants.add(enrollment)

            # Ghi nhận kết quả
            record_assessment_result(
                enrollment_id=enrollment.pk,
                event_id=event.pk,
                actor=actor,
                status=AssessmentResult.Status.GRADED,
                score=score,
                attempt_number=1,
                feedback=grade.note or "",
                reason="Đồng bộ tự động từ bảng điểm kỹ năng",
            )

        # 4. Tính toán điểm tổng kết
        final_result = calculate_final_result(enrollment_id=enrollment.pk)
        return final_result

    except Exception as e:
        logger.warning("Không thể tự động đồng bộ Grade sang Assessment: %s", str(e), exc_info=True)
        return None
