# TÀI LIỆU KHẢO SÁT VÀ PHÂN TÍCH TOÀN DIỆN HỆ THỐNG PHỤC VỤ XÂY DỰNG BẢNG ĐẶC TẢ USE CASE

**Dự án:** Hệ thống Quản trị Trung tâm Tiếng Anh tích hợp Blockchain (**VISTA** - `APP-Trung-Tam-Tieng-Anh`)  
**Tài liệu:** `SYSTEM_ANALYSIS_FOR_USE_CASE_SPECIFICATION.md`  
**Vai trò thực hiện:** System Analyst (Chuyên viên Phân tích Hệ thống)  
**Ngày lập:** 06/11/2026  
**Trạng thái tài liệu:** Bản khảo sát chi tiết & Thu thập thông tin (Giai đoạn tiền đặc tả)  

---

## PHẦN I. TỔNG QUAN HỆ THỐNG

### 1. Mục đích hệ thống
Hệ thống **VISTA** là phần mềm quản trị tích hợp dành cho trung tâm tiếng Anh, số hóa toàn bộ chu trình vận hành từ tuyển sinh, đào tạo, quản lý tài chính, khảo thí điểm số cho đến cấp phát và xác minh văn bằng/chứng chỉ tốt nghiệp. Đặc biệt, hệ thống giải quyết bài toán chống gian lận học vị và làm giả điểm số thông qua việc ứng dụng công nghệ **Hợp đồng thông minh (Smart Contract)** trên nền tảng **Ethereum Blockchain**.

### 2. Công nghệ và Kiến trúc tổng thể
- **Kiến trúc phần mềm:** Kiến trúc **MVT (Model - View - Template)** của Django kết hợp mô hình **Client - Server** theo cơ chế **Server-Side Rendering (SSR)**.
- **Kiến trúc dữ liệu:** Mô hình lưu trữ lai (**Hybrid Storage**):
  - *Dữ liệu nghiệp vụ chi tiết (Off-chain):* Hệ quản trị CSDL quan hệ **MySQL 8.0** (`utf8mb4`).
  - *Dữ liệu toàn vẹn mật mã (On-chain):* Mạng **Ethereum Blockchain (Ganache Testnet RPC: `127.0.0.1:7545`)**, Smart Contract `CertificateVerification.sol`, SDK **Web3.py (v7.x)**, hàm băm **Keccak-256**.
- **Backend Framework:** **Python 3.12+/3.14** & **Django Framework 6.1.2**; xác thực qua **Session Authentication** & Custom Backend `EmailOrUsernameModelBackend`; phân quyền vai trò **RBAC (Role-Based Access Control)** qua Custom Decorators.
- **Frontend Layer:** **HTML5, CSS3, JavaScript (ES6+)**, Django Template Language (DTL), **Chart.js (v4.x)**, **RemixIcon (v4.3)**, hỗ trợ **Dark Mode / Light Mode**.
- **Thư viện tích hợp:** `openpyxl` (xuất báo cáo Excel), `mysqlclient` (kết nối C-Driver), `python-dotenv` (bảo mật biến môi trường).

### 3. Các phân hệ (Modules) chính
1. **Module Xác thực & Quản trị Hệ thống (System & Auth):** Đăng nhập linh hoạt (Username/Email), kiểm soát phiên làm việc, quản lý tài khoản người dùng, phân quyền RBAC và chuyển đổi giao diện sáng/tối.
2. **Module Quản lý Học viên (Students):** Tiếp nhận hồ sơ, sinh mã `HV-xxxx`, tra cứu 360°, cập nhật thông tin và theo dõi trạng thái học tập.
3. **Module Quản lý Giáo viên (Teachers):** Hồ sơ giảng viên, sinh mã `GV-xxxx`, bằng cấp, thông tin liên hệ và lịch phân công đứng lớp.
4. **Module Quản lý Khóa học (Courses):** Quản lý danh mục chương trình học, thời lượng, học phí tiêu chuẩn và trạng thái tuyển sinh.
5. **Module Quản lý Lớp học & Xếp lớp (Classes & Enrollments):** Mở lớp, phân công giáo viên, giới hạn sĩ số, xếp lịch học, ghi danh học viên và luân chuyển lớp học (`ClassTransfer`).
6. **Module Thời khóa biểu & Điểm danh (Attendance):** Tự động sinh danh sách buổi học (`ClassSession`), điểm danh học viên từng buổi (4 trạng thái), tính tỷ lệ chuyên cần.
7. **Module Điểm số & Khảo thí (Grading & Assessment Policy):** Cấu hình quy chế đánh giá linh hoạt (thang điểm 10, IELTS Band, Pass/Fail), nhập điểm thành phần có trọng số %, tính điểm tổng kết và xếp loại học lực.
8. **Module Tài chính & Học phí (Finance & Tuition):** Tự động sinh phiếu học phí khi ghi danh, thu tiền nhiều đợt (tiền mặt, chuyển khoản, thẻ), in biên lai thanh toán và xuất báo cáo Excel (`.xlsx`).
9. **Module Chứng chỉ & Blockchain (Certificates & Blockchain):** Cổng kiểm duyệt điều kiện (Gatekeeper), quy trình phê duyệt 2 bước (Học vụ đề xuất $\rightarrow$ Admin duyệt & ký số băm Keccak-256 lên Smart Contract Ganache), cổng xác minh tính toàn vẹn công khai.
10. **Module Bảng điều khiển & Báo cáo (Dashboard):** Chỉ số KPI thời gian thực, biểu đồ doanh thu tài chính (Area Chart) và cơ cấu công nợ (Doughnut Chart).

