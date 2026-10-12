
# core/admin.py

import hashlib
import json

from django.contrib import admin, messages

from .models import (
    Student,
    Course,
    EnglishClass,
    Teacher,
    Grade,
    Tuition,
    Certificate,
)

from .blockchain.blockchain_service import issue_certificate


# =====================================================
# QUAN LY HOC VIEN
# =====================================================

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "phone",
        "created_at",
    )

    search_fields = (
        "full_name",
        "email",
        "phone",
    )


# =====================================================
# QUAN LY KHOA HOC
# =====================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "tuition",
        "duration",
    )

    search_fields = ("name",)


# =====================================================
# QUAN LY LOP HOC
# =====================================================

@admin.register(EnglishClass)
class EnglishClassAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "course",
        "teacher",
        "start_date",
        "end_date",
    )

    list_filter = (
        "course",
        "teacher",
    )

    search_fields = (
        "name",
        "course__name",
        "teacher__full_name",
    )


# =====================================================
# QUAN LY GIAO VIEN
# =====================================================

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "full_name",
        "email",
        "phone",
        "specialization",
    )

    search_fields = (
        "full_name",
        "email",
        "phone",
    )


# =====================================================
# QUAN LY DIEM SO
# =====================================================

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "english_class",
        "oral_score",
        "listening_score",
        "reading_score",
        "writing_score",
        "exam_date",
    )

    list_filter = (
        "english_class",
        "exam_date",
    )

    search_fields = (
        "student__full_name",
        "english_class__name",
    )


# =====================================================
# QUAN LY HOC PHI
# =====================================================

@admin.register(Tuition)
class TuitionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "english_class",
        "total_fee",
        "paid_amount",
        "payment_date",
    )

    list_filter = (
        "english_class",
        "payment_date",
    )

    search_fields = (
        "student__full_name",
        "english_class__name",
    )


# =====================================================
# QUAN LY CHUNG CHI BLOCKCHAIN
# =====================================================

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):

    list_display = (
        "certificate_code",
        "student",
        "english_class",
        "issue_date",
        "score",
        "classification",
        "blockchain_status",
        "block_number",
    )

    list_filter = (
        "blockchain_status",
        "issue_date",
        "classification",
    )

    search_fields = (
        "certificate_code",
        "student__full_name",
        "student__email",
        "english_class__name",
        "transaction_hash",
    )

    readonly_fields = (
        "certificate_code",
        "data_hash",
        "transaction_hash",
        "block_number",
        "blockchain_status",
        "created_at",
    )

    fieldsets = (
        (
            "Thong tin chung chi",
            {
                "fields": (
                    "certificate_code",
                    "student",
                    "english_class",
                    "issue_date",
                    "score",
                    "classification",
                )
            },
        ),
        (
            "Thong tin Blockchain",
            {
                "fields": (
                    "data_hash",
                    "transaction_hash",
                    "block_number",
                    "blockchain_status",
                )
            },
        ),
        (
            "Thong tin he thong",
            {
                "fields": ("created_at",)
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Luu chung chi vao Django, sau do ghi ma bam
        len Blockchain va cap nhat ket qua giao dich.
        """

        # Luu chung chi truoc de tao ma chung chi
        super().save_model(request, obj, form, change)

        # Khong ghi lai neu chung chi da duoc xac nhan
        if obj.blockchain_status == "issued":
            self.message_user(
                request,
                "Chung chi nay da duoc ghi len Blockchain.",
                level=messages.INFO,
            )
            return

        try:
            # Tao du lieu chung chi de tinh SHA-256
            certificate_data = {
                "certificate_code": obj.certificate_code,
                "student_id": obj.student_id,
                "student_name": obj.student.full_name,
                "class_id": obj.english_class_id,
                "class_name": obj.english_class.name,
                "issue_date": obj.issue_date.isoformat(),
                "score": str(obj.score),
                "classification": obj.classification or "",
            }

            # Chuan hoa JSON de tao ma bam on dinh
            json_data = json.dumps(
                certificate_data,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )

            data_hash = "0x" + hashlib.sha256(
                json_data.encode("utf-8")
            ).hexdigest()

            # Ghi ma chung chi va ma bam len Blockchain
            result = issue_certificate(
                obj.certificate_code,
                data_hash,
            )

            # Cap nhat ket qua giao dich
            obj.data_hash = result["data_hash"]
            obj.transaction_hash = result["transaction_hash"]
            obj.block_number = result["block_number"]
            obj.blockchain_status = "issued"

            obj.save(
                update_fields=[
                    "data_hash",
                    "transaction_hash",
                    "block_number",
                    "blockchain_status",
                ]
            )

            self.message_user(
                request,
                (
                    "Ghi chung chi len Blockchain thanh cong. "
                    f"Ma giao dich: {result['transaction_hash']}"
                ),
                level=messages.SUCCESS,
            )

        except Exception as exc:
            # Chung chi van ton tai trong Django,
            # nhung giao dich Blockchain chua thanh cong
            obj.blockchain_status = "failed"

            obj.save(
                update_fields=["blockchain_status"]
            )

            self.message_user(
                request,
                (
                    "Da luu chung chi vao Django nhung ghi "
                    f"Blockchain that bai: {exc}"
                ),
                level=messages.ERROR,
            )
