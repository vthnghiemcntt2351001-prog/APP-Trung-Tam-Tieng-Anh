# KẾ HOẠCH VÀ LỘ TRÌNH NÂNG CẤP TOÀN DIỆN HỆ THỐNG
**Dự án:** Ứng dụng Quản trị Trung tâm Tiếng Anh (`APP-Trung-Tam-Tieng-Anh`)  
**Mục tiêu:** Khắc phục triệt để lỗ hổng an ninh, hoàn thiện nghiệp vụ vận hành thực tế, chuẩn hóa kiến trúc CSDL MySQL, tối ưu hiệu năng và nâng cấp giao diện đạt chuẩn phần mềm thương mại hiện đại.  
**Thời gian thực hiện dự kiến:** 30 ngày (5 Giai đoạn)  
**Tài liệu tham chiếu:** [BAO_CAO_DANH_GIA_VA_DE_XUAT_NANG_CAP_TOAN_DIEN.md](BAO_CAO_DANH_GIA_VA_DE_XUAT_NANG_CAP_TOAN_DIEN.md)

---

## I. NGUYÊN TẮC THI CÔNG & TIÊU CHUẨN KỸ THUẬT

1. **Bảo toàn dữ liệu tuyệt đối (Zero Data Loss):** Toàn bộ các thay đổi CSDL trên MySQL 8.0 phải được thực hiện qua Django Migrations. Trước mỗi đợt migration, phải sao lưu dữ liệu (`mysqldump`).
2. **Không đập đi xây lại:** Giữ vững kiến trúc Django Monolith đang hoạt động ổn định, phát triển theo phương thức module hóa (modular refactoring), kế thừa tối đa mã nguồn hiện có.
3. **Commit vi mô (Atomic Commits):** Mỗi nhiệm vụ kỹ thuật phải được kiểm thử tự động hoặc kiểm thử giao diện đạt tiêu chuẩn mới tạo git commit tương ứng.
4. **Bảo mật theo tiêu chuẩn (Security-First):** Triệt tiêu hoàn toàn mã backdoor/thử nghiệm, tuân thủ nguyên tắc đặc quyền tối thiểu (Least Privilege).

---

## II. LỘ TRÌNH 5 GIAI ĐOẠN CHI TIẾT

```text
┌────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 1 (Ngày 01 - 03): SỬA LỖI P0, BẢO MẬT & DỌN DẸP RUNTIME      │ [✅ HOÀN THÀNH 100%]
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 2 (Ngày 04 - 10): HOÀN THIỆN TOÀN VẸN CSDL & NGHIỆP VỤ      │ [✅ HOÀN THÀNH 100%]
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 3 (Ngày 11 - 17): PHÂN TRANG, TỐI ƯU HIỆU NĂNG & UX FORM     │ [✅ HOÀN THÀNH 100%]
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 4 (Ngày 18 - 24): CHUẨN HÓA DESIGN SYSTEM, RESPONSIVE & DARK │ [✅ HOÀN THÀNH 100%]
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 5 (Ngày 25 - 30): BUỔI HỌC, ĐIỂM DANH, KIỂM THỬ & DOCKER GOLIVE│ [✅ HOÀN THÀNH 100%]
└────────────────────────────────────────────────────────────────────────┘
```

---

### GIAI ĐOẠN 1: KHẮC PHỤC LỖI KHẨN CẤP (P0/P1), BẢO MẬT & DỌN DẸP RUNTIME
*Thời lượng: 3 ngày (Ngày 01 - Ngày 03)*  
*Mục tiêu: Đưa hệ thống về trạng thái an toàn tuyệt đối và triệt tiêu các lỗi gây sập trang 500.*

#### Ngày 01: Vá triệt để lỗ hổng xác thực bảo mật P0 tại `core/backends.py`
- **Vấn đề:** Phương thức `authenticate()` hiện tại đang dùng `user.set_password(password)` và tự động cấp quyền superuser, cho phép đăng nhập bất kỳ tài khoản admin nào với mật khẩu bất kỳ.
- **Công việc thực hiện:**
  1. Viết lại `EmailOrUsernameModelBackend` kế thừa chuẩn Django `ModelBackend`.
  2. Bắt buộc kiểm tra mật khẩu hợp lệ bằng `user.check_password(password)`. Trả về `None` nếu sai thông tin xác thực.
  3. Gỡ bỏ hoàn toàn logic tự động gán quyền Superuser hoặc tự tạo người dùng mới khi đăng nhập.
  4. Đặt lại mật khẩu an toàn cho các tài khoản quản trị (`admin`, `hocvu`, `taichinh`).
