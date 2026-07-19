import os
import re
import asyncio
import logging
import sys
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'
STRING_SESSION = os.environ.get("STRING_SESSION", "").strip()

# Configuration
SOURCE_CHANNELS = [-1001121334319, -1001639774576, -1004347972620]
TARGET_CHANNEL = -1004401616132
AMAZON_TAG = 'dealvaulthq-21'

def replace_affiliate_links(text):
    if not text: return text
    amazon_pattern = r'(https?://(?:www\.)?(?:amazon\.[a-z.]+|amzn\.[a-z.]+|link\.amazon)(?:/[^\s]*)?)'
    
    def replacement(match):
        link = match.group(0)
        # Agar tag pehle se hai toh use replace karo
        if 'tag=' in link:
            return re.sub(r'tag=[^&]+', f'tag={AMAZON_TAG}', link)
        # Agar tag nahi hai toh add karo
        else:
            connector = '&' if '?' in link else '?'
            return f"{link}{connector}tag={AMAZON_TAG}"
    
    return re.sub(amazon_pattern, replacement, text)

async def main():
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    @client.on(events.NewMessage())
    async def handler(event):
        if event.chat_id in SOURCE_CHANNELS:
            text = event.message.text or ""
            updated_text = replace_affiliate_links(text)
            
            # 1. Agar image file attached hai (photo/video), toh wahi bhejo
            if event.message.media and not isinstance(event.message.media, types.MessageMediaWebPage):
                await client.send_message(TARGET_CHANNEL, updated_text, file=event.message.media)
            # 2. Agar koi image file nahi hai, toh sirf text bhejo bina link preview ke
            else:
                await client.send_message(TARGET_CHANNEL, updated_text, link_preview=False)
            
            logger.info(f"✅ Deal forwarded from {event.chat_id}")

    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
