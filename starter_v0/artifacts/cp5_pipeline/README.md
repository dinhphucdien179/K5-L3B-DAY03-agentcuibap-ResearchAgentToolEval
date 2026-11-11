# CP5 — Pipeline & prompt inspector

Bổ sung khả năng quan sát UI; không phải phiên bản tối ưu prompt/tool hoặc một run eval mới. Giữ nguyên dữ liệu và bằng chứng CP2–CP4.

## Cách xem

Mở UI NEXUS, chọn **Pipeline & prompt**. Sơ đồ tổng quan có sẵn trước khi gửi câu hỏi. Sau khi chạy chat hoặc research desk, chọn lượt thực thi để xem đường đi đã ghi nhận.

- **Agent chat:** `app.py` → prompt + deployment policy + lịch sử + câu hỏi → `ui.runtime.run_turn()` → Groq provider → tool calls → `execute_tool()` → kết quả tool → vòng model tiếp theo hoặc dừng.
- **Research desk:** form → `execute_tool(research_board)` → Tavily → chuẩn hóa/gộp URL, nhóm domain và tạo board → UI/transcript. Không gọi model ở đường này.
- Tool `clarify` có `awaiting_user` dừng để đợi người dùng; `send` bị khóa tại runtime UI. Lỗi provider/tool và giới hạn vòng/call có trạng thái riêng.

## Dữ liệu được ghi

`ui/runtime.py` thêm `request_config` và `model_requests` vào kết quả, được lưu vào transcript của lượt mới. Mỗi lần thử gọi adapter giữ snapshot đã redact của messages sau khi giới hạn context, model, temperature, trạng thái và số tool call model trả về. Tool schema được snapshot một lần cho lượt đó.

Snapshot là đầu vào adapter đã che dữ liệu nhạy cảm, không phải bản bắt gói HTTP. Lỗi trong adapter không chứng minh request đã được gửi qua mạng. Không ghi reasoning riêng của model hoặc `response.raw`.

Kết quả tool quay về dưới dạng text `TOOL_RESULTS_JSON` trong role `user`; lệnh tool được lưu dưới dạng `TOOL_CALLS_JSON` trong role `assistant`. Context gửi model có thể rút gọn, trong khi tool trace giữ kết quả đã redact đầy đủ.

Prompt/policy/schema **hiện tại** được xem riêng với snapshot **của lượt đã chọn**. Transcript cũ không có snapshot thì UI báo thiếu, không dựng lại giả đầu vào lịch sử. Workflow bên trong board mô tả các bước đã hoàn tất; không có timing riêng cho từng bước.

## Kiểm chứng

Kiểm thử offline dùng provider/tool giả lập để kiểm tra snapshot, vòng feedback, dừng clarify/blocked/error và khả năng mở inspector mà không gọi API. Kết quả cùng kiểm tra health và hash được ghi trong `validation.json` / `pytest.xml` của thư mục này. Bằng chứng CP5 trước đó nằm nguyên tại `artifacts/cp4_cp5/`.

- Toàn bộ suite: **195 passed, 0 failed, 0 skipped**; trong đó 11 test mới cho pipeline. Có test chọn lượt cũ, tự chuyển đến lượt mới và reset phiên mà không mang lịch sử cũ sang.
- Một lượt **Groq 20b thật** qua AppTest: `system → system → user` → `clarify` → `waiting_for_user`, 1 lần gọi adapter, 11 schema, 0 lỗi render. Xem [live_pipeline_check.json](live_pipeline_check.json) và transcript được trỏ trong đó. Đây là lượt kiểm tra bổ sung, không thay thế eval group hoặc transcript CP5 trước.
- Tại thời điểm chốt tính năng, 129 file được bảo vệ trong manifest không thay đổi. Không sửa prompt, khai báo tool, provider, harness, eval dataset hoặc kết quả cũ cho tính năng này.

Các manifest/validation ghi trạng thái ở từng checkpoint. Khi thu gọn thư mục, bản sao source giống hệt code hiện tại và báo cáo kiểm tra lặp được lược bỏ; run, transcript, snapshot prompt/tool và kết quả pytest vẫn giữ lại.

Link dùng thử: https://connection-hawaii-narrative-mom.trycloudflare.com — Quick Tunnel tạm thời, cần giữ app/tunnel/máy hoạt động. Không nhận là đã kiểm tra visual bằng trình duyệt khi Computer Use bị chặn.
