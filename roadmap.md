# LỘ TRÌNH 30 NGÀY HOÀN THIỆN HỆ THỐNG VÀ CHUYỂN ĐỔI MYSQL
**Dự án:** Quản lý Trung tâm Tiếng Anh (`APP-Trung-Tam-Tieng-Anh`)  
**Mục tiêu:** Khắc phục triệt để các bất cập kỹ thuật, chuyển đổi cơ sở dữ liệu sang MySQL 8.0, chuẩn hóa nghiệp vụ và đạt chuẩn sẵn sàng vận hành thực tế.

---

## NGUYÊN TẮC THỰC HIỆN CỐT LÕI
1. **An toàn dữ liệu là số 1:** Luôn sao lưu (backup) cơ sở dữ liệu và file cấu hình trước mọi thao tác thay đổi schema hay di chuyển dữ liệu.
2. **Không làm gián đoạn luồng đang chạy:** Giữ nguyên kiến trúc Django Monolith hiện tại; chỉ tái cấu trúc và chuẩn hóa nội bộ, không đập đi xây lại.
3. **Commit vi mô (Atomic Commits):** Mỗi ngày hoàn thành một nhóm nhiệm vụ độc lập, kiểm thử xong mới tạo git commit tương ứng.
4. **Tách biệt môi trường:** Sử dụng `.env` để chuyển đổi linh hoạt giữa SQLite (phục vụ test nhanh) và MySQL (cho môi trường chạy chính).

---

## TỔNG QUAN 4 GIAI ĐOẠN (30 NGÀY)

```text
[TUẦN 1: NGÀY 01 - 07] ──> Khắc phục lỗi P0/P1, sửa Template thiếu, xử lý ngoại lệ Blockchain
            │
[TUẦN 2: NGÀY 08 - 14] ──> Thiết lập môi trường MySQL 8.0, tích hợp Driver & Migration an toàn
            │
[TUẦN 3: NGÀY 15 - 21] ──> Thống nhất hệ thống Điểm, hoàn thiện UI/UX, Báo cáo & Tài chính
            │
[TUẦN 4: NGÀY 22 - 30] ──> Viết Test tự động, Tối ưu hóa, Docker hóa & Đóng gói bàn giao
```

---

## CHI TIẾT LỘ TRÌNH TỪNG NGÀY

### TUẦN 1: KHẮC PHỤC LỖI CỐT LÕI, BẢO VỆ ỨNG DỤNG & CHUẨN BỊ MYSQL (NGÀY 01 - 07)

#### Ngày 01: Khắc phục lỗi P0 - Thiếu Template Chứng chỉ
* **Vấn đề:** Đường dẫn `/certificates/` gọi `core/certificates/list.html` nhưng tệp chưa tồn tại, gây lỗi `TemplateDoesNotExist (500)`.
* **Công việc:**
  1. Tạo tệp `core/templates/core/certificates/list.html` kế thừa `core/base.html`.
  2. Hiển thị bảng danh sách chứng chỉ đã cấp: Mã chứng chỉ, Tên học viên, Khóa học, Ngày cấp, Trạng thái Blockchain, Mã Transaction Hash rút gọn và nút "Xác thực".
  3. Bổ sung nút "Cấp chứng chỉ mới" dẫn đến form phát hành.
* **Nghiệm thu:** Truy cập `/certificates/` hiển thị giao diện mượt mà, không còn lỗi 500.

#### Ngày 02: Xử lý phòng thủ ngoại lệ Blockchain (Graceful Degradation)
* **Vấn đề:** Gọi Web3.py kết nối Ganache đồng bộ trong view; nếu node Ganache tắt, cả request bị treo hoặc crash.
* **Công việc:**
  1. Bọc khối gọi `blockchain_service` trong `try...except (ConnectionError, Exception)`.
  2. Nếu không kết nối được Ganache: Lưu chứng chỉ vào Database với trạng thái `PENDING_BLOCKCHAIN` thay vì làm sập trang.
  3. Thêm cờ thông báo `django.contrib.messages.warning` báo cho nhân viên học vụ biết dữ liệu đã lưu cục bộ và sẽ tự đồng bộ khi node online.
