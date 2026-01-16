import os
import requests
import re
import zipfile
import cv2
import shutil
from pyrogram import Client, filters
from pyrogram.types import Message

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = ""

API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

# Database/Logs File
LOG_FILE = "ban_logs.txt"
BANNED_STICKERS_DB = "nsfw_stickers.txt"

# Bad Words
BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut"]

app = Client("A1_ULTRA_V2", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UTILS ---

def save_log(log_msg):
    with open(LOG_FILE, "a+", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def blacklist_sticker(sticker_id):
    with open(BANNED_STICKERS_DB, "a+", encoding="utf-8") as f:
        f.write(sticker_id + "\n")

def is_sticker_blacklisted(sticker_id):
    if not os.path.exists(BANNED_STICKERS_DB): return False
    with open(BANNED_STICKERS_DB, "r") as f:
        return sticker_id in f.read()

def check_nsfw(file_path):
    if not file_path or not os.path.exists(file_path): return False
    params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
    with open(file_path, 'rb') as f:
        try:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
            output = r.json()
            if output.get('status') == 'success':
                nudity = output['nudity']
                if nudity['sexual_display'] > 0.5 or nudity['erotica'] > 0.5:
                    return True
        except: pass
    return False

def check_video_nsfw(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    for i in [frame_count//4, frame_count//2, (3*frame_count)//4]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            tmp = f"vframe_{i}.jpg"
            cv2.imwrite(tmp, frame)
            bad = check_nsfw(tmp)
            os.remove(tmp)
            if bad:
                cap.release()
                return True
    cap.release()
    return False

# --- UI INTERFACE MESSAGES ---

BAN_MSG = """
╔════════════════════════
║ 🛡️ **NSFW VIOLATION DETECTED**
╠════════════════════════
║ 👤 **User:** {user}
║ 🆔 **ID:** `{user_id}`
║ 🚫 **Reason:** {reason}
║ 🛠️ **Action:** Permanent Ban
╚════════════════════════
"""

# --- HANDLERS ---

@app.on_message(filters.command("logs") & filters.group)
async def view_logs(client, message):
    if os.path.exists(LOG_FILE):
        await message.reply_document(LOG_FILE, caption="📁 **NSFW Ban History Logs**")
    else:
        await message.reply("No logs found yet.")

@app.on_message(filters.group & (filters.photo | filters.video | filters.sticker | filters.document))
async def a1_moderator(client, message: Message):
    file_path = None
    reason = "NSFW Content"
    
    # 1. Check if Sticker is already Blacklisted
    if message.sticker and is_sticker_blacklisted(message.sticker.file_unique_id):
        await message.chat.ban_member(message.from_user.id)
        await message.delete()
        return

    try:
        # Video Stickers & Videos
        if message.video or (message.sticker and message.sticker.is_video) or (message.document and message.document.mime_type and "video" in message.document.mime_type):
            file_path = await message.download()
            if check_video_nsfw(file_path):
                if message.sticker: blacklist_sticker(message.sticker.file_unique_id)
                await message.chat.ban_member(message.from_user.id)
                await message.delete()
                log = f"Banned {message.from_user.id} for Video NSFW"
                save_log(log)
                await message.reply(BAN_MSG.format(user=message.from_user.mention, user_id=message.from_user.id, reason="Video/Animated NSFW"))

        # Static Stickers & Photos
        elif message.photo or message.sticker or (message.document and message.document.mime_type and "image" in message.document.mime_type):
            # Skip animated .tgs stickers as they are JSON (AI can't scan)
            if message.sticker and message.sticker.is_animated:
                return # Manual check needed for .tgs or just block all animated

            file_path = await message.download()
            if check_nsfw(file_path):
                if message.sticker: blacklist_sticker(message.sticker.file_unique_id)
                await message.chat.ban_member(message.from_user.id)
                await message.delete()
                log = f"Banned {message.from_user.id} for Image/Sticker NSFW"
                save_log(log)
                await message.reply(BAN_MSG.format(user=message.from_user.mention, user_id=message.from_user.id, reason="Image/Sticker NSFW"))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

# --- NEW JOIN SCAN ---
@app.on_message(filters.group & filters.new_chat_members)
async def join_guard(client, message: Message):
    for user in message.new_chat_members:
        photos = [p async for p in client.get_chat_photos(user.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id)
            if check_nsfw(path):
                await message.chat.ban_member(user.id)
                await message.reply(BAN_MSG.format(user=user.mention, user_id=user.id, reason="NSFW Profile Picture"))
            if os.path.exists(path): os.remove(path)

print("💎 A1 ULTRA V2 IS LIVE...")
app.run()
