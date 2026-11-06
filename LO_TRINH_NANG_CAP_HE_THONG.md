# KẾ HOẠCH VÀ LỘ TRÌNH NÂNG CẤP TOÀN DIỆN HỆ THỐNG (CẬP NHẬT 2026)
**Dự án:** Ứng dụng Quản trị Trung tâm Tiếng Anh (`APP-Trung-Tam-Tieng-Anh`)  
**Phiên bản tài liệu:** v2.0 (Cập nhật sau đợt kiểm tra, rà soát logic & UI/UX toàn diện)  
**Mục tiêu:** Khắc phục triệt để các lỗi sai lệch dữ liệu tài chính, hoàn thiện tính liên kết - đồng bộ giữa các phân hệ, loại bỏ hoàn toàn lỗi hiển thị Dark Mode và nâng cấp trải nghiệm người dùng đạt chuẩn phần mềm thương mại thực tế.  
**Thời gian thực hiện dự kiến:** 18 ngày làm việc (4 Giai đoạn trọng tâm)  
**Tài liệu tham chiếu:** Báo cáo kiểm tra và đánh giá toàn diện logic & tính đồng bộ hệ thống.

---

## I. TỔNG KẾT HIỆN TRẠNG HỆ THỐNG SAU AUDIT TOÀN DIỆN

### 1. Các hạng mục kỹ thuật đã hoàn thành tốt (Kế thừa & Duy trì)
- [x] **Bảo mật xác thực:** Đã vá lỗ hổng P0 tại `core/backends.py`, mật khẩu kiểm tra an toàn qua `user.check_password()`.
- [x] **Cơ sở dữ liệu & Migrations:** 18 migration áp dụng thành công trên MySQL 8.0 / SQLite; cấu trúc bảng quan hệ chặt chẽ.
- [x] **Lịch sử thanh toán:** Bảng `PaymentTransaction` lưu vết từng đợt nộp tiền, hình thức thanh toán và sinh mã phiếu thu tự động.
- [x] **Phòng thủ mạng Blockchain:** Đóng gói hàm `is_blockchain_available()`, hệ thống tự phát hiện trạng thái offline của node Ganache mà không gây crash trang.
- [x] **Phân hệ Buổi học & Điểm danh:** Model `ClassSession`, `Attendance` và giao diện điểm danh nhanh hoạt động tốt.
- [x] **Bộ kiểm thử tự động cơ sở:** Đã có 28 test cases chạy thành công (`Ran 28 tests in 28.7s - OK`).

### 2. Các điểm nghẽn & Sai lệch phát hiện cần khắc phục ngay
1. **Lỗi sai lệch doanh thu Dashboard (Critical):** Biểu đồ 6 tháng truy vấn tổng `Tuition.paid_amount` theo `Tuition.payment_date`, dẫn đến việc dồn toàn bộ tiền đóng lũy kế vào tháng gần nhất, sai lệch hoàn toàn so với thực tế các lần nộp trong `PaymentTransaction`.
2. **Xung đột sửa học phí (High):** Hàm `tuition_edit` cho phép sửa tay `paid_amount`, phá vỡ liên kết với bảng `PaymentTransaction` và sẽ bị ghi đè khi phát sinh giao dịch mới.
3. **Lỗ hổng cấp chứng chỉ không ràng buộc (High):** `certificate_add` cho phép cấp chứng chỉ cho học viên còn nợ học phí, vắng quá số buổi hoặc điểm liệt; tự động gán điểm 8.0 nếu học viên chưa từng thi.
4. **Lỗi phân quyền gây 403 Forbidden (High):** Nút "Duyệt chuyển lớp" tại `classes/list.html` hiển thị cho Học vụ (`can_manage_academics`), nhưng view xử lý lại chặn bằng `@admin_required`.
5. **Vỡ giao diện Dark Mode nghiêm trọng (High):** Thanh phân trang dùng chung (`pagination.html`), form cấp chứng chỉ (`certificates/add.html`), form khóa học và biên lai hardcode màu nền trắng `#ffffff`, tạo mảng chói lóa trên nền tối.
6. **Mất liên thông Đào tạo ↔ Tài chính (Medium):** Ghi danh học viên vào lớp không tự động tạo phiếu học phí; chuyển lớp thành công thì tiền học ở lớp cũ bị kẹt lại, không được kết chuyển sang lớp mới.
7. **Biểu mẫu chưa chuẩn hóa Django Forms (Medium):** Các view Thêm/Sửa Khóa học, Lớp học, Giáo viên vẫn đọc `request.POST` thô, mất trắng dữ liệu khi nhập sai.
8. **Hệ thống Icon & Breakpoints phân mảnh (Medium):** Trộn lẫn 3 kiểu icon (RemixIcon, inline SVG, Emoji); media queries dùng tùy tiện từ 480px đến 1200px.

