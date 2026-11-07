# 4.5 MÔ TẢ CƠ SỞ DỮ LIỆU VẬT LÝ (DATABASE SCHEMA)
## HỆ THỐNG QUẢN LÝ TRUNG TÂM TIẾNG ANH VISTA TÍCH HỢP BLOCKCHAIN
*Hệ quản trị CSDL: MySQL 8.0 | Bảng mã ký tự: utf8mb4_unicode_ci*

---

### TỔNG QUAN LƯỢC ĐỒ CƠ SỞ DỮ LIỆU
Cơ sở dữ liệu của hệ thống VISTA được tối ưu hóa theo mô hình 11 bảng cốt lõi, áp dụng kỹ thuật chuẩn hóa kết hợp phi chuẩn hóa có kiểm soát (Controlled Denormalization) nhằm đáp ứng toàn diện 12 nhóm nghiệp vụ quản lý đào tạo, tài chính và xác thực chứng chỉ Blockchain.

| STT | Tên bảng (Table) | Phân hệ nghiệp vụ | Chức năng chính |
|:---:|---|---|---|
| 1 | `users` | Quản trị & Phân quyền | Quản lý tài khoản đăng nhập nội bộ (Admin, Giáo vụ, Kế toán) |
| 2 | `teachers` | Quản lý Đào tạo | Hồ sơ lý lịch và chuyên môn giảng dạy của giảng viên |
| 3 | `students` | Quản lý Đào tạo | Hồ sơ nhân thân học viên và mã định danh `student_code` |
| 4 | `courses` | Quản lý Đào tạo | Danh mục khóa học, biểu phí tiêu chuẩn và thời lượng đào tạo |
| 5 | `assessment_policies`| Quy chế đánh giá | Thang điểm, điểm đạt chuẩn và cơ cấu tỷ trọng điểm (%) |
| 6 | `classes` | Quản lý Đào tạo | Lớp học cụ thể theo khóa học, giảng viên phụ trách và sĩ số |
| 7 | `enrollments` | Quản lý Đào tạo | Quá trình học tập của học viên và nhật ký chuyển lớp |
| 8 | `attendance` | Chuyên cần & Điểm danh | Nhật ký theo dõi điểm danh chuyên cần của học viên theo ngày |
| 9 | `grades` | Đánh giá & Điểm số | Điểm số 4 kỹ năng (Nghe, Nói, Đọc, Viết) và điểm tổng kết |
| 10| `tuitions` | Quản lý Tài chính | Nghĩa vụ học phí, số tiền đã đóng, biên lai và trạng thái công nợ |
| 11| `certificates` | Chứng chỉ & Blockchain | Cấp chứng chỉ tốt nghiệp, lưu mã băm SHA-256 và TxHash Ethereum |

---

### CHI TIẾT CÁC BẢNG DỮ LIỆU

#### 1. Bảng `users` (Tài khoản người dùng nội bộ)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã định danh người dùng |
| `username` | VARCHAR(150) | | UNIQUE, NOT NULL | Tên đăng nhập |
| `password` | VARCHAR(255) | | NOT NULL | Mật khẩu băm (BCrypt/Argon2) |
| `full_name` | VARCHAR(150) | | NOT NULL | Họ và tên đầy đủ |
| `email` | VARCHAR(254) | | NOT NULL | Địa chỉ email |
| `role` | ENUM | | NOT NULL | Vai trò: 'ADMIN', 'ACADEMIC', 'FINANCE' |
| `is_active` | BOOLEAN | | DEFAULT TRUE | Trạng thái hoạt động |
| `created_at` | DATETIME | | DEFAULT CURRENT_TIMESTAMP | Ngày tạo tài khoản |

#### 2. Bảng `teachers` (Hồ sơ giảng viên)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã giảng viên |
| `user_id` | INT | FK | UNIQUE, NULL | Liên kết tài khoản `users(id)` |
| `full_name` | VARCHAR(150) | | NOT NULL | Họ và tên giảng viên |
| `email` | VARCHAR(254) | | UNIQUE, NOT NULL | Email liên hệ |
| `phone` | VARCHAR(20) | | NOT NULL | Số điện thoại |
| `specialization`| VARCHAR(100) | | NOT NULL | Chuyên môn (IELTS, TOEIC, Giao tiếp) |
| `address` | TEXT | | NULL | Địa chỉ nơi ở |
| `is_active` | BOOLEAN | | DEFAULT TRUE | Trạng thái giảng dạy |

