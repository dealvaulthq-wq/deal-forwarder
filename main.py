import os
import re
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
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

SOURCE_CHANNELS = ['offerlooters', -1001121334319, -1001639774576, 'testing_7787']
TARGET_CHANNEL = '@dealvaulthq'
AMAZON_TAG = 'dealvaulthq-21'

# --- ADVANCED LINK REPLACER ---
def replace_affiliate_links(text):
    if not text:
        return text
    
    # Yeh pattern amazon, amzn.in, amzn.to, aur link.amazon sabhi ko pakad lega
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

# --- USERBOT LOGIC ---
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    try:
        message_text = event.message.text
        updated_text = replace_affiliate_links(message_text)
        if event.message.media:
            await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media)
        else:
            await client.send_message(TARGET_CHANNEL, updated_text)
        print("Deal successfully forward ho gayi!")
    except Exception as e:
        print(f"Error handling message: {e}")

print("Userbot is starting...")
client.start()
print("Userbot is running smoothly...")
client.run_until_disconnected()