---

## II. LỘ TRÌNH 4 GIAI ĐOẠN CHI TIẾT

```text
┌────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 1 (Ngày 01 - 03): SỬA LỖI DOANH THU, HỌC PHÍ & LỖI 403 RBAC   │ [⏳ ĐANG TRIỂN KHAI]
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 2 (Ngày 04 - 08): ĐỒNG BỘ ĐÀO TẠO - TÀI CHÍNH & CHỨNG CHỈ     │ [📋 CHỜ THI CÔNG]
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 3 (Ngày 09 - 14): CHUẨN HÓA DESIGN SYSTEM, DARK MODE & FORMS  │ [📋 CHỜ THI CÔNG]
├────────────────────────────────────────────────────────────────────────┤
│ GIAI ĐOẠN 4 (Ngày 15 - 18): TỐI ƯU UX, BÁO CÁO EXCEL & TEST SUITE > 85% │ [📋 CHỜ THI CÔNG]
└────────────────────────────────────────────────────────────────────────┘
```

---

### GIAI ĐOẠN 1: KHẮC PHỤC LỖI NGHIỆP VỤ CẤP BÁCH & BẢO MẬT (P0/P1)
*Thời lượng: 3 ngày (Ngày 01 - Ngày 03)*  
*Mục tiêu: Đảm bảo số liệu tài chính trên Dashboard chính xác 100%, khóa lỗ hổng ghi đè dữ liệu và triệt tiêu lỗi 403 Forbidden.*

#### Nhiệm vụ 1.1: Sửa logic thống kê doanh thu thực thu trên Dashboard
- **Tệp xử lý:** `core/handlers/dashboard.py`
- **Nội dung kỹ thuật:**
  1. Thay thế câu truy vấn doanh thu theo tháng: Thay vì nhóm trên model `Tuition` (vốn chỉ chứa số tiền lũy kế và ngày đóng gần nhất), chuyển sang truy vấn trực tiếp bảng `PaymentTransaction`:
     ```python
     paid_sum = PaymentTransaction.objects.filter(
         payment_date__year=y,
         payment_date__month=m,
     ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
     ```
  2. Tính toán doanh thu dự kiến (`monthly_expected`) dựa trên học phí các lớp mở trong tháng hoặc công nợ phải thu.
- **Tiêu chí nghiệm thu:** Học viên nộp tiền đợt 1 vào tháng 1, nộp đợt 2 vào tháng 3 -> Doanh thu tháng 1 và tháng 3 hiển thị chính xác từng khoản nộp tương ứng trên biểu đồ.

#### Nhiệm vụ 1.2: Chuẩn hóa luồng Sửa Học phí & Bảo vệ Lịch sử Thu ngân
- **Tệp xử lý:** `core/handlers/tuition.py`, `core/templates/core/finance/tuition/edit.html`
- **Nội dung kỹ thuật:**
  1. Trong `tuition_edit`: Khóa trường `paid_amount` thành dạng chỉ đọc (Readonly), không cho phép nhân viên gõ tay sửa số tiền đã nộp.
  2. Bổ sung bảng danh sách các đợt nộp tiền (`tuition.transactions.all()`) ngay trên giao diện sửa phiếu học phí.
  3. Thêm nút liên kết trực tiếp "Thu học phí bổ sung" (`tuition_payment_add`) để mọi phát sinh tiền đều được ghi nhận qua `PaymentTransaction`.
