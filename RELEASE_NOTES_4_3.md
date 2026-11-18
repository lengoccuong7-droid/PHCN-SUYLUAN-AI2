# PHCN AI 4.3.0 – Advanced Clinical Reasoning & Iterative Re-analysis

## Kế thừa
- Dùng PHCN AI 4.2.0 làm baseline.
- Giữ các module hồ sơ, tri thức, khám, bài tập, đối soát, theo dõi, kế hoạch và sao lưu.
- Không thay đổi schema lưu hồ sơ hiện có.

## Nâng cấp trong 4.3
1. Bổ sung ô nhập tự do thông tin khám/bệnh sử còn thiếu ngay dưới kết quả phân tích.
2. Nút “Phân tích lại với thông tin bổ sung” chạy lại toàn bộ engine trên dữ liệu gốc cộng toàn bộ thông tin bổ sung.
3. Giữ các vòng phân tích trong phiên làm việc; hiển thị lịch sử và so sánh giả thuyết ưu tiên giữa hai vòng gần nhất.
4. Parser NLP tiếp nhận trường supplemental_text, do đó dữ liệu mới tham gia trích xuất triệu chứng, vị trí, diễn tiến và quan hệ mô tả.
5. Báo cáo có số vòng phân tích, nội dung bổ sung và tuyên bố rõ vai trò quyết định cuối cùng của bác sĩ.
6. Cập nhật nhận diện phiên bản giao diện và sửa caption bị lặp ở 4.2.

## Giới hạn quan trọng
- Đây vẫn là suy luận offline dựa trên luật, từ vựng và trọng số; không phải mô hình AI chuyên khoa đã được thẩm định.
- Phân tích lại là chạy lại engine trên dữ liệu đã nhập, không tự thực hiện khám, không đọc ảnh MRI/X-quang để kết luận và không xác nhận chẩn đoán thay bác sĩ.
- Thông tin bổ sung được lưu vào payload khi người dùng lưu lần khám. Lịch sử các vòng phân tích trong giao diện hiện được giữ trong phiên Streamlit; muốn lưu bền vững từng vòng riêng biệt cần bổ sung bảng lịch sử phiên phân tích ở một bản tiếp theo.
- Điểm heuristic không phải xác suất bệnh. Cần đánh giá cờ đỏ và khám trực tiếp; bác sĩ quyết định chấp nhận, điều chỉnh hoặc bác bỏ.

## Kiểm thử
- Kiểm tra cú pháp Python toàn bộ mã nguồn.
- Chạy bộ pytest hiện có nếu môi trường cài đủ phụ thuộc.
- Kiểm tra ZIP integrity bằng testzip.
- Đây không phải kiểm định lâm sàng hoặc chứng nhận an toàn y tế.
