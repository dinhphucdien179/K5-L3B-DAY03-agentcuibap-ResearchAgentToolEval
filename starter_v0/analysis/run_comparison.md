# So sánh các run thực tế

Cập nhật: 2026-11-10T23:43:25+07:00 (GMT+7).

Chọn lần chạy **hợp lệ mới nhất** cho từng version/suite, không chọn điểm cao nhất. Run hợp lệ có đủ case được đo và không có provider error. Điểm chỉ đo routing/args; lỗi API của tool được đếm riêng bên dưới.

| Version/suite | Pass | Routing | Args | Multi-turn | Tool errors (calls/cases) | Run gốc |
|---|---:|---:|---:|---:|---:|---|
| v0/base | 13/20 (65.00%) | 75.00% | 65.00% | 100.00% | 9/9 | [v0_B_base_openrouter_20261110T185819400914.json](../runs/v0_B_base_openrouter_20261110T185819400914.json) |
| v1/base | 15/20 (75.00%) | 90.00% | 75.00% | 83.33% | 10/10 | [v1_B_base_openrouter_20261110T191733245712.json](../runs/v1_B_base_openrouter_20261110T191733245712.json) |
| v2/base | 18/20 (90.00%) | 95.00% | 90.00% | 100.00% | 9/9 | [v2_B_base_openrouter_20261110T192059631983.json](../runs/v2_B_base_openrouter_20261110T192059631983.json) |
| v3/base | 19/20 (95.00%) | 100.00% | 95.00% | 100.00% | 8/8 | [v3_B_base_openrouter_20261110T192320127555.json](../runs/v3_B_base_openrouter_20261110T192320127555.json) |
| v4/base | 19/20 (95.00%) | 100.00% | 95.00% | 100.00% | 8/8 | [v4_B_base_openrouter_20261110T213840374908.json](../runs/v4_B_base_openrouter_20261110T213840374908.json) |
| v5/base | 19/20 (95.00%) | 100.00% | 95.00% | 100.00% | 8/8 | [v5_B_base_openrouter_20261110T234010963310.json](../runs/v5_B_base_openrouter_20261110T234010963310.json) |
| v6/base | 20/20 (100.00%) | 100.00% | 100.00% | 100.00% | 8/8 | [v6_B_base_openrouter_20261110T234242756239.json](../runs/v6_B_base_openrouter_20261110T234242756239.json) |
| v3/group | 8/10 (80.00%) | 90.00% | 80.00% | 100.00% | 0/0 | [v3_B_group_openrouter_20261110T192305674708.json](../runs/v3_B_group_openrouter_20261110T192305674708.json) |
| v4/group | 9/10 (90.00%) | 90.00% | 90.00% | 100.00% | 0/0 | [v4_B_group_openrouter_20261110T213941166369.json](../runs/v4_B_group_openrouter_20261110T213941166369.json) |
| v5/group | 10/10 (100.00%) | 100.00% | 100.00% | 100.00% | 0/0 | [v5_B_group_openrouter_20261110T233945822009.json](../runs/v5_B_group_openrouter_20261110T233945822009.json) |
| v6/group | 10/10 (100.00%) | 100.00% | 100.00% | 100.00% | 0/0 | [v6_B_group_openrouter_20261110T234157985676.json](../runs/v6_B_group_openrouter_20261110T234157985676.json) |

## Thay đổi có bằng chứng

v0-v4 descriptions/hypotheses were documented retrospectively from snapshots and saved runs. v5 onward have prospective hypothesis.json recorded before evaluation. v1 also changed the tool set; its improvement cannot be attributed to the prompt alone.

- **v0**: Đo starter trước tối ưu; chọn lần chạy hợp lệ mới nhất, không chọn điểm cao nhất.
- **v1**: Viết lại phạm vi research, clarify dữ liệu thiếu, preview/xác nhận trước gửi và trust boundary; đồng thời đăng ký deduplicate, investigate, compare_research, citation_audit.
- **v2**: Giữ prompt v1; viết lại mô tả khi dùng/không dùng và schema args (handle, news/timeframe, Top, send confirmation) cho các tool.
- **v3**: Thêm thứ tự phân loại request: gửi/xác nhận, thiếu định danh, chọn tool hẹp nhất, rồi tổng hợp; giữ tools v2.
- **v4**: Giữ tools v3; bổ sung quy tắc batch các góc nhìn/tiêu chí vào một workbench call và truyền timeframe=all khi không giới hạn thời gian.
- **v5**: Giữ nguyên tools v4; ưu tiên ý định gửi/đăng trước quy tắc hỏi thông tin thiếu, dùng clarify yes_no để xin phép tiếp tục workflow dù draft còn thiếu; đây chưa phải duyệt nội dung để gửi.
- **v6**: V5 vẫn lỗi R12; giữ prompt v5 và các schema, chỉ làm rõ ngoại lệ yes_no cho yêu cầu gửi lần đầu, kể cả thiếu draft, ngay trong mô tả clarify.