- **Tiêu chí nghiệm thu:** Không còn hiện tượng lệch số dư giữa `Tuition.paid_amount` và `Sum(transactions.amount)`; lịch sử giao dịch được bảo toàn vẹn toàn.

#### Nhiệm vụ 1.3: Sửa lỗi phân quyền nút "Duyệt chuyển lớp" tránh HTTP 403
- **Tệp xử lý:** `core/templates/core/academics/classes/list.html`, `core/handlers/class_transfers.py`
- **Nội dung kỹ thuật:**
  1. Tại `classes/list.html`: Điều chỉnh điều kiện hiển thị nút "Duyệt chuyển lớp" sang `{% if is_admin %}` thay vì `can_manage_academics`.
  2. Tại `core/handlers/class_transfers.py`: Cập nhật `class_transfer_list` cho phép cán bộ Học vụ truy cập để theo dõi trạng thái yêu cầu (`@academic_required`), nhưng giữ nguyên `@admin_required` cho hai hành động `class_transfer_approve` và `class_transfer_reject`.
- **Tiêu chí nghiệm thu:** Cán bộ Học vụ không bị ấn nhầm vào nút gây lỗi 403; Admin truy cập và duyệt chuyển lớp bình thường.

---

### GIAI ĐOẠN 2: HOÀN THIỆN LIÊN KẾT LIÊN PHÂN HỆ & ĐỒNG BỘ DỮ LIỆU
*Thời lượng: 5 ngày (Ngày 04 - Ngày 08)*  
*Mục tiêu: Đảm bảo dữ liệu luân chuyển tự động, thông suốt giữa Đào tạo, Điểm số, Tài chính và Chứng chỉ.*

#### Nhiệm vụ 2.1: Tự động hóa liên kết Đào tạo ↔ Tài chính khi Xếp lớp
- **Tệp xử lý:** `core/handlers/academics.py` (hàm `class_detail`)
- **Nội dung kỹ thuật:**
  1. Khi nhân viên học vụ đăng ký học viên vào lớp thành công (`Enrollment.objects.create`), tự động kích hoạt tạo bản ghi `Tuition` tương ứng:
     ```python
     Tuition.objects.get_or_create(
         student=student,
         english_class=english_class,
         defaults={
             "total_fee": english_class.course.tuition,
             "paid_amount": Decimal("0"),
             "note": f"Học phí tự động khởi tạo khi ghi danh lớp {english_class.name}",
         }
     )
     ```
- **Tiêu chí nghiệm thu:** Thêm học viên vào lớp -> Kiểm tra danh sách học phí tại `/tuitions/` lập tức thấy bản ghi học phí kèm số tiền phải thu, không bị sót công nợ.

