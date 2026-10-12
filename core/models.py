
from django.db import models


# ==============================
# QUẢN LÝ HỌC VIÊN
# ==============================
class Student(models.Model):
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
        verbose_name="Ngày tạo"
    )

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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Khóa học"
        verbose_name_plural = "Danh sách khóa học"


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

    students = models.ManyToManyField(
        Student,
        blank=True,
        related_name="english_classes",
        verbose_name="Học viên"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Lớp học"
        verbose_name_plural = "Danh sách lớp học"

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
        verbose_name="Ngày thanh toán gần nhất"
    )

    note = models.TextField(
        blank=True,
        verbose_name="Ghi chú"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
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

    def __str__(self):
        return f"{self.student.full_name} - {self.english_class.name}"

    class Meta:
        verbose_name = "Học phí"
        verbose_name_plural = "Danh sách học phí"
        ordering = ["-created_at"]


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
