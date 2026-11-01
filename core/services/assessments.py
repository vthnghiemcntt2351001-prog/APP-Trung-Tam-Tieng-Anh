from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.models import (
    AssessmentEvent,
    AssessmentResult,
    AssessmentResultAudit,
    Enrollment,
    FinalResult,
)


def _event_max_score(event):
    return event.max_score or event.component.max_score


def _aggregate(values, method):
    if method == "highest":
        return max(values)
    if method == "latest":
        return values[-1]
    return sum(values, Decimal("0")) / Decimal(len(values))


@transaction.atomic
def record_assessment_result(
    *,
    enrollment_id,
    event_id,
    actor,
    status,
    score=None,
    attempt_number=1,
    feedback="",
    reason="",
):
    enrollment = Enrollment.objects.select_for_update().get(pk=enrollment_id)
    event = (
        AssessmentEvent.objects.select_for_update()
        .select_related("english_class", "component__policy")
        .get(pk=event_id)
    )
    if enrollment.english_class_id != event.english_class_id:
        raise ValidationError("Học viên không thuộc lớp của đợt đánh giá này.")
    if not event.participants.filter(pk=enrollment.pk).exists():
        raise ValidationError("Học viên không nằm trong danh sách của đợt đánh giá này.")
    existing_final_result = FinalResult.objects.filter(
        enrollment=enrollment
    ).only("policy_id").first()
    effective_policy_id = (
        enrollment.assessment_policy_id
        or (
            existing_final_result.policy_id
            if existing_final_result
            else enrollment.english_class.assessment_policy_id
        )
    )
    if effective_policy_id != event.component.policy_id:
        raise ValidationError("Đợt đánh giá không thuộc quy chế đang gán cho lớp.")

    result = (
        AssessmentResult.objects.select_for_update()
        .filter(
            enrollment=enrollment,
            event=event,
            attempt_number=attempt_number,
        )
        .first()
    )
    old_score = result.score if result else None
    old_status = result.status if result else ""
    if result and (old_score != score or old_status != status) and not reason.strip():
        raise ValidationError("Khi sửa kết quả đã lưu, cần ghi lý do thay đổi.")

    if result is None:
        result = AssessmentResult(
            enrollment=enrollment,
            event=event,
            attempt_number=attempt_number,
        )
    result.score = score
    result.status = status
    result.feedback = (feedback or "").strip()
    result.graded_by = actor
    result.graded_at = timezone.now() if status == AssessmentResult.Status.GRADED else None
    result.full_clean()
    result.save()

    if old_score != result.score or old_status != result.status:
        AssessmentResultAudit.objects.create(
            result=result,
            old_score=old_score,
            new_score=result.score,
            old_status=old_status,
            new_status=result.status,
            reason=(reason or "Nhập kết quả lần đầu").strip(),
            changed_by=actor,
        )

    calculate_final_result(enrollment_id=enrollment.pk)
    return result


@transaction.atomic
def calculate_final_result(*, enrollment_id):
    enrollment = (
        Enrollment.objects.select_for_update()
        .select_related("english_class__assessment_policy", "assessment_policy")
        .get(pk=enrollment_id)
    )
    previous_final_result = (
        FinalResult.objects.select_for_update()
        .select_related("policy")
        .filter(enrollment=enrollment)
        .first()
    )
    policy = (
        previous_final_result.policy
        if previous_final_result
        else enrollment.assessment_policy or enrollment.english_class.assessment_policy
    )
    if policy is None:
        raise ValidationError("Lớp chưa được gán quy chế đánh giá.")
    if policy.course_id != enrollment.english_class.course_id:
        raise ValidationError("Quy chế đánh giá không thuộc khóa học của lớp.")

    components = list(policy.components.all().order_by("id"))
    if not components:
        raise ValidationError("Quy chế chưa có thành phần đánh giá.")

    details = {}
    weighted_score = Decimal("0")
    used_weight = Decimal("0")
    missing_required = []
    failed_components = []

    for component in components:
        results = list(
            AssessmentResult.objects.filter(
                enrollment=enrollment,
                event__english_class=enrollment.english_class,
                event__component=component,
                status=AssessmentResult.Status.GRADED,
            )
            .select_related("event", "event__component")
            .order_by("event__assessment_date", "event_id", "attempt_number", "id")
        )
        normalized_scores = [
            result.score * policy.max_score / _event_max_score(result.event)
            for result in results
        ]

        if not normalized_scores:
            details[component.name] = {
                "status": "missing",
                "weight": str(component.weight),
            }
            if component.required:
                missing_required.append(component.name)
            continue

        component_score = _aggregate(normalized_scores, component.aggregation)
        weighted_score += component_score * component.weight / Decimal("100")
        used_weight += component.weight

        raw_scores = [result.score for result in results]
        raw_component_score = _aggregate(raw_scores, component.aggregation)
        component_minimum = component.minimum_score
        normalized_minimum = (
            component_minimum * policy.max_score / component.max_score
            if component_minimum is not None
            else None
        )
        if normalized_minimum is not None and component_score < normalized_minimum:
            failed_components.append(component.name)

        details[component.name] = {
            "score_on_policy_scale": str(component_score),
            "score_on_component_scale": str(raw_component_score),
            "weight": str(component.weight),
            "attempts_counted": len(results),
            "aggregation": component.aggregation,
        }

    if missing_required or used_weight == 0:
        final_score = None
        result_status = FinalResult.Status.PENDING_RESULTS
        details["missing_required_components"] = missing_required
    else:
        # Optional components without a score do not silently reduce the result.
        unrounded_score = weighted_score * Decimal("100") / used_weight
        final_score = unrounded_score.quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        if (
            policy.pass_score is None
            and policy.scale != policy.Scale.PASS_FAIL
        ):
            raise ValidationError("Quy chế cần cấu hình điểm tổng kết tối thiểu.")
        passed_overall = (
            policy.pass_score is None or unrounded_score >= policy.pass_score
        )
        result_status = (
            FinalResult.Status.PASSED
            if passed_overall and not failed_components
            else FinalResult.Status.NOT_PASSED
        )
        details["failed_components"] = failed_components
        details["used_weight"] = str(used_weight)

    final_result, _ = FinalResult.objects.update_or_create(
        enrollment=enrollment,
        defaults={
            "policy": policy,
            "final_score": final_score,
            "status": result_status,
            "calculation_details": details,
            "calculated_at": timezone.now(),
        },
    )
    if enrollment.assessment_policy_id is None:
        enrollment.assessment_policy = policy
        enrollment.save(update_fields=["assessment_policy"])
    return final_result
