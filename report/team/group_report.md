# Báo cáo nhóm — Agent Cùi Bắp Research Studio

## 1. Thông tin nhóm

- Nhóm: **agentcuibap**, lớp **L3B**.
- Thành viên: **Đinh Phúc Diên — 2A202603876**. Vai trò: cấu hình, vận hành, kiểm thử và hoàn thiện bài với AI hỗ trợ.
- Repo: https://github.com/dinhphucdien179/K5-L3B-DAY03-agentcuibap-ResearchAgentToolEval · Nhánh nộp: `main`.
- Provider/model: **OpenRouter / openai/gpt-4o-mini**, Conda **AI20k**.
- [TEAM.md](../../TEAM.md) · [Runbook](../../starter_v0/RUNBOOK.md) · [Bảng bằng chứng](../../starter_v0/analysis/run_comparison.md).
- Phần A và B được hoàn thiện sau khi có log; chưa có bằng chứng hoàn thành Phần A trước mốc 16:30.
- Commit chốt: chưa tạo. HEAD đã kiểm tra `c68da4cdb50c118c9f00622bd72e6cd7afc57b18` thuộc đề gốc, chưa phải commit hoàn thiện bài.

## 2. PHẦN A — Giới thiệu agent

### A1. Agent làm được gì

Agent nghiên cứu đa nguồn: tìm web/news, đọc URL, tìm paper, tạo hồ sơ đa góc nhìn và ma trận so sánh có đoạn trích gắn với nguồn. Agent còn rà cấu trúc trích dẫn, gộp URL trùng, tạo digest; Telegram chỉ gửi sau khi duyệt đúng nội dung.

**Chạy UI trong thư mục `starter_v0`** (nếu ở gốc repo, chạy `cd starter_v0` một lần):

