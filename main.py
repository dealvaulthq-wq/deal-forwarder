import os
import re
import asyncio
import logging
import sys
import requests
import threading
from collections import deque
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'
STRING_SESSION = os.environ.get("STRING_SESSION", "").strip()
CUELINKS_API_KEY = os.environ.get("CUELINKS_API_KEY", "").strip()

SOURCE_CHANNELS = [
    -1001121334319,
    -1001639774576,
    -1004347972620,
    -1002226389011,
    -1002110119819
]

LOOT_RESTRICTED_CHANNELS = [
    -1002226389011,
    -1002110119819
] 

TARGET_CHANNEL = -1004401616132
AMAZON_TAG = 'dealvaulthq-21'

WATERMARK_TEXT = "\n\n━━━━━━━━━━━━━\n🚀 **Join Deal Vault HQ for More Loot Deals!**"

recent_deals = deque(maxlen=100)
bot_paused = False
total_forwarded_count = 0

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

def clean_and_format_text(text):
    cleaned = re.sub(r'[═▀▄█▬]{3,}', '', text)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # Sirf product ke hisab se exact 1 ya 2 relevant tags (No BestBuy, No DealVaultHQ)
    tags_list = []
    lower_txt = text.lower()
    
    if any(w in lower_txt for w in ['shoe', 'sneaker', 'nike', 'puma', 'adidas', 'clothing', 'shirt', 'jean', 'tshirt', 'facewash', 'skin', 'beauty', 'cream']):
        tags_list.append("#FashionBeauty")
    if any(w in lower_txt for w in ['phone', 'mobile', 'earbud', 'headphone', 'watch', 'smartwatch', 'laptop', 'charger', 'cable']):
        tags_list.append("#Electronics")
    if any(w in lower_txt for w in ['kitchen', 'home', 'bulb', 'bottle', 'bedsheet', 'pillow', 'cleaner']):
        tags_list.append("#HomeNeeds")
    if any(w in lower_txt for w in ['loot', 'glitch', 'error', '99', '49']):
        tags_list.append("#LootDeals")
        
    final_tags = " ".join(list(dict.fromkeys(tags_list))[:2])
    
    if final_tags:
        return cleaned.strip() + "\n\n" + final_tags
    return cleaned.strip()

def process_deal(text):
    allowed_domains = ['amazon', 'amzn', 'link.amazon', 'flipkart', 'fkrt.cc', 'myntra', 'myntr. it', 'ajiio. in', 'ajio', 'shopsy']
    link_pattern = r'https?://(?:www\.)?([a-zA-Z0-9.-]+)(?:/[^\s]*)?'
    
    matches = list(re.finditer(link_pattern, text, re.IGNORECASE))
    updated_text = text
    found_valid_link = False
    first_link_clean = None
    
    for match in matches:
        full_link = match.group(0)
        domain = match.group(1).lower()
        
        if any(d in domain for d in allowed_domains):
            found_valid_link = True
            if "amazon" in domain or "amzn" in domain:
                new_link = full_link.split('?')[0] + f"?tag={AMAZON_TAG}"
            else:
                new_link = get_cuelinks_url(full_link)
            
            if not first_link_clean:
                first_link_clean = new_link.split('?')[0]
                
            updated_text = updated_text.replace(full_link, new_link)
        else:
            updated_text = updated_text.replace(full_link, "")
            
    if found_valid_link:
        if first_link_clean in recent_deals:
            logger.info("⚠️ Duplicate deal detected, skipped!")
            return None
        
        recent_deals.append(first_link_clean)
        
        formatted_text = clean_and_format_text(updated_text)
        
        # Bada banner sirf tabhi aayega jab asli mein koi special glitch/lowest loot ho
        header_banner = ""
        if any(k in text.lower() for k in ["lowest", "free", "error", "glitch", "99", "49"]):
            header_banner = "🚨 **CRAZY GLITCH / LOWEST PRICE ALERT!**\n━━━━━━━━━━━━━\n"
            
        final_output = header_banner + formatted_text + WATERMARK_TEXT
        return final_output
        
    return None

async def main():
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    @client.on(events.NewMessage())
    async def handler(event):
        global bot_paused, total_forwarded_count
        
        if event.is_private or event.chat_id == TARGET_CHANNEL:
            msg_text = event.message.text or ""
            if msg_text.lower() == "/pause":
                bot_paused = True
                await event.respond("⏸️ **Deal Vault Bot is now PAUSED.**")
                return
            elif msg_text.lower() == "/resume":
                bot_paused = False
                await event.respond("▶️ **Deal Vault Bot is now RESUMED.**")
                return
            elif msg_text.lower() == "/stats":
                status = "PAUSED ⏸️" if bot_paused else "RUNNING 🟢"
                await event.respond(f"📊 **Status:** {status}\n- Total Forwarded: {total_forwarded_count}")
                return

        if bot_paused:
            return

        if event.chat_id in SOURCE_CHANNELS:
            text = event.message.text or ""
            
            if event.chat_id in LOOT_RESTRICTED_CHANNELS:
                if "loot" not in text.lower():
                    return

            final_text = process_deal(text)
            
            if final_text:
                if event.message.media and not isinstance(event.message.media, types.MessageMediaWebPage):
                    await client.send_message(TARGET_CHANNEL, final_text, file=event.message.media, link_preview=False)
                else:
                    await client.send_message(TARGET_CHANNEL, final_text, link_preview=False)
                
                total_forwarded_count += 1
                logger.info(f"✅ Clean deal posted! Total: {total_forwarded_count}")

    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
