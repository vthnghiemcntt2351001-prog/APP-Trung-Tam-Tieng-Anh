from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.models import ClassTransfer, Enrollment, EnglishClass


@transaction.atomic
def request_class_transfer(
    *,
    student_id,
    source_class_id,
    target_class_id,
    reason,
    actor,
):
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError("Vui lòng nhập lý do chuyển lớp.")

    source_enrollment = (
        Enrollment.objects.select_for_update()
        .select_related("student", "english_class")
        .filter(
            student_id=student_id,
            english_class_id=source_class_id,
            status=Enrollment.Status.STUDYING,
        )
        .first()
    )
    if source_enrollment is None:
        raise ValidationError("Học viên không có ghi danh đang học ở lớp cũ.")

    source_class = source_enrollment.english_class
    target_class = (
        EnglishClass.objects.select_for_update()
        .select_related("course")
        .filter(pk=target_class_id)
        .first()
    )
    if target_class is None:
        raise ValidationError("Không tìm thấy lớp đích.")
    if target_class.pk == source_class.pk:
        raise ValidationError("Lớp đích phải khác lớp hiện tại.")

    if ClassTransfer.objects.filter(
        source_enrollment=source_enrollment,
        status=ClassTransfer.Status.PENDING,
    ).exists():
        raise ValidationError("Đã có yêu cầu chuyển lớp đang chờ duyệt.")

    target_enrollment = (
        Enrollment.objects.select_for_update()
        .filter(
            student_id=student_id,
            english_class=target_class,
        )
        .first()
    )
    if target_enrollment and target_enrollment.status == Enrollment.Status.STUDYING:
        raise ValidationError("Học viên đang học lớp đích rồi.")
    if target_enrollment and target_enrollment.status == Enrollment.Status.COMPLETED:
        raise ValidationError("Học viên đã hoàn thành lớp đích.")

    active_count = target_class.enrollments.filter(
        status=Enrollment.Status.STUDYING
    ).count()
    if active_count >= target_class.max_students:
        raise ValidationError("Lớp đích đã đủ sĩ số.")

    transfer_data = {
        "student": source_enrollment.student,
        "source_class": source_class,
        "target_class": target_class,
        "source_enrollment": source_enrollment,
        "reason": reason,
        "requested_by": actor,
    }

    # Cùng khóa: chuyển ngay, không cần Admin duyệt.
    if source_class.course_id == target_class.course_id:
        today = timezone.localdate()
        now = timezone.now()

        source_enrollment.status = Enrollment.Status.TRANSFERRED
        source_enrollment.ended_at = today
        source_enrollment.note = "\n".join(
            part
            for part in (
                source_enrollment.note,
                f"Chuyển sang lớp {target_class.name}: {reason}",
            )
            if part
        )
        source_enrollment.save(
            update_fields=["status", "ended_at", "note"]
        )

        if target_enrollment:
            target_enrollment.status = Enrollment.Status.STUDYING
            target_enrollment.enrolled_at = today
            target_enrollment.ended_at = None
            if target_enrollment.assessment_policy_id is None:
                target_enrollment.assessment_policy = target_class.assessment_policy
            target_enrollment.save(
                update_fields=[
                    "status",
                    "enrolled_at",
                    "ended_at",
                    "assessment_policy",
                ]
            )
            destination_enrollment = target_enrollment
        else:
            destination_enrollment = Enrollment.objects.create(
                student=source_enrollment.student,
                english_class=target_class,
                assessment_policy=target_class.assessment_policy,
                status=Enrollment.Status.STUDYING,
                enrolled_at=today,
                note=f"Chuyển từ lớp {source_class.name}: {reason}",
            )

        return ClassTransfer.objects.create(
            **transfer_data,
            destination_enrollment=destination_enrollment,
            status=ClassTransfer.Status.COMPLETED,
            performed_by=actor,
            transferred_at=now,
        )

    # Khác khóa: chỉ tạo yêu cầu. Admin sẽ duyệt ở bước sau.
    return ClassTransfer.objects.create(
        **transfer_data,
        status=ClassTransfer.Status.PENDING,
    )