#### 3. Bảng `students` (Hồ sơ học viên)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã học viên nội bộ |
| `user_id` | INT | FK | UNIQUE, NULL | Liên kết tài khoản `users(id)` |
| `student_code` | VARCHAR(50) | | UNIQUE, NOT NULL | Mã học viên hiển thị (vd: HV-0001) |
| `full_name` | VARCHAR(150) | | NOT NULL | Họ và tên học viên |
| `email` | VARCHAR(254) | | UNIQUE, NOT NULL | Email liên hệ |
| `phone` | VARCHAR(20) | | NOT NULL | Số điện thoại |
| `date_of_birth`| DATE | | NOT NULL | Ngày tháng năm sinh |
| `address` | TEXT | | NULL | Địa chỉ cư trú |
| `is_active` | BOOLEAN | | DEFAULT TRUE | Trạng thái hoạt động |
| `created_at` | DATETIME | | DEFAULT CURRENT_TIMESTAMP | Ngày tiếp nhận hồ sơ |

#### 4. Bảng `courses` (Khóa học)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã khóa học |
| `name` | VARCHAR(200) | | NOT NULL | Tên khóa học |
| `description` | TEXT | | NULL | Mô tả lộ trình học |
| `tuition_fee` | DECIMAL(12,2) | | NOT NULL, DEFAULT 0 | Học phí tiêu chuẩn |
| `duration_hours`| INT | | NOT NULL, DEFAULT 60 | Thời lượng đào tạo (giờ) |
| `is_active` | BOOLEAN | | DEFAULT TRUE | Trạng thái tuyển sinh |

#### 5. Bảng `assessment_policies` (Quy chế đánh giá - Đã gộp thành phần điểm)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã quy chế |
| `course_id` | INT | FK | UNIQUE, NOT NULL | Áp dụng cho khóa học `courses(id)` (1-1) |
| `name` | VARCHAR(150) | | NOT NULL | Tên quy chế |
| `version` | INT | | NOT NULL, DEFAULT 1 | Phiên bản quy chế |
| `scale_type` | ENUM | | NOT NULL | Thang điểm: 'SCORE_10', 'IELTS_BAND' |
| `max_score` | DECIMAL(4,2) | | NOT NULL, DEFAULT 10 | Điểm trần tối đa |
| `pass_score` | DECIMAL(4,2) | | NOT NULL, DEFAULT 5 | Điểm đạt chuẩn tối thiểu |
| `attendance_weight`| DECIMAL(3,2) | | NOT NULL, DEFAULT 0.1 | Tỷ trọng chuyên cần (10%) |
| `midterm_weight`| DECIMAL(3,2) | | NOT NULL, DEFAULT 0.3 | Tỷ trọng điểm giữa kỳ (30%) |
| `final_weight` | DECIMAL(3,2) | | NOT NULL, DEFAULT 0.6 | Tỷ trọng điểm cuối kỳ (60%) |
| `status` | ENUM | | DEFAULT 'ACTIVE' | Trạng thái: 'DRAFT', 'ACTIVE', 'ARCHIVED' |
| `effective_from`| DATE | | NOT NULL | Ngày bắt đầu áp dụng |
| `effective_to` | DATE | | NULL | Ngày hết hiệu lực |

#### 6. Bảng `classes` (Lớp học)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã lớp học |
| `course_id` | INT | FK | NOT NULL | Thuộc khóa học `courses(id)` |
| `teacher_id` | INT | FK | NOT NULL | Giảng viên đứng lớp `teachers(id)` |
| `name` | VARCHAR(100) | | NOT NULL | Tên định danh lớp (IELTS-2026A) |
| `start_date` | DATE | | NOT NULL | Ngày khai giảng |
| `end_date` | DATE | | NOT NULL | Ngày bế giảng dự kiến |
| `max_students` | INT | | DEFAULT 25 | Sĩ số tối đa |
| `is_active` | BOOLEAN | | DEFAULT TRUE | Trạng thái mở lớp |

#### 7. Bảng `enrollments` (Ghi danh & Lịch sử chuyển lớp)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã bản ghi ghi danh |
| `student_id` | INT | FK | NOT NULL | Học viên `students(id)` |
| `class_id` | INT | FK | NOT NULL | Lớp học `classes(id)` |
| `enrolled_at` | DATE | | NOT NULL | Ngày nhập học |
| `status` | ENUM | | DEFAULT 'ACTIVE' | Trạng thái: 'ACTIVE', 'COMPLETED', 'DROPPED', 'TRANSFERRED' |
| `transfer_reason`| TEXT | | NULL | Lý do nếu có chuyển lớp |
| `note` | TEXT | | NULL | Ghi chú học vụ |

