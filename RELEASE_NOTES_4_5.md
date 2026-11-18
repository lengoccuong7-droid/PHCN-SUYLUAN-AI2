# PHCN AI 4.5.0 – Clinical Reasoning Upgrade

## Thay đổi chính
- Sửa trích xuất phủ định có phạm vi theo danh sách, không tự biến các cụm "không tràn dịch, khóa khớp, mất vững hoặc tê" thành bằng chứng dương tính.
- Không mở rộng từ đồng nghĩa bằng cách nối thêm từ vào văn bản gốc trước khi xét phủ định; cách cũ có thể làm mất quan hệ phủ định.
- Thu hẹp đặc trưng cảm giác: "nóng rát" đơn độc không còn tự động bị coi là dị cảm.
- Tách valgus động trong squat khỏi cơ chế chấn thương valgus.
- Thu hẹp nhận diện đau dây chằng bên ngoài gối; đau lồi cầu ngoài không tự động đồng nghĩa đau LCL.
- Bổ sung đặc trưng vai: AROM/PROM cùng hạn chế, hạn chế đa hướng, xoay ngoài giảm rõ và tiền sử đái tháo đường.
- Bổ sung giả thuyết ITBS: vị trí đau vùng lồi cầu ngoài, đau khi chạy xuống dốc/tải chạy, đau quanh 30 độ gấp gối và Noble Compression dương tính. Ober không được xem là bằng chứng xác nhận độc lập.
- Sửa phân loại thời gian: 4 tháng được xếp mạn tính; 2 tuần được xếp bán cấp.
- Không báo mâu thuẫn chỉ vì có đau khi hoạt động nhưng không đau trong một bối cảnh khác.
- Cập nhật thông báo an toàn trên giao diện: công cụ hỗ trợ quyết định, không thay thế bác sĩ.

## Kiểm thử
- Bộ kiểm thử tự động: 42/42 passed.
- Kiểm thử hồi quy bao gồm ca đau thắt lưng, ca vai đông cứng giả định và ca ITBS giả định.
- Thêm kiểm thử phủ định theo danh sách và phân biệt valgus động với cơ chế chấn thương.

## Giới hạn còn lại
- Chưa thực hiện kiểm thử giao diện Streamlit trực tiếp trong môi trường build vì Streamlit chưa được cài đặt tại môi trường này.
- Bộ quy tắc chưa bao phủ toàn bộ bệnh lý của mọi vùng cơ thể; trường hợp ngoài phạm vi luật cần được trả về trạng thái chưa đủ dữ liệu, không suy diễn chẩn đoán.
- Điểm thuật toán không phải xác suất mắc bệnh và chưa được hiệu chuẩn trên quần thể bệnh nhân độc lập.
- Chưa có thẩm định lâm sàng độc lập hoặc chứng nhận thiết bị y tế. Không dùng kết quả làm chẩn đoán xác định hay thay thế bác sĩ.
- Giữ nguyên cơ sở dữ liệu SQLite, kho tri thức và thư viện bài tập từ bản 4.4.
