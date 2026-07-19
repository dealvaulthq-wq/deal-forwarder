import os
import re
import asyncio
import logging
import sys
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# --- STABLE DUMMY SERVER (Render ke liye) ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    with TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        logger.info(f"🟢 Server running on port {port}")
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- CONFIGURATION ---
API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'
STRING_SESSION = os.environ.get("STRING_SESSION", "").strip()

SOURCE_CHANNELS = [-1001121334319, -1001639774576, -1004347972620]
TARGET_CHANNEL = -1004401616132
AMAZON_TAG = 'dealvaulthq-21'

last_message_text = ""

def replace_affiliate_links(text):
    if not text: return text
    amazon_pattern = r'(https?://(?:www\.)?(?:amazon\.[a-z.]+|amzn\.[a-z.]+|link\.amazon)(?:/[^\s]*)?)'
    def replacement(match):
        link = match.group(0).split('?')[0] # Purana tag hata ke naya tag lagayega
        return f"{link}?tag={AMAZON_TAG}"
    return re.sub(amazon_pattern, replacement, text)

async def main():
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    @client.on(events.NewMessage())
    async def handler(event):
        global last_message_text
        if event.chat_id in SOURCE_CHANNELS:
            text = event.message.text or ""
            
            # FILTRATION: Sirf wahi forward hoga jisme Amazon link ho
            if not bool(re.search(r'amzn\.[a-z.]+|amazon\.[a-z.]+', text, re.IGNORECASE)):
                return
            
            # DUPLICATE CHECK: Ek hi message bar-bar nahi aayega
            if text == last_message_text:
                return
            last_message_text = text
            
            updated_text = replace_affiliate_links(text)
            
            if event.message.media and not isinstance(event.message.media, types.MessageMediaWebPage):
                await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media)
            else:
                await client.send_message(TARGET_CHANNEL, updated_text, link_preview=False)
            
            logger.info("✅ Deal forwarded successfully!")

    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
