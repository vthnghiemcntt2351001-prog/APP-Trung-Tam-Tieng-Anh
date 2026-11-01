
from django.db import models
from django.utils import timezone
from django.conf import settings

# ==============================
# QUẢN LÝ HỌC VIÊN
# ==============================
class Student(models.Model):
    full_name = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="Họ và tên"
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email"
    )
    phone = models.CharField(
        max_length=15,
        db_index=True,
        verbose_name="Số điện thoại"
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ngày sinh"
    )
    address = models.TextField(
        blank=True,
        verbose_name="Địa chỉ"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Ngày tạo"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Đang hoạt động"
    )

    @property
    def student_code(self):
        return f"HV-{self.id:04d}"

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Học viên"
        verbose_name_plural = "Danh sách học viên"


# ==============================
# QUẢN LÝ KHÓA HỌC
# ==============================
class Course(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Tên khóa học"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Mô tả"
    )
    tuition = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        verbose_name="Học phí"
    )
    duration = models.PositiveIntegerField(
        default=3,
        verbose_name="Thời lượng (tháng)"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Đang hoạt động"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Khóa học"
        verbose_name_plural = "Danh sách khóa học"


class AssessmentPolicy(models.Model):
    """Versioned grading rules that can be assigned to course classes."""

    class Scale(models.TextChoices):
        NUMERIC = "numeric", "Điểm số"
        BAND = "band", "Band điểm"
        PASS_FAIL = "pass_fail", "Đạt / Chưa đạt"

    class Status(models.TextChoices):
        DRAFT = "draft", "Bản nháp"
        ACTIVE = "active", "Đang áp dụng"
        ARCHIVED = "archived", "Ngừng áp dụng"

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="assessment_policies",
        verbose_name="Khóa học",
    )
    name = models.CharField(max_length=150, verbose_name="Tên quy chế")
    version = models.PositiveIntegerField(default=1, verbose_name="Phiên bản")
    scale = models.CharField(
        max_length=20,
        choices=Scale.choices,
        default=Scale.NUMERIC,
        verbose_name="Thang đánh giá",
    )
    max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=10,
        verbose_name="Điểm tối đa",
    )
    pass_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Điểm tổng kết tối thiểu",
    )
    rounding_precision = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Số chữ số làm tròn",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name="Trạng thái",
    )
    effective_from = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ngày bắt đầu áp dụng",
    )
    effective_to = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ngày kết thúc áp dụng",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from decimal import Decimal

        from django.core.exceptions import ValidationError

        errors = {}
        if self.max_score <= 0:
            errors["max_score"] = "Điểm tối đa phải lớn hơn 0."
        if self.pass_score is not None and not (
            Decimal("0") <= self.pass_score <= self.max_score
        ):
            errors["pass_score"] = "Điểm đạt phải nằm trong thang điểm của quy chế."
        if self.rounding_precision > 4:
            errors["rounding_precision"] = "Chỉ hỗ trợ làm tròn tối đa 4 chữ số."
        if (
            self.effective_from
            and self.effective_to
            and self.effective_to < self.effective_from
        ):
            errors["effective_to"] = "Ngày kết thúc phải sau ngày bắt đầu."
        if self.status == self.Status.ACTIVE:
            if self.scale != self.Scale.PASS_FAIL and self.pass_score is None:
                errors["pass_score"] = (
                    "Cần cấu hình điểm tổng kết tối thiểu trước khi kích hoạt."
                )
            total_weight = (
                sum(
                    self.components.values_list("weight", flat=True),
                    Decimal("0"),
                )
                if self.pk
                else Decimal("0")
            )
            if total_weight != Decimal("100"):
                errors["status"] = (
                    "Tổng tỷ trọng các thành phần phải bằng 100% "
                    "trước khi kích hoạt quy chế."
                )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        if self.pk:
            old = type(self).objects.get(pk=self.pk)
            if old.status in (self.Status.ACTIVE, self.Status.ARCHIVED):
                if (
                    old.status == self.Status.ACTIVE
                    and self.status == self.Status.DRAFT
                ) or (
                    old.status == self.Status.ARCHIVED
                    and self.status != self.Status.ARCHIVED
                ):
                    raise ValidationError(
                        "Không thể đưa quy chế đã kích hoạt/ngừng áp dụng "
                        "trở lại bản nháp. Hãy tạo phiên bản mới."
                    )
                immutable_fields = (
                    "course_id",
                    "name",
                    "version",
                    "scale",
                    "max_score",
                    "pass_score",
                    "rounding_precision",
                    "effective_from",
                    "effective_to",
                )
                if any(
                    getattr(old, field) != getattr(self, field)
                    for field in immutable_fields
                ):
                    raise ValidationError(
                        "Quy chế đang áp dụng không được sửa. "
                        "Hãy tạo phiên bản mới để giữ nguyên kết quả lịch sử."
                    )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        if self.status != self.Status.DRAFT:
            raise ValidationError("Chỉ được xóa quy chế còn ở trạng thái bản nháp.")
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.name} v{self.version} — {self.course.name}"

    class Meta:
        verbose_name = "Quy chế đánh giá"
        verbose_name_plural = "Quy chế đánh giá"
        constraints = [
            models.UniqueConstraint(
                fields=("course", "name", "version"),
                name="unique_course_assessment_policy_version",
            ),
        ]


