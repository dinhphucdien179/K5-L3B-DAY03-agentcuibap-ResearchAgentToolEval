# Báo cáo cá nhân — Đào Văn Hiệp - 2A202603813

## 1. Thông tin thành viên

- Họ tên: Đào Văn Hiệp
- MSSV: 2A202603813
- Email: 26ai.hiepdv3@vinuni.edu.vn
- GitHub: https://github.com/daohiep2903

## 2. Phần việc phụ trách

Trong nhóm agentcuibap (K5–L3B), tôi được phân công phụ trách CP3:
xây dựng và kiểm thử `research_board`, công cụ giúp agent tổ chức kết quả
tìm kiếm thành bản đồ nguồn để người dùng xem và so sánh.

Phạm vi được giao gồm định nghĩa đầu vào/đầu ra của tool, chuẩn hóa và
gộp URL trùng, nhóm nguồn theo domain, tạo đồ thị, theo dõi kết quả theo
từng truy vấn, bổ sung unit test và hoàn thiện `TOOL.md` cùng mục B5a
trong báo cáo nhóm. Phần review chéo với Nhân tập trung vào cách UI hiển
thị lỗi của tool và giải thích giới hạn của dữ liệu.

## 3. Đóng góp cụ thể và kết quả

- `research_board` dùng Tavily để tìm nguồn, chuẩn hóa URL, gộp kết quả
  trùng, nhóm theo domain và tạo đồ thị nguồn.
- Bản mở rộng hỗ trợ tối đa 3 truy vấn: 1 truy vấn chính và tối đa 2 truy
  vấn so sánh. Tool ghi nhận mỗi URL xuất hiện ở truy vấn nào và thống kê
  mức độ đầy đủ của thông tin nguồn.
- Các test bao phủ luồng thành công, đầu vào không hợp lệ, thiếu API key,
  timeout, HTTP 429, lỗi một phần và giới hạn số request. HTTP được mô
  phỏng trong unit test để kiểm tra hành vi của code mà không gọi API thật.

| Chỉ số | Kết quả đối chiếu báo cáo nhóm |
|---|---:|
| Unit test cho riêng `research_board` | 64 case: 35 ban đầu + 29 bổ sung |
| Toàn bộ bộ test tại thời điểm chốt CP3 v2 | 147 passed, 0 failed, 0 skipped |
| Eval nhóm ở CP4 | 10/10 PASS, trong đó 2 case kiểm tra agent chọn `research_board` |
| Toàn bộ bộ test sau khi nhóm tích hợp pipeline CP5 | 195 passed, 0 failed, 0 skipped |

Kết quả CP4 và CP5 là số liệu tích hợp của cả nhóm. Riêng CP4 dùng
Groq / `openai/gpt-oss-120b`; 10/10 là kết quả trên bộ eval nhóm,
khác với bộ 20 case base của CP2.

## 4. Bằng chứng và cách kiểm tra

- [Đặc tả tool](../../starter_v0/tools/research_board/TOOL.md)
- [Mã nguồn tool](../../starter_v0/tools/research_board/tool.py)
- [Unit test](../../starter_v0/tests/test_tools_todo.py)
- [Kết quả pytest tại mốc CP3 v2](../../starter_v0/artifacts/cp3_v2/pytest.txt)
- [Báo cáo nhóm](group_report.md): mục B5a ghi bằng chứng của tool;
  mục 6 ghi phân công cá nhân.

## 5. Tự đánh giá

Unit test và eval trả lời hai câu hỏi khác nhau. Unit test kiểm tra tool
xử lý dữ liệu đúng sau khi nhận tham số; eval kiểm tra agent có chọn
đúng tool và truyền đúng tham số hay không. Ví dụ, agent có thể gọi đúng
`research_board`, nhưng code vẫn có thể đếm cùng một nguồn hai lần nếu
URL chỉ khác tham số theo dõi hoặc fragment.

Một giới hạn của tool là URL xuất hiện trong nhiều truy vấn chỉ cho thấy
các truy vấn tìm được cùng một nguồn. Điều đó chưa chứng minh các nguồn
đồng ý với nhau, độc lập với nhau hay thông tin trong nguồn đã được xác
minh. Khi đọc kết quả, cần phân biệt truy vấn bị lỗi với truy vấn chạy
thành công nhưng không tìm thấy nguồn.
