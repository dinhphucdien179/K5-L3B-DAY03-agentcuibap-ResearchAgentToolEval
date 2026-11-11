# Báo cáo cá nhân — Đinh Phúc Diên

## 1. Thông tin

- Họ tên: **Đinh Phúc Diên**.
- MSSV: **2A202603876**.
- Email: 26ai.diendp@vinuni.edu.vn.
- GitHub: [dinhphucdien179](https://github.com/dinhphucdien179).
- Nhóm: **agentcuibap**, lớp **L3B**.

## 2. Phần việc tôi phụ trách

Theo [phân công của nhóm](../../TEAM.md), tôi phụ trách cấu hình môi trường
Conda `AI20k` và OpenRouter, phần tối ưu CP2 ở v5–v6, bốn tool nghiên cứu của
CP3, cùng việc chạy kiểm tra và thực hiện phiên chat demo.

## 3. Nội dung thực hiện

### Cấu hình và vận hành

Tôi cấu hình provider OpenRouter với model `openai/gpt-4o-mini`, đặt API key
trong `.env` và sử dụng môi trường `AI20k` để tránh cài nhầm dependency vào
Python hệ thống. Tôi trực tiếp chạy preflight, pytest và hai bộ eval ở bản v4;
kết quả terminal được lưu trong [bản kiểm tra thực tế](../../starter_v0/analysis/member_verification_20261110.md).

Tôi cũng khởi chạy Streamlit và Cloudflare Tunnel để kiểm tra giao diện. Khi
gặp lỗi đường dẫn `starter_v0/app.py` trong lúc đã đứng ở `starter_v0`, tôi xác
định lại thư mục chạy và dùng đường dẫn `app.py`. Link tunnel chỉ dùng được
khi ứng dụng và tiến trình tunnel còn hoạt động.

### CP2 — Tối ưu v5 và v6

Tôi tập trung vào ranh giới xác nhận gửi nội dung. Ở v5, phần thay đổi nằm
trong system prompt: ưu tiên hỏi xác nhận khi người dùng yêu cầu gửi, kể cả
khi bản nháp còn thiếu. Kết quả base vẫn là 19/20; case R12 vẫn chọn sai
`response_type`, nên cách sửa này chưa giải quyết được lỗi.

Ở v6, phần thay đổi được thu hẹp vào mô tả của `clarify` trong `tools.yaml`:
làm rõ việc dùng `yes_no` cho yêu cầu gửi lần đầu. Kết quả lưu của vòng này
là base 20/20 và group 10/10. Tôi phân biệt sự đồng ý tiếp tục quy trình với
việc duyệt đúng nội dung cuối cùng; hai việc này không được xem là một.

| Phiên bản OpenRouter | Base | Group | Ghi nhận |
|---|---:|---:|---|
| v4 | 19/20 | 9/10 | Lần tôi trực tiếp chạy và cung cấp log |
| v5 | 19/20 | 10/10 | Sửa prompt, R12 vẫn chưa đạt |
| v6 | 20/20 | 10/10 | Sửa mô tả clarify, R12 đạt |

### CP3 — Bốn tool nghiên cứu

Phần công cụ tôi phụ trách gồm:

| Tool | Mục đích và điểm cần kiểm tra |
|---|---|
| `investigate` | Thu thập bằng chứng theo nhiều góc nhìn, giữ nguồn và báo phần thiếu dữ liệu |
| `compare_research` | Lập ma trận bằng chứng theo cùng tiêu chí cho nhiều đối tượng |
| `citation_audit` | Kiểm tra ID nguồn, URL và đoạn chưa có trích dẫn; không kết luận nội dung đúng sai |
| `deduplicate` | Gộp URL trùng do tracking, giữ nguồn đầu và tham số có ý nghĩa |

Các tool có implementation, `TOOL.md`, registry và schema tương ứng. Phần
kiểm thử bao phủ đầu vào không hợp lệ, thiếu key, lỗi truy vấn từng phần,
URL và citation. Các regression được giữ để tránh sửa một lỗi rồi làm mất
nguồn đã thu thập hoặc gộp nhầm hai URL khác nội dung.

### Kiểm tra và chat demo

Trong phiên `chat.py` tôi trực tiếp thực hiện 5 lượt: nghiên cứu RAG, yêu cầu
đọc bài khi chưa có URL, bổ sung URL arXiv, yêu cầu gửi một bản tin và hủy gửi.
Phiên này không gọi `send`. Lượt nghiên cứu đầu gọi `investigate` hai lần;
tôi giữ nguyên transcript để phản ánh hành vi thực tế.

## 4. Bằng chứng

- [Preflight, pytest và eval tôi trực tiếp chạy](../../starter_v0/analysis/member_verification_20261110.md): 257 test pass ở bản v4.
- [Giả thuyết v5](../../starter_v0/artifacts/versions/v5/hypothesis.json) và [v6](../../starter_v0/artifacts/versions/v6/hypothesis.json).
- [Base v6](../../starter_v0/runs/v6_B_base_openrouter_20261110T234242756239.json) và [group v6](../../starter_v0/runs/v6_B_group_openrouter_20261110T234157985676.json).
- [Unit test tool](../../starter_v0/tests/test_tools_todo.py) và [regression CP3](../../starter_v0/tests/test_cp3_regressions.py).
- [Transcript tôi trực tiếp chạy](../../starter_v0/transcripts/v4_openrouter_20261110T214232005322.transcript.json).
- [Kiểm tra giao diện và tunnel](../../starter_v0/analysis/ui_connectivity_current.json).

## 5. Cách tôi đối chiếu kết quả

Tôi đối chiếu tool được gọi và arguments trong run JSON, không chỉ nhìn câu
trả lời cuối. Tôi kiểm tra riêng trạng thái API, số case được đo và lỗi provider.
Với tool, tôi phân biệt unit test của implementation với eval khả năng model
chọn tool; một trong hai đạt không bảo đảm phần còn lại đạt.

Kết quả kiểm tra chung hiện tại là **407 test pass, 0 fail, 0 skip**, được ghi
trong [validation.json](../../starter_v0/analysis/validation.json). Đây là kết
quả của bản chung, không phải số test của riêng bốn tool tôi phụ trách. Các
điểm v6 ở trên thuộc snapshot v6; bản v7 chưa có run model để đối chiếu.

## 6. Tự đánh giá và phần cần cải thiện

Phần tôi tập trung giải quyết là môi trường chạy, ranh giới xác nhận gửi và
các tool nghiên cứu có nguồn để đối chiếu. Qua các lần kiểm tra, tôi rút ra
rằng cần thu hẹp từng thay đổi và đo lại thay vì xem một quy tắc trong prompt
là đã đủ bảo đảm hành vi.

Điểm cần cải thiện là kiểm tra chất lượng nguồn và độ ổn định của câu trả lời.
Một số API mạng xã hội vẫn trả lỗi HTTP dù routing đúng. Tôi chưa có bằng
chứng gửi Telegram thật, chạy model local hoặc thử nghiệm với người ngoài nhóm.