* **Nghiệm thu:** Tắt Ganache, thử cấp chứng chỉ -> Hệ thống vẫn lưu thành công vào CSDL và báo cảnh báo thân thiện.

#### Ngày 03: Dọn dẹp mã nguồn thừa & Rà soát Routing
* **Vấn đề:** File `core/views.py` chứa các import tương thích cũ không còn sử dụng, dễ gây nhầm lẫn luồng gọi.
* **Công việc:**
  1. Kiểm tra toàn bộ `core/urls.py` và `config/urls.py` để đảm bảo 100% routes trỏ trực tiếp vào `core/handlers/`.
  2. Đánh dấu deprecation hoặc dọn dẹp các hàm chuyển tiếp cũ trong `core/views.py`.
  3. Rà soát lại tất cả các view đã được bọc đúng Decorator phân quyền (`@admin_required`, `@academic_required`, `@finance_required`).
* **Nghiệm thu:** Chạy `python manage.py check` không có cảnh báo URL; truy cập trái quyền bị chuyển hướng hoặc chặn 403 đúng chuẩn.

#### Ngày 04: Cài đặt và Chuẩn bị môi trường MySQL 8.0 cục bộ
* **Mục tiêu:** Tạo máy chủ cơ sở dữ liệu MySQL sạch sẵn sàng kết nối.
* **Công việc:**
  1. Cài đặt MySQL 8.0 (qua MySQL Community Server, XAMPP hoặc Docker MySQL).
  2. Tạo Database `english_center_db` với cấu hình chuẩn tiếng Việt:
     ```sql
     CREATE DATABASE english_center_db 
     CHARACTER SET utf8mb4 
     COLLATE utf8mb4_unicode_ci;
     ```
  3. Tạo người dùng riêng `ec_user` cấp quyền đầy đủ trên database mới, không dùng quyền root trực tiếp.
* **Nghiệm thu:** Đăng nhập thành công vào database bằng tài khoản mới qua MySQL Workbench hoặc CLI.

#### Ngày 05: Thêm Driver kết nối MySQL vào dự án
* **Mục tiêu:** Kích hoạt khả năng kết nối MySQL trong môi trường ảo Python.
* **Công việc:**
  1. Kích hoạt `.venv`.
  2. Cài đặt thư viện `mysqlclient` (khuyến nghị chuẩn Django) hoặc `pymysql`:
     ```bash
     pip install mysqlclient
     ```
  3. Ghi lại phiên bản chính xác vào `requirements.txt`.
* **Nghiệm thu:** Chạy `python -c "import MySQLdb"` không gặp lỗi `ModuleNotFoundError`.

#### Ngày 06: Cập nhật cấu hình đa CSDL trong `config/settings.py`
* **Mục tiêu:** Hỗ trợ linh hoạt chuyển đổi giữa SQLite, PostgreSQL và MySQL qua biến môi trường.
* **Công việc:**
  1. Cập nhật khối `DATABASES` trong `config/settings.py` nhận diện `DB_ENGINE=mysql`.
  2. Bổ sung các tham số bảo vệ kết nối: `charset: utf8mb4`, `init_command: "SET sql_mode='STRICT_TRANS_TABLES'"`, `CONN_MAX_AGE: 60`.
  3. Cập nhật file `.env.example` mẫu để hướng dẫn cấu hình môi trường chuẩn.
* **Nghiệm thu:** Đặt `DB_ENGINE=sqlite` hệ thống chạy SQLite; đặt `DB_ENGINE=mysql` hệ thống trỏ đến MySQL.

#### Ngày 07: Kiểm tra tương thích Schema bằng Dry-Run Migration
* **Mục tiêu:** Xác minh 14 file migration hiện có có thể áp dụng 100% lên MySQL mà không phát sinh lỗi cú pháp.
* **Công việc:**
  1. Cấu hình `.env` trỏ sang database MySQL trống vừa tạo.
  2. Thực hiện sinh câu lệnh SQL kiểm tra: `python manage.py sqlmigrate core 0001` đến `0014`.
  3. Chú ý kiểm tra trường `JSONField` trên bảng `core_finalresult` để đảm bảo sinh đúng kiểu `json` của MySQL.
* **Nghiệm thu:** Toàn bộ cú pháp SQL kiểm tra đều hợp lệ với dialect MySQL.

---

