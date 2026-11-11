# Báo cáo nhóm — Research Studio

## 1. Thông tin nhóm

- Nhóm **agentcuibap**, lớp **L3B**; nhánh nộp `main`.
- Thành viên: Đinh Phúc Diên — 2A202603876, Đào Văn Hiệp — 2A202603813, Lê Nguyễn Anh Nhân — 2A202603838.
- Phân công và báo cáo cá nhân: [TEAM.md](../../TEAM.md).
- Runtime: Conda **AI20k**; UI hỗ trợ OpenRouter, OpenAI, Groq, Gemini, Anthropic và Ollama.
- Phiên bản hiện tại: **v7**. Điểm lịch sử chỉ áp dụng prompt/schema/model được ghi trong từng run.
- Chưa có bằng chứng hoàn thành Phần A trước mốc 16:30.

## 2. PHẦN A — Giới thiệu agent

### A1. Chức năng và cách chạy

Agent tìm web/news, đọc URL, tra paper/policy, nghiên cứu đa góc nhìn, lập ma trận
bằng chứng, rà citation, gộp URL và dựng bản đồ nguồn. UI có chat đa provider,
Pipeline quan sát request/tool event và Research Board theo từng phiên.

Từ `starter_v0`:

```bash
conda run --no-capture-output -n AI20k python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

Mở http://localhost:8501. Chia sẻ public bằng
`conda run --no-capture-output -n AI20k python scripts/share_ui.py`; link được in
ở cuối terminal, tồn tại khi UI và tunnel hoạt động. Xem [RUNBOOK.md](../../starter_v0/RUNBOOK.md).

Bằng chứng truy cập UI và tunnel đã ghi tại [ui_connectivity_current.json](../../starter_v0/analysis/ui_connectivity_current.json)
và [public_deployment.json](../../starter_v0/artifacts/cp4_cp5/public_deployment.json).
Đó là kiểm tra ở thời điểm được ghi, không bảo đảm link cũ còn hoạt động.
Chưa có bằng chứng nhóm ngoài dùng thử.

### A2. Công cụ

| Tool | Chức năng | Mới |
|---|---|---|
| clarify | Hỏi thiếu dữ liệu hoặc xin xác nhận | Không |
| timeline, social_search | Lấy bài tài khoản hoặc tìm thảo luận X/Twitter | Không |
| lookup, fetch | Tìm web/news và đọc URL | Không |
| format, send | Định dạng digest và gửi Telegram sau phê duyệt | Không |
| policy, papers, paper_text | Tra policy, tìm và đọc paper arXiv | Không |
| investigate | Hồ sơ nguồn/excerpt theo nhiều góc của một chủ đề | Có |
| compare_research | Ma trận bằng chứng theo đối tượng và tiêu chí | Có |
| citation_audit | Rà ID nguồn, URL và đoạn thiếu citation | Có |
| deduplicate | Gộp URL tracking, giữ tham số nội dung và nguồn đầu | Có |
| research_board | Gộp URL, provenance, domain graph và coverage tối đa 3 query | Có |

Model không được tự gửi Telegram trong UI. Mặc định khóa gửi; chỉ khi server đặt
`RESEARCH_ALLOW_SEND=1`, người dùng duyệt nguyên văn bằng nút mới thực hiện gửi.
Hủy, đổi yêu cầu hoặc reset phiên làm hết hiệu lực bản nháp đang chờ.

### A3. Câu hỏi mẫu

1. Nghiên cứu RAG theo hai góc hiệu quả thực tế và hạn chế, mỗi góc 1 nguồn; dẫn URL.
2. So sánh PostgreSQL và Elasticsearch theo tìm kiếm toàn văn; mỗi ô 1 nguồn.
3. Rà bản nháp "Kết quả [S9]" với danh mục `[{"id":"S1","url":"https://example.org/study"}]`.
4. Gộp URL `https://example.org/a?utm_source=x` và `https://example.org/a#intro`.
5. Lập research board về thermal energy storage trong tháng, tối đa 4 kết quả.

## 3. Giải pháp

