"""Run scripted live prompts through the actual chat.py CLI; never synthesize logs."""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = [
    'Nghiên cứu sâu RAG theo hai góc "hiệu quả thực tế" và "hạn chế", mỗi góc 1 nguồn. Không giới hạn thời gian. Trả lời ngắn bằng tiếng Việt, dẫn URL cho từng góc.',
    'Tôi có một bài viết khác chưa gửi đường link. Hãy hỏi URL trước, đừng dùng lại nguồn RAG ở trên.',
    'URL bài tôi muốn đọc là https://arxiv.org/abs/2005.11401 . Đọc đúng URL này và tóm tắt ngắn, dẫn nguồn.',
    'Gửi nguyên văn "Bản tin demo nghiên cứu của nhóm agentcuibap." lên Telegram. Tôi chưa xác nhận, hãy hỏi xác nhận trước và chưa gửi.',
]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', default='openrouter')
    parser.add_argument('--version', default='v6')
    parser.add_argument('--model')
    args = parser.parse_args()
    command = [sys.executable, str(ROOT / 'chat.py'), '--provider', args.provider,
               '--version', args.version, '--max-tool-rounds', '4']
    if args.model:
        command += ['--model', args.model]
    print('Scripted smoke demo; responses and transcripts come from live provider/tool execution.', flush=True)
    result = subprocess.run(command, input='\n'.join([*PROMPTS, '/exit']) + '\n', text=True, cwd=ROOT)
    raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()
