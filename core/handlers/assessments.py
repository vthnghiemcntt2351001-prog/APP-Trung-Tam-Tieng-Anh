from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from ..models import (
    AssessmentComponent,
    AssessmentEvent,
    AssessmentPolicy,
    AssessmentResult,
    Course,
    Enrollment,
    EnglishClass,
    FinalResult,
)
from ..permissions import admin_context, admin_required, academic_required
from ..services.assessments import record_assessment_result


@admin_required
def assessment_policy_list(request):
    policies = AssessmentPolicy.objects.select_related("course").prefetch_related(
        "components"
    ).order_by("-id")

    total_count = policies.count()
    active_count = policies.filter(status=AssessmentPolicy.Status.ACTIVE).count()
    draft_count = policies.filter(status=AssessmentPolicy.Status.DRAFT).count()
    archived_count = policies.filter(status=AssessmentPolicy.Status.ARCHIVED).count()

    q = request.GET.get("q", "").strip()
    course_id = request.GET.get("course_id", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if q:
        policies = policies.filter(name__icontains=q)
    if course_id:
        policies = policies.filter(course_id=course_id)
    if status_filter:
        policies = policies.filter(status=status_filter)

    courses = Course.objects.order_by("name")

    return render(
        request,
        "core/academics/assessments/policies.html",
        {
            "policies": policies,
            "courses": courses,
            "q": q,
            "selected_course_id": course_id,
            "selected_status": status_filter,
            "total_count": total_count,
            "active_count": active_count,
            "draft_count": draft_count,
            "archived_count": archived_count,
            **admin_context(request),
        },
    )


@admin_required
def assessment_policy_create(request):
    form_data = {}
    if request.method == "POST":
        form_data = request.POST
        try:
            course = get_object_or_404(Course, pk=request.POST.get("course"))
            policy = AssessmentPolicy(
                course=course,
                name=request.POST.get("name", "").strip(),
                version=int(request.POST.get("version", "1")),
                scale=request.POST.get("scale", AssessmentPolicy.Scale.NUMERIC),
                max_score=Decimal(request.POST.get("max_score", "10")),
                pass_score=(
                    Decimal(request.POST["pass_score"])
                    if request.POST.get("pass_score", "").strip()
                    else None
                ),
                rounding_precision=int(request.POST.get("rounding_precision", "1")),
                effective_from=parse_date(request.POST.get("effective_from", "")) or None,
                effective_to=parse_date(request.POST.get("effective_to", "")) or None,
                status=AssessmentPolicy.Status.DRAFT,
            )
            policy.full_clean()

            names = request.POST.getlist("component_name")
            weights = request.POST.getlist("component_weight")
            max_scores = request.POST.getlist("component_max_score")
            required_values = request.POST.getlist("component_required")
            minimum_scores = request.POST.getlist("component_minimum")
            aggregations = request.POST.getlist("component_aggregation")
            rows = []
            for index, name in enumerate(names):
                name = name.strip()
                if not name:
                    continue
                rows.append(AssessmentComponent(
                    policy=policy,
                    name=name,
                    weight=Decimal(weights[index]),
                    max_score=Decimal(max_scores[index]),
                    required=(str(index) in required_values),
                    minimum_score=(
                        Decimal(minimum_scores[index])
                        if minimum_scores[index].strip()
                        else None
                    ),
                    aggregation=aggregations[index],
                ))
            if not rows:
                raise ValidationError("Hãy thêm ít nhất một thành phần đánh giá.")

            with transaction.atomic():
                policy.save()
                for component in rows:
                    component.policy = policy
                    component.full_clean()
                    component.save()
                if request.POST.get("activate") == "yes":
                    policy.status = AssessmentPolicy.Status.ACTIVE
                    policy.save()
        except (InvalidOperation, ValueError, TypeError, IndexError, IntegrityError) as exc:
            messages.error(request, f"Thông tin quy chế chưa hợp lệ: {exc}")
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "Đã tạo quy chế đánh giá và các thành phần.")
            return redirect("assessment_policy_list")

    return render(
        request,
        "core/academics/assessments/policy_form.html",
        {
            "courses": Course.objects.order_by("name"),
            "form_data": form_data,
            **admin_context(request),
        },
    )


