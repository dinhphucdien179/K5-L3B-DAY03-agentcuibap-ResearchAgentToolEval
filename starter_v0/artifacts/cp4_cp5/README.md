# CP4 + CP5 — group eval and NEXUS live UI

## Kết quả chính

- CP4: đúng **10 case mới, 5 single + 5 multi**, 2 case route `research_board`, có case dùng `compare_queries`.
- Run group thật trên Groq `openai/gpt-oss-120b`: **10/10 PASS, 0 provider errors**, routing/argument/multi-turn đều 100%.
- CP5: NEXUS Streamlit gồm chat, research desk, graph pan/zoom/chọn node, evidence card/provenance, workflow, coverage, query comparison và tool trace.
- Test cuối: **184 passed, 0 failed, 0 skipped**; 147 case trước giữ nguyên, thêm 12 case kiểm tra dataset và 25 runtime/AppTest UI.
- Có CLI transcript thật, tiếp nối xác nhận thật và AppTest UI chạy provider/Tavily thật. Không bịa phản hồi nhóm khác hoặc nhận mock là live run.

## Link và cách chạy

**Public:** <https://connection-hawaii-narrative-mom.trycloudflare.com>

**Local:** <http://127.0.0.1:8501>

Link Quick Tunnel là tạm thời: máy, Streamlit và cloudflared phải còn chạy. Khởi động lại tunnel có thể tạo URL khác. Các process hiện được giữ chạy nền; PID và kiểm tra cuối nằm trong [public_deployment.json](public_deployment.json).

Từ `starter_v0/`, trong môi trường Python `lab3`:

