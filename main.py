import os
import re
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# --- DUMMY PORT FOR RENDER FORWARDER ---
# Yeh Render ko chup rakhne ke liye hai taaki port scan timeout na aaye
async def start_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = SimpleHTTPRequestHandler
    try:
        with TCPServer(("", port), handler) as httpd:
            print(f"Dummy server running on port {port}")
            while True:
                httpd.handle_request()
                await asyncio.sleep(1)
    except Exception as e:
        print(f"Dummy server error: {e}")

# --- CONFIGURATION ---
API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'
STRING_SESSION = os.environ.get("STRING_SESSION")

SOURCE_CHANNELS = ['offerlooters', -1001121334319, -1001639774576]
TARGET_CHANNEL = '@dealvaulthq'
AMAZON_TAG = 'dealvaulthq-21'

# --- USERBOT LOGIC ---
client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

def replace_affiliate_links(text):
    if not text:
        return text
    amazon_links = re.findall(r'(https?://(?:www\.)?amazon\.[a-z.]+(?:/[^\s]*)?)', text)
    for link in amazon_links:
        if 'tag=' in link:
            new_link = re.sub(r'tag=[^&]+', f'tag={AMAZON_TAG}', link)
        else:
            connector = '&' if '?' in link else '?'
            new_link = f"{link}{connector}tag={AMAZON_TAG}"
        text = text.replace(link, new_link)
    return text

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    try:
        message_text = event.message.text
        updated_text = replace_affiliate_links(message_text)
        if event.message.media:
            await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media)
        else:
            await client.send_message(TARGET_CHANNEL, updated_text)
        print("Deal successfully copied and link replaced!")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    print("Userbot is starting...")
    await client.start()
    print("Userbot is running smoothly...")
    # Dummy server aur bot dono ko sath me chalayenge
    await asyncio.gather(
        start_dummy_server(),
        client.run_until_disconnected()
    )

if __name__ == '__main__':
    asyncio.run(main())
