from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError

from ..services.class_transfers import request_class_transfer

from ..models import ClassTransfer, Course, EnglishClass, Enrollment, Student, Teacher
from ..permissions import admin_required, academic_required, admin_context


@academic_required
def course_list(request):
    """Hiển thị danh sách khóa học."""

    keyword = request.GET.get("q", "").strip()

    courses = Course.objects.filter(is_active=True).order_by("id")

    if keyword:
        courses = courses.filter(
            Q(name__icontains=keyword)
            | Q(description__icontains=keyword)
        )

    from django.core.paginator import Paginator
    paginator = Paginator(courses, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "core/academics/courses/list.html", {
        "page_obj": page_obj,
        "courses": page_obj,
        "keyword": keyword,
        **admin_context(request),
    })


@academic_required
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

    return render(request, "core/academics/courses/add.html", {
        **admin_context(request),
    })


@academic_required
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

    return render(request, "core/academics/courses/edit.html", {
        "course": course,
        **admin_context(request),
    })


@admin_required
def course_delete(request, course_id):
    """Chỉ Admin được xóa / lưu trữ khóa học."""

    course = get_object_or_404(Course, pk=course_id)

    if request.method == "POST":
        action = request.POST.get("action", "archive")
        if action == "restore":
            course.is_active = True
            course.save(update_fields=["is_active"])
            messages.success(request, f"Đã khôi phục khóa học '{course.name}' hoạt động trở lại.")
        else:
            course.is_active = False
            course.save(update_fields=["is_active"])
            messages.success(request, f"Đã lưu trữ khóa học '{course.name}'. Toàn bộ lớp học và lịch sử học phí được bảo toàn nguyên vẹn.")
        return redirect("course_list")

    return render(request, "core/academics/courses/delete.html", {
        "course": course,
        **admin_context(request),
    })


