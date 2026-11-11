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
| 1 | Đinh Phúc Diên | 2A202603876 | 26ai.diendp@vinuni.edu.vn | [dinhphucdien179](https://github.com/dinhphucdien179) | Cấu hình, vận hành, kiểm thử và hoàn thiện bài với AI hỗ trợ |
| 2 | Đào Văn Hiệp | 2A202603813 | 26ai.hiepdv3@vinuni.edu.vn | https://github.com/daohiep2903 | CP2 |
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
- 
## Đào Văn Hiệp — 2A202603813

### Phần việc phụ trách

- CP2: tối ưu prompt và tool declaration v1–v3.

### Đóng góp cụ thể

- CP2 đạt case accuracy 65% → 75% → 90% → 90%; lưu snapshot, hash, giả thuyết và phân tích lỗi. V3 không tăng tổng accuracy so với v2.
- Codex hỗ trợ code, chạy kiểm tra và soạn báo cáo; thành viên bổ sung việc tự kiểm tra thực tế. Chưa có public URL hoặc người ngoài nhóm dùng thử.

### Bằng chứng

- [Báo cáo cá nhân](report/team/2A202603813_DaoVanHiep.md).
- [CP2](starter_v0/analysis/CP2_REPORT.md), [version log](starter_v0/artifacts/version_log.csv).