- **Nghiệm thu:** Thử đăng nhập sai mật khẩu -> Hệ thống chặn và báo lỗi; chỉ cho phép đăng nhập khi mật khẩu đúng 100%.

#### Ngày 02: Khắc phục lỗi Crash 500 khi tìm kiếm chứng chỉ & Rà soát ORM
- **Vấn đề:** Trang `/certificates/` bị sập 500 khi người dùng nhập từ khóa tìm kiếm do truy vấn trường `student__student_code` không tồn tại trong model `Student`.
- **Công việc thực hiện:**
  1. Sửa hàm `certificate_list` trong [core/handlers/certificates.py](core/handlers/certificates.py), thay thế bằng tìm kiếm theo tên học viên, email hoặc mã chứng chỉ:
     ```python
     Q(certificate_code__icontains=keyword) | Q(student__full_name__icontains=keyword) | Q(student__email__icontains=keyword)
     ```
  2. Rà soát toàn bộ các câu truy vấn `Q(...)` và `filter(...)` trong toàn bộ thư mục `core/handlers/` để đảm bảo 100% khớp đúng trường dữ liệu của model.
- **Nghiệm thu:** Tìm kiếm từ khóa bất kỳ trên trang `/certificates/` hoạt động mượt mà, phản hồi đúng kết quả mà không phát sinh ngoại lệ `FieldError`.

#### Ngày 03: Dọn dẹp tệp mồ côi, mã chết & Đồng bộ tài liệu cấu trúc
- **Vấn đề:** Tồn tại tệp template không sử dụng `core/templates/core/students/form.html`; tệp `PROJECT_STRUCTURE.md` nhắc đến `core/views.py` đã bị xóa.
- **Công việc thực hiện:**
  1. Xóa bỏ an toàn tệp `core/templates/core/students/form.html`.
  2. Cập nhật [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) phản ánh chính xác cấu trúc handler hiện thời, loại bỏ tham chiếu `views.py`.
  3. Thêm cấu hình hỗ trợ chuyển đổi linh hoạt giữa MySQL và SQLite trong [config/settings.py](config/settings.py) dựa trên biến môi trường `DB_ENGINE`.
- **Nghiệm thu:** Chạy `python manage.py check` không có cảnh báo; cây thư mục dự án sạch sẽ, đồng nhất với tài liệu.

---

### GIAI ĐOẠN 2: HOÀN THIỆN TÍNH TOÀN VẸN CSDL & NGHIỆP VỤ CỐT LÕI
*Thời lượng: 7 ngày (Ngày 04 - Ngày 10)*  
*Mục tiêu: Đảm bảo tính chính xác về dữ liệu tài chính kế toán và hoàn thiện các luồng nghiệp vụ còn thiếu.*

#### Ngày 04 - 05: Thiết kế bảng Lịch sử thanh toán học phí (`PaymentTransaction`)
- **Vấn đề:** Bảng `Tuition` hiện tại chỉ lưu tổng số tiền đã đóng, khi học viên đóng học phí nhiều đợt sẽ bị ghi đè, làm mất lịch sử các lần thu trước đó.
- **Công việc thực hiện:**
  1. Thêm model `PaymentTransaction` trong `core/models.py`:
     - `tuition` (ForeignKey đến `Tuition`, `on_delete=models.CASCADE`)
     - `receipt_code` (CharField, mã biên lai duy nhất, ví dụ `BL-202610-0001`)
     - `amount` (DecimalField, số tiền thu đợt này)
     - `payment_method` (CharField: Tiền mặt, Chuyển khoản, Thẻ)
     - `payment_date` (DateField)
     - `collected_by` (ForeignKey đến `User`, nhân viên thu ngân)
     - `note` (TextField)
  2. Tạo migration an toàn (`python manage.py makemigrations core`) và migrate vào MySQL.
  3. Cập nhật logic: Khi tạo giao dịch thu tiền mới, tự động cập nhật `paid_amount` trên bản ghi `Tuition` cha và tính toán lại công nợ còn lại.
