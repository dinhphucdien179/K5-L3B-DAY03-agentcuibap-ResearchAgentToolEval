# Kiểm tra trực tiếp của Đinh Phúc Diên — 10/11/2026

Nguồn: kết quả terminal thành viên cung cấp và các file JSON tương ứng trong
repo. Các lệnh dưới đây do thành viên chạy trong `starter_v0`, bằng Conda
`AI20k`; đây không phải một lần chạy mới do script tạo báo cáo thực hiện.

| Kiểm tra | Kết quả quan sát |
|---|---|
| `python -m pytest -q` | `257 passed in 5.53s`, không failed/skipped |
| `python scripts/preflight_provider.py --provider openrouter` | `OK provider=openrouter model=openai/gpt-4o-mini`; tool timeline, screenname=sama, limit=1 |
| Base v4 | 19/20; provider_error_cases=0; measured_cases=20 |
| Group v4 | 9/10; provider_error_cases=0; measured_cases=10 |
| Chat v4 | 5 lượt; không provider/tool error; không gọi send |

## File bằng chứng

- [Base run](../runs/v4_B_base_openrouter_20261110T213840374908.json)
- [Group run](../runs/v4_B_group_openrouter_20261110T213941166369.json)
- [Chat transcript](../transcripts/v4_openrouter_20261110T214232005322.transcript.json)
- [Output pytest do phiên triển khai lưu trước đó](pytest_final.txt): cùng 257 test pass, thời gian chạy có thể khác.

## Hai case eval còn FAIL

- R12: gọi clarify đúng tool nhưng response_type=text thay vì yes_no.
- G01: gọi investigate thêm lần nữa cho cùng chủ đề và cùng tập góc nhìn.

Đã xác nhận UI truy cập được qua trao đổi với thành viên. Chưa có bằng chứng
người ngoài nhóm dùng thử, gửi Telegram thật hoặc chạy model local.
