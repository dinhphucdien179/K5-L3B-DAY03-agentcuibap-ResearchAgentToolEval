# Research Board v2

Bản mở rộng của tool CP3, cung cấp dữ liệu phân tích nguồn cho UI/workflow sau này. Giữ cách gọi bốn tham số cũ và một search mặc định; không làm UI hoặc gọi API live trong bước này.

## Tính năng mới

| Tính năng | Dữ liệu và hành vi |
|---|---|
| So sánh tối đa 3 truy vấn | Main query và tối đa 2 `compare_queries` do người dùng cung cấp; thống kê URL/domain chung, item riêng từng cặp |
| Dấu vết từng URL | Query đã tìm thấy, thứ hạng, relevance từng lần xuất hiện, tracking field đã loại; giữ metadata của card đầu tiên |
| Graph đúng membership | Cạnh `retrieves` trực tiếp từ query tới item trong comparison mode; tách khỏi quan hệ domain `hosts` item |
| Metadata coverage | Đếm title/excerpt/ngày do provider cung cấp, liệt kê card thiếu dữ liệu, tỉ lệ item theo domain và domain chiếm nhiều nhất |
| Partial failure | Giữ nguồn đã lấy; query lỗi/skipped có dữ liệu unknown/null; không giả thành không có bằng chứng |
| Budget và giới hạn | 1 request mặc định, tối đa 3 tuần tự khi so sánh; không retry; dừng phần còn lại khi 429/401/403 |

Mỗi query giữ tối đa `max_results` item duy nhất (1–20), union toàn board không quá 60. Nếu provider trả thừa thì vẫn áp giới hạn. Tổng thống kê trên các response hợp lệ thỏa `retrieved = unique + duplicate + discarded`.

Provenance giữ tối đa 20 occurrence/card, đếm đầy đủ số occurrence quan sát được và đánh dấu `truncated` nếu vượt giới hạn. Chỉ giữ URL đã clean và tên tracking parameter, không đưa tracking value trở lại output.

## Cách gọi

```python
from tools import TOOL_FUNCTIONS

result = TOOL_FUNCTIONS["research_board"](
    query="solid-state batteries",
    compare_queries=["sodium-ion batteries", "LFP batteries"],
    topic="news",
    timeframe="month",
    max_results=5,
)
```

Đây là ví dụ interface cho khi có cấu hình key và chủ động chạy live; **không được thực thi trong kiểm thử CP3**. `compare_queries` bỏ qua, `None` hoặc `[]` đều giữ một search. Query so sánh phải khác nhau sau trim/casefold và được validate hết trước request đầu tiên.

[TOOL.md](../../tools/research_board/TOOL.md) mô tả contract chi tiết. Schema model được cập nhật tại [tools.yaml](../tools.yaml); registry giữ nguyên tên `research_board`.

## Output mẫu và phạm vi đã kiểm chứng

- [comparison.mock.json](comparison.mock.json): ví dụ synthetic có query chung/riêng, metadata thiếu và graph nguồn/tài liệu.
- [partial.mock.json](partial.mock.json): một query thành công, query thứ hai bị 429, query thứ ba không được gọi; overlap với query lỗi là `null`.

Cả hai có nhãn `offline_mock_example`, `live_api=false` và `not_an_eval_run=true`. Đây không phải nguồn thật, metric hay run model thật. Mỗi kết quả comparison có query reports và request count để caller/UI biết mức độ hoàn thành trước khi đọc giao/riêng.

Coverage đo metadata của card đầu tiên được giữ, không xác thực ngày đăng/freshness. Share là phần item thuộc domain, làm tròn 4 chữ số thập phân; tổng các share làm tròn có thể không đúng 1 tuyệt đối. Domain và URL overlap không chứng minh claim đúng, publisher độc lập hoặc đồng thuận ngữ nghĩa.

## Kiểm thử

Chạy trong `starter_v0` bằng môi trường `lab3`:

```powershell
python -B -m pytest -p no:cacheprovider --junitxml=artifacts/cp3_v2/pytest.xml -q
```

Kết quả thật: **147 passed, 0 failed, 0 skipped**.

| Nhóm | Số case |
|---|---:|
| Contract 11 tool | 60 |
| Example giữ nguyên | 7 |
| TODO tool cũ đã hoàn thiện ở CP3 v1 | 16 |
| research_board v1 giữ nguyên assertions | 35 |
| Test mới v2 | 29 |

Test mới kiểm tra validation trước network, cap/request payload, giao/riêng theo query, cùng domain khác tài liệu, provenance sạch và có giới hạn, độ phủ metadata, partial/empty/unknown, stop 429/401/403 và xử lý exception bất ngờ không mất nguồn đã lấy. Tất cả fake HTTP và fake key; fixture gốc vẫn chặn network thật.

Bằng chứng: [test source](../../tests/test_tools_todo.py), [stdout pytest](pytest.txt), [JUnit](pytest.xml), [validation](validation.json).

## Giữ lịch sử và giới hạn

Các file trong [CP2](../cp2/) và [CP3 v1](../cp3/) cùng run JSON/CSV cũ được giữ nguyên. [baseline/](baseline/) lưu source bốn file trước nâng cấp, đối chiếu fingerprint CP3 v1. [protected_hashes.json](protected_hashes.json) ghi nhận 105 file ngoài phạm vi chỉnh sửa tại thời điểm checkpoint. Bản sao source v2 trùng hoàn toàn với code hiện tại đã được lược bỏ; implementation và test nằm trong `tools/`, `tests/`.

10 declaration cũ không đổi; chỉ mở rộng declaration `research_board`. Không đổi system prompt, provider, evaluator, fixture hay eval cases. Không ghi metric mới vào version_log.csv vì chưa có run eval live cho build này. UI/deploy và eval nhóm CP4 chưa thực hiện.

Có hỗ trợ Codex trong implementation/test/review. Không mô phỏng output mock thành thành tích API hoặc model; không tạo commit hay đóng góp cá nhân giả.
