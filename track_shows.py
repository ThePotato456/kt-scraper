import requests
from bs4 import BeautifulSoup
import hashlib
import json
import time
import os
from datetime import datetime

# --- Configuration ---
EVENTS_URL = "https://comedymothership.com/shows"
EVENTS_FILE = "events.json"
DISCORD_WEBHOOK_URL = open("/home/user/vscode_projects/kt-scraper/discord_webhook.txt").read().strip() if os.path.exists("/home/user/vscode_projects/kt-scraper/discord_webhook.txt") else None

# --- Core Scraper ---
def fetch_events():
    response = requests.get(EVENTS_URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    events = []

    for li in soup.find_all('li'):
        card = li.find('div', class_=lambda c: c and c.startswith('EventCard_eventCard__'))
        if not card:
            continue

        event = {}

        # Title and date
        title_wrapper = card.find('div', class_='EventCard_titleWrapper__XdXmH')
        if title_wrapper:
            date = title_wrapper.find('div', class_='h6')
            title = title_wrapper.find('h3')
            event['date'] = date.text.strip() if date else ''
            event['title'] = title.text.strip() if title else ''

        # Time, location, ticket types
        details = card.select('ul.EventCard_detailsWrapper__o7OUO li')
        if details:
            detail_texts = [li.get_text(strip=True) for li in details]
            event['time'] = detail_texts[0] if len(detail_texts) > 0 else ''
            event['location'] = detail_texts[1] if len(detail_texts) > 1 else ''
            event['ticket_types'] = detail_texts[2:] if len(detail_texts) > 2 else []

        # Description
        desc = card.find('div', class_=lambda c: c and c.startswith('EventCard_description__'))
        event['description_snippet'] = desc.get_text(strip=True) if desc else ''

        # Sold out status
        sold_out_btn = card.find('button', class_=lambda c: c and 'soldOut' in c)
        event['sold_out'] = sold_out_btn is not None

        # Event link
        share_link = card.find('a', class_='ShareUrlLink_shareLink__C_3RL')
        event['link'] = share_link['href'] if share_link else ''

        # Event ID - use stable, consistent fields
        hash_source = f"{event.get('title')}{event.get('time')}{event.get('date')}{event.get('link')}"
        event['id'] = hashlib.sha256(hash_source.encode()).hexdigest()

        events.append(event)

    return events

# --- File Storage ---
def load_previous_events():
    try:
        with open(EVENTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_events(events):
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f, indent=2)

def get_new_events(current_events, previous_events):
    previous_ids = {e['id'] for e in previous_events}
    return [e for e in current_events if e['id'] not in previous_ids]

# --- Discord Alerting ---
def send_discord_alert(events):
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("Discord webhook not configured.")

    def format_events(events):
        messages = []
        current_msg = "**🎭 New Comedy Mothership Shows Announced!**\n\n"

        for e in events:
            is_kill_tony = "<@&1371669782235189319>" if "Kill Tony" in e["title"] else ""
            ticket_lines = "\n".join(f"🎟️ {t}" for t in e.get("ticket_types", []))
            sold_status = "❌ Sold Out" if e.get("sold_out") else "✅ Available"

            entry = f"{is_kill_tony}```\n**{e['title']}**\n{sold_status}\n🗓️ {e['date']} at {e['time']}\n📍 {e['location']}\n{ticket_lines}\n🔗 {e['link']}\n```"

            if len(current_msg) + len(entry) > 1900:
                messages.append(current_msg)
                current_msg = ""
            current_msg += entry

        messages.append(current_msg)
        return messages

    for msg in format_events(events):
        payload = {
            "username": "Mothership Tracker",
            "content": msg.strip()
        }
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            raise RuntimeError(f"Failed to send message: {response.status_code}, {response.text}")
        print("✅ Discord alert sent.")
        time.sleep(5)

def send_no_events_alert():
    if not DISCORD_WEBHOOK_URL:
        return
    payload = {
        "username": "Mothership Tracker",
        "content": "**❌ No new events found.**"
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("✅ No events alert sent.")
    else:
        print(f"⚠️ Failed to send no events alert: {response.status_code}")

# --- Main Execution ---
def main():
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ Discord webhook URL not set. Please create discord_webhook.txt and put the link in there.")
        return


    print(f"[{datetime.now()}] Starting Comedy Mothership event check...")

    current_events = fetch_events()
    print(f"🔍 Fetched {len(current_events)} current events.")
    
    previous_events = load_previous_events()
    new_events = get_new_events(current_events, previous_events)
    print(f"🆕 Found {len(new_events)} new events.")

    try:
        if new_events:
            send_discord_alert(new_events)
            save_events(current_events)  # Only save if alerting was successful
        else:
            send_no_events_alert()
    except Exception as e:
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    main()
