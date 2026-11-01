import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Student, Teacher, Course, EnglishClass, PaymentTransaction


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["full_name", "email", "phone", "date_of_birth", "address"]
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Họ và tên học viên (ví dụ: Nguyễn Văn A)",
                "required": True,
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "placeholder": "hocvien@example.com",
                "required": True,
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "09xxxxxxxx hoặc 03xxxxxxxx",
                "required": True,
            }),
            "date_of_birth": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
            }),
            "address": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Địa chỉ liên hệ / thường trú",
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        # Loại bỏ dấu cách hoặc dấu gạch ngang
        cleaned_phone = re.sub(r"[\s\-\.]", "", phone)
        if not re.match(r"^(0|\+84)[0-9]{9,10}$", cleaned_phone):
            raise ValidationError("Số điện thoại không hợp lệ (cần 10 chữ số, bắt đầu bằng 0 hoặc +84).")
        return cleaned_phone

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        query = Student.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise ValidationError(f"Email '{email}' đã được đăng ký bởi học viên khác.")
        return email


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["full_name", "email", "phone", "specialization", "address"]
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Họ và tên giáo viên",
                "required": True,
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "placeholder": "giaovien@example.com",
                "required": True,
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "09xxxxxxxx",
                "required": True,
            }),
            "specialization": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Chuyên môn giảng dạy (IELTS, TOEIC, Giao tiếp...)",
            }),
            "address": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "Địa chỉ liên hệ",
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        cleaned_phone = re.sub(r"[\s\-\.]", "", phone)
        if not re.match(r"^(0|\+84)[0-9]{9,10}$", cleaned_phone):
            raise ValidationError("Số điện thoại không hợp lệ (cần 10 chữ số).")
        return cleaned_phone

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        query = Teacher.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        if query.exists():
            raise ValidationError(f"Email '{email}' đã được sử dụng bởi giáo viên khác.")
        return email


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["name", "description", "tuition", "duration"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Tên khóa học (ví dụ: IELTS Master 7.5+)",
                "required": True,
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 4,
                "placeholder": "Mục tiêu đào tạo, đối tượng học viên và lộ trình...",
            }),
            "tuition": forms.NumberInput(attrs={
                "class": "form-input",
                "min": "0",
                "step": "100000",
                "placeholder": "Số tiền học phí (VNĐ)",
                "required": True,
            }),
            "duration": forms.NumberInput(attrs={
                "class": "form-input",
                "min": "1",
                "max": "36",
                "placeholder": "Thời lượng khóa học (tháng)",
                "required": True,
            }),
        }

    def clean_tuition(self):
        tuition = self.cleaned_data.get("tuition")
        if tuition is not None and tuition < 0:
            raise ValidationError("Học phí không thể là số âm.")
        return tuition

    def clean_duration(self):
        duration = self.cleaned_data.get("duration")
        if duration is not None and duration < 1:
            raise ValidationError("Thời lượng khóa học tối thiểu là 1 tháng.")
        return duration


class EnglishClassForm(forms.ModelForm):
    class Meta:
        model = EnglishClass
        fields = ["name", "course", "teacher", "start_date", "end_date", "max_students"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Tên lớp học (ví dụ: IELTS-K24-Tối 246)",
                "required": True,
            }),
            "course": forms.Select(attrs={
                "class": "form-select",
                "required": True,
            }),
            "teacher": forms.Select(attrs={
                "class": "form-select",
            }),
            "start_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
                "required": True,
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
            }),
            "max_students": forms.NumberInput(attrs={
                "class": "form-input",
                "min": "1",
                "max": "100",
                "value": "20",
                "required": True,
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            raise ValidationError({"end_date": "Ngày kết thúc khóa học phải sau hoặc cùng ngày bắt đầu."})

        return cleaned_data


class PaymentTransactionForm(forms.ModelForm):
    class Meta:
        model = PaymentTransaction
        fields = ["amount", "payment_method", "payment_date", "note"]
        widgets = {
            "amount": forms.NumberInput(attrs={
                "class": "form-input",
                "min": "1000",
                "step": "10000",
                "placeholder": "Số tiền nộp đợt này (VNĐ)",
                "required": True,
            }),
            "payment_method": forms.Select(attrs={
                "class": "form-select",
                "required": True,
            }),
            "payment_date": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",
                "required": True,
            }),
            "note": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 2,
                "placeholder": "Ghi chú thu ngân (ví dụ: Nộp tiền mặt tại quầy, chuyển khoản qua Techcombank...)",
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise ValidationError("Số tiền nộp phải lớn hơn 0 VNĐ.")
        return amount