- **Nghiệm thu:** Xem chi tiết học phí của học viên thấy rõ danh sách tất cả các đợt nộp tiền, ngày nộp, người thu và số tiền từng lần.

#### Ngày 06 - 07: Xây dựng giao diện và luồng Cấp chứng chỉ mới từ Web UI
- **Vấn đề:** Hiện tại nhân viên học vụ không thể cấp chứng chỉ mới trên giao diện web, phải vào Django Admin.
- **Công việc thực hiện:**
  1. Tạo handler `certificate_add` trong `core/handlers/certificates.py` và route `/certificates/add/`.
  2. Tạo template `core/templates/core/certificates/add.html`.
  3. Tích hợp logic thông minh: Khi chọn một lớp học, hệ thống tự động lọc và gợi ý các học viên đã có kết quả tổng kết Đạt (`FinalResult.status == 'passed'`) và chưa từng được cấp chứng chỉ cho lớp đó.
  4. Tự động sinh mã chứng chỉ chuẩn `CERT-XXXXXXXXXXXX` và tự tính xếp loại dựa trên điểm số tổng kết.
- **Nghiệm thu:** Nhân viên học vụ có thể cấp chứng chỉ mới trực tiếp từ giao diện web trong vòng chưa đầy 1 phút.

#### Ngày 08 - 10: Tích hợp Django Forms & Khắc phục lỗi mất dữ liệu khi submit lỗi
- **Vấn đề:** Hiện tại toàn bộ biểu mẫu đều đọc `request.POST.get()` thủ công, khi xảy ra lỗi nhập liệu (ví dụ sai ngày, sai số tiền), hệ thống redirect và làm mất sạch thông tin người dùng vừa nhập.
- **Công việc thực hiện:**
  1. Tạo tệp `core/forms.py`, xây dựng các form chuẩn:
     - `StudentForm`, `TeacherForm`, `CourseForm`, `EnglishClassForm`
     - `TuitionPaymentForm`, `CertificateIssueForm`
  2. Gắn widget định dạng ngày (`type="date"`), tiền tệ (`min=0`), số điện thoại và email.
  3. Cập nhật các view trong `core/handlers/`: Nếu `form.is_valid()` thất bại, render lại template kèm dữ liệu đã nhập và hiển thị thông báo lỗi cụ thể ngay dưới từng trường dữ liệu bị sai.
- **Nghiệm thu:** Thử nhập thiếu hoặc sai một trường trong form -> Trang hiển thị lỗi rõ ràng ngay cạnh trường đó, các thông tin đúng khác vẫn được giữ nguyên vẹn.

---

### GIAI ĐOẠN 3: TỐI ƯU HIỆU NĂNG, PHÂN TRANG & TRẢI NGHIỆM NGƯỜI DÙNG (UX)
*Thời lượng: 7 ngày (Ngày 11 - Ngày 17)*  
*Mục tiêu: Đảm bảo hệ thống vận hành siêu mượt, tải nhanh và trải nghiệm tương tác liền mạch.*

#### Ngày 11 - 13: Triển khai Phân trang chuẩn toàn diện (Pagination)
- **Vấn đề:** Toàn bộ danh sách đều load 100% bản ghi ra giao diện mà không phân trang.
- **Công việc thực hiện:**
  1. Xây dựng template partial dùng chung `core/templates/core/partials/pagination.html` (gồm nút Trước, Sau, nhảy đến số trang, hiển thị tổng số kết quả).
  2. Bổ sung `Paginator` trong Django vào tất cả các handler danh sách:
     - Danh sách Học viên (`student_list` - 15 học viên/trang)
     - Danh sách Phiếu học phí (`tuition_list` - 15 phiếu/trang)
     - Danh sách Khóa học & Lớp học (`course_list`, `class_list` - 12 lớp/trang)
     - Danh sách Giáo viên (`teacher_list` - 12 giảng viên/trang)
     - Danh sách Chứng chỉ (`certificate_list` - 15 chứng chỉ/trang)
     - Danh sách Bảng điểm (`grade_list` - 20 bài thi/trang)
  3. Giữ nguyên các tham số tìm kiếm và bộ lọc (`q=...`, `status=...`) khi bấm chuyển trang.
- **Nghiệm thu:** Toàn bộ các trang danh sách đều có thanh phân trang đồng bộ, tải trang nhanh dưới 100ms ngay cả khi có hàng nghìn bản ghi.

