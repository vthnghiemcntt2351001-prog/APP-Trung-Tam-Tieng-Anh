from datetime import timedelta
from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time

from ..models import Attendance, ClassSession, EnglishClass, Enrollment, Student, Teacher
from ..permissions import academic_required, admin_context


@academic_required
def session_list(request, class_id):
    """Hiển thị danh sách các buổi học của một lớp học kèm tình trạng điểm danh."""
    english_class = get_object_or_404(
        EnglishClass.objects.select_related("course", "teacher"),
        pk=class_id,
    )

    sessions = (
        ClassSession.objects.filter(english_class=english_class)
        .select_related("teacher")
        .annotate(
            total_attendees=Count("attendances"),
            present_count=Count(
                "attendances",
                filter=Q(attendances__status=Attendance.AttendanceStatus.PRESENT),
            ),
            late_count=Count(
                "attendances",
                filter=Q(attendances__status=Attendance.AttendanceStatus.LATE),
            ),
            absent_count=Count(
                "attendances",
                filter=Q(
                    attendances__status__in=[
                        Attendance.AttendanceStatus.ABSENT_EXCUSED,
                        Attendance.AttendanceStatus.ABSENT_UNEXCUSED,
                    ]
                ),
            ),
        )
        .order_by("session_number")
    )

    # Thống kê tổng quan
    total_sessions = sessions.count()
    completed_sessions = sum(1 for s in sessions if s.is_completed)
    active_students_count = (
        Enrollment.objects.filter(
            english_class=english_class,
            status=Enrollment.Status.STUDYING,
        ).count()
        or english_class.students.count()
    )

    return render(
        request,
        "core/academics/attendance/session_list.html",
        {
            "english_class": english_class,
            "sessions": sessions,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "active_students_count": active_students_count,
            **admin_context(request),
        },
    )


@academic_required
def session_add(request, class_id):
    """Thêm một buổi học mới cho lớp."""
    english_class = get_object_or_404(EnglishClass, pk=class_id)
    teachers = Teacher.objects.filter(is_active=True).order_by("full_name")

    # Gợi ý số buổi tiếp theo
    max_session = (
        ClassSession.objects.filter(english_class=english_class)
        .values_list("session_number", flat=True)
        .order_by("-session_number")
        .first()
        or 0
    )
    next_session_number = max_session + 1

    if request.method == "POST":
        session_number_raw = request.POST.get("session_number", "").strip()
        session_date_raw = request.POST.get("session_date", "").strip()
        start_time_raw = request.POST.get("start_time", "").strip()
        end_time_raw = request.POST.get("end_time", "").strip()
        room = request.POST.get("room", "").strip()
        teacher_id = request.POST.get("teacher", "").strip()
        topic = request.POST.get("topic", "").strip()
        notes = request.POST.get("notes", "").strip()

        try:
            session_number = int(session_number_raw)
            if session_number <= 0:
                raise ValueError("Số buổi phải lớn hơn 0.")
        except (ValueError, TypeError):
            messages.error(request, "Vui lòng nhập số thứ tự buổi học hợp lệ.")
            return redirect("session_add", class_id=class_id)

        session_date = parse_date(session_date_raw)
        if not session_date:
            messages.error(request, "Vui lòng chọn ngày học hợp lệ.")
            return redirect("session_add", class_id=class_id)

        start_time = parse_time(start_time_raw) if start_time_raw else None
        end_time = parse_time(end_time_raw) if end_time_raw else None

        teacher = (
            get_object_or_404(Teacher, pk=teacher_id) if teacher_id else None
        ) or english_class.teacher

        if ClassSession.objects.filter(
            english_class=english_class,
            session_number=session_number,
        ).exists():
            messages.error(
                request,
                f"Buổi số {session_number} đã tồn tại trong lớp này.",
            )
            return redirect("session_add", class_id=class_id)

        ClassSession.objects.create(
            english_class=english_class,
            session_number=session_number,
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            room=room,
            teacher=teacher,
            topic=topic,
            notes=notes,
        )

        messages.success(request, f"Đã thêm buổi học số {session_number} thành công!")
        return redirect("session_list", class_id=class_id)

    return render(
        request,
        "core/academics/attendance/session_add.html",
        {
            "english_class": english_class,
            "teachers": teachers,
            "next_session_number": next_session_number,
            "default_date": timezone.localdate().isoformat(),
            **admin_context(request),
        },
    )