### 4. Danh sách Tác nhân (Actors)
1. **Quản trị viên (ADMIN) - Primary Actor:**
   - Người nắm toàn quyền hệ thống (`is_superuser=True` hoặc thuộc nhóm `Admin`).
   - Quản trị tài khoản nhân sự, phân vai trò, phê duyệt chuyển lớp khác khóa học, chủ sở hữu ví Smart Contract (Contract Owner) trực tiếp thẩm định và ký số phát hành chứng chỉ lên Blockchain.
   - Có quyền can thiệp cấp cao (Admin Override) vào toàn bộ dữ liệu đào tạo và tài chính khi cần xử lý ngoại lệ.
2. **Nhân viên Đào tạo (ACADEMIC STAFF / Học vụ) - Primary Actor:**
   - Nhân sự thuộc nhóm `Học vụ` (`ROLE_ACADEMIC`).
   - Trực tiếp quản lý hồ sơ học viên, giáo viên, khóa học, lớp học, ghi danh, điểm danh buổi học, nhập sổ điểm theo quy chế, và lập hồ sơ đề xuất cấp chứng chỉ tốt nghiệp (Step 1).
   - Bị giới hạn: Không có quyền truy cập module Tài chính, không có quyền duyệt chuyển lớp khác khóa, không có quyền can thiệp vào nút ký số Blockchain.
3. **Kế toán (ACCOUNTANT / Tài chính) - Primary Actor:**
   - Nhân sự thuộc nhóm `Tài chính` (`ROLE_FINANCE`).
   - Quản lý danh sách học phí, theo dõi công nợ, lập phiếu thu thanh toán, in biên lai cho học viên và xuất báo cáo Excel.
   - Bị giới hạn: Không có quyền truy cập vào các module Đào tạo, lớp học, điểm số, chứng chỉ và quản trị tài khoản.
4. **Hệ thống Blockchain (BLOCKCHAIN NODE / Smart Contract) - Secondary / System Actor:**
   - Mạng Ethereum / Ganache RPC cục bộ tiếp nhận giao dịch ghi mã băm chứng chỉ, đóng dấu khối (Block Number, TxHash) và cung cấp hàm đối chiếu dữ liệu theo thời gian thực.
5. **Người dùng công khai / Học viên / Nhà tuyển dụng (PUBLIC GUEST) - Secondary Actor:**
   - Người dùng bên ngoài trung tâm truy cập cổng xác minh chứng chỉ trực tuyến (`/certificates/verify/`) mà không cần đăng nhập.

---

## PHẦN II. DANH SÁCH USE CASE HỆ THỐNG

| Mã Use Case | Tên Use Case | Tác nhân chính | Module nghiệp vụ | Trạng thái triển khai |
|:---:|---|---|---|:---:|
| **UC01** | Đăng nhập hệ thống | Admin, Nhân viên Đào tạo, Kế toán | Xác thực & Quản trị | **Hoàn thành** |
| **UC02** | Đăng xuất hệ thống | Admin, Nhân viên Đào tạo, Kế toán | Xác thực & Quản trị | **Hoàn thành** |
| **UC03** | Quản lý tài khoản người dùng | Admin | Xác thực & Quản trị | **Hoàn thành** |
| **UC04** | Phân quyền vai trò người dùng | Admin | Xác thực & Quản trị | **Hoàn thành** |
| **UC05** | Quản lý hồ sơ học viên | Admin, Nhân viên Đào tạo | Quản lý Đào tạo | **Hoàn thành** |
| **UC06** | Quản lý hồ sơ giáo viên | Admin, Nhân viên Đào tạo | Quản lý Đào tạo | **Hoàn thành** |
| **UC07** | Quản lý danh mục khóa học | Admin, Nhân viên Đào tạo | Quản lý Đào tạo | **Hoàn thành** |
| **UC08** | Quản lý lớp học & ghi danh | Admin, Nhân viên Đào tạo | Quản lý Đào tạo | **Hoàn thành** |
| **UC09** | Yêu cầu & phê duyệt chuyển lớp | Admin, Nhân viên Đào tạo | Quản lý Đào tạo | **Hoàn thành** |
| **UC10** | Quản lý buổi học & điểm danh | Admin, Nhân viên Đào tạo | Thời khóa biểu | **Hoàn thành** |
| **UC11** | Cấu hình quy chế đánh giá điểm | Admin | Khảo thí & Điểm số | **Hoàn thành** |
| **UC12** | Quản lý sổ điểm & tổng kết điểm | Admin, Nhân viên Đào tạo | Khảo thí & Điểm số | **Hoàn thành** |
| **UC13** | Quản lý học phí & công nợ | Admin, Kế toán | Quản lý Tài chính | **Hoàn thành** |
| **UC14** | Lập phiếu thu & in biên lai | Admin, Kế toán | Quản lý Tài chính | **Hoàn thành** |
| **UC15** | Xuất báo cáo tài chính ra Excel | Admin, Kế toán | Quản lý Tài chính | **Hoàn thành** |
| **UC16** | Lập đề xuất cấp chứng chỉ | Nhân viên Đào tạo, Admin | Chứng chỉ & Blockchain | **Hoàn thành** |
| **UC17** | Phê duyệt & Ký số Blockchain | Admin (Chủ sở hữu hợp đồng) | Chứng chỉ & Blockchain | **Hoàn thành** |
| **UC18** | Xác minh chứng chỉ công khai | Public Guest, Mọi tác nhân | Chứng chỉ & Blockchain | **Hoàn thành** |
| **UC19** | Theo dõi Dashboard thống kê | Admin, Nhân viên Đào tạo, Kế toán | Giám sát & Báo cáo | **Hoàn thành** |

---

## PHẦN III. PHÂN TÍCH CHI TIẾT USE CASE TRỌNG TÂM: NHÓM QUẢN LÝ TÀI KHOẢN & XÁC THỰC

### USE CASE UC01: ĐĂNG NHẬP HỆ THỐNG

