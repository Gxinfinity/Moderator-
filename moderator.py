import os, requests, re, cv2, asyncio, zipfile, shutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "" 
# IDs & Keys
LOG_CHANNEL_ID = "-1003506657299" # Apna Log Channel ID daalein
SUDO_USERS = [7487670897, 8409591285] 
API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut", "sexy"]
DOWNLOAD_DIR = "./downloads/"
LINK_WARNINGS = {} 
SCAN_DATA = {}
GBAN_LIST = set() # Note: Database nahi hai, VPS restart par ye list khali ho jayegi.

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_ULTIMATE_FINAL", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- A1 INTERFACE DESIGNS ---

DM_START_TEXT = """
✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🛡️ **ɪ ᴀᴍ ᴛʜᴇ ᴍᴏsᴛ ᴘᴏᴡᴇʀғᴜʟ ɢᴜᴀʀᴅɪᴀɴ**
Status: `A1 God Mode Active` 🚀
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
🛠️ **Action:** `Full Cleanup + Permanent Ban`
━━━━━━━━━━━━━━━━━━━━
"""

# --- CORE FUNCTIONS ---

async def send_to_logs(client, message, user, reason, action):
    try:
        report = (
            f"🚨 **ᴀ1 sʏsᴛᴇᴍ ᴀᴄᴛɪᴏɴ ʟᴏɢ**\n"
            f"━━━━━━━━━━━━\n"
            f"🛠️ **Action:** `{action}`\n"
            f"👤 **Name:** {user.first_name}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"🔗 **Username:** @{user.username or 'None'}\n"
            f"📝 **Reason:** `{reason}`\n"
            f"📍 **Group:** {message.chat.title}\n"
            f"━━━━━━━━━━━━"
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
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
            res = r.json()
            if res.get('status') == 'success':
                n = res['nudity']
                if n['sexual_display'] > 0.2 or n['erotica'] > 0.2 or n['sexual_activity'] > 0.2: return True
    except: pass
    return False

async def a1_instant_destruction(client, message, reason):
    user = message.from_user
    try:
        await message.delete() 
        await message.chat.ban_member(user.id)
        await client.delete_user_history(message.chat.id, user.id)
        await message.reply_text(BAN_CARD.format(user=user.mention, user_id=user.id, reason=reason))
        await send_to_logs(client, message, user, reason, "Instant Ban + History Clear")
    except: pass

# --- HANDLERS ---

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    if message.chat.type == message.chat.type.PRIVATE:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")],
            [InlineKeyboardButton("📢 Updates", url="https://t.me/Cyber_Github"), InlineKeyboardButton("🛠️ Support", url="https://t.me/Cyber_Github")]
        ])
        await message.reply_text(DM_START_TEXT, reply_markup=buttons)

