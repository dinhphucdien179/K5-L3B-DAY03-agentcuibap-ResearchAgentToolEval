# Báo cáo cá nhân — Đào Văn Hiệp - 2A202603813

## 1. Thông tin

- Họ tên: **Đào Văn Hiệp**.
- MSSV: **2A202603813**.
- Email: 26ai.hiepdv3@vinuni.edu.vn.
- GitHub: [daohiep2903](https://github.com/daohiep2903).
- Nhóm: **agentcuibap**, lớp **L3B**.

## 2. Phần việc phụ trách

Theo [TEAM.md](../../TEAM.md), tôi phụ trách CP2: tối ưu system prompt,
tool declaration và phân tích kết quả v1–v3. Chuỗi thực nghiệm tôi trình bày
sử dụng **Groq / `openai/gpt-oss-120b`**, với snapshot tại `artifacts/cp2/`.

## 3. Nội dung thực hiện

### V1 — Hỏi lại khi thiếu thông tin

Tôi tập trung vào quy tắc xử lý thông tin thiếu trong system prompt: hỏi lại
thay vì tự đoán tài khoản hoặc URL, đồng thời giữ thông tin đã có trong hội
thoại. Kết quả tăng từ 13/20 lên 16/20; R10 và R11 được sửa.

### V2 — Xác nhận trước khi gửi

Tôi tập trung vào quy tắc xuất bản: yêu cầu gửi ban đầu chưa phải xác nhận;
nội dung và đích nhận phải được duyệt rõ ràng. Kết quả đạt 17/20 và R12 được
sửa ở vòng này. Tuy nhiên, M02 chuyển sang chọn sai tool, làm routing giảm
từ 95% xuống 90%, nên tôi theo dõi cả hồi quy thay vì chỉ nhìn điểm tổng.

### V3 — Làm rõ mô tả tool và tham số

Tôi tập trung sửa mô tả trong `tools.yaml`: khi nào dùng mỗi tool và cách
truyền query, topic, timeframe. Cấu trúc schema được giữ nguyên để đối chiếu
ảnh hưởng của phần mô tả. Kết quả đạt 18/20; R03 và M02 được sửa, multi-turn
đạt 100%. R12 tái lỗi và R13 chưa xử lý đủ yêu cầu nhiều nguồn.

## 4. Kết quả và bằng chứng

| Phiên bản Groq | Case accuracy | Routing | Arguments | Multi-turn |
|---|---:|---:|---:|---:|
| v0 | 13/20 — 65% | 75% | 65% | 83,33% |
| v1 | 16/20 — 80% | 95% | 80% | 83,33% |
| v2 | 17/20 — 85% | 90% | 85% | 83,33% |
| v3 | 18/20 — 90% | 95% | 90% | 100% |

Các run đều đo đủ 20 case và không có provider error. Số liệu này thuộc
chuỗi Groq v0–v3, không phải chuỗi OpenRouter hoặc điểm của v7 hiện tại.

- [Nhật ký giả thuyết, snapshot và phân tích CP2](../../starter_v0/artifacts/cp2/experiment_log.md).
- [Run v1](../../starter_v0/runs/v1_B_base_groq_20261111T012136469699.json).
- [Run v2](../../starter_v0/runs/v2_B_base_groq_20261111T012508887737.json).
- [Run v3](../../starter_v0/runs/v3_B_base_groq_20261111T013146721916.json).
- [Kiểm tra bằng chứng CP2](../../starter_v0/artifacts/cp2/validation.json).

## 5. Tự đánh giá

Tôi đối chiếu tool calls và arguments của từng case giữa các vòng, đồng thời
kiểm tra hash prompt/tools với snapshot. Qua ba vòng, tôi thấy một thay đổi
có thể tăng điểm tổng nhưng vẫn tạo lỗi mới ở tình huống khác.

Phần cần cải thiện là ranh giới xác nhận gửi và xử lý yêu cầu nhiều nguồn.
Tôi cũng cần review câu trả lời ngoài phạm vi, vì không gọi tool chưa đủ để
kết luận câu trả lời đúng. Lỗi API của tool được xem riêng với lỗi routing;
điểm 18/20 không chứng minh mọi nguồn đều truy cập thành công.