@academic_required
def class_list(request):
    keyword = request.GET.get("q", "").strip()
    course_id = request.GET.get("course_id", "").strip()

    classes = (
        EnglishClass.objects
        .filter(is_active=True)
        .select_related("course", "teacher")
        .annotate(
            active_student_count=Count(
                "enrollments",
                filter=Q(enrollments__status=Enrollment.Status.STUDYING),
            )
        )
        .order_by("id")
    )

    if keyword:
        classes = classes.filter(
            Q(name__icontains=keyword) |
            Q(course__name__icontains=keyword) |
            Q(teacher__full_name__icontains=keyword)
        )
    if course_id:
        classes = classes.filter(course_id=course_id)

    from django.core.paginator import Paginator
    paginator = Paginator(classes, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    courses = Course.objects.all().order_by("name")

    return render(request, "core/academics/classes/list.html", {
        "page_obj": page_obj,
        "classes": page_obj,
        "courses": courses,
        "keyword": keyword,
        "selected_course_id": course_id,
        **admin_context(request),
    })


@academic_required
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

    return render(request, "core/academics/classes/add.html", {
        "courses": courses,
        "teachers": teachers,
        **admin_context(request),
    })


@academic_required
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
                    english_class.enrollments.filter(
                        status=Enrollment.Status.STUDYING
                    ).count() > max_students
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

    return render(request, "core/academics/classes/edit.html", {
        "english_class": english_class,
        "courses": courses,
        "teachers": teachers,
        **admin_context(request),
    })


@academic_required
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

        enrollment = Enrollment.objects.filter(
            student=student,
            english_class=english_class,
        ).first()

        if enrollment and enrollment.status == Enrollment.Status.STUDYING:
            messages.warning(
                request,
                "Học viên này đã được đăng ký vào lớp."
            )

        elif (
            english_class.enrollments.filter(
                status=Enrollment.Status.STUDYING
            ).count()
            >= english_class.max_students
        ):
            messages.error(
                request,
                "Lớp học đã đủ sĩ số. "
                "Vui lòng tăng sĩ số tối đa của lớp."
            )

        else:
            if enrollment:
                enrollment.status = Enrollment.Status.STUDYING
                enrollment.enrolled_at = timezone.localdate()
                enrollment.ended_at = None
                if enrollment.assessment_policy_id is None:
                    enrollment.assessment_policy = english_class.assessment_policy
                enrollment.save(
                    update_fields=[
                        "status",
                        "enrolled_at",
                        "ended_at",
                        "assessment_policy",
                    ]
                )
            else:
                Enrollment.objects.create(
                    student=student,
                    english_class=english_class,
                    assessment_policy=english_class.assessment_policy,
                    status=Enrollment.Status.STUDYING,
                )
            messages.success(
                request,
                f"Đăng ký học viên {student.full_name} "
                "vào lớp thành công!"
            )

        return redirect("class_detail", class_id=class_id)

    enrollments = (
        english_class.enrollments
        .select_related("student")
        .order_by("student__full_name")
    )
    pending_transfer_student_ids = set(
        ClassTransfer.objects.filter(
            source_class=english_class,
            status=ClassTransfer.Status.PENDING,
        ).values_list("student_id", flat=True)
    )
    students = Student.objects.filter(
        enrollments__english_class=english_class,
        enrollments__status=Enrollment.Status.STUDYING,
    ).order_by("full_name")

    target_classes = (
        EnglishClass.objects
        .select_related("course")
        .annotate(
            active_student_count=Count(
                "enrollments",
                filter=Q(enrollments__status=Enrollment.Status.STUDYING),
            )
        )
        .exclude(pk=english_class.pk)
        .order_by("name")
    )

    available_students = (
        Student.objects
        .exclude(
            enrollments__english_class=english_class,
            enrollments__status=Enrollment.Status.STUDYING,
        )
        .order_by("full_name")
    )

    return render(request, "core/academics/classes/detail.html", {
        "english_class": english_class,
        "students": students,
        "enrollments": enrollments,
        "pending_transfer_student_ids": pending_transfer_student_ids,
        "enrollment_statuses": [
            choice for choice in Enrollment.Status.choices
            if choice[0] != Enrollment.Status.TRANSFERRED
        ],
        "target_classes": target_classes,
        "available_students": available_students,
        **admin_context(request),
    })


@academic_required
def enrollment_transfer(request, class_id, student_id):
    if request.method != "POST":
        return redirect("class_detail", class_id=class_id)

    try:
        transfer = request_class_transfer(
            student_id=student_id,
            source_class_id=class_id,
            target_class_id=request.POST.get("target_class_id"),
            reason=request.POST.get("reason", ""),
            actor=request.user,
        )
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    except (ValueError, TypeError):
        messages.error(request, "Thông tin chuyển lớp không hợp lệ.")
    else:
        if transfer.status == "pending":
            messages.info(
                request,
                "Hai lớp khác khóa học. Yêu cầu đã gửi và đang chờ Admin duyệt.",
            )
        else:
            messages.success(
                request,
                "Đã chuyển học viên. Lớp cũ và lớp mới đã được lưu vào lịch sử.",
            )

    return redirect("class_detail", class_id=class_id)


@academic_required
def enrollment_status_update(request, class_id, student_id):
    if request.method != "POST":
        return redirect("class_detail", class_id=class_id)

    enrollment = get_object_or_404(
        Enrollment.objects.select_related("student"),
        english_class_id=class_id,
        student_id=student_id,
    )
    if ClassTransfer.objects.filter(
        source_enrollment=enrollment,
        status=ClassTransfer.Status.PENDING,
    ).exists():
        messages.error(
            request,
            "Không thể đổi trạng thái khi yêu cầu chuyển lớp đang chờ Admin duyệt.",
        )
        return redirect("class_detail", class_id=class_id)

    new_status = request.POST.get("status", "")

    if (
        new_status not in Enrollment.Status.values
        or new_status == Enrollment.Status.TRANSFERRED
    ):
        messages.error(request, "Trạng thái ghi danh không hợp lệ.")
        return redirect("class_detail", class_id=class_id)

    enrollment.status = new_status
    enrollment.ended_at = (
        timezone.localdate()
        if new_status in (
            Enrollment.Status.STOPPED,
            Enrollment.Status.COMPLETED,
        )
        else None
    )
    enrollment.save(update_fields=["status", "ended_at"])
    messages.success(
        request,
        f"Đã cập nhật trạng thái ghi danh của {enrollment.student.full_name}.",
    )
    return redirect("class_detail", class_id=class_id)


@admin_required
def student_remove_from_class(request, class_id, student_id):
    english_class = get_object_or_404(EnglishClass, id=class_id)
    student = get_object_or_404(Student, id=student_id)

    if request.method != "POST":
        return redirect("class_detail", class_id=class_id)

    enrollment = Enrollment.objects.filter(
        english_class=english_class,
        student=student,
        status=Enrollment.Status.STUDYING,
    ).first()

    if enrollment:
        if ClassTransfer.objects.filter(
            source_enrollment=enrollment,
            status=ClassTransfer.Status.PENDING,
        ).exists():
            messages.error(
                request,
                "Không thể hủy ghi danh khi yêu cầu chuyển lớp đang chờ Admin duyệt.",
            )
            return redirect("class_detail", class_id=class_id)

        enrollment.status = Enrollment.Status.STOPPED
        enrollment.ended_at = timezone.localdate()
        enrollment.save(update_fields=["status", "ended_at"])
        messages.success(
            request,
            f"Đã hủy đăng ký học viên {student.full_name} khỏi lớp."
        )
    else:
        messages.warning(request, "Học viên không thuộc lớp này.")

    return redirect("class_detail", class_id=class_id)


@academic_required
def teacher_list(request):
    keyword = request.GET.get("q", "").strip()
    teachers = Teacher.objects.filter(is_active=True)

    if keyword:
        teachers = teachers.filter(
            Q(full_name__icontains=keyword)
            | Q(email__icontains=keyword)
            | Q(phone__icontains=keyword)
        )

    teachers = teachers.order_by("id")

    from django.core.paginator import Paginator
    paginator = Paginator(teachers, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "core/academics/teachers/list.html", {
        "page_obj": page_obj,
        "teachers": page_obj,
        "keyword": keyword,
        **admin_context(request),
    })


@academic_required
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
        "core/academics/teachers/add.html",
        admin_context(request),
    )


@academic_required
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

    return render(request, "core/academics/teachers/edit.html", {
        "teacher": teacher,
        **admin_context(request),
    })


@admin_required
def teacher_delete(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == "POST":
        action = request.POST.get("action", "archive")
        if action == "restore":
            teacher.is_active = True
            teacher.save(update_fields=["is_active"])
            messages.success(request, f"Đã khôi phục giảng viên '{teacher.full_name}' hoạt động trở lại.")
        else:
            teacher.is_active = False
            teacher.save(update_fields=["is_active"])
            messages.success(request, f"Đã lưu trữ giảng viên '{teacher.full_name}'. Lịch sử phân công và dữ liệu đào tạo được bảo toàn nguyên vẹn.")
        return redirect("teacher_list")

    return render(request, "core/academics/teachers/delete.html", {
        "teacher": teacher,
        **admin_context(request),
    })
