import os
import requests
import re
import cv2
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "YAHAN_TOKEN_DAALEIN" # @BotFather se lein

API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut"]

app = Client("A1_ULTRA_PRO_MAX", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- A1 INTERFACE DESIGNS ---

# DM (Private Chat) Start Interface
DM_START_TEXT = """
✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🛡️ **I am the most advanced NSFW Guardian.**
I protect your groups from:
• 🔞 **NSFW Photos & Videos**
• 🔞 **Gande Stickers (All Types)**
• 🤬 **Abuses & Bad Words**
• 👤 **NSFW Profile & Name/Bio**

**Status:** `A1 - Ultra Active` 🚀
━━━━━━━━━━━━━━━━━━━━
"""

# Group Start Interface
GP_START_TEXT = """
🛡️ **ᴀ1 ɴsғᴡ sʏsᴛᴇᴍ ɪs ᴏɴʟɪɴᴇ**
━━━━━━━━━━━━━━━━━━━━
✅ **Group is now under A1 Protection.**
I will automatically:
• Ban anyone sending NSFW.
• Delete all messages of the banned user.
• Scan joining members for NSFW DPs.

**Powered By:** `A1 Ultra Pro Max`
━━━━━━━━━━━━━━━━━━━━
"""

# Attractive Ban Card
BAN_CARD = """
🚫 **NSFW VIOLATION DETECTED**
━━━━━━━━━━━━━━━━━━━━
👤 **User:** {user}
🆔 **ID:** `{user_id}`
📝 **Reason:** `{reason}`
🛠️ **Action:** `Permanent Ban + History Cleared`
━━━━━━━━━━━━━━━━━━━━
"""

# --- HELPER FUNCTIONS ---

def check_nsfw(file_path):
    if not file_path or not os.path.exists(file_path): return False
    params = {'models': 'nudity-2.0,wad', 'api_user': API_USER, 'api_secret': API_SECRET}
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
            res = r.json()
            if res.get('status') == 'success':
                n = res['nudity']
                # High sensitivity for A1 performance
                if n['sexual_display'] > 0.3 or n['erotica'] > 0.3: return True
    except: pass
    return False

async def full_cleanup_ban(client, message, reason):
    user_id = message.from_user.id
    try:
        # 1. Ban User
        await message.chat.ban_member(user_id)
        # 2. Delete Entire History of that user
        await client.delete_user_history(message.chat.id, user_id)
        # 3. Alert Group
        await message.reply_text(BAN_CARD.format(user=message.from_user.mention, user_id=user_id, reason=reason))
        # 4. Save Log
        with open("logs.txt", "a+") as f: f.write(f"Banned: {user_id} | Reason: {reason}\n")
    except: pass

# --- COMMAND HANDLERS ---

@app.on_message(filters.command("start") & filters.private)
async def start_private(client, message):
    await message.reply_text(
        text=DM_START_TEXT,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Add Me to Your Group", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")
        ], [
            InlineKeyboardButton("📢 Support Channel", url="https://t.me/YourSupportChannel")
        ]])
    )

@app.on_message(filters.command("start") & filters.group)
async def start_group(client, message):
    await message.reply_text(text=GP_START_TEXT)

# --- MAIN GUARD LOGIC (A1 Level) ---

@app.on_message(filters.group & ~filters.service)
async def a1_guardian(client, message: Message):
    if not message.from_user: return
    user = message.from_user

    # 1. NAME/USERNAME SCAN
    name_check = f"{user.first_name} {user.last_name or ''} {user.username or ''}".lower()
    for word in BAD_WORDS:
        if word in name_check:
            await full_cleanup_ban(client, message, f"Ganda Name/Bio ({word})")
            return

    # 2. TEXT & CAPTION SCAN
    text = (message.text or message.caption or "").lower()
    for word in BAD_WORDS:
        if re.search(rf"\b{word}\b", text):
            await full_cleanup_ban(client, message, f"Bad Words Used ({word})")
            return

    # 3. STICKER & MEDIA SCAN
    file_path = None
    try:
        if message.sticker:
            # Animated Stickers (.tgs) direct block/ban for security
            if message.sticker.is_animated:
                await full_cleanup_ban(client, message, "Animated Sticker (Prohibited)")
                return
            
            # Static/Video Stickers download aur scan
            file_path = await message.download()
            if check_nsfw(file_path):
                await full_cleanup_ban(client, message, "NSFW Sticker")

        elif message.photo or message.video:
            file_path = await message.download()
            is_bad = False
            if message.video:
                cap = cv2.VideoCapture(file_path)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 10) # 10th frame check
                ret, frame = cap.read()
                if ret:
                    cv2.imwrite("v_tmp.jpg", frame)
                    if check_nsfw("v_tmp.jpg"): is_bad = True
                    os.remove("v_tmp.jpg")
                cap.release()
            else:
                is_bad = check_nsfw(file_path)

            if is_bad:
                await full_cleanup_ban(client, message, "NSFW Media")

    except Exception as e: print(f"Error: {e}")
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

# 4. PROFILE PICTURE GUARD
@app.on_message(filters.group & filters.new_chat_members)
async def profile_check(client, message: Message):
    for user in message.new_chat_members:
        photos = [p async for p in client.get_chat_photos(user.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id)
            if check_nsfw(path):
                await message.chat.ban_member(user.id)
                await message.reply(BAN_CARD.format(user=user.mention, user_id=user.id, reason="NSFW Profile Picture"))
            if os.path.exists(path): os.remove(path)

print("💎 A1 ULTRA PRO MAX INTERFACE IS LIVE...")
app.run()