class AssessmentComponent(models.Model):
    class Aggregation(models.TextChoices):
        AVERAGE = "average", "Trung bình các lần"
        HIGHEST = "highest", "Lấy điểm cao nhất"
        LATEST = "latest", "Lấy điểm gần nhất"

    policy = models.ForeignKey(
        AssessmentPolicy,
        on_delete=models.CASCADE,
        related_name="components",
        verbose_name="Quy chế",
    )
    name = models.CharField(max_length=120, verbose_name="Thành phần")
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Tỷ trọng (%)",
    )
    max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=10,
        verbose_name="Điểm tối đa thành phần",
    )
    required = models.BooleanField(default=True, verbose_name="Bắt buộc có điểm")
    minimum_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Điểm tối thiểu riêng",
    )
    aggregation = models.CharField(
        max_length=20,
        choices=Aggregation.choices,
        default=Aggregation.AVERAGE,
        verbose_name="Cách tổng hợp các lần đánh giá",
    )

    def clean(self):
        from decimal import Decimal

        from django.core.exceptions import ValidationError

        errors = {}
        if self.weight <= 0 or self.weight > 100:
            errors["weight"] = "Tỷ trọng phải lớn hơn 0% và không vượt quá 100%."
        if self.max_score <= 0:
            errors["max_score"] = "Điểm tối đa phải lớn hơn 0."
        if self.minimum_score is not None and not (
            Decimal("0") <= self.minimum_score <= self.max_score
        ):
            errors["minimum_score"] = "Điểm tối thiểu phải nằm trong thang điểm."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        if self.policy_id and self.policy.status in (
            AssessmentPolicy.Status.ACTIVE,
            AssessmentPolicy.Status.ARCHIVED,
        ):
            if not self.pk:
                raise ValidationError(
                    "Không thể thêm thành phần vào quy chế đang áp dụng."
                )
            old = type(self).objects.get(pk=self.pk)
            if any(
                getattr(old, field) != getattr(self, field)
                for field in (
                    "policy_id",
                    "name",
                    "weight",
                    "max_score",
                    "required",
                    "minimum_score",
                    "aggregation",
                )
            ):
                raise ValidationError(
                "Không thể sửa thành phần của quy chế đã kích hoạt/ngừng áp dụng; "
                    "hãy tạo phiên bản quy chế mới."
                )
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        if self.policy.status in (
            AssessmentPolicy.Status.ACTIVE,
            AssessmentPolicy.Status.ARCHIVED,
        ):
            raise ValidationError(
                "Không thể xóa thành phần của quy chế đã kích hoạt/ngừng áp dụng."
            )
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.weight}%)"

    class Meta:
        verbose_name = "Thành phần đánh giá"
        verbose_name_plural = "Thành phần đánh giá"
        constraints = [
            models.UniqueConstraint(
                fields=("policy", "name"),
                name="unique_assessment_component_name",
            ),
        ]


