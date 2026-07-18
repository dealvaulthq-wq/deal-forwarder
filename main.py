import os
import re
from telethon import TelegramClient, events

# --- CONFIGURATION ---
API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'

# Jo 3 channels track karne hain (1 public, 2 private IDs)
SOURCE_CHANNELS = ['offerlooters', -1001121334319, -1001639774576]

# Tumhara khud ka Telegram Channel jahan deals jayengi
TARGET_CHANNEL = '@dealvault_hq'

# Tumhara Amazon Affiliate Tag
AMAZON_TAG = 'dealvaulthq-21'

# --- USERBOT LOGIC ---
client = TelegramClient('my_userbot_session', API_ID, API_HASH)

def replace_affiliate_links(text):
    if not text:
        return text
    # Amazon ke links ko track karke tumhare tag se replace karne ke liye regex
    amazon_links = re.findall(r'(https?://(?:www\.)?amazon\.[a-z.]+/?[^\s]*)', text)
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
        
        # Message media (photo/video) ke sath copy karega
        if event.message.media:
            await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media)
        else:
            await client.send_message(TARGET_CHANNEL, updated_text)
        print("Deal successfully copied and link replaced!")
    except Exception as e:
        print(f"Error: {e}")

print("Userbot is starting... Pehli baar run karne par OTP maangega.")
client.start()
print("Userbot is running smoothly...")
client.run_until_disconnected()
