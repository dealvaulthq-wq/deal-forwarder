import os
import re
import asyncio
import logging
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- LOGGING SETUP (Taaki Render par logs 100% dikhein) ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- DUMMY SERVER LOGIC ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = SimpleHTTPRequestHandler
    try:
        with TCPServer(("", port), handler) as httpd:
            logger.info(f"Dummy web server started on port {port}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"Dummy server error: {e}")

server_thread = threading.Thread(target=run_dummy_server, daemon=True)
server_thread.start()

# --- CONFIGURATION ---
API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'
STRING_SESSION = os.environ.get("STRING_SESSION")

SOURCE_CHANNELS = ['offerlooters', -1001121334319, -1001639774576, -1004347972620] 
TARGET_CHANNEL = '@dealvaulthq'
AMAZON_TAG = 'dealvaulthq-21'

# --- ADVANCED LINK REPLACER ---
def replace_affiliate_links(text):
    if not text:
        return text
    # Fix for link.amazon (bina .com/.in ke)
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

# --- USERBOT MAIN ASYNC RUNNER ---
async def main():
    logger.info("Userbot script start ho rahi hai...")
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    # Hum saare messages listen karenge aur manually check karenge (Caching issue solve)
    @client.on(events.NewMessage())
    async def handler(event):
        try:
            chat = await event.get_chat()
            chat_id = event.chat_id
            
            # Check if message is from our target channels
            is_source = False
            if chat_id in SOURCE_CHANNELS:
                is_source = True
            elif hasattr(chat, 'username') and chat.username and chat.username in SOURCE_CHANNELS:
                is_source = True

            if is_source:
                logger.info(f"Naya message mila from ID/Username: {chat_id}")
                message_text = event.message.text or ""
                updated_text = replace_affiliate_links(message_text)
                
                if event.message.media:
                    await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media)
                else:
                    await client.send_message(TARGET_CHANNEL, updated_text)
                logger.info("Deal perfectly forward ho gayi!")
        except Exception as e:
            logger.error(f"Error aayi: {e}")

    logger.info("Telegram se connect kar rahe hain...")
    await client.start()
    logger.info("Userbot FULLY LIVE hai aur deals ka wait kar raha hai!")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
import os
import re
import asyncio
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import threading
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- DUMMY SERVER LOGIC IN BACKGROUND THREAD ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = SimpleHTTPRequestHandler
    try:
        with TCPServer(("", port), handler) as httpd:
            print(f"Dummy web server started on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Dummy server error: {e}")

server_thread = threading.Thread(target=run_dummy_server, daemon=True)
server_thread.start()

# --- CONFIGURATION ---
API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'
STRING_SESSION = os.environ.get("STRING_SESSION")

# Tumhari saari source channels ki IDs aur usernames
SOURCE_CHANNELS = ['offerlooters', -1001121334319, -1001639774576, -1004347972620] 
TARGET_CHANNEL = '@dealvaulthq'
AMAZON_TAG = 'dealvaulthq-21'

# --- ADVANCED LINK REPLACER ---
def replace_affiliate_links(text):
    if not text:
        return text
    amazon_pattern = r'(https?://(?:www\.)?(?:amazon\.[a-z.]+|amzn\.[a-z.]+|link\.amazon\.[a-z.]+)(?:/[^\s]*)?)'
    amazon_links = re.findall(amazon_pattern, text)
    for link in amazon_links:
        if 'tag=' in link:
            new_link = re.sub(r'tag=[^&]+', f'tag={AMAZON_TAG}', link)
        else:
            connector = '&' if '?' in link else '?'
            new_link = f"{link}{connector}tag={AMAZON_TAG}"
        text = text.replace(link, new_link)
    return text

# --- USERBOT MAIN ASYNC RUNNER ---
async def main():
    print("Userbot script initializing...")
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    @client.on(events.NewMessage(chats=SOURCE_CHANNELS))
    async def handler(event):
        try:
            print("Naya message detect hua!")
            message_text = event.message.text or ""
            updated_text = replace_affiliate_links(message_text)
            if event.message.media:
                await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media)
            else:
                await client.send_message(TARGET_CHANNEL, updated_text)
            print("Message successfully forward ho gaya!")
        except Exception as e:
            print(f"Error handling message: {e}")

    print("Connecting to Telegram...")
    await client.start()
    print("Userbot is running smoothly inside loop...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