#### 1. Tên và Mục tiêu
- **Mã Use Case:** UC01
- **Tên Use Case:** Đăng nhập hệ thống (System Login)
- **Mục tiêu:** Xác minh danh tính người dùng nội bộ, cấp phiên làm việc hợp lệ (Session) và chuyển hướng tới giao diện chức năng phù hợp với vai trò được phân quyền.

#### 2. Tác nhân
- **Tác nhân chính:** Quản trị viên (Admin), Nhân viên Đào tạo, Kế toán.
- **Tác nhân phụ:** Không.

#### 3. Mô tả nghiệp vụ
Người dùng truy cập vào trang đăng nhập, cung cấp định danh (có thể là Tên đăng nhập `username` hoặc Địa chỉ `email`) và Mật khẩu `password`. Hệ thống kiểm tra thông tin đối chiếu với cơ sở dữ liệu, đảm bảo tài khoản đang ở trạng thái hoạt động (`is_active=True`), sau đó tạo phiên làm việc bảo mật và chuyển hướng người dùng vào trang Bảng điều khiển (Dashboard).

#### 4. Tiền điều kiện
- Người dùng đã được cấp tài khoản trong hệ thống (`auth_user`).
- Người dùng chưa đăng nhập hoặc phiên đăng nhập trước đó đã hết hạn.
- Thiết bị có kết nối mạng tới máy chủ ứng dụng.

#### 5. Luồng sự kiện chính (Basic Flow)
1. Người dùng truy cập đường dẫn đăng nhập `/accounts/login/` trên trình duyệt.
2. Hệ thống hiển thị form đăng nhập gồm 2 ô nhập: "Tài khoản" (Username/Email) và "Mật khẩu", kèm nút chuyển đổi giao diện Sáng/Tối.
3. Người dùng nhập tên đăng nhập hoặc email, nhập mật khẩu và nhấn nút "Đăng nhập".
4. Hệ thống tiếp nhận yêu cầu `POST`, gọi Custom Authentication Backend `EmailOrUsernameModelBackend` tại `core/backends.py`.
5. Hệ thống tìm kiếm bản ghi trong bảng `auth_user` khớp không phân biệt hoa thường với username hoặc email (`Q(username__iexact=...) | Q(email__iexact=...)`).
6. Hệ thống thực hiện kiểm tra mật khẩu bằng thuật toán băm bảo mật `user.check_password(password)`.
7. Hệ thống kiểm tra cờ trạng thái `user.is_active` (phải bằng `True`).
8. Xác thực thành công: Hệ thống sinh `session_key`, lưu thông tin phiên vào bảng `django_session`, ghi nhận `last_login`, tạo Cookie phiên (`sessionid`) trên trình duyệt với cờ bảo mật `HttpOnly` và `SameSite=Lax`.
9. Hệ thống chuyển hướng người dùng về trang chủ `/` (Dashboard).

#### 6. Các luồng sự kiện thay thế (Alternative Flows)
- **Alt 1 - Đăng nhập bằng Email thay vì Username:** Tại bước 3, người dùng nhập địa chỉ email hợp lệ đã đăng ký (ví dụ: `admin@englishcenter.edu.vn`). Backend tại bước 5 tự động phát hiện khớp với trường `email` và xác thực bình thường.
- **Alt 2 - Đăng nhập có tham số chuyển hướng tiếp theo (`?next=/...`):** Tại bước 1, người dùng truy cập một trang được bảo vệ (ví dụ `/tuitions/`). Hệ thống tự động đính kèm `?next=/tuitions/`. Sau khi đăng nhập thành công ở bước 8, hệ thống chuyển hướng thẳng tới trang đích trong tham số `next` thay vì trang chủ.

#### 7. Các luồng ngoại lệ (Exception Flows)
- **Ex 1 - Bỏ trống tên đăng nhập hoặc mật khẩu:**
  - *Điều kiện:* Người dùng nhấn đăng nhập khi một trong 2 trường để trống.
  - *Hệ thống xử lý:* Thuộc tính `required` của HTML5 cảnh báo trên ô nhập; nếu gửi `POST` rỗng, backend trả về lỗi "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu", giữ nguyên form đăng nhập.
- **Ex 2 - Sai tên đăng nhập hoặc sai mật khẩu:**
  - *Điều kiện:* Không tìm thấy user hoặc `check_password()` trả về `False`.
  - *Hệ thống xử lý:* Hiển thị hộp thông báo lỗi màu đỏ: *"Tài khoản hoặc mật khẩu chưa chính xác. Vui lòng thử lại."* (tại `login.html`), không tiết lộ việc sai username hay sai password để chống dò quét tài khoản.
- **Ex 3 - Tài khoản bị khóa (`is_active=False`):**
  - *Điều kiện:* Người dùng nhập đúng username và password nhưng tài khoản đã bị Admin khóa.
  - *Hệ thống xử lý:* `self.user_can_authenticate(user)` trả về `False`. Hệ thống từ chối đăng nhập và báo lỗi tài khoản không hợp lệ.
- **Ex 4 - Truy cập trái quyền sau khi đăng nhập (`next` bị chặn):**
  - *Điều kiện:* Kế toán đăng nhập thành công nhưng trước đó yêu cầu vào trang `/assessment-policies/`.
  - *Hệ thống xử lý:* Decorator `@admin_required` chặn lại và trả về mã lỗi HTTP 403 Forbidden kèm thông báo: *"Bạn không có quyền thực hiện chức năng này."*

#### 8. Hậu điều kiện (Post-conditions)
- Trạng thái người dùng chuyển thành `Authenticated`.
- Một phiên làm việc mới được tạo trong bảng `django_session`.
- Trường `last_login` trong bảng `auth_user` được cập nhật thời gian đăng nhập gần nhất.
- Giao diện người dùng nạp thanh điều hướng với các module được phân quyền tương ứng.

