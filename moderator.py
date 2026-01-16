import os, requests, re, cv2, asyncio, zipfile, shutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "" 

# Sightengine Keys
API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

# Settings
BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut"]
DOWNLOAD_DIR = "./downloads/"
LINK_WARNINGS = {} # Links ke warnings track karne ke liye

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_ULTRA_V4_FINAL", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- A1 INTERFACE ---

BAN_CARD = """
✨ **ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🚫 **ᴜsᴇʀ ʙᴀɴɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ**
━━━━━━━━━━━━━━━━━━━━
👤 **User:** {user}
🆔 **ID:** `{user_id}`
🔗 **Link:** [Profile Link](tg://user?id={user_id})
📝 **Reason:** `{reason}`
🛠️ **Action:** `Direct Ban + All Messages Cleared`
━━━━━━━━━━━━━━━━━━━━
"""

# --- CORE AI DETECTION ---

def check_nsfw(file_path):
    if not file_path or not os.path.exists(file_path): return False
    # Convert stickers to JPG for accurate AI scanning
    if file_path.endswith((".webp", ".png")):
        try:
            img = Image.open(file_path).convert("RGB")
            file_path = file_path + ".jpg"
            img.save(file_path, "JPEG")
        except: pass
    
    params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
            res = r.json()
            if res.get('status') == 'success':
                n = res['nudity']
                # Threshold for direct ban (nudity detected)
                if n['sexual_display'] > 0.3 or n['erotica'] > 0.3 or n['sexual_activity'] > 0.3:
                    return True
    except: pass
    return False

async def a1_direct_ban(client, message, reason):
    user_id = message.from_user.id
    try:
        await message.chat.ban_member(user_id)
        await client.delete_user_history(message.chat.id, user_id)
        await message.reply_text(BAN_CARD.format(user=message.from_user.mention, user_id=user_id, reason=reason))
    except: pass

# --- HANDLERS ---

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("✨ **A1 NSFW Director is Active!**\nDirect ban for Nudity. Warning for Links.")

@app.on_message(filters.group & ~filters.service)
async def a1_guardian(client, message: Message):
    if not message.from_user: return
    user_id = message.from_user.id

    # 1. LINK WARNING SYSTEM
    text = (message.text or message.caption or "").lower()
    if "t.me/" in text or "http" in text:
        LINK_WARNINGS[user_id] = LINK_WARNINGS.get(user_id, 0) + 1
        if LINK_WARNINGS[user_id] >= 3:
            await a1_direct_ban(client, message, "Spamming Links (3 Warnings)")
        else:
            await message.reply(f"⚠️ {message.from_user.mention}, **Warning {LINK_WARNINGS[user_id]}/3!** Links are not allowed.")
            await message.delete()
        return

    # 2. BAD WORDS SCAN
    if any(re.search(rf"\b{word}\b", text) for word in BAD_WORDS):
        await a1_direct_ban(client, message, "Bad Words Used")
        return

    # 3. MEDIA SCAN (Photos, Videos, Stickers)
    file_path = None
    try:
        if message.photo or message.sticker or message.video:
            # Animated Stickers ban
            if message.sticker and message.sticker.is_animated:
                await a1_direct_ban(client, message, "Animated Sticker (Prohibited)")
                return

            file_path = await message.download(file_name=DOWNLOAD_DIR)
            is_bad = False

            # Video/Video Sticker Frame Scan
            if message.video or (message.sticker and message.sticker.is_video):
                cap = cv2.VideoCapture(file_path)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 5) # Scan 5th frame
                ret, frame = cap.read()
                if ret:
                    tmp_v = f"{DOWNLOAD_DIR}v_{message.id}.jpg"
                    cv2.imwrite(tmp_v, frame)
                    if check_nsfw(tmp_v): is_bad = True
                    os.remove(tmp_v)
                cap.release()
            else:
                is_bad = check_nsfw(file_path)

            if is_bad:
                await a1_direct_ban(client, message, "NSFW Content Detected")

    except Exception as e: print(f"A1 Log Error: {e}")
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

# 4. JOINING MEMBER PROFILE GUARD
@app.on_message(filters.group & filters.new_chat_members)
async def join_check(client, message: Message):
    for u in message.new_chat_members:
        # Name scan
        if any(word in f"{u.first_name} {u.last_name or ''}".lower() for word in BAD_WORDS):
            await message.chat.ban_member(u.id)
            await message.reply(f"🚫 **Ban!** {u.mention} has a bad name.")
            continue
            
        # Profile Pic Scan
        photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
            if check_nsfw(path):
                await message.chat.ban_member(u.id)
                await message.reply(f"🚫 **Auto-Ban!** {u.mention} joined with NSFW Profile Picture.")
            if os.path.exists(path): os.remove(path)

print("🚀 A1 ULTRA DIRECTOR IS LIVE...")
app.run()
