# PHCN AI 4.2.0 – Diagnosis Synthesis Upgrade

## Mục tiêu
Bổ sung tầng tổng hợp chẩn đoán sơ bộ có giải thích sau các bộ máy NLP và suy luận hiện hữu. Đây là hệ thống hỗ trợ quyết định, không phải công cụ chẩn đoán xác định.

## Nâng cấp
- Thêm `core/diagnosis_synthesis.py` để chọn giả thuyết ưu tiên từ các giả thuyết đã được bộ suy luận hiện tại tạo ra.
- Tạo danh sách chẩn đoán phân biệt, bằng chứng ủng hộ, bằng chứng chống lại/mâu thuẫn, dữ kiện còn thiếu, cảnh báo an toàn và giới hạn.
- Báo cáo lâm sàng có mục **Tổng hợp chẩn đoán sơ bộ**.
- Nhận diện bí danh tên nghiệm pháp Lasègue, SLR/Straight Leg Raise và Bragard theo mã đặc trưng mà bộ luật đang sử dụng.
- Đưa `free_text` vào feature extractor để văn bản tự do thực sự tham gia suy luận, không chỉ parser NLP.
- Giảm cộng điểm trùng lặp giữa Lasègue, SLR và Bragard: vẫn hiển thị từng kết quả nhưng đóng góp điểm theo cụm nghiệm pháp liên quan.
- Phân biệt cụm “đau bùng phát” với vị trí giải phẫu “bụng”.
- Giảm báo mâu thuẫn giả khi một triệu chứng được mô tả ở hai vùng giải phẫu khác nhau.
- Giữ nguyên toàn bộ bộ hồ sơ, cơ sở dữ liệu, 8 tab, thư viện bài tập và PWA offline capture từ bản 4.1.

## Thay đổi
- Tên phiên bản giao diện và báo cáo chuyển từ 4.1 sang 4.2.
- Điểm định hướng ở các ca có nhiều nghiệm pháp căng thần kinh dương tính có thể thấp hơn trước vì không cộng dồn các phép thử tương quan như bằng chứng độc lập.
- Báo cáo có thêm phần tổng hợp chẩn đoán ưu tiên và chẩn đoán phân biệt.

## Giữ nguyên
- Streamlit, SQLite và cấu trúc 8 tab.
- Kho tri thức lâm sàng, thư viện bài tập và dữ liệu hiện có.
- Không gọi API AI bên ngoài; không yêu cầu API key.
- Kiến trúc offline-first hiện hữu. Lưu ý: PWA offline capture vẫn chỉ hỗ trợ ghi nhận ngoại tuyến; các trang Streamlit và suy luận chính vẫn cần máy chủ đang hoạt động.

## Kiểm thử
- `python -m compileall -q .`
- `PYTHONPATH=. pytest -q`
- Bộ kiểm thử gồm các ca hồi quy hiện hữu và kiểm thử mới cho tổng hợp chẩn đoán, bí danh nghiệm pháp và phân biệt “bùng phát”.

## Giới hạn đã biết
- Bộ máy vẫn là NLP và suy luận quy tắc/heuristic offline; chưa phải mô hình ngôn ngữ lớn chạy cục bộ và không thể hiểu mọi bệnh sử mới như bác sĩ.
- Chẩn đoán ưu tiên là giả thuyết cần kiểm chứng. Điểm thuật toán không phải xác suất mắc bệnh.
- Cần kiểm thử lâm sàng độc lập, đa vùng cơ thể và trên dữ liệu chưa dùng phát triển trước khi triển khai thực tế.