#### 9. Dữ liệu đầu vào và đầu ra
- **Đầu vào:**
  - `username` (String, độ dài $\le 150$, bắt buộc).
  - `password` (String, độ dài $\le 128$, bắt buộc).
  - `csrfmiddlewaretoken` (String, 64 ký tự, bắt buộc chống tấn công CSRF).
  - `next` (String URL, tùy chọn).
- **Đầu ra:**
  - Đối tượng người dùng đã xác thực `request.user`.
  - Cookie phiên `sessionid` và Cookie `csrftoken`.
  - Giao diện trang Dashboard (HTTP 302 Redirect $\rightarrow$ HTTP 200).

#### 10. Các quy tắc nghiệp vụ (Business Rules)
- **BR01.1 (Định danh không phân biệt hoa thường):** Người dùng có thể gõ `Admin`, `admin`, hoặc `ADMIN` đều được chấp nhận (`__iexact`).
- **BR01.2 (Bảo vệ brute-force & mật khẩu):** Mật khẩu lưu trữ bắt buộc băm bằng thuật toán an toàn PBKDF2 với SHA256 và chuỗi salt độc lập, không lưu mật khẩu thô (plain-text).
- **BR01.3 (Bảo mật phiên làm việc):** Cờ `SESSION_COOKIE_HTTPONLY = True`, `SESSION_COOKIE_SAMESITE = 'Lax'`.
- **BR01.4 (Bảo mật CSRF):** Mọi request `POST` đều phải đính kèm `{% csrf_token %}` hợp lệ, nếu không trả về lỗi HTTP 403.

#### 11. Các bảng Database liên quan
- `auth_user`: Đọc thông tin `username`, `email`, `password`, `is_active`, `is_superuser`; cập nhật `last_login`.
- `auth_user_groups` & `auth_group`: Nạp danh sách các nhóm vai trò (`Admin`, `Học vụ`, `Tài chính`) liên kết với user.
- `django_session`: Thêm bản ghi phiên làm việc mới (`session_key`, `session_data`, `expire_date`).

#### 12. Vị trí Code và Thành phần xử lý
- **URL Routing:** `config/urls.py` (`path('accounts/login/', ...)`).
- **Template:** `core/templates/core/auth/login.html`.
- **Custom Auth Backend:** `core/backends.py` (`class EmailOrUsernameModelBackend`).
- **Settings:** `config/settings.py` (`AUTHENTICATION_BACKENDS`, `LOGIN_URL`, `LOGIN_REDIRECT_URL`).

---

### USE CASE UC03: QUẢN LÝ TÀI KHOẢN NGƯỜI DÙNG

#### 1. Tên và Mục tiêu
- **Mã Use Case:** UC03
- **Tên Use Case:** Quản lý tài khoản người dùng nội bộ (User Account Management)
- **Mục tiêu:** Cung cấp cho Quản trị viên công cụ xem danh sách, thêm mới, cập nhật thông tin, cấp lại mật khẩu, khóa/mở khóa và xóa tài khoản nhân sự trong hệ thống.

#### 2. Tác nhân
- **Tác nhân chính:** Quản trị viên (ADMIN).
- **Tác nhân phụ:** Không (Nhân viên Đào tạo và Kế toán hoàn toàn bị cấm truy cập).

#### 3. Mô tả nghiệp vụ
Quản trị viên truy cập trang quản lý tài khoản để theo dõi toàn bộ nhân sự đang sử dụng hệ thống. Admin có thể thực hiện tìm kiếm, lọc theo vai trò, thêm tài khoản mới và gán vai trò tương ứng (`Admin`, `Học vụ`, `Tài chính`), chỉnh sửa thông tin nhân viên, đặt lại mật khẩu mới, khóa tạm thời hoặc xóa vĩnh viễn tài khoản khỏi hệ thống khi nhân viên nghỉ việc.

#### 4. Tiền điều kiện
- Người dùng đã đăng nhập với vai trò **Quản trị viên** (`is_superuser=True` hoặc thuộc nhóm `Admin`).

#### 5. Luồng sự kiện chính (Basic Flow)
1. Admin chọn menu "Hệ thống" $\rightarrow$ "Quản lý tài khoản" (URL: `/system/users/`).
2. Hệ thống kiểm tra quyền `@admin_required`: Cho phép truy cập.
3. Hệ thống truy vấn bảng `auth_user`, nạp danh sách người dùng kèm vai trò (`groups`), tính toán 4 chỉ số thống kê (Tổng tài khoản, số Admin, số Học vụ, số Tài chính) và phân trang 15 bản ghi/trang.
4. Hệ thống hiển thị giao diện danh sách tài khoản (`core/system/users/list.html`).
5. **Thao tác tạo tài khoản mới:**
   - a. Admin nhấn nút "+ Tạo tài khoản mới".
   - b. Hệ thống hiển thị modal biểu mẫu nhập liệu.
   - c. Admin nhập Tên đăng nhập (username), Mật khẩu khởi tạo, Họ đệm, Tên, Email, chọn Vai trò (`Admin`/`Học vụ`/`Tài chính`), tích chọn cờ kích hoạt và nhấn "Xác nhận tạo tài khoản".
   - d. Hệ thống nhận request `POST` tới `/system/users/add/`.
   - e. Hệ thống kiểm tra trùng lặp username trong bảng `auth_user`.
   - f. Hệ thống tạo tài khoản qua `User.objects.create_user(...)`, mã hóa mật khẩu, liên kết user với Group vai trò tương ứng và cấp cờ `is_staff=True` nếu là Admin.
   - g. Hệ thống hiển thị thông báo thành công: *"Đã tạo tài khoản '[username]' thành công."* và nạp lại danh sách.

#### 6. Các luồng sự kiện thay thế (Alternative Flows)
- **Alt 1 - Tìm kiếm và lọc tài khoản:**
  - Tại bước 4, Admin nhập từ khóa vào ô tìm kiếm (tìm theo username, họ tên, email) hoặc bấm vào các nút pill vai trò (`Admin`, `Học vụ`, `Tài chính`). Hệ thống lọc dữ liệu qua câu lệnh `Q(...)` và hiển thị danh sách tương ứng.