#### Nhiệm vụ 2.2: Thiết lập Cổng kiểm duyệt điều kiện Cấp chứng chỉ & Quy trình Phê duyệt 2 bước (Enterprise Workflow)
- **Tệp xử lý:** `core/handlers/certificates.py` (`certificate_add`, `certificate_issue`), `core/templates/core/certificates/add.html`, `core/templates/core/certificates/list.html`
- **Nội dung kỹ thuật:**
  1. **Quy trình 2 bước chuẩn doanh nghiệp (Option 2):**
     - **Bước 1 (Học vụ):** Chỉ có quyền lập đề xuất chứng chỉ (`blockchain_status="pending"`), không có quyền tự ý ký số Blockchain. Giao diện hiển thị banner quy trình 2 bước, ẩn nút bấm/toggle ký Blockchain.
     - **Bước 2 (Admin):** Xem danh sách đề xuất, thẩm định điều kiện và bấm nút "Duyệt & Ký số" để trực tiếp đóng dấu băm SHA-256 lên Smart Contract Ganache/Ethereum.
  2. **Cổng kiểm duyệt điều kiện (Gatekeeper):**
     - **Điều kiện tài chính:** Chặn cấp nếu `tuition.paid_amount < tuition.total_fee` (còn nợ học phí). Hiển thị số tiền nợ cụ thể.
     - **Điều kiện học lực:** Điểm tổng kết phải đạt tối thiểu `score >= 5.0` (tránh cấp chứng chỉ cho học viên có kết quả chưa đạt).
     - Đánh dấu cảnh báo ngay trên danh sách chọn học viên `[⚠️ Nợ học phí]` và `[⚠️ Chưa đạt điểm sàn]`.
- **Tiêu chí nghiệm thu:** [ĐÃ HOÀN THÀNH 100%] Không thể lập đề xuất/cấp cho học viên nợ phí hoặc điểm < 5.0; Học vụ không thể can thiệp ký số Blockchain; Admin toàn quyền duyệt ký số; toàn bộ 8 bài kiểm tra nghiệp vụ và 28 test cases hệ thống đều PASS.

#### Nhiệm vụ 2.3: Xây dựng cơ chế luân chuyển học phí khi Học viên Chuyển lớp
- **Tệp xử lý:** `core/services/class_transfers.py` (`request_class_transfer`, `approve_class_transfer`)
- **Nội dung kỹ thuật:**
  1. Khi phê duyệt chuyển lớp: Tự động tìm bản ghi `Tuition` ở lớp cũ.
  2. Kết chuyển toàn bộ số tiền đã đóng (`paid_amount`) và các giao dịch `PaymentTransaction` hoặc tạo bản ghi ghi nhận số tiền chuyển giao sang phiếu học phí của lớp mới.
  3. Nếu chuyển sang lớp có học phí khác nhau, tự động tính khoản tiền chênh lệch (phải thu thêm hoặc bảo lưu hoàn trả).
- **Tiêu chí nghiệm thu:** Học viên chuyển lớp không bị đòi học phí hai lần; công nợ ở lớp mới phản ánh chính xác số tiền đã đóng từ lớp cũ.

#### Nhiệm vụ 2.4: Đồng bộ Điểm số hai chiều & Tích hợp Dashboard toàn diện
- **Tệp xử lý:** `core/services/grading.py`, `core/handlers/dashboard.py`
- **Nội dung kỹ thuật:**
  1. Khi giảng viên nhập điểm qua Sổ điểm quy chế (`assessment_event_gradebook`), tự động cập nhật ngược lại điểm kỹ năng tương ứng trong model `Grade` (nếu có).
  2. Nâng cấp truy vấn thống kê điểm trên Dashboard: Đọc dữ liệu điểm từ cả hai nguồn `FinalResult` và `Grade`, tránh việc chấm điểm qua quy chế mới nhưng Dashboard báo điểm trung bình bằng 0.
- **Tiêu chí nghiệm thu:** Chấm điểm trên bất kỳ phân hệ nào thì bảng điểm và biểu đồ thống kê Dashboard đều đồng bộ số liệu.

#### Nhiệm vụ 2.5: Chuyển đổi Biểu mẫu sang Django Forms & Dọn dẹp Mã chết
- **Tệp xử lý:** `core/handlers/academics.py`, `core/handlers/students.py`
- **Nội dung kỹ thuật:**
  1. Áp dụng `CourseForm`, `TeacherForm`, `EnglishClassForm` đã có trong `core/forms.py` vào các hàm `course_add`, `course_edit`, `teacher_add`, `teacher_edit`, `class_add`, `class_edit`.
  2. Khi người dùng nhập sai, giữ nguyên toàn bộ dữ liệu đã điền và tô đỏ trường bị lỗi kèm thông báo cụ thể.
  3. Xóa đoạn mã render chết sau lệnh `return` tại `students.py` (dòng 109 - 114).
