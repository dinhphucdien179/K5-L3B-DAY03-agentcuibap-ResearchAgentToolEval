# Báo cáo cá nhân — Đinh Phúc Diên

## 1. Thông tin

- Họ tên: **Đinh Phúc Diên**
- MSSV: **2A202603876**
- Email: dinhphucdien179@gmail.com
- GitHub: [dinhphucdien179](https://github.com/dinhphucdien179)
- Nhóm: **agentcuibap**, lớp **L3B**
- Repo: [K5-L3B-DAY03-agentcuibap-ResearchAgentToolEval](https://github.com/dinhphucdien179/K5-L3B-DAY03-agentcuibap-ResearchAgentToolEval), nhánh `main`.

## 2. Phần việc phụ trách

Em phụ trách cấu hình môi trường và API, vận hành agent, chạy các bước kiểm tra,
thực hiện demo và phối hợp với Codex để hoàn thiện bài. Code, unit test, eval,
UI và nội dung tổng hợp báo cáo có sử dụng AI hỗ trợ.

## 3. Đóng góp cụ thể

- Cấu hình Conda `AI20k`, OpenRouter và các API research; chạy preflight thành công với model `openai/gpt-4o-mini`.
- Trực tiếp chạy `pytest`: **257 passed, 0 failed, 0 skipped**.
- Trực tiếp chạy base eval v4: **19/20 case**, routing **100%**, argument **95%**, multi turn **100%**.
- Trực tiếp chạy group eval v4: **9/10 case**, gồm đúng **5 single turn + 5 multi turn**.
- Tự khởi chạy UI Streamlit, tạo link qua Cloudflare Tunnel và xác nhận mở được giao diện.
- Thực hiện phiên `chat.py` **5 lượt**: nghiên cứu RAG, yêu cầu thiếu URL, bổ sung URL arXiv, yêu cầu gửi Telegram và hủy gửi.
- Cung cấp log test/eval/chat và lỗi vận hành để đối chiếu, sửa hướng dẫn và cập nhật bằng chứng báo cáo.

## 4. Bằng chứng

| Nội dung | File |
|---|---|
| Kiểm tra link demo public | [ui_connectivity_current.json](../../starter_v0/analysis/ui_connectivity_current.json): trang/health 200, WebSocket 101 |
| Kết quả tự chạy test và preflight | [member_verification_20261110.md](../../starter_v0/analysis/member_verification_20261110.md) |
| Base eval v4 | [v4_B_base_openrouter_20261110T213840374908.json](../../starter_v0/runs/v4_B_base_openrouter_20261110T213840374908.json) |
| Group eval v4 | [v4_B_group_openrouter_20261110T213941166369.json](../../starter_v0/runs/v4_B_group_openrouter_20261110T213941166369.json) |
| Chat tương tác 5 lượt | [v4_openrouter_20261110T214232005322.transcript.json](../../starter_v0/transcripts/v4_openrouter_20261110T214232005322.transcript.json) |
| Lịch sử cải tiến và hash | [version_log.csv](../../starter_v0/artifacts/version_log.csv) |
| Tổng hợp và hạn chế | [group_report.md](group_report.md) |
| Cách chạy bằng AI20k | [RUNBOOK.md](../../starter_v0/RUNBOOK.md) |

Commit chốt bài chưa được tạo. HEAD hiện tại là commit đề gốc; chưa dùng commit
đó làm bằng chứng đóng góp kỹ thuật của cá nhân.

## 5. AI/công cụ đã dùng và cách kiểm tra

Em dùng **Codex** để hỗ trợ triển khai bốn tool `investigate`, `compare_research`,
`citation_audit`, `deduplicate`; viết test; sửa runtime xác nhận gửi; xây dựng UI
và tổng hợp báo cáo từ log. AI cũng hỗ trợ giải thích lỗi đường dẫn và tunnel.

Em kiểm tra kết quả bằng cách chạy pytest trong đúng AI20k, gọi provider thật,
chạy hai bộ eval và thực hiện chat tương tác. Với các case FAIL, đối chiếu tool
calls và args trong run JSON thay vì chỉ xem câu trả lời. Không sửa bộ eval gốc,
không ghi kết quả Telegram gửi thật hoặc model local khi chưa có run chứng minh.

## 6. Tự đánh giá dựa trên kết quả thực tế

Phần vận hành và kiểm tra đã có bằng chứng: test không fail/skip, provider hoạt
động, base đạt 95%, group đạt 90% và phiên chat xử lý được thiếu URL, bổ sung
thông tin, xin xác nhận rồi hủy gửi. UI đã được em mở và xác nhận chạy được.

Bài vẫn còn các hạn chế: R12 hỏi nội dung bằng `response_type=text` trong khi
eval yêu cầu `yes_no`; G01 có thêm một call `investigate`; một số API mạng xã hội
trả lỗi HTTP. Kết quả routing cao chưa chứng minh nội dung luôn đúng hoặc API
luôn hoạt động. Telegram gửi thật, thử model local và đánh giá bởi người ngoài
nhóm chưa có bằng chứng hoàn thành.

Ưu tiên cải thiện là giảm call research lặp, làm rõ luồng xác nhận và bổ sung
kiểm tra chất lượng nguồn. Các giới hạn này được giữ nguyên trong log và báo cáo.