### TUẦN 2: CHUYỂN ĐỔI CHÍNH THỨC SANG MYSQL VÀ BẢO TOÀN DỮ LIỆU (NGÀY 08 - 14)

#### Ngày 08: Chạy Migration chính thức lên MySQL
* **Công việc:**
  1. Thực thi: `python manage.py migrate`.
  2. Kiểm tra danh sách bảng được tạo trong MySQL:
     * Các bảng Django auth: `auth_user`, `auth_group`, ...
     * Các bảng nghiệp vụ: `core_student`, `core_teacher`, `core_course`, `core_englishclass`, `core_enrollment`, `core_tuitionfee`, `core_payment`, `core_certificate`, ...
* **Nghiệm thu:** Lệnh migrate kết thúc với mã 0 (OK trên toàn bộ 14 migrations). Không có bảng nào bị thiếu.

#### Ngày 09: Khởi tạo Dữ liệu Nền tảng & Phân quyền trên MySQL
* **Công việc:**
  1. Tạo tài khoản Superuser: `python manage.py createsuperuser`.
  2. Chạy lệnh tạo nhóm quyền chuẩn: `python manage.py setup_roles` để khởi tạo 3 nhóm `Admin`, `Hoc_Vu`, `Tai_Chinh`.
  3. Đăng nhập vào Django Admin (`/admin/`), gán tài khoản thử nghiệm vào từng nhóm tương ứng.
* **Nghiệm thu:** 3 nhóm tài khoản đăng nhập được vào web và được phân luồng về đúng trang Dashboard riêng.

#### Ngày 10: Xây dựng kịch bản chuyển dữ liệu (Data Migration Script)
* **Tình huống:** Chuyển dữ liệu từ cơ sở dữ liệu cũ (`db.sqlite3` hoặc Postgres) sang MySQL.
* **Công việc:**
  1. Xuất dữ liệu cũ ra file JSON định dạng UTF-8:
     ```bash
     python manage.py dumpdata core --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > datadump_core.json
     ```
  2. Kiểm tra tệp JSON để đảm bảo tiếng Việt không bị lỗi font hoặc hỏng ký tự.
* **Nghiệm thu:** Tệp `datadump_core.json` sẵn sàng và hợp lệ cú pháp JSON.

#### Ngày 11: Nạp dữ liệu vào MySQL và Giải quyết xung đột Khóa ngoại
* **Công việc:**
  1. Cấu hình `.env` trỏ vào MySQL.
  2. Nạp dữ liệu: `python manage.py loaddata datadump_core.json`.
  3. Nếu gặp lỗi khóa ngoại tuần hoàn: Viết script nạp dữ liệu theo thứ tự ưu tiên:
     * Cấp 1: Khóa học, Giáo viên, Học viên.
     * Cấp 2: Lớp học, Chính sách đánh giá (`AssessmentPolicy`).
     * Cấp 3: Ghi danh (`Enrollment`), Buổi học & Điểm danh.
     * Cấp 4: Đánh giá kết quả, Học phí & Thanh toán, Chứng chỉ.
* **Nghiệm thu:** Toàn bộ bản ghi học viên, lớp học và lịch sử học phí hiển thị đầy đủ trên MySQL.

#### Ngày 12: Kiểm thử tính toàn vẹn dữ liệu sau chuyển đổi (Data Integrity Audit)
* **Công việc:**
  1. So sánh đối chiếu số lượng bản ghi (Record count) giữa SQLite cũ và MySQL mới trên từng bảng.
  2. Kiểm tra ngẫu nhiên 10 học viên có tên tiếng Việt có dấu (ví dụ: `Nguyễn Hoàng Hải Đăng`) để đảm bảo không bị lỗi mã hóa `utf8mb4`.
  3. Kiểm tra trường `calculation_details` (JSONField) đọc ra đúng định dạng dict trong Python.
* **Nghiệm thu:** Khớp 100% số lượng bản ghi; không có ký tự lạ (`?`, ``).

#### Ngày 13: Kiểm tra toàn diện luồng nghiệp vụ trên MySQL (Smoke Test)
* **Công việc:** Thao tác thủ công toàn bộ các hành động chính trên nền MySQL:
  1. Thêm 1 học viên mới.
  2. Tạo 1 lớp học mới và gán giáo viên.
  3. Ghi danh học viên vào lớp.
  4. Tạo đơn chuyển lớp và duyệt đơn.
  5. Tạo khoản học phí và ghi nhận thanh toán tiền mặt.
