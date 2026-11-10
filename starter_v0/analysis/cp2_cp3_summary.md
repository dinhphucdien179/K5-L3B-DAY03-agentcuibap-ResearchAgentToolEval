# Bằng chứng CP2 và CP3 — Đinh Phúc Diên

Đã kiểm tra bằng Conda **AI20k**: **272 passed, 0 failed, 0 skipped**, lúc
23:43:25 ngày 10/11/2026 (GMT+7). Bằng chứng: [pytest_final.txt](pytest_final.txt)
và [pytest.xml](pytest.xml). Các run v5/v6 do Codex chạy với provider/tool thật
theo yêu cầu của Đinh Phúc Diên; không ghi đây là các lần sinh viên tự gõ lệnh.

## CP2 — Tối ưu và đo lại

Giữ nguyên các run/snapshot v0–v4: base lần lượt **13/20 → 15/20 → 18/20 →
19/20 → 19/20**. Giả thuyết cũ được mô tả hồi cứu; v1 thay cả prompt và tool
set nên không thể quy toàn bộ mức tăng cho prompt.

| Vòng mới | Thay đổi riêng | Base | Group | Giả thuyết trước eval |
|---|---|---:|---:|---|
| v5 | Chỉ system prompt: ưu tiên hỏi yes/no khi user muốn gửi, dù draft còn thiếu | 19/20 | 10/10 | [v5/hypothesis.json](../artifacts/versions/v5/hypothesis.json) |
| v6 | Chỉ `clarify.description`: ngoại lệ yes/no cho ý định gửi lần đầu | 20/20 | 10/10 | [v6/hypothesis.json](../artifacts/versions/v6/hypothesis.json) |

V5 chưa sửa được R12; v6 chọn đúng `clarify(response_type="yes_no")`.
Đồng ý tiếp tục workflow chưa phải duyệt nội dung gửi: runtime vẫn yêu cầu
user xem và duyệt đúng bản tin trước khi `send`.

Đối chiếu thời gian cùng múi giờ GMT+7:

| Vòng | Ghi giả thuyết | Run group được lưu | Run base được lưu |
|---|---|---|---|
| v5 | 23:28:52 | 23:39:45 | 23:40:10 |
| v6 | 23:41:05 | 23:41:57 | 23:42:42 |

Giả thuyết được lưu trước lệnh chạy eval. `generated_at` của run là thời điểm
lưu kết quả, dùng giờ local nhưng không ghi offset; không coi nó là giờ bắt
đầu eval. Tất cả timestamp trên thuộc ngày 10/11/2026.

Bản hiện hành khớp hai snapshot v6 và SHA-256 trong hai run:

- Artifact: `v6+pe4386e443011+t3b71705b7594`.
- Prompt: `e4386e4430110a368e3ee25b21ee79a7390e6b629a7110bac7d849e3c84b9d5f`.
- Tools: `3b71705b759497516b4dc703c759028baadfa5b1e60201bdac4b9ec94d208d9a`.
- [Base v6: 20/20](../runs/v6_B_base_openrouter_20261110T234242756239.json), [group v6: 10/10](../runs/v6_B_group_openrouter_20261110T234157985676.json): `measured_cases == total_cases`, `provider_error_cases == 0`; routing, args và multi turn đều 100%.

Base vẫn có **8 tool call lỗi HTTP 403** (5 timeline, 3 social_search);
group không có tool error. Điểm trên đo routing/args, không chứng minh API
thành công hay nội dung nghiên cứu đúng. Xem toàn bộ lịch sử, hash và lỗi API
trong [version_log.csv](../artifacts/version_log.csv), [run_comparison.md](run_comparison.md)
và [summary.json](summary.json). Snapshot v1–v6 đều khớp hash từng run; tools
v0 được đối chiếu với Git ancestor bất biến, không lấy HEAD đã tối ưu.

## CP3 — Tool mới, contract và test

Cả bốn tool có `tool.py`, `TOOL.md` đúng frontmatter, đăng ký trong
[`TOOL_FUNCTIONS`](../tools/__init__.py) và [`tools.yaml`](../artifacts/tools.yaml).
Các số dưới là **hàm test có tên**, không cộng các biến thể parameterization:

| Tool | Công dụng | Hàm trong `test_tools_todo.py` | Ví dụ test |
|---|---|---:|---|
| [investigate](../tools/investigate/TOOL.md) | Tìm bằng chứng theo nhiều góc, giữ excerpt và báo khoảng trống | 7 | `test_investigate_builds_dossier_with_traceable_excerpts`, `test_investigate_invalid_input_returns_error_without_network`, `test_investigate_http_failure_returns_error_dict` |
| [compare_research](../tools/compare_research/TOOL.md) | So sánh nhiều đối tượng theo cùng tiêu chí | 3 | `test_comparison_builds_same_criteria_cells_and_deduplicates_source_catalog`, `test_comparison_rejects_invalid_input_before_network`, `test_comparison_missing_key_returns_all_cell_errors_without_network` |
| [citation_audit](../tools/citation_audit/TOOL.md) | Rà ID dẫn nguồn, URL và đoạn chưa có citation | 3 | `test_audit_resolves_grouped_references_and_reports_unused_sources_without_mutation`, `test_audit_bad_inputs_return_error`, `test_audit_missing_references_identify_lines_and_uncited_blocks` |
| [deduplicate](../tools/deduplicate/TOOL.md) | Gộp URL trùng, giữ nguồn đầu và tham số nội dung | 5 | `test_deduplicate_keeps_first_source_and_does_not_modify_input`, `test_deduplicate_bad_input_returns_error`, `test_deduplicate_malformed_url_returns_error_dict` |

Các test dùng HTTP mock, không cần API key thật. [Eval nhóm](../data/eval_group.json)
có G01–G04 route tới lần lượt bốn tool, cùng các case args và boundary.

Bổ sung [14 regression case CP3](../tests/test_cp3_regressions.py): giữ nguồn
đã lấy khi truy vấn khác trả payload sai hoặc exception; chuẩn hóa hostname
và title; từ chối URL chứa whitespace/control; giữ phân biệt hoa/thường của
credentials trong URL; bỏ citation mẫu đã escape; nhận diện đúng fence code.
Regression provenance trong [test_evidence_reporting.py](../tests/test_evidence_reporting.py)
kiểm tra Git HEAD đã tối ưu vẫn truy được tools baseline bằng hash ancestor.

## Đóng góp và trạng thái lưu bài

Đinh Phúc Diên cấu hình, vận hành và đã trực tiếp kiểm tra v4 theo bằng chứng
cũ; Codex hỗ trợ code, test, phân tích và thực thi các vòng bổ sung CP2/CP3 này.
Commit `ca5b1a6` của `dinhphucdien179` đã lưu phần bài trước. Các thay đổi bổ
sung v5/v6, regression và báo cáo trong lượt này hiện **chưa commit/push**.
Không tạo lại hoặc chỉnh sửa run cũ để nâng điểm.
