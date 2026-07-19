import os
import re
import asyncio
import logging
import sys
import requests
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'
STRING_SESSION = os.environ.get("STRING_SESSION", "").strip()
CUELINKS_API_KEY = os.environ.get("CUELINKS_API_KEY", "").strip()

# Total 5 Source Channels (3 Normal + 2 Lallantop Restricted Channels)
SOURCE_CHANNELS = [
    -1001121334319,  # Normal Channel 1
    -1001639774576,  # Normal Channel 2
    -1004347972620,  # Normal Channel 3 (Testing etc.)
    -1002226389011,  # Lallantop Restricted Channel 1
    -1002110119819   # Lallantop Restricted Channel 2
]

# In 2 channels se sirf "Loot" likha hone par hi message aayega
LOOT_RESTRICTED_CHANNELS = [
    -1002226389011,
    -1002110119819
] 

TARGET_CHANNEL = -1004401616132
AMAZON_TAG = 'dealvaulthq-21'

# --- LOGGING & SERVER ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    with TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        logger.info(f"🟢 Server running on port {port}")
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- LOGIC ---
def get_cuelinks_url(url):
    try:
        response = requests.post(
            "https://api.cuelinks.com/v3/links",
            headers={"Authorization": f"Bearer {CUELINKS_API_KEY}", "Content-Type": "application/json"},
            json={"url": url, "format": "json"},
            timeout=5
        )
        data = response.json()
        return data.get('url', url)
    except Exception as e:
        logger.error(f"Cuelinks API Error: {e}")
        return url

def process_text(text):
    allowed_domains = ['amazon', 'amzn', 'link.amazon', 'flipkart', 'fkrt.cc', 'myntra', 'ajio', 'shopsy']
    link_pattern = r'https?://(?:www\.)?([a-zA-Z0-9.-]+)(?:/[^\s]*)?'
    
    matches = list(re.finditer(link_pattern, text, re.IGNORECASE))
    updated_text = text
    found_valid_link = False
    
    for match in matches:
        full_link = match.group(0)
        domain = match.group(1).lower()
        
        if any(d in domain for d in allowed_domains):
            found_valid_link = True
            if "amazon" in domain or "amzn" in domain:
                new_link = full_link.split('?')[0] + f"?tag={AMAZON_TAG}"
            else:
                new_link = get_cuelinks_url(full_link)
            updated_text = updated_text.replace(full_link, new_link)
        else:
            updated_text = updated_text.replace(full_link, "")
            
    return updated_text if found_valid_link else None

async def main():
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    @client.on(events.NewMessage())
    async def handler(event):
        if event.chat_id in SOURCE_CHANNELS:
            text = event.message.text or ""
            
            # Agar message un 2 Lallantop channels se hai, toh check karo ki "loot" word hai ya nahi
            if event.chat_id in LOOT_RESTRICTED_CHANNELS:
                if "loot" not in text.lower():
                    return  # Agar "loot" nahi hai, toh message drop kar do

            updated_text = process_text(text)
            
            if updated_text:
                if event.message.media and not isinstance(event.message.media, types.MessageMediaWebPage):
                    await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media, link_preview=False)
                else:
                    await client.send_message(TARGET_CHANNEL, updated_text, link_preview=False)
                logger.info("✅ Deal forwarded successfully from 5 channels setup!")

    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