```powershell
python -m pip install -r requirements.txt
$env:NEXUS_MODEL = "openai/gpt-oss-20b"
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Ở terminal thứ hai, với cloudflared đã cài từ nguồn chính thức:

```powershell
cloudflared tunnel --url http://127.0.0.1:8501 --no-autoupdate --protocol http2
```

Trên máy hiện tại có thể gọi binary tại `$env:TEMP\codex-research-tunnel\cloudflared.exe`. Infrastructure logs phục vụ vận hành nằm ngoài gói bằng chứng; kết quả kiểm tra được giữ trong public_deployment.json. Không đưa API key vào trình duyệt hoặc tham số URL. Chỉ server đọc `.env`.

## CP4 — dataset và run

[eval_group.json](../../data/eval_group.json) được thiết kế từ lỗi thật đã quan sát trong v0–v4, dùng chủ đề/câu chữ mới. Mỗi case có `what_it_tests`, `origin_failure`, `origin_cases` và `from_run`. Chỉ đối chiếu args quan trọng.

- [group_freeze.json](group_freeze.json): thời điểm/hash chốt dataset và artifact trước request đầu tiên.
- [eval_group.frozen.json](eval_group.frozen.json): bản case được chốt, byte-equal dữ liệu đang dùng.
- [system_prompt.md](system_prompt.md), [tools.yaml](tools.yaml): snapshot CP3 v2, không sửa để làm đẹp kết quả.
- [Run group](../../runs/cp3-research-board-v2_B_group_groq_20261111T022506173733.json).
- [group_analysis.json](group_analysis.json): summary, tool health, board execution và review tay.
- [test_eval_group.py](../../tests/test_eval_group.py): đếm 5/5, kiểm tra nguyên gốc, registry/schema và nguồn failure có thật.

Lệnh tương đương, giữ Telegram credential không khả dụng trong process eval:

```powershell
python run_eval.py --provider groq --model openai/gpt-oss-120b --version cp3-research-board-v2 --suite group --eval-cases data/eval_group.json --system-prompt artifacts/cp4_cp5/system_prompt.md --tools artifacts/cp4_cp5/tools.yaml
```

Có đúng một run group, không sửa cases sau khi xem kết quả. Đây không phải vòng tối ưu chỉ đổi nhãn và không phải tăng base accuracy 90% lên 100%: group là bộ 10 case khác. Hai board thực thi thật có `status=ok`: G01 giữ 4 item/4 domain; G06 so sánh 2 query, giữ 8 item/8 domain.

**Giới hạn:** G09/G10 gọi đúng social tool/args nhưng API trả HTTPError. G05 không gọi tool đúng như yêu cầu; phần giải thích phân biệt overlap với claim agreement nhưng mô tả nhầm board gọi lookup/social/timeline, trong khi code dùng Tavily trực tiếp. Điểm tự động không chấm những sai lệch nội dung đó.

## CP5 — hội thoại live và quota

Input test là scripted synthetic prompts, được giữ trong transcript gốc, không phải lời của nhóm khác.

1. Request bình thường: research_board → format, có nguồn.
2. Thiếu URL: clarify và dừng chờ.
3. Bổ sung URL: fetch đúng trang.
4. Yêu cầu đăng bản nháp: hỏi đích Telegram còn thiếu.
5. Tiếp nối sau khi cung cấp đích: clarify yes/no, nhắc đúng draft/kênh, không gửi thật.

Run đầu dùng 120b chỉ hoàn thành hai lượt, hai lượt sau gặp **429 quota tokens/ngày**. Giữ nguyên [transcript lỗi](../../transcripts/cp3-research-board-v2_groq_20261111T022652587579.transcript.json) và [quota_event.json](quota_event.json); không tính nó là hội thoại hoàn tất.

CP5 sau đó dùng `openai/gpt-oss-20b`, có [4 lượt CLI, 0 provider error](../../transcripts/cp3-research-board-v2_groq_20261111T023231396178.transcript.json) và [lượt tiếp nối xác nhận](../../transcripts/cp5_confirmation_20b_20261111T024124787005.transcript.json). Tiếp nối dùng hàm gốc `chat.run_model_tool_loop` với đúng user/assistant history thật từ CLI, ghi `resumes_transcript`; không chèn response giả vào file cũ.

UI dùng `NEXUS_MODEL` riêng để không sửa `.env`/provider hoặc bằng chứng group 120b. Không gán điểm group cho 20b, không nhận model switch là vòng cải thiện CP2. Telegram credentials bị gỡ khỏi child process CLI/eval sau khi load dotenv; trên public UI, `send` bị chặn ngay ở runtime trước implementation, kể cả `confirmed=true`.

## UI và kiểm tra

Code: [app.py](../../app.py), [ui/runtime.py](../../ui/runtime.py), [ui/components.py](../../ui/components.py), [styles.css](../../ui/styles.css).

- Mở trang không gọi model/tool. Câu mẫu chỉ điền input, user phải submit.
- Chat giữ structured context theo session; khóa gửi/đăng và hiển thị trạng thái blocked.
- Tool error/partial có banner độc lập với câu trả lời model, cùng trace đã redact.
- Transcript riêng UUID/session, có start/end thật, artifact/policy/runtime hashes; người dùng chỉ download transcript phiên mình.
- Giới hạn 30 lượt/phiên, 4 vòng và 8 tool call/lượt; context model có giới hạn, raw trace vẫn được giữ đầy đủ.
- Source text được escape, graph dùng JSON escaping + SVG `textContent` trong iframe do app tạo.

Bằng chứng UI thật:

- [ui_apptest_live.json](ui_apptest_live.json): form 2 query gọi Tavily thật, 4 item/domain, graph 10 node/12 edge, không render exception.
- [ui_chat_and_board_live.json](ui_chat_and_board_live.json): chat Groq 20b hỏi URL thiếu, rồi direct desk gọi Tavily thật; [transcript UI](../../transcripts/ui_5081701108074068b13e46d924d9f7a3.transcript.json).
- [ui_issue_log.json](ui_issue_log.json): avatar không hợp lệ sau lượt đầu đã được phát hiện, sửa và thêm regression; không che lần kiểm tra lỗi.
- [test_ui_runtime.py](../../tests/test_ui_runtime.py): send guard, error/redaction, context/call caps và AppTest empty/error sau submit.
- [pytest.txt](pytest.txt), [pytest.xml](pytest.xml): 184 passed.

**Giới hạn QA:** Computer Use dừng vì không xác định được current browser URL trên Windows đủ chắc chắn; không thử bypass hoặc đổi công nghệ để tiếp tục GUI. Official Streamlit AppTest đã kiểm chứng render/action/backend; public root/health HTTP 200 và WebSocket handshake 101. Không nhận đây là screenshot/visual QA, kiểm chứng mobile hoặc thử chéo bởi nhóm khác.

## Giữ nguyên bằng chứng và điều còn thiếu

[protected_hashes.json](protected_hashes.json) được tạo trước CP4/CP5 cho 125 file hiện có. Không đổi evaluator, fixed base/extension, provider, tool implementation/declaration/prompt hoặc artifact/run/CSV CP2–CP3. File mới phục vụ UI/tests/bằng chứng; file có sẵn chỉ thay dataset nhóm, requirements và báo cáo.

[validation.json](validation.json) đối chiếu hash, dataset freeze, group score, transcript, unit test và endpoint. Bảng A1–A3/B3/B4/B5a ở [group_report.md](../../../report/team/group_report.md) trỏ tới các file thật.

Chưa có phản hồi thực tế từ nhóm khác, chưa gửi Telegram và không nhận bonus gửi tin. Thông tin thành viên/commit cá nhân cần do nhóm điền theo thực tế; không tự bịa. Phiên bản local/public phụ thuộc quota dịch vụ và máy đang chạy, không phải hosting bền vững.

Nguồn chính thức: [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest), [Groq models](https://console.groq.com/docs/models), [Groq rate limits](https://console.groq.com/docs/rate-limits), [Cloudflare Quick Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/).
