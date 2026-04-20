import json
import os
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from config import API_ID, API_HASH, SESSION_NAME, CHANNELS

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORK_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

TZ_UTC8 = timezone(timedelta(hours=8))

client = TelegramClient(os.path.join(WORK_DIR, SESSION_NAME), API_ID, API_HASH)


async def fetch_channel(channel, since, until):
    try:
        entity = await client.get_entity(channel)
        title = getattr(entity, 'title', channel)
    except Exception as e:
        print(f"  ✗ @{channel}: {e}")
        return None, []

    messages = []
    async for msg in client.iter_messages(entity, offset_date=until, limit=None):
        if msg.date < since:
            break
        if msg.text:
            messages.append({
                "id": msg.id,
                "date": msg.date.astimezone(TZ_UTC8).strftime('%Y-%m-%d %H:%M:%S'),
                "views": msg.views,
                "forwards": msg.forwards,
                "text": msg.text,
            })

    messages.reverse()
    print(f"  ✓ @{channel} ({title}): {len(messages)} 条")
    return title, messages


async def main():
    await client.start()

    now = datetime.now(TZ_UTC8)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    since_utc = yesterday.astimezone(timezone.utc)
    until_utc = now.astimezone(timezone.utc)

    date_label = yesterday.strftime('%Y-%m-%d')
    print(f"抓取: {date_label} 00:00 ~ {now.strftime('%Y-%m-%d %H:%M')} (UTC+8)")

    all_results = {
        "fetch_time": now.strftime('%Y-%m-%d %H:%M:%S UTC+8'),
        "range": f"{date_label} 00:00 ~ {now.strftime('%Y-%m-%d %H:%M')} UTC+8",
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