#### Ngày 14 - 15: Liên kết tương tác động giữa Học viên & Lớp học khi thu phí
- **Vấn đề:** Form thêm phiếu học phí yêu cầu chọn học viên và lớp học riêng biệt, dễ chọn nhầm học viên chưa vào lớp.
- **Công việc thực hiện:**
  1. Bổ sung một endpoint nội bộ (JSON API): `/api/students/<student_id>/classes/` trả về các lớp học mà học viên đó đang theo học.
  2. Bổ sung JavaScript tại [core/static/core/js/tuition_add.js](core/static/core/js/tuition_add.js): Khi người dùng chọn Học viên, dropdown Lớp học tự động cập nhật chỉ hiển thị các lớp học viên đó đã ghi danh, tự động điền học phí và số tiền còn nợ.
- **Nghiệm thu:** Nhân viên tài chính chọn học viên -> dropdown lớp học tự động hiển thị chính xác lớp học viên đang học, loại bỏ hoàn toàn khả năng lập sai phiếu học phí.

#### Ngày 16 - 17: Thống nhất và liên thông 2 hệ thống điểm số
- **Vấn đề:** Dự án đang tồn tại song song model `Grade` (4 kỹ năng cứng) và hệ thống `AssessmentPolicy` (quy chế điểm động) nhưng hai bên không liên thông.
- **Công việc thực hiện:**
  1. Xây dựng quy chế mẫu chuẩn 4 kỹ năng (Nghe, Nói, Đọc, Viết - mỗi kỹ năng 25%) bằng `AssessmentPolicy`.
  2. Cho phép tự động chuyển đổi điểm từ các bản ghi `Grade` cũ sang `AssessmentResult` của đợt thi tương ứng.
  3. Bổ sung liên kết trên giao diện Sổ điểm: Xem trực tiếp bảng tổng hợp điểm 4 kỹ năng và điểm trung bình tích lũy của từng học viên trong lớp.
- **Nghiệm thu:** Dữ liệu điểm tập trung nhất quán về một mối, kết quả tổng kết tự động làm căn cứ cho việc cấp chứng chỉ.

---

### GIAI ĐOẠN 4: CHUẨN HÓA DESIGN SYSTEM, RESPONSIVE & DARK MODE
*Thời lượng: 7 ngày (Ngày 18 - Ngày 24)*  
*Mục tiêu: Đưa giao diện đạt chuẩn thẩm mỹ cao cấp (WOW user), nhất quán trên mọi kích thước thiết bị.*

#### Ngày 18 - 19: Chuẩn hóa Design System & Đồng bộ Breakpoint Responsive
- **Vấn đề:** 12 tệp CSS trang có 12 mốc media query tùy tiện gây lệch bố cục trên Tablet (iPad 768px).
- **Công việc thực hiện:**
  1. Định nghĩa chuẩn 4 breakpoint cố định trong [core/static/core/css/base.css](core/static/core/css/base.css):
     - `--bp-mobile: 640px` (Điện thoại)
     - `--bp-tablet: 768px` (Máy tính bảng dọc)
     - `--bp-laptop: 1024px` (Máy tính bảng ngang / Laptop nhỏ)
     - `--bp-desktop: 1280px` (Màn hình Desktop)
  2. Đồng bộ hóa toàn bộ các media query trong các file `pages/**/*.css` theo 4 mốc trên.
  3. Bổ sung thanh cuộn ngang `table-responsive` chống tràn cho toàn bộ các bảng dữ liệu trên thiết bị di động.
- **Nghiệm thu:** Kiểm thử mượt mà trên iPhone, iPad Air/Mini (768px - 834px) và Laptop/PC; không còn hiện tượng vỡ layout hay tràn ngang trang.

#### Ngày 20 - 22: Triển khai Chế độ Giao diện Tối (Dark Mode) toàn diện
- **Công việc thực hiện:**
  1. Mở rộng biến CSS Theme trong `base.css`:
     - Chế độ sáng: `--canvas: #f8fafc`, `--surface: #ffffff`, `--ink: #0f172a`, `--line: #e2e8f0`
     - Chế độ tối (`[data-theme="dark"]`): `--canvas: #0f172a`, `--surface: #1e293b`, `--ink: #f8fafc`, `--line: #334155`
  2. Bổ sung nút chuyển đổi Theme Toggle (Mặt trời ☀️ / Mặt trăng 🌙) trên thanh Topbar của giao diện.
  3. Tự động lưu lựa chọn của người dùng vào `localStorage` và tự động phát hiện tùy chọn hệ thống qua `@media (prefers-color-scheme: dark)`.
  4. Rà soát và áp dụng Dark Mode cho toàn bộ các thành phần: Table, Modal, Card, Dropdown, Form Input, Toast messages.
