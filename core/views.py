
from decimal import Decimal, InvalidOperation
from datetime import date
from functools import wraps

from django.utils.dateparse import parse_date
from django.db import models
from django.db.models import Avg, Q, Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    Student,
    Course,
    EnglishClass,
    Teacher,
    Grade,
    Tuition,
    Certificate,
)

# Tích hợp Blockchain xác minh chứng chỉ
from .blockchain.blockchain_service import (
    issue_database_certificate,
    verify_database_certificate,
)


# ==================================================
# PHÂN QUYỀN ADMIN VÀ NHÂN VIÊN
# ==================================================

def is_admin_user(user):
    """Kiểm tra người dùng có quyền Admin hay không."""
    if not user.is_authenticated:
        return False

    return (
        user.is_superuser
        or user.groups.filter(name="Admin").exists()
    )


def admin_required(view_func):
    """Chỉ Admin mới được thực hiện chức năng được bảo vệ."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_admin_user(request.user):
            messages.error(
                request,
                "Bạn không có quyền thực hiện chức năng này."
            )
            return redirect("home")

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_context(request):
    """Dữ liệu phân quyền dùng cho giao diện."""
    return {
        "is_admin": is_admin_user(request.user),
    }


# ==================================================
# TRANG CHỦ
# ==================================================

@login_required
def home(request):
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_courses = Course.objects.count()
    total_classes = EnglishClass.objects.count()
    total_grades = Grade.objects.count()

    class_statistics = EnglishClass.objects.annotate(
        student_count=models.Count("students")
    ).order_by("name")

    if total_grades:
        scores = Grade.objects.aggregate(
            oral=Avg("oral_score"),
            listening=Avg("listening_score"),
            reading=Avg("reading_score"),
            writing=Avg("writing_score"),
        )

        average_score = round(
            sum(
                (scores[field] or 0)
                for field in [
                    "oral",
                    "listening",
                    "reading",
                    "writing",
                ]
            ) / 4,
            2,
        )
    else:
        average_score = 0

    tuition_statistics = Tuition.objects.aggregate(
        total_fee=Sum("total_fee"),
        total_paid=Sum("paid_amount"),
    )

    total_fee = (
        tuition_statistics["total_fee"]
        or Decimal("0")
    )

    total_paid = (
        tuition_statistics["total_paid"]
        or Decimal("0")
    )

    total_debt = total_fee - total_paid

    context = {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_courses": total_courses,
        "total_classes": total_classes,
        "total_grades": total_grades,
        "class_statistics": class_statistics,
        "average_score": average_score,
        "total_fee": total_fee,
        "total_paid": total_paid,
        "total_debt": total_debt,
        **admin_context(request),
    }

    return render(request, "core/home.html", context)


# ==================================================
# QUẢN LÝ HỌC VIÊN
# ==================================================

@login_required
def student_list(request):
    keyword = request.GET.get("q", "").strip()

    students = Student.objects.all()

    if keyword:
        students = students.filter(
            Q(full_name__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(phone__icontains=keyword)
        )

    students = students.order_by("id")

    context = {
        "students": students,
        "keyword": keyword,
        **admin_context(request),
    }

    return render(request, "core/student_list.html", context)


@login_required
def student_add(request):
    if request.method == "POST":
        full_name = (
            request.POST.get("full_name")
            or request.POST.get("name", "")
        ).strip()

        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        date_of_birth = request.POST.get("date_of_birth") or None
        address = request.POST.get("address", "").strip()

        if not full_name or not email or not phone:
            messages.error(
                request,
                "Vui lòng nhập họ tên, email và số điện thoại."
            )

        elif Student.objects.filter(email=email).exists():
            messages.error(request, "Email này đã được sử dụng.")

        else:
            Student.objects.create(
                full_name=full_name,
                email=email,
                phone=phone,
                date_of_birth=date_of_birth,
                address=address,
            )

            messages.success(request, "Thêm học viên thành công!")
            return redirect("student_list")

    return render(
        request,
        "core/student_add.html",
        admin_context(request),
    )


@login_required
def student_edit(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        full_name = (
            request.POST.get("full_name")
            or request.POST.get("name", "")
        ).strip()

        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        date_of_birth = request.POST.get("date_of_birth") or None
        address = request.POST.get("address", "").strip()

        if not full_name or not email or not phone:
            messages.error(
                request,
                "Vui lòng nhập họ tên, email và số điện thoại."
            )

        elif Student.objects.filter(
            email=email
        ).exclude(id=student.id).exists():
            messages.error(request, "Email này đã được sử dụng.")

        else:
            student.full_name = full_name
            student.email = email
            student.phone = phone
            student.date_of_birth = date_of_birth
            student.address = address
            student.save()

            messages.success(
                request,
                "Cập nhật học viên thành công!"
            )
            return redirect("student_list")

    context = {
        "student": student,
        **admin_context(request),
    }

    return render(request, "core/student_edit.html", context)


@admin_required
def student_delete(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        student.delete()
        messages.success(request, "Xóa học viên thành công!")
        return redirect("student_list")

    return render(request, "core/student_delete.html", {
        "student": student,
        **admin_context(request),
    })


# ==================================================
# QUẢN LÝ KHÓA HỌC
# ==================================================

@login_required
def course_list(request):
    """Hiển thị danh sách khóa học."""

    keyword = request.GET.get("q", "").strip()

    courses = Course.objects.all().order_by("id")

    if keyword:
        courses = courses.filter(
            Q(name__icontains=keyword)
            | Q(description__icontains=keyword)
        )

    return render(request, "core/course_list.html", {
        "courses": courses,
        "keyword": keyword,
        **admin_context(request),
    })


@admin_required
def course_add(request):
    """Thêm khóa học."""

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        tuition_raw = request.POST.get("tuition", "").strip()
        duration_raw = request.POST.get("duration", "").strip()

        if not name:
            messages.error(request, "Vui lòng nhập tên khóa học.")

        elif not tuition_raw or not duration_raw:
            messages.error(
                request,
                "Vui lòng nhập học phí và thời lượng khóa học."
            )

        else:
            try:
                tuition = Decimal(tuition_raw)
                duration = int(duration_raw)

                if (
                    not tuition.is_finite()
                    or tuition < 0
                    or tuition > Decimal("999999999999")
                ):
                    raise ValueError

                if duration < 1 or duration > 1200:
                    raise ValueError

                Course.objects.create(
                    name=name,
                    description=description,
                    tuition=tuition,
                    duration=duration,
                )

                messages.success(
                    request,
                    "Thêm khóa học thành công!"
                )
                return redirect("course_list")

            except (InvalidOperation, ValueError, TypeError):
                messages.error(
                    request,
                    "Học phí hoặc thời lượng không hợp lệ."
                )

    return render(request, "core/course_add.html", {
        **admin_context(request),
    })


@admin_required
def course_edit(request, course_id):
    """Cập nhật khóa học."""

    course = get_object_or_404(Course, pk=course_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        tuition_raw = request.POST.get("tuition", "").strip()
        duration_raw = request.POST.get("duration", "").strip()

        if not name:
            messages.error(request, "Vui lòng nhập tên khóa học.")

        elif not tuition_raw or not duration_raw:
            messages.error(
                request,
                "Vui lòng nhập học phí và thời lượng khóa học."
            )

        else:
            try:
                tuition = Decimal(tuition_raw)
                duration = int(duration_raw)

                if (
                    not tuition.is_finite()
                    or tuition < 0
                    or tuition > Decimal("999999999999")
                ):
                    raise ValueError

                if duration < 1 or duration > 1200:
                    raise ValueError

                course.name = name
                course.description = description
                course.tuition = tuition
                course.duration = duration
                course.save()

                messages.success(
                    request,
                    "Cập nhật khóa học thành công!"
                )
                return redirect("course_list")

            except (InvalidOperation, ValueError, TypeError):
                messages.error(
                    request,
                    "Học phí hoặc thời lượng không hợp lệ."
                )

    return render(request, "core/course_edit.html", {
        "course": course,
        **admin_context(request),
    })


@admin_required
def course_delete(request, course_id):
    """Chỉ Admin được xóa khóa học."""

    course = get_object_or_404(Course, pk=course_id)

    if request.method == "POST":
        course.delete()
        messages.success(request, "Xóa khóa học thành công!")
        return redirect("course_list")

    return render(request, "core/course_delete.html", {
        "course": course,
        **admin_context(request),
    })


# ==================================================
# QUẢN LÝ LỚP HỌC
# ==================================================

@login_required
def class_list(request):
    classes = (
        EnglishClass.objects
        .select_related("course", "teacher")
        .prefetch_related("students")
        .order_by("id")
    )

    return render(request, "core/class_list.html", {
        "classes": classes,
        **admin_context(request),
    })


@login_required
def class_add(request):
    courses = Course.objects.all().order_by("name")
    teachers = Teacher.objects.all().order_by("full_name")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        course_id = request.POST.get("course")
        teacher_id = request.POST.get("teacher")
        start_date_raw = request.POST.get("start_date")
        end_date_raw = request.POST.get("end_date") or None
        max_students_raw = request.POST.get("max_students", "20")

        if not name or not course_id or not start_date_raw:
            messages.error(
                request,
                "Vui lòng nhập tên lớp, khóa học và ngày bắt đầu."
            )
        else:
            try:
                start_date = parse_date(start_date_raw)
                end_date = (
                    parse_date(end_date_raw)
                    if end_date_raw else None
                )
                max_students = int(max_students_raw)

                if not start_date:
                    raise ValueError

                if end_date_raw and not end_date:
                    raise ValueError

                if max_students < 1:
                    raise ValueError

                course = get_object_or_404(Course, id=course_id)

                teacher = (
                    get_object_or_404(Teacher, id=teacher_id)
                    if teacher_id else None
                )

                if end_date and end_date < start_date:
                    messages.error(
                        request,
                        "Ngày kết thúc phải bằng hoặc sau ngày bắt đầu."
                    )
                else:
                    EnglishClass.objects.create(
                        name=name,
                        course=course,
                        teacher=teacher,
                        teacher_name=(
                            teacher.full_name if teacher else ""
                        ),
                        start_date=start_date,
                        end_date=end_date,
                        max_students=max_students,
                    )

                    messages.success(
                        request,
                        "Thêm lớp học thành công!"
                    )
                    return redirect("class_list")

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Ngày tháng hoặc sĩ số không hợp lệ. "
                    "Sĩ số phải là số nguyên lớn hơn 0."
                )

    return render(request, "core/class_add.html", {
        "courses": courses,
        "teachers": teachers,
        **admin_context(request),
    })


@login_required
def class_edit(request, class_id):
    english_class = get_object_or_404(
        EnglishClass,
        id=class_id,
    )
    courses = Course.objects.all().order_by("name")
    teachers = Teacher.objects.all().order_by("full_name")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        course_id = request.POST.get("course")
        teacher_id = request.POST.get("teacher")
        start_date_raw = request.POST.get("start_date")
        end_date_raw = request.POST.get("end_date") or None
        max_students_raw = request.POST.get("max_students", "20")

        if not name or not course_id or not start_date_raw:
            messages.error(
                request,
                "Vui lòng nhập tên lớp, khóa học và ngày bắt đầu."
            )
        else:
            try:
                start_date = parse_date(start_date_raw)
                end_date = (
                    parse_date(end_date_raw)
                    if end_date_raw else None
                )
                max_students = int(max_students_raw)

                if not start_date:
                    raise ValueError

                if end_date_raw and not end_date:
                    raise ValueError

                if max_students < 1:
                    raise ValueError

                course = get_object_or_404(Course, id=course_id)

                teacher = (
                    get_object_or_404(Teacher, id=teacher_id)
                    if teacher_id else None
                )

                if end_date and end_date < start_date:
                    messages.error(
                        request,
                        "Ngày kết thúc phải bằng hoặc sau ngày bắt đầu."
                    )

                elif (
                    english_class.students.count() > max_students
                ):
                    messages.error(
                        request,
                        "Sĩ số tối đa không được nhỏ hơn "
                        "số học viên hiện tại."
                    )

                else:
                    english_class.name = name
                    english_class.course = course
                    english_class.teacher = teacher
                    english_class.teacher_name = (
                        teacher.full_name if teacher else ""
                    )
                    english_class.start_date = start_date
                    english_class.end_date = end_date
                    english_class.max_students = max_students
                    english_class.save()

                    messages.success(
                        request,
                        "Cập nhật lớp học thành công!"
                    )
                    return redirect("class_list")

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Ngày tháng hoặc sĩ số không hợp lệ. "
                    "Sĩ số phải là số nguyên lớn hơn 0."
                )

    return render(request, "core/class_edit.html", {
        "english_class": english_class,
        "courses": courses,
        "teachers": teachers,
        **admin_context(request),
    })


@login_required
def class_detail(request, class_id):
    english_class = get_object_or_404(
        EnglishClass.objects.select_related("course", "teacher"),
        pk=class_id,
    )

    if request.method == "POST":
        student_id = request.POST.get("student_id")

        if not student_id:
            messages.error(request, "Vui lòng chọn học viên.")
            return redirect("class_detail", class_id=class_id)

        student = get_object_or_404(Student, pk=student_id)

        if english_class.students.filter(pk=student.pk).exists():
            messages.warning(
                request,
                "Học viên này đã được đăng ký vào lớp."
            )

        elif (
            english_class.students.count()
            >= english_class.max_students
        ):
            messages.error(
                request,
                "Lớp học đã đủ sĩ số. "
                "Vui lòng tăng sĩ số tối đa của lớp."
            )

        else:
            english_class.students.add(student)
            messages.success(
                request,
                f"Đăng ký học viên {student.full_name} "
                "vào lớp thành công!"
            )

        return redirect("class_detail", class_id=class_id)

    students = english_class.students.all().order_by("full_name")

    available_students = (
        Student.objects
        .exclude(english_classes=english_class)
        .order_by("full_name")
    )

    return render(request, "core/class_detail.html", {
        "english_class": english_class,
        "students": students,
        "available_students": available_students,
        **admin_context(request),
    })


@admin_required
def student_remove_from_class(request, class_id, student_id):
    english_class = get_object_or_404(EnglishClass, id=class_id)
    student = get_object_or_404(Student, id=student_id)

    if request.method != "POST":
        return redirect("class_detail", class_id=class_id)

    if english_class.students.filter(id=student.id).exists():
        english_class.students.remove(student)
        messages.success(
            request,
            f"Đã hủy đăng ký học viên {student.full_name} khỏi lớp."
        )
    else:
        messages.warning(request, "Học viên không thuộc lớp này.")

    return redirect("class_detail", class_id=class_id)


# ==================================================
# QUẢN LÝ GIÁO VIÊN
# ==================================================

@login_required
def teacher_list(request):
    keyword = request.GET.get("q", "").strip()
    teachers = Teacher.objects.all()

    if keyword:
        teachers = teachers.filter(
            Q(full_name__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(phone__icontains=keyword)
        )

    return render(request, "core/teacher_list.html", {
        "teachers": teachers.order_by("id"),
        "keyword": keyword,
        **admin_context(request),
    })


@login_required
def teacher_add(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        specialization = request.POST.get(
            "specialization", ""
        ).strip()
        address = request.POST.get("address", "").strip()

        if not full_name or not email or not phone:
            messages.error(
                request,
                "Vui lòng nhập họ tên, email và số điện thoại."
            )

        elif Teacher.objects.filter(email=email).exists():
            messages.error(request, "Email này đã được sử dụng.")

        else:
            Teacher.objects.create(
                full_name=full_name,
                email=email,
                phone=phone,
                specialization=specialization,
                address=address,
            )

            messages.success(request, "Thêm giáo viên thành công!")
            return redirect("teacher_list")

    return render(
        request,
        "core/teacher_add.html",
        admin_context(request),
    )


@login_required
def teacher_edit(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        specialization = request.POST.get(
            "specialization", ""
        ).strip()
        address = request.POST.get("address", "").strip()

        if not full_name or not email or not phone:
            messages.error(
                request,
                "Vui lòng nhập họ tên, email và số điện thoại."
            )

        elif Teacher.objects.filter(
            email=email
        ).exclude(id=teacher.id).exists():
            messages.error(request, "Email này đã được sử dụng.")

        else:
            teacher.full_name = full_name
            teacher.email = email
            teacher.phone = phone
            teacher.specialization = specialization
            teacher.address = address
            teacher.save()

            messages.success(
                request,
                "Cập nhật giáo viên thành công!"
            )
            return redirect("teacher_list")

    return render(request, "core/teacher_edit.html", {
        "teacher": teacher,
        **admin_context(request),
    })


@admin_required
def teacher_delete(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == "POST":
        teacher.delete()
        messages.success(request, "Xóa giáo viên thành công!")
        return redirect("teacher_list")

    return render(request, "core/teacher_delete.html", {
        "teacher": teacher,
        **admin_context(request),
    })


# ==================================================
# QUẢN LÝ ĐIỂM SỐ
# ==================================================

@login_required
def grade_list(request):
    keyword = request.GET.get("q", "").strip()

    grades = Grade.objects.select_related(
        "student",
        "english_class",
        "english_class__course",
    ).all()

    if keyword:
        grades = grades.filter(
            Q(student__full_name__icontains=keyword)
            | Q(english_class__name__icontains=keyword)
        )

    return render(request, "core/grade_list.html", {
        "grades": grades,
        "keyword": keyword,
        **admin_context(request),
    })


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
        return None, (
            f"Học viên {student.full_name} chưa được ghi danh vào lớp "
            f"{english_class.name}. Vui lòng ghi danh trước khi nhập điểm."
        )

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
    return grade, None


@login_required
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

    return render(request, "core/grade_add.html", {
        "students": students,
        "classes": classes,
        "form_data": (
            request.POST if request.method == "POST" else {}
        ),
        **admin_context(request),
    })


@login_required
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

    return render(request, "core/grade_edit.html", {
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

    return render(request, "core/grade_delete.html", {
        "grade": grade,
        **admin_context(request),
    })


# ==================================================
# QUẢN LÝ HỌC PHÍ
# ==================================================

@login_required
def tuition_list(request):
    tuitions = Tuition.objects.select_related(
        "student",
        "english_class",
        "english_class__course",
    ).all()

    keyword = request.GET.get("q", "").strip()

    if keyword:
        tuitions = tuitions.filter(
            Q(student__full_name__icontains=keyword)
            | Q(english_class__name__icontains=keyword)
        )

    total_fee = (
        tuitions.aggregate(total=Sum("total_fee"))["total"]
        or Decimal("0")
    )

    total_paid = (
        tuitions.aggregate(total=Sum("paid_amount"))["total"]
        or Decimal("0")
    )

    total_debt = sum(
        (item.remaining_amount for item in tuitions),
        Decimal("0"),
    )

    context = {
        "tuitions": tuitions,
        "keyword": keyword,
        "total_fee": total_fee,
        "total_paid": total_paid,
        "total_debt": total_debt,
        **admin_context(request),
    }

    return render(request, "core/tuition_list.html", context)


@login_required
def tuition_add(request):
    students = Student.objects.all().order_by("full_name")

    classes = EnglishClass.objects.select_related(
        "course"
    ).all().order_by("name")

    if request.method == "POST":
        student_id = request.POST.get("student")
        class_id = request.POST.get("english_class")
        paid_amount_raw = request.POST.get(
            "paid_amount", "0"
        ).strip()
        payment_date_raw = request.POST.get("payment_date") or None
        note = request.POST.get("note", "").strip()

        try:
            student = Student.objects.get(pk=student_id)

            english_class = EnglishClass.objects.select_related(
                "course"
            ).get(pk=class_id)

            if not english_class.students.filter(pk=student.pk).exists():
                messages.error(
                    request,
                    "Học viên chưa đăng ký vào lớp này."
                )
                return redirect("tuition_add")

            paid_amount = Decimal(paid_amount_raw)

            if not paid_amount.is_finite() or paid_amount < 0:
                raise ValueError

            if paid_amount > english_class.course.tuition:
                messages.error(
                    request,
                    "Số tiền đã đóng không được lớn hơn học phí khóa học."
                )
                return redirect("tuition_add")

            payment_date = (
                parse_date(payment_date_raw)
                if payment_date_raw else None
            )

            if payment_date_raw and not payment_date:
                messages.error(
                    request,
                    "Ngày thanh toán không hợp lệ."
                )
                return redirect("tuition_add")

            Tuition.objects.create(
                student=student,
                english_class=english_class,
                total_fee=english_class.course.tuition,
                paid_amount=paid_amount,
                payment_date=payment_date,
                note=note,
            )

            messages.success(
                request,
                "Tạo phiếu học phí thành công!"
            )
            return redirect("tuition_list")

        except (Student.DoesNotExist, EnglishClass.DoesNotExist):
            messages.error(
                request,
                "Học viên hoặc lớp học không tồn tại."
            )

        except (InvalidOperation, ValueError, TypeError):
            messages.error(
                request,
                "Số tiền đã đóng không hợp lệ."
            )

    return render(request, "core/tuition_add.html", {
        "students": students,
        "classes": classes,
        "today": date.today().isoformat(),
        **admin_context(request),
    })


@login_required
def tuition_edit(request, tuition_id):
    tuition = get_object_or_404(
        Tuition.objects.select_related(
            "student",
            "english_class__course",
        ),
        pk=tuition_id,
    )

    if request.method == "POST":
        paid_amount_raw = request.POST.get(
            "paid_amount", ""
        ).strip()
        payment_date_raw = request.POST.get("payment_date") or None
        note = request.POST.get("note", "").strip()

        try:
            paid_amount = Decimal(paid_amount_raw)

            if not paid_amount.is_finite() or paid_amount < 0:
                raise ValueError

            if paid_amount > tuition.total_fee:
                messages.error(
                    request,
                    "Số tiền đã đóng không được lớn hơn tổng học phí."
                )
                return redirect(
                    "tuition_edit",
                    tuition_id=tuition.id,
                )

            payment_date = (
                parse_date(payment_date_raw)
                if payment_date_raw else None
            )

            if payment_date_raw and not payment_date:
                messages.error(
                    request,
                    "Ngày thanh toán không hợp lệ."
                )
                return redirect(
                    "tuition_edit",
                    tuition_id=tuition.id,
                )

            tuition.paid_amount = paid_amount
            tuition.payment_date = payment_date
            tuition.note = note
            tuition.save()

            messages.success(
                request,
                "Cập nhật phiếu học phí thành công!"
            )
            return redirect("tuition_list")

        except (InvalidOperation, ValueError, TypeError):
            messages.error(
                request,
                "Số tiền đã đóng không hợp lệ."
            )

    return render(request, "core/tuition_edit.html", {
        "tuition": tuition,
        "today": date.today().isoformat(),
        **admin_context(request),
    })


@admin_required
def tuition_delete(request, tuition_id):
    if request.method != "POST":
        return redirect("tuition_list")

    tuition = get_object_or_404(Tuition, pk=tuition_id)
    tuition.delete()

    messages.success(request, "Xóa phiếu học phí thành công!")
    return redirect("tuition_list")


# ==================================================
# QUẢN LÝ CHỨNG CHỈ BLOCKCHAIN
# ==================================================

@login_required
def certificate_list(request):
    """Hiển thị danh sách chứng chỉ và trạng thái Blockchain."""

    keyword = request.GET.get("q", "").strip()

    certificates = (
        Certificate.objects
        .select_related(
            "student",
            "english_class",
            "english_class__course",
        )
        .all()
        .order_by("-id")
    )

    if keyword:
        certificates = certificates.filter(
            Q(certificate_code__icontains=keyword)
            | Q(student__full_name__icontains=keyword)
            | Q(english_class__name__icontains=keyword)
        )

    context = {
        "certificates": certificates,
        "keyword": keyword,
        **admin_context(request),
    }

    return render(
        request,
        "core/certificate_list.html",
        context,
    )


@admin_required
def certificate_issue(request, certificate_id):
    """Cấp chứng chỉ lên Blockchain."""

    if request.method != "POST":
        return redirect("certificate_list")

    certificate = get_object_or_404(
        Certificate,
        pk=certificate_id,
    )

    if certificate.blockchain_status == "issued":
        messages.warning(
            request,
            "Chứng chỉ này đã được cấp trên Blockchain."
        )
        return redirect("certificate_list")

    try:
        result = issue_database_certificate(certificate)

        if result.get("status") == "success":
            messages.success(
                request,
                f"Cấp chứng chỉ {certificate.certificate_code} "
                f"thành công. Block: {result.get('block_number')}."
            )
        else:
            messages.error(
                request,
                "Chưa xác nhận được giao dịch Blockchain thành công."
            )

    except Exception as exc:
        messages.error(
            request,
            "Không thể cấp chứng chỉ Blockchain. "
            f"Chi tiết: {exc}. "
            "Hãy kiểm tra Ganache và cấu hình smart contract."
        )

    return redirect("certificate_list")


@login_required
def certificate_verify(request):
    """Xác minh chứng chỉ trên Blockchain."""

    result = None
    certificate_code = ""

    if request.method == "POST":
        certificate_code = request.POST.get(
            "certificate_code",
            "",
        ).strip()

        if not certificate_code:
            messages.error(
                request,
                "Vui lòng nhập mã chứng chỉ cần xác minh."
            )
        else:
            certificate = Certificate.objects.filter(
                certificate_code=certificate_code,
            ).first()

            if certificate is None:
                result = {
                    "valid": False,
                    "message": (
                        "Không tìm thấy chứng chỉ trong hệ thống."
                    ),
                    "certificate_code": certificate_code,
                }
            else:
                try:
                    result = verify_database_certificate(
                        certificate
                    )

                except Exception:
                    result = {
                        "valid": False,
                        "message": (
                            "Không thể xác minh Blockchain. "
                            "Vui lòng kiểm tra Ganache, RPC "
                            "và cấu hình smart contract."
                        ),
                        "certificate_code": certificate_code,
                    }

    context = {
        "result": result,
        "certificate_code": certificate_code,
        **admin_context(request),
    }

    return render(
        request,
        "core/certificate_verify.html",
        context,
    )
