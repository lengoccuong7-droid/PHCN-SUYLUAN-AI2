# PHCN AI 4.4.0 – Clinical Consistency & Neurological Reasoning Update

## Mục tiêu
Sửa lỗi trích xuất dữ kiện, chuẩn hóa nghiệm pháp, phân biệt diễn tiến cấp trên nền mạn, cải thiện nhận diện dấu hiệu thần kinh và an toàn báo cáo.

## Thay đổi
- Sửa so khớp từ khóa theo ranh giới từ để tránh nhận nhầm `ngã` trong `ngay`.
- Bổ sung nhận diện cơ chế cúi/nâng/bê vật nặng và đau tăng khi ho/hắt hơi.
- Chuẩn hóa alias Lasègue/SLR/Bragard kể cả tên có hậu tố `Test`.
- Bổ sung nhận diện yếu cơ EHL và phản xạ gân gót giảm từ ghi chú khám.
- Phân biệt đợt cấp trên nền đau mạn khi có bằng chứng thời lượng cấp và mạn.
- Không dùng bên đối chiếu trong phần sức cơ/phản xạ để kết luận bệnh nhân có triệu chứng hai bên.
- Loại bỏ các quan hệ sự kiện trùng lặp trong báo cáo NLP.
- Bổ sung yếu tố tăng đau khi cúi, ho, hắt hơi và giảm khi nằm/kê gối.
- Tab Hệ thống đọc phiên bản từ `VERSION`; tên file sao lưu đồng bộ phiên bản.
- Giao diện ghi rõ ảnh tải lên chưa được phân tích tự động; cờ đỏ không được tích hiển thị là chưa ghi nhận, không phải loại trừ.

## Giới hạn còn phải công khai
- NLP và suy luận vẫn là hệ thống luật offline, không phải mô hình ngôn ngữ y khoa đã được thẩm định.
- Định khu rễ L5/S1 chỉ là định hướng cần đối chiếu khám thần kinh; không tự suy ra tầng đĩa đệm.
- Điểm thuật toán không phải xác suất bệnh.
- Ảnh MRI/X-quang chưa được phân tích tự động.
- Cần bác sĩ chuyên khoa rà soát bộ quy tắc và thư viện bài tập trước khi triển khai lâm sàng.

## Kiểm thử hồi quy
- Bổ sung ca kiểm thử thắt lưng có đợt cấp trên nền mạn, đau lan một bên, EHL 4/5, phản xạ gân gót giảm và các nghiệm pháp căng thần kinh dương tính.
- Bộ kiểm thử tự động trong gói: 38 kiểm thử; đã chạy thành công trong môi trường build.
- Đã kiểm tra cú pháp Python và tính hợp lệ JSON của các kho tri thức.
