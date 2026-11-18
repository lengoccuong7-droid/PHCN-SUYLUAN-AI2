> Tài liệu lịch sử của bản 4.4; không dùng làm báo cáo kiểm thử cho bản 4.5. Xem BUILD_REPORT_4_5.md.

# PHCN AI 4.4.0 – Báo cáo kiểm tra bản build

## Đã thực hiện
- Giữ nguyên cấu trúc 8 tab và các module quản lý hồ sơ, cẩm nang, khám lâm sàng, bài tập, đối soát, theo dõi, kế hoạch và sao lưu.
- Giữ nguyên tệp SQLite có trong gói nguồn; không xóa hoặc tạo lại cơ sở dữ liệu.
- Sửa các lỗi đã xác định trong 4.3 về nhận diện từ, bên triệu chứng, diễn tiến cấp trên nền mạn, nghiệm pháp, dấu hiệu thần kinh, quan hệ NLP trùng và thông tin phiên bản/sao lưu.
- Bổ sung đối soát tự động một số dữ kiện quan trọng và bộ kiểm thử hồi quy ca thắt lưng.

## Kết quả kiểm tra
- Pytest: 38 passed.
- Python compileall: thành công.
- 5 tệp JSON tri thức: đọc/parse hợp lệ.
- Báo cáo lâm sàng cho ca kiểm thử: tạo thành công; hội chứng đau kiểu rễ thần kinh được ưu tiên hơn đau thắt lưng cơ học không đặc hiệu; không phát sinh giả thuyết hội chứng đuôi ngựa chỉ từ yếu một chân.
- Tính toàn vẹn ZIP: sẽ được xác minh sau khi đóng gói.

## Giới hạn chưa thể xác nhận trong môi trường build
- Streamlit không được cài trong môi trường build; chưa chạy giao diện tương tác trực tiếp trên trình duyệt/điện thoại.
- Không có xác nhận thẩm định lâm sàng độc lập cho bộ luật hoặc thư viện bài tập.
- Không có phân tích ảnh MRI/X-quang tự động.
- Chất lượng suy luận vẫn phụ thuộc vào từ vựng/quy tắc; cách diễn đạt mới có thể không được nhận diện.

## Hướng dẫn sử dụng an toàn
- Đây là công cụ hỗ trợ quyết định lâm sàng, không thay thế khám trực tiếp.
- Điểm định hướng là điểm heuristic, không phải xác suất mắc bệnh.
- Dấu hiệu yếu cơ mới xuất hiện/tiến triển cần được đánh giá y khoa trực tiếp sớm.
- Khi triển khai qua Internet, cần HTTPS, xác thực và kiểm soát truy cập; không dùng dữ liệu định danh thật trong bộ kiểm thử.