- **Alt 2 - Chỉnh sửa thông tin & Đặt lại mật khẩu (User Edit):**
  - Tại bước 4, Admin nhấn nút "Sửa" tại một dòng tài khoản.
  - Hệ thống mở modal chỉnh sửa, nạp sẵn thông tin cũ (username bị vô hiệu hóa không cho sửa).
  - Admin cập nhật Họ tên, Email, thay đổi Vai trò, hoặc nhập mật khẩu mới vào ô "Đặt lại mật khẩu mới", sau đó nhấn "Lưu thay đổi".
  - Backend tại `user_edit()` cập nhật các trường, nếu có mật khẩu mới (độ dài $\ge 6$ ký tự) thì gọi `user.set_password(new_password)`. Lưu thay đổi và thông báo thành công.
- **Alt 3 - Khóa / Mở khóa tài khoản (Toggle Active Status):**
  - Tại bước 4, Admin nhấn nút biểu tượng Khóa/Mở khóa trên dòng người dùng.
  - Hệ thống gửi request `POST` tới `/system/users/<id>/toggle-status/`.
  - Backend đảo ngược giá trị cờ `user.is_active = not user.is_active` và lưu vào DB.
  - Thông báo: *"Đã tạm khóa tài khoản '...' "* hoặc *"Đã mở khóa tài khoản '...' "*.

#### 7. Các luồng ngoại lệ (Exception Flows)
- **Ex 1 - Người dùng không phải Admin truy cập:**
  - *Điều kiện:* Nhân viên Đào tạo hoặc Kế toán cố tình nhập URL `/system/users/`.
  - *Hệ thống xử lý:* Decorator `@admin_required` chặn lại, trả về mã HTTP 403 Forbidden: *"Bạn không có quyền truy cập chức năng này."*
- **Ex 2 - Trùng tên đăng nhập khi tạo mới:**
  - *Điều kiện:* Admin nhập username đã tồn tại trong bảng `auth_user`.
  - *Hệ thống xử lý:* `User.objects.filter(username=username).exists()` trả về `True`. Hệ thống báo lỗi: *"Tên đăng nhập '[username]' đã tồn tại trong hệ thống."* và hủy thao tác tạo.
- **Ex 3 - Bỏ trống tên đăng nhập hoặc mật khẩu khi tạo:**
  - *Hệ thống xử lý:* Báo lỗi: *"Tên đăng nhập và mật khẩu không được để trống."*
- **Ex 4 - Đặt mật khẩu mới quá ngắn khi sửa:**
  - *Điều kiện:* Admin nhập mật khẩu mới dưới 6 ký tự.
  - *Hệ thống xử lý:* Báo lỗi: *"Mật khẩu mới phải có ít nhất 6 ký tự."* và không lưu mật khẩu mới.
- **Ex 5 - Tự khóa hoặc tự xóa tài khoản của chính mình:**
  - *Điều kiện:* Admin đang đăng nhập nhấn nút khóa hoặc xóa tài khoản của chính mình (`request.user.id == user.id`).
  - *Hệ thống xử lý:* Bị chặn tại backend với thông báo lỗi: *"Bạn không thể khóa tài khoản của chính mình"* hoặc *"Bạn không thể xóa tài khoản đang đăng nhập của chính mình."*
- **Ex 6 - Khóa hoặc xóa tài khoản Superuser tối cao:**
  - *Điều kiện:* Admin cố tình khóa hoặc xóa tài khoản có cờ `is_superuser=True`.
  - *Hệ thống xử lý:* Bị chặn tại backend: *"Không thể khóa/xóa tài khoản Superuser của hệ thống."*

#### 8. Hậu điều kiện (Post-conditions)
- Bản ghi mới được tạo hoặc cập nhật trong bảng `auth_user` và `auth_user_groups`.
- Nếu bị xóa, bản ghi user và liên kết nhóm bị xóa vĩnh viễn khỏi DB.
- Trạng thái danh sách người dùng trên giao diện được cập nhật tức thì.

#### 9. Dữ liệu đầu vào và đầu ra
- **Đầu vào (Tạo mới/Cập nhật):**
  - `username` (String, $\le 150$ ký tự, bắt buộc khi tạo, bất biến khi sửa).
  - `password` / `new_password` (String, $\ge 6$ ký tự).
  - `first_name`, `last_name` (String, $\le 150$ ký tự, tùy chọn).
  - `email` (Email hợp lệ, $\le 254$ ký tự, tùy chọn).
  - `role` (String, giá trị thuộc `['Admin', 'Học vụ', 'Tài chính']`).
  - `is_active` (Boolean).
- **Đầu ra:**
  - Thông báo thành công dạng Toast/Alert.
  - Danh sách bảng hiển thị thông tin cập nhật: Avatar chữ cái đầu, Username, Họ tên, Email, Huy hiệu vai trò, Huy hiệu trạng thái Hoạt động/Đã khóa.

#### 10. Các quy tắc nghiệp vụ (Business Rules)
- **BR03.1 (Toàn vẹn danh tính):** Username là định danh duy nhất và không được phép chỉnh sửa sau khi đã khởi tạo thành công (`disabled` trên giao diện, không nhận update ở backend).
- **BR03.2 (An toàn quyền sở hữu):** Tuyệt đối không cho phép tài khoản tự tước quyền đăng nhập của chính mình (chống lỗi lockout toàn hệ thống).
- **BR03.3 (Bảo vệ Superuser):** Tài khoản Superuser gốc không thể bị vô hiệu hóa hoặc xóa bởi bất kỳ thao tác nào từ giao diện Web.
- **BR03.4 (Tiêu chuẩn mật khẩu):** Mật khẩu reset/khởi tạo phải có độ dài tối thiểu 6 ký tự.
- **BR03.5 (Đồng bộ cờ Staff):** Nếu được gán vai trò `Admin`, hệ thống tự động gắn cờ `is_staff=True` để có quyền truy cập các cấu hình hệ thống cấp cao.

