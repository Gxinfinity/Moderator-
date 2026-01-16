import os, requests, re, cv2, asyncio, zipfile, shutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = ""

# Sightengine Keys
API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut", "sexy"]
DOWNLOAD_DIR = "./downloads/"
SCAN_DATA = {} 
LINK_WARNINGS = {}

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_ULTRA_PRO_MAX", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- A1 UI INTERFACE DESIGNS ---

DM_START_TEXT = """
✨ **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🛡️ **ɪ ᴀᴍ ᴛʜᴇ ᴍᴏsᴛ ᴘᴏᴡᴇʀғᴜʟ ɢᴜᴀʀᴅɪᴀɴ**

I protect your groups from:
• 🔞 **NSFW Media & Stickers**
• 🤬 **Bad Words & Abuses**
• 👤 **NSFW Profile Pictures**
• 🔗 **Spam Links & Advertisements**

**Status:** `A1 - Pro Max Active` 🚀
━━━━━━━━━━━━━━━━━━━━
"""

BAN_CARD = """
✨ **ᴀ1 ɴsғᴡ ᴅɪʀᴇᴄᴛᴏʀ** ✨
━━━━━━━━━━━━━━━━━━━━
🚫 **ᴜsᴇʀ ʙᴀɴɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ**
━━━━━━━━━━━━━━━━━━━━
👤 **User:** {user}
🆔 **ID:** `{user_id}`
🔗 **Link:** [Profile Link](tg://user?id={user_id})
📝 **Reason:** `{reason}`
🛠️ **Action:** `Direct Ban + History Cleared`
━━━━━━━━━━━━━━━━━━━━
"""

# --- CORE FUNCTIONS ---

def check_nsfw(file_path):
    if not file_path or not os.path.exists(file_path): return False
    if file_path.endswith((".webp", ".png")):
        try:
            img = Image.open(file_path).convert("RGB")
            temp_path = file_path + ".jpg"
            img.save(temp_path, "JPEG")
            file_path = temp_path
        except: pass
    
    params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
    try:
        with open(file_path, 'rb') as f:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
            res = r.json()
            if res.get('status') == 'success':
                n = res['nudity']
                # Strict 0.3 threshold for direct ban
                if n['sexual_display'] > 0.3 or n['erotica'] > 0.3 or n['sexual_activity'] > 0.3: return True
    except: pass
    return False

async def a1_direct_ban(client, message, reason):
    user_id = message.from_user.id
    try:
        await message.delete() 
        await client.delete_user_history(message.chat.id, user_id) # Clears all user messages
        await message.chat.ban_member(user_id) 
        await message.reply_text(BAN_CARD.format(user=message.from_user.mention, user_id=user_id, reason=reason))
    except: pass

# --- HANDLERS ---

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    if message.chat.type == message.chat.type.PRIVATE:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me to Your Group", url=f"https://t.me/{(await client.get_me()).username}?startgroup=true")],
            [InlineKeyboardButton("📢 Updates", url="https://t.me/Cyber_Github"), InlineKeyboardButton("🛠️ Support", url="https://t.me/Cyber_Github")]
        ])
        await message.reply_text(DM_START_TEXT, reply_markup=buttons)
    else:
        await message.reply_text("🛡️ **A1 Pro Max Protection is Active!**")

@app.on_message(filters.command("scan") & filters.group)
async def scan_command(client, message):
    user_status = await client.get_chat_member(message.chat.id, message.from_user.id)
    if user_status.status not in ["administrator", "creator"]:
        return await message.reply("❌ **Sirf Admins hi scan kar sakte hain!**")

    status_msg = await message.reply("🔍 **A1 System: Scanning all members for NSFW...**")
    bad_users = []
    
    async for member in client.get_chat_members(message.chat.id):
        if member.user.is_bot: continue
        u = member.user
        is_bad = False
        u_info = f"{u.first_name} {u.last_name or ''} {u.username or ''}".lower()
        if any(word in u_info for word in BAD_WORDS): is_bad = True
        
        if not is_bad:
            photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
            if photos:
                path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
                if check_nsfw(path): is_bad = True
                if os.path.exists(path): os.remove(path)
        if is_bad: bad_users.append(u.id)

    if bad_users:
        SCAN_DATA[message.chat.id] = bad_users
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚠️ Warn All", callback_data="warn_all"), InlineKeyboardButton("🚫 Ban All", callback_data="ban_all")],
            [InlineKeyboardButton("🗑️ Close", callback_data="close_scan")]
        ])
        await status_msg.edit(f"🚨 **A1 Scan Report**\nFound `{len(bad_users)}` suspicious members.", reply_markup=buttons)
    else:
        await status_msg.edit("✅ **Group is Clean!** No NSFW profiles found.")

