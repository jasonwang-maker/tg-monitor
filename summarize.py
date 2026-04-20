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

    channel_list_html = ""
    for ch, info in data['channels'].items():
        n = len(info['messages'])
        desc = {
            'netblocks': '全球断网/封锁实时监测',
            'usher2': '俄罗斯互联网封锁追踪 (Эшер II)',
            'zatelecom': '俄罗斯电信行业动态 (ЗаТелеком)',
            'INTERNETFORIRAN': '伊朗互联网自由',
            'vps_xhq': 'VPS信号旗播报 (中国/VPN行业)',
        }.get(ch, '')
        channel_list_html += f"@{ch} ({info['title']}) — {desc} — {n}条消息\n"

    prompt = f"""你是一个网络封锁舆情分析师，服务于一家 VPN 公司（主要客户为中国用户）。以下是今天从 Telegram 频道抓取的原始消息。

## 监控频道
{channel_list_html}
时间范围: {data['range']}
共计: {total}条消息

## 原始消息
{messages_text}

## 任务
生成一份简体中文 HTML 邮件报告。

## 严格要求

**格式要求：**
1. 报告开头用表格列出每个频道的名称、说明、本期消息数量
2. 按地区分类整理（伊朗、俄罗斯、中国、其他），每个地区用不同颜色区块
3. 末尾加"对 VPN 业务的影响提示"
4. HTML 格式，使用内联样式，适合邮件阅读
5. 只输出 HTML 代码，不要包含 ```html 标记

**内容要求：**
1. 所有非简体中文内容（英文、俄文、波斯文）必须翻译为简体中文
2. 不要给原始消息原文，整合翻译后给出详细摘要
3. 每条有实质内容的消息都要被覆盖到，不要遗漏重要信息
4. 包含具体数据点：天数、小时数、百分比、地区数量等原文提到的数字
5. 技术细节要保留：协议名称（如 SNI Spoofing、VLESS、DPI）、工具名、具体封锁手段
6. 如果某个地区没有消息，明确写"本期无相关消息"，不要编造内容

**绝对禁止：**
- 不要编造或推测原始消息中没有的信息
- 不要添加原文中不存在的数据或事件
- 如果信息不足以得出结论，就不要下结论"""

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