#### 8. Bảng `attendance` (Điểm danh chuyên cần)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã lượt điểm danh |
| `class_id` | INT | FK | NOT NULL | Lớp học `classes(id)` |
| `student_id` | INT | FK | NOT NULL | Học viên `students(id)` |
| `session_date` | DATE | | NOT NULL | Ngày diễn ra buổi học |
| `status` | ENUM | | NOT NULL | Chuyên cần: 'PRESENT', 'ABSENT_EXCUSED', 'ABSENT_UNEXCUSED', 'LATE' |
| `note` | VARCHAR(255) | | NULL | Lý do nghỉ / phép |
| `recorded_at` | DATETIME | | DEFAULT CURRENT_TIMESTAMP | Thời điểm ghi nhận |

#### 9. Bảng `grades` (Bảng điểm bài thi & Đánh giá kết quả)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã bảng điểm |
| `enrollment_id`| INT | FK | UNIQUE, NOT NULL | Quá trình học `enrollments(id)` (1-1) |
| `oral_score` | DECIMAL(4,2) | | DEFAULT 0.00 | Điểm Nói (Speaking) |
| `listening_score`| DECIMAL(4,2)| | DEFAULT 0.00 | Điểm Nghe (Listening) |
| `reading_score`| DECIMAL(4,2) | | DEFAULT 0.00 | Điểm Đọc (Reading) |
| `writing_score`| DECIMAL(4,2) | | DEFAULT 0.00 | Điểm Viết (Writing) |
| `average_score`| DECIMAL(4,2) | | DEFAULT 0.00 | Điểm trung bình tổng kết môn |
| `is_passed` | BOOLEAN | | DEFAULT FALSE | Đạt chuẩn tốt nghiệp hay chưa |
| `exam_date` | DATE | | NOT NULL | Ngày thi / kiểm tra |
| `note` | TEXT | | NULL | Nhận xét của giảng viên chấm |

#### 10. Bảng `tuitions` (Học phí & Biên lai thu tiền)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã phiếu học phí |
| `enrollment_id`| INT | FK | UNIQUE, NOT NULL | Quá trình học `enrollments(id)` (1-1) |
| `total_fee` | DECIMAL(12,2) | | NOT NULL, DEFAULT 0 | Tổng học phí phải đóng |
| `paid_amount` | DECIMAL(12,2) | | NOT NULL, DEFAULT 0 | Số tiền đã đóng |
| `payment_date` | DATE | | NULL | Ngày nộp tiền |
| `payment_method`| ENUM | | DEFAULT 'CASH' | Phương thức: 'CASH', 'BANK_TRANSFER', 'MOMO', 'VNPAY', 'CARD' |
| `receipt_code` | VARCHAR(50) | | UNIQUE, NULL | Số biên lai thu phí (vd: HD-2026-001) |
| `is_paid` | BOOLEAN | | DEFAULT FALSE | Đã nộp đủ học phí hay chưa |
| `created_at` | DATETIME | | DEFAULT CURRENT_TIMESTAMP | Thời điểm lập phiếu |

#### 11. Bảng `certificates` (Chứng chỉ tốt nghiệp & Neo Blockchain)
| Tên cột | Kiểu dữ liệu | Khóa | Ràng buộc | Ý nghĩa |
|---|---|:---:|---|---|
| `id` | INT | PK | AUTO_INCREMENT | Mã chứng chỉ |
| `enrollment_id`| INT | FK | UNIQUE, NOT NULL | Quá trình học `enrollments(id)` (1-1) |
| `certificate_code`| VARCHAR(100)| | UNIQUE, NOT NULL | Số hiệu chứng chỉ văn bằng (CERT-2026-001) |
| `issue_date` | DATE | | NOT NULL | Ngày cấp bằng |
| `final_score` | DECIMAL(4,2) | | NOT NULL | Điểm tổng kết in trên bằng |
| `classification`| VARCHAR(50) | | NOT NULL | Xếp loại (Xuất sắc, Giỏi, Khá) |
| `data_hash` | VARCHAR(66) | | NOT NULL | Mã băm SHA-256 dữ liệu chứng chỉ |
| `transaction_hash`| VARCHAR(66)| | NULL | Mã băm giao dịch (TxHash) Ethereum |
| `block_number` | BIGINT | | NULL | Số khối Block trên mạng Blockchain |
| `blockchain_status`| ENUM | | DEFAULT 'PENDING' | Trạng thái: 'PENDING', 'ANCHORED', 'FAILED', 'VERIFIED' |
| `created_at` | DATETIME | | DEFAULT CURRENT_TIMESTAMP | Thời điểm cấp |