- **Tiêu chí nghiệm thu:** Nhập sai định dạng email hoặc học phí âm -> Form báo lỗi ngay dưới ô nhập, các thông tin khác không bị xóa trắng.

---

### GIAI ĐOẠN 3: NÂNG CẤP UI/UX, CHUẨN HÓA DESIGN SYSTEM & DARK MODE
*Thời lượng: 6 ngày (Ngày 09 - Ngày 14)*  
*Mục tiêu: Đưa toàn bộ giao diện đạt độ nhất quán thương mại cao cấp, hỗ trợ Dark Mode hoàn hảo.*

#### Nhiệm vụ 3.1: Khắc phục triệt để lỗi Dark Mode trên các trang Form và Phân trang
- **Tệp xử lý:**
  - `core/templates/core/partials/pagination.html`
  - `core/templates/core/certificates/add.html`
  - `core/templates/core/academics/courses/list.html`
  - `core/templates/core/academics/attendance/session_list.html`
  - `core/templates/core/finance/tuition/receipt.html`
- **Nội dung kỹ thuật:**
  1. Thay thế 100% các mã màu cố định (`#ffffff`, `#0f172a`, `#e2e8f0`, `#64748b`) bằng biến Design Tokens: `var(--surface)`, `var(--ink)`, `var(--line)`, `var(--canvas)`.
  2. Bổ sung khối CSS `[data-theme="dark"]` cho thanh phân trang:
     ```css
     [data-theme="dark"] .saas-pagination-nav {
         background: var(--surface-card);
         border-color: var(--line);
     }
     [data-theme="dark"] .page-link {
         background: var(--surface);
         border-color: var(--line);
         color: var(--ink);
     }
     ```
- **Tiêu chí nghiệm thu:** Bật Dark Mode, toàn bộ trang và thanh phân trang chuyển màu tối dịu mắt, độ tương phản văn bản đạt chuẩn WCAG AA, không còn mảng trắng chói.

#### Nhiệm vụ 3.2: Dọn dẹp thẻ `<style>` nội tuyến & Chuẩn hóa CSS Files
- **Tệp xử lý:** Toàn bộ thư mục `core/templates/core/`
- **Nội dung kỹ thuật:**
  1. Di chuyển mã CSS từ thẻ `<style>` trong `certificates/add.html` sang `core/static/core/css/pages/certificates/add.css`.
  2. Di chuyển CSS của `pagination.html` vào `core/static/core/css/base.css`.
  3. Loại bỏ hoàn toàn các khai báo `!important` không cần thiết tại `teachers/add.html` và các trang liên quan.
- **Tiêu chí nghiệm thu:** Thư mục template sạch sẽ, tách biệt hoàn toàn cấu trúc HTML và mã định dạng CSS.

#### Nhiệm vụ 3.3: Thống nhất Hệ thống Biểu tượng (Iconography) về RemixIcon
- **Tệp xử lý:** Các template phân hệ Điểm danh (`attendance`), Phân quyền (`system/roles`), và Chứng chỉ (`certificates`)
- **Nội dung kỹ thuật:**
  1. Thay thế các biểu tượng cảm xúc Emoji (`📊`, `➕`, `🛡️`, `🎓`, `💳`, `👤`) bằng thẻ RemixIcon đồng bộ (`ri-bar-chart-2-line`, `ri-add-line`, `ri-shield-check-line`, `ri-graduation-cap-line`, `ri-bank-card-line`, `ri-user-line`).
  2. Chuẩn hóa kích thước icon: 16px cho nút bấm, 18px cho menu, 24px cho thẻ thống kê.
- **Tiêu chí nghiệm thu:** Giao diện có nhận diện đồng bộ, sắc nét, mang phong thái phần mềm doanh nghiệp (Enterprise SaaS).

