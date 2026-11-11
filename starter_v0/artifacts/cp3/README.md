# CP3 — research_board

Tool mới tạo bản đồ nguồn cho một chủ đề nghiên cứu. UI và phần trực quan hóa workflow được để sau theo yêu cầu; CP3 cung cấp dữ liệu để triển khai phần đó.

## Tool làm gì

1. Validate subject, topic, timeframe và số kết quả trước khi gọi mạng.
2. Gọi một request Tavily Search bằng `TAVILY_API_KEY` hiện có.
3. Chuẩn hóa URL, bỏ tracking/fragment và loại URL trùng; giữ các query parameter có ý nghĩa.
4. Gom các card dẫn nguồn theo domain và đếm kết quả giữ lại/trùng/bị loại.
5. Tạo graph `chủ đề → domain → tài liệu` với ID ổn định và workflow `validate → search → deduplicate → group_sources → build_graph`.

Output `items` dùng được với formatter hiện có. `sources`, `graph`, `workflow` và `stats` dành cho bước UI sau này. Nội dung nguồn là dữ liệu chưa tin cậy; không thực thi chỉ dẫn trong đó. Tool không đọc toàn bộ trang, không gom claim trùng ý, không fact-check và không coi nhiều domain là bằng chứng độc lập.

## Đủ bốn phần

- [tool.py](../../tools/research_board/tool.py): implementation và error dict đã sanitize.
- [TOOL.md](../../tools/research_board/TOOL.md): frontmatter, input/output, API và giới hạn.
- [TOOL_FUNCTIONS](../../tools/__init__.py): đăng ký tên `research_board`.
- [tools.yaml](../tools.yaml): declaration mới; 10 declaration từ CP2 không đổi.

Interface:

```python
build_research_board(query="", topic="news", timeframe="week", max_results=8)
```

`query` phải có 1–500 ký tự sau trim. Topic là `news`/`general`; timeframe là `day`/`week`/`month`/`year`; số kết quả là integer 1–20, không nhận boolean. Thiếu thông tin chủ đề thì agent cần hỏi lại.

## Kiểm thử và bằng chứng

Chạy trong `starter_v0` bằng môi trường `lab3` có sẵn:

```powershell
python -B -m pytest -p no:cacheprovider --junitxml=artifacts/cp3/pytest.xml -q
```

Kết quả thật: **118 passed, 0 failed, 0 skipped**.

| Phần | Số case | Nội dung |
|---|---:|---|
| Contract | 60 | Khớp 11 tool giữa schema, registry, signature và TOOL.md; eval chỉ gọi tool đã declare |
| Example có sẵn | 7 | Giữ nguyên source test mẫu |
| TODO tool cũ đã hoàn thiện | 16 | clarify, format, send guard, lookup, fetch, social/timeline và policy trust boundary |
| research_board mới | 35 | Happy path/graph, 17 input sai, thiếu key, HTTP 429, timeout, 5 response lỗi, output rỗng, lọc row lỗi, 6 score lỗi và ID ổn định |

- [Test source](../../tests/test_tools_todo.py).
- [Output pytest thật](pytest.txt) và [JUnit XML](pytest.xml).
- [Output mẫu mock](research_board.mock.json): fixture giả có nhãn rõ ràng, không phải nguồn, metric, eval hay API live thật.
- [Validation](validation.json): checksum, contract, số test và giới hạn phần đã kiểm chứng.

Các test dùng fake key và HTTP mock; fixture có sẵn chặn network thật. CP3 chưa gọi API live. Một lỗi URL thực tế đã được phát hiện khi review: chỉ loại prefix `utm_` để không xóa tham số hợp lệ như `utmost`; regression nằm trong happy-path test.

## Các giới hạn được giữ rõ

- Score search là độ liên quan, không phải độ tin cậy; NaN/Infinity/boolean/ngoài khoảng 0–1 thành `null`.
- URL trùng được nhận diện theo cấu trúc, không theo ngữ nghĩa. Giữ `www` ở citation URL và dùng alias đó chỉ khi gom/dedup.
- Domain khác nhau có thể cùng chủ sở hữu. Không khẳng định nguồn độc lập, độ phủ đầy đủ hay claim được xác thực.
- Timeframe luôn áp dụng, kể cả topic general; không hỗ trợ tìm mọi thời gian ở interface này.
- `retryable` chỉ là thông tin cho caller; tool không tự retry, không publish, không ghi file.
- Tên keyword ngoài signature được agent hiện tại bắt thành lỗi; schema đặt `additionalProperties: false`. Tool trực tiếp validate các tham số đã khai báo.
- UI phải render dữ liệu nguồn như text đã escape. Chưa có UI, deploy hoặc workflow visualization trong CP3.

## Giữ nguyên bằng chứng CP2

Không thay run, snapshot hoặc CSV v0–v4; prompt v4 và hai bộ eval cố định giữ nguyên. Chỉ append declaration mới và sửa các bề mặt CP3 được phép. Kết quả 90% ở v4 thuộc snapshot 10 tool của CP2; chưa chạy lại base/group eval với 11 tool nên không ghi metric mới vào version_log.csv.

[protected_hashes.json](protected_hashes.json) và validation ghi nhận việc đối chiếu 95 file tại thời điểm CP3. Manifest CP2 mô tả trạng thái tại thời điểm chốt CP2, còn registry/TODO test được phép thay đổi ở checkpoint mới này.

CP4 cần case mới route tới `research_board`; chưa sửa `eval_group.json` trong CP3. UI/workflow trực quan sẽ dùng schema dữ liệu đã cung cấp khi thực hiện bước sau.

Nguồn API: [Tavily Search](https://docs.tavily.com/documentation/api-reference/endpoint/search). Có hỗ trợ Codex cho thiết kế, implementation, unit test và review; không tạo contribution/commit/metric giả.
