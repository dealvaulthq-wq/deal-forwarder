import os
import re
import asyncio
import logging
import sys
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# Forced flush aur clear logging taaki Render pe dikhe hi dikhe
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- DUMMY SERVER ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = SimpleHTTPRequestHandler
    try:
        with TCPServer(("", port), handler) as httpd:
            logger.info(f"🟢 Dummy web server listening on port {port}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"🔴 Dummy server crashed: {e}")

server_thread = threading.Thread(target=run_dummy_server, daemon=True)
server_thread.start()

# --- CONFIGURATION ---
API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'
STRING_SESSION = os.environ.get("STRING_SESSION", "").strip()

SOURCE_CHANNELS = ['offerlooters', -1001121334319, -1001639774576, -1004347972620] 
TARGET_CHANNEL = '@dealvaulthq'
AMAZON_TAG = 'dealvaulthq-21'

def replace_affiliate_links(text):
    if not text:
        return text
    amazon_pattern = r'(https?://(?:www\.)?(?:amazon\.[a-z.]+|amzn\.[a-z.]+|link\.amazon)(?:/[^\s]*)?)'
    amazon_links = re.findall(amazon_pattern, text)
    for link in amazon_links:
        if 'tag=' in link:
            new_link = re.sub(r'tag=[^&]+', f'tag={AMAZON_TAG}', link)
        else:
            connector = '&' if '?' in link else '?'
            new_link = f"{link}{connector}tag={AMAZON_TAG}"
        text = text.replace(link, new_link)
    return text

async def main():
    logger.info("🚀 Userbot initializing main function...")
    
    if not STRING_SESSION:
        logger.error("❌ STRING_SESSION environment variable missing or empty!")
        return

    try:
        logger.info("🔄 Connecting to Telegram using StringSession...")
        client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
        
        @client.on(events.NewMessage())
        async def handler(event):
            try:
                chat_id = event.chat_id
                chat = await event.get_chat()
                
                is_source = False
                if chat_id in SOURCE_CHANNELS:
                    is_source = True
                elif hasattr(chat, 'username') and chat.username and chat.username in SOURCE_CHANNELS:
                    is_source = True

                if is_source:
                    logger.info(f"📥 Message intercepted from source: {chat_id}")
                    message_text = event.message.text or ""
                    updated_text = replace_affiliate_links(message_text)
                    
                    if event.message.media:
                        await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media)
                    else:
                        await client.send_message(TARGET_CHANNEL, updated_text)
                    logger.info("✅ Deal successfully forwarded!")
            except Exception as handler_err:
                logger.error(f"❌ Error inside handler: {handler_err}")

        await client.start()
        logger.info("🎯 USERBOT IS FULLY RUNNING AND CONNECTED!")
        await client.run_until_disconnected()
        
    except Exception as client_err:
        logger.error(f"❌ Critical error in Telegram Client: {client_err}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as main_err:
        logger.error(f"❌ Asyncio loop crashed: {main_err}")
