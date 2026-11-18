# PHCN AI 4.5.0 – Trợ lý suy luận lâm sàng PHCN offline-first

## Chức năng
- Quản lý hồ sơ bệnh nhân và lịch sử lần khám bằng SQLite.
- Nhập bệnh sử tự do và thông tin khám có cấu trúc.
- NLP tiếng Việt dựa trên quy tắc để nhận diện triệu chứng, vị trí, bên triệu chứng, diễn tiến cấp trên nền mạn, yếu tố tăng/giảm và một số dấu hiệu thần kinh.
- Chuẩn hóa trạng thái nghiệm pháp (dương tính/âm tính/chưa thực hiện), tránh nhầm tên nghiệm pháp có hậu tố Test.
- Đối soát một số dữ kiện quan trọng như EHL 4/5, phản xạ gân gót giảm và tính nhất quán của dữ liệu đầu vào.
- Suy luận giả thuyết, bằng chứng ủng hộ/chống lại, dữ liệu còn thiếu, cảnh báo và tổng hợp chẩn đoán sơ bộ.
- 4.5 bổ sung nhận diện hạn chế AROM/PROM đa hướng và xoay ngoài ở vai; tiền sử đái tháo đường là yếu tố điều chỉnh; bổ sung quy tắc ITBS dựa trên vị trí đau, tải chạy xuống dốc, góc gấp gối và Noble Compression.
- 4.5 cải thiện phạm vi phủ định theo cụm liệt kê, tránh biến "không khóa khớp/không mất vững/không tê" thành triệu chứng dương tính; tách valgus động khi squat khỏi cơ chế chấn thương valgus.
- Bổ sung thông tin tự do sau phân tích và chạy phân tích lại nhiều vòng mà không nhập lại hồ sơ.
- Tra cứu tri thức, nghiệm pháp, kho bài tập, theo dõi, kế hoạch PHCN và sao lưu.
- Không gọi API AI bên ngoài.

## Cài đặt trên Windows
1. Cài Python 3.10 hoặc mới hơn.
2. Giải nén ZIP.
3. Mở Command Prompt tại thư mục dự án.
4. Tạo môi trường: `python -m venv .venv`
5. Kích hoạt: `.venv\Scripts\activate`
6. Cài thư viện: `pip install -r requirements.txt`
7. Chạy: `streamlit run app.py`
8. Mở địa chỉ Streamlit hiển thị trong terminal.

## macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Dùng trên điện thoại
Có thể mở giao diện qua URL của máy chủ Streamlit nếu điện thoại truy cập được máy chủ qua mạng/Internet. PWA hỗ trợ một phần lưu nội dung ngoại tuyến; engine Streamlit và SQLite vẫn chạy trên máy chủ. Vì vậy, không được hiểu là ứng dụng có thể suy luận hoàn toàn khi iPhone mất kết nối tới máy chủ.

## Bảo mật
- Dữ liệu SQLite nằm trong `data/phcn_ai.db`. Sao lưu định kỳ bằng chức năng trong ứng dụng hoặc sao chép an toàn tệp DB khi ứng dụng đã dừng.
- Không triển khai máy chủ công khai nếu chưa cấu hình mật khẩu, HTTPS và kiểm soát truy cập.
- Chỉ dùng dữ liệu đã được phép xử lý; hạn chế thông tin định danh không cần thiết.

## Vai trò lâm sàng và giới hạn
Đây là công cụ hỗ trợ quyết định, không thay thế bác sĩ. Bộ suy luận hiện tại là hệ thống luật/NLP offline, không phải mô hình hiểu ngôn ngữ tổng quát hoặc AI chuyên khoa đã được thẩm định. Điểm thuật toán không phải xác suất mắc bệnh. Bác sĩ trực tiếp khám là người quyết định cuối cùng.

## Phiên bản
Xem `VERSION`, `RELEASE_NOTES_4_3.md`, `RELEASE_NOTES_4_4.md` và `RELEASE_NOTES_4_5.md`.