#### Nhiệm vụ 3.4: Đồng bộ Breakpoint Responsive & Ngữ nghĩa HTML5
- **Tệp xử lý:** Toàn bộ tệp CSS trang tại `core/static/core/css/pages/`
- **Nội dung kỹ thuật:**
  1. Quy chuẩn toàn bộ media queries theo 4 mốc: `--bp-mobile: 640px`, `--bp-tablet: 768px`, `--bp-laptop: 1024px`, `--bp-desktop: 1280px`.
  2. Xóa bỏ thẻ `<header>` và `<main>` lồng sai chuẩn HTML5 bên trong `courses/add.html`, `courses/edit.html`, `courses/delete.html`.
- **Tiêu chí nghiệm thu:** Kiểm thử hoàn hảo trên iPad Air (768px - 820px), iPhone và Laptop; mã HTML vượt qua bộ kiểm tra W3C Validator.

---

### GIAI ĐOẠN 4: TỐI ƯU TRẢI NGHIỆM, BÁO CÁO & KIỂM THỬ MỞ RỘNG
*Thời lượng: 4 ngày (Ngày 15 - Ngày 18)*  
*Mục tiêu: Hoàn thiện trải nghiệm người dùng, báo cáo xuất file chỉn chu và nâng cao độ phủ test tự động lên > 85%.*

#### Nhiệm vụ 4.1: Tối ưu hóa hàm Xuất Excel (Báo cáo Học viên & Học phí)
- **Tệp xử lý:** `core/handlers/students.py` (`student_export_excel`), `core/handlers/tuition.py` (`tuition_export_excel`)
- **Nội dung kỹ thuật:**
  1. Khi tính độ rộng tự động cho cột (`ws.column_dimensions[col_letter].width`), bỏ qua các dòng tiêu đề gộp 1 và 2 (`if cell.row > 3`).
  2. Cố định độ rộng hợp lý cho cột STT (8 ký tự), Mã học viên/phiếu (14 ký tự).
- **Tiêu chí nghiệm thu:** File Excel tải về mở lên có tỷ lệ cột cân đối, đẹp mắt, có thể in ấn ngay mà không cần chỉnh tay.

#### Nhiệm vụ 4.2: Tối ưu Điều hướng & Trải nghiệm Thông báo
- **Tệp xử lý:** `core/templates/core/base.html`, `core/handlers/certificates.py`
- **Nội dung kỹ thuật:**
  1. Thêm liên kết trực tiếp đến "Duyệt chuyển lớp" (`class_transfer_list`) và "Quy chế đánh giá" (`assessment_policy_list`) vào nhóm Quản trị Hệ thống trên Sidebar khi đăng nhập bằng quyền Admin.
  2. Cải thiện trang Xác minh Chứng chỉ (`certificate_verify`): Phân biệt rõ thông báo "Chứng chỉ có thật trong CSDL nhưng Blockchain đang tắt" với "Chứng chỉ giả mạo / Không tồn tại".
- **Tiêu chí nghiệm thu:** Quản trị viên dễ dàng tìm thấy tất cả tính năng quản trị chỉ với 1 click từ Sidebar.

#### Nhiệm vụ 4.3: Mở rộng Bộ kiểm thử tự động (Unit Tests & Integration Tests)
- **Tệp xử lý:** `core/tests/`
- **Nội dung kỹ thuật:**
  1. Thêm `test_tuition_workflow.py`: Kiểm tra thanh toán từng đợt, tính công nợ, chống ghi đè số tiền.
  2. Thêm `test_certificate_eligibility.py`: Kiểm tra cổng chặn cấp chứng chỉ khi còn nợ học phí hoặc vắng thi.
  3. Thêm `test_forms_validation.py`: Kiểm tra xác thực email trùng, số điện thoại không hợp lệ trên Django Forms.
  4. Đạt mục tiêu độ phủ kiểm thử (Test Coverage) > 85%, tổng số test cases đạt trên 40 tests.
