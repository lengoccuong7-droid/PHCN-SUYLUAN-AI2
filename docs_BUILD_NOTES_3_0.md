# Build notes – PHCN AI 3.0.0-dev2

## Nguồn nền thực tế
Bản nguồn có thể khôi phục trong Library tại thời điểm build là `PHCN_AI_2_4_3.zip`. Không tìm thấy gói 2.5.0 trong Library ở phiên làm việc này. Vì vậy dev2 được phát triển trên bộ nguồn 2.4.3 đã khôi phục cùng các tệp dev1 còn tồn tại trong thư mục làm việc; không tuyên bố đây là bản nâng cấp đầy đủ từ 2.5.0.

## Các tệp được chỉnh sửa
- `core/reasoning_engine.py`
- `core/clinical_engine.py`
- `modules/tab3_kham.py`
- `tests/test_general_reasoning.py`
- `tests/test_case13_14_regression.py`
- `VERSION`, `README_3_0_DEV.md`, `CHANGELOG_3_0_DEV.md`

## Xác minh
- `PYTHONPATH=. python -m pytest -q`: 25 passed.
- `python -m compileall -q .`: passed.
- Chưa thực hiện smoke test giao diện Streamlit trên điện thoại.
- Môi trường build hiện tại chưa cài Streamlit; do đó chưa thể xác nhận khởi chạy giao diện app tại đây.
- Chưa xuất ZIP theo yêu cầu: chỉ xuất khi người dùng xác nhận.
