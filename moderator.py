import os, requests, re, cv2, asyncio, zipfile, shutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "" 

LOG_CHANNEL_ID = -1003506657299 
SUDO_USERS = [7487670897, 8409591285] 

API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut", "sexy"]
DOWNLOAD_DIR = "./downloads/"
ADMIN_WARNINGS = {} 

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_TURBO_GOD", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- CORE FUNCTIONS ---

async def send_logs(client, message, user, reason, action):
    try:
        report = (
            f"🚨 **ᴀ1 sʏsᴛᴇᴍ ᴀᴄᴛɪᴏɴ ʟᴏɢ**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛠️ **Action:** `{action}`\n"
            f"👤 **Name:** {user.first_name}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"📝 **Reason:** `{reason}`\n"
            f"📍 **Group:** {message.chat.title}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await client.send_message(LOG_CHANNEL_ID, report)
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
            # Highly sensitive threshold
            if n['sexual_display'] > 0.15 or n['erotica'] > 0.15: return True
    except: pass
    return False

async def a1_instant_destruction(client, message, reason):
    user = message.from_user
    chat_id = message.chat.id
    try:
        # 1. Pehle user ko BAN karo taki wo aur messages na bhej sake
        await message.chat.ban_member(user.id)
        
        # 2. FAST BATCH DELETION Logic
        msg_ids = []
        async for msg in client.get_chat_history(chat_id, limit=200): # Pichle 200 messages scan karega
            if msg.from_user and msg.from_user.id == user.id:
                msg_ids.append(msg.id)
        
        if msg_ids:
            await client.delete_messages(chat_id, msg_ids) # Ek saath saare uda dega (Very Fast)
        
        # 3. Report
        await message.reply_text(f"🚫 **Turbo Ban!** {user.mention} removed. {len(msg_ids)} messages wiped instantly.")
        await send_logs(client, message, user, reason, f"Instant Ban + {len(msg_ids)} Messages Deleted")
    except Exception as e: print(f"Destruction Error: {e}")

# --- GUARDIAN LOGIC ---

@app.on_message(filters.group & ~filters.service)
async def a1_guardian(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id
    
    is_admin = False
    try:
        member = await client.get_chat_member(message.chat.id, u_id)
        if member.status in [member.status.ADMINISTRATOR, member.status.OWNER]: is_admin = True
    except: pass

    # 1. LINK PROTECTION
    text = (message.text or message.caption or "").lower()
    if "t.me/" in text or "http" in text:
        await message.delete()
        if is_admin:
            ADMIN_WARNINGS[u_id] = ADMIN_WARNINGS.get(u_id, 0) + 1
            await message.reply(f"⚠️ **Admin Warning {ADMIN_WARNINGS[u_id]}/3!** Links delete kar diye gaye hain.")
            return
        await a1_instant_destruction(client, message, "Spamming Links")
        return

    # 2. STICKER & MEDIA SCAN (Instant Action)
    file_path = None
    try:
        if message.photo or message.sticker or message.video:
            # Animated Sticker handle
            if message.sticker and message.sticker.is_animated:
                await message.delete()
                if not is_admin: await a1_instant_destruction(client, message, "Animated Sticker")
                return

            file_path = await message.download(file_name=DOWNLOAD_DIR)
            is_bad = False
            
            if message.video or (message.sticker and message.sticker.is_video):
                cap = cv2.VideoCapture(file_path); cap.set(cv2.CAP_PROP_POS_FRAMES, 5)
                ret, frame = cap.read()
                if ret:
                    tmp = f"{DOWNLOAD_DIR}v_{message.id}.jpg"; cv2.imwrite(tmp, frame)
                    is_bad = check_nsfw(tmp); os.remove(tmp)
                cap.release()
            else:
                is_bad = check_nsfw(file_path)

            if is_bad:
                await message.delete()
                if not is_admin: 
                    await a1_instant_destruction(client, message, "NSFW Media")
                else: 
                    await message.reply("⚠️ **Admin Alert!** NSFW media removed.")
                    await send_logs(client, message, message.from_user, "NSFW Media (Admin)", "Warning + Deletion")
    except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

# 3. JOIN GUARD (Profile, Bio & Name Scan)
@app.on_message(filters.group & filters.new_chat_members)
async def join_guard(client, message: Message):
    for u in message.new_chat_members:
        try:
            full_user = await client.get_users(u.id)
            bio = (full_user.bio or "").lower()
            name = f"{u.first_name} {u.last_name or ''} {u.username or ''}".lower()

            if any(word in name for word in BAD_WORDS) or any(word in bio for word in BAD_WORDS):
                await message.chat.ban_member(u.id)
                await message.reply(f"🚫 **Direct Ban!** {u.mention} banned for NSFW Name/Bio.")
                continue
            
            photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
            if photos:
                path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
                if check_nsfw(path):
                    await message.chat.ban_member(u.id)
                    # Instant Cleanup for new member
                    async for msg in client.get_chat_history(message.chat.id, limit=50):
                        if msg.from_user and msg.from_user.id == u.id:
                            try: await msg.delete()
                            except: pass
                    await message.reply(f"🚫 **Auto-Ban!** {u.mention} had NSFW PFP.")
                if os.path.exists(path): os.remove(path)
        except: pass

print("🚀 A1 TURBO GOD MODE IS LIVE...")
app.run()