#### 11. Các bảng Database liên quan
- `auth_user`: Bảng chính lưu trữ thông tin tài khoản nhân sự.
- `auth_group`: Bảng danh mục vai trò (`Admin`, `Học vụ`, `Tài chính`).
- `auth_user_groups`: Bảng trung gian ánh xạ quan hệ nhiều-nhiều (N-N) giữa user và vai trò.

#### 12. Vị trí Code và Thành phần xử lý
- **URL Routing:** `core/urls.py` (các đường dẫn `/system/users/...`).
- **Handler xử lý:** `core/handlers/system.py` (`user_list`, `user_add`, `user_edit`, `user_toggle_status`, `user_delete`).
- **Template giao diện:** `core/templates/core/system/users/list.html`.
- **CSS giao diện:** `core/static/core/css/pages/system/system.css`.
- **Bảo mật:** `core/permissions.py` (Decorator `@admin_required`).

---

## PHẦN IV. MA TRẬN PHÂN QUYỀN TRUY CẬP (RBAC MATRIX)

*Dựa trên việc kiểm tra thực tế các Decorator (`@admin_required`, `@academic_required`, `@finance_required`, `@staff_required`) và logic kiểm tra `has_role()` trong source code:*

| STT | Phân hệ / Chức năng chi tiết | Quản trị viên (Admin) | Nhân viên Đào tạo (Học vụ) | Kế toán (Tài chính) | Căn cứ mã nguồn (Decorator / File) |
|:---:|---|:---:|:---:|:---:|---|
| **1** | **Bảng điều khiển (Dashboard)** | Được phép | Được phép | Được phép | `@login_required` (`dashboard.py`) |
| **2** | **Quản lý tài khoản người dùng** | **Được phép** | Không được phép | Không được phép | `@admin_required` (`system.py`) |
| **3** | **Xem ma trận phân quyền vai trò** | **Được phép** | Không được phép | Không được phép | `@admin_required` (`system.py`) |
| **4** | **Xem & tra cứu hồ sơ học viên** | Được phép | Được phép | Không được phép | `@academic_required` (`students.py`) |
| **5** | **Thêm, sửa, xóa học viên** | Được phép | Được phép | Không được phép | `@academic_required` (`students.py`) |
| **6** | **Xuất danh sách học viên ra Excel** | Được phép | Được phép | Không được phép | `@academic_required` (`students.py`) |
| **7** | **Quản lý danh mục khóa học** | Được phép | Được phép | Không được phép | `@academic_required` (`academics.py`) |
| **8** | **Quản lý danh sách giáo viên** | Được phép | Được phép | Không được phép | `@academic_required` (`academics.py`) |
| **9** | **Quản lý lớp học & mở lớp mới** | Được phép | Được phép | Không được phép | `@academic_required` (`academics.py`) |
| **10** | **Ghi danh học viên vào lớp học** | Được phép | Được phép | Không được phép | `@academic_required` (`academics.py`) |
| **11** | **Yêu cầu chuyển lớp học viên** | Được phép | Được phép | Không được phép | `@academic_required` (`class_transfers.py`) |
| **12** | **Phê duyệt chuyển lớp khác khóa học** | **Được phép** | Không được phép | Không được phép | `@admin_required` (`class_transfers.py`) |
| **13** | **Điểm danh học viên theo buổi học** | Được phép | Được phép | Không được phép | `@academic_required` (`attendance.py`) |
| **14** | **Cấu hình quy chế đánh giá điểm** | **Được phép** | Không được phép | Không được phép | `@admin_required` (`assessments.py`) |
| **15** | **Nhập điểm sổ điểm & tổng kết** | Được phép | Được phép | Không được phép | `@academic_required` (`assessments.py`, `grades.py`) |
| **16** | **Lập đề xuất cấp chứng chỉ** | Được phép | **Được phép (Có ĐK)** | Không được phép | `@academic_required` (`certificates.py`) |
| **17** | **Duyệt & Ký số phát hành Blockchain** | **Được phép** | Không được phép | Không được phép | `@admin_required` (`certificates.py`) |
| **18** | **Quản lý phiếu học phí & công nợ** | Được phép | Không được phép | **Được phép** | `@finance_required` (`tuition.py`) |
| **19** | **Lập phiếu thu tiền học phí** | Được phép | Không được phép | **Được phép** | `@finance_required` (`tuition.py`) |
| **20** | **In biên lai thu tiền học phí** | Được phép | Không được phép | **Được phép** | `@finance_required` (`tuition.py`) |
| **21** | **Xuất báo cáo tài chính ra Excel** | Được phép | Không được phép | **Được phép** | `@finance_required` (`tuition.py`) |
| **22** | **Xác minh chứng chỉ công khai** | Được phép | Được phép | Được phép | Không yêu cầu đăng nhập (`certificates.py`) |

*Ghi chú:*  
- **Admin** có cơ chế kế thừa toàn quyền (`user.is_superuser or user.groups.filter(name=ROLE_ADMIN).exists()` luôn trả về `True` trong hàm `has_role()`).
- **Có ĐK (Có điều kiện):** Nhân viên đào tạo chỉ được phép tạo đề xuất ở trạng thái `pending`, không được phép tự ý chọn ký số Blockchain; đồng thời học viên phải thỏa mãn không nợ học phí và điểm sàn $\ge 5.0$.

---

## PHẦN V. TỔNG HỢP QUY TẮC NGHIỆP VỤ (BUSINESS RULES)