- **Tiêu chí nghiệm thu:** Lệnh `python manage.py test` vượt qua 100% tests trong thời gian dưới 30 giây.

#### Nhiệm vụ 4.4: Kiểm thử Hồi quy toàn diện (Regression Testing) & Bàn giao
- **Nội dung kỹ thuật:**
  1. Kiểm thử trọn vẹn luồng học viên từ đầu đến cuối: Thêm học viên -> Đăng ký lớp -> Tự sinh học phí -> Thu tiền từng đợt -> Điểm danh -> Nhập điểm -> Cấp chứng chỉ băm Blockchain.
  2. Cập nhật tài liệu kỹ thuật và bàn giao mã nguồn hoàn thiện.

---

## III. MA TRẬN PHÂN LOẠI ƯU TIÊN THEO NGUYÊN TẮC MOSCOW (CẬP NHẬT)

| Mức độ | Các hạng mục công việc | Thời hạn hoàn thành |
|---|---|:---:|
| **MUST HAVE** *(Bắt buộc phải làm ngay)* | • Sửa câu truy vấn doanh thu Dashboard theo `PaymentTransaction`<br>• Khóa sửa tay `paid_amount` trong `tuition_edit`<br>• Sửa lỗi 403 nút "Duyệt chuyển lớp" trên `classes/list.html`<br>• Tự động tạo `Tuition` khi ghi danh học viên vào lớp<br>• Ràng buộc điều kiện học phí, điểm số khi cấp chứng chỉ<br>• Sửa lỗi hiển thị Dark Mode cho thanh phân trang | **Giai đoạn 1 & 2** |
| **SHOULD HAVE** *(Cần thiết cho tính đồng bộ)* | • Kết chuyển học phí khi duyệt chuyển lớp `ClassTransfer`<br>• Chuyển đổi Khóa học, Giáo viên, Lớp học sang Django Forms<br>• Đồng bộ hai chiều điểm số quy chế và bảng điểm 4 kỹ năng<br>• Dọn dẹp toàn bộ thẻ `<style>` inline vào file CSS riêng<br>• Chuẩn hóa toàn bộ hệ sinh thái Icon sang RemixIcon | **Giai đoạn 2 & 3** |
| **COULD HAVE** *(Làm tăng tính cao cấp & thẩm mỹ)* | • Sửa lỗi dãn cột tiêu đề khi xuất Excel<br>• Bổ sung link quản trị chuyển lớp và quy chế lên Sidebar Admin<br>• Thêm animation mượt mà khi lọc bảng dữ liệu | **Giai đoạn 4** |
| **WON'T HAVE** *(Chưa cần thiết lúc này)* | • Chuyển đổi sang kiến trúc Microservices<br>• Viết ứng dụng Mobile App riêng biệt<br>• Tích hợp cổng thanh toán trực tuyến bên ngoài (VNPAY/Momo) | *Xem xét sau khi Golive* |

---

## IV. BẢNG TIÊU CHÍ NGHIỆM THU ĐẠT CHUẨN (DEFINITION OF DONE - DOD)

Mỗi nhiệm vụ trong lộ trình nâng cấp chỉ được đánh dấu hoàn thành khi đáp ứng đủ 5 điều kiện:
1. **Logic & Nghiệp vụ:** Xử lý chính xác dữ liệu đầu vào - đầu ra, không phát sinh lỗi ngoại lệ hoặc sai lệch số học.
2. **Tính Đồng bộ:** Dữ liệu cập nhật tại một phân hệ phải lập tức phản ánh chính xác tại các phân hệ liên quan (Đào tạo ↔ Tài chính ↔ Điểm số ↔ Dashboard).
3. **Giao diện & Thẩm mỹ:** Đạt chuẩn hiển thị trên cả Light Mode và Dark Mode; co giãn tốt trên Mobile, Tablet và Desktop; tuân thủ Design System chung.
4. **Bảo mật & Phân quyền:** Tuân thủ chặt chẽ quyền hạn vai trò (Admin, Học vụ, Tài chính); không để lộ nút bấm dẫn đến lỗi 403 Forbidden.
5. **Kiểm thử tự động:** Có test case tương ứng và chạy lệnh `python manage.py test` đạt kết quả xanh (Pass 100%).