Prompt ưu tiên scope, hỏi lại khi thiếu dữ liệu và ranh giới xuất bản; declaration
nêu khi dùng/không dùng và quy ước args. Registry/schema khớp implementation.
Tool trả lỗi hoặc kết quả partial có cấu trúc; UI giữ nguồn và lỗi thật trong trace.
Nguồn web/policy là dữ liệu không đáng tin để thực thi chỉ dẫn.

`investigate` và `compare_research` thu thập bằng chứng có ID; `citation_audit`
kiểm tra cấu trúc tham chiếu. `research_board` biểu diễn coverage/provenance;
URL overlap không chứng minh các nguồn đồng ý hoặc claim đúng.
Form Research desk gọi tool trực tiếp, không được tính là model routing.

## 4. PHẦN B — Kết quả và bằng chứng

### B1. Version evidence

| Provider | Version | Thay đổi | Trước → Sau | Run |
|---|---|---|---|---|
| OpenRouter | v0 | baseline (original starter prompt/tools) | 0.65 | [v0_B_base_openrouter_20261110T185819400914.json](../../starter_v0/runs/v0_B_base_openrouter_20261110T185819400914.json) |
| OpenRouter | v1 | artifacts/system_prompt.md; artifacts/tools.yaml (register 4 CP3 tools) | 0.65 → 0.75 | [v1_B_base_openrouter_20261110T191733245712.json](../../starter_v0/runs/v1_B_base_openrouter_20261110T191733245712.json) |
| OpenRouter | v2 | artifacts/tools.yaml | 0.75 → 0.9 | [v2_B_base_openrouter_20261110T192059631983.json](../../starter_v0/runs/v2_B_base_openrouter_20261110T192059631983.json) |
| OpenRouter | v3 | artifacts/system_prompt.md | 0.9 → 0.95 | [v3_B_base_openrouter_20261110T192320127555.json](../../starter_v0/runs/v3_B_base_openrouter_20261110T192320127555.json) |
| OpenRouter | v4 | artifacts/system_prompt.md | 0.95 → 0.95 | [v4_B_base_openrouter_20261110T213840374908.json](../../starter_v0/runs/v4_B_base_openrouter_20261110T213840374908.json) |
| OpenRouter | v5 | artifacts/system_prompt.md | 0.95 → 0.95 | [v5_B_base_openrouter_20261110T234010963310.json](../../starter_v0/runs/v5_B_base_openrouter_20261110T234010963310.json) |
| OpenRouter | v6 | artifacts/tools.yaml (clarify.description only) | 0.95 → 1.0 | [v6_B_base_openrouter_20261110T234242756239.json](../../starter_v0/runs/v6_B_base_openrouter_20261110T234242756239.json) |
| Groq | v0 | baseline | 0.65 | [v0_B_base_groq_20261111T011139896815.json](../../starter_v0/runs/v0_B_base_groq_20261111T011139896815.json) |
| Groq | v1 | artifacts/system_prompt.md | 0.65 → 0.8 | [v1_B_base_groq_20261111T012136469699.json](../../starter_v0/runs/v1_B_base_groq_20261111T012136469699.json) |
| Groq | v2 | artifacts/system_prompt.md | 0.8 → 0.85 | [v2_B_base_groq_20261111T012508887737.json](../../starter_v0/runs/v2_B_base_groq_20261111T012508887737.json) |
| Groq | v3 | artifacts/tools.yaml | 0.85 → 0.9 | [v3_B_base_groq_20261111T013146721916.json](../../starter_v0/runs/v3_B_base_groq_20261111T013146721916.json) |
| Groq | v4 | artifacts/system_prompt.md | 0.9 → 0.9 | [v4_B_base_groq_20261111T013837151492.json](../../starter_v0/runs/v4_B_base_groq_20261111T013837151492.json) |

[Version log](../../starter_v0/artifacts/version_log.csv) giữ hash, lý do, giả thuyết và run gốc.
Snapshot OpenRouter ở `artifacts/versions/`; snapshot Groq ở `artifacts/cp2/`.
Các chuỗi version cùng tên thuộc thực nghiệm provider khác nhau, không nối thành
một đường tiến bộ. Chỉ dùng run có provider_error_cases=0 và measured_cases=total_cases.