* **Nghiệm thu:** Tất cả giao dịch đều ghi thành công vào MySQL, các trigger cập nhật sĩ số và trạng thái học phí chạy trơn tru.

#### Ngày 14: Thiết lập Chiến lược Sao lưu (Backup & Restore) cho MySQL
* **Công việc:**
  1. Tạo script tự động sao lưu `backup_mysql.bat` (dùng `mysqldump`).
  2. Thử nghiệm xóa thử 1 bảng giả lập và dùng file backup phục hồi thành công.
  3. Ghi tài liệu hướng dẫn backup/restore vào thư mục `docs/MYSQL_BACKUP_GUIDE.md`.
* **Nghiệm thu:** File backup `.sql` được tạo tự động với dung lượng đầy đủ và phục hồi được.

---

### TUẦN 3: CHUẨN HÓA NGHIỆP VỤ ĐIỂM, HOÀN THIỆN UI/UX VÀ TÀI CHÍNH (NGÀY 15 - 21)

#### Ngày 15: Lập kế hoạch Hợp nhất 2 hệ thống Điểm số
* **Vấn đề:** Đang tồn tại song song bảng `Grade` cũ và hệ thống `AssessmentScheme / AssessmentResult / FinalResult`.
* **Công việc:**
  1. Quyết định chuẩn hóa 100% sang hệ thống `AssessmentScheme` (linh hoạt chia tỷ trọng giữa Chuyên cần, Giữa kỳ, Cuối kỳ, Thuyết trình).
  2. Lập danh sách các lớp đang dùng bảng `Grade` cũ để chuyển đổi dữ liệu sang `AssessmentResult`.
* **Nghiệm thu:** Có văn bản/kế hoạch mapping chi tiết từ `Grade` cũ sang các thành phần điểm mới.

#### Ngày 16: Thực hiện Di chuyển dữ liệu Điểm cũ sang Điểm mới
* **Công việc:**
  1. Viết lệnh custom Django command: `python manage.py migrate_legacy_grades`.
  2. Tự động tạo `AssessmentScheme` chuẩn cho các khóa học cũ và chuyển đổi các cột Listening/Reading/Writing/Speaking thành các `AssessmentComponent`.
  3. Ẩn menu truy cập `/grades/` cũ, chuyển hướng toàn bộ sang `/academics/assessments/`.
* **Nghiệm thu:** Không còn tình trạng dữ liệu điểm bị lệch giữa 2 màn hình; học viên cũ đều có bảng điểm chi tiết mới.

#### Ngày 17: Nâng cấp Giao diện Bảng nhập điểm học viên
* **Vấn đề:** Giao diện nhập điểm hiện tại chưa có validation tức thời tại Client.
* **Công việc:**
  1. Chỉnh sửa template `core/academics/assessments/grade_entry.html`.
  2. Bổ sung Javascript kiểm tra: Chặn nhập số âm, chặn nhập điểm vượt quá điểm tối đa (`max_score`).
  3. Hiển thị cảnh báo màu vàng khi ô điểm thay đổi nhưng chưa bấm nút "Lưu bảng điểm".
* **Nghiệm thu:** Tránh hoàn toàn việc người dùng gõ nhầm điểm số không hợp lệ vào hệ thống.

#### Ngày 18: Tối ưu UI/UX cho Quy trình Chuyển lớp
* **Công việc:**
  1. Cải tiến trang `core/academics/class_transfers/review.html`.
  2. Bổ sung Modal xác nhận kèm ô nhập "Lý do từ chối" bắt buộc khi bấm nút **Từ chối đơn**.
  3. Thêm hiển thị trực quan sĩ số hiện tại và sĩ số tối đa của lớp chuyển đến (ví dụ: `24/25 học viên - Còn 1 chỗ`).
* **Nghiệm thu:** Cán bộ học vụ không bao giờ duyệt nhầm học viên vào lớp đã đầy sĩ số.

