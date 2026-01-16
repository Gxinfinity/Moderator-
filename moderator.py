import os, requests, re, cv2, asyncio, zipfile, shutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "" 

# Log Channel ID (Example: -100123456789)
LOG_CHANNEL_ID = -1003506657299 

API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut", "sexy"]
DOWNLOAD_DIR = "./downloads/"
LINK_WARNINGS = {}
SCAN_DATA = {}

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_ULTRA_V7", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- A1 UI INTERFACE ---

DM_START_TEXT = """
✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🛡️ **ɪ ᴀᴍ ᴛʜᴇ ᴍᴏsᴛ ᴘᴏᴡᴇʀғᴜʟ ɢᴜᴀʀᴅɪᴀɴ**
I protect your groups from NSFW Media, Bad Words, and Spam.

**Status:** `A1 Pro Max Active` 🚀
━━━━━━━━━━━━━━━━━━━━
"""

BAN_CARD = """
✨ **ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🚫 **ᴜsᴇʀ ʙᴀɴɴᴇᴅ ɪɴsᴛᴀɴᴛʟʏ**
━━━━━━━━━━━━━━━━━━━━
👤 **User:** {user}
🆔 **ID:** `{user_id}`
📝 **Reason:** `{reason}`
🛠️ **Action:** `All Messages Cleared + Ban`
━━━━━━━━━━━━━━━━━━━━
"""

# --- CORE FUNCTIONS ---

async def send_to_logs(client, message, user, reason, action):
    try:
        await client.send_message(
            LOG_CHANNEL_ID,
            f"🚨 **ᴀ1 sʏsᴛᴇᴍ ᴀᴄᴛɪᴏɴ ʟᴏɢ**\n━━━━━━━━━━━━\n🛠️ **Action:** `{action}`\n👤 **Name:** {user.first_name}\n🆔 **ID:** `{user.id}`\n📝 **Reason:** `{reason}`\n📍 **Group:** {message.chat.title}\n━━━━━━━━━━━━"
        )
    except: pass

def check_nsfw(file_path):
    if not file_path or not os.path.exists(file_path): return False
    if file_path.endswith((".webp", ".png")):
        try:
            img = Image.open(file_path).convert("RGB")
            t_path = file_path + ".jpg"
            img.save(t_path, "JPEG")
            file_path = t_path
        except: pass
    
    params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
    try:
        r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': open(file_path, 'rb')}, data=params)
        res = r.json()
        if res.get('status') == 'success':
            n = res['nudity']
            # Strict threshold for instant action
            if n['sexual_display'] > 0.2 or n['erotica'] > 0.2 or n['sexual_activity'] > 0.2: return True
    except: pass
    return False

async def a1_instant_destruction(client, message, reason):
    user = message.from_user
    try:
        # 1. Pehle Triggering Message udaao (Sabse zaroori)
        await message.delete()
        # 2. Fir User ko Ban karo
        await message.chat.ban_member(user.id)
        # 3. Fir uski saari History saaf karo
        await client.delete_user_history(message.chat.id, user.id)
        # 4. Report bhejo
        await message.reply_text(BAN_CARD.format(user=user.mention, user_id=user.id, reason=reason))
        await send_to_logs(client, message, user, reason, "Instant Ban + History Clear")
    except Exception as e:
        print(f"Ban Error: {e}")

# --- HANDLERS ---

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    if message.chat.type == message.chat.type.PRIVATE:
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Me to Your Group", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")]])
        await message.reply_text(DM_START_TEXT, reply_markup=buttons)

@app.on_message(filters.group & ~filters.service)
async def a1_guardian(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id
    
    # Admin Check
    is_admin = False
    try:
        member = await client.get_chat_member(message.chat.id, u_id)
        if member.status in ["administrator", "creator"]: is_admin = True
    except: pass

    # 1. MEDIA SCAN (Photos, Videos, Stickers)
    file_path = None
    try:
        if message.photo or message.sticker or message.video or (message.document and message.document.file_name and message.document.file_name.endswith('.zip')):
            # Direct delete logic for stickers/images
            file_path = await message.download(file_name=DOWNLOAD_DIR)
            if check_nsfw(file_path):
                # Pehle delete, fir baaki action
                await message.delete() 
                if not is_admin:
                    await a1_instant_destruction(client, message, "NSFW Content")
                else:
                    await send_to_logs(client, message, message.from_user, "NSFW (Admin)", "Admin Message Deleted Only")
                    await message.reply(f"⚠️ **Admin Alert!** NSFW media detect hua aur mita diya gaya.")
    except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

# 2. JOIN SCAN
@app.on_message(filters.group & filters.new_chat_members)
async def join_check(client, message: Message):
    for u in message.new_chat_members:
        # Profile Pic Scan
        photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
            if check_nsfw(path):
                await message.chat.ban_member(u.id)
                await client.delete_user_history(message.chat.id, u.id)
                await send_to_logs(client, message, u, "NSFW Profile Pic", "Join Ban + History Clear")
            if os.path.exists(path): os.remove(path)

print("🚀 A1 V7 (FIXED) IS LIVE...")
app.run()