# ==============================
# QUẢN LÝ GIÁO VIÊN
# ==============================
class Teacher(models.Model):
    full_name = models.CharField(
        max_length=100,
        verbose_name="Họ và tên"
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Email"
    )
    phone = models.CharField(
        max_length=15,
        verbose_name="Số điện thoại"
    )
    specialization = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Chuyên môn"
    )
    address = models.TextField(
        blank=True,
        verbose_name="Địa chỉ"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Đang hoạt động"
    )

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Giáo viên"
        verbose_name_plural = "Danh sách giáo viên"


# ==============================
# QUẢN LÝ LỚP HỌC
# ==============================
class EnglishClass(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Tên lớp"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="classes",
        verbose_name="Khóa học"
    )

    assessment_policy = models.ForeignKey(
        AssessmentPolicy,
        on_delete=models.PROTECT,
        related_name="classes",
        null=True,
        blank=True,
        verbose_name="Quy chế đánh giá",
    )

    # Giữ lại tên giáo viên cũ để tránh mất dữ liệu
    teacher_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tên giáo viên cũ"
    )

    # Liên kết lớp học với giáo viên
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="english_classes",
        verbose_name="Giáo viên phụ trách"
    )

    start_date = models.DateField(
        db_index=True,
        verbose_name="Ngày bắt đầu"
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ngày kết thúc"
    )

    max_students = models.PositiveIntegerField(
        default=20,
        verbose_name="Sĩ số tối đa"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Đang hoạt động"
    )

    students = models.ManyToManyField(
        Student,
        blank=True,
        through="Enrollment",
        related_name="english_classes",
        verbose_name="Học viên"
    )

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.course_id
            and self.assessment_policy_id
            and self.assessment_policy.course_id != self.course_id
        ):
            raise ValidationError({
                "assessment_policy": "Quy chế đánh giá phải thuộc khóa học của lớp."
            })

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Lớp học"
        verbose_name_plural = "Danh sách lớp học"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        STUDYING = "studying", "Đang học"
        TRANSFERRED = "transferred", "Đã chuyển lớp"
        STOPPED = "stopped", "Đã dừng"
        COMPLETED = "completed", "Hoàn thành"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Học viên",
    )
    english_class = models.ForeignKey(
        EnglishClass,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Lớp học",
    )
    assessment_policy = models.ForeignKey(
        AssessmentPolicy,
        on_delete=models.PROTECT,
        related_name="enrollments",
        null=True,
        blank=True,
        verbose_name="Phiên bản quy chế áp dụng",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.STUDYING,
        db_index=True,
        verbose_name="Trạng thái ghi danh",
    )
    enrolled_at = models.DateField(
        default=timezone.localdate,
        db_index=True,
        verbose_name="Ngày ghi danh",
    )
    ended_at = models.DateField(
        null=True,
        blank=True,
        verbose_name="Ngày kết thúc",
    )
    note = models.TextField(blank=True, verbose_name="Ghi chú")

    def __str__(self):
        return f"{self.student} - {self.english_class} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Ghi danh"
        verbose_name_plural = "Danh sách ghi danh"
        ordering = ["-enrolled_at", "student__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=("student", "english_class"),
                name="unique_student_class_enrollment",
            ),
        ]