@admin_required
def assessment_policy_activate(request, policy_id):
    if request.method == "POST":
        policy = get_object_or_404(AssessmentPolicy, pk=policy_id)
        try:
            policy.status = AssessmentPolicy.Status.ACTIVE
            policy.save()
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "Đã kích hoạt quy chế đánh giá.")
    return redirect("assessment_policy_list")


@admin_required
def assessment_policy_archive(request, policy_id):
    if request.method == "POST":
        policy = get_object_or_404(AssessmentPolicy, pk=policy_id)
        try:
            policy.status = AssessmentPolicy.Status.ARCHIVED
            policy.save()
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "Đã ngừng áp dụng quy chế cho các lớp mới.")
    return redirect("assessment_policy_list")


@academic_required
def assessment_class_list(request):
    keyword = request.GET.get("q", "").strip()

    classes = EnglishClass.objects.select_related(
        "course", "assessment_policy"
    ).order_by("course__name", "name")

    if keyword:
        classes = classes.filter(
            Q(name__icontains=keyword) | Q(course__name__icontains=keyword)
        )

    total_classes = classes.count()
    assigned_count = classes.exclude(assessment_policy=None).count()
    unassigned_count = total_classes - assigned_count

    return render(
        request,
        "core/academics/assessments/classes.html",
        {
            "classes": classes,
            "keyword": keyword,
            "total_classes": total_classes,
            "assigned_count": assigned_count,
            "unassigned_count": unassigned_count,
            **admin_context(request),
        },
    )


@academic_required
def class_assessments(request, class_id):
    english_class = get_object_or_404(
        EnglishClass.objects.select_related("course", "assessment_policy"),
        pk=class_id,
    )
    if request.method == "POST":
        if not request.user.groups.filter(name="Admin").exists() and not request.user.is_superuser:
            messages.error(request, "Chỉ Admin được gán quy chế đánh giá cho lớp.")
            return redirect("class_assessments", class_id=class_id)
        policy = get_object_or_404(
            AssessmentPolicy,
            pk=request.POST.get("policy_id"),
            course=english_class.course,
            status=AssessmentPolicy.Status.ACTIVE,
        )
        policy_changed = english_class.assessment_policy_id != policy.pk
        if policy_changed and english_class.assessment_events.exists():
            messages.error(
                request,
                "Lớp đã có đợt đánh giá. Không thể đổi quy chế giữa chừng; "
                "hãy tạo lớp mới hoặc hoàn tất quy chế hiện tại.",
            )
            return redirect("class_assessments", class_id=class_id)
        with transaction.atomic():
            english_class.assessment_policy = policy
            english_class.save(update_fields=["assessment_policy"])
            enrollment_query = Enrollment.objects.filter(english_class=english_class)
            if not policy_changed:
                enrollment_query.filter(
                    assessment_policy__isnull=True
                ).update(assessment_policy=policy)
            else:
                enrollment_query.update(assessment_policy=policy)
        messages.success(request, "Đã gán quy chế cho lớp.")
        return redirect("class_assessments", class_id=class_id)

    components = (
        english_class.assessment_policy.components.all()
        if english_class.assessment_policy_id
        else AssessmentComponent.objects.none()
    )
    events = (
        english_class.assessment_events.select_related("component")
        .order_by("-assessment_date", "name")
    )
    active_policies = AssessmentPolicy.objects.filter(
        course=english_class.course,
        status=AssessmentPolicy.Status.ACTIVE,
    ).order_by("name", "-version")
    return render(
        request,
        "core/academics/assessments/class_events.html",
        {
            "english_class": english_class,
            "components": components,
            "events": events,
            "active_policies": active_policies,
            **admin_context(request),
        },
    )


