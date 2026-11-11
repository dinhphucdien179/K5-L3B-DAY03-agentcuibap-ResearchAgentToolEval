# Báo cáo cá nhân — Lê Nguyễn Anh Nhân

## 1. Thông tin

- Họ tên: **Lê Nguyễn Anh Nhân**.
- MSSV: **2A202603838**.
- Nhóm: **agentcuibap**, lớp **L3B**.

## 2. Phần việc tôi phụ trách

Theo [phân công của nhóm](../../TEAM.md), tôi phụ trách eval nhóm, giao diện
và pipeline, transcript demo và tổng hợp báo cáo. Trọng tâm của tôi là làm
cho quá trình kiểm tra có dữ liệu đối chiếu: model nhận gì, chọn tool nào,
implementation trả gì và giao diện hiển thị kết quả ra sao.

## 3. Nội dung thực hiện

### CP4 — Eval nhóm

Tôi tập trung thiết kế và đối chiếu các tình huống hỏi thiếu dữ liệu, sửa
tham số qua hội thoại, yêu cầu nhiều nguồn và ranh giới gửi nội dung. Với
`research_board`, các case kiểm tra cả yêu cầu dựng bản đồ nguồn ở một lượt
và việc sửa khoảng thời gian, số lượng, query so sánh ở nhiều lượt.

Bộ Groq được đóng băng trước lần đánh giá đã lưu và đạt 10/10 với model
`openai/gpt-oss-120b`, không có provider error. Tôi phân biệt kết quả đó với
trạng thái thực thi: một số API mạng xã hội vẫn trả HTTPError và có câu trả
lời cần review tay dù case được chấm PASS.

Bộ nộp hiện tại được chốt chung ở đúng 10 case: 5 single turn, 5 multi turn,
bao phủ cả 5 tool mới. Bộ này có khác biệt với bộ Groq đã đo; tôi không dùng
điểm 10/10 cũ để khẳng định điểm của bộ hiện tại.

### CP5 — UI và pipeline

Phần giao diện tôi phụ trách có chat, Research Board, pipeline và execution
log. UI hiện tại cho phép chọn provider/model và dùng chung registry 15 tool.
Tôi chú ý tách hai luồng tương tác: chat để model chọn tool, còn Research desk
là thao tác gọi `research_board` trực tiếp từ form.

Pipeline hiển thị thứ tự system prompt, policy, lịch sử phiên và câu hỏi;
schema tool được gửi riêng cho provider. Snapshot của từng request được ghi
tại đầu vào adapter và đã che dữ liệu nhạy cảm. Đây không phải bản bắt gói
HTTP, cũng không phải phần suy nghĩ nội bộ của model.

Khi tool lỗi hoặc chỉ có dữ liệu một phần, UI giữ lại trạng thái và nguồn
đã thu được trong trace. Mỗi phiên có lịch sử và transcript riêng. Model
không được tự gửi Telegram; mặc định khóa gửi, còn chế độ cho phép gửi cần
nút duyệt đúng bản nháp. Hủy hoặc bắt đầu phiên mới phải làm hết hiệu lực
bản nháp đang chờ.

### Transcript và báo cáo

Tôi phụ trách tổng hợp các tình huống demo và liên kết transcript với báo cáo.
Phiên Groq 20b có bốn lượt: dựng board/tổng hợp, hỏi URL còn thiếu, đọc URL
được bổ sung và hỏi thông tin gửi. Phiên tiếp nối ghi thêm bước hỏi xác nhận.
Đây là tình huống thử nghiệm soạn sẵn qua API thật; chưa có gửi Telegram.

Lần thử 120b gặp quota 429 được giữ lại để giải thích việc đổi model cho demo.
Các run dùng để so sánh CP2 và run group vẫn được đọc theo model ghi trong
chính run đó. Tôi không dùng các lượt lỗi quota làm bằng chứng hoàn tất demo.

## 4. Bằng chứng

| Nội dung | Bằng chứng |
|---|---|
| Bộ eval hiện tại | [eval_group.json](../../starter_v0/data/eval_group.json), [test dataset](../../starter_v0/tests/test_eval_group.py) |
| Bộ Groq đã đo | [Dataset đóng băng](../../starter_v0/artifacts/cp4_cp5/eval_group.frozen.json), [freeze metadata](../../starter_v0/artifacts/cp4_cp5/group_freeze.json) |
| Kết quả group Groq | [Run 10/10](../../starter_v0/runs/cp3-research-board-v2_B_group_groq_20261111T022506173733.json), [phân tích lỗi và giới hạn](../../starter_v0/artifacts/cp4_cp5/group_analysis.json) |
| UI và quan sát pipeline | [app.py](../../starter_v0/app.py), [runtime](../../starter_v0/ui/runtime.py), [pipeline](../../starter_v0/ui/pipeline.py) |
| Chat demo qua API thật | [Phiên 20b](../../starter_v0/transcripts/cp3-research-board-v2_groq_20261111T023231396178.transcript.json), [lượt tiếp nối](../../starter_v0/transcripts/cp5_confirmation_20b_20261111T024124787005.transcript.json) |
| AppTest với request thật | [live_pipeline_check.json](../../starter_v0/artifacts/cp5_pipeline/live_pipeline_check.json) |
| Kiểm tra code hiện tại | [validation.json](../../starter_v0/analysis/validation.json), [JUnit XML](../../starter_v0/analysis/pytest_final.xml) |
| Tổng hợp kết quả | [Báo cáo nhóm](group_report.md) |

## 5. Cách tôi đối chiếu kết quả

Tôi kiểm tra số case, tỷ lệ single/multi, schema arguments và các case route
tới tool mới. Khi đọc run, tôi xem cả summary, tool event và lỗi trả về. Khi
đọc pipeline, tôi phân biệt tool call model đề xuất với tool thực sự đã chạy,
không coi một node trong sơ đồ là bằng chứng thực thi.

Bản chung hiện tại có **407 test pass, 0 fail, 0 skip**, gồm kiểm tra dataset,
runtime và AppTest. Các mốc 184 hoặc 195 test trong artifact là checkpoint
trước đó. Kiểm tra live của checkpoint pipeline cũng không thay thế việc
chạy lại model/API cho v7; hiện chưa có run đó.

## 6. Tự đánh giá và phần cần cải thiện

Phần tôi tập trung là khả năng quan sát và đối chiếu: câu trả lời cần đi kèm
nguồn, trace và trạng thái lỗi; báo cáo cần dẫn tới đúng run và snapshot.
Điều tôi rút ra là routing đúng chưa bảo đảm tool thành công, và hiển thị
được graph chưa có nghĩa các nguồn đã được xác minh.

Tôi cần bổ sung kiểm tra trực quan trên trình duyệt/mobile và thử với người
ngoài nhóm. Link Cloudflare chỉ là link tạm, cần giữ ứng dụng và tunnel chạy.
Hiện chưa có bằng chứng gửi Telegram thật hoặc phản hồi người ngoài nhóm.
