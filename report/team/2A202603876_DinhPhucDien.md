# Báo cáo cá nhân — Đinh Phúc Diên

## 1. Thông tin

- Họ tên: **Đinh Phúc Diên**
- MSSV: **2A202603876**
- Email: 26ai.diendp@vinuni.edu.vn
- GitHub: [dinhphucdien179](https://github.com/dinhphucdien179)
- Nhóm: **agentcuibap**, lớp **L3B**
- Repo: [K5-L3B-DAY03-agentcuibap-ResearchAgentToolEval](https://github.com/dinhphucdien179/K5-L3B-DAY03-agentcuibap-ResearchAgentToolEval), nhánh `main`.

## 2. Phần việc phụ trách

Em phụ trách CP2–CP5: tối ưu prompt/tool declaration, xây dựng tool và test với Codex hỗ trợ; trực tiếp cấu hình AI20k/API, chạy kiểm thử/eval v4 và thực hiện demo. Các vòng v5/v6 cùng kiểm tra 272 test được Codex chạy trong AI20k theo yêu cầu của em và có log riêng.

## 3. Đóng góp cụ thể

- Cấu hình Conda `AI20k`, OpenRouter và các API research; chạy preflight thành công với model `openai/gpt-4o-mini`.
- Trực tiếp chạy `pytest`: **257 passed, 0 failed, 0 skipped**.
- Trực tiếp chạy base eval v4: **19/20 case**, routing **100%**, argument **95%**, multi turn **100%**.
- Trực tiếp chạy group eval v4: **9/10 case**, gồm đúng **5 single turn + 5 multi turn**.
- Tự khởi chạy UI Streamlit, tạo link qua Cloudflare Tunnel và xác nhận mở được giao diện.
- Thực hiện phiên `chat.py` **5 lượt**: nghiên cứu RAG, yêu cầu thiếu URL, bổ sung URL arXiv, yêu cầu gửi Telegram và hủy gửi.
- Cung cấp log test/eval/chat và lỗi vận hành để đối chiếu, sửa hướng dẫn và cập nhật bằng chứng báo cáo.
- CP2 bổ sung: dùng Codex sửa quy tắc xác nhận ở prompt v5 rồi sửa riêng clarify.description ở v6; giả thuyết được ghi trước khi đo. Bản v6 đạt base 20/20 và group 10/10.
- CP3 bổ sung: dùng Codex sửa lỗi payload tìm kiếm, URL và citation; thêm 14 regression case. Kiểm tra cuối toàn suite: **272 passed, 0 failed, 0 skipped**.

## 4. Bằng chứng

| Nội dung | File |
|---|---|
| Kiểm tra link demo public | [ui_connectivity_current.json](../../starter_v0/analysis/ui_connectivity_current.json): trang/health 200, WebSocket 101 |
| Kết quả tự chạy test và preflight | [member_verification_20261110.md](../../starter_v0/analysis/member_verification_20261110.md) |
| Base eval v4 | [v4_B_base_openrouter_20261110T213840374908.json](../../starter_v0/runs/v4_B_base_openrouter_20261110T213840374908.json) |
| Group eval v4 | [v4_B_group_openrouter_20261110T213941166369.json](../../starter_v0/runs/v4_B_group_openrouter_20261110T213941166369.json) |
| Chat tương tác 5 lượt | [v4_openrouter_20261110T214232005322.transcript.json](../../starter_v0/transcripts/v4_openrouter_20261110T214232005322.transcript.json) |
| CP2–CP3 bổ sung | [cp2_cp3_summary.md](../../starter_v0/analysis/cp2_cp3_summary.md) |
| Base v6 | [v6_B_base_openrouter_20261110T234242756239.json](../../starter_v0/runs/v6_B_base_openrouter_20261110T234242756239.json) |
| Group v6 | [v6_B_group_openrouter_20261110T234157985676.json](../../starter_v0/runs/v6_B_group_openrouter_20261110T234157985676.json) |
| Test mới nhất | [pytest_final.txt](../../starter_v0/analysis/pytest_final.txt), [pytest.xml](../../starter_v0/analysis/pytest.xml): 272 pass |
| Lịch sử cải tiến và hash | [version_log.csv](../../starter_v0/artifacts/version_log.csv) |
| Tổng hợp và hạn chế | [group_report.md](group_report.md) |
| Cách chạy bằng AI20k | [RUNBOOK.md](../../starter_v0/RUNBOOK.md) |


## 5. AI/công cụ đã dùng và cách kiểm tra

Em dùng **AI** để hỗ trợ triển khai bốn tool `investigate`, `compare_research`,
`citation_audit`, `deduplicate`; viết test; sửa runtime xác nhận gửi; xây dựng UI
và tổng hợp báo cáo từ log. AI cũng hỗ trợ giải thích lỗi đường dẫn và tunnel.

Em kiểm tra kết quả bằng cách chạy pytest trong đúng AI20k, gọi provider thật,
chạy hai bộ eval và thực hiện chat tương tác. Với các case FAIL, đối chiếu tool
calls và args trong run JSON thay vì chỉ xem câu trả lời. Không sửa bộ eval gốc,
không ghi kết quả Telegram gửi thật hoặc model local khi chưa có run chứng minh.

## 6. Tự đánh giá dựa trên kết quả thực tế

Ở lần em trực tiếp chạy bản v4: 257 test pass, base đạt 95%, group đạt 90%; phiên chat xử lý được thiếu URL, bổ sung thông tin, xin xác nhận rồi hủy gửi. UI đã được em mở và xác nhận chạy được.

CP2–CP3 bổ sung với Codex hỗ trợ đã có kết quả v6: base **20/20**, group **10/10** và **272 test pass**. R12 và G01 đều pass trong run mới. Một số API mạng xã hội vẫn trả lỗi HTTP; độ liên quan và độ đúng của nội dung cần review riêng. Điểm routing cao chưa chứng minh nội dung luôn đúng hoặc API luôn hoạt động. Telegram gửi thật, thử model local và đánh giá bởi người ngoài nhóm chưa có bằng chứng hoàn thành.

Ưu tiên tiếp theo là đo độ ổn định qua nhiều run và bổ sung kiểm tra chất lượng nguồn. Các log FAIL cũ và giới hạn của phép đo được giữ nguyên trong báo cáo.