class ClassTransfer(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        COMPLETED = "completed", "Đã chuyển"
        REJECTED = "rejected", "Từ chối"

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="class_transfers",
        verbose_name="Học viên",
    )
    source_class = models.ForeignKey(
        EnglishClass,
        on_delete=models.PROTECT,
        related_name="outgoing_transfers",
        verbose_name="Lớp cũ",
    )
    target_class = models.ForeignKey(
        EnglishClass,
        on_delete=models.PROTECT,
        related_name="incoming_transfers",
        verbose_name="Lớp mới",
    )
    source_enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        related_name="transfer_requests",
        verbose_name="Ghi danh lớp cũ",
    )
    destination_enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="transfer_records",
        verbose_name="Ghi danh lớp mới",
    )
    reason = models.TextField(verbose_name="Lý do chuyển")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Trạng thái yêu cầu",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_class_transfers",
        verbose_name="Người yêu cầu",
    )
    requested_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Ngày gửi yêu cầu",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_class_transfers",
        verbose_name="Quản lý phê duyệt",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ngày phê duyệt",
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="performed_class_transfers",
        verbose_name="Người thực hiện chuyển",
    )
    transferred_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Ngày chuyển lớp",
    )

    def __str__(self):
        return (
            f"{self.student} — {self.source_class} → "
            f"{self.target_class} ({self.get_status_display()})"
        )

    class Meta:
        verbose_name = "Lịch sử chuyển lớp"
        verbose_name_plural = "Lịch sử chuyển lớp"
        ordering = ["-requested_at"]
# ==============================
# QUẢN LÝ ĐIỂM SỐ
# ==============================
class Grade(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name="Học viên"
    )

    english_class = models.ForeignKey(
        EnglishClass,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name="Lớp học"
    )

    oral_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        verbose_name="Điểm nói"
    )

    listening_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        verbose_name="Điểm nghe"
    )

    reading_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        verbose_name="Điểm đọc"
    )

    writing_score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        verbose_name="Điểm viết"
    )

    exam_date = models.DateField(
        verbose_name="Ngày kiểm tra"
    )

    note = models.TextField(
        blank=True,
        verbose_name="Nhận xét"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    @property
    def average_score(self):
        return round(
            (
                self.oral_score
                + self.listening_score
                + self.reading_score
                + self.writing_score
            ) / 4,
            2
        )

    @property
    def classification(self):
        score = self.average_score

        if score >= 8:
            return "Giỏi"
        elif score >= 6.5:
            return "Khá"
        elif score >= 5:
            return "Trung bình"
        return "Yếu"

    def __str__(self):
        return f"{self.student.full_name} - {self.english_class.name}"

    class Meta:
        verbose_name = "Điểm số"
        verbose_name_plural = "Danh sách điểm số"
        ordering = ['-exam_date']


class AssessmentEvent(models.Model):
    english_class = models.ForeignKey(
        EnglishClass,
        on_delete=models.PROTECT,
        related_name="assessment_events",
        verbose_name="Lớp học",
    )
    component = models.ForeignKey(
        AssessmentComponent,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name="Thành phần đánh giá",
    )
    participants = models.ManyToManyField(
        Enrollment,
        blank=True,
        related_name="assessment_events",
        verbose_name="Học viên tham gia",
    )
    name = models.CharField(max_length=180, verbose_name="Tên lần đánh giá")
    assessment_date = models.DateField(db_index=True, verbose_name="Ngày đánh giá")
    max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Điểm tối đa (để trống dùng điểm thành phần)",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_assessment_events",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.english_class_id
            and self.component_id
            and self.english_class.assessment_policy_id
            != self.component.policy_id
        ):
            raise ValidationError(
                "Thành phần đánh giá phải thuộc quy chế đang gán cho lớp."
            )
        if self.max_score is not None and self.max_score <= 0:
            raise ValidationError({"max_score": "Điểm tối đa phải lớn hơn 0."})

    def __str__(self):
        return f"{self.english_class} — {self.name}"

    class Meta:
        verbose_name = "Đợt đánh giá"
        verbose_name_plural = "Đợt đánh giá"
        ordering = ["-assessment_date", "name"]


