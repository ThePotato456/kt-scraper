import requests
from bs4 import BeautifulSoup
import json
import time
import hashlib
from datetime import datetime

EVENTS_URL = "https://comedymothership.com/shows"
EVENTS_FILE = "events.json"

# Replace with your actual Discord webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1371659254452326420/IkZiyug_8uj8SHtY0idgvEY-Hsfp8cQnzwz0ZHfW0SJrIX-vo7cSAdkj8OAW9Uml3eao"

def fetch_events():
    response = requests.get(EVENTS_URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    # All <li> tags that might contain events
    list_items = soup.find_all('li')

    events = []


    for li in list_items:
        event = {}
        event['id'] = ''

        # Get main div of event card
        card = li.find('div', class_=lambda c: c and c.startswith('EventCard_eventCard__'))
        if not card:
            continue  # Not an event card

        # --- Title & Date ---
        title_wrapper = card.find('div', class_='EventCard_titleWrapper__XdXmH')
        if title_wrapper:
            date = title_wrapper.find('div', class_='h6')
            title = title_wrapper.find('h3')
            event['date'] = date.text.strip() if date else ''
            event['title'] = title.text.strip() if title else ''



        # --- Time, Location, Ticket Info ---
        detail_items = card.select('ul.EventCard_detailsWrapper__o7OUO li')
        if detail_items:
            details = [li.get_text(strip=True) for li in detail_items]
            event['time'] = details[0] if len(details) > 0 else ''
            event['location'] = details[1] if len(details) > 1 else ''
            event['ticket_types'] = details[2:] if len(details) > 2 else []

        # --- Short Description ---
        desc = card.find('div', class_=lambda c: c and c.startswith('EventCard_description__'))
        if desc:
            event['description_snippet'] = desc.get_text(strip=True)

        # --- Sold Out Status ---
        sold_out_btn = card.find('button', class_=lambda c: c and 'soldOut' in c)
        event['sold_out'] = sold_out_btn is not None

        # --- Event Link ---
        share_link = card.find('a', class_='ShareUrlLink_shareLink__C_3RL')
        if share_link:
            event['link'] = share_link['href']
        # --- Event ID ---
        event['id'] = hashlib.sha256(f"{event['title']}{event['time']}{event['date']}".encode()).hexdigest()

        events.append(event)
    return events

def load_previous_events():
    try:
        with open(EVENTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_events(events):
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f, indent=2)

def get_new_events(current, previous):
    previous_ids = {e["id"] for e in previous}
    return [e for e in current if e["id"] not in previous_ids]

"""
  {
    "id": "274309de4c94a7d63140188f48b24736e17e88cc36dbaffd5d7a8c8bfaecacab",
    "date": "Thursday, May 15",
    "title": "Ron White and Friends",
    "time": "7:00 PM - 9:00 PM",
    "location": "FAT MAN",
    "ticket_types": [
      "General Admission",
      "Booth Seating"
    ],
    "description_snippet": "ATTENTION: 100% of tickets redemptions require the ORIGINAL purchaser to be present, as verified by government issued ID...Show Full Event Description",
    "sold_out": true,
    "link": "https://comedymothership.com/shows/111779"
  },
  """

def send_discord_alert(new_events):
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook not set.")
        return

    # Split message if it goes over Discord's 2000 character limit
    def chunk_messages(events):
        chunks = []
        current = "**🎭 New Comedy Mothership Shows Announced!**\n\n"
        for e in events:
            ticket_types = "\n".join([f"🎟️ {t}" for t in e.get("ticket_types", [])])
            sold_out = "❌ Sold Out" if e.get("sold_out") else "✅ Available"
            is_kill_tony = "<@&1371669782235189319>" if "Kill Tony" in e['title'] else ""
            entry = f"{is_kill_tony}```\n**[{e['id']}] {e['title']}**\n{sold_out}\n🗓️ {e['date']} at {e['time']}\n📍 {e['location']}\n{ticket_types}\n🔗{e['link']}\n```"
            if len(current) + len(entry) > 1900:
                chunks.append(current)
                current = ""
            current += entry
        chunks.append(current)
        return chunks

    messages = chunk_messages(new_events)

    for content in messages:
        payload = {
            "username": "Mothership Tracker",
            "content": content.strip()
        }

        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

        if response.status_code == 204:
            print("✅ Discord alert sent.")
            time.sleep(5)
        else:
            print(f"⚠️ Failed to send Discord message: {response.status_code}")
            print(f"Response: {response.text}")

# no events alert
def send_no_events_alert():
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook not set.")
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
        print(f"Response: {response.text}")

def main():
    print(f"[{datetime.now()}] Fetching events...")
    current_events = fetch_events()
    previous_events = load_previous_events()
    new_events = get_new_events(current_events, previous_events)

    if new_events:
        print(f"Found {len(new_events)} new event(s). Sending to Discord...")
        send_discord_alert(new_events)
        save_events(current_events)
    else:
        print("No new events found.")
        send_no_events_alert()

if __name__ == "__main__":
    main()
