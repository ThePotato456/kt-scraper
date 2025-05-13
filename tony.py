import asyncio
from pyppeteer import launch
import os
from bs4 import BeautifulSoup
import json

async def main():
    chromium_path = os.path.abspath('./chromium/chrome.exe')

    browser = await launch(executablePath=chromium_path, headless=True)
    page = await browser.newPage()
    await page.goto('https://comedymothership.com/shows')

    # Get page HTML content
    content = await page.content()
    await browser.close()

    # Parse with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')

    # All <li> tags that might contain events
    list_items = soup.find_all('li')

    events = []

    for li in list_items:
        event = {}

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

        events.append(event)

    # Output the JSON object
    print(json.dumps(events, indent=2))

    open('output.json', 'w').write(json.dumps(events, indent=2))


# Run the script
asyncio.get_event_loop().run_until_complete(main())
