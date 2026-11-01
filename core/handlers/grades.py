from decimal import Decimal, InvalidOperation

from django.utils.dateparse import parse_date
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Student, EnglishClass, Grade
from ..permissions import admin_required, academic_required, admin_context


def save_grade_from_post(request, grade=None):
    student_id = request.POST.get("student")
    class_id = request.POST.get("english_class")

    try:
        student = Student.objects.get(pk=student_id)
        english_class = EnglishClass.objects.get(pk=class_id)

    except (
        Student.DoesNotExist,
        EnglishClass.DoesNotExist,
        ValueError,
        TypeError,
    ):
        return None, "Vui lòng chọn học viên và lớp học hợp lệ."

    if not english_class.students.filter(pk=student.pk).exists():
        english_class.students.add(student)

    score_fields = [
        "oral_score",
        "listening_score",
        "reading_score",
        "writing_score",
    ]

    scores = {}

    for field in score_fields:
        raw_value = request.POST.get(field, "").strip()

        try:
            score = Decimal(raw_value)

        except (InvalidOperation, ValueError):
            return None, (
                "Vui lòng nhập đầy đủ điểm hợp lệ cho cả 4 kỹ năng."
            )

        if not score.is_finite() or score < 0 or score > 10:
            return None, (
                "Điểm của mỗi kỹ năng phải nằm trong khoảng từ 0 đến 10."
            )

        if score.as_tuple().exponent < -2:
            return None, (
                "Điểm chỉ được nhập tối đa 2 chữ số thập phân."
            )

        scores[field] = score

    exam_date = parse_date(request.POST.get("exam_date", ""))

    if not exam_date:
        return None, "Vui lòng chọn ngày kiểm tra hợp lệ."

    data = {
        "student": student,
        "english_class": english_class,
        "exam_date": exam_date,
        "note": request.POST.get("note", "").strip(),
        **scores,
    }

    if grade is None:
        grade = Grade(**data)
    else:
        for field, value in data.items():
            setattr(grade, field, value)

    grade.save()
    
    # Đồng bộ sang hệ thống quy chế đánh giá & FinalResult
    try:
        from ..services.grading import sync_grade_to_assessment
        actor = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        sync_grade_to_assessment(grade, actor=actor)
    except Exception:
        pass

    return grade, None


@academic_required
def grade_list(request):
    keyword = request.GET.get("q", "").strip()
    class_id = request.GET.get("class_id", "").strip()

    grades = Grade.objects.select_related(
        "student",
        "english_class",
        "english_class__course",
    ).all().order_by("-exam_date", "-id")

    if keyword:
        grades = grades.filter(
            Q(student__full_name__icontains=keyword)
            | Q(english_class__name__icontains=keyword)
        )

    if class_id:
        grades = grades.filter(english_class_id=class_id)

    total_count = grades.count()
    grades_list = list(grades)

    avg_score = 0.0
    passed_count = 0
    max_score = 0.0

    if total_count > 0:
        scores = [float(g.average_score) for g in grades_list]
        avg_score = round(sum(scores) / total_count, 1)
        passed_count = sum(1 for s in scores if s >= 5.0)
        max_score = max(scores)

    classes = EnglishClass.objects.all().order_by("name")

    from django.core.paginator import Paginator
    paginator = Paginator(grades, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "core/grades/list.html", {
        "page_obj": page_obj,
        "grades": page_obj,
        "keyword": keyword,
        "selected_class_id": class_id,
        "classes": classes,
        "total_count": total_count,
        "avg_score": avg_score,
        "passed_count": passed_count,
        "max_score": max_score,
        **admin_context(request),
    })


@academic_required
def grade_add(request):
    if request.method == "POST":
        grade, error = save_grade_from_post(request)

        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Thêm điểm thành công!")
            return redirect("grade_list")

    students = Student.objects.all().order_by("full_name")

    classes = EnglishClass.objects.select_related(
        "course"
    ).all().order_by("name")

    return render(request, "core/grades/add.html", {
        "students": students,
        "classes": classes,
        "form_data": (
            request.POST if request.method == "POST" else {}
        ),
        **admin_context(request),
    })


@academic_required
def grade_edit(request, grade_id):
    grade = get_object_or_404(Grade, pk=grade_id)

    if request.method == "POST":
        updated_grade, error = save_grade_from_post(request, grade)

        if error:
            messages.error(request, error)
        else:
            messages.success(request, "Cập nhật điểm thành công!")
            return redirect("grade_list")

    students = Student.objects.all().order_by("full_name")

    classes = EnglishClass.objects.select_related(
        "course"
    ).all().order_by("name")

    return render(request, "core/grades/edit.html", {
        "grade": grade,
        "classes": classes,
        "students": students,
        "form_data": (
            request.POST if request.method == "POST" else {}
        ),
        **admin_context(request),
    })


@admin_required
def grade_delete(request, grade_id):
    grade = get_object_or_404(Grade, pk=grade_id)

    if request.method == "POST":
        grade.delete()
        messages.success(request, "Xóa điểm thành công!")
        return redirect("grade_list")

    return render(request, "core/grades/delete.html", {
        "grade": grade,
        **admin_context(request),
    })