@academic_required
def assessment_event_create(request, class_id):
    english_class = get_object_or_404(
        EnglishClass.objects.select_related("assessment_policy"),
        pk=class_id,
    )
    if request.method != "POST":
        return redirect("class_assessments", class_id=class_id)
    if english_class.assessment_policy is None:
        messages.error(request, "Hãy gán quy chế đánh giá cho lớp trước.")
        return redirect("class_assessments", class_id=class_id)

    try:
        component = get_object_or_404(
            AssessmentComponent,
            pk=request.POST.get("component_id"),
            policy=english_class.assessment_policy,
        )
        event = AssessmentEvent(
            english_class=english_class,
            component=component,
            name=request.POST.get("name", "").strip(),
            assessment_date=parse_date(request.POST.get("assessment_date", "")),
            max_score=(
                Decimal(request.POST["max_score"])
                if request.POST.get("max_score", "").strip()
                else None
            ),
            created_by=request.user,
        )
        with transaction.atomic():
            event.full_clean()
            event.save()
            event.participants.set(
                Enrollment.objects.filter(
                    english_class=english_class,
                    status=Enrollment.Status.STUDYING,
                )
            )
    except (InvalidOperation, ValueError, TypeError, ValidationError) as exc:
        messages.error(
            request,
            "Không thể tạo đợt đánh giá: "
            + (" ".join(exc.messages) if isinstance(exc, ValidationError) else str(exc)),
        )
    else:
        messages.success(request, "Đã tạo đợt đánh giá.")
    return redirect("class_assessments", class_id=class_id)


@academic_required
def assessment_event_gradebook(request, event_id):
    event = get_object_or_404(
        AssessmentEvent.objects.select_related(
            "english_class", "component", "component__policy"
        ),
        pk=event_id,
    )
    enrollments = (
        event.participants.select_related("student")
        .order_by("student__full_name")
    )

    if request.method == "POST":
        try:
            enrollment_id = int(request.POST.get("enrollment_id", ""))
            enrollment = get_object_or_404(
                enrollments,
                pk=enrollment_id,
            )
            status = request.POST.get("status", AssessmentResult.Status.GRADED)
            raw_score = request.POST.get("score", "").strip()
            score = Decimal(raw_score) if raw_score else None
            record_assessment_result(
                enrollment_id=enrollment.pk,
                event_id=event.pk,
                actor=request.user,
                status=status,
                score=score,
                attempt_number=int(request.POST.get("attempt_number", "1")),
                feedback=request.POST.get("feedback", ""),
                reason=request.POST.get("reason", ""),
            )
        except (InvalidOperation, ValueError, TypeError) as exc:
            messages.error(request, f"Dữ liệu điểm không hợp lệ: {exc}")
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "Đã lưu kết quả và cập nhật tổng kết.")
        return redirect("assessment_event_gradebook", event_id=event.pk)

    results_by_enrollment = {}
    for result in AssessmentResult.objects.filter(event=event).order_by(
        "attempt_number"
    ):
        results_by_enrollment.setdefault(result.enrollment_id, []).append(result)
    final_results = {
        result.enrollment_id: result
        for result in FinalResult.objects.filter(enrollment__in=enrollments)
    }
    grade_rows = []
    for enrollment in enrollments:
        attempts = results_by_enrollment.get(enrollment.pk, [])
        grade_rows.append({
            "enrollment": enrollment,
            "attempts": attempts,
            "next_attempt": max(
                (result.attempt_number for result in attempts),
                default=0,
            ) + 1,
            "final_result": final_results.get(enrollment.pk),
        })
    return render(
        request,
        "core/academics/assessments/gradebook.html",
        {
            "event": event,
            "grade_rows": grade_rows,
            "result_statuses": AssessmentResult.Status.choices,
            "maximum_score": event.max_score or event.component.max_score,
            **admin_context(request),
        },
    )