1. **Quy tắc Xác thực & Phân quyền:**
   - **BR-SEC-01:** Mật khẩu người dùng phải đạt độ dài tối thiểu 6 ký tự và được mã hóa một chiều qua hàm băm an toàn PBKDF2.
   - **BR-SEC-02:** Người dùng không có quyền truy cập vào URL bị chặn sẽ bị trả về mã lỗi HTTP 403 Forbidden ngay tại tầng View Middleware.
   - **BR-SEC-03:** Không cho phép tài khoản tự khóa hoặc tự xóa chính mình để đảm bảo tính sẵn sàng quản trị.

2. **Quy tắc Đào tạo & Ghi danh:**
   - **BR-ACA-01 (Giới hạn sĩ số):** Khi ghi danh học viên vào lớp, hệ thống kiểm tra số lượng học viên hiện tại (`enrollment_count`). Nếu đã đạt hoặc vượt quá sĩ số tối đa (`max_students`), hệ thống từ chối ghi danh thêm.
   - **BR-ACA-02 (Tự động khởi tạo học phí):** Khi một học viên được ghi danh thành công vào lớp học, hệ thống tự động sinh một bản ghi học phí (`Tuition`) với số tiền `total_fee` bằng đúng mức học phí tiêu chuẩn của khóa học tương ứng.
   - **BR-ACA-03 (Chuyển lớp khác khóa):** Nếu học viên chuyển lớp giữa hai lớp thuộc cùng một khóa học, Học vụ có thể xử lý; nếu chuyển sang lớp thuộc khóa học khác (học phí khác nhau), bắt buộc phải có Quản trị viên (Admin) phê duyệt.

3. **Quy tắc Khảo thí & Điểm số:**
   - **BR-GRD-01 (Thang điểm hợp lệ):** Điểm số nhập vào hệ thống bắt buộc là số thực nằm trong đoạn từ $0.00$ đến $10.00$.
   - **BR-GRD-02 (Tổng trọng số 100%):** Các đầu điểm thành phần trong Quy chế đánh giá phải có tổng trọng số bằng đúng 100%.
   - **BR-GRD-03 (Quy tắc xếp loại tốt nghiệp):**
     - Điểm $\ge 9.0$: Xuất sắc.
     - Điểm $\ge 8.0$ và $< 9.0$: Giỏi.
     - Điểm $\ge 6.5$ và $< 8.0$: Khá.
     - Điểm $\ge 5.0$ và $< 6.5$: Trung bình.
     - Điểm $< 5.0$: Chưa đạt (Không đủ chuẩn đầu ra).

4. **Quy tắc Tài chính & Học phí:**
   - **BR-FIN-01 (Giới hạn số tiền thanh toán):** Số tiền thanh toán trong mỗi phiếu thu phải lớn hơn 0 và không được vượt quá số tiền dư nợ còn lại (`debt = total_fee - paid_amount`).
   - **BR-FIN-02 (Cập nhật trạng thái tự động):**
     - Nếu `paid_amount == 0`: Trạng thái "Chưa thanh toán".
     - Nếu `paid_amount < total_fee`: Trạng thái "Còn nợ" (Thanh toán một phần).
     - Nếu `paid_amount >= total_fee`: Trạng thái "Đã hoàn tất".

5. **Quy tắc Kiểm duyệt Cấp chứng chỉ & Blockchain (Gatekeeper & 2-Step Approval):**
   - **BR-CRT-01 (Điều kiện tài chính):** Học viên bắt buộc phải hoàn tất 100% học phí (`paid_amount >= total_fee`). Nếu còn nợ dù chỉ 1 đồng, hệ thống chặn lập đề xuất và từ chối cấp chứng chỉ.
   - **BR-CRT-02 (Điều kiện học lực):** Điểm tốt nghiệp của học viên phải đạt chuẩn sàn tối thiểu từ $5.00$ trở lên. Học viên bị xếp loại "Chưa đạt" không được phép cấp chứng chỉ.
   - **BR-CRT-03 (Phê duyệt 2 bước):** Nhân viên Đào tạo chỉ có quyền lập đề xuất (`blockchain_status='pending'`). Chỉ có Quản trị viên (Admin) mới có quyền bấm "Duyệt & Ký số" để băm Keccak-256 và gửi giao dịch lên Smart Contract.
   - **BR-CRT-04 (Tính toàn vẹn xác minh):** Dữ liệu xác minh được tính lại từ CSDL MySQL và so sánh với mã băm lưu trữ trên Blockchain. Nếu hai mã băm trùng khớp 100%, chứng chỉ được xác nhận Toàn vẹn; nếu có sự sai lệch dù chỉ 1 ký tự, hệ thống cảnh báo Giả mạo.

---

## PHẦN VI. TỔNG HỢP CÁC TRƯỜNG HỢP NGOẠI LỆ (EXCEPTIONS & EDGE CASES)

1. **Ngoại lệ về Xác thực & Tài khoản:**
   - Người dùng nhập sai mật khẩu quá số lần quy định (hiện tại Django mặc định chưa khóa cứng IP, chỉ hiển thị thông báo lỗi chung).
   - Người dùng truy cập trực tiếp bằng URL khi chưa đăng nhập $\rightarrow$ Chuyển hướng 302 về `/accounts/login/?next=...`.
   - Nhân viên bị Admin khóa tài khoản khi đang giữ phiên làm việc $\rightarrow$ Ở request tiếp theo, middleware kiểm tra `is_active=False` và tự động đăng xuất người dùng.
2. **Ngoại lệ về Lớp học & Đào tạo:**
   - Lớp học đã đủ sĩ số tối đa nhưng cố tình ghi danh $\rightarrow$ Backend chặn và cảnh báo lỗi vượt sĩ số.
   - Học viên chưa hoàn thành khóa học nhưng cố tình làm thủ tục chuyển lớp $\rightarrow$ Hệ thống cảnh báo tình trạng học tập.
