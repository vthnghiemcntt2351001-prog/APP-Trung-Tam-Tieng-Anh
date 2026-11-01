# CẨM NANG HƯỚNG DẪN SỬ DỤNG HỆ THỐNG (USER MANUAL)
**Dự án:** Hệ thống Quản trị Trung tâm Tiếng Anh (English Center Management System)  
**Phiên bản:** v1.0.0 Enterprise  
**Dành cho:** Cán bộ Học vụ, Kế toán Tài chính & Quản trị viên Trung tâm  

---

## 1. ĐĂNG NHẬP VÀ ĐIỀU HƯỚNG HỆ THỐNG

1. **Truy cập:** Mở trình duyệt web và nhập địa chỉ hệ thống (ví dụ: `http://localhost:8000/` hoặc domain nội bộ).
2. **Đăng nhập:** Nhập Tên đăng nhập và Mật khẩu được cấp.
3. **Phân quyền tự động:**
   - Hệ thống tự động nhận diện vai trò của bạn và hiển thị các menu được phép truy cập.
   - Nếu bạn cố tình truy cập các đường dẫn vượt quyền (ví dụ Học vụ truy cập trang Thu tiền), hệ thống sẽ hiển thị trang thông báo **403 Forbidden - Từ chối quyền truy cập**.

---

## 2. HƯỚNG DẪN DÀNH CHO CÁN BỘ HỌC VỤ (ACADEMIC STAFF)

### 2.1. Quản lý Học viên
- **Thêm học viên mới:**
  1. Vào menu **Học viên** -> Nhấn nút **Thêm học viên**.
  2. Điền Họ và tên, Email, Số điện thoại, Ngày sinh và Địa chỉ.
  3. Nhấn **Lưu học viên**. Hệ thống sẽ kiểm tra trùng lặp Email tự động.
- **Tìm kiếm & Lọc học viên:**
  - Nhập tên, email hoặc số điện thoại vào thanh tìm kiếm.
  - Chọn tab **Đang học** hoặc **Đã lưu trữ** để xem danh sách tương ứng.
- **Lưu trữ học viên (Soft Delete):**
  - Để ngừng nhận học viên mà không làm mất lịch sử đóng học phí và chứng chỉ, nhấn **Ngừng hoạt động / Lưu trữ**. Bản ghi học viên được bảo toàn 100% trong cơ sở dữ liệu.

### 2.2. Quản lý Khóa học & Lớp học
- **Tạo lớp học mới:**
  1. Vào menu **Lớp học** -> Nhấn **Thêm lớp học**.
  2. Chọn Khóa học, Phân công Giáo viên phụ trách, Ngày bắt đầu, Ngày kết thúc và **Sĩ số tối đa** (mặc định 20 học viên).
  3. Nhấn **Lưu lớp học**.
- **Ghi danh học viên vào lớp:**
  1. Vào danh sách Lớp học -> Bấm vào tên lớp để xem **Chi tiết lớp học**.
  2. Tại bảng **Đăng ký học viên**, chọn học viên từ danh sách chưa xếp lớp.
  3. Nhấn **Đăng ký vào lớp**. Hệ thống sẽ tự động cập nhật thanh đo tỷ lệ sĩ số (ví dụ: `15/20 học viên - Còn 5 chỗ`).
  4. Nếu lớp đã đầy sĩ số, hệ thống sẽ cảnh báo màu đỏ và chặn không cho ghi danh quá giới hạn.

### 2.3. Quy trình Chuyển lớp cho Học viên (Class Transfer)
- **Trường hợp 1: Chuyển giữa 2 lớp CÙNG KHÓA HỌC:**
  1. Tại trang **Chi tiết lớp học**, tìm học viên trong danh sách.
  2. Chọn lớp đích cần chuyển đến -> Nhập lý do chuyển -> Nhấn **Chuyển lớp**.
  3. Hệ thống sẽ **tự động chuyển ngay lập tức**: Học viên chuyển sang trạng thái `Đang học` ở lớp mới, và ghi nhận `Đã chuyển lớp` ở lớp cũ.
- **Trường hợp 2: Chuyển giữa 2 lớp KHÁC KHÓA HỌC:**
  1. Học vụ thao tác tương tự như trên.
  2. Do khác chương trình đào tạo và học phí, hệ thống sẽ tự động chuyển đơn sang trạng thái **Chờ duyệt (PENDING)** và thông báo đến Quản trị viên (Admin).
  3. Khi Admin phê duyệt, học viên mới chính thức được chuyển sang lớp mới.

