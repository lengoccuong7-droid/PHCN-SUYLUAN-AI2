# PHCN AI 4.5.0 – Báo cáo xác minh bản build

## Phạm vi
Bản 4.5 phát triển trên mã nguồn 4.4, giữ nguyên cấu trúc 8 phân hệ, SQLite, kho tri thức JSON, thư viện bài tập, PWA ghi nhận offline và cơ chế không gọi API AI bên ngoài.

## Kết quả kiểm tra
- `python -m compileall -q core database modules tests`: đạt.
- `PYTHONPATH=. pytest -q`: 42/42 kiểm thử đạt.
- 5 tệp JSON trong thư mục `knowledge/`: đọc và phân tích cú pháp hợp lệ.
- Cơ sở dữ liệu SQLite: mở được; các bảng `learned_weights`, `learning_proposals`, `feedback_log` đang không có bản ghi.
- Hồi quy ca vai: giả thuyết viêm dính bao khớp vai đứng đầu khi dữ liệu có hạn chế AROM/PROM đa hướng và xoay ngoài rõ.
- Hồi quy ca gối: giả thuyết ITBS đứng đầu với vị trí đau phù hợp, chạy xuống dốc, đau quanh 30° và Noble dương tính.
- Kiểm tra phủ định: không trích xuất nhầm mất vững, khóa khớp, tê hoặc cơ chế chấn thương valgus từ câu phủ định; valgus động trong squat không bị coi là cơ chế chấn thương.
- Kiểm tra ZIP: sẽ được xác minh sau khi đóng gói.

## Giới hạn xác minh
- Không thể chạy kiểm thử giao diện Streamlit trực tiếp trong môi trường build này vì chưa cài Streamlit. Các module được kiểm tra wiring bằng test import stub; cần cài requirements và chạy thực tế trên máy triển khai.
- Không có thẩm định độc lập của bác sĩ chuyên khoa hoặc đánh giá trên tập dữ liệu bệnh nhân đại diện.
- 42 kiểm thử phần mềm không chứng minh độ chính xác lâm sàng. Bộ quy tắc chỉ bao phủ các nhóm bệnh/kiểu hình đã được mã hóa.
- Điểm định hướng thuật toán không phải xác suất mắc bệnh, không được dùng làm chẩn đoán xác định hoặc thay thế bác sĩ.
- PWA chỉ hỗ trợ ghi nhận một phần khi offline; engine Streamlit và SQLite vẫn cần máy chủ hoạt động và điện thoại kết nối được tới máy chủ.

## Bảo mật
Database đóng gói hiện chỉ có ba bảng kỹ thuật và không có bản ghi. Không đưa hồ sơ bệnh nhân thật vào bộ kiểm thử.
