import requests
import json
import os
import sys
import time

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

CATEGORIES = [
    'appliancerepair',  # Ремонт бытовой техники
    'computerrepair',   # Ремонт компьютерной техники
    'videorepair',      # Ремонт видеотехники
]

STATE_FILE = 'seen_tasks.json'


def load_seen():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_seen(seen):
    # Keep only the last 2000 IDs to avoid the file growing too large
    seen_list = sorted(seen, key=lambda x: int(x))[-2000:]
    with open(STATE_FILE, 'w') as f:
        json.dump(seen_list, f)


def fetch_tasks(slug):
    url = 'https://s.onliner.by/api/tasks'
    params = {
        'sections[]': slug,
        'page': 1,
        'limit': 50,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get('tasks', [])
    except Exception as e:
        print(f"[ERROR] Fetching {slug}: {e}", file=sys.stderr)
        return []


def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] No Telegram credentials, skipping notification.")
        return False
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    try:
        resp = requests.post(url, json={
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
        }, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[ERROR] Telegram: {e}", file=sys.stderr)
        return False


def format_message(task):
    section_name = task.get('section', {}).get('name', 'Неизвестная категория')
    title = task.get('title', 'Без названия')
    description = (task.get('description') or '').strip()
    if len(description) > 250:
        description = description[:250] + '...'
    location = (task.get('location') or {}).get('formatted_locality', '')
    html_url = task.get('html_url', '')
    price = task.get('price')

    lines = [
        f'🔧 <b>{section_name}</b>',
        '',
        f'<b>{title}</b>',
    ]
    if description:
        lines += ['', description]
    if location:
        lines.append(f'\n📍 {location}')
    if price:
        lines.append(f'💰 {price} BYN')
    if html_url:
        lines.append(f'\n🔗 <a href="{html_url}">Открыть заявку</a>')

    return '\n'.join(lines)


def main():
    seen = load_seen()
    is_first_run = len(seen) == 0

    all_tasks = []
    for slug in CATEGORIES:
        tasks = fetch_tasks(slug)
        all_tasks.extend(tasks)
        print(f"[INFO] {slug}: fetched {len(tasks)} tasks")

    # Deduplicate by ID, sort newest first
    seen_in_batch = set()
    unique_tasks = []
    for t in all_tasks:
        tid = t['id']
        if tid not in seen_in_batch:
            seen_in_batch.add(tid)
            unique_tasks.append(t)
    unique_tasks.sort(key=lambda t: t['id'], reverse=True)

    new_tasks = [t for t in unique_tasks if str(t['id']) not in seen]

    # Add all current IDs to seen
    for t in unique_tasks:
        seen.add(str(t['id']))

    if is_first_run:
        save_seen(seen)
        print(f"[INFO] First run complete. Saved {len(seen)} existing task IDs.")
        print("[INFO] From now on you'll receive notifications about NEW tasks only.")
        return

    print(f"[INFO] Found {len(new_tasks)} new task(s).")

    sent = 0
    for task in new_tasks:
        msg = format_message(task)
        if send_telegram(msg):
            sent += 1
        # Respect Telegram rate limit: max 30 messages/second
        if sent % 20 == 0 and sent > 0:
            time.sleep(1)

    save_seen(seen)
    print(f"[INFO] Sent {sent} Telegram notification(s).")


if __name__ == '__main__':
    main()
