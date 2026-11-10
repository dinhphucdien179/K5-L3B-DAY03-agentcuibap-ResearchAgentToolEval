# Nhóm agentcuibap — L3B

## Thông tin nộp bài

- Tên nhóm: **agentcuibap**
- Lớp: **L3B**
- Repo: [K5-L3B-DAY03-agentcuibap-ResearchAgentToolEval](https://github.com/dinhphucdien179/K5-L3B-DAY03-agentcuibap-ResearchAgentToolEval)
- Nhánh nộp: `main`
- Link demo hiện tại: [https://wives-rfc-clocks-delayed.trycloudflare.com](https://wives-rfc-clocks-delayed.trycloudflare.com) — hoạt động khi UI và tunnel còn chạy.
- Commit chốt bài: chưa tạo; HEAD hiện tại `c68da4cdb50c118c9f00622bd72e6cd7afc57b18` là commit của đề gốc, không phải commit hoàn thiện bài.

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
|---:|---|---|---|---|---|
| 1 | Đinh Phúc Diên | 2A202603876 | dinhphucdien179@gmail.com | [dinhphucdien179](https://github.com/dinhphucdien179) | Cấu hình, vận hành, kiểm thử và hoàn thiện bài với AI hỗ trợ |

## Đinh Phúc Diên — 2A202603876

### Phần việc trực tiếp thực hiện

- Cấu hình môi trường Conda `AI20k`, provider OpenRouter và API key cho các tool.
- Chạy preflight, unit test và base/group eval; cung cấp log để đối chiếu lỗi.
- Khởi chạy UI Streamlit và Cloudflare Tunnel, xác nhận truy cập được giao diện.
- Thực hiện phiên chat 5 lượt: research, thiếu URL, bổ sung URL, yêu cầu gửi và hủy gửi.
- Phối hợp với Codex để xây dựng tool mới, test, UI, phân tích log và hoàn thiện báo cáo.

### Đóng góp và hỗ trợ AI

Codex hỗ trợ triển khai bốn tool mới (`investigate`, `compare_research`,
`citation_audit`, `deduplicate`), sửa lỗi tool/runtime, soạn test, eval và UI.
Đinh Phúc Diên trực tiếp vận hành các bước kiểm tra và phiên chat được ghi nhận
bên dưới. Nội dung có AI hỗ trợ được công khai trong báo cáo cá nhân.

### Bằng chứng

- [Báo cáo cá nhân](report/team/2A202603876_DinhPhucDien.md)
- [Báo cáo nhóm](report/team/group_report.md)
- [Kết quả thành viên tự kiểm tra](starter_v0/analysis/member_verification_20261110.md)
- [Base eval: 19/20](starter_v0/runs/v4_B_base_openrouter_20261110T213840374908.json)
- [Group eval: 9/10](starter_v0/runs/v4_B_group_openrouter_20261110T213941166369.json)
- [Transcript tương tác: 5 lượt](starter_v0/transcripts/v4_openrouter_20261110T214232005322.transcript.json)
- [Version log](starter_v0/artifacts/version_log.csv)