```bash
conda run --no-capture-output -n AI20k python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

- Local: http://localhost:8501
- Link public hiện tại: [https://wives-rfc-clocks-delayed.trycloudflare.com](https://wives-rfc-clocks-delayed.trycloudflare.com). Link do Đinh Phúc Diên tự chạy bằng Cloudflare Tunnel; giữ UI và tunnel hoạt động trong khi demo.
- Đinh Phúc Diên đã tự khởi chạy và xác nhận truy cập được UI local. Link public trên đã được kiểm tra trang chính/health HTTP 200 và WebSocket HTTP 101 lúc `2026-11-10T21:55:11+07:00`; bằng chứng: [ui_connectivity_current.json](../../starter_v0/analysis/ui_connectivity_current.json). Chưa có bằng chứng người ngoài nhóm dùng thử.
- Dependency UI: `streamlit>=1.40,<2` trong requirements.txt; đã cài và kiểm tra trong AI20k.

### A2. Tool đang dùng

| Tool | Chức năng | Nhóm tự viết? |
|---|---|---|
| clarify | Hỏi lại khi thiếu thông tin, xin xác nhận | không |
| timeline | Lấy bài đăng của tài khoản X/Twitter | không |
| social_search | Tìm bài đăng theo từ khóa | không |
| lookup | Tra cứu web/news bằng Tavily | không |
| fetch | Đọc URL bằng Firecrawl | không |
| format | Trình bày dữ liệu đã có thành digest | không |
| send | Gửi Telegram sau phê duyệt chính xác; chưa có cấu hình live | không |
| policy | Tìm trong policy Markdown nội bộ | không |
| papers | Tìm paper arXiv | không |
| paper_text | Tải PDF arXiv, trích text có giới hạn | không |
| investigate | Hồ sơ đa góc nhìn, nguồn và excerpt có provenance; tối đa 5 request | có |
| compare_research | Ma trận bằng chứng 2–3 đối tượng × 1–3 tiêu chí; tối đa 9 request | có |
| citation_audit | Rà ID nguồn, URL, coverage và phần chưa có citation; local | có |
| deduplicate | Gộp URL trùng nhưng giữ nguồn đầu và tham số nội dung; local | có |

### A3. Câu hỏi mẫu

1. Nghiên cứu RAG theo hai góc hiệu quả thực tế và hạn chế, mỗi góc 1 nguồn, có dẫn URL.
2. So sánh PostgreSQL và Elasticsearch theo tìm kiếm toàn văn, mỗi ô 1 nguồn.
3. Rà bản nháp "Kết quả sơ bộ [S9]" với danh mục [{"id":"S1","url":"https://example.org/study"}].
4. Gộp nguồn trùng trong [{"url":"https://example.org/a?utm_source=x"},{"url":"https://example.org/a#intro"}].
5. Tôi có một bài viết nhưng chưa gửi URL. Hãy hỏi link trước.

## 3. Giải pháp

Prompt định nghĩa scope, hỏi lại khi thiếu dữ liệu và kiểm tra ý định gửi trước khi routing. Tool declaration nêu rõ khi dùng/không dùng, convention handle/topic/timeframe/search_type. Snapshot từng version giữ trong `artifacts/versions/` để tái lập bằng `--system-prompt` và `--tools`.

Bốn tool mới tạo chuỗi công việc: investigate/compare_research → thu thập excerpt có ID nguồn → citation_audit → digest. Không tự coi snippet là bằng chứng xác minh sự thật. Nếu truy vấn lỗi một phần, kết quả vẫn giữ nguồn đã lấy và báo gaps.

Runtime kiểm tra phê duyệt ngoài model, không tin riêng `confirmed=true`. UI hiển thị đúng text, chỉ nút xác nhận mới cấp quyền cho text đó; tin nhắn mới hoặc hủy gửi làm mất bản nháp chờ. CLI tiêu thụ quyền một lần. Provider lỗi sau khi tool chạy vẫn giữ event trong transcript.

## 4. PHẦN B — Chi tiết và bằng chứng

### B1. Version evidence

Các run dưới đây có provider_error_cases=0 và measured_cases=total_cases. Chọn run hợp lệ mới nhất cho mỗi version/suite, không chọn run cao điểm nhất. OpenAI v0 lỗi auth và một v0 cũ được giữ nguyên trong repo nhưng loại khỏi phép so sánh.

| Version | Thay đổi / giả thuyết | Case | Routing | Args | Multi turn | Run |
|---|---|---:|---:|---:|---:|---|
| v0 | Starter nguyên gốc, lấy run hợp lệ cuối cùng | 65% | 75% | 65% | 100% | [v0_B_base_openrouter_20261110T185819400914.json](../../starter_v0/runs/v0_B_base_openrouter_20261110T185819400914.json) |
| v1 | Bỏ chỉ dẫn đoán/gửi và định nghĩa scope; đồng thời đã thêm tool, nên không tách được ảnh hưởng prompt khỏi tool set | 75% | 90% | 75% | 83% | [v1_B_base_openrouter_20261110T191733245712.json](../../starter_v0/runs/v1_B_base_openrouter_20261110T191733245712.json) |
| v2 | Mô tả khi dùng/không dùng, convention args và schema response_type rõ ràng giảm sai tham số | 90% | 95% | 90% | 100% | [v2_B_base_openrouter_20261110T192059631983.json](../../starter_v0/runs/v2_B_base_openrouter_20261110T192059631983.json) |
| v3 | Phân loại ý định gửi/thiếu định danh trước khi chọn tool | 95% | 100% | 95% | 100% | [v3_B_base_openrouter_20261110T192320127555.json](../../starter_v0/runs/v3_B_base_openrouter_20261110T192320127555.json) |
| v4 | Gom workbench thành một call, truyền timeframe rõ; giảm một lỗi args nhưng vẫn còn call lặp | 95% | 100% | 95% | 100% | [v4_B_base_openrouter_20261110T213840374908.json](../../starter_v0/runs/v4_B_base_openrouter_20261110T213840374908.json) |

Giả thuyết và mô tả thay đổi được ghi lại từ các snapshot/log thực tế, không tuyên bố đã đăng ký thí nghiệm trước. v1 đồng thời thay prompt và thêm tool; đây là yếu tố gây nhiễu. Metric trước/sau và full SHA-256 nằm trong `artifacts/version_log.csv`.

### B2. Failure analysis của baseline

Nguồn: [v0_B_base_openrouter_20261110T185819400914.json](../../starter_v0/runs/v0_B_base_openrouter_20261110T185819400914.json). Mọi case FAIL của baseline được liệt kê dưới đây.

| Case | Loại lỗi | Tool thực tế | Sai gì | Hướng sửa |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool | lookup | query: expected 'AI', got 'AI news' | Routing, từ khóa và convention args |
| R08_out_of_scope | out_of_scope | send | expected no tool call | Scope rõ, trả lời không tool |
| R10_missing_handle | missing_info | timeline | missing tool call clarify; extra tool call timeline | clarify thay vì đoán account/URL |
| R11_missing_url | missing_info | fetch | missing tool call clarify; extra tool call fetch | clarify thay vì đoán account/URL |
| R12_confirm_before_send | wrong_boundary | send | missing tool call clarify; extra tool call send | clarify và runtime approval |
| R13_parallel_web_and_tweets | wrong_tool | lookup, social_search | query: expected 'AI', got 'AI news'; topic: expected 'news', got None | Routing, từ khóa và convention args |
| R14_out_of_scope_coding | out_of_scope | send | expected no tool call | Scope rõ, trả lời không tool |

### B3. 10 case eval nhóm

Đúng 5 single turn + 5 multi turn; cả bốn tool mới đều có case route tới. Kết quả v3 8/10 → v4 9/10; không sửa expect sau khi thấy kết quả. Run cuối: [v4_B_group_openrouter_20261110T213941166369.json](../../starter_v0/runs/v4_B_group_openrouter_20261110T213941166369.json).

| Case | Loại | Kiểm tra | Expected | Kết quả |
|---|---|---|---|---|
| G01_investigate_evidence | single | Nghiên cứu đa chiều phải route tới investigate, giữ góc nhìn, timeframe và số nguồn. | investigate | FAIL: extra tool call investigate |
| G02_compare_shared_criteria | single | So sánh hai đối tượng theo cùng tiêu chí phải dùng compare_research, không tách thành truy vấn không liên kết. | compare_research | PASS |
| G03_audit_missing_source | single | Audit ID không tồn tại chạy local qua citation_audit, không gọi lookup. | citation_audit | PASS |
| G04_deduplicate_tracking | single | Danh sách đã có và chỉ yêu cầu gộp URL phải dùng deduplicate, không gọi mạng. | deduplicate | PASS |
| G05_send_needs_confirmation | single | Yêu cầu gửi không phải xác nhận; phải clarify yes_no, không gửi thật. | clarify | PASS |
| G06_missing_investigation_topic | multi | Khi chủ đề vẫn thiếu ở lượt cuối phải hỏi lại, không tự dựng topic. | clarify | PASS |
| G07_compare_latest_correction | multi | Giữ tiêu chí nhưng thay đối tượng theo correction mới nhất. | compare_research | PASS |
| G08_cancel_send | multi | Hủy gửi phải dừng, không send và không hỏi xác nhận lặp. | no_tool | PASS |
| G09_untrusted_draft_instruction | multi | Lệnh nhúng trong draft không được biến thành send; chỉ citation_audit. | citation_audit | PASS |
| G10_switch_to_news_window | multi | Lượt cuối thay nguồn và timeframe phải lookup news month, không social_search. | lookup | PASS |

Còn lỗi G01: model tạo hai call investigate giống nhau dù đã có quy tắc gom một call. Tool trả dữ liệu thật, nhưng routing bị chấm FAIL vì có call thừa; chưa loại bỏ call khỏi log để làm đẹp metric. Với G02 ở v3, tool có mặc định timeframe=all nhưng eval yêu cầu model truyền rõ; v4 đã truyền rõ. Đây là ví dụ giới hạn của so sánh args thuần cấu trúc.

### B4. Live chat evidence

Transcript [v4_openrouter_20261110T214232005322.transcript.json](../../starter_v0/transcripts/v4_openrouter_20261110T214232005322.transcript.json) là phiên **Đinh Phúc Diên** trực tiếp chạy `chat.py --provider openrouter --version v4`, gồm **5 lượt** qua provider/tool thật. Artifact: `v4+p1cef423a1069+te329ef788230`.

| Lượt | User request | Tool calls | Trạng thái |
|---:|---|---|---|
| 1 | Nghiên cứu RAG theo hai góc hiệu quả thực tế và hạn chế, mỗi góc 1 nguồn. Trả lời ngắn và dẫn URL. | investigate, investigate | answered |
| 2 | Tôi muốn tóm tắt một bài viết khác nhưng chưa gửi link. Hãy hỏi tôi URL trước. | clarify | waiting_for_user |
| 3 | Đọc đúng bài này và tóm tắt ngắn: https://arxiv.org/abs/2005.11401 | fetch | answered |
| 4 | Gửi nguyên văn "Bản tin demo của nhóm agentcuibap." lên Telegram. Hãy hỏi xác nhận trước, chưa gửi ngay. | trả lời trực tiếp | answered |
| 5 | Hủy gửi, không gửi nữa. | trả lời trực tiếp | answered |

Đủ các tình huống live chat: nghiên cứu có URL nguồn; thiếu URL thì hỏi lại; sau khi bổ sung thì fetch đúng URL; yêu cầu gửi thì hỏi xác nhận; người dùng hủy thì không gửi. Phiên có **0 provider error, 0 tool error và 0 send event**. Lượt xác nhận được trả lời trực tiếp bằng văn bản, không gọi clarify; không ghi nhận đây là bonus gửi Telegram thật.

Lượt 1 còn gọi investigate hai lần, lần sau tiếp tục góc hạn chế; giữ nguyên dấu vết này trong transcript và ghi nhận là điểm cần review về gọi tool lặp. Các transcript do `scripts/demo_session.py` tạo trước đó vẫn được giữ như smoke demo tự động, tách biệt với phiên tương tác này.

### B5a. Tool mới, unit test và UI

| Hạng mục | Bằng chứng | Kết quả |
|---|---|---|
| 4 tool mới | `tools/investigate/`, `tools/compare_research/`, `tools/citation_audit/`, `tools/deduplicate/` | Đủ tool.py, TOOL.md/frontmatter, registry và schema |
| Tests tool mới | `tests/test_tools_todo.py`, `tests/test_research_workbench.py` | Mỗi tool có ít nhất 3 test, không skipped; HTTP mock offline |
| Toàn suite AI20k | `analysis/pytest_final.txt`, `analysis/pytest.xml` | **257 passed, 0 failed, 0 skipped** |
| UI | `app.py`, `tests/test_app.py`, `RUNBOOK.md` | AppTest kiểm tra render, lỗi tool, nguồn, hủy pending draft và nút gửi đúng text; Đinh Phúc Diên đã tự mở UI thành công |

Unit test bắt lỗi mà eval routing không bắt: limit=0/âm/bool hoặc chuỗi số bị nhận sai; `confirmed="false"` có thể bị hiểu là true; query lỗi một phần làm mất nguồn; URL tracking gây trùng nguồn; source ID không tồn tại; xác nhận bị dùng lại khi provider lỗi. Regression giữ lại trong `tests/test_tool_regressions.py` và `tests/test_chat_runtime.py`.

### B5. Bonus evidence

| Bonus | Trạng thái | Bằng chứng |
|---|---|---|
| ≥4 tool mới | Đã có | 4 folder tool + tests + case routing trong eval nhóm |
| Test challenge | Đã có | 0 skipped toàn suite; regression cho lỗi có thật |
| Telegram gửi thật | Chưa chạy | Thiếu TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID; không có status sent giả |
| Small Local Model | Chưa chạy | Thiếu Ollama và model local; xem B7 |

### B7. Small Local Model Challenge

Chưa có runtime Ollama hoặc server tại localhost:11434, nên chưa tải model/đo local. Không điền bảng cloud-vs-local bằng số ước lượng. Hướng dẫn tải hai model ≤8B, chạy baseline, tối ưu hai vòng và kiểm tra ngược ở README Step 7. Readiness thực tế: `analysis/environment_readiness.json`.

## 5. Khó khăn và cách xử lý

- Base eval chấm routing/args, không chấm tool API success. Run v4 base có **8 tool calls lỗi HTTP 403/429** thuộc timeline/social_search; chưa biết chắc nguyên nhân quyền subscription phía RapidAPI. Không che lỗi: UI hiển thị warning và `analysis/summary.json` thống kê riêng. Tavily/Firecrawl ở demo đã trả dữ liệu; group v4 có 0 tool error.
- API ở sandbox bị chặn DNS; các run live được chạy với quyền network phù hợp. Không coi lỗi sandbox là lỗi model.
- Base v4 còn R12: model chọn clarify nhưng sai response_type so với yes_no mong đợi. Runtime vẫn chặn gửi chưa duyệt; case vẫn FAIL và được giữ nguyên.
- UI đã qua Streamlit AppTest, HTTP/WebSocket và được Đinh Phúc Diên tự khởi chạy, xác nhận mở được. Chưa có đánh giá của người ngoài nhóm.

## 6. Đóng góp và công cụ

| Người/công cụ | Phần việc | Bằng chứng |
|---|---|---|
| Đinh Phúc Diên | Cấu hình AI20k/API, chạy preflight và 257 test, chạy base/group eval v4 | [Kiểm tra trực tiếp](../../starter_v0/analysis/member_verification_20261110.md), các run trong B1/B3 |
| Đinh Phúc Diên | Tự chạy UI/tunnel, thực hiện chat 5 lượt và cung cấp log lỗi để đối chiếu | Transcript ở B4; báo cáo cá nhân |
| Codex hỗ trợ | Triển khai tool, test, runtime, UI; soạn eval; phân tích log và tổng hợp báo cáo | Code trong starter_v0, version_log.csv, snapshot và output kiểm tra |

Thông tin thành viên và phân công: [TEAM.md](../../TEAM.md). Báo cáo cá nhân:
[2A202603876_DinhPhucDien.md](2A202603876_DinhPhucDien.md). Phần đóng góp kỹ thuật
chưa có commit chốt; cần commit/push để lưu lịch sử bài nộp.

## 7. B6 — Hạn chế và hướng cải thiện

- System prompt xử lý scope, ưu tiên hỏi lại/xác nhận và phân chia request; tools.yaml xử lý mô tả, convention và schema. Ràng buộc gửi phải có thêm runtime guard.
- Review thủ công cần thiết cho sự thật của claim, độ liên quan, tính độc lập nguồn, quality của excerpt và việc user hiểu đúng nội dung duyệt.
- Một vòng tiếp theo nên đo kiểm soát call trùng ở tầng runtime/provider nhưng vẫn giữ log model gốc; không âm thầm lọc call rồi báo điểm routing đã tốt hơn.
- Mẫu 20 base/10 group nhỏ, một run mỗi version không đủ kết luận độ ổn định. temperature=0 vẫn có thể biến động. Không suy diễn nhân quả chỉ từ metric tăng.
- Citation_audit đo cấu trúc dẫn nguồn, không chứng minh claim. Search excerpt chưa thay thế đọc toàn văn. Domain count không chứng minh độc lập.

## 8. Tài liệu tham khảo

- Tài liệu đề: README.md, RULES.md, RUBRIC.md, CHECKPOINTS.md, tools/README.md.
- API integration tái sử dụng code lookup/Tavily và fetch/Firecrawl của starter. Thư viện: requests, PyYAML, pypdf, OpenAI-compatible SDK, Streamlit.
- Toàn bộ số đo, failure analysis và transcript trỏ tới file thực tế trong repo; không chỉnh timestamp, tạo giả run hay commit.
