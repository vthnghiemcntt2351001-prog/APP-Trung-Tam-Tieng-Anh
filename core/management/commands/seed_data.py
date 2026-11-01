# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import (
    Course,
    Teacher,
    EnglishClass,
    Student,
    Enrollment,
    Tuition,
    Certificate,
)


class Command(BaseCommand):
    help = "Khoi tao du lieu mau phong phu bang Tieng Viet co dau chuan cho MySQL"

    def handle(self, *args, **options):
        self.stdout.write("Dang nap du lieu mau Tieng Viet co dau vao MySQL...")

        # 1. Khóa học có dấu
        courses_data = [
            {
                "name": "IELTS Cấp Tốc 6.5+",
                "description": "Luyện thi IELTS 4 kỹ năng cam kết chuẩn đầu ra 6.5+.",
                "tuition": Decimal("8500000"),
                "duration": 6,
            },
            {
                "name": "TOEIC 4 Kỹ Năng 750+",
                "description": "Chuyên sâu Nghe - Đọc - Nói - Viết cho sinh viên và người đi làm.",
                "tuition": Decimal("4800000"),
                "duration": 3,
            },
            {
                "name": "Tiếng Anh Giao Tiếp Doanh Nghiệp",
                "description": "Thực chiến email thương mại, thuyết trình và đàm phán quốc tế.",
                "tuition": Decimal("3900000"),
                "duration": 3,
            },
            {
                "name": "Luyện Thi B2 Vstep",
                "description": "Luyện đề và phản xạ định dạng đề thi Vstep chuẩn Bộ Giáo Dục.",
                "tuition": Decimal("5200000"),
                "duration": 4,
            },
            {
                "name": "Tiếng Anh Nền Tảng Cho Người Mất Gốc",
                "description": "Lấy lại phát âm chuẩn quốc tế và ngữ pháp căn bản từ con số 0.",
                "tuition": Decimal("2500000"),
                "duration": 2,
            },
        ]

        courses = []
        for c in courses_data:
            course, _ = Course.objects.update_or_create(
                name=c["name"],
                defaults={
                    "description": c["description"],
                    "tuition": c["tuition"],
                    "duration": c["duration"],
                },
            )
            courses.append(course)
        self.stdout.write(f"- Da cap nhat {len(courses)} khoa hoc tieng Viet co dau.")

        # 2. Giáo viên có dấu
        teachers_data = [
            {
                "full_name": "Thầy John Smith",
                "email": "john.smith@englishcenter.edu.vn",
                "phone": "0901234567",
                "specialization": "IELTS Master Trainer (Đại học Cambridge)",
                "address": "Quận 1, TP. Hồ Chí Minh",
            },
            {
                "full_name": "Cô Nguyễn Thị Mai Lan",
                "email": "mailan.nguyen@englishcenter.edu.vn",
                "phone": "0912345678",
                "specialization": "Thạc sĩ Sư phạm Tiếng Anh (IELTS 8.5)",
                "address": "Quận 3, TP. Hồ Chí Minh",
            },
            {
                "full_name": "Thầy Trần Minh Hoàng",
                "email": "hoang.tran@englishcenter.edu.vn",
                "phone": "0987654321",
                "specialization": "Chuyên gia TOEIC 990 (8 năm kinh nghiệm)",
                "address": "Quận Bình Thạnh, TP. Hồ Chí Minh",
            },
            {
                "full_name": "Cô Emily Watson",
                "email": "emily.watson@englishcenter.edu.vn",
                "phone": "0933445566",
                "specialization": "Giảng viên Bản ngữ - Tiếng Anh Thương mại",
                "address": "Quận 7, TP. Hồ Chí Minh",
            },
        ]

        teachers = []
        for t in teachers_data:
            teacher, _ = Teacher.objects.update_or_create(
                email=t["email"],
                defaults={
                    "full_name": t["full_name"],
                    "phone": t["phone"],
                    "specialization": t["specialization"],
                    "address": t["address"],
                },
            )
            teachers.append(teacher)
        self.stdout.write(f"- Da cap nhat {len(teachers)} giao vien tieng Viet co dau.")

        # 3. Lớp học có dấu
        today = timezone.localdate()
        classes_data = [
            {
                "name": "IELTS-K01 (Tối 2-4-6)",
                "course": courses[0],
                "teacher": teachers[0],
                "start_date": today,
                "end_date": today + datetime.timedelta(days=180),
                "max_students": 20,
            },
            {
                "name": "IELTS-K02 (Tối 3-5-7)",
                "course": courses[0],
                "teacher": teachers[1],
                "start_date": today - datetime.timedelta(days=30),
                "end_date": today + datetime.timedelta(days=150),
                "max_students": 18,
            },
            {
                "name": "TOEIC-A01 (Sáng 2-4-6)",
                "course": courses[1],
                "teacher": teachers[2],
                "start_date": today - datetime.timedelta(days=15),
                "end_date": today + datetime.timedelta(days=75),
                "max_students": 25,
            },
            {
                "name": "COMM-B01 (Tối Thứ 7 - Chủ Nhật)",
                "course": courses[2],
                "teacher": teachers[3],
                "start_date": today,
                "end_date": today + datetime.timedelta(days=90),
                "max_students": 15,
            },
            {
                "name": "FOUNDATION-01 (Tối 3-5-7)",
                "course": courses[4],
                "teacher": teachers[1],
                "start_date": today - datetime.timedelta(days=10),
                "end_date": today + datetime.timedelta(days=50),
                "max_students": 22,
            },
        ]

        classes = []
        for cl in classes_data:
            c_obj, _ = EnglishClass.objects.update_or_create(
                name=cl["name"],
                defaults={
                    "course": cl["course"],
                    "teacher": cl["teacher"],
                    "start_date": cl["start_date"],
                    "end_date": cl["end_date"],
                    "max_students": cl["max_students"],
                },
            )
            classes.append(c_obj)
        self.stdout.write(f"- Da cap nhat {len(classes)} lop hoc tieng Viet co dau.")

        # 4. Học viên (Tiếng Việt có dấu chuẩn)
        students_data = [
            ("Nguyễn Hoàng Hải Đăng", "haidang@gmail.com", "0908112233", "2002-05-14", "Quận 1, TP. Hồ Chí Minh"),
            ("Trần Thị Bích Ngọc", "bichngoc@gmail.com", "0918223344", "2003-08-22", "TP. Biên Hòa, Đồng Nai"),
            ("Lê Văn Quốc Huy", "quochuy@gmail.com", "0977334455", "2001-11-09", "TP. Thủ Dầu Một, Bình Dương"),
            ("Phạm Minh Khoa", "minhkhoa@gmail.com", "0934556677", "2000-02-18", "Tân An, Long An"),
            ("Võ Hoàng Yến Nhi", "yennhi@gmail.com", "0945667788", "2004-09-30", "Quận 5, TP. Hồ Chí Minh"),
            ("Đặng Quốc Bảo", "quocbao@gmail.com", "0988776655", "2002-01-25", "TP. Vũng Tàu"),
            ("Bùi Thị Thu Thảo", "thuthao@gmail.com", "0966554433", "2003-07-12", "Ninh Kiều, Cần Thơ"),
            ("Hoàng Văn Thái Sơn", "thaison@gmail.com", "0922334411", "2001-04-05", "Mỹ Tho, Tiền Giang"),
            ("Đoàn Ngọc Anh Thư", "anhthu@gmail.com", "0911224455", "2004-12-01", "Quận Bình Thạnh, TP. Hồ Chí Minh"),
            ("Vũ Đình Gia Huy", "giahuy@gmail.com", "0933778899", "2002-06-19", "Phan Thiết, Bình Thuận"),
            ("Trịnh Mỹ Duyên", "myduyen@gmail.com", "0944889900", "2003-03-15", "TP. Bến Tre"),
            ("Ngô Thanh Tùng", "thanhtung@gmail.com", "0955990011", "2000-10-28", "Long Xuyên, An Giang"),
            ("Đinh Thị Kim Ngân", "kimngan@gmail.com", "0977112244", "2002-08-08", "Quận Gò Vấp, TP. Hồ Chí Minh"),
            ("Phan Trọng Nghĩa", "trongnghia@gmail.com", "0988223355", "2001-05-20", "TP. Tây Ninh"),
            ("Lý Quỳnh Hương", "quynhhuong@gmail.com", "0900334466", "2004-07-04", "Quận Phú Nhuận, TP. Hồ Chí Minh"),
        ]

        students = []
        for name, email, phone, dob, addr in students_data:
            s_obj, _ = Student.objects.update_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "phone": phone,
                    "date_of_birth": datetime.date.fromisoformat(dob),
                    "address": addr,
                },
            )
            students.append(s_obj)
        self.stdout.write(f"- Da cap nhat {len(students)} hoc vien co dau day du.")

        # 5. Ghi danh & Học phí
        for i, s in enumerate(students):
            target_class = classes[i % len(classes)]
            Enrollment.objects.get_or_create(
                student=s,
                english_class=target_class,
                defaults={
                    "status": Enrollment.Status.STUDYING,
                    "enrolled_at": today,
                },
            )

            total = target_class.course.tuition
            if i % 3 == 0:
                paid = total
            elif i % 3 == 1:
                paid = total / Decimal("2")
            else:
                paid = Decimal("0")

            Tuition.objects.update_or_create(
                student=s,
                english_class=target_class,
                defaults={
                    "total_fee": total,
                    "paid_amount": paid,
                    "payment_date": today if paid > 0 else None,
                    "note": "Nộp học phí nhập học đợt đầu.",
                },
            )

        # 6. Chứng chỉ mẫu có dấu
        cert_data = [
            (students[0], classes[1], Decimal("8.0"), "Giỏi"),
            (students[3], classes[2], Decimal("7.5"), "Khá"),
            (students[7], classes[3], Decimal("8.5"), "Xuất sắc"),
        ]

        for st, cl, sc, clsf in cert_data:
            Certificate.objects.update_or_create(
                student=st,
                english_class=cl,
                defaults={
                    "issue_date": today,
                    "score": sc,
                    "classification": clsf,
                    "blockchain_status": "pending",
                },
            )

        self.stdout.write(self.style.SUCCESS("HOAN TAT! Toan bo du lieu MySQL da duoc cap nhat Tieng Viet co dau tuyet dep."))
