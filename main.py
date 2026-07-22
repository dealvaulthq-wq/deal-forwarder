import os
import re
import asyncio
import logging
import sys
import threading
import requests
from collections import deque
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession

# --- CONFIGURATION ---
API_ID = 30457846
API_HASH = '311a981ad11c95c88b1970d0be59f94d'
STRING_SESSION = os.environ.get("STRING_SESSION", "").strip()

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
WATERMARK_TEXT = "\n\n━━━━━━━━━━━━━\n⚡ @DealVaultHQ"

recent_deals = deque(maxlen=100)
bot_paused = False
total_forwarded_count = 0

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# --- INDEPENDENT HTTP SERVER FOR RENDER & UPTIMEROBOT ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")
    def log_message(self, format, *args):
        pass

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    logger.info(f"🟢 Keep-alive HTTP Server running on port {port}")
    server.serve_forever()

# Start server immediately in background thread
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- LINK EXPANDER FUNCTION ---
def expand_short_link(url):
    try:
        # Request bhej kar dekhenge ki short link kahan redirect ho raha hai
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=5)
        return response.url
    except Exception as e:
        logger.error(f"Failed to expand URL {url}: {e}")
        return url

# --- LOGIC ---
def clean_and_format_text(text):
    cleaned = re.sub(r'[═▀▄█▬]{3,}', '', text)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    tags_list = []
    lower_txt = text.lower()
    
    if any(w in lower_txt for w in ['shoe', 'sneaker', 'nike', 'puma', 'adidas', 'clothing', 'shirt', 'jean', 'tshirt', 'facewash', 'skin', 'beauty', 'cream']):
        tags_list.append("#FashionBeauty")
    if any(w in lower_txt for w in ['phone', 'mobile', 'earbud', 'headphone', 'watch', 'smartwatch', 'laptop', 'charger', 'cable']):
        tags_list.append("#Electronics")
    if any(w in lower_txt for w in ['kitchen', 'home', 'bulb', 'bottle', 'bedsheet', 'pillow', 'cleaner']):
        tags_list.append("#HomeNeeds")
    if any(w in lower_txt for w in ['loot', 'glitch', 'error', '99', '49', '1', 'grab']):
        tags_list.append("#LootDeals")
        
    final_tags = " ".join(list(dict.fromkeys(tags_list))[:2])
    
    if final_tags:
        return cleaned.strip() + "\n\n" + final_tags
    return cleaned.strip()

def process_deal(text):
    allowed_domains = ['amazon', 'amzn', 'link.amazon']
    link_pattern = r'https?://(?:www\.)?[a-zA-Z0-9.-]+[^\s?#]*(?:\?[^\s#]*)?'
    
    matches = list(re.finditer(link_pattern, text, re.IGNORECASE))
    updated_text = text
    found_valid_link = False
    first_link_clean = None
    
    for match in matches:
        full_link = match.group(0)
        
        # Agar amzn.to short link hai, toh usko pehle expand karke asli lamba URL nikalenge
        target_link = full_link
        if "amzn.to" in full_link:
            target_link = expand_short_link(full_link)
            
        parsed = urlparse(target_link)
        domain = parsed.netloc.lower()
        
        if any(d in domain for d in allowed_domains):
            found_valid_link = True
            
            # Asli URL milne ke baad purana tag hata kar apna tag lagayenge
            base_url = target_link.split('&tag=')[0].split('?tag=')[0].split('?')[0]
            
            if '?' in base_url:
                new_link = f"{base_url}&tag={AMAZON_TAG}"
            else:
                new_link = f"{base_url}?tag={AMAZON_TAG}"
                
            if not first_link_clean:
                first_link_clean = base_url
                
            # Message ke andar wale short/gande link ko naye clean link se replace kar denge
            updated_text = updated_text.replace(full_link, new_link)
        else:
            updated_text = updated_text.replace(full_link, "")
            
    if found_valid_link:
        if first_link_clean in recent_deals:
            logger.info("⚠️ Duplicate deal detected, skipped!")
            return None
        
        recent_deals.append(first_link_clean)
        formatted_text = clean_and_format_text(updated_text)
        
        lower_text = text.lower()
        header_banner = ""
        
        if "rs. 1" in lower_text or "rs 1" in lower_text or "₹1" in text or "1 rupe" in lower_text:
            header_banner = "🔥 **MEGA ₹1 STORE / 1 RUPEE DEAL!** 🔥\n━━━━━━━━━━━━━\n"
        elif any(k in lower_text for k in ["lowest", "free", "error", "glitch", "49", "loot", "grab"]):
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
                logger.info(f"✅ Clean Amazon deal posted! Total: {total_forwarded_count}")

    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