## Lỗi còn lại và tình trạng API tool

- **v0/base**: 7 case routing/args chưa đạt; 9 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {"403": 8, "429": 1}.
  - `R03_web_news_routing`: wrong_arg_value — query: expected 'AI', got 'AI news'.
  - `R08_out_of_scope`: unexpected_tool_call — expected no tool call.
  - `R10_missing_handle`: missing_tool_call — missing tool call clarify; extra tool call timeline.
  - `R11_missing_url`: missing_tool_call — missing tool call clarify; extra tool call fetch.
  - `R12_confirm_before_send`: missing_tool_call — missing tool call clarify; extra tool call send.
  - `R13_parallel_web_and_tweets`: wrong_arg_value — query: expected 'AI', got 'AI news'; topic: expected 'news', got None.
  - `R14_out_of_scope_coding`: unexpected_tool_call — expected no tool call.
- **v1/base**: 5 case routing/args chưa đạt; 10 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {"403": 9, "429": 1}.
  - `R03_web_news_routing`: wrong_arg_value — query: expected 'AI', got 'AI news'.
  - `R10_missing_handle`: missing_tool_call — missing tool call clarify; extra tool call timeline.
  - `R12_confirm_before_send`: wrong_arg_value — response_type: expected 'yes_no', got 'text'.
  - `R13_parallel_web_and_tweets`: wrong_arg_value — topic: expected 'news', got None.
  - `M06_switch_tool`: missing_tool_call — missing tool call lookup; extra tool call social_search.
- **v2/base**: 2 case routing/args chưa đạt; 9 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {"403": 8, "429": 1}.
  - `R10_missing_handle`: missing_tool_call — missing tool call clarify; extra tool call social_search.
  - `R12_confirm_before_send`: wrong_arg_value — response_type: expected 'yes_no', got 'text'.
- **v3/base**: 1 case routing/args chưa đạt; 8 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {"403": 7, "429": 1}.
  - `R12_confirm_before_send`: wrong_arg_value — response_type: expected 'yes_no', got 'text'.
- **v4/base**: 1 case routing/args chưa đạt; 8 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {"403": 8}.
  - `R12_confirm_before_send`: wrong_arg_value — response_type: expected 'yes_no', got 'text'.
- **v5/base**: 1 case routing/args chưa đạt; 8 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {"403": 8}.
  - `R12_confirm_before_send`: wrong_arg_value — response_type: expected 'yes_no', got 'text'.
- **v6/base**: 0 case routing/args chưa đạt; 8 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {"403": 8}.
- **v3/group**: 2 case routing/args chưa đạt; 0 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {}.
  - `G01_investigate_evidence`: extra_tool_call — extra tool call investigate.
  - `G02_compare_shared_criteria`: wrong_arg_value — timeframe: expected 'all', got None.
- **v4/group**: 1 case routing/args chưa đạt; 0 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {}.
  - `G01_investigate_evidence`: extra_tool_call — extra tool call investigate.
- **v5/group**: 0 case routing/args chưa đạt; 0 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {}.
- **v6/group**: 0 case routing/args chưa đạt; 0 tool call trả lỗi, 0 call trả kết quả partial. HTTP status: {}.

Tool errors không bị `run_eval.py` tính là failure nếu model chọn đúng tool/args. Đặc biệt, RapidAPI trả HTTP 403 ở các run base; các điểm routing cao không chứng minh timeline/social_search đã lấy được dữ liệu.

## Hash và snapshot

Hash dưới đây lấy nguyên từ JSON run, không thay bằng hash file hiện tại.

- **v0/base**: `v0+pf0c107a9d7a1+t41a2894f8ad1`
  - prompt SHA-256: `f0c107a9d7a14032c948d642d7c36f2a85cb6d69a099530093a874c94d472446`; snapshot khớp: `True`.
  - tools SHA-256: `41a2894f8ad1b5f1af946a1ebd34dc809faa05f187393d1fb770540a67c9074a`; Git original khớp: `True`. Không tạo lại file tools v0.
- **v1/base**: `v1+pbbe91757ae3b+t87ed98d75509`
  - prompt SHA-256: `bbe91757ae3bed8e239fe7d46a8ab1e49d8661e2044f70dfe3d9b761c58add3b`; snapshot khớp: `True`.
  - tools SHA-256: `87ed98d75509992e885acf04aaa638b1ebf3251d25ad22f8e8bd818dbb60237c`; snapshot khớp: `True`.
