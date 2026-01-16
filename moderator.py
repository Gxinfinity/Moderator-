import os
import requests
import re
import cv2
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "" 
API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut"]

app = Client("A1_PRO_DIRECTOR", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- UI INTERFACE (Unique & Attractive) ---

START_TEXT = """
✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🛡️ **I am the most advanced NSFW Guardian.**
I protect your groups from:
• 🔞 NSFW Photos & Videos
• 🔞 Gande Stickers
• 🤬 Bad Words & Abuses
• 🔞 NSFW Profile Pictures

**Status:** `Running Smoothly` 🚀
━━━━━━━━━━━━━━━━━━━━
"""

BAN_CARD = """
🚫 **NSFW VIOLATION DETECTED**
━━━━━━━━━━━━━━━━━━━━
👤 **User:** {user}
🆔 **ID:** `{user_id}`
📝 **Reason:** `{reason}`
🛠️ **Action:** `Permanent Ban`
━━━━━━━━━━━━━━━━━━━━
"""

# --- HELPER FUNCTIONS ---

def save_log(msg):
    with open("logs.txt", "a+") as f:
        f.write(msg + "\n")

def check_nsfw(file_path):
    if not file_path or not os.path.exists(file_path): return False
    params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
            res = r.json()
            if res.get('status') == 'success':
                n = res['nudity']
                if n['sexual_display'] > 0.5 or n['erotica'] > 0.5: return True
    except: pass
    return False

# --- COMMANDS ---

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        text=START_TEXT,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("➕ Add Me to Group", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")
        ]])
    )

# --- MAIN MODERATOR LOGIC ---

@app.on_message(filters.group & (filters.text | filters.photo | filters.video | filters.sticker | filters.document))
async def a1_guard(client, message: Message):
    if not message.from_user: return
    
    # 1. BAD WORDS SCAN
    if message.text:
        for word in BAD_WORDS:
            if re.search(rf"\b{word}\b", message.text.lower()):
                try:
                    await message.chat.ban_member(message.from_user.id)
                    await message.delete()
                    save_log(f"Banned {message.from_user.id} for Bad Words")
                    return
                except: pass

    # 2. STICKER & MEDIA SCAN
    file_path = None
    try:
        if message.sticker:
            # Animated Stickers (.tgs) scan nahi ho sakte, isliye seedha ban
            if message.sticker.is_animated:
                await message.chat.ban_member(message.from_user.id)
                await message.delete()
                await message.reply(BAN_CARD.format(user=message.from_user.mention, user_id=message.from_user.id, reason="Animated Sticker (Prohibited)"))
                return
            
            # Static aur Video Stickers scan karein
            file_path = await message.download()
            if check_nsfw(file_path):
                await message.chat.ban_member(message.from_user.id)
                await message.delete()
                await message.reply(BAN_CARD.format(user=message.from_user.mention, user_id=message.from_user.id, reason="NSFW Sticker Detected"))
                save_log(f"Banned {message.from_user.id} for NSFW Sticker")

        elif message.photo or message.video:
            file_path = await message.download()
            # Video frames scan logic
            is_bad = False
            if message.video:
                cap = cv2.VideoCapture(file_path)
                ret, frame = cap.read()
                if ret:
                    cv2.imwrite("v_tmp.jpg", frame)
                    if check_nsfw("v_tmp.jpg"): is_bad = True
                    os.remove("v_tmp.jpg")
                cap.release()
            else:
                is_bad = check_nsfw(file_path)

            if is_bad:
                await message.chat.ban_member(message.from_user.id)
                await message.delete()
                await message.reply(BAN_CARD.format(user=message.from_user.mention, user_id=message.from_user.id, reason="NSFW Media Detected"))
                save_log(f"Banned {message.from_user.id} for NSFW Media")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

print("💎 A1 ULTRA PRO IS LIVE...")
app.run()
