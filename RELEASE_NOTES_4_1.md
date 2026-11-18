# PHCN AI 4.1.0 – Release Notes

## Nâng cấp chính
1. Thêm parser bệnh sử tự do tiếng Việt chạy offline.
2. Trích xuất triệu chứng và trạng thái phủ định; vị trí giải phẫu; bên; diễn tiến; thời lượng; yếu tố tăng/giảm; quan hệ được người bệnh mô tả.
3. Bổ sung kiểm tra một số mâu thuẫn và dấu hiệu an toàn.
4. Tích hợp kết quả vào `analyze_case()` và `render_report()`.
5. Thêm hiển thị kết quả NLP trong tab Khám lâm sàng.
6. Mở rộng suy luận tổng quát để đọc cả trường `free_text`.

## Bảo toàn
- Giữ nguyên dữ liệu tri thức, kho bài tập, SQLite schema và 8 tab từ baseline 4.0.
- Không thêm dịch vụ AI/API bên ngoài hoặc tự gửi dữ liệu bệnh nhân.

## Kiểm thử
- `python -m compileall -q .`: đạt.
- `PYTHONPATH=. pytest -q`: 24 passed.
- Chưa xác minh khởi chạy giao diện Streamlit thực tế trong môi trường build; cần chạy thử trên máy triển khai và điện thoại.

## Giới hạn
Parser là NLP quy tắc, không phải hiểu ngôn ngữ tự do tổng quát. Mọi kết luận lâm sàng phải được người có chuyên môn xác minh.