@academic_required
def session_attendance(request, session_id):
    """Giao diện điểm danh nhanh cho buổi học."""
    session = get_object_or_404(
        ClassSession.objects.select_related("english_class", "teacher"),
        pk=session_id,
    )
    english_class = session.english_class

    # Lấy danh sách học viên đang học trong lớp
    enrollments = (
        Enrollment.objects.filter(
            english_class=english_class,
            status=Enrollment.Status.STUDYING,
        )
        .select_related("student")
        .order_by("student__full_name")
    )

    if enrollments.exists():
        students = [e.student for e in enrollments]
    else:
        # Fallback qua quan hệ many-to-many nếu chưa migrate hết sang Enrollment
        students = list(english_class.students.filter(is_active=True).order_by("full_name"))

    # Lấy dữ liệu điểm danh đã lưu từ trước
    existing_attendances = {
        att.student_id: att
        for att in Attendance.objects.filter(session=session).select_related("student")
    }

    if request.method == "POST":
        actor = request.user if request.user.is_authenticated else None
        updated_count = 0

        with transaction.atomic():
            for student in students:
                status_key = f"status_{student.id}"
                note_key = f"note_{student.id}"

                status_val = request.POST.get(status_key, Attendance.AttendanceStatus.PRESENT)
                note_val = request.POST.get(note_key, "").strip()

                if status_val not in dict(Attendance.AttendanceStatus.choices):
                    status_val = Attendance.AttendanceStatus.PRESENT

                Attendance.objects.update_or_create(
                    session=session,
                    student=student,
                    defaults={
                        "status": status_val,
                        "note": note_val,
                        "recorded_by": actor,
                    },
                )
                updated_count += 1

            session.is_completed = True
            session.save(update_fields=["is_completed"])

        messages.success(
            request,
            f"Đã ghi nhận điểm danh thành công cho {updated_count} học viên của buổi {session.session_number}!",
        )
        return redirect("session_list", class_id=english_class.id)

    # Ghép dữ liệu cho template
    student_records = []
    for student in students:
        att = existing_attendances.get(student.id)
        student_records.append({
            "student": student,
            "status": att.status if att else Attendance.AttendanceStatus.PRESENT,
            "note": att.note if att else "",
        })

    return render(
        request,
        "core/academics/attendance/session_attendance.html",
        {
            "session": session,
            "english_class": english_class,
            "student_records": student_records,
            "total_students": len(students),
            "status_choices": Attendance.AttendanceStatus.choices,
            **admin_context(request),
        },
    )


@academic_required
def class_attendance_report(request, class_id):
    """Báo cáo tổng hợp chuyên cần của cả lớp học."""
    english_class = get_object_or_404(
        EnglishClass.objects.select_related("course", "teacher"),
        pk=class_id,
    )

    sessions = list(
        ClassSession.objects.filter(english_class=english_class).order_by("session_number")
    )
    total_sessions_count = len(sessions)

    enrollments = (
        Enrollment.objects.filter(
            english_class=english_class,
            status=Enrollment.Status.STUDYING,
        )
        .select_related("student")
        .order_by("student__full_name")
    )

    if enrollments.exists():
        students = [e.student for e in enrollments]
    else:
        students = list(english_class.students.filter(is_active=True).order_by("full_name"))

    # Lấy toàn bộ bản ghi điểm danh của lớp
    all_attendances = list(
        Attendance.objects.filter(session__english_class=english_class).select_related(
            "session", "student"
        )
    )

    # Map attendance: (student_id, session_id) -> status
    attendance_map = {
        (att.student_id, att.session_id): att.status
        for att in all_attendances
    }

    report_rows = []
    for student in students:
        present_count = 0
        late_count = 0
        excused_count = 0
        unexcused_count = 0

        session_statuses = []
        for session in sessions:
            status = attendance_map.get((student.id, session.id))
            session_statuses.append({
                "session": session,
                "status": status,
            })
            if status == Attendance.AttendanceStatus.PRESENT:
                present_count += 1
            elif status == Attendance.AttendanceStatus.LATE:
                late_count += 1
            elif status == Attendance.AttendanceStatus.ABSENT_EXCUSED:
                excused_count += 1
            elif status == Attendance.AttendanceStatus.ABSENT_UNEXCUSED:
                unexcused_count += 1

        attended_units = present_count + (late_count * 0.8)
        attendance_rate = (
            round((attended_units / total_sessions_count) * 100, 1)
            if total_sessions_count > 0
            else 100.0
        )

        is_warning = attendance_rate < 80.0 and total_sessions_count > 0

        report_rows.append({
            "student": student,
            "session_statuses": session_statuses,
            "present_count": present_count,
            "late_count": late_count,
            "excused_count": excused_count,
            "unexcused_count": unexcused_count,
            "attendance_rate": attendance_rate,
            "is_warning": is_warning,
        })

    return render(
        request,
        "core/academics/attendance/attendance_report.html",
        {
            "english_class": english_class,
            "sessions": sessions,
            "report_rows": report_rows,
            "total_sessions": total_sessions_count,
            **admin_context(request),
        },
    )