- **Nghiệm thu:** Chuyển đổi qua lại giữa Light Mode và Dark Mode mượt mà không chớp nháy (zero FOUC); độ tương phản màu sắc đạt chuẩn WCAG AA.

#### Ngày 23 - 24: Loại bỏ CSS Inline, Thẻ `!important` & Hoàn thiện Micro-animations
- **Công việc thực hiện:**
  1. Rà soát toàn bộ thư mục `core/templates/`, chuyển tất cả các thẻ `<style>` nội tuyến vào đúng tệp CSS của trang.
  2. Loại bỏ các khai báo `!important` không cần thiết bằng cách chuẩn hóa CSS Selector Specificity.
  3. Thêm các hiệu ứng vi mô (micro-interactions):
     - Hiệu ứng hover nổi nhẹ trên các thẻ thống kê Dashboard (`transform: translateY(-2px)` kèm shadow mềm).
     - Skeleton loader nhẹ khi tải dữ liệu bảng.
     - Hiệu ứng chuyển cảnh mượt mà (`transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1)`).
- **Nghiệm thu:** Giao diện đem lại trải nghiệm sang trọng, chuyên nghiệp, mã CSS đóng gói sạch sẽ.

---

### GIAI ĐOẠN 5: BUỔI HỌC, ĐIỂM DANH, KIỂM THỬ TỰ ĐỘNG & ĐÓNG GÓI PRODUCTION
*Thời lượng: 6 ngày (Ngày 25 - Ngày 30)*  
*Mục tiêu: Bổ sung phân hệ vận hành thực tế cuối cùng, nâng cao độ phủ test và sẵn sàng vận hành thương mại.*

#### Ngày 25 - 26: Xây dựng Phân hệ Buổi học (`ClassSession`) & Điểm danh (`Attendance`)
- **Vấn đề:** Hiện tại trung tâm chưa có công cụ ghi nhận học viên nghỉ học, đi muộn hoặc học bù.
- **Công việc thực hiện:**
  1. Thêm model `ClassSession` (Lớp, Buổi số mấy, Ngày học, Phòng học, Giáo viên đứng lớp, Nội dung bài giảng).
  2. Thêm model `Attendance` (Buổi học, Học viên, Trạng thái: Có mặt / Vắng có phép / Vắng không phép / Đi muộn, Ghi chú).
  3. Xây dựng giao diện Điểm danh nhanh cho giáo viên/học vụ (dạng danh sách tích chọn trực quan trên từng buổi học).
  4. Tự động thống kê tỷ lệ chuyên cần của học viên trong toàn khóa học.
- **Nghiệm thu:** Giáo viên mở điện thoại hoặc máy tính điểm danh lớp học chỉ với 30 giây; hệ thống tự động cảnh báo học viên vắng quá số buổi quy định.

#### Ngày 27 - 28: Tách tác vụ Blockchain bất đồng bộ & Mở rộng Kiểm thử (Test Suite)
- **Công việc thực hiện:**
  1. Bọc việc phát hành chứng chỉ lên Blockchain trong cơ chế xử lý phòng thủ an toàn: ghi nhận trạng thái `PENDING_BLOCKCHAIN` trước, tránh nghẽn luồng HTTP chính khi node Ganache phản hồi chậm.
  2. Mở rộng bộ kiểm thử trong `core/tests/`:
     - Viết test kiểm tra xác thực mật khẩu an toàn.
     - Viết test cho luồng giao dịch thanh toán học phí từng đợt.
     - Viết test cho chức năng cấp và xác minh chứng chỉ.
     - Viết test cho phân trang và bộ lọc.
  3. Đạt mục tiêu độ phủ kiểm thử (Test Coverage) > 85%.
- **Nghiệm thu:** Chạy `python manage.py test` vượt qua 100% test case (dự kiến > 25 tests pass), thời gian chạy dưới 15 giây.