### 2.4. Quản lý Quy chế & Nhập điểm Học viên
- **Gán quy chế đánh giá cho lớp:**
  1. Vào menu **Điểm số & Đánh giá** -> Chọn lớp học tương ứng.
  2. Gán quy chế đánh giá điểm (ví dụ: Chuyên cần 10% + Giữa kỳ 40% + Cuối kỳ 50%).
- **Tạo đợt đánh giá & Nhập điểm:**
  1. Bấm **Tạo đợt đánh giá** (ví dụ: Thi giữa kỳ - Midterm Test).
  2. Chọn thành phần điểm và ngày tổ chức thi.
  3. Tại bảng nhập điểm, nhập điểm số cho từng học viên tham gia. Hệ thống có kiểm tra chặn nhập điểm số âm hoặc vượt quá điểm tối đa của thành phần.
  4. Bấm **Lưu kết quả**: Hệ thống tự động kích hoạt Service tính điểm trọng số và cập nhật trạng thái tổng kết (`Đạt` hoặc `Chưa đạt`).

---

## 3. HƯỚNG DẪN DÀNH CHO BỘ PHẬN TÀI CHÍNH / KẾ TOÁN (FINANCE)

### 3.1. Quản lý Học phí & Thu tiền
- **Tạo khoản học phí mới:**
  1. Vào menu **Học phí** -> Nhấn **Tạo phiếu học phí**.
  2. Chọn Học viên và Lớp học (học phí chuẩn của khóa học sẽ tự động được gợi ý).
  3. Nhập số tiền thu đợt đầu (nếu có), ngày nộp tiền và ghi chú.
  4. Nhấn **Lưu phiếu thu**.
- **Cập nhật đóng tiền thêm:**
  1. Tại danh sách học phí, bấm **Thu tiền** trên dòng học viên tương ứng.
  2. Nhập số tiền đóng thêm. Hệ thống tự động tính toán lại:
     - Số tiền đã đóng lũy kế.
     - Số tiền còn nợ (`total_fee - paid_amount`).
     - Tự động đổi trạng thái sang `Đã thanh toán`, `Thanh toán một phần` hoặc `Chưa thanh toán`.

### 3.2. In Biên lai Thu tiền chuẩn A5
- Tại phiếu học phí của học viên, bấm biểu tượng **In biên lai**.
- Giao diện biên lai hiển thị chuẩn mực: Mã phiếu thu (`PT-xxxxx`), Tên học viên, Khóa học, Số tiền bằng số và **Số tiền viết bằng chữ tiếng Việt** (tự động chuyển đổi).
- Nhấn phím `Ctrl + P` hoặc nút **In phiếu**: Giao diện được định dạng in ấn tối ưu cho giấy A5/A4, ẩn toàn bộ thanh điều hướng của website.

### 3.3. Xuất Báo cáo Học phí ra file Excel
- Tại trang danh sách học phí, bấm nút **Xuất Excel**.
- Hệ thống sẽ trích xuất toàn bộ dữ liệu ra tệp `.xlsx` chuyên nghiệp, đầy đủ định dạng số tiền VNĐ, ngày tháng và bảng tổng hợp doanh thu.

---

## 4. HƯỚNG DẪN DÀNH CHO QUẢN TRỊ VIÊN (ADMIN)

### 4.1. Phê duyệt Đơn chuyển lớp
1. Vào menu **Duyệt chuyển lớp** (chỉ hiển thị cho tài khoản Quản trị viên).
2. Xem danh sách các yêu cầu chuyển lớp khác khóa học đang ở trạng thái `Chờ duyệt`.
3. Kiểm tra sĩ số lớp mới:
   - Nếu lớp mới còn chỗ trống: Bấm **Phê duyệt** để hoàn tất việc chuyển học viên.
   - Nếu không đồng ý: Nhấn **Từ chối đơn** kèm lý do từ chối. Ghi danh lớp cũ của học viên được giữ nguyên.

### 4.2. Cấp Chứng chỉ Tốt nghiệp lên Blockchain
1. Vào menu **Chứng chỉ**.
2. Chọn học viên đã hoàn thành khóa học và đạt điểm chuẩn.
3. Bấm nút **Cấp lên Blockchain**:
   - Hệ thống sẽ đóng gói dữ liệu kết quả học tập, băm mật mã và gửi giao dịch lên Smart Contract.
   - Khi hoàn tất, hệ thống trả về Mã giao dịch (TxHash) và Số Block vĩnh viễn trên sổ cái.
4. **Tra cứu công khai:** Phụ huynh và nhà tuyển dụng có thể vào trang `/certificates/verify/` để nhập mã chứng chỉ hoặc quét mã QR xác thực tính toàn vẹn 100%, không thể làm giả.
