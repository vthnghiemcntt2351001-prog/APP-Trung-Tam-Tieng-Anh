
# core/admin.py

from django.contrib import admin, messages

from .models import (
    Student,
    Course,
    EnglishClass,
    Enrollment,
    ClassTransfer,
    AssessmentPolicy,
    AssessmentComponent,
    AssessmentEvent,
    AssessmentResult,
    AssessmentResultAudit,
    FinalResult,
    Teacher,
    Grade,
    Tuition,
    PaymentTransaction,
    Certificate,
    ClassSession,
    Attendance,
)

from .blockchain.blockchain_service import issue_database_certificate


class AssessmentComponentInline(admin.TabularInline):
    model = AssessmentComponent
    extra = 1


@admin.register(AssessmentPolicy)
class AssessmentPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "course", "version", "scale", "status", "pass_score")
    list_filter = ("status", "scale", "course")
    search_fields = ("name", "course__name")
    inlines = (AssessmentComponentInline,)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AssessmentEvent)
class AssessmentEventAdmin(admin.ModelAdmin):
    list_display = ("name", "english_class", "component", "assessment_date")
    list_filter = ("english_class__course", "english_class", "component")
    search_fields = ("name", "english_class__name", "component__name")


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "event", "attempt_number", "score", "status", "graded_by", "graded_at")
    list_filter = ("status", "event__english_class", "event__component")
    search_fields = ("enrollment__student__full_name", "event__name")
    readonly_fields = tuple(field.name for field in AssessmentResult._meta.fields)

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FinalResult)
class FinalResultAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "policy", "final_score", "status", "calculated_at", "confirmed_by")
    list_filter = ("status", "policy", "enrollment__english_class")
    search_fields = ("enrollment__student__full_name",)
    readonly_fields = tuple(field.name for field in FinalResult._meta.fields)

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AssessmentResultAudit)
class AssessmentResultAuditAdmin(admin.ModelAdmin):
    list_display = ("result", "old_score", "new_score", "changed_by", "changed_at")
    readonly_fields = tuple(field.name for field in AssessmentResultAudit._meta.fields)

    def has_view_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ClassTransfer)
class ClassTransferAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "source_class",
        "target_class",
        "status",
        "requested_at",
        "transferred_at",
        "requested_by",
        "performed_by",
    )
    list_filter = ("status", "source_class__course", "target_class__course")
    search_fields = (
        "student__full_name",
        "source_class__name",
        "target_class__name",
        "reason",
    )
    readonly_fields = tuple(
        field.name for field in ClassTransfer._meta.fields
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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

class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Tuition)
class TuitionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "english_class",
        "total_fee",
        "paid_amount",
        "remaining_amount",
        "payment_status",
        "payment_date",
    )

    list_filter = (
        "english_class__course",
        "english_class",
        "payment_date",
    )

    search_fields = (
        "student__full_name",
        "student__email",
        "english_class__name",
    )
    readonly_fields = ("paid_amount", "created_at")
    inlines = (PaymentTransactionInline,)



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
            result = issue_database_certificate(obj)

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


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_code",
        "tuition",
        "amount",
        "payment_method",
        "payment_date",
        "collected_by",
        "created_at",
    )
    list_filter = ("payment_method", "payment_date")
    search_fields = (
        "receipt_code",
        "tuition__student__full_name",
        "tuition__student__email",
    )


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    fields = ("student", "status", "note", "recorded_by")
    autocomplete_fields = ("student",)


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    list_display = (
        "english_class",
        "session_number",
        "session_date",
        "room",
        "teacher",
        "topic",
        "is_completed",
    )
    list_filter = ("english_class__course", "english_class", "is_completed", "session_date")
    search_fields = ("english_class__name", "topic", "room", "teacher__full_name")
    inlines = (AttendanceInline,)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "session",
        "status",
        "note",
        "recorded_by",
        "recorded_at",
    )
    list_filter = ("status", "session__english_class", "session__session_date")
    search_fields = (
        "student__full_name",
        "student__phone",
        "session__english_class__name",
        "session__topic",
    )


