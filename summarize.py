import json
import os
import re
import requests
from datetime import datetime, timedelta, timezone
from config import GEMINI_API_KEY

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORK_DIR, 'data')
TZ_UTC8 = timezone(timedelta(hours=8))

CHANNEL_DESC = {
    'netblocks': '全球断网/封锁实时监测',
    'usher2': '俄罗斯互联网封锁追踪 (Эшер II)',
    'zatelecom': '俄罗斯电信行业动态 (ЗаТелеком)',
    'INTERNETFORIRAN': '伊朗互联网自由',
    'vps_xhq': 'VPS信号旗播报 (中国/VPN行业)',
    'projectXtls': 'Project X 翻墙协议开发 (VLESS/XTLS)',
    'projectVless': 'Project VLESS 俄语翻墙技术讨论群',
}

HTML_TEMPLATE = """<html>
<body style="font-family: -apple-system, Arial, sans-serif; max-width: 780px; margin: 0 auto; color: #333; padding: 20px;">

<h2 style="border-bottom: 2px solid #2563eb; padding-bottom: 8px; margin-bottom: 4px;">
  📡 TG 频道监控日报
</h2>
<p style="color: #666; margin-top: 4px; font-size: 14px;">
  监控时间：{time_range}<br>
  监控频道：{channel_names}<br>
  共抓取 <strong>{total} 条</strong>消息（{channel_counts}）
</p>

<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">

{sections}

<h3 style="color: #059669; margin-bottom: 8px;">📊 对 VPN 业务的影响提示</h3>
<div style="background: #ecfdf5; border-radius: 8px; padding: 14px 16px; margin-bottom: 16px; line-height: 1.8; font-size: 14px;">
{business_impact}
</div>

<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
<p style="color: #999; font-size: 12px;">
  自动生成于 {gen_time} &nbsp;|&nbsp; 数据来源：Telegram 频道监控
</p>

</body>
</html>"""


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


def call_gemini(prompt):
    import time
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 8000,
            "temperature": 0.2,
        },
    }
    for attempt in range(3):
        resp = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=180,
        )
        if resp.status_code == 200:
            parts = resp.json()["candidates"][0]["content"]["parts"]
            return "".join(p["text"] for p in parts if "text" in p and "thoughtSignature" not in p)
        if resp.status_code in (429, 500, 502, 503):
            wait = 10 * (attempt + 1)
            print(f"Gemini API {resp.status_code}, retrying in {wait}s... (attempt {attempt+1}/3)")
            time.sleep(wait)
            continue
        resp.raise_for_status()
    resp.raise_for_status()


