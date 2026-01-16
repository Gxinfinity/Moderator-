import os, requests, re, cv2, asyncio, zipfile, shutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "YAHAN_APNA_TOKEN" 

# Sahii ID daalein (Example: -100xxxxxxxxxx)
LOG_CHANNEL_ID = -1003506657299 
SUDO_USERS = [7487670897, 8409591285] 

API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut", "sexy"]
DOWNLOAD_DIR = "./downloads/"
ADMIN_WARNINGS = {} # Sirf Admins ke liye

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_GOD_MODE_FINAL", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- A1 INTERFACE ---

BAN_CARD = """
✨ **ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🚫 **ᴜsᴇʀ ʙᴀɴɴᴇᴅ ɪɴsᴛᴀɴᴛʟʏ**
━━━━━━━━━━━━━━━━━━━━
👤 **User:** {user}
🆔 **ID:** `{user_id}`
📝 **Reason:** `{reason}`
🛠️ **Action:** `Full History Cleanup + Ban`
━━━━━━━━━━━━━━━━━━━━
"""

# --- CORE FUNCTIONS ---

async def send_logs(client, message, user, reason, action):
    try:
        report = (
            f"🚨 **ᴀ1 sʏsᴛᴇᴍ ᴀᴄᴛɪᴏɴ ʟᴏɢ**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛠️ **Action:** `{action}`\n"
            f"👤 **Name:** {user.first_name}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"🔗 **Username:** @{user.username or 'None'}\n"
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
            # Strict threshold for instant action
            if n['sexual_display'] > 0.2 or n['erotica'] > 0.2 or n['sexual_activity'] > 0.2: return True
    except: pass
    return False

async def a1_instant_destruction(client, message, reason):
    user = message.from_user
    chat_id = message.chat.id
    try:
        # 1. Pehle Triggering message udaao
        await message.delete()
        # 2. Phir Permanent Ban
        await message.chat.ban_member(user.id)
        # 3. Phir user ki poori HISTORY wipe (Supergroup required)
        await client.delete_user_history(chat_id, user.id)
        # 4. Report
        await message.reply_text(BAN_CARD.format(user=user.mention, user_id=user.id, reason=reason))
        await send_logs(client, message, user, reason, "Instant Destruction (Ban + History Wipe)")
    except Exception as e: print(f"Destruction Error: {e}")

# --- GUARDIAN LOGIC ---

@app.on_message(filters.group & ~filters.service)
async def a1_guardian(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id
    
    # Admin Check
    is_admin = False
    try:
        member = await client.get_chat_member(message.chat.id, u_id)
        if member.status in [member.status.ADMINISTRATOR, member.status.OWNER]: is_admin = True
    except: pass

    text = (message.text or message.caption or "").lower()

    # 1. LINK PROTECTION
    if "t.me/" in text or "http" in text or message.forward_from or message.forward_from_chat:
        # Mili-seconds mein delete
        await message.delete()
        if is_admin:
            ADMIN_WARNINGS[u_id] = ADMIN_WARNINGS.get(u_id, 0) + 1
            await message.reply(f"⚠️ **Admin Warning {ADMIN_WARNINGS[u_id]}/3!** Links allowed nahi hain.")
            return
        
        # Normal User: Direct Ban (No Warning)
        await a1_instant_destruction(client, message, "Spamming Links (Direct Ban)")
        return

    # 2. MEDIA SCAN (Photo, Sticker, Video, Zip)
    file_path = None
    try:
        if message.photo or message.sticker or message.video or (message.document and message.document.file_name and message.document.file_name.endswith('.zip')):
            file_path = await message.download(file_name=DOWNLOAD_DIR)
            if check_nsfw(file_path):
                # Pehle message delete karo
                await message.delete()
                if not is_admin:
                    # Normal User: Direct Ban
                    await a1_instant_destruction(client, message, "NSFW Media Violation")
                else:
                    # Admin: Warning Only
                    ADMIN_WARNINGS[u_id] = ADMIN_WARNINGS.get(u_id, 0) + 1
                    await message.reply(f"⚠️ **Admin Warning {ADMIN_WARNINGS[u_id]}/3!** NSFW media removed.")
                    await send_logs(client, message, message.from_user, "NSFW Media (Admin)", "Warning + Deletion")
    except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

# 3. JOIN SCAN (Profile Pic & Name)
@app.on_message(filters.group & filters.new_chat_members)
async def join_guard(client, message: Message):
    for u in message.new_chat_members:
        if any(word in f"{u.first_name} {u.username or ''}".lower() for word in BAD_WORDS):
            await message.chat.ban_member(u.id); continue
        
        photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
            if check_nsfw(path):
                await message.chat.ban_member(u.id)
                await client.delete_user_history(message.chat.id, u.id)
                await send_logs(client, message, u, "NSFW Profile Pic", "Join Ban + History Wipe")
            if os.path.exists(path): os.remove(path)

# Health Check Command
@app.on_message(filters.command("check") & filters.group)
async def health_check(client, message):
    me = await client.get_chat_member(message.chat.id, "me")
    report = (
        f"🛠️ **ᴀ1 ʙᴏᴛ sᴛᴀᴛᴜs ᴄʜᴇᴄᴋ**\n"
        f"━━━━━━━━━━━━\n"
        f"🚫 **Ban Status:** {'✅' if me.privileges.can_restrict_members else '❌'}\n"
        f"🗑️ **Delete Status:** {'✅' if me.privileges.can_delete_messages else '❌'}\n"
        f"📊 **Supergroup:** {'✅' if message.chat.type.name == 'SUPERGROUP' else '❌'}\n"
        f"━━━━━━━━━━━━"
    )
    await message.reply(report)

print("🚀 A1 GOD MODE FINAL FIX IS LIVE...")
app.run()
