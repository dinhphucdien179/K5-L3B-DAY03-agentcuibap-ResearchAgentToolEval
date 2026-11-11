# Báo cáo cá nhân — LeNguyenAnhNhan-2A202603838


## 1. Thông tin thành viên

- Họ tên: Lê Nguyễn Anh Nhân
- MSSV: 2A202603838
- Email: 26ai.nhanlna@vinuni.edu.vn


## 2. Phần việc phụ trách


| Gói | Trách nhiệm | Sản phẩm và tiêu chí nghiệm thu |
|---|---|---|
| 1. Eval nhóm | CP4: 10 case gốc, freeze dataset, run group và B3 | Đúng 5 single + 5 multi, có case tool mới, metadata đầy đủ; không sửa case sau khi biết điểm |
| 2. UI và live evidence | CP5: chat, research desk, graph và pipeline inspector; transcript/B4 | Hiển thị lỗi thật, chặn send, tách đường trực tiếp với model routing; payload được redact |
| 3. Tích hợp và review chéo | Tích hợp Phần A/B, đối chiếu checklist và kiểm thử; review kết quả CP2 với Diên, lỗi tool với Hiệp

## 3. Đóng góp cụ thể

### 3.1. Thiết kế và đọc eval nhóm

`eval_group.json` có đúng 10 case: 5 single-turn, 5 multi-turn; hai case route tới `research_board`. Các tình huống bám lỗi thật như tự đoán dữ liệu, sửa query/thời gian/số lượng trong hội thoại, đổi URL và chưa phê duyệt gửi. Case chỉ kiểm tra args cần thiết; dataset được chốt trước khi chạy.

Run group dùng Groq `openai/gpt-oss-120b`, đo đủ 10/10, 0 provider error và 10 PASS. Đây là điểm routing/args của một suite riêng; không thay điểm base 90%. G09/G10 còn lỗi HTTP của social API. G05 PASS `no_tool` nhưng model mô tả sai backend của board, cần review tay.

### 3.2. UI, pipeline và ranh giới

NEXUS dùng Streamlit, có chat agent và research desk. Chat lắp system prompt → policy public UI → history phiên → câu hỏi, gửi schema riêng cho Groq rồi thực thi tool qua registry. Kết quả quay về context bằng text `TOOL_RESULTS_JSON`; `clarify` dừng chờ người dùng. Research desk gọi thẳng `research_board`, không được dùng để chứng minh model tự route đúng.

UI khóa `send` ngay tại runtime kể cả `confirmed=true`, hiển thị lỗi/partial riêng và giữ transcript theo session. Pipeline inspector cho xem cấu hình hiện tại cùng snapshot đầu vào adapter của từng vòng mới; không dựng prompt quá khứ cho lượt cũ, không suy diễn HTTP đã gửi khi adapter lỗi và không ghi reasoning riêng của model.

### 3.3. Kiểm thử, triển khai và giới hạn

CLI có phiên 20b hoàn chỉnh và lượt tiếp nối xác nhận yes/no; lần 120b lỗi quota được giữ riêng. UI dùng 20b do ngân sách quota, không đổi model trong chuỗi so sánh CP2 hoặc run group. Bằng chứng AppTest gồm tool/API thật và test offline. Tại checkpoint pipeline toàn suite 195 passed, 0 failed/skipped; có 11 test mới cho snapshot, flow và reset phiên.

Link Cloudflare là tạm thời, cần giữ máy/app/tunnel chạy. Kiểm tra browser visual bị Computer Use chặn, nên không nhận là đã thử mobile hay có nhóm khác dùng thử.

## 4. Bằng chứng và cách kiểm tra

| Bằng chứng | Nội dung đối chiếu |
|---|---|
| [Dataset nhóm](../../starter_v0/data/eval_group.json) và [group freeze](../../starter_v0/artifacts/cp4_cp5/group_freeze.json) | 10 case, cấu trúc/metadata và hash trước run |
| [Run group](../../starter_v0/runs/cp3-research-board-v2_B_group_groq_20261111T022506173733.json) và [phân tích](../../starter_v0/artifacts/cp4_cp5/group_analysis.json) | PASS routing/args tách khỏi HTTPError và review nội dung |
| [app.py](../../starter_v0/app.py), [runtime](../../starter_v0/ui/runtime.py), [pipeline](../../starter_v0/ui/pipeline.py) | Luồng chat/direct form, send guard, context và trace |
| [Transcript CLI 20b](../../starter_v0/transcripts/cp3-research-board-v2_groq_20261111T023231396178.transcript.json) và [xác nhận tiếp nối](../../starter_v0/transcripts/cp5_confirmation_20b_20261111T024124787005.transcript.json) | Research, thiếu URL/bổ sung URL, hỏi duyệt trước gửi |
| [Bằng chứng CP4/CP5](../../starter_v0/artifacts/cp4_cp5/README.md) và [pipeline](../../starter_v0/artifacts/cp5_pipeline/README.md) | Run/transcript/UI, triển khai, live AppTest và giới hạn QA |
| [Pytest pipeline](../../starter_v0/artifacts/cp5_pipeline/pytest.txt) | 195 passed tại checkpoint pipeline |
| [Báo cáo nhóm](group_report.md) | Phần A, B3/B4 và checklist bằng chứng |

Các bước tự kiểm tra thuộc phần việc: kiểm tra count/schema của dataset; đối chiếu build/hash; đọc tool events/error chứ không chỉ summary; thử ba ranh giới research/thiếu dữ liệu/gửi; kiểm tra transcript không lộ credential và test reset không mang lịch sử phiên cũ sang.

- Commit cá nhân: LeNguyenAnhNhan

### AI/công cụ và cách tự kiểm tra

- **AI/công cụ cá nhân đã dùng:** Codex, Python/pytest, Streamlit và Git.
- **Nội dung AI hỗ trợ và phần tự sửa:** AI hỗ trợ code UI, test và đọc log; mình định hướng yêu cầu, điều chỉnh demo và báo cáo.
- **Cách cá nhân tự kiểm tra kết quả:** Đối chiếu case với tool calls/args, đọc transcript và lỗi tool; tham chiếu kết quả 195 test passed.
- **Điều đã hiểu và có thể giải thích khi vấn đáp:** Vai trò của prompt, tool schema, runtime; luồng gọi tool và điều kiện hỏi lại, xác nhận hoặc dừng. Routing đúng chưa bảo đảm API và nội dung trả lời đúng.
- **Khó khăn, phần cần cải thiện:** Quota model, lỗi API và phân tích trace; cần kiểm tra thêm giao diện và chất lượng câu trả lời.
- **Tự đánh giá đóng góp:** Phụ trách eval nhóm, UI/pipeline, transcript và tổng hợp báo cáo theo phân công.

## 5. Tự đánh giá

Tập trung hiểu luồng agent, phân biệt lỗi prompt/tool với lỗi API và đối chiếu kết quả bằng log. Khi tối ưu cần giữ cố định model, bộ case và có giả thuyết cho từng vòng. Phần cần cải thiện là đọc trace chủ động hơn và kiểm tra thêm chất lượng nguồn, câu trả lời cùng trải nghiệm UI.
