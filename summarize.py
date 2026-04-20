import json
import os
import requests
from datetime import datetime, timedelta, timezone
from config import GROQ_API_KEY

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORK_DIR, 'data')
TZ_UTC8 = timezone(timedelta(hours=8))


def load_daily_json():
    now = datetime.now(TZ_UTC8)
    yesterday = (now.replace(hour=0, minute=0, second=0, microsecond=0)
                 - timedelta(days=1))
    date_label = yesterday.strftime('%Y-%m-%d')
    path = os.path.join(DATA_DIR, f"daily_{date_label}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"未找到: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f), date_label


def summarize(data, date_label):
    channel_summary = []
    total = 0
    for ch, info in data['channels'].items():
        n = len(info['messages'])
        total += n
        channel_summary.append(f"@{ch} ({info['title']}): {n}条")

    header = f"监控频道: {', '.join(channel_summary)}。共{total}条消息。"

    messages_text = ""
    for ch, info in data['channels'].items():
        if not info['messages']:
            continue
        messages_text += f"\n--- 频道: @{ch} ({info['title']}) ---\n"
        for msg in info['messages']:
            messages_text += f"[{msg['date']}] (views:{msg['views']}) {msg['text']}\n\n"

    prompt = f"""你是一个网络封锁舆情分析师，服务于一家 VPN 公司。以下是今天从多个 Telegram 频道抓取的原始消息。

频道概况: {header}
时间范围: {data['range']}

原始消息:
{messages_text}

请生成一份简体中文 HTML 邮件报告，要求:

1. 首行概览: 列出监控了哪些频道、共多少条消息
2. 按地区/主题分类整理（如伊朗、俄罗斯、中国、其他），每个分类用不同颜色区块
3. 不要给出原始消息原文，而是整合翻译后给出摘要分析
4. 每个分类包含: 发生了什么、关键数据点、值得关注的趋势
5. 所有非简体中文内容翻译为简体中文
6. 末尾加一段"对 VPN 业务的影响提示"
7. HTML 格式美观、适合邮件阅读，使用内联样式
8. 只输出 HTML 代码，不要包含 ```html 标记或其他说明文字"""

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
            "temperature": 0.3,
        },
        timeout=120,
    )
    resp.raise_for_status()

    html = resp.json()["choices"][0]["message"]["content"]
    if html.startswith("```"):
        html = html.split("\n", 1)[1]
    if html.endswith("```"):
        html = html.rsplit("```", 1)[0]

    report_path = os.path.join(DATA_DIR, f"report_{date_label}.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"报告已生成: {report_path}")
    return report_path, date_label, total


if __name__ == '__main__':
    data, date_label = load_daily_json()
    summarize(data, date_label)