OpenRouter v1 đổi cả prompt và tool set nên không quy mức tăng cho một nguyên nhân.
V5/v6 có hypothesis ghi trước eval: v5 vẫn sai boundary R12, v6 chỉ sửa clarify.description
và đạt base 20/20, group 10/10 trên bộ case khi đó. Groq v4 đạt 18/20, giữ tổng điểm
v3 nhưng sửa R12 và hồi quy R03; xem [experiment_log.md](../../starter_v0/artifacts/cp2/experiment_log.md).
Chưa có run model cho v7 và bộ 10 case hiện tại; không dùng điểm cũ thay cho kết quả này.

### B2. Phân tích lỗi

Baseline OpenRouter sai chọn tool/args ở R03/R13, tự đoán dữ liệu ở R10/R11,
vượt ranh giới gửi ở R12 và gọi tool ngoài scope ở R08/R14. Thay đổi prompt/tool
được giải thích tại [cp2_cp3_summary.md](../../starter_v0/analysis/cp2_cp3_summary.md).

Điểm tự động chỉ đo routing/args. [Review Groq](../../starter_v0/artifacts/cp2/manual_review.md)
cho thấy có câu trả lời ngoài scope dù máy chấm PASS. RapidAPI trả lỗi 403 trong
một số run; route đúng không chứng minh API lấy dữ liệu thành công.

### B3. Eval nhóm

Bộ [eval_group.json](../../starter_v0/data/eval_group.json) có đúng **10 case: 5 single turn,
5 multi turn**, bao phủ cả 5 tool mới. Mỗi case ghi điều kiểm tra và lỗi baseline
làm cơ sở cho giả thuyết regression; đây không phải sao chép câu hỏi của bộ cố định.
Query/expect của các case được chọn được giữ nguyên, chưa đo model cho v7.

| Case | Loại | Kiểm tra | Expected |
|---|---|---|---|
| G01_investigate_evidence | single | wrong_tool | investigate |
| G02_compare_shared_criteria | single | wrong_arg_value | compare_research |
| G03_audit_missing_source | single | wrong_tool | citation_audit |
| G04_deduplicate_tracking | single | wrong_tool | deduplicate |
| G01_board_thermal_storage_month | single | wrong_tool | research_board |
| G06_missing_investigation_topic | multi | missing_info | clarify |
| G07_compare_latest_correction | multi | wrong_arg_value | compare_research |
| G08_cancel_send | multi | wrong_boundary | no_tool |
| G09_untrusted_draft_instruction | multi | wrong_boundary | citation_audit |
| G06_board_compare_correct_window_and_count | multi | wrong_arg_value | research_board |

Run nhóm đã ghi: [OpenRouter v6: 10/10](../../starter_v0/runs/v6_B_group_openrouter_20261110T234157985676.json)
và [Groq: 10/10](../../starter_v0/runs/cp3-research-board-v2_B_group_groq_20261111T022506173733.json).
Hai run này dùng bộ case/snapshot tại thời điểm chạy, không phải điểm của bộ hiện tại.
Bộ Groq được đóng băng tại [eval_group.frozen.json](../../starter_v0/artifacts/cp4_cp5/eval_group.frozen.json).

### B4. Live chat và UI

[Phiên Đinh Phúc Diên trực tiếp chạy](../../starter_v0/transcripts/v4_openrouter_20261110T214232005322.transcript.json)
có 5 lượt: nghiên cứu RAG → hỏi URL còn thiếu → fetch đúng URL arXiv → hỏi duyệt
bản nháp Telegram → hủy gửi. Lượt đầu gọi investigate hai lần; transcript giữ
nguyên để thể hiện lỗi lặp thực tế. Phiên này không gửi Telegram.

[Phiên Groq 20b](../../starter_v0/transcripts/cp3-research-board-v2_groq_20261111T023231396178.transcript.json)
là prompt synthetic qua API thật: research_board/format → hỏi URL → fetch → hỏi
đích gửi; [phiên tiếp nối](../../starter_v0/transcripts/cp5_confirmation_20b_20261111T024124787005.transcript.json)
hỏi xác nhận nhưng chưa gửi. Lượt 120b bị quota 429 được giữ nguyên, không tính
là hoàn tất hội thoại: [quota_event.json](../../starter_v0/artifacts/cp4_cp5/quota_event.json).