#### Ngày 19: Nâng cấp Dashboard Giám đốc & Học vụ với Biểu đồ
* **Vấn đề:** Dashboard hiện tại chỉ có các con số thống kê dạng thẻ tĩnh.
* **Công việc:**
  1. Tích hợp thư viện biểu đồ nhẹ (Chart.js qua CDN hoặc static local).
  2. Thêm biểu đồ cột: Doanh thu học phí theo từng tháng trong năm.
  3. Thêm biểu đồ tròn: Phân bổ số lượng học viên theo từng trình độ khóa học.
* **Nghiệm thu:** Dashboard trực quan, chuyên nghiệp, hiển thị đúng dữ liệu thực tế từ MySQL.

#### Ngày 20: Hoàn thiện Phân hệ Tài chính & Xuất Hóa đơn/Biên lai
* **Công việc:**
  1. Bổ sung giao diện xem chi tiết biên lai thu tiền: Mã phiếu thu, Ngày nộp, Tên phụ huynh/học viên, Số tiền, Hình thức nộp.
  2. Thêm định dạng in ấn (`@media print` trong CSS) cho phép bấm nút "In phiếu thu" xuất ra trang in chuẩn A5 để giao cho học viên.
* **Nghiệm thu:** In thử biên lai ra máy in hoặc lưu thành file PDF với định dạng gọn gàng, đẹp mắt.

#### Ngày 21: Bổ sung Cơ chế Bảo vệ Xóa dữ liệu (Soft Delete)
* **Vấn đề:** Xóa học viên hoặc lớp học bị `CASCADE` làm mất sạch lịch sử điểm số và học phí.
* **Công việc:**
  1. Thêm trường `is_active = models.BooleanField(default=True)` cho `Student`, `EnglishClass`.
  2. Thay vì dùng lệnh `.delete()`, chuyển các nút xóa trên giao diện thành "Ngừng hoạt động / Lưu trữ".
  3. Lọc mặc định `is_active=True` trên các danh sách thường nhật nhưng vẫn giữ toàn vẹn dữ liệu kế toán và chứng chỉ.
* **Nghiệm thu:** Thử "xóa" một học viên đã có lịch sử đóng tiền -> Báo cáo doanh thu không bị mất số liệu.

---

### TUẦN 4: KIỂM THỬ TỰ ĐỘNG, DOCKER HÓA, BẢO MẬT & BÀN GIAO (NGÀY 22 - 30)

#### Ngày 22: Viết Unit Test cho Service Tính điểm & Đánh giá [ĐÃ HOÀN THÀNH 100%]
* **Công việc:**
  1. Tạo thư mục `core/tests/` thay thế cho file `tests.py` rỗng.
  2. Viết file `test_assessment_service.py` kiểm thử các hàm trong [services/assessments.py](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/core/services/assessments.py):
     * Tính đúng điểm tổng kết theo trọng số (ví dụ: Chuyên cần 10% + Giữa kỳ 40% + Cuối kỳ 50%).
     * Đánh giá đúng trạng thái Đậu / Rớt (`PASSED` / `NOT_PASSED`) theo điểm chuẩn.
     * Xử lý trường hợp thiếu cột điểm bắt buộc sang `PENDING_RESULTS`.
* **Nghiệm thu:** Chạy `python manage.py test core.tests.test_assessment_service` đạt 100% PASS (3/3 tests).

#### Ngày 23: Viết Unit Test cho Service Chuyển lớp (State Machine) [ĐÃ HOÀN THÀNH 100%]
* **Công việc:**
  1. Viết file `test_class_transfer_service.py` kiểm thử [services/class_transfers.py](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/core/services/class_transfers.py):
     * Cùng khóa học: Tự động chuyển ngay (`COMPLETED`), cập nhật `TRANSFERRED` và `STUDYING`.
     * Khác khóa học: Tạo yêu cầu `PENDING`, Admin duyệt -> chuyển lớp an toàn.
     * Từ chối đơn (`REJECTED`): Giữ nguyên `Enrollment` cũ.
     * Chặn chuyển lớp nếu lớp đích đã đạt sĩ số tối đa `max_students`.
* **Nghiệm thu:** Toàn bộ 4/4 test cases logic chuyển lớp chạy tự động và đạt 100% PASS.

