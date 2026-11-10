# Chạy Research Studio — Conda AI20k

Chạy tất cả lệnh dưới đây trong **thư mục `starter_v0`**.
Nếu terminal đang kết thúc bằng `/starter_v0$`, bạn đã ở đúng chỗ.
Nếu đang ở thư mục gốc project, chạy `cd starter_v0` một lần.

## 1. Chuẩn bị

Môi trường `AI20k` cần có dependency của `requirements.txt`;
`cloudflared` cần có trong môi trường này nếu muốn chia sẻ link.

Điền key vào `.env` (xem `.env.example`), không commit file này:

```dotenv
OPENROUTER_API_KEY=
TAVILY_API_KEY=
FIRECRAWL_API_KEY=
RAPIDAPI_KEY=
RAPIDAPI_TWITTER_HOST=twitter-api45.p.rapidapi.com
```

## 2. Chạy UI — terminal 1

```bash
conda run --no-capture-output -n AI20k python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

Mở **http://localhost:8501**. Trong thanh bên, chọn **OpenRouter** và model
**`openai/gpt-4o-mini`**, rồi nhập câu hỏi hoặc chọn prompt mẫu.
Xem **Theo dõi agent** để kiểm tra tool; bấm **Tải transcript JSON** để lưu phiên demo.

## 3. Chia sẻ link — terminal 2 (tuỳ chọn)

```bash
conda run --no-capture-output -n AI20k python scripts/share_ui.py
```

Mở link **`https://…trycloudflare.com` ở cuối terminal** sau khi báo đã kết nối.
Log dài được lưu trong `analysis/tunnel.log`.
Mỗi lần chạy tunnel có thể có link mới. Giữ cả hai terminal chạy khi demo;
nhấn **Ctrl+C** ở từng terminal để dừng. Dừng tunnel thì link chia sẻ hết hoạt động.

## Kiểm tra code (tuỳ chọn)

```bash
conda run --no-capture-output -n AI20k python -m pytest tests -q
```
