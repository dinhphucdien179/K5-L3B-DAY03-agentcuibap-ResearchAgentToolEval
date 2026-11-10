# Báo cáo cá nhân — CP2: Tối ưu research agent

## 1. Thông tin thành viên

- Họ tên: Đào Văn Hiệp
- MSSV: 2A202603813
- Email: daohiep302@gmail.com
- GitHub: https://github.com/daohiep2903

## 2. Phần việc phụ trách

Phụ trách CP2: tối ưu system prompt và tool declaration qua ba vòng v1–v3, so sánh với baseline v0 trên bộ base eval gồm 20 case. Provider/model dùng là OpenRouter / `openai/gpt-4o-mini`.

Phân công cá nhân chỉ gồm CP2, không gồm CP3, CP4 hoặc CP5. Codex hỗ trợ triển khai và kiểm tra; các mục tự kiểm tra/tự đánh giá bên dưới cần thành viên xác nhận theo trải nghiệm thực tế.

## 3. Đóng góp cụ thể

Các sản phẩm CP2 đã được tạo với sự hỗ trợ của Codex:

- V1 sửa `system_prompt.md`: thay chỉ dẫn đoán/làm ngay bằng hỏi lại khi thiếu thông tin, giới hạn phạm vi và yêu cầu xác nhận trước khi gửi.
- V2 sửa description của các tool: phân biệt tìm web, bài của tài khoản và thảo luận xã hội; giữ nguồn tìm kiếm khi người dùng đổi chủ đề.
- V3 sửa description của arguments: handle không có `@`, `Top/Latest`, `topic/timeframe`, `response_type` và điều kiện `confirmed=true`.
- Lưu snapshot, run JSON và version log để đối chiếu thay đổi với số đo thật.

| Version | Case đạt | Case accuracy | Routing accuracy |
|---|---:|---:|---:|
| v0 | 13/20 | 65% | 75% |
| v1 | 15/20 | 75% | 95% |
| v2 | 18/20 | 90% | 100% |
| v3 | 18/20 | 90% | 100% |

V3 sửa lỗi `response_type` ở R12 và thiếu `topic=news` ở M02 của v2, nhưng phát sinh lỗi query ở R03/R13. Vì vậy không kết luận v3 tốt hơn v2 về tổng accuracy.

## 4. Bằng chứng

- Phân tích và liên kết tới từng run: [CP2_REPORT.md](../../starter_v0/analysis/CP2_REPORT.md).
- Hash, giả thuyết và metric từng vòng: [version_log.csv](../../starter_v0/artifacts/version_log.csv).
- Artifact đang dùng: [system_prompt.md](../../starter_v0/artifacts/system_prompt.md), [tools.yaml](../../starter_v0/artifacts/tools.yaml). Snapshot tương ứng nằm trong `starter_v0/artifacts/versions/v0` đến `v3`.
- Kiểm tra do Codex thực hiện: hash snapshot khớp run; mỗi run đo đủ 20/20 case, không có provider error; contract test 55 passed sau mỗi vòng; toàn suite cuối 62 passed, 17 skipped thuộc TODO CP3.
- AI/công cụ đã dùng: Codex hỗ trợ sửa artifact, chạy eval/test, phân tích log và soạn báo cáo. Không có commit/PR được tạo cho phần việc này.
- Cách tôi tự kiểm tra kết quả: [Điền việc đã thực sự làm, ví dụ đọc `actual_tool_calls` và `failures` của R12/M02/R03/R13, đối chiếu metric và giải thích nguyên nhân.]

## 5. Tự đánh giá

### Phạm vi đóng góp

CP3, CP4 và CP5 là sản phẩm khác của nhóm, không tính vào đóng góp cá nhân trong báo cáo này. Codex hỗ trợ chỉnh artifact CP2, chạy eval/test và soạn bằng chứng; việc tự kiểm tra cần được thành viên xác nhận trung thực.

Kết quả kỹ thuật cho thấy accuracy tăng 25 điểm phần trăm so với baseline, còn routing tăng 25 điểm phần trăm. V3 vẫn còn hai case sai arguments; query gần nghĩa bị grader chấm sai do so khớp chính xác. Một run cho mỗi version chưa đủ đánh giá độ ổn định hoặc khả năng tổng quát.

Điểm cần hiểu khi trình bày: system prompt quy định hành vi chung; tool description giúp chọn đúng công cụ; parameter description giúp truyền đúng arguments. Chỉ đổi một giả thuyết mỗi vòng giúp giải thích kết quả đo, nhưng chưa chứng minh quan hệ nhân quả qua một lần chạy.