def summarize(data, date_label):
    channel_counts_list = []
    total = 0
    channel_names_list = []
    for ch, info in data['channels'].items():
        n = len(info['messages'])
        total += n
        channel_counts_list.append(f"{info['title']} {n}条")
        channel_names_list.append(info['title'])

    messages_text = ""
    for ch, info in data['channels'].items():
        if not info['messages']:
            messages_text += f"\n--- 频道: @{ch} ({info['title']}) — {CHANNEL_DESC.get(ch, '')} ---\n(本期无消息)\n"
            continue
        messages_text += f"\n--- 频道: @{ch} ({info['title']}) — {CHANNEL_DESC.get(ch, '')} ---\n"
        for msg in info['messages']:
            text = msg['text'][:500] + ('...' if len(msg['text']) > 500 else '')
            messages_text += f"[{msg['date']}] (views:{msg['views']}) {text}\n\n"

    prompt = f"""你是一个网络封锁舆情分析师。请根据以下原始消息，生成地区分类摘要。

## 原始消息
{messages_text}

## 任务
根据消息内容自动识别涉及的国家/地区，按地区分类进行翻译和深度整理。

## 输出格式
对每个涉及的地区，输出以下格式（用 === 分隔地区）：

===地区名===
标题：一句话总结该地区本期的核心动态
内容：
用多个加粗小标题分段（如 **断网现状：** **技术动态：** **社会影响：** 等），每段详细展开。要求：
- 地区名用简体中文（如：伊朗、俄罗斯、中国、土耳其、缅甸等）
- 所有非简体中文内容必须翻译为简体中文
- 保留所有具体数字（天数、小时、百分比、地区数量等）
- 保留所有技术术语（SNI Spoofing、DPI、VLESS、NAT、Domain Fronting 等）
- 每条有实质内容的原始消息都必须被覆盖，不要遗漏
- 只输出有消息的地区，没有消息的地区不要输出
===END===

最后输出：
===业务影响===
针对 VPN 公司（主要客户为中国用户）的业务影响提示，用要点列表。
===END===

## 严格禁止
- 不要编造原始消息中没有的信息
- 不要添加原文中不存在的数据或事件
- 没有消息就说没有，不要填充"""

    result = call_gemini(prompt)
    print(f"AI 返回长度: {len(result)} 字符")
    print(f"AI 返回前200字: {result[:200]}")

    region_flags = {
        '伊朗': '🇮🇷', '俄罗斯': '🇷🇺', '中国': '🇨🇳', '土耳其': '🇹🇷',
        '缅甸': '🇲🇲', '巴基斯坦': '🇵🇰', '印度': '🇮🇳', '古巴': '🇨🇺',
        '委内瑞拉': '🇻🇪', '埃塞俄比亚': '🇪🇹', '朝鲜': '🇰🇵', '越南': '🇻🇳',
        '乌克兰': '🇺🇦', '白俄罗斯': '🇧🇾', '叙利亚': '🇸🇾', '苏丹': '🇸🇩',
    }
    color_pool = [
        {'color': '#dc2626', 'bg': '#fef2f2'},
        {'color': '#2563eb', 'bg': '#eff6ff'},
        {'color': '#d97706', 'bg': '#fffbeb'},
        {'color': '#059669', 'bg': '#ecfdf5'},
        {'color': '#7c3aed', 'bg': '#f5f3ff'},
        {'color': '#db2777', 'bg': '#fdf2f8'},
        {'color': '#0891b2', 'bg': '#ecfeff'},
        {'color': '#ca8a04', 'bg': '#fefce8'},
    ]

    region_blocks = re.findall(r'===([^=]+?)===\s*(.*?)===END===', result, re.DOTALL)
    region_blocks = [(name.strip(), body.strip()) for name, body in region_blocks
                     if name.strip() != '业务影响']

    sections_html = ""
    business_html = ""

    for i, (region, block) in enumerate(region_blocks):
        style = color_pool[i % len(color_pool)]
        flag = region_flags.get(region, '🌐')

        title_line = ""
        content = block
        if block.startswith("标题：") or block.startswith("标题:"):
            lines = block.split("\n", 1)
            title_line = lines[0].replace("标题：", "").replace("标题:", "").strip()
            content = lines[1].strip() if len(lines) > 1 else ""

        if content.startswith("内容：") or content.startswith("内容:"):
            content = content.split("\n", 1)[1].strip() if "\n" in content else content.replace("内容：", "").replace("内容:", "")

        content_html = ""
        for para in content.split("\n\n"):
            para = para.strip()
            if para:
                para = para.replace("\n", "<br>")
                content_html += f"<p>{para}</p>\n"
        if not content_html:
            for para in content.split("\n"):
                para = para.strip()
                if para:
                    content_html += f"<p>{para}</p>\n"

        header_text = f"{flag} {region}"
        if title_line:
            header_text += f"：{title_line}"

        sections_html += f"""
<h3 style="color: {style['color']}; margin-bottom: 8px;">{header_text}</h3>
<div style="background: {style['bg']}; border-radius: 8px; padding: 14px 16px; margin-bottom: 16px; line-height: 1.8; font-size: 14px;">
{content_html}
</div>
"""

    biz_marker = "===业务影响==="
    if biz_marker in result:
        biz_block = result.split(biz_marker)[1].split("===END===")[0].strip()
        biz_html = ""
        for line in biz_block.split("\n"):
            line = line.strip()
            if line and line != "内容：":
                if line.startswith("- ") or line.startswith("* "):
                    line = line[2:]
                biz_html += f"<li>{line}</li>\n"
        business_html = f'<ul style="margin: 0; padding-left: 20px;">\n{biz_html}</ul>'
    else:
        business_html = "<p>本期数据不足，暂无特别提示。</p>"

    gen_time = datetime.now(TZ_UTC8).strftime('%Y-%m-%d %H:%M UTC+8')

    html = HTML_TEMPLATE.format(
        time_range=data['range'],
        channel_names='、'.join(channel_names_list),
        total=total,
        channel_counts='、'.join(channel_counts_list),
        sections=sections_html,
        business_impact=business_html,
        gen_time=gen_time,
    )

    report_path = os.path.join(DATA_DIR, f"report_{date_label}.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"报告已生成: {report_path}")
    return report_path, date_label, total


if __name__ == '__main__':
    data, date_label = load_daily_json()
    summarize(data, date_label)
