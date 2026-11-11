# Báo cáo cá nhân — Đinh Phúc Diên

## 1. Thông tin

- Họ tên: **Đinh Phúc Diên**.
- MSSV: **2A202603876**.
- Email: 26ai.diendp@vinuni.edu.vn.
- GitHub: [dinhphucdien179](https://github.com/dinhphucdien179).
- Nhóm: **agentcuibap**, lớp **L3B**.

## 2. Phần việc phụ trách

Theo [TEAM.md](../../TEAM.md), em phụ trách cấu hình môi trường và OpenRouter,
tối ưu CP2 ở v5–v6, bốn tool nghiên cứu của CP3, chạy kiểm tra và thực hiện
phiên chat demo.

## 3. Nội dung thực hiện

### Cấu hình và kiểm tra môi trường

Em cấu hình Conda `AI20k`, provider OpenRouter với model `openai/gpt-4o-mini`
và các API phục vụ nghiên cứu. Em trực tiếp chạy preflight, pytest và eval
ở v4; kết quả ghi nhận 257 test pass, base 19/20 và group 9/10. Em cũng mở
UI Streamlit và Cloudflare Tunnel để kiểm tra truy cập giao diện.

### CP2 — Tối ưu v5–v6

Em tập trung vào lỗi xác nhận gửi ở R12. V5 sửa system prompt để ưu tiên
hỏi xác nhận khi có yêu cầu gửi; kết quả base vẫn 19/20 nên lỗi chưa được
giải quyết. V6 giữ prompt và sửa riêng mô tả `clarify` trong `tools.yaml`,
làm rõ `response_type="yes_no"` cho yêu cầu gửi lần đầu.

| Phiên bản OpenRouter | Base | Group | Thay đổi |
|---|---:|---:|---|
| v4 | 19/20 | 9/10 | Mốc em trực tiếp kiểm tra |
| v5 | 19/20 | 10/10 | Sửa quy tắc xác nhận trong prompt |
| v6 | 20/20 | 10/10 | Sửa mô tả clarify, R12 đạt |

Các điểm này thuộc snapshot của từng phiên bản, không phải điểm của v7.

### CP3 — Bốn tool nghiên cứu

| Tool em phụ trách | Chức năng |
|---|---|
| `investigate` | Thu thập nguồn và đoạn trích theo nhiều góc nhìn |
| `compare_research` | Lập ma trận bằng chứng theo đối tượng và tiêu chí chung |
| `citation_audit` | Rà ID nguồn, URL và đoạn thiếu trích dẫn |
| `deduplicate` | Gộp URL trùng, giữ nguồn đầu và tham số nội dung |

Phần kiểm thử bao phủ đầu vào không hợp lệ, thiếu key, lỗi truy vấn từng phần,
URL tracking và citation không khớp. Các tool có `TOOL.md`, đăng ký trong
registry và schema tương ứng. Em chú trọng việc giữ nguồn đã lấy được khi
một truy vấn khác lỗi, và không gộp nhầm các URL khác nội dung.

### Chat demo

Em trực tiếp thực hiện phiên chat 5 lượt: nghiên cứu RAG, yêu cầu đọc bài
khi thiếu URL, bổ sung URL arXiv, yêu cầu gửi bản tin và hủy gửi. Phiên này
không gọi `send`. Lượt nghiên cứu đầu gọi `investigate` hai lần; transcript
được giữ nguyên để đối chiếu lỗi lặp.

## 4. Bằng chứng

- [Kết quả em trực tiếp chạy ở v4](../../starter_v0/analysis/member_verification_20261110.md).
- [Giả thuyết v5](../../starter_v0/artifacts/versions/v5/hypothesis.json), [v6](../../starter_v0/artifacts/versions/v6/hypothesis.json).
- [Base v6](../../starter_v0/runs/v6_B_base_openrouter_20261110T234242756239.json), [group v6](../../starter_v0/runs/v6_B_group_openrouter_20261110T234157985676.json).
- [Unit test tool](../../starter_v0/tests/test_tools_todo.py), [regression CP3](../../starter_v0/tests/test_cp3_regressions.py).
- [Transcript demo 5 lượt](../../starter_v0/transcripts/v4_openrouter_20261110T214232005322.transcript.json).

## 5. Tự đánh giá

Em đối chiếu kết quả bằng tool calls, arguments và lỗi thực thi trong run JSON.
Điểm routing đúng không bảo đảm API thành công hoặc nội dung đã được xác minh.
Kết quả test chung hiện tại là **407 passed, 0 failed, 0 skipped**, theo
[validation.json](../../starter_v0/analysis/validation.json); đây không phải
số test riêng của phần em phụ trách. V7 chưa có run model mới.

Phần cần cải thiện là chất lượng nguồn, độ ổn định qua nhiều lần chạy và xử lý
API mạng xã hội bị lỗi. Em chưa có bằng chứng gửi Telegram thật hoặc chạy
Small Local Model Challenge.
