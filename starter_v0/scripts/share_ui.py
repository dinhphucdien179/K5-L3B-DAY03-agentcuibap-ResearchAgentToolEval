"""Open a demo tunnel and keep its link at the bottom of concise terminal output."""
from __future__ import annotations

import re
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Iterable, TextIO
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "analysis" / "tunnel.log"
ORIGIN = "http://127.0.0.1:8501"
TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com\b")


def show_link(url: str, message: str, log_path: Path) -> None:
    print(f"\n{message}\nGiữ terminal này chạy; Ctrl+C để dừng.", flush=True)
    print(f"Log chi tiết: {log_path}\n\nLink demo:\n{url}", flush=True)


def follow_output(lines: Iterable[str], log: TextIO, log_path: Path) -> bool:
    """Keep raw logs on disk; announce the URL only after connection succeeds."""
    url = None
    connected = False
    announced = False
    for line in lines:
        log.write(line)
        log.flush()
        match = TUNNEL_URL.search(line)
        if match:
            url = match.group(0)
        if "Registered tunnel connection" in line:
            connected = True
        if url and connected and not announced:
            show_link(url, "Tunnel đã kết nối.", log_path)
            announced = True
        elif announced and ("ERR" in line.split() or "Unregistered tunnel connection" in line):
            print(f"\nTunnel báo lỗi; xem chi tiết trong {log_path}.", flush=True)
            print(f"Link demo (có thể tạm gián đoạn):\n{url}", flush=True)
            connected = False
        elif announced and connected and "Registered tunnel connection" in line:
            show_link(url, "Tunnel đã kết nối lại.", log_path)
    return announced


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main() -> int:
    binary = shutil.which("cloudflared")
    if not binary:
        print("Chưa tìm thấy cloudflared. Chạy script bằng môi trường Conda AI20k.")
        return 1
    try:
        with urlopen(f"{ORIGIN}/_stcore/health", timeout=3) as response:
            if response.status != 200:
                raise URLError("UI chưa sẵn sàng")
    except (URLError, OSError) as exc:
        print(f"Chưa kết nối được UI tại {ORIGIN}. Chạy terminal 1 trước.\nChi tiết: {exc}")
        return 1

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    command = [binary, "tunnel", "--url", ORIGIN, "--protocol", "http2",
               "--edge-ip-version", "4", "--no-autoupdate"]
    process = None
    try:
        with LOG_PATH.open("w", encoding="utf-8") as log:
            print("Đang mở tunnel, chờ kết nối…", flush=True)
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, encoding="utf-8", errors="replace",
                                       bufsize=1, start_new_session=True)
            follow_output(process.stdout, log, LOG_PATH)
            code = process.wait()
        print(f"\nTunnel đã kết thúc (exit={code}). Xem log: {LOG_PATH}", flush=True)
        return code or 1
    except KeyboardInterrupt:
        print("\nĐã dừng tunnel.", flush=True)
        return 0
    except OSError as exc:
        print(f"Không mở được tunnel: {exc}", flush=True)
        return 1
    finally:
        if process is not None:
            stop_process(process)


def handle_termination(signum, frame) -> None:
    raise KeyboardInterrupt


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_termination)
    raise SystemExit(main())