UI từng được kiểm tra qua AppTest với API thật: [chat/board](../../starter_v0/artifacts/cp4_cp5/ui_chat_and_board_live.json),
[query comparison](../../starter_v0/artifacts/cp4_cp5/ui_apptest_live.json),
[pipeline](../../starter_v0/artifacts/cp5_pipeline/live_pipeline_check.json).
Kiểm tra này không thay thế visual QA hoặc phản hồi người ngoài nhóm.

### B5a. Tool, test và bản nộp

Mỗi tool mới có `tool.py`, `TOOL.md`, frontmatter, registry và declaration;
`tests/test_tools_todo.py` có ít nhất 3 hàm test cho từng tool.
Test dùng HTTP/provider giả và chặn network thật. Các regression kiểm tra input xấu,
partial/timeout, URL có nghĩa, provenance, citation, tool error, gửi đúng bản nháp,
hủy/reset phiên và snapshot payload model.

Kiểm tra cuối trong AI20k: **407 passed, 0 failed, 0 skipped**. Chi tiết: [validation.json](../../starter_v0/analysis/validation.json)
và [JUnit XML](../../starter_v0/analysis/pytest_final.xml).
Log checkpoint trong `artifacts/cp*/` và `analysis/pytest.xml` giữ nguyên cho đối chiếu lịch sử.

### B5. Bonus

- Có 5 tool mới, mỗi tool có ít nhất 3 test.
- Kết quả test cuối được dẫn ở B5a; không dùng TODO/skip để bỏ qua test.
- Chưa có bằng chứng gửi Telegram thật; không nhận bonus gửi tin.
- Chưa chạy Small Local Model Challenge; hỗ trợ Ollama không đồng nghĩa có kết quả local.

## 5. Khó khăn và giới hạn

API/quota có thể lỗi; model route đúng vẫn có thể nhận tool error hoặc tóm tắt sai.
Coverage/domain/score của search không xác minh nội dung, tính độc lập hoặc độ mới.
Cloudflare Quick Tunnel phụ thuộc máy và process đang chạy. V7 đã kiểm tra offline,
chưa đo lại model/API; cần chạy lệnh trong [README.md](../../starter_v0/README.md) để ghi run mới.

Phạm vi code hiện có gồm thay đổi `agent.py`/`chat.py` để chặn gửi và giữ log khi lỗi,
cùng Groq provider và lựa chọn CLI. Đây là phần ngoài danh sách chỉnh prompt/tool
của starter; không nhận là mọi file đều nằm trong danh sách được sửa. Logic chấm
điểm và nội dung case cố định không được sửa để nâng điểm.

## 6. Đóng góp và công cụ AI

Đóng góp thực tế, bằng chứng và báo cáo theo MSSV nằm trong [TEAM.md](../../TEAM.md).
Codex hỗ trợ code, test, phân tích log và tài liệu. Thành viên tự trình bày phần
đã hiểu, đã tự kiểm tra và tự đánh giá trong báo cáo cá nhân; không bịa commit,
transcript, metric hoặc lời nhận xét người dùng.

## 7. B6 — Hướng cải thiện

Đo lại v7 trên bộ case chốt; review tay câu trả lời và chất lượng nguồn; kiểm tra
browser/mobile và thử với người ngoài nhóm. Theo dõi lỗi API riêng với routing,
tránh chạy nhiều lần rồi chỉ chọn điểm cao. Nguồn chỉ được xem là bằng chứng trong
phạm vi excerpt/URL đã quan sát, không phải kết luận đã kiểm chứng.

## 8. Tham khảo

[Yêu cầu bài](../../README.md), [quy tắc](../../RULES.md), [rubric](../../RUBRIC.md),
[tool contract](../../starter_v0/tools/README.md), [runbook](../../starter_v0/RUNBOOK.md),
[version log](../../starter_v0/artifacts/version_log.csv).
