# Research Studio — agentcuibap

Chạy các lệnh trong thư mục `starter_v0`, bằng môi trường Conda `AI20k`.
Hướng dẫn mở UI và chia sẻ link: [RUNBOOK.md](RUNBOOK.md).

## Ứng dụng

`app.py` là điểm chạy UI. Thanh bên chọn provider/model; các tab gồm Agent chat,
Pipeline & prompt, Research board và Execution log. Registry có 15 tool, trong đó
5 tool nhóm thêm: `investigate`, `compare_research`, `citation_audit`, `deduplicate`,
`research_board`. Form Research desk gọi tool trực tiếp; chat dùng model để chọn tool.

Copy `.env.example` thành `.env` rồi điền key. API key chỉ lưu ở server, không nhập
vào UI và không commit. Telegram mặc định bị khóa; muốn demo gửi thật cần cấu hình
`RESEARCH_ALLOW_SEND=1`, token/chat ID và duyệt nguyên văn bằng nút xác nhận.

## Kiểm tra

```bash
conda run --no-capture-output -n AI20k python -m pytest -q
conda run --no-capture-output -n AI20k python scripts/preflight_provider.py --provider openrouter
conda run --no-capture-output -n AI20k python run_eval.py --provider openrouter --version v7 --suite base --eval-cases data/eval_base.json
conda run --no-capture-output -n AI20k python run_eval.py --provider openrouter --version v7 --suite group --eval-cases data/eval_group.json
conda run --no-capture-output -n AI20k python chat.py --provider openrouter --version v7
```

`data/eval_group.json` có đúng 10 case: 5 single turn, 5 multi turn, bao phủ 5 tool
mới, args và boundary. Các lệnh provider/eval/chat gọi API thật và dùng quota.

## Cấu trúc

| Đường dẫn | Nội dung |
|---|---|
| `artifacts/system_prompt.md`, `artifacts/tools.yaml` | Prompt/schema đang dùng, bản v7 |
| `tools/`, `tests/`, `ui/` | Implementation, unit test và các thành phần giao diện |
| `artifacts/version_log.csv`, `artifacts/versions/`, `artifacts/cp*/` | Lịch sử thử nghiệm và snapshot giữ nguyên để đối chiếu hash |
| `runs/`, `transcripts/` | Kết quả eval và hội thoại đã ghi |
| `analysis/validation.json`, `analysis/pytest_final.xml` | Kiểm tra code bản hiện tại |

Số liệu v0–v6 và Groq trong bằng chứng thuộc đúng snapshot ghi trong run, không phải
điểm của v7. Các file snapshot trong `artifacts/` phục vụ tái lập thực nghiệm.

## Quy định lab

File học viên được sửa theo đề: `artifacts/system_prompt.md`, `artifacts/tools.yaml`,
`artifacts/version_log.csv`, `data/eval_group.json`, `tools/`, `tests/test_tools_todo.py`,
code UI và `requirements.txt`. Không sửa nội dung case trong `data/eval_base.json`
và `data/eval_research_extension.json`.

[Yêu cầu bài](../README.md) · [Quy tắc](../RULES.md) · [Cấu hình API](../docs/TOOL-SETUP.md)
· [Báo cáo nhóm](../report/team/group_report.md).
