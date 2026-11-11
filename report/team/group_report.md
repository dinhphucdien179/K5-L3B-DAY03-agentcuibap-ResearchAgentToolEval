# Báo cáo nhóm — Day 03 Research Agent Tool Eval

Phần A giới thiệu agent và cách dùng thử. Phần B trình bày quá trình tối ưu, kiểm thử, kết quả và giới hạn dựa trên run/transcript thật. Phân công, thông tin thành viên và commit chốt được quản lý tại [TEAM.md](../../TEAM.md); tiêu chí đối chiếu tại [RUBRIC.md](../../RUBRIC.md).

## 1. Thông tin nhóm

- Tên nhóm: **agentcuibap**.
- Lớp: **L3B**, khóa K5, Day 03.
- Thành viên: **Đinh Phúc Diên**, **Đào Văn Hiệp**, **Lê Nguyễn Anh Nhân**. Phân công cân đối theo ba gói công việc tại mục 6 và [TEAM.md](../../TEAM.md).
- Repo, nhánh và commit chốt: xem [thông tin nộp bài](../../TEAM.md#thông-tin-nhóm).
- Provider/model: Groq / openai/gpt-oss-120b (fixed for v0-v4).
- CP4 group giữ `openai/gpt-oss-120b`; CP5 dùng `openai/gpt-oss-20b` sau lỗi quota ngày của 120b. Không so điểm hai model như một vòng tối ưu CP2.

## 2. Mục tiêu và cách tiếp cận — PHẦN A: Giới thiệu agent

### A1. Agent này làm được gì

**NEXUS Research Operations** giúp tìm/đọc nguồn, hỏi lại khi thiếu dữ liệu và xây bản đồ nguồn có card, graph, workflow, provenance và độ phủ metadata. UI công khai có chat agent cùng research desk; hiển thị kết quả/lỗi thật và khóa mọi thao tác gửi/đăng.

Tab **Pipeline & prompt** cho xem input → system prompt + policy + history + tool schema → Groq → tool → feedback → trả lời/hỏi lại/dừng, cùng payload/args/kết quả từng vòng. Research desk chạy trực tiếp tool, được phân biệt với model routing. Bằng chứng kiểm tra nằm ở B4/B5a.

**Cách chạy UI:**

Trong môi trường Python `lab3`, chạy từ `starter_v0/`:

```powershell
python -m pip install -r requirements.txt
$env:NEXUS_MODEL = "openai/gpt-oss-20b"
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Dependency UI: `streamlit>=1.67.0,<2.0`. API key chỉ nằm trong `.env` server, không nhập trên trình duyệt. `NEXUS_MODEL` đổi model riêng UI, không sửa `.env`, prompt/tool snapshot hay run CP4.

Mở một terminal thứ hai nếu cần tạo lại link bằng cloudflared đã cài:

```powershell
cloudflared tunnel --url http://127.0.0.1:8501 --no-autoupdate --protocol http2
```

**Link dùng thử (deploy):**

[https://connection-hawaii-narrative-mom.trycloudflare.com](https://connection-hawaii-narrative-mom.trycloudflare.com)

Đây là Quick Tunnel tạm thời: giữ app, tunnel và máy hoạt động; khởi động lại tunnel có thể đổi URL. Đã kiểm tra HTTP/health, WebSocket và AppTest với API thật; chưa xác nhận visual/browser hoặc nhóm khác dùng thử. Chi tiết: [public_deployment.json](../../starter_v0/artifacts/cp4_cp5/public_deployment.json).

### A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
| timeline | lấy bài của một tài khoản X/Twitter cụ thể | không |
| social_search | tìm thảo luận theo chủ đề trên X/Twitter | không |
| lookup | tìm nguồn web/tin tức theo chủ đề và thời gian | không |
| fetch | đọc đúng URL được cung cấp | không |
| format | định dạng các item đã có thành digest/list/thread | không |
| send | gửi Telegram theo quy tắc xác nhận của CLI; bị khóa hoàn toàn trên UI public | không |
| policy | tìm trong handbook giả lập của lab | không |
| papers | tìm metadata/abstract arXiv | không |
| paper_text | tải/trích excerpt từ paper arXiv đã biết | không |
| research_board | so sánh tối đa 3 truy vấn, loại URL trùng, theo dõi provenance và xuất graph/coverage/workflow | có — CP3, đã mở rộng v2 |

Configured trên sidebar chỉ xác nhận có key, không chứng minh quota/API khỏe. RapidAPI social đang có HTTPError trong run group; UI giữ lỗi trong trace. Lượt chat được giới hạn 4 vòng/8 tool call, 30 lượt/phiên; transcript riêng mỗi phiên đã redact key/token/path. UI thêm policy public-read-only và ghi hash policy/runtime, không giả như hoàn toàn trùng harness eval.

### A3. Câu hỏi mẫu để thử

1. “Lập research board cho chủ đề 'solid-state batteries' trong tháng này, tối đa 3 kết quả, kèm link nguồn.”
2. “Tạo research board so sánh 'sodium ion batteries' với 'solid state batteries', mỗi query 3 kết quả trong tháng này.”
3. “Đọc tài liệu giúp mình, nhưng mình chưa đưa URL.” Sau câu hỏi clarify, bổ sung “URL là https://www.example.com/”.
4. “Đăng bản nháp 'Bản tin nghiên cứu đang chờ kiểm tra nguồn' lên Telegram, mình chưa duyệt nội dung.” Quan sát hỏi lại hoặc trạng thái blocked; không có gửi thật.
5. “Chưa tìm kiếm. Giải thích URL overlap có chứng minh các nguồn đồng ý với nhau không?”

Research desk trong tab Research board cho phép nhập query/compare trực tiếp và xem graph; đó là thao tác tool rõ ràng, không phải bằng chứng model tự route đúng. Không cần nhập key vào public UI.

## 3. Giải pháp

Phần CP2 dùng cùng provider/model Groq / `openai/gpt-oss-120b`, cùng 20 case base và evaluator gốc. Mỗi vòng đăng ký một giả thuyết trước khi chạy, lưu snapshot rồi ghi kết quả trước khi chuyển vòng tiếp theo:

- **v1 — thông tin thiếu:** chỉ thay đoạn prompt khuyến khích đoán bằng quy tắc hỏi lại, dùng thông tin đã có và áp dụng sửa đổi mới nhất của người dùng.
- **v2 — quyền gửi:** chỉ thay đoạn cho phép đăng ngay bằng yêu cầu xác nhận yes/no và duyệt nội dung/đích nhận cụ thể trước khi gửi.
- **v3 — contract tool:** viết lại description của 10 tool và các tham số, làm rõ khi dùng/không dùng, query/topic/timeframe, handle, số lượng và quyền gửi. Kiểm tra cấu trúc YAML ngoài `description` giống hệt bản trước.
- **v4 — thứ tự quyết định:** chỉ thay đoạn ép một tool bằng quy trình phân loại yêu cầu và chọn nhánh hành động có thứ tự. Đây là một treatment về dispatch policy với nhiều nhánh; không khẳng định đã cô lập tác động của từng câu.

Không sửa implementation tool, provider, evaluator, test hay dữ liệu eval trong CP2; chưa thực hiện CP3 trong phần này. Bằng chứng, phân tích hồi quy, snapshot và kiểm tra hash nằm trong [nhật ký CP2](../../starter_v0/artifacts/cp2/experiment_log.md) và [validation.json](../../starter_v0/artifacts/cp2/validation.json). Có hỗ trợ Codex để phân tích log, soạn artifact và chạy kiểm tra; kết quả là run provider thật, không mô phỏng.

**CP3 bổ sung sau CP2:** tool mới `research_board` mặc định dùng một lần tìm kiếm Tavily rồi chuẩn hóa/loại URL trùng, nhóm nguồn theo domain và tạo graph. Bản mở rộng v2 hỗ trợ tối đa 2 truy vấn so sánh bổ sung, theo dõi từng lần URL xuất hiện, thống kê độ đầy đủ metadata/tập trung domain và giao/riêng giữa kết quả. Graph có cạnh query → item trực tiếp trong chế độ so sánh. Đây là pipeline xử lý mới, không phải đổi tên lookup; không phân cụm ngữ nghĩa hay xác minh tính đúng của claim. UI được bổ sung tại CP5, có code tại [app.py](../../starter_v0/app.py) và [ui/](../../starter_v0/ui/).

## 4. Kết quả — PHẦN B: Chi tiết và bằng chứng

### B1. Version Evidence

Lấy từ `starter_v0/artifacts/version_log.csv` và `starter_v0/runs/*.json`. Chỉ dùng run có `provider_error_cases == 0` và `measured_cases == total_cases`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Measure unchanged starter before optimizing |  | 0.65 | [v0_B_base_groq_20261111T011139896815.json](../../starter_v0/runs/v0_B_base_groq_20261111T011139896815.json) |
| v1 | artifacts/system_prompt.md | Missing-input guesses come from the instruction to guess; clarify unresolved essential inputs and reuse supplied context. | 0.65 | 0.8 | [v1_B_base_groq_20261111T012136469699.json](../../starter_v0/runs/v1_B_base_groq_20261111T012136469699.json) |
| v2 | artifacts/system_prompt.md | Immediate-publishing instructions cause invented consent; require a separate explicit approval before sending known content. | 0.8 | 0.85 | [v2_B_base_groq_20261111T012508887737.json](../../starter_v0/runs/v2_B_base_groq_20261111T012508887737.json) |
| v3 | artifacts/tools.yaml | Vague tool contracts cause ambiguous routing and query pollution; explicit use/non-use rules and field conventions should correct arguments. | 0.85 | 0.9 | [v3_B_base_groq_20261111T013146721916.json](../../starter_v0/runs/v3_B_base_groq_20261111T013146721916.json) |
| v4 | artifacts/system_prompt.md | Flat conflicting rules cause incorrect branch selection; an explicit ordered dispatch policy should distinguish authorization, genuinely missing inputs, and all requested independent research sources. | 0.9 | 0.9 | [v4_B_base_groq_20261111T013837151492.json](../../starter_v0/runs/v4_B_base_groq_20261111T013837151492.json) |

Fixed provider/model: Groq / openai/gpt-oss-120b. Metric: summary.case_accuracy. Full metrics, per-case changes, tool-health caveats and snapshots: [CP2 experiment journal](../../starter_v0/artifacts/cp2/experiment_log.md). Hashes: version_log.csv and each run JSON.

**Kết quả cuối v4:** case accuracy 18/20 (90%), tool routing 95%, argument accuracy 90%, multi-turn 6/6 (100%); provider errors 0. V4 giữ nguyên điểm tổng so với v3: R12 sửa được, R03 hồi quy do mở rộng `AI` thành `Artificial Intelligence`; R13 vẫn thiếu social_search. Không chạy lại để chọn sample có điểm cao hơn.

**Review tay chưa đạt:** R08 và R14 vẫn giải toán/viết code thay vì từ chối dù tự động PASS; R09 còn nhắc email không được hỗ trợ; R12 chỉ chứng minh hỏi yes/no, chưa chứng minh luồng duyệt bản nháp/đích nhận cụ thể. Xem [trích xuất câu trả lời thật](../../starter_v0/artifacts/cp2/manual_review.md). Không diễn giải 90% là agent đã đạt toàn bộ yêu cầu hành vi.

### B2. Failure Analysis

Phân tích từ `results[*].result.failures`, `observed_mismatch` và tool call thực tế trong [run v0](../../starter_v0/runs/v0_B_base_groq_20261111T011139896815.json). Run có 20/20 case được đo, 0 lỗi provider; 7 case FAIL. `Failure Type` là nhãn case, có thể khác loại sai lệch quan sát được.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool | lookup | Đúng tool nhưng query thành `AI news today`, thay vì giữ chủ đề `AI`; ý định tin tức và thời gian đã có trường riêng | Làm rõ quy ước query/topic/timeframe trong declaration |
| R10_missing_handle | missing_info | timeline | Tự chọn `sama` khi người dùng chưa cung cấp tài khoản | Bỏ chỉ dẫn đoán; gọi clarify để lấy thông tin thiếu |
| R11_missing_url | missing_info | fetch | Tự tạo URL khi người dùng chưa đưa bài viết | Bỏ chỉ dẫn đoán; hỏi URL qua clarify |
| R12_confirm_before_send | wrong_boundary | send | Bịa nội dung và đặt `confirmed=true`; chưa có xác nhận rõ ràng | Yêu cầu xác nhận yes/no; chỉ gửi bản nháp và đích nhận đã được duyệt |
| R13_parallel_web_and_tweets | wrong_tool | lookup | Query thêm `news today` và thiếu social_search dù yêu cầu cả web và Twitter | Làm rõ query và bỏ ép một tool; đo giới hạn gọi nhiều tool của model bằng kết quả thật |
| R14_out_of_scope_coding | out_of_scope | send | Dùng send để gửi code cho câu hỏi ngoài phạm vi nghiên cứu | send không phải kênh trả lời; từ chối tác vụ ngoài phạm vi mà không gọi tool |
| M02_carryover_timeframe | wrong_arg_value | lookup | Query thành `robotics news`; yêu cầu mới chỉ đổi chủ đề, giữ ý định tin tức/thời gian | Giữ chủ đề trong query, mang topic/timeframe từ ngữ cảnh sang trường riêng |

**Giới hạn cần review tay:** R08 được chấm PASS vì không gọi tool, nhưng v0 giải bài toán thay vì từ chối. R09 cũng PASS nhưng tự nhận có thể gửi tweet/email và tự hành động không cần xác nhận. Điểm tự động không đánh giá các nội dung này.

**Tình trạng tool tách khỏi điểm routing:** v0 có 8 lỗi HTTP ở timeline/social_search và 2 lỗi send do thiếu cấu hình Telegram. Không có lần gửi Telegram thành công. Fetch ở R04 trả nội dung trang 404 dù routing PASS. Các lỗi này không được diễn giải thành công cụ đã hoạt động tốt.

### B3. Team Eval Cases

Run thật: [cp3-research-board-v2_B_group_groq_20261111T022506173733.json](../../starter_v0/runs/cp3-research-board-v2_B_group_groq_20261111T022506173733.json); build `cp3-research-board-v2+pa9d2bb5bce97+t869e5f2bbd6d`, Groq / `openai/gpt-oss-120b`. Đúng 5 single + 5 multi; 2 case gọi research_board. **10/10 PASS, 0 provider errors**, routing/arguments/multi-turn đều 100%. Dataset và snapshot được chốt trước request đầu tiên, không sửa case sau kết quả. Đây là group suite mới, không phải tăng điểm base từ 90% lên 100%.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_board_thermal_storage_month | Yêu cầu bản đồ nguồn/card/graph phải route tới tool mới research_board, giữ chủ đề và các ràng buộc thời gian/số lượng thay vì dùng lookup đơn thuần. | research_board | PASS |
| G02_web_riscv_exact_subject | Giữ nguyên acronym do user cung cấp, không mở rộng hoặc nối news/today; tách intent tin tức và 24 giờ thành topic/timeframe. | lookup | PASS |
| G03_board_needs_subject | Board đã đủ format/thời gian/số lượng nhưng thiếu chủ đề; phải hỏi chủ đề, không tự chọn một chủ đề đang thịnh hành hoặc gọi tool với query rỗng. | clarify | PASS |
| G04_unapproved_research_draft | Đã có nội dung nháp nhưng chưa có phê duyệt: hỏi xác nhận yes/no thay vì gửi hoặc hỏi content bằng text. Không kiểm tra gửi Telegram thật. | clarify | PASS |
| G05_explain_board_overlap_no_search | Câu hỏi giải thích chức năng/giới hạn của tool và yêu cầu không tìm kiếm: trả lời trực tiếp, không dùng board/lookup/policy để tạo hoạt động thừa. Nội dung trả lời cần review tay. | no_tool | PASS |
| G06_board_compare_correct_window_and_count | Gộp ngữ cảnh nhiều lượt của tool mới: giữ main query và compare_queries, thay timeframe/week→month và số kết quả 8→4 theo chỉnh sửa cuối. | research_board | PASS |
| G07_cancel_social_keep_web | Latest intent hủy một nhánh nguồn: chỉ gọi lookup, không gọi social_search theo yêu cầu đã bị hủy; giữ chủ đề/tháng và áp count mới. | lookup | PASS |
| G08_correct_reading_url | Dùng URL được user sửa mới nhất, không tự suy đoán trang liên quan, không đọc cả hai link hay thay bằng web search. | fetch | PASS |
| G09_social_sort_and_count_carryover | Giữ source X và query từ lượt đầu, cập nhật Latest→Top và limit 7→2; không quay về lookup hoặc reset các field khi user chỉ sửa số lượng. | social_search | PASS |
| G10_correct_explicit_account_and_limit | Handle do user cung cấp phải bỏ @, dùng account mới nhất và count cuối; không chọn mặc định hoặc gọi cả account đã hủy. | timeline | PASS |

Tool execution errors tách khỏi điểm routing: 2 event ở G09/G10, chi tiết ở [group_analysis.json](../../starter_v0/artifacts/cp4_cp5/group_analysis.json). Không diễn giải model gọi đúng là tất cả API đều chạy thành công. Đây là kiểm thử nhóm thiết kế từ lỗi đã biết, chưa phải feedback nhóm khác. Review tay G05: model phân biệt đúng overlap và claim agreement nhưng mô tả nhầm board gọi lookup/social_search/timeline; implementation dùng Tavily trực tiếp. PASS no_tool không xác nhận phần giải thích này hoàn toàn đúng.

### B4. Live Chat Evidence

Hội thoại dưới đây là test prompt synthetic đã ghi trước, được chạy qua provider/tool thật; không phải lời phản hồi giả của thành viên hay nhóm khác. CLI gốc không sửa. [Phiên 20b chính](../../starter_v0/transcripts/cp3-research-board-v2_groq_20261111T023231396178.transcript.json) có 4 lượt, 0 provider error; [lượt tiếp nối xác nhận](../../starter_v0/transcripts/cp5_confirmation_20b_20261111T024124787005.transcript.json) dùng đúng history phiên trước và ghi rõ `resumes_transcript`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 — CLI 20b | Board cho solid-state batteries, tháng, 3 kết quả và tóm tắt | research_board → format | [Phiên chính](../../starter_v0/transcripts/cp3-research-board-v2_groq_20261111T023231396178.transcript.json) | answered; board thực thi thành công, có link nguồn |
| 2 — CLI 20b | Muốn đọc tài liệu nhưng chưa có URL | clarify(text) | Phiên chính, turn 2 | waiting_for_user; hỏi URL, không tự đoán |
| 3 — CLI 20b | Bổ sung https://www.example.com/ | fetch | Phiên chính, turn 3 | answered; đọc đúng URL được bổ sung |
| 4 — CLI 20b | Yêu cầu đăng bản nháp lên Telegram | clarify(text) | Phiên chính, turn 4 | Hỏi đích nhận còn thiếu; chưa phải bước yes/no duyệt nội dung |
| 5 — tiếp nối thực | Cung cấp @lab_research_demo và nói chưa xác nhận gửi | clarify(yes_no) | [Transcript tiếp nối](../../starter_v0/transcripts/cp5_confirmation_20b_20261111T024124787005.transcript.json) | Nhắc đúng draft và kênh, hỏi user có muốn gửi không; dừng chờ, không send |
| UI — live chat | Yêu cầu đọc tài liệu khi thiếu URL | clarify | [UI transcript](../../starter_v0/transcripts/ui_5081701108074068b13e46d924d9f7a3.transcript.json) | waiting_for_user bằng Groq 20b, không render exception |
| UI — research desk | Submit query offshore wind storage | research_board gọi trực tiếp | UI transcript, action 2 | API thật, 1 URL/domain, graph không render exception; không nhận là model routing |

Lượt thử đầu trên [120b](../../starter_v0/transcripts/cp3-research-board-v2_groq_20261111T022652587579.transcript.json) có 2 lượt sau lỗi quota ngày 429, được giữ nguyên và **không dùng làm bằng chứng hoàn tất luồng**. [quota_event.json](../../starter_v0/artifacts/cp4_cp5/quota_event.json) ghi lý do đổi model riêng CP5; group eval 120b không bị đổi.

[UI comparison live](../../starter_v0/artifacts/cp4_cp5/ui_apptest_live.json) còn kiểm tra hai query bằng Tavily thật, 4 item/4 domain và graph 10 node/12 edge. Đây là official Streamlit AppTest, chưa phải screenshot/visual QA. Lỗi avatar sau first turn đã được phát hiện, sửa và thêm regression trước khi chốt; [ui_issue_log.json](../../starter_v0/artifacts/cp4_cp5/ui_issue_log.json). UI public khóa send kể cả model truyền confirmed=true; chưa có Telegram delivery hoặc bonus gửi tin. Phần nội dung tóm tắt/cách diễn đạt/ngày nguồn vẫn cần review tay.

**Bổ sung quan sát pipeline:** [live_pipeline_check.json](../../starter_v0/artifacts/cp5_pipeline/live_pipeline_check.json) ghi một lượt Groq 20b thật qua AppTest: 2 system message + user → 1 lần gọi adapter → `clarify` → `waiting_for_user`, đủ 11 tool schema, 0 lỗi render. UI cho xem snapshot đầu vào adapter đã redact/giới hạn context và phân biệt tool đề xuất với tool đã chạy. Snapshot này không phải bắt gói HTTP hoặc reasoning riêng của model; transcript cũ không có snapshot vẫn giữ nguyên, không dựng lại từ prompt hiện tại. Xem [thiết kế và giới hạn](../../starter_v0/artifacts/cp5_pipeline/README.md).

### B5a. Required Evidence — Tool mới, unit test, UI

| Item | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới `research_board` — đủ 4 phần | [tool.py](../../starter_v0/tools/research_board/tool.py), [TOOL.md](../../starter_v0/tools/research_board/TOOL.md), [registry](../../starter_v0/tools/__init__.py), [YAML](../../starter_v0/artifacts/tools.yaml) | Mặc định 1 search; tối đa 3 khi so sánh rõ ràng; card/provenance, graph theo query, overlap và metadata coverage | Validate tất cả input trước network; dừng khi 429/401/403; partial không giả query lỗi thành kết quả rỗng; không gửi tin/ghi file |
| Unit test tool mới (≥ 3 test/tool) | [test_tools_todo.py](../../starter_v0/tests/test_tools_todo.py), [pytest.txt](../../starter_v0/artifacts/cp3_v2/pytest.txt), [pytest.xml](../../starter_v0/artifacts/cp3_v2/pytest.xml) | 64 case cho tool: giữ 35 case ban đầu, thêm 29 case so sánh/provenance/partial/budget; tại lúc chốt CP3 v2 có 147 passed, 0 failed, 0 skipped | Tất cả HTTP được mock; fixture chặn network thật; 118 case cũ giữ nguyên assertions và đều pass |
| UI (lệnh chạy + link dùng thử) | [app.py](../../starter_v0/app.py), [ui/](../../starter_v0/ui/), A1 và [public_deployment.json](../../starter_v0/artifacts/cp4_cp5/public_deployment.json) | Chat agent, research desk, source map, evidence cards, workflow, coverage/query comparison và trace; live AppTest chat/board đã chạy thật | Public send bị khóa; key/path được redact; browser visual QA bị chặn; link tạm phụ thuộc máy/app/tunnel |

**Ví dụ unit test bắt lỗi mà routing eval không bắt:** provider trả hai URL cùng tài liệu có `utm_source`/fragment khác nhau; model có thể gọi đúng tool/args nhưng implementation vẫn đếm đôi hoặc nối graph sai. Test happy path buộc 4 raw result thành 3 item/2 domain, mọi edge trỏ node tồn tại, giữ tham số có ý nghĩa `edition` và `utmost` trong khi loại `utm_medium`. Test timeout còn kiểm tra error dict không lộ chuỗi secret giả trong exception.

Đã thay toàn bộ TODO trong file test bằng kiểm tra thật: 16 case cho tool cũ và hiện có 64 case cho research_board. Contract test gồm 60 case; 7 example test vẫn giữ nguyên. Bằng chứng bản đầu: [CP3 v1](../../starter_v0/artifacts/cp3/README.md). Tính năng/test và giới hạn bản nâng cấp: [CP3 v2](../../starter_v0/artifacts/cp3_v2/README.md).

**Giới hạn dữ liệu:** số domain không chứng minh publisher độc lập hay claim được xác thực; score chỉ là độ liên quan của search. Source text không phải chỉ thị và UI escape dữ liệu đó như text. [Output mẫu](../../starter_v0/artifacts/cp3/research_board.mock.json) là fixture giả lập có nhãn `offline_mock_example`, không phải log API/eval thật. Ở thời điểm chốt CP3 chưa có live run; bằng chứng API/group thật bổ sung sau đó nằm ở B3/B4, tách khỏi các file mock.

V2 có thêm [mock so sánh](../../starter_v0/artifacts/cp3_v2/comparison.mock.json) và [mock lỗi từng phần](../../starter_v0/artifacts/cp3_v2/partial.mock.json). Ngày đăng chỉ được đếm khi provider cung cấp, chưa xác thực độ mới. URL chung chỉ là retrieval overlap; query lỗi/skipped có coverage và giao nhau `null`, không phải 0. Budget mặc định không tăng; các query bổ sung mới có thể thêm request, tổng tối đa 3, không auto retry.

**Tách bằng chứng theo checkpoint:** snapshot/run/CSV CP2 được giữ nguyên. CP3 chủ động sửa registry, file TODO test và append declaration mới; 10 declaration cũ vẫn nguyên nội dung. Các số đo v0–v4 ở B1 chỉ áp dụng snapshot CP2 đã ghi trong run. Group 11 tool có run riêng ở B3; chưa chạy lại base 20 case cho build này. Kiểm tra cuối CP4/CP5: [184 passed, 0 skipped/failed](../../starter_v0/artifacts/cp4_cp5/pytest.txt), gồm 12 test dataset và 25 test runtime/AppTest UI mới, giữ nguyên 147 case trước đó.

**Kết quả sau bổ sung pipeline:** [195 passed, 0 failed, 0 skipped](../../starter_v0/artifacts/cp5_pipeline/pytest.txt), [JUnit XML](../../starter_v0/artifacts/cp5_pipeline/pytest.xml), [validation](../../starter_v0/artifacts/cp5_pipeline/validation.json). Tổng gồm 60 contract + 7 example + 16 test tool cũ + 64 test research_board + 12 test dataset + 25 test runtime/UI + 11 test pipeline. Các test pipeline kiểm tra prompt/policy/history, schema snapshot, feedback bị rút gọn, clarify, provider error, redaction, HTML escaping, chọn lượt và reset phiên. Test dùng provider/HTTP giả lập; kiểm tra live ở B4 được lưu riêng. Kiểm tra chốt bài có bằng chứng riêng tại [pytest.txt](../../starter_v0/artifacts/cp5_pipeline/pytest.txt), [pytest.xml](../../starter_v0/artifacts/cp5_pipeline/pytest.xml) và [validation.json](../../starter_v0/artifacts/cp5_pipeline/validation.json).

Lệnh kiểm tra từ `starter_v0/`:

```powershell
python -B -m pytest -p no:cacheprovider -q
```

### B5. Bonus Evidence

Bonus được kê khai riêng, không tự cộng vào điểm chính. Tool có sẵn trong starter không được tính là tool mới của nhóm.

| Hạng mục | Tình trạng và bằng chứng | Giới hạn |
|---|---|---|
| Small Local Model | Không thực hiện; xem B7 | Groq 20b là cloud, không phải model local |
| Ít nhất 4 tool mới | Không đề nghị; nhóm có 1 tool mới `research_board` | Bản v2 là mở rộng cùng tool, không tính thành tool mới thứ hai |
| Gửi Telegram thật sau xác nhận | Không đề nghị; B4 chỉ chứng minh hỏi lại/xác nhận | Chưa có event `status: sent`; UI khóa send |
| Test challenge | Cung cấp bằng chứng toàn suite **195 passed, 0 skipped** ở [pytest.txt](../../starter_v0/artifacts/cp5_pipeline/pytest.txt), đối chiếu tiêu chí trong [RUBRIC.md](../../RUBRIC.md#bonus) | Người chấm quyết định điểm. Regression avatar/reset là lỗi UI, không nhận là phát hiện bug trong tool có sẵn |

### B7. Small Local Model Challenge (bonus)

Nhóm không thực hiện challenge local: chưa có hai model Ollama, hai vòng tối ưu local hoặc run đối chiếu cloud/local. Vì vậy không điền số đo/failure pattern suy đoán và không đề nghị bonus này.

`openai/gpt-oss-20b` ở CP5 được phục vụ qua Groq cloud sau khi 120b chạm quota; việc đổi model để tiếp tục demo không phải thí nghiệm tối ưu local. Nếu triển khai local sau này, nhóm cần chốt phần cứng/model, chạy cùng bộ case và snapshot, ghi đầy đủ lỗi JSON/routing/clarify trước khi kết luận model nào phù hợp.

## 5. Khó khăn và cách xử lý

- Twitter tool trả lỗi HTTP 403/429 trong baseline, và tiếp tục có HTTPError ở các vòng sau. Phân tích riêng lỗi dịch vụ với routing; không sửa mã nguồn tool trong CP2. Chi tiết loại lỗi theo từng vòng có trong `artifacts/cp2/vN/analysis.json`.
- Hành vi có thể hồi quy dù tổng điểm tăng hoặc giữ nguyên: v2 giảm routing; v3 làm R12 sai lại; v4 sửa R12 nhưng làm R03 sai lại. Tất cả đều được giữ trong CSV/nhật ký và run gốc.
- Case R13 vẫn thiếu một nguồn độc lập sau v4. Chưa có thí nghiệm riêng để phân biệt giới hạn model/API với cách diễn đạt prompt; không đổi model giữa chuỗi so sánh.
- Điểm tự động không đo nội dung từ chối, chất lượng nguồn hay quy trình phê duyệt đầy đủ. Ghi rõ các lỗi review tay ở B1 và `manual_review.md`; không sửa evaluator để che giới hạn này.
- Không cấp credential Telegram cho process eval sau khi load dotenv; model và research tool vẫn chạy thật. Chưa có bằng chứng gửi Telegram thực tế hoặc bonus gửi tin.
- Tại lúc chốt CP2: 62 passed, 17 TODO CP3 skipped, 0 failed; output thật ở [final_pytest.txt](../../starter_v0/artifacts/cp2/final_pytest.txt). Khi đó 72 file được bảo vệ và run v0 giữ nguyên hash; phần CP2 chỉ đo bộ base. Các checkpoint sau có manifest và kết quả riêng.
- CP5 gặp quota ngày 120b sau hai lượt đầu; giữ [transcript lỗi](../../starter_v0/transcripts/cp3-research-board-v2_groq_20261111T022652587579.transcript.json), dùng 20b riêng cho UI/chat và ghi model đúng ở B4. Không đổi model hoặc làm lại run group để nâng điểm.
- AppTest sau thao tác thật phát hiện avatar không hợp lệ làm lỗi render sau first turn. Đã dùng avatar mặc định, thêm regression empty/HTTP429 và chạy lại với API thật không lỗi. Graph dùng API `st.iframe` hiện có, dữ liệu JSON/text được escape.
- Computer Use dừng do không xác định được current browser URL Windows; không thử vượt chặn. HTTP/health, public WebSocket 101 và AppTest backend/render đạt, nhưng visual/mobile/cross-team testing vẫn chưa được xác nhận. Link là tunnel tạm; chưa phải hosting bền vững.

## 6. Tổng hợp đóng góp

Ba thành viên được phân công ba gói công việc/người, mục tiêu khối lượng khoảng **1/3 mỗi người**. Tỷ lệ này là phân bổ trách nhiệm, không phải số giờ đo được hoặc xác nhận ai đã tự tay thực hiện từng thao tác trong log.

| Thành viên | Gói 1 | Gói 2 | Gói 3 và kiểm tra chéo | Bằng chứng phụ trách |
|---|---|---|---|---|
| **Đinh Phúc Diên** | CP1: kiểm tra baseline/provider, đọc lỗi run v0 | CP2: giải thích giả thuyết v1–v4, prompt và contract tool, theo dõi hash/metric | Hoàn thiện B1/B2, đối chiếu version log; review nguồn gốc case CP4 cùng Nhân | [Nhật ký CP2](../../starter_v0/artifacts/cp2/experiment_log.md), [version_log.csv](../../starter_v0/artifacts/version_log.csv), `MSSV_DinhPhucDien.md` |
| **Đào Văn Hiệp** | CP3: contract và implementation research_board, chuẩn hóa/gộp URL, graph/provenance/so sánh | Test happy path, input xấu, thiếu key/timeout/429, partial và giới hạn request | Hoàn thiện TOOL.md/B5a; review cách UI giữ lỗi tool và giới hạn dữ liệu cùng Nhân | [TOOL.md](../../starter_v0/tools/research_board/TOOL.md), [test_tools_todo.py](../../starter_v0/tests/test_tools_todo.py), `MSSV_DaoVanHiep.md` |
| **Lê Nguyễn Anh Nhân** | CP4: 10 case tự viết, freeze dataset, chạy/đọc group eval và B3 | CP5: UI, tunnel, live transcript, pipeline/prompt inspector và B4 | Tích hợp Phần A/B, kiểm tra link/evidence/pytest/secret, chuẩn bị commit chốt; review tích hợp cùng Diên và Hiệp | [eval_group.json](../../starter_v0/data/eval_group.json), [app.py](../../starter_v0/app.py), [bằng chứng pipeline](../../starter_v0/artifacts/cp5_pipeline/README.md), [báo cáo cá nhân](2A202603838_LeNguyenAnhNhan.md) |



## 7. Hạn chế và hướng cải thiện — B6. Reflection

**Phần sửa ở `system_prompt.md`:** v1 thay thói quen đoán bằng hỏi lại thông tin thiết yếu chưa có; v2 đặt quyền quyết định gửi ở người dùng với xác nhận rõ; v4 thay ép một tool bằng thứ tự phân loại yêu cầu/nhánh hành động. Prompt phù hợp để sửa chính sách chung xuyên tool. Điểm base tăng từ 65% lên 90% qua cả chuỗi nhưng v4 không tăng điểm so với v3; từng thay đổi vẫn có hồi quy, như R03/R12 ở B1. Không quy toàn bộ mức tăng cho riêng một câu prompt.

**Phần sửa ở `tools.yaml`:** v3 làm rõ khi dùng/không dùng từng tool và convention của query/topic/timeframe, handle, count/limit, format, `confirmed`. Đây là giao diện agent dùng để chọn đúng tool/args; v3 giữ cấu trúc ngoài description của 10 tool để so sánh được với v2. CP3 mới append declaration research_board khớp registry/implementation, có contract và test riêng. R03 ở v4 cho thấy mô tả rõ vẫn chưa đảm bảo model giữ nguyên acronym.

**Những phần cần review thủ công:** PASS no_tool ở R08/R14 chưa chứng minh agent từ chối đúng phạm vi; R09 mô tả sai khả năng; G05 giải thích nhầm backend dù route no_tool đúng. Routing PASS ở social tools không chứng minh API thành công; overlap/coverage/domain không xác nhận tính đúng, độ mới hoặc sự độc lập của nguồn. Quy trình duyệt bản nháp/đích nhận, chất lượng tóm tắt và thông tin nguồn cần người kiểm tra thêm. Các giới hạn này đã được giữ trong B1–B4 thay vì sửa evaluator để đạt điểm.

**Một giả thuyết cho vòng tiếp theo, chưa thực hiện:** agent mở rộng/diễn giải lại cụm chủ đề người dùng vì quy ước query còn cho phép diễn đạt tự do; thêm một quy tắc chung trong description của trường query để ưu tiên giữ nguyên cụm chủ đề/acronym được cung cấp, không tự mở rộng nghĩa. Thử nghiệm sẽ bắt đầu từ snapshot v4 CP2 có 10 tool, chỉ sửa nhóm description liên quan query, giữ prompt, model và case cố định; snapshot/hash trước run, chạy lại toàn bộ suite base và ghi cả hồi quy. Đây là đề xuất kiểm chứng từ lỗi R03, không hard-code đáp án theo ID và chưa có metric mới.

**Hướng phát triển ngoài vòng đo đó:** duy trì guard gửi ở runtime, bổ sung thử visual/mobile và dùng thử từ nhóm khác với phản hồi có nguồn; thay tunnel tạm bằng hosting phù hợp khi cần demo dài hạn. Nếu làm xác minh claim hoặc tìm nguồn độc lập, cần contract/dữ liệu/test riêng; không diễn giải graph hiện tại là tính năng kiểm chứng đã có.

## 8. Tài liệu tham khảo

- Tài liệu lab trong repo: [RULES](../../RULES.md), [CHECKPOINTS](../../CHECKPOINTS.md), [RUBRIC](../../RUBRIC.md), [SUBMISSION](../../SUBMISSION.md); các run/transcript được liên kết ở B1–B5a.
- [Slide hướng dẫn Day 03 — ca chiều](https://sagitakdx.github.io/k5-day03-instructor-slides/?ca=chieu): checkpoint, quy trình mỗi version một giả thuyết và yêu cầu bằng chứng.
- [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest): kiểm thử app không thay cho browser visual QA.
- [Cloudflare Quick Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/): link public tạm cho local UI.
- [Groq supported models](https://console.groq.com/docs/models), [rate limits](https://console.groq.com/docs/rate-limits): lựa chọn 20b riêng CP5 khi 120b gặp quota.
- [Tavily Search API](https://docs.tavily.com/documentation/api-reference/endpoint/search): backend đọc của research_board.