@transaction.atomic
def approve_class_transfer(*, transfer_id, actor):
    transfer = (
        ClassTransfer.objects.select_for_update()
        .select_related("source_class", "target_class", "student")
        .filter(pk=transfer_id)
        .first()
    )
    if transfer is None:
        raise ValidationError("Không tìm thấy yêu cầu chuyển lớp.")
    if transfer.status != ClassTransfer.Status.PENDING:
        raise ValidationError("Yêu cầu này không còn chờ duyệt.")
    if transfer.source_class.course_id == transfer.target_class.course_id:
        raise ValidationError("Yêu cầu này không thuộc trường hợp cần Admin duyệt.")

    target_class = EnglishClass.objects.select_for_update().get(
        pk=transfer.target_class_id
    )
    source_enrollment = Enrollment.objects.select_for_update().get(
        pk=transfer.source_enrollment_id
    )
    if (
        source_enrollment.student_id != transfer.student_id
        or source_enrollment.english_class_id != transfer.source_class_id
        or source_enrollment.status != Enrollment.Status.STUDYING
    ):
        raise ValidationError("Ghi danh lớp cũ đã thay đổi; không thể duyệt.")

    target_enrollment = (
        Enrollment.objects.select_for_update()
        .filter(
            student_id=transfer.student_id,
            english_class=target_class,
        )
        .first()
    )
    if target_enrollment and target_enrollment.status in (
        Enrollment.Status.STUDYING,
        Enrollment.Status.COMPLETED,
    ):
        raise ValidationError("Học viên đang học hoặc đã hoàn thành lớp đích.")

    active_count = target_class.enrollments.filter(
        status=Enrollment.Status.STUDYING
    ).count()
    if active_count >= target_class.max_students:
        raise ValidationError("Lớp đích đã đủ sĩ số; chưa thể duyệt.")

    today = timezone.localdate()
    now = timezone.now()
    source_enrollment.status = Enrollment.Status.TRANSFERRED
    source_enrollment.ended_at = today
    source_enrollment.note = "\n".join(
        part
        for part in (
            source_enrollment.note,
            f"Chuyển sang lớp {target_class.name}: {transfer.reason}",
        )
        if part
    )
    source_enrollment.save(update_fields=["status", "ended_at", "note"])

    if target_enrollment:
        target_enrollment.status = Enrollment.Status.STUDYING
        target_enrollment.enrolled_at = today
        target_enrollment.ended_at = None
        if target_enrollment.assessment_policy_id is None:
            target_enrollment.assessment_policy = target_class.assessment_policy
        target_enrollment.save(
            update_fields=[
                "status",
                "enrolled_at",
                "ended_at",
                "assessment_policy",
            ]
        )
        destination_enrollment = target_enrollment
    else:
        destination_enrollment = Enrollment.objects.create(
            student=transfer.student,
            english_class=target_class,
            assessment_policy=target_class.assessment_policy,
            status=Enrollment.Status.STUDYING,
            enrolled_at=today,
            note=f"Chuyển từ lớp {transfer.source_class.name}: {transfer.reason}",
        )

    transfer.destination_enrollment = destination_enrollment
    transfer.status = ClassTransfer.Status.COMPLETED
    transfer.approved_by = actor
    transfer.approved_at = now
    transfer.performed_by = actor
    transfer.transferred_at = now
    transfer.save(
        update_fields=[
            "destination_enrollment",
            "status",
            "approved_by",
            "approved_at",
            "performed_by",
            "transferred_at",
        ]
    )
    return transfer


@transaction.atomic
def reject_class_transfer(*, transfer_id, actor):
    transfer = (
        ClassTransfer.objects.select_for_update()
        .filter(pk=transfer_id)
        .first()
    )
    if transfer is None:
        raise ValidationError("Không tìm thấy yêu cầu chuyển lớp.")
    if transfer.status != ClassTransfer.Status.PENDING:
        raise ValidationError("Yêu cầu này không còn chờ duyệt.")

    transfer.status = ClassTransfer.Status.REJECTED
    # These fields record the administrator's decision for both approve and reject.
    transfer.approved_by = actor
    transfer.approved_at = timezone.now()
    transfer.save(update_fields=["status", "approved_by", "approved_at"])
    return transfer