class AssessmentResult(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chưa nhập điểm"
        GRADED = "graded", "Đã chấm"
        ABSENT = "absent", "Vắng thi"
        EXEMPT = "exempt", "Được miễn"
        VOID = "void", "Đã hủy"

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        related_name="assessment_results",
        verbose_name="Ghi danh",
    )
    event = models.ForeignKey(
        AssessmentEvent,
        on_delete=models.PROTECT,
        related_name="results",
        verbose_name="Đợt đánh giá",
    )
    attempt_number = models.PositiveSmallIntegerField(default=1, verbose_name="Lần thi")
    score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Điểm",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Trạng thái điểm",
    )
    feedback = models.TextField(blank=True, verbose_name="Nhận xét")
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="graded_assessment_results",
        null=True,
        blank=True,
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}
        if (
            self.enrollment_id
            and self.event_id
            and self.enrollment.english_class_id != self.event.english_class_id
        ):
            errors["enrollment"] = "Điểm phải thuộc học viên của đúng lớp đánh giá."
        if self.status == self.Status.GRADED and self.score is None:
            errors["score"] = "Kết quả đã chấm phải có điểm."
        if self.status != self.Status.GRADED and self.score is not None:
            errors["score"] = "Chỉ kết quả đã chấm mới được có điểm số."
        if self.status == self.Status.GRADED and self.score is not None:
            maximum = (
                self.event.max_score
                if self.event.max_score is not None
                else self.event.component.max_score
            )
            if self.score < 0 or self.score > maximum:
                errors["score"] = f"Điểm phải nằm trong khoảng 0 đến {maximum}."
        if self.attempt_number < 1:
            errors["attempt_number"] = "Lần đánh giá phải từ 1 trở lên."
        if errors:
            raise ValidationError(errors)

    class Meta:
        verbose_name = "Kết quả đánh giá"
        verbose_name_plural = "Kết quả đánh giá"
        constraints = [
            models.UniqueConstraint(
                fields=("enrollment", "event", "attempt_number"),
                name="unique_enrollment_event_attempt",
            ),
        ]


class FinalResult(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "Đang học"
        PENDING_RESULTS = "pending_results", "Chờ đủ điểm"
        PASSED = "passed", "Đạt"
        NOT_PASSED = "not_passed", "Chưa đạt"
        EXEMPTED = "exempted", "Được miễn"
        WITHDRAWN = "withdrawn", "Đã rút"

    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.PROTECT,
        related_name="final_results",
        verbose_name="Ghi danh",
    )
    policy = models.ForeignKey(
        AssessmentPolicy,
        on_delete=models.PROTECT,
        related_name="final_results",
        verbose_name="Phiên bản quy chế",
    )
    final_score = models.DecimalField(
        max_digits=9,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Điểm tổng kết",
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        db_index=True,
        verbose_name="Kết quả",
    )
    calculation_details = models.JSONField(default=dict, blank=True)
    calculated_at = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="confirmed_final_results",
        null=True,
        blank=True,
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Kết quả tổng kết"
        verbose_name_plural = "Kết quả tổng kết"
        constraints = [
            models.UniqueConstraint(
                fields=("enrollment",),
                name="unique_final_result_per_enrollment",
            ),
        ]


class AssessmentResultAudit(models.Model):
    result = models.ForeignKey(
        AssessmentResult,
        on_delete=models.PROTECT,
        related_name="audit_entries",
    )
    old_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    new_score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    reason = models.TextField()
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assessment_result_audits",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lịch sử chỉnh điểm"
        verbose_name_plural = "Lịch sử chỉnh điểm"
        ordering = ["-changed_at"]


