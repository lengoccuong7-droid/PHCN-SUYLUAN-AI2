# PHCN AI 4.0.0 – Release notes

## Nguồn tích hợp
- Deepseek.zip do người dùng cung cấp: ứng dụng 6 khu vực, dữ liệu bài tập, tri thức, database, bộ suy luận và đối soát.
- PHCN AI 3.0-dev2: `reasoning_engine.py`, `clinical_engine.py`, regression cases và build notes được khôi phục từ Library.
- Lưu ý nguồn: build notes 3.0-dev2 ghi rõ baseline đầy đủ gần nhất có thể khôi phục trước đó là 2.4.3; không có archive 2.5.0/3.0-dev2 đầy đủ. Vì vậy đây là tích hợp trên Deepseek.zip, không tuyên bố tái tạo toàn bộ source tree 3.0-dev2.

## Thay đổi
- Chuẩn hóa phần mở rộng file `.py.txt`, `.json.txt`, `.toml.txt`.
- Tích hợp general reasoning của dev2 vào kết quả phân tích Deepseek.
- Sửa sigmoid 0.50 khi không có bằng chứng: giả thuyết không có bằng chứng ủng hộ không còn tự động đạt ngưỡng hiển thị.
- Bổ sung alias ACL/MCL/Achilles/deep gluteal và trạng thái SLR âm tính.
- Bổ sung đánh giá ROM/sức cơ ghi nhận và dữ liệu cần làm rõ.
- Bổ sung module semantic learner statistics bị thiếu.
- Phản hồi không tự động cập nhật trọng số; tạo đề xuất chờ duyệt.
- Thêm khu vực Kế hoạch PHCN và Hệ thống/Sao lưu.
- Thêm PWA ghi nhận offline trên điện thoại bằng IndexedDB và nhập JSON chống trùng vào SQLite.
- Thêm mật khẩu tùy chọn qua `PHCN_APP_PASSWORD`.

## Kết quả kiểm thử trong môi trường build
- `python -m compileall -q .`: đạt.
- `PYTHONPATH=. python -m pytest -q`: 19 passed.
- Streamlit UI smoke test: chưa chạy được trong môi trường build do không có package Streamlit và không thể tải package từ Internet.
- Truy cập từ điện thoại qua Internet công cộng: cần triển khai lên máy chủ HTTPS riêng; không thể hoàn tất chỉ bằng ZIP.