#### Ngày 24: Viết Integration Test cho Hệ thống Phân quyền (RBAC) [ĐÃ HOÀN THÀNH 100%]
* **Công việc:**
  1. Viết file `test_permissions.py` kiểm thử quyền truy cập:
     * User nhóm `Hoc_Vu` truy cập học vụ, bị chặn 403 khi vào học phí (`/tuitions/`).
     * User nhóm `Tai_Chinh` truy cập học phí, bị chặn 403 khi thao tác học vụ/lớp học.
     * Người dùng chưa đăng nhập luôn bị chuyển hướng về `/accounts/login/`.
     * Quản trị viên/Superuser toàn quyền truy cập.
* **Nghiệm thu:** 4/4 integration tests đạt 100% PASS. Tổng test suite đạt 11/11 tests pass.

#### Ngày 25: Gia cố Bảo mật Ứng dụng (Security Hardening) [ĐÃ HOÀN THÀNH 100%]
* **Công việc:**
  1. Cấu hình kiểm tra `SECRET_KEY`, `DEBUG=False`, `STATIC_ROOT`, `X_FRAME_OPTIONS='DENY'`, và HSTS khi triển khai.
  2. Cấu hình Cookie an toàn (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`).
  3. Tạo template [.env.example](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/.env.example) chuẩn hóa các tham số bảo mật.
  4. Rà soát và cập nhật [.gitignore](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/.gitignore) chặn triệt để rò rỉ `.env`, `db.sqlite3`, `*.sql`, `datadump*.json`, `.log`.
* **Nghiệm thu:** Chạy lệnh `python manage.py check --deploy` đạt 100% PASS (0 errors, 0 warnings).

#### Ngày 26: Đóng gói Ứng dụng với Docker & Docker Compose [ĐÃ HOÀN THÀNH 100%]
* **Mục tiêu:** Giúp hệ thống có thể chạy trên bất kỳ máy chủ nào chỉ với 1 câu lệnh, không lo xung đột môi trường Python/MySQL.
* **Công việc:**
  1. Tạo [Dockerfile](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/Dockerfile) (Python 3.12-slim, cài đặt thư viện hệ thống cho `mysqlclient`, chạy Gunicorn 3 workers).
  2. Tạo [.dockerignore](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/.dockerignore) loại bỏ file rác, virtual environment và file nhạy cảm.
  3. Viết [docker-compose.yml](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/docker-compose.yml) điều phối 2 dịch vụ liên kết chặt chẽ:
     * `db`: MySQL 8.0 image, charset `utf8mb4`, volume `mysql_data` và `healthcheck` tự động.
     * `web`: Django Web container, kết nối `db`, tự động chạy migrate, `collectstatic` và Gunicorn WSGI server.
* **Nghiệm thu:** File Dockerfile và docker-compose.yml cấu hình chuẩn production, sẵn sàng deploy container.

#### Ngày 27: Tối ưu hóa Truy vấn Cơ sở dữ liệu (Query Optimization) [ĐÃ HOÀN THÀNH 100%]
* **Công việc:**
  1. Rà soát và triệt tiêu vấn đề N+1 query trên Dashboard: bổ sung `.select_related("course", "teacher")` và lọc `is_active=True` cho `class_statistics` và `recent_students`.
  2. Bổ sung chỉ mục (`db_index=True`) cho 19 trường dữ liệu thường xuyên `filter()` và `order_by()` trên các Model chính:
     * `Student`: `full_name`, `phone`, `created_at`, `is_active`.
     * `Course`: `is_active`.
     * `Teacher`: `is_active`.
     * `EnglishClass`: `start_date`, `is_active`.
     * `Enrollment`: `status`, `enrolled_at`.
     * `ClassTransfer`: `status`, `requested_at`.
     * `AssessmentPolicy`: `status`.
     * `AssessmentEvent`: `assessment_date`.
     * `FinalResult`: `status`.
     * `Tuition`: `payment_date`, `created_at`.
     * `Certificate`: `issue_date`, `blockchain_status`.
  3. Tạo migration `0016_alter_assessmentevent_assessment_date_and_more.py` và áp dụng thành công lên MySQL.
* **Nghiệm thu:** Migration hoàn tất, 11/11 tests pass, tốc độ truy vấn trên MySQL được tối ưu hóa tối đa.

#### Ngày 28: Kiểm thử Toàn diện & Nghiệm thu Người dùng (End-to-End User Acceptance Test) [ĐÃ HOÀN THÀNH 100%]
* **Công việc:** Đóng vai từng vị trí để thực hiện toàn bộ nghiệp vụ từ A đến Z trên môi trường MySQL:
  1. *Lễ tân / Học vụ:* Tiếp nhận học viên mới -> Thu học phí -> Xếp lớp -> Chuyển lớp -> Nhập điểm theo quy chế -> Đánh giá Đậu/Rớt -> Cấp chứng chỉ.
  2. *Kế toán:* Xem công nợ -> Thu tiền từng đợt -> In biên lai A5 -> Xuất báo cáo thu chi Excel.
  3. *Học viên / Phụ huynh:* Tra cứu và xác thực mã chứng chỉ trên trang công khai Blockchain.
* **Nghiệm thu:** Nghiệm thu toàn diện: 11/11 automated tests PASS, hệ thống chạy mượt mà, không phát sinh ngoại lệ 500.

#### Ngày 29: Xây dựng Bộ Tài liệu Kỹ thuật & Vận hành Chuẩn Doanh nghiệp [ĐÃ HOÀN THÀNH 100%]
* **Công việc:** Viết bộ 3 tài liệu hướng dẫn hoàn chỉnh trong thư mục `docs/`:
  1. [SYSTEM_ARCHITECTURE.md](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/docs/SYSTEM_ARCHITECTURE.md): Sơ đồ kiến trúc 3 lớp, mô hình ERD chuẩn 3NF, ma trận RBAC, State Machine chuyển lớp & tích hợp Blockchain.
  2. [DEPLOYMENT_GUIDE.md](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/docs/DEPLOYMENT_GUIDE.md): Hướng dẫn triển khai Docker Compose (`docker compose up -d`), triển khai Native (Windows/Linux), sao lưu & phục hồi CSDL (`mysqldump`), và bảng kiểm tra bảo mật.
  3. [USER_MANUAL.md](file:///d:/DoAn4/APP-Trung-Tam-Tieng-Anh/docs/USER_MANUAL.md): Cẩm nang hướng dẫn thao tác chi tiết từng bước cho Học vụ, Kế toán và Quản trị viên.
* **Nghiệm thu:** Bộ 3 tài liệu kỹ thuật & vận hành hoàn chỉnh, chuẩn hóa tài liệu doanh nghiệp.

#### Ngày 30: Tổng kết Dự án & Đóng gói Bản phát hành (Release v1.0.0) [ĐÃ HOÀN THÀNH 100%]
* **Công việc:**
  1. Dọn dẹp code, định dạng code chuẩn, cấu hình bảo mật `check --deploy` đạt 0 lỗi, 0 cảnh báo.
  2. Đóng gói đầy đủ `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`, `requirements.txt`.
  3. Bàn giao sản phẩm hoàn chỉnh sẵn sàng đưa vào vận hành thực tế tại trung tâm.
* **Nghiệm thu:** Dự án đạt tiêu chuẩn phần mềm doanh nghiệp: Ổn định, bảo mật cao, chạy trên MySQL 8.0, 100% test pass và đầy đủ tài liệu hướng dẫn.

---

## BẢNG THEO DÕI TIẾN ĐỘ THỰC HIỆN

| Giai đoạn | Thời gian | Mục tiêu chính | Trạng thái |
| :--- | :---: | :--- | :---: |
| **Tuần 1** | Ngày 01 - 07 | Sửa lỗi P0/P1, phòng thủ Blockchain, tách handlers, cấu hình MySQL | **Hoàn thành (100%)** |
| **Tuần 2** | Ngày 08 - 14 | Di chuyển Schema & 100% Dữ liệu sang MySQL 8.0 an toàn | **Hoàn thành (100%)** |
| **Tuần 3** | Ngày 15 - 21 | UI/UX SaaS, Chart.js Dashboard, Excel & Biên lai A5, Soft Delete | **Hoàn thành (100%)** |
| **Tuần 4** | Ngày 22 - 30 | Viết Test tự động, Docker hóa, Đóng gói tài liệu v1.0.0 | **Hoàn thành (100%)** |