class Tuition(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="tuitions",
        verbose_name="Học viên"
    )

    english_class = models.ForeignKey(
        EnglishClass,
        on_delete=models.PROTECT,
        related_name="tuitions",
        verbose_name="Lớp học"
    )

    total_fee = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name="Tổng học phí"
    )

    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=0,
        verbose_name="Số tiền đã đóng"
    )

    payment_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Ngày thanh toán gần nhất"
    )

    note = models.TextField(
        blank=True,
        verbose_name="Ghi chú"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Ngày tạo"
    )

    @property
    def remaining_amount(self):
        return max(self.total_fee - self.paid_amount, 0)

    @property
    def payment_status(self):
        if self.paid_amount >= self.total_fee:
            return "Đã thanh toán"
        elif self.paid_amount > 0:
            return "Thanh toán một phần"
        return "Chưa thanh toán"

    @property
    def is_paid(self):
        return bool(self.total_fee and self.paid_amount >= self.total_fee)

    def __str__(self):
        return f"{self.student.full_name} - {self.english_class.name}"

    class Meta:
        verbose_name = "Học phí"
        verbose_name_plural = "Danh sách học phí"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=("student", "english_class"),
                name="unique_student_class_tuition",
            ),
        ]


def generate_receipt_code():
    import uuid
    from django.utils import timezone
    return f"PT-{timezone.now().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"


class PaymentTransaction(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Tiền mặt"
        BANK_TRANSFER = "bank_transfer", "Chuyển khoản"
        CARD = "card", "Thẻ tín dụng / POS"
        ONLINE = "online", "Cổng thanh toán online"

    tuition = models.ForeignKey(
        Tuition,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Phiếu học phí",
    )
    receipt_code = models.CharField(
        max_length=40,
        unique=True,
        default=generate_receipt_code,
        verbose_name="Mã biên lai / Số phiếu thu",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="Số tiền đóng (VNĐ)",
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name="Hình thức thanh toán",
    )
    payment_date = models.DateField(
        default=timezone.localdate,
        db_index=True,
        verbose_name="Ngày nộp tiền",
    )
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="collected_payments",
        null=True,
        blank=True,
        verbose_name="Người thu tiền",
    )
    note = models.TextField(
        blank=True,
        verbose_name="Ghi chú thanh toán",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Thời điểm ghi nhận",
    )

    def clean(self):
        from decimal import Decimal
        from django.core.exceptions import ValidationError
        if self.amount <= 0:
            raise ValidationError({"amount": "Số tiền đóng phải lớn hơn 0 VNĐ."})
        if self.tuition_id:
            existing_paid = self.tuition.transactions.exclude(pk=self.pk).aggregate(
                total=models.Sum("amount")
            )["total"] or Decimal("0")
            if existing_paid + self.amount > self.tuition.total_fee:
                raise ValidationError({
                    "amount": f"Số tiền đóng vượt quá tổng học phí còn lại (Tổng học phí: {self.tuition.total_fee:,.0f} đ, đã đóng: {existing_paid:,.0f} đ)."
                })

    def save(self, *args, **kwargs):
        from decimal import Decimal
        self.full_clean()
        super().save(*args, **kwargs)
        total_paid = self.tuition.transactions.aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")
        self.tuition.paid_amount = total_paid
        latest_date = self.tuition.transactions.order_by("-payment_date").values_list("payment_date", flat=True).first()
        self.tuition.payment_date = latest_date or self.payment_date
        self.tuition.save(update_fields=["paid_amount", "payment_date"])

    def delete(self, *args, **kwargs):
        from decimal import Decimal
        tuition = self.tuition
        super().delete(*args, **kwargs)
        total_paid = tuition.transactions.aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0")
        tuition.paid_amount = total_paid
        latest_date = tuition.transactions.order_by("-payment_date").values_list("payment_date", flat=True).first()
        tuition.payment_date = latest_date
        tuition.save(update_fields=["paid_amount", "payment_date"])

    def __str__(self):
        return f"{self.receipt_code} - {self.tuition.student.full_name} ({self.amount:,.0f} đ)"

    class Meta:
        verbose_name = "Giao dịch thu học phí"
        verbose_name_plural = "Lịch sử thu học phí"
        ordering = ["-payment_date", "-id"]



# =====================================================
# QUAN LY CHUNG CHI VA XAC MINH BLOCKCHAIN
# =====================================================

import uuid


def generate_certificate_code():
    """Tao ma chung chi duy nhat."""
    return f"CERT-{uuid.uuid4().hex[:12].upper()}"


