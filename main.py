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
CUELINKS_API_KEY = os.environ.get("CUELINKS_API_KEY", "").strip() # Yahan apni nayi API Key daalna

SOURCE_CHANNELS = [-1001121334319, -1001639774576, -1004347972620]
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
            json={"url": url, "format": "json"}
        )
        data = response.json()
        return data.get('url', url)
    except:
        return url

def process_text(text):
    # Amazon Link Handling
    amazon_pattern = r'(https?://(?:www\.)?(?:amazon\.[a-z.]+|amzn\.[a-z.]+|link\.amazon)(?:/[^\s]*)?)'
    text = re.sub(amazon_pattern, lambda m: f"{m.group(0).split('?')[0]}?tag={AMAZON_TAG}", text)
    
    # Other Affiliate Sites (Flipkart, Myntra, Ajio)
    other_sites = r'(https?://(?:www\.)?(?:flipkart|myntra|ajio|tatacliq)\.[a-z.]+(?:/[^\s]*)?)'
    matches = re.findall(other_sites, text, re.IGNORECASE)
    for link in matches:
        new_link = get_cuelinks_url(link)
        text = text.replace(link, new_link)
        
    return text

async def main():
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    @client.on(events.NewMessage())
    async def handler(event):
        if event.chat_id in SOURCE_CHANNELS:
            text = event.message.text or ""
            if not text: return
            
            updated_text = process_text(text)
            
            if event.message.media and not isinstance(event.message.media, types.MessageMediaWebPage):
                await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media)
            else:
                await client.send_message(TARGET_CHANNEL, updated_text, link_preview=False)
            logger.info("✅ Deal processed and forwarded!")

    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
