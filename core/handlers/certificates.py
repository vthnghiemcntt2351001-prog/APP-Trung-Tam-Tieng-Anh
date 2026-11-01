from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from ..models import Certificate, Course
from ..permissions import admin_required, academic_required, staff_required, admin_context
from ..blockchain.blockchain_service import (
    issue_database_certificate,
    verify_database_certificate,
    is_blockchain_available,
)


@academic_required
def certificate_list(request):
    """Hiển thị danh sách chứng chỉ và trạng thái Blockchain."""

    keyword = request.GET.get("q", "").strip()
    status = request.GET.get("status", "all").strip()
    course_id = request.GET.get("course_id", "").strip()
    classification = request.GET.get("classification", "all").strip()

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
        keyword_filter = (
            Q(certificate_code__icontains=keyword)
            | Q(student__full_name__icontains=keyword)
            | Q(student__email__icontains=keyword)
            | Q(english_class__name__icontains=keyword)
        )
        if keyword.upper().startswith("HV-"):
            raw_id = keyword.upper().replace("HV-", "").strip()
            if raw_id.isdigit():
                keyword_filter |= Q(student__id=int(raw_id))
        certificates = certificates.filter(keyword_filter)

    if status and status != "all":
        certificates = certificates.filter(blockchain_status=status)

    if course_id:
        certificates = certificates.filter(english_class__course_id=course_id)

    if classification and classification != "all":
        certificates = certificates.filter(classification__iexact=classification)

    # Live metric counters
    total_count = Certificate.objects.count()
    issued_count = Certificate.objects.filter(blockchain_status="issued").count()
    pending_count = Certificate.objects.filter(blockchain_status="pending").count()
    distinction_count = Certificate.objects.filter(
        Q(classification__icontains="Xuất sắc") | Q(classification__icontains="Giỏi")
    ).count()

    from django.core.paginator import Paginator
    paginator = Paginator(certificates, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    courses = Course.objects.all().order_by("name")

    context = {
        "page_obj": page_obj,
        "certificates": page_obj,
        "keyword": keyword,
        "selected_status": status,
        "selected_course_id": course_id,
        "selected_classification": classification,
        "total_count": total_count,
        "issued_count": issued_count,
        "pending_count": pending_count,
        "distinction_count": distinction_count,
        "courses": courses,
        "blockchain_available": is_blockchain_available(),
        **admin_context(request),
    }

    return render(
        request,
        "core/certificates/list.html",
        context,
    )


@academic_required
def certificate_add(request):
    """Cấp chứng chỉ tốt nghiệp mới cho học viên trực tiếp từ Web UI."""
    from decimal import Decimal, InvalidOperation
    from datetime import date
    from django.utils.dateparse import parse_date
    from ..models import EnglishClass, Student, Enrollment, FinalResult, Grade

    classes = EnglishClass.objects.select_related("course").all().order_by("name")
    selected_class_id = request.GET.get("class_id") or request.POST.get("english_class")
    selected_class = None
    eligible_students = []

    if selected_class_id:
        selected_class = EnglishClass.objects.select_related("course").filter(pk=selected_class_id).first()
        if selected_class:
            issued_student_ids = Certificate.objects.filter(
                english_class=selected_class
            ).values_list("student_id", flat=True)

            enrollments = Enrollment.objects.filter(
                english_class=selected_class
            ).select_related("student").exclude(student_id__in=issued_student_ids)

            for en in enrollments:
                student = en.student
                final_res = FinalResult.objects.filter(enrollment=en).first()
                grade_record = Grade.objects.filter(student=student, english_class=selected_class).first()

                score = None
                if final_res and final_res.final_score is not None:
                    score = round(float(final_res.final_score), 2)
                elif grade_record:
                    score = float(grade_record.average_score)

                if score is not None:
                    if score >= 9.0:
                        classification = "Xuất sắc"
                    elif score >= 8.0:
                        classification = "Giỏi"
                    elif score >= 6.5:
                        classification = "Khá"
                    elif score >= 5.0:
                        classification = "Trung bình"
                    else:
                        classification = "Chưa đạt"
                else:
                    classification = "Đạt chuẩn tốt nghiệp"
                    score = 8.0

                eligible_students.append({
                    "student": student,
                    "score": score,
                    "classification": classification,
                    "enrollment_status": en.get_status_display(),
                })

    if request.method == "POST":
        student_id = request.POST.get("student")
        class_id = request.POST.get("english_class")
        score_raw = request.POST.get("score", "8.0").strip()
        classification = request.POST.get("classification", "Giỏi").strip()
        issue_date_raw = request.POST.get("issue_date") or None
        auto_blockchain = request.POST.get("auto_blockchain") == "1"

        try:
            student = get_object_or_404(Student, pk=student_id)
            english_class = get_object_or_404(EnglishClass.objects.select_related("course"), pk=class_id)

            if Certificate.objects.filter(student=student, english_class=english_class).exists():
                messages.warning(request, f"Học viên '{student.full_name}' đã được cấp chứng chỉ cho lớp này.")
                return redirect("certificate_list")

            score = Decimal(score_raw)
            if not score.is_finite() or score < 0 or score > 10:
                raise ValueError("Điểm số phải từ 0 đến 10.")

            issue_date = parse_date(issue_date_raw) if issue_date_raw else date.today()
            if not issue_date:
                raise ValueError("Ngày cấp chứng chỉ không hợp lệ.")

            cert = Certificate.objects.create(
                student=student,
                english_class=english_class,
                score=score,
                classification=classification or "Đạt",
                issue_date=issue_date,
            )

            msg = f"Đã cấp chứng chỉ '{cert.certificate_code}' cho học viên '{student.full_name}' thành công!"

            if auto_blockchain and is_blockchain_available():
                try:
                    result = issue_database_certificate(cert)
                    if result.get("status") == "success":
                        msg += f" (Đã ghi nhận lên Blockchain tại Block #{result.get('block_number')})"
                except Exception as exc:
                    msg += f" (Lưu ý: Chưa ghi được lên Blockchain: {exc})"

            messages.success(request, msg)
            return redirect("certificate_list")

        except (InvalidOperation, ValueError, TypeError) as exc:
            messages.error(request, f"Dữ liệu cấp chứng chỉ không hợp lệ: {exc}")

    from datetime import date
    return render(request, "core/certificates/add.html", {
        "classes": classes,
        "selected_class": selected_class,
        "eligible_students": eligible_students,
        "today": date.today().isoformat(),
        "blockchain_available": is_blockchain_available(),
        **admin_context(request),
    })


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


@staff_required
def certificate_verify(request):
    """Xác minh chứng chỉ trên Blockchain."""

    result = None
    certificate_code = request.GET.get("code", "").strip() or request.POST.get("certificate_code", "").strip()
    certificate_obj = None

    if request.method == "POST" or (request.method == "GET" and request.GET.get("code")):
        if not certificate_code:
            messages.error(
                request,
                "Vui lòng nhập mã chứng chỉ cần xác minh."
            )
        else:
            certificate = (
                Certificate.objects
                .select_related("student", "english_class", "english_class__course")
                .filter(certificate_code=certificate_code)
                .first()
            )

            if certificate is None:
                result = {
                    "valid": False,
                    "message": "Không tìm thấy chứng chỉ trong hệ thống.",
                    "certificate_code": certificate_code,
                }
            else:
                certificate_obj = certificate
                try:
                    result = verify_database_certificate(certificate)
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
        "certificate": certificate_obj,
        "blockchain_available": is_blockchain_available(),
        **admin_context(request),
    }

    return render(
        request,
        "core/certificates/verify.html",
        context,
    )
