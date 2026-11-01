# Thiết kế ghi danh học viên vào lớp

## Quy tắc đã chốt

- Trạng thái thuộc về một lần ghi danh vào một lớp, không đặt trực tiếp trên hồ sơ học viên.
- Bốn trạng thái: `studying` (Đang học), `transferred` (Đã chuyển lớp), `stopped` (Đã dừng), `completed` (Hoàn thành).
- `completed` nghĩa là học viên đã học hết khóa.
- Chuyển lớp tạo/kích hoạt ghi danh ở lớp mới; ghi danh lớp cũ được giữ lại với trạng thái `transferred`.
- Thao tác chuyển lớp kiểm tra lớp đích khác lớp hiện tại, chưa đủ sĩ số và học viên chưa hoàn thành lớp đích; cập nhật hai ghi danh trong cùng transaction. Trạng thái `transferred` chỉ được đặt qua thao tác chuyển lớp.
- Mỗi cặp học viên/lớp hiện chỉ có một bản ghi ghi danh. Nếu ghi danh lại cùng lớp, bản ghi đó được kích hoạt lại; hệ thống chưa lưu nhật ký từng lần đổi trạng thái.

## Cài đặt trong dự án

- `Enrollment` là model trung gian của `EnglishClass.students`.
- Migration `0008_enrollment` sao chép quan hệ nhiều-nhiều cũ sang ghi danh mới với trạng thái `studying`; ngày ghi danh cũ được ước tính bằng ngày bắt đầu lớp vì dữ liệu cũ không có ngày ghi danh. Migration `0009` thay `paused` cũ bằng `stopped` và thêm trạng thái `transferred`.
- Sĩ số chỉ tính ghi danh `studying`; tạm dừng/đã dừng/hoàn thành không chiếm chỗ.
- Cập nhật trạng thái ghi danh bằng POST; khi dừng, chuyển lớp hoặc hoàn thành, lưu ngày kết thúc. Khi chuyển về đang học, xóa ngày kết thúc.
- Trang chi tiết lớp có thao tác chuyển học viên sang lớp khác còn chỗ; ghi chú hai phía chỉ ra lớp chuyển đi/chuyển đến.

## Giới hạn hiện tại

- Chưa có lịch sử sự kiện trạng thái, người thao tác hoặc lý do bắt buộc.
- Chưa tự đánh dấu hoàn thành theo ngày kết thúc; người dùng có quyền cần xác nhận học viên đã học hết khóa rồi mới chọn trạng thái này.
- Chưa có quy tắc tự động chuyển học viên sang lớp mới.