@app.on_message(filters.group & ~filters.service)
async def a1_guardian(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id
    
    # Check Admin Status
    is_admin = False
    try:
        member = await client.get_chat_member(message.chat.id, u_id)
        if member.status in ["administrator", "creator"]: is_admin = True
    except: pass

    # 1. LINK WARNINGS
    text = (message.text or message.caption or "").lower()
    if "t.me/" in text or "http" in text:
        if is_admin: 
            await message.delete()
            return
        LINK_WARNINGS[u_id] = LINK_WARNINGS.get(u_id, 0) + 1
        if LINK_WARNINGS[u_id] >= 3:
            await a1_direct_ban(client, message, "Spamming Links (3 Warnings)")
        else:
            await message.reply(f"⚠️ {message.from_user.mention}, **Warning {LINK_WARNINGS[u_id]}/3!** Links delete kar diye gaye hain.")
            await message.delete()
        return

    # 2. MEDIA SCAN (Image/Video/Sticker/Zip)
    file_path = None
    try:
        if message.photo or message.sticker or message.video or (message.document and message.document.file_name.endswith('.zip')):
            file_path = await message.download(file_name=DOWNLOAD_DIR)
            is_bad = False
            
            # ZIP Scan
            if message.document and message.document.file_name.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    z_tmp = f"{DOWNLOAD_DIR}unzip_{message.id}"
                    zip_ref.extractall(z_tmp)
                    for r, _, files in os.walk(z_tmp):
                        for f in files:
                            if f.lower().endswith(('.jpg', '.png', '.webp')):
                                if check_nsfw(os.path.join(r, f)): is_bad = True; break
                    shutil.rmtree(z_tmp)
            
            # Video Scan
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
                if not is_admin: await a1_direct_ban(client, message, "NSFW Content")
                else: await message.reply("⚠️ **Admin Alert!** NSFW media detect hua aur delete kiya gaya.")
    except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

@app.on_message(filters.group & filters.new_chat_members)
async def join_guard(client, message: Message):
    for u in message.new_chat_members:
        # Profile, Name & Username Scan
        u_info = f"{u.first_name} {u.last_name or ''} {u.username or ''}".lower()
        if any(word in u_info for word in BAD_WORDS):
            await message.chat.ban_member(u.id)
            await message.reply(f"🚫 **Direct Ban!** {u.mention} ka naam ganda hai.")
            continue
        
        photos = [p async for p in client.get_chat_photos(u.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id, file_name=DOWNLOAD_DIR)
            if check_nsfw(path):
                await message.chat.ban_member(u.id)
                await client.delete_user_history(message.chat.id, u.id)
                await message.reply(f"🚫 **Auto-Ban!** {u.mention} has NSFW DP. History cleared.")
            if os.path.exists(path): os.remove(path)

@app.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    chat_id = query.message.chat.id
    if query.data == "ban_all" and chat_id in SCAN_DATA:
        await query.answer("Cleaning Group...")
        for u_id in SCAN_DATA[chat_id]:
            try: await client.ban_chat_member(chat_id, u_id); await client.delete_user_history(chat_id, u_id)
            except: pass
        await query.edit_message_text("✅ **Group Cleaned!**")
    elif query.data == "close_scan": await query.message.delete()

print("🚀 A1 ULTRA PRO MAX MERGER IS LIVE...")
app.run()
