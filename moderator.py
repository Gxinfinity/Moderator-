import os
import requests
import re
import cv2
import asyncio
import zipfile
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = ""
API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

# Gande Words List
BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut"]

# Downloads folder fix
DOWNLOAD_DIR = "./downloads/"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

app = Client("A1_ULTRA_DIRECTOR", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- A1 INTERFACE ---

BAN_CARD = """
🚫 **NSFW VIOLATION DETECTED**
━━━━━━━━━━━━━━━━━━━━
👤 **User:** {user}
🆔 **ID:** `{user_id}`
📝 **Reason:** `{reason}`
🛠️ **Action:** `Permanent Ban + History Cleared`
━━━━━━━━━━━━━━━━━━━━
"""

# --- CORE FUNCTIONS ---

def check_nsfw(file_path):
    if not file_path or not os.path.exists(file_path): return False
    params = {'models': 'nudity-2.0,wad', 'api_user': API_USER, 'api_secret': API_SECRET}
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
            res = r.json()
            if res.get('status') == 'success':
                n = res['nudity']
                if n['sexual_display'] > 0.3 or n['erotica'] > 0.3: return True
    except: pass
    return False

async def a1_ban_cleanup(client, message, reason):
    try:
        user_id = message.from_user.id
        await message.chat.ban_member(user_id)
        await client.delete_user_history(message.chat.id, user_id)
        await message.reply_text(BAN_CARD.format(user=message.from_user.mention, user_id=user_id, reason=reason))
    except: pass

# --- HANDLERS ---

@app.on_message(filters.command("start") & filters.private)
async def start_private(client, message):
    await message.reply_text(
        "✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨\n━━━━━━━━━━━━━━━━━━━━\n🛡️ I am active and protecting your groups.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Me to Group", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")]])
    )

@app.on_message(filters.group & ~filters.service)
async def a1_logic(client, message: Message):
    if not message.from_user: return
    user = message.from_user

    # 1. Name/Username Scan
    u_info = f"{user.first_name} {user.last_name or ''} {user.username or ''}".lower()
    if any(word in u_info for word in BAD_WORDS):
        await a1_ban_cleanup(client, message, "NSFW in Name/Username")
        return

    # 2. Text/Caption Scan
    text = (message.text or message.caption or "").lower()
    if any(re.search(rf"\b{word}\b", text) for word in BAD_WORDS):
        await a1_ban_cleanup(client, message, "Gande Words Used")
        return

    # 3. Media/Sticker/Zip Scan
    file_path = None
    try:
        # ZIP CHECK
        if message.document and message.document.file_name and message.document.file_name.endswith('.zip'):
            file_path = await message.download(file_name=DOWNLOAD_DIR)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                z_tmp = f"{DOWNLOAD_DIR}unzip_{message.id}"
                zip_ref.extractall(z_tmp)
                for r, _, files in os.walk(z_tmp):
                    for f in files:
                        if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                            if check_nsfw(os.path.join(r, f)):
                                await a1_ban_cleanup(client, message, "NSFW inside ZIP")
                                shutil.rmtree(z_tmp)
                                return
                shutil.rmtree(z_tmp)

        # STICKER/PHOTO/VIDEO CHECK
        elif message.photo or message.sticker or message.video:
            # Animated Stickers ban
            if message.sticker and message.sticker.is_animated:
                await a1_ban_cleanup(client, message, "Animated Sticker (Prohibited)")
                return

            file_path = await message.download(file_name=DOWNLOAD_DIR)
            is_bad = False
            
            if message.video or (message.sticker and message.sticker.is_video):
                cap = cv2.VideoCapture(file_path)
                ret, frame = cap.read()
                if ret:
                    tmp_frame = f"{DOWNLOAD_DIR}frame_{message.id}.jpg"
                    cv2.imwrite(tmp_frame, frame)
                    if check_nsfw(tmp_frame): is_bad = True
                    if os.path.exists(tmp_frame): os.remove(tmp_frame)
                cap.release()
            else:
                is_bad = check_nsfw(file_path)

            if is_bad:
                await a1_ban_cleanup(client, message, "NSFW Media/Sticker")

    except Exception as e:
        print(f"A1 Error: {e}")
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

# 4. Join Scan
@app.on_message(filters.group & filters.new_chat_members)
async def join_scan(client, message: Message):
    for u in message.new_chat_members:
        photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
            if check_nsfw(path):
                await message.chat.ban_member(u.id)
                await message.reply(BAN_CARD.format(user=u.mention, user_id=u.id, reason="NSFW Profile Picture"))
            if os.path.exists(path): os.remove(path)

print("🚀 A1 ULTRA PRO MAX IS LIVE (Bugs Fixed)...")
app.run()