- **v2/base**: `v2+pbbe91757ae3b+te329ef788230`
  - prompt SHA-256: `bbe91757ae3bed8e239fe7d46a8ab1e49d8661e2044f70dfe3d9b761c58add3b`; snapshot khớp: `True`.
  - tools SHA-256: `e329ef788230b5c031fbdb5e5ac64aa7d96788d600567450ceb4cf8ffd6cae62`; snapshot khớp: `True`.
- **v3/base**: `v3+p5c6f97d6a7c1+te329ef788230`
  - prompt SHA-256: `5c6f97d6a7c10b6fe2e9c2396f25a4ae64b14df200514505d8ab840c52b360e4`; snapshot khớp: `True`.
  - tools SHA-256: `e329ef788230b5c031fbdb5e5ac64aa7d96788d600567450ceb4cf8ffd6cae62`; snapshot khớp: `True`.
- **v4/base**: `v4+p1cef423a1069+te329ef788230`
  - prompt SHA-256: `1cef423a106940a815fcf710d3fd719a909f6953d560b71a64e4cba6a5340be8`; snapshot khớp: `True`.
  - tools SHA-256: `e329ef788230b5c031fbdb5e5ac64aa7d96788d600567450ceb4cf8ffd6cae62`; snapshot khớp: `True`.
- **v5/base**: `v5+pe4386e443011+te329ef788230`
  - prompt SHA-256: `e4386e4430110a368e3ee25b21ee79a7390e6b629a7110bac7d849e3c84b9d5f`; snapshot khớp: `True`.
  - tools SHA-256: `e329ef788230b5c031fbdb5e5ac64aa7d96788d600567450ceb4cf8ffd6cae62`; snapshot khớp: `True`.
- **v6/base**: `v6+pe4386e443011+t3b71705b7594`
  - prompt SHA-256: `e4386e4430110a368e3ee25b21ee79a7390e6b629a7110bac7d849e3c84b9d5f`; snapshot khớp: `True`.
  - tools SHA-256: `3b71705b759497516b4dc703c759028baadfa5b1e60201bdac4b9ec94d208d9a`; snapshot khớp: `True`.
- **v3/group**: `v3+p5c6f97d6a7c1+te329ef788230`
  - prompt SHA-256: `5c6f97d6a7c10b6fe2e9c2396f25a4ae64b14df200514505d8ab840c52b360e4`; snapshot khớp: `True`.
  - tools SHA-256: `e329ef788230b5c031fbdb5e5ac64aa7d96788d600567450ceb4cf8ffd6cae62`; snapshot khớp: `True`.
- **v4/group**: `v4+p1cef423a1069+te329ef788230`
  - prompt SHA-256: `1cef423a106940a815fcf710d3fd719a909f6953d560b71a64e4cba6a5340be8`; snapshot khớp: `True`.
  - tools SHA-256: `e329ef788230b5c031fbdb5e5ac64aa7d96788d600567450ceb4cf8ffd6cae62`; snapshot khớp: `True`.
- **v5/group**: `v5+pe4386e443011+te329ef788230`
  - prompt SHA-256: `e4386e4430110a368e3ee25b21ee79a7390e6b629a7110bac7d849e3c84b9d5f`; snapshot khớp: `True`.
  - tools SHA-256: `e329ef788230b5c031fbdb5e5ac64aa7d96788d600567450ceb4cf8ffd6cae62`; snapshot khớp: `True`.
- **v6/group**: `v6+pe4386e443011+t3b71705b7594`
  - prompt SHA-256: `e4386e4430110a368e3ee25b21ee79a7390e6b629a7110bac7d849e3c84b9d5f`; snapshot khớp: `True`.
  - tools SHA-256: `3b71705b759497516b4dc703c759028baadfa5b1e60201bdac4b9ec94d208d9a`; snapshot khớp: `True`.

## Run không dùng để tính tiến bộ

- [v0_B_base_openai_20261110T184708827363.json](../runs/v0_B_base_openai_20261110T184708827363.json): measured_cases_does_not_equal_total_cases, provider_error_cases_nonzero_or_missing, case_contains_provider_error.
- [v0_B_base_openrouter_20261110T185625193558.json](../runs/v0_B_base_openrouter_20261110T185625193558.json): superseded_by_newer_valid_run_same_version_and_suite.
- [v4_B_base_openrouter_20261110T192640949460.json](../runs/v4_B_base_openrouter_20261110T192640949460.json): superseded_by_newer_valid_run_same_version_and_suite.
- [v4_B_group_openrouter_20261110T192557285563.json](../runs/v4_B_group_openrouter_20261110T192557285563.json): superseded_by_newer_valid_run_same_version_and_suite.

Chi tiết số liệu và từng lỗi tool: [summary.json](summary.json). Log phiên bản: [version_log.csv](../artifacts/version_log.csv).