3. **Ngoại lệ về Điểm số & Chuyên cần:**
   - Điểm số nhập vào là ký tự chữ hoặc số âm/lớn hơn 10 $\rightarrow$ Form validation bắt lỗi ngay tại client và backend bắt ngoại lệ `ValueError`.
   - Điểm danh trùng lặp 2 lần cho cùng một học viên trong cùng một buổi học $\rightarrow$ Sử dụng cơ chế `update_or_create()` để cập nhật trạng thái mới nhất thay vì sinh ra bản ghi rác.
4. **Ngoại lệ về Học phí & Thu tiền:**
   - Kế toán nhập số tiền thanh toán lớn hơn số nợ thực tế $\rightarrow$ Backend kiểm tra và từ chối giao dịch: *"Số tiền thanh toán vượt quá số nợ còn lại"*.
   - Học viên không có bản ghi học phí nhưng mở trang lập phiếu thu $\rightarrow$ Hệ thống báo lỗi không tìm thấy đối tượng (`Http404`).
5. **Ngoại lệ về Blockchain & Smart Contract:**
   - **Mạng Ganache bị tắt hoặc mất kết nối RPC (`http://127.0.0.1:7545`):**
     - View bắt ngoại lệ `ConnectionError` / `Exception`.
     - Hệ thống **không làm gián đoạn ứng dụng Web**, vẫn lưu trữ chứng chỉ ở trạng thái Database bình thường và cảnh báo Admin: *"Chưa ghi nhận được lên Blockchain do mạng ngoại tuyến, vui lòng kiểm tra node Ganache"*.
   - **Ví Owner trong Ganache không đủ số dư Gas:** Hệ thống bắt lỗi `RuntimeError` và hiển thị thông báo lỗi chi tiết cho Quản trị viên.
   - **Chứng chỉ đã được cấp trên Blockchain nhưng bấm ký lại lần 2:** Hệ thống kiểm tra `certificate.blockchain_status == 'issued'` và chặn lại: *"Chứng chỉ này đã được cấp trên Blockchain"*.

---

## PHẦN VII. NHỮNG THÔNG TIN CÒN THIẾU & CÁC CÂU HỎI CẦN XÁC NHẬN TỪ BẠN

Sau khi rà soát toàn bộ source code và cơ sở dữ liệu, tôi phát hiện một số điểm cần trao đổi để đảm bảo bảng đặc tả Use Case chi tiết sau này hoàn toàn khớp với kỳ vọng thực tế của bạn:

### 1. Vấn đề về Cổng người dùng của Giảng viên và Học viên:
- **Hiện trạng trong code:** Hiện tại hệ thống chỉ có tài khoản đăng nhập nội bộ cho **Admin**, **Học vụ (Đào tạo)** và **Tài chính (Kế toán)**. Bảng `Student` và `Teacher` chỉ là các bảng lưu hồ sơ nghiệp vụ, **chưa được liên kết khóa ngoại với bảng tài khoản `auth_user`**.
- **Câu hỏi xác nhận 1:** Trong đồ án tốt nghiệp, bạn có dự định mở rộng thêm cổng đăng nhập riêng (Portal) cho Giáo viên (để tự điểm danh/nhập điểm) và Học viên (để xem điểm/thời khóa biểu) không, hay giữ nguyên phạm vi hiện tại là hệ thống quản trị nội bộ tập trung cho 3 vai trò (Admin, Đào tạo, Kế toán)?

### 2. Vấn đề về Cơ chế Đăng ký tài khoản (Sign up):
- **Hiện trạng trong code:** Hệ thống là phần mềm quản trị doanh nghiệp khép kín, **không có trang "Đăng ký" (Register) công khai ngoài màn hình login**. Toàn bộ tài khoản nhân sự mới đều do Quản trị viên (Admin) tạo thủ công trong trang `/system/users/`.
- **Câu hỏi xác nhận 2:** Trong bảng đặc tả Use Case, chức năng tạo tài khoản sẽ được đặc tả chính thức là **Use Case "Quản lý tài khoản người dùng" (do Admin thực hiện)**, không có Use Case "Tự đăng ký tài khoản", điều này có đúng với mong muốn của bạn không?

### 3. Vấn đề về Quên mật khẩu & Gửi Email:
- **Hiện trạng trong code:** Tại màn hình đăng nhập chỉ có ô Tên đăng nhập và Mật khẩu, chưa có nút "Quên mật khẩu" hay "Đăng nhập bằng Google/Facebook". Mật khẩu của nhân viên khi quên sẽ do **Admin đặt lại trực tiếp trong trang quản lý tài khoản**.
- **Câu hỏi xác nhận 3:** Bạn có muốn giữ nguyên quy trình chuẩn nội bộ này (Admin hỗ trợ reset mật khẩu) để viết vào đặc tả, hay cần bổ sung thêm Use Case "Quên mật khẩu qua Email"?

### 4. Vấn đề về Thu hồi / Hủy chứng chỉ Blockchain (Revoke Certificate):
- **Hiện trạng trong code:** Smart contract hiện chỉ có 2 hàm: `issueCertificate` (Ghi chứng chỉ) và `verifyCertificate` / `getCertificate` (Xác minh chứng chỉ). Một khi đã ký số lên Blockchain thì bản ghi mang tính bất biến tuyệt đối, chưa có hàm thu hồi (`revoke`).
- **Câu hỏi xác nhận 4:** Khi viết đặc tả quy trình cấp chứng chỉ, bạn muốn mô tả tính năng này theo cơ chế **Bất biến vĩnh viễn (Immutability)**, hay cần thiết kế thêm Use Case "Thu hồi chứng chỉ" (Revocation)?

---

*(Tài liệu này được tạo tự động bởi System Analyst và lưu trữ trực tiếp tại file: `D:\DoAn4\APP-Trung-Tam-Tieng-Anh\SYSTEM_ANALYSIS_FOR_USE_CASE_SPECIFICATION.md`)*

