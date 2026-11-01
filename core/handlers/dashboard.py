from decimal import Decimal

from django.db import models
from django.db.models import Avg, Sum
from django.shortcuts import render
from django.utils import timezone

from ..models import Student, Course, EnglishClass, Teacher, Grade, Tuition
from ..permissions import admin_context, staff_required


@staff_required
def home(request):
    permissions = admin_context(request)
    context = {**permissions}

    if permissions["can_manage_academics"]:
        total_grades = Grade.objects.count()
        context.update({
            "total_students": Student.objects.count(),
            "total_teachers": Teacher.objects.count(),
            "total_courses": Course.objects.count(),
            "total_classes": EnglishClass.objects.count(),
            "total_grades": total_grades,
            "class_statistics": EnglishClass.objects.filter(
                is_active=True
            ).select_related(
                "course", "teacher"
            ).annotate(
                student_count=models.Count("students")
            ).order_by("name"),
            "recent_students": Student.objects.filter(is_active=True).order_by("-id")[:5],
            "average_score": 0,
        })

        if total_grades:
            scores = Grade.objects.aggregate(
                oral=Avg("oral_score"),
                listening=Avg("listening_score"),
                reading=Avg("reading_score"),
                writing=Avg("writing_score"),
            )
            context["average_score"] = round(
                sum((scores[field] or 0) for field in (
                    "oral", "listening", "reading", "writing"
                )) / 4,
                2,
            )

        # Thống kê phân bổ học viên theo từng khóa học
        course_stats = list(
            Course.objects.annotate(
                student_count=models.Count("classes__students", distinct=True)
            ).order_by("-student_count", "name")
        )
        active_courses = [c for c in course_stats if c.student_count > 0]
        if not active_courses:
            active_courses = course_stats[:6]

        context["course_labels"] = [c.name for c in active_courses]
        context["course_student_counts"] = [c.student_count for c in active_courses]
        context["course_distribution"] = active_courses

    if permissions["can_manage_finance"]:
        tuition_statistics = Tuition.objects.aggregate(
            total_fee=Sum("total_fee"),
            total_paid=Sum("paid_amount"),
        )
        total_fee = tuition_statistics["total_fee"] or Decimal("0")
        total_paid = tuition_statistics["total_paid"] or Decimal("0")
        context.update({
            "total_fee": total_fee,
            "total_paid": total_paid,
            "total_debt": total_fee - total_paid,
        })

        # Thống kê doanh thu học phí theo 6 tháng gần nhất
        today = timezone.localdate()
        monthly_labels = []
        monthly_paid = []
        monthly_expected = []

        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            month_label = f"T{m:02d}/{y}"
            monthly_labels.append(month_label)

            paid_sum = Tuition.objects.filter(
                payment_date__year=y,
                payment_date__month=m,
            ).aggregate(s=Sum("paid_amount"))["s"] or Decimal("0")

            fee_sum = Tuition.objects.filter(
                created_at__year=y,
                created_at__month=m,
            ).aggregate(s=Sum("total_fee"))["s"] or Decimal("0")

            if paid_sum == 0:
                paid_sum = Tuition.objects.filter(
                    created_at__year=y,
                    created_at__month=m,
                ).aggregate(s=Sum("paid_amount"))["s"] or Decimal("0")

            monthly_paid.append(float(paid_sum))
            monthly_expected.append(float(fee_sum or paid_sum))

        context["monthly_labels"] = monthly_labels
        context["monthly_paid"] = monthly_paid
        context["monthly_expected"] = monthly_expected

    return render(request, "core/dashboard/home.html", context)