class Certificate(models.Model):
    certificate_code = models.CharField(
        max_length=50,
        unique=True,
        default=generate_certificate_code,
        verbose_name="Mã chứng chỉ"
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="certificates",
        verbose_name="Học viên"
    )

    english_class = models.ForeignKey(
        EnglishClass,
        on_delete=models.PROTECT,
        related_name="certificates",
        verbose_name="Lớp học"
    )

    issue_date = models.DateField(
        db_index=True,
        verbose_name="Ngày cấp"
    )

    score = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        verbose_name="Điểm tổng kết"
    )

    classification = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Xếp loại"
    )

    data_hash = models.CharField(
        max_length=66,
        blank=True,
        default="",
        verbose_name="Mã băm Blockchain"
    )

    transaction_hash = models.CharField(
        max_length=66,
        blank=True,
        default="",
        verbose_name="Mã giao dịch Blockchain"
    )

    block_number = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="Số Block"
    )

    blockchain_status = models.CharField(
        max_length=20,
        default="pending",
        db_index=True,
        choices=[
            ("pending", "Chưa ghi Blockchain"),
            ("issued", "Đã ghi Blockchain"),
            ("failed", "Ghi Blockchain thất bại"),
        ],
        verbose_name="Trạng thái Blockchain"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Ngày tạo"
    )

    def __str__(self):
        return (
            f"{self.certificate_code} - "
            f"{self.student.full_name}"
        )

    class Meta:
        verbose_name = "Chứng chỉ"
        verbose_name_plural = "Danh sách chứng chỉ"
        ordering = ["-created_at"]


# =====================================================
# QUẢN LÝ BUỔI HỌC VÀ ĐIỂM DANH CHUYÊN CẦN
# =====================================================

class ClassSession(models.Model):
    """Buổi học cụ thể của một lớp học."""

    english_class = models.ForeignKey(
        EnglishClass,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name="Lớp học",
    )
    session_number = models.PositiveIntegerField(
        verbose_name="Buổi thứ",
    )
    session_date = models.DateField(
        db_index=True,
        verbose_name="Ngày học",
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Giờ bắt đầu",
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Giờ kết thúc",
    )
    room = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Phòng học",
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conducted_sessions",
        verbose_name="Giáo viên đứng lớp",
    )
    topic = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Chủ đề / Bài học",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Nội dung / Ghi chú buổi học",
    )
    is_completed = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Đã hoàn thành",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Thời điểm tạo",
    )

    def __str__(self):
        return f"{self.english_class.name} — Buổi {self.session_number} ({self.session_date})"

    class Meta:
        verbose_name = "Buổi học"
        verbose_name_plural = "Danh sách buổi học"
        ordering = ["english_class", "session_number"]
        constraints = [
            models.UniqueConstraint(
                fields=("english_class", "session_number"),
                name="unique_class_session_number",
            ),
        ]


class Attendance(models.Model):
    """Bản ghi điểm danh của học viên trong từng buổi học."""

    class AttendanceStatus(models.TextChoices):
        PRESENT = "present", "Có mặt"
        ABSENT_EXCUSED = "absent_excused", "Vắng có phép"
        ABSENT_UNEXCUSED = "absent_unexcused", "Vắng không phép"
        LATE = "late", "Đi muộn"

    session = models.ForeignKey(
        ClassSession,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="Buổi học",
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendances",
        verbose_name="Học viên",
    )
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
        db_index=True,
        verbose_name="Trạng thái điểm danh",
    )
    note = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ghi chú",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_attendances",
        verbose_name="Người điểm danh",
    )
    recorded_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Thời điểm ghi nhận",
    )

    def __str__(self):
        return f"{self.student.full_name} — {self.session} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Điểm danh"
        verbose_name_plural = "Danh sách điểm danh"
        ordering = ["session", "student__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=("session", "student"),
                name="unique_session_student_attendance",
            ),
        ]

