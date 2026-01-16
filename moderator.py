import os, requests, re, cv2, asyncio, zipfile, shutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "" 

# Log Channel ID yahan daalein (Example: -100123456789)
LOG_CHANNEL_ID = -1003506657299 

API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut", "sexy"]
DOWNLOAD_DIR = "./downloads/"
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_ULTRA_LOG_EDITION", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- A1 INTERFACE DESIGNS ---

LOG_TEXT = """
🚨 **ᴀ1 sʏsᴛᴇᴍ ᴀᴄᴛɪᴏɴ ʟᴏɢ** 🚨
━━━━━━━━━━━━━━━━━━━━
🛠️ **Action:** `{action}`
👤 **Name:** {name}
🆔 **User ID:** `{user_id}`
🔗 **Username:** @{username}
📝 **Reason:** `{reason}`
📍 **Group:** {group_name}
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
🛠️ **Action:** `Full Cleanup + Ban`
━━━━━━━━━━━━━━━━━━━━
"""

# --- CORE FUNCTIONS ---

async def send_to_logs(client, message, user, reason, action):
    """Log channel mein report bhejne ke liye"""
    try:
        await client.send_message(
            LOG_CHANNEL_ID,
            LOG_TEXT.format(
                action=action,
                name=user.first_name,
                user_id=user.id,
                username=user.username or "None",
                reason=reason,
                group_name=message.chat.title
            )
        )
    except Exception as e:
        print(f"Log Error: {e}")

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
            if n['sexual_display'] > 0.2 or n['erotica'] > 0.2: return True
    except: pass
    return False

async def a1_instant_destruction(client, message, reason):
    user = message.from_user
    try:
        await message.chat.ban_member(user.id)
        await client.delete_user_history(message.chat.id, user.id)
        await message.reply_text(BAN_CARD.format(user=user.mention, user_id=user.id, reason=reason))
        # Log send karein
        await send_to_logs(client, message, user, reason, "Instant Ban + History Clear")
    except Exception as e:
        print(f"Destruction Fail: {e}")

# --- GUARDIAN LOGIC ---

@app.on_message(filters.group & ~filters.service)
async def a1_guard(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id

    is_admin = False
    try:
        member = await client.get_chat_member(message.chat.id, u_id)
        if member.status in ["administrator", "creator"]: is_admin = True
    except: pass

    # 1. Media Scan (Photos, Videos, Stickers)
    file_path = None
    try:
        if message.photo or message.sticker or message.video:
            file_path = await message.download(file_name=DOWNLOAD_DIR)
            if check_nsfw(file_path):
                if not is_admin:
                    await a1_instant_destruction(client, message, "NSFW Media Detected")
                else:
                    await message.delete()
                    await send_to_logs(client, message, message.from_user, "NSFW Media (Admin)", "Message Deleted Only")
                    await message.reply("⚠️ **Admin Alert!** NSFW removed.")
    except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

# 2. Join Scan (New Members)
@app.on_message(filters.group & filters.new_chat_members)
async def join_guard(client, message: Message):
    for u in message.new_chat_members:
        # Profile Scan
        photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
            if check_nsfw(path):
                await message.chat.ban_member(u.id)
                await client.delete_user_history(message.chat.id, u.id)
                await send_to_logs(client, message, u, "NSFW Profile Picture", "Direct Join Ban")
            if os.path.exists(path): os.remove(path)

print("🚀 A1 ULTRA PRO MAX (LOG EDITION) IS LIVE...")
app.run()
