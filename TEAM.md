# Nhóm agentcuibap — L3B

- Repo: [K5-L3B-DAY03-agentcuibap-ResearchAgentToolEval](https://github.com/dinhphucdien179/K5-L3B-DAY03-agentcuibap-ResearchAgentToolEval)
- Nhánh nộp: `main`.
- [Báo cáo nhóm](report/team/group_report.md) · [Cách chạy](starter_v0/RUNBOOK.md) · [Kiểm tra bản nộp](starter_v0/analysis/validation.json).
- UI local: http://localhost:8501. Link public được tạo khi chạy `scripts/share_ui.py`; cần giữ UI và tunnel hoạt động.

## Thành viên và đóng góp

| Họ tên | MSSV | Email | GitHub | Phần việc và bằng chứng |
|---|---|---|---|---|
| Đinh Phúc Diên | 2A202603876 | 26ai.diendp@vinuni.edu.vn | [dinhphucdien179](https://github.com/dinhphucdien179) | Cấu hình AI20k/OpenRouter, CP2 v5–v6, bốn tool nghiên cứu, trực tiếp chạy kiểm tra và chat demo; [báo cáo](report/team/2A202603876_DinhPhucDien.md) |
| Đào Văn Hiệp | 2A202603813 | 26ai.hiepdv3@vinuni.edu.vn | [daohiep2903](https://github.com/daohiep2903) | CP2: tối ưu prompt/tool declaration và phân tích v1–v3; [báo cáo](report/team/2A202603813_DaoVanHiep.md) |
| Lê Nguyễn Anh Nhân | 2A202603838 | 26ai.nhanlna@vinuni.edu.vn | [ying684](https://github.com/ying684) | Eval nhóm, UI/pipeline, transcript và tổng hợp báo cáo; [báo cáo](report/team/2A202603838_LeNguyenAnhNhan.md) |



## Bằng chứng chung

- CP2: [version log](starter_v0/artifacts/version_log.csv), [snapshot OpenRouter](starter_v0/artifacts/versions/), [nhật ký Groq](starter_v0/artifacts/cp2/experiment_log.md).
- CP3: [tool registry](starter_v0/tools/__init__.py), [tool declarations](starter_v0/artifacts/tools.yaml), [unit test](starter_v0/tests/test_tools_todo.py).
- CP4: [10 case nhóm](starter_v0/data/eval_group.json), [test dataset](starter_v0/tests/test_eval_group.py).
- CP5: [UI](starter_v0/app.py), [pipeline](starter_v0/ui/pipeline.py), [chat thực tế 5 lượt](starter_v0/transcripts/v4_openrouter_20261110T214232005322.transcript.json).
- Kiểm tra cuối: [validation.json](starter_v0/analysis/validation.json), [JUnit XML](starter_v0/analysis/pytest_final.xml).

Các điểm model trong báo cáo được dẫn đến run và snapshot tương ứng; không xem điểm cũ là kết quả của bản v7 hiện tại.
Commit nộp bài được xác định từ lịch sử `main` sau khi nhóm commit và push.
