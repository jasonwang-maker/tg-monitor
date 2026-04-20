"""完整流水线: 抓取 → AI 整理 → 发邮件"""
import subprocess
import sys
import os

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(WORK_DIR)

def run(script):
    print(f"\n{'='*40}")
    print(f"执行: {script}")
    print('='*40)
    result = subprocess.run([sys.executable, script], cwd=WORK_DIR)
    if result.returncode != 0:
        print(f"✗ {script} 失败，退出码 {result.returncode}")
        sys.exit(1)

run('daily_fetch.py')

from summarize import load_daily_json, summarize
data, date_label = load_daily_json()
report_path, date_label, total = summarize(data, date_label)

from send_email import send
subject = f"📡 TG 频道监控日报 {date_label} ({total}条新消息)"
send(subject, report_path)

print(f"\n全部完成!")
