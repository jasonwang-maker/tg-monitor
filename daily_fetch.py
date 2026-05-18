import json
import os
from datetime import datetime, timezone
from telethon import TelegramClient
from config import API_ID, API_HASH, SESSION_NAME, CHANNELS, NOISY_CHANNELS, NOISY_MIN_LENGTH, NOISY_KEYWORDS
from report_window import TZ_UTC8, get_report_window

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORK_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

client = TelegramClient(os.path.join(WORK_DIR, SESSION_NAME), API_ID, API_HASH)


def _is_relevant(text, keywords):
    t = text.lower()
    return any(kw.lower() in t for kw in keywords)


async def fetch_channel(channel, since, until):
    try:
        entity = await client.get_entity(channel)
        title = getattr(entity, 'title', channel)
    except Exception as e:
        print(f"  ✗ @{channel}: {e}")
        return None, []

    is_noisy = channel in NOISY_CHANNELS
    messages = []
    raw_count = 0
    async for msg in client.iter_messages(entity, offset_date=until, limit=None):
        if msg.date < since:
            break
        if not msg.text:
            continue
        raw_count += 1
        if is_noisy:
            if len(msg.text) < NOISY_MIN_LENGTH:
                continue
            if not _is_relevant(msg.text, NOISY_KEYWORDS):
                continue
        messages.append({
            "id": msg.id,
            "date": msg.date.astimezone(TZ_UTC8).strftime('%Y-%m-%d %H:%M:%S'),
            "views": msg.views,
            "forwards": msg.forwards,
            "text": msg.text,
        })

    messages.reverse()
    if is_noisy:
        print(f"  ✓ @{channel} ({title}): {len(messages)} 条 (原始 {raw_count} 条，已过滤)")
    else:
        print(f"  ✓ @{channel} ({title}): {len(messages)} 条")
    return title, messages


async def main():
    await client.start()

    now = datetime.now(TZ_UTC8)
    report_start, report_end = get_report_window(now)

    since_utc = report_start.astimezone(timezone.utc)
    until_utc = report_end.astimezone(timezone.utc)

    date_label = report_start.strftime('%Y-%m-%d')
    print(f"运行时间: {now.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)")
    print(f"抓取: {report_start.strftime('%Y-%m-%d %H:%M')} ~ {report_end.strftime('%Y-%m-%d %H:%M')} (UTC+8)")

    all_results = {
        "fetch_time": now.strftime('%Y-%m-%d %H:%M:%S UTC+8'),
        "range": f"{report_start.strftime('%Y-%m-%d %H:%M')} ~ {report_end.strftime('%Y-%m-%d %H:%M')} UTC+8",
        "channels": {}
    }

    total = 0
    for channel in CHANNELS:
        title, msgs = await fetch_channel(channel, since_utc, until_utc)
        all_results["channels"][channel] = {
            "title": title or channel,
            "messages": msgs,
        }
        total += len(msgs)

    output_file = os.path.join(DATA_DIR, f"daily_{date_label}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"完成: {total} 条 → {output_file}")


with client:
    client.loop.run_until_complete(main())
