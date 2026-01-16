import os, requests, re, cv2, asyncio, zipfile, shutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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
LINK_WARNINGS = {}
ADMIN_WARNINGS = {}
GBAN_LIST = set()
SCAN_DATA = {}

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_SONIC_GOD_MODE", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- CORE SONIC FUNCTIONS ---

async def a1_sonic_cleanup(client, chat_id, user_id):
    """Fastest Batch Deletion: Background task to wipe history"""
    msg_ids = []
    try:
        async for msg in client.get_chat_history(chat_id, limit=300):
            if msg.from_user and msg.from_user.id == user_id:
                msg_ids.append(msg.id)
                if len(msg_ids) >= 100:
                    await client.delete_messages(chat_id, msg_ids)
                    msg_ids = []
        if msg_ids: await client.delete_messages(chat_id, msg_ids)
    except: pass

async def send_logs(client, message, user, reason, action):
    try:
        report = (f"🚨 **ᴀ1 sʏsᴛᴇᴍ ᴀᴄᴛɪᴏɴ ʟᴏɢ**\n━━━━━━━━━━━━\n"
                  f"🛠️ **Action:** `{action}`\n👤 **Name:** {user.first_name}\n"
                  f"🆔 **ID:** `{user.id}`\n📝 **Reason:** `{reason}`\n"
                  f"📍 **Group:** {message.chat.title}\n━━━━━━━━━━━━")
        await client.send_message(LOG_CHANNEL_ID, report)
    except: pass

def check_nsfw(file_path):
    if not file_path or not os.path.exists(file_path): return False
    if file_path.endswith((".webp", ".png")):
        try:
            img = Image.open(file_path).convert("RGB")
            t_path = file_path + ".jpg"; img.save(t_path, "JPEG")
            file_path = t_path
        except: pass
    
    params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
    try:
        r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': open(file_path, 'rb')}, data=params)
        res = r.json()
        if res.get('status') == 'success':
            n = res['nudity']
            if n['sexual_display'] > 0.15 or n['erotica'] > 0.15: return True
    except: pass
    return False

# --- HANDLERS ---

@app.on_message(filters.group & ~filters.service)
async def a1_guardian(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id
    if u_id in GBAN_LIST: await message.chat.ban_member(u_id); await message.delete(); return

    is_admin = False
    try:
        member = await client.get_chat_member(message.chat.id, u_id)
        if member.status in [member.status.ADMINISTRATOR, member.status.OWNER]: is_admin = True
    except: pass

    text = (message.text or message.caption or "").lower()

    # 1. LINK & FORWARD PROTECTION
    if "t.me/" in text or "http" in text or message.forward_from:
        await message.delete()
        if is_admin: await message.reply("⚠️ Admin, link allow nahi hai!"); return
        await message.chat.ban_member(u_id)
        asyncio.create_task(a1_sonic_cleanup(client, message.chat.id, u_id))
        return

    # 2. MEDIA & STICKER SCAN
    file_path = None
    try:
        if message.photo or message.sticker or message.video or message.document:
            if message.sticker and message.sticker.is_animated:
                await message.delete()
                if not is_admin: await message.chat.ban_member(u_id); asyncio.create_task(a1_sonic_cleanup(client, message.chat.id, u_id))
                return

            file_path = await message.download(file_name=DOWNLOAD_DIR)
            is_bad = False
            
            if message.document and message.document.file_name.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zf:
                    for f in zf.namelist():
                        if f.lower().endswith(('.jpg', '.png', '.webp')):
                            zf.extract(f, DOWNLOAD_DIR)
                            if check_nsfw(os.path.join(DOWNLOAD_DIR, f)): is_bad = True; break
            
            elif message.video or (message.sticker and message.sticker.is_video):
                cap = cv2.VideoCapture(file_path); cap.set(cv2.CAP_PROP_POS_FRAMES, 5)
                ret, frame = cap.read()
                if ret:
                    tmp = f"{DOWNLOAD_DIR}v_{message.id}.jpg"; cv2.imwrite(tmp, frame)
                    if check_nsfw(tmp): is_bad = True
                    os.remove(tmp)
                cap.release()
            else: is_bad = check_nsfw(file_path)

            if is_bad:
                await message.delete()
                if not is_admin:
                    await message.chat.ban_member(u_id)
                    asyncio.create_task(a1_sonic_cleanup(client, message.chat.id, u_id))
                    await send_logs(client, message, message.from_user, "NSFW Content", "Direct Ban + Sonic Cleanup")
                else: await message.reply("⚠️ Admin Alert! NSFW removed.")
    except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

@app.on_message(filters.group & filters.new_chat_members)
async def join_guard(client, message: Message):
    for u in message.new_chat_members:
        try:
            full_user = await client.get_users(u.id)
            bio, name = (full_user.bio or "").lower(), f"{u.first_name} {u.username or ''}".lower()
            if any(word in name for word in BAD_WORDS) or any(word in bio for word in BAD_WORDS):
                await message.chat.ban_member(u.id); continue
            if "http" in bio: await message.reply(f"⚠️ {u.mention}, bio link allowed nahi hai.")
            photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
            if photos:
                path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
                if check_nsfw(path):
                    await message.chat.ban_member(u.id)
                    asyncio.create_task(a1_sonic_cleanup(client, message.chat.id, u.id))
                if os.path.exists(path): os.remove(path)
        except: pass

@app.on_message(filters.command("gban") & filters.user(SUDO_USERS))
async def gban_cmd(client, message):
    if not message.reply_to_message: return
    uid = message.reply_to_message.from_user.id
    GBAN_LIST.add(uid); await message.chat.ban_member(uid); await message.reply("Global Ban Active! 🚫")

print("🚀 A1 SUPER SONIC (A-Z FEATURES) IS LIVE...")
app.run()