---

## V. BẢNG THEO DÕI TIẾN ĐỘ THI CÔNG CHI TIẾT

| Mã NV | Hạng mục công việc | Phân hệ | Mức ưu tiên | Trạng thái |
|:---:|---|:---:|:---:|:---:|
| **1.1** | Sửa câu truy vấn doanh thu biểu đồ Dashboard theo `PaymentTransaction` & Tái thiết kế Hero Charts chuẩn SaaS | Dashboard | P0 | ✅ Đã hoàn thành (05/11/2026) |
| **1.2** | Khóa sửa tay `paid_amount` trong `tuition_edit`, bảo toàn lịch sử giao dịch | Tài chính | P1 | ⏳ Đang làm |
| **1.3** | Sửa phân quyền nút "Duyệt chuyển lớp" tại `classes/list.html` tránh lỗi 403 | Phân quyền | P1 | ⏳ Đang làm |
| **2.1** | Tự động khởi tạo phiếu học phí `Tuition` khi ghi danh học viên vào lớp | Đào tạo | P1 | 📋 Chờ làm |
| **2.2** | Kiểm duyệt điều kiện cấp chứng chỉ (Công nợ = 0, Chuyên cần >= 80%, Điểm >= 5.0) | Chứng chỉ | P1 | 📋 Chờ làm |
| **2.3** | Xây dựng logic kết chuyển học phí khi học viên chuyển lớp | Đào tạo / Tài chính | P2 | 📋 Chờ làm |
| **2.4** | Đồng bộ hai chiều điểm số quy chế ↔ bảng điểm 4 kỹ năng cũ | Điểm số | P2 | 📋 Chờ làm |
| **2.5** | Chuyển đổi biểu mẫu Khóa học, Giáo viên, Lớp học sang Django Forms | Đào tạo | P2 | 📋 Chờ làm |
| **2.6** | Xóa mã chết dư thừa tại `student_edit` trong `students.py` | Học viên | P3 | 📋 Chờ làm |
| **3.1** | Sửa lỗi Dark Mode cho thanh phân trang `pagination.html` và các form | UI/UX | P1 | 📋 Chờ làm |
| **3.2** | Di chuyển toàn bộ CSS inline vào các tệp tĩnh riêng biệt | UI/UX | P2 | 📋 Chờ làm |
| **3.3** | Thống nhất toàn bộ hệ thống biểu tượng sang RemixIcon (`ri-*`) | UI/UX | P2 | 📋 Chờ làm |
| **3.4** | Chuẩn hóa Responsive Breakpoints (640, 768, 1024, 1280) & Ngữ nghĩa HTML | UI/UX | P2 | 📋 Chờ làm |
| **4.1** | Sửa lỗi dãn rộng cột STT khi xuất file Excel báo cáo | Báo cáo | P3 | 📋 Chờ làm |
| **4.2** | Bổ sung liên kết quản trị chuyển lớp và quy chế lên Sidebar Admin | Điều hướng | P3 | 📋 Chờ làm |
| **4.3** | Mở rộng bộ kiểm thử tự động Unit Tests (Coverage > 85%, > 40 test cases) | Kiểm thử | P2 | 📋 Chờ làm |
| **4.4** | Kiểm thử hồi quy toàn diện hệ thống và bàn giao nghiệm thu | Toàn hệ thống | P1 | 📋 Chờ làm |

---
*Kế hoạch và lộ trình này là căn cứ kỹ thuật chính thức để triển khai nâng cấp hệ thống `APP-Trung-Tam-Tieng-Anh` đạt tiêu chuẩn phần mềm thương mại thực tế.*