#### Ngày 29 - 30: Đóng gói Docker Production, Hardening An ninh & Bàn giao
- **Công việc thực hiện:**
  1. Hoàn thiện tệp `Dockerfile` và `docker-compose.yml` chạy 3 service: `web` (Django + Gunicorn), `db` (MySQL 8.0) và `node` (Ganache Blockchain).
  2. Thiết lập cấu hình bảo vệ môi trường Production trong `settings.py`:
     - Cưỡng bức tạo khóa bí mật `DJANGO_SECRET_KEY` mạnh qua biến môi trường.
     - Bật các cờ an ninh: `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `X_FRAME_OPTIONS = 'DENY'`.
  3. Biên soạn tài liệu Hướng dẫn triển khai và Vận hành hệ thống (`DEPLOYMENT_GUIDE.md`).
- **Nghiệm thu:** Chạy `docker compose up -d` là toàn bộ hệ thống khởi chạy hoàn hảo, tự động migrate database và sẵn sàng tiếp nhận người dùng thật.

---

## III. MA TRẬN PHÂN LOẠI ƯU TIÊN THEO NGUYÊN TẮC MOSCOW

| Mức độ | Các hạng mục công việc | Thời hạn hoàn thành |
|---|---|:---:|
| **MUST HAVE** *(Bắt buộc phải làm ngay)* | • Vá lỗi xác thực bảo mật P0 tại `core/backends.py`<br>• Sửa lỗi sập 500 khi tìm kiếm chứng chỉ<br>• Bổ sung bảng Lịch sử nộp tiền `PaymentTransaction`<br>• Thêm giao diện Web Cấp chứng chỉ mới<br>• Tích hợp phân trang toàn diện (Pagination) | **Tuần 1 & 2** |
| **SHOULD HAVE** *(Nên có để hệ thống hoàn thiện)* | • Chuyển đổi biểu mẫu sang Django Forms giữ dữ liệu<br>• Lọc tương tác động AJAX Học viên - Lớp học<br>• Chuẩn hóa Responsive Breakpoints trên iPad/Tablet<br>• Phân hệ Buổi học & Điểm danh chuyên cần (`Attendance`) | **Tuần 3 & 4** |
| **COULD HAVE** *(Làm tăng tính cao cấp của phần mềm)* | • Hỗ trợ giao diện nền tối (Dark Mode)<br>• Tách hàng đợi tác vụ ngầm cho Blockchain<br>• Xuất báo cáo điểm danh ra Excel | **Tuần 4** |
| **WON'T HAVE** *(Chưa cần thiết ở giai đoạn này)* | • Chuyển đổi sang Microservices (tiếp tục giữ Monolith)<br>• Tích hợp Trí tuệ nhân tạo (AI chatbot)<br>• Tách ứng dụng Mobile App riêng (Web Responsive đã đáp ứng đủ) | *Xem xét sau Golive* |

---

## IV. BẢNG TIÊU CHÍ NGHIỆM THU TỔNG THỂ (DOD - DEFINITION OF DONE)

Một tính năng chỉ được xem là hoàn thành khi đáp ứng trọn vẹn 5 tiêu chí:
1. **Chức năng:** Hoạt động đúng yêu cầu nghiệp vụ, không sinh lỗi runtime console hoặc 500.
2. **Giao diện:** Đẹp mắt, tương thích hoàn hảo trên Mobile, Tablet (768px) và Desktop; hỗ trợ cả Light Mode và Dark Mode.
3. **Dữ liệu:** Lưu trữ chính xác vào MySQL 8.0, tuân thủ ràng buộc khóa ngoại và bảo toàn dữ liệu.
4. **Bảo mật:** Đã được kiểm tra quyền truy cập theo vai trò (RBAC) và bảo vệ CSRF.
5. **Kiểm thử:** Có ít nhất một test case tự động kiểm tra luồng chạy chính và vượt qua `python manage.py test`.

---
*Kế hoạch này được xây dựng dựa trên khảo sát thực tế toàn diện mã nguồn dự án. Sau khi hoàn thành 5 giai đoạn, hệ thống sẽ đạt mức sẵn sàng vận hành thực tế 98/100 điểm, đáp ứng đầy đủ tiêu chuẩn của một phần mềm quản lý giáo dục chuyên nghiệp.*
