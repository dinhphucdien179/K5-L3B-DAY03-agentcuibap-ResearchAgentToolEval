# Báo cáo cá nhân — Đào Văn Hiệp — 2A202603813

## 1. Thông tin

- Họ tên: **Đào Văn Hiệp**.
- MSSV: **2A202603813**.
- Email: 26ai.hiepdv3@vinuni.edu.vn.
- GitHub: [daohiep2903](https://github.com/daohiep2903).
- Nhóm: **agentcuibap**, lớp **L3B**.

## 2. Phần việc tôi phụ trách

Theo [phân công của nhóm](../../TEAM.md), tôi phụ trách CP2: phân tích lỗi,
tối ưu system prompt và tool declaration ở các phiên bản v1–v3.

Trong báo cáo này, tôi dùng chuỗi thực nghiệm **Groq / `openai/gpt-oss-120b`**
được lưu tại `artifacts/cp2/`. Tên phiên bản và số liệu bên dưới thuộc chuỗi
này; chuỗi OpenRouter có snapshot và kết quả riêng.

## 3. Nội dung thực hiện

### Phân tích baseline

Tôi tập trung đọc các trường hợp chọn sai tool, truyền sai arguments, tự đoán
thông tin còn thiếu và gửi khi chưa có xác nhận. Baseline Groq đạt 13/20 case.
Từ các lỗi này, tôi chia hướng tối ưu thành từng vòng để có thể đối chiếu
thay đổi với kết quả, thay vì sửa nhiều phần cùng lúc.

### V1 — Hỏi lại khi thiếu dữ liệu

Ở vòng v1, tôi tập trung vào đoạn xử lý thông tin thiếu trong system prompt.
Giả thuyết là yêu cầu hỏi lại một cách rõ ràng sẽ giảm việc tự đoán tài khoản
hoặc URL, đồng thời vẫn sử dụng thông tin đã có trong lịch sử hội thoại.

Kết quả tăng lên 16/20; hai case R10 và R11 được sửa. Tôi không xem việc
không gọi tool là đủ chứng minh câu trả lời đã đúng phạm vi, vì vẫn có trường
hợp model trả lời nội dung ngoài nhiệm vụ nghiên cứu.

### V2 — Làm rõ xác nhận trước khi gửi

Ở vòng v2, phần chỉnh sửa nằm trong đoạn quy định xuất bản của system prompt.
Tôi tập trung phân biệt yêu cầu gửi ban đầu với sự xác nhận ở một lượt sau,
và yêu cầu duyệt nội dung cùng đích nhận cụ thể.

Kết quả đạt 17/20 và R12 được sửa ở vòng này. Tuy nhiên, routing accuracy giảm
từ 95% xuống 90% do M02 chuyển sang chọn sai tool. Vì vậy, tôi xem cả tiến bộ
và hồi quy, không chỉ nhìn case accuracy tổng.

### V3 — Làm rõ mô tả tool và tham số

Ở vòng v3, tôi tập trung vào `tools.yaml`: mô tả khi nào dùng hoặc không dùng
mỗi tool, cùng quy ước cho query, topic và timeframe. Cấu trúc schema được giữ
nguyên để việc đối chiếu tập trung vào mô tả.

Kết quả đạt 18/20; R03 và M02 được sửa, multi-turn đạt 100%. R12 tái lỗi và
R13 chưa xử lý đủ yêu cầu nhiều nguồn, nên tôi không kết luận rằng ranh giới
gửi và khả năng phối hợp tool đã được giải quyết hoàn toàn.

## 4. Kết quả và bằng chứng

| Phiên bản Groq | Case accuracy | Routing | Arguments | Multi-turn |
|---|---:|---:|---:|---:|
| v0 | 13/20 — 65% | 75% | 65% | 83,33% |
| v1 | 16/20 — 80% | 95% | 80% | 83,33% |
| v2 | 17/20 — 85% | 90% | 85% | 83,33% |
| v3 | 18/20 — 90% | 95% | 90% | 100% |

Các run trên đều đo đủ 20 case và không có provider error. Bằng chứng:

- [Nhật ký giả thuyết và phân tích CP2](../../starter_v0/artifacts/cp2/experiment_log.md).
- [Snapshot và phân tích v1](../../starter_v0/artifacts/cp2/v1/analysis.json), [v2](../../starter_v0/artifacts/cp2/v2/analysis.json), [v3](../../starter_v0/artifacts/cp2/v3/analysis.json).
- [Run v1](../../starter_v0/runs/v1_B_base_groq_20261111T012136469699.json).
- [Run v2](../../starter_v0/runs/v2_B_base_groq_20261111T012508887737.json).
- [Run v3](../../starter_v0/runs/v3_B_base_groq_20261111T013146721916.json).
- [Kiểm tra artifact và kết quả CP2](../../starter_v0/artifacts/cp2/validation.json).

## 5. Cách tôi đối chiếu kết quả

Tôi đọc tool calls và arguments của từng case thất bại, so sánh giữa hai vòng
liền nhau và kiểm tra hash của prompt/tools với snapshot đã lưu. Tôi giữ riêng
các chỉ số routing, arguments và multi-turn để nhận ra lỗi mới ngay cả khi
điểm tổng tăng.

Tôi cũng phân biệt lỗi provider với lỗi API của tool. Không có provider error
chỉ cho biết các case được đo; điều đó không chứng minh nguồn mạng xã hội đã
truy cập thành công hoặc nội dung trả lời đã được kiểm chứng.

## 6. Tự đánh giá và phần cần cải thiện

Phần tôi phụ trách giúp làm rõ cách xử lý dữ liệu thiếu, xác nhận gửi và mô tả
công cụ qua ba vòng tối ưu. Điều tôi rút ra là prompt và tool declaration cần
nhất quán; sửa một nơi có thể làm xuất hiện hồi quy ở tình huống khác.

Tôi cần tiếp tục phân tích các trường hợp phối hợp nhiều nguồn và kiểm tra tay
câu trả lời ngoài phạm vi. Kết quả 18/20 ở v3 thuộc chuỗi thực nghiệm Groq này,
không phải điểm của bản v7 hiện tại hay kết quả riêng của các phần CP3–CP5.