@app.on_message(filters.group & ~filters.service)
async def a1_guardian(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id
    
    if u_id in GBAN_LIST:
        await message.chat.ban_member(u_id)
        await message.delete()
        return

    is_admin = False
    try:
        member = await client.get_chat_member(message.chat.id, u_id)
        if member.status in [member.status.ADMINISTRATOR, member.status.OWNER]: is_admin = True
    except: pass

    text = (message.text or message.caption or "").lower()

    # 1. LINK & FORWARD PROTECTION
    if "t.me/" in text or "http" in text or message.forward_from or message.forward_from_chat:
        if is_admin: return
        await message.delete()
        LINK_WARNINGS[u_id] = LINK_WARNINGS.get(u_id, 0) + 1
        if LINK_WARNINGS[u_id] >= 3:
            await a1_instant_destruction(client, message, "Spamming Links (3 Warnings)")
            del LINK_WARNINGS[u_id]
        else:
            await message.reply(f"⚠️ {message.from_user.mention}, **Warning {LINK_WARNINGS[u_id]}/3!** Links delete kar diye gaye hain.")
        return

    # 2. MEDIA SCAN (Photos, Stickers, Videos, Documents/ZIP)
    file_path = None
    try:
        if message.photo or message.sticker or message.video or (message.document and message.document.file_name and message.document.file_name.endswith('.zip')):
            if message.sticker and message.sticker.is_animated:
                if not is_admin: await a1_instant_destruction(client, message, "Animated Sticker")
                else: await message.delete()
                return

            file_path = await message.download(file_name=DOWNLOAD_DIR)
            is_bad = False
            
            if message.document and message.document.file_name and message.document.file_name.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    z_tmp = f"{DOWNLOAD_DIR}unzip_{message.id}"
                    zip_ref.extractall(z_tmp)
                    for r, _, files in os.walk(z_tmp):
                        for f in files:
                            if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp')):
                                if check_nsfw(os.path.join(r, f)): is_bad = True; break
                    shutil.rmtree(z_tmp)
            
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
                if not is_admin: await a1_instant_destruction(client, message, "NSFW Content Detected")
                else: await message.reply("⚠️ **Admin Alert!** NSFW media removed instantly.")
    except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

@app.on_message(filters.group & filters.new_chat_members)
async def join_guard(client, message: Message):
    for u in message.new_chat_members:
        if u.id in GBAN_LIST:
            await message.chat.ban_member(u.id); continue
            
        u_info = f"{u.first_name} {u.username or ''}".lower()
        if any(word in u_info for word in BAD_WORDS):
            await message.chat.ban_member(u.id); continue
        
        photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
            if check_nsfw(path):
                await message.chat.ban_member(u.id)
                await client.delete_user_history(message.chat.id, u.id)
                await send_to_logs(client, message, u, "NSFW Profile Pic", "Join Ban + Cleanup")
            if os.path.exists(path): os.remove(path)

@app.on_message(filters.command("scan") & filters.group)
async def scan_command(client, message):
    user_status = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user_status.status not in [user_status.status.ADMINISTRATOR, user_status.status.OWNER]:
        return await message.reply("❌ **Sirf Admins hi scan kar sakte hain!**")

    status_msg = await message.reply("🔍 **Scanning members...**")
    bad_users = []
    async for member in client.get_chat_members(message.chat.id):
        if member.user.is_bot: continue
        if any(word in f"{member.user.first_name} {member.user.username or ''}".lower() for word in BAD_WORDS):
            bad_users.append(member.user.id)
    
    if bad_users:
        SCAN_DATA[message.chat.id] = bad_users
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Ban All", callback_data="ban_all")]])
        await status_msg.edit(f"🚨 Found `{len(bad_users)}` suspicious members.", reply_markup=buttons)
    else:
        await status_msg.edit("✅ Group is clean.")

@app.on_message(filters.command("check") & filters.group)
async def health_check(client, message):
    me = await client.get_chat_member(message.chat.id, "me")
    await message.reply(f"🚫 Ban: {'✅' if me.privileges.can_restrict_members else '❌'}\n🗑️ Delete: {'✅' if me.privileges.can_delete_messages else '❌'}\n📊 Supergroup: {'✅' if message.chat.type.name == 'SUPERGROUP' else '❌'}")

@app.on_message(filters.command("gban") & filters.user(SUDO_USERS))
async def gban_user(client, message):
    if not message.reply_to_message: return await message.reply("Reply to a user to GBAN!")
    target_id = message.reply_to_message.from_user.id
    GBAN_LIST.add(target_id)
    await message.chat.ban_member(target_id)
    await message.reply(f"🚫 **GBAN!** User `{target_id}` globally banned.")

@app.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    if query.data == "ban_all" and query.message.chat.id in SCAN_DATA:
        for u_id in SCAN_DATA[query.message.chat.id]:
            try: await query.message.chat.ban_member(u_id)
            except: pass
        await query.message.edit("✅ All suspicious members banned.")

print("🚀 A1 GOD MODE IS LIVE...")
app.run()
