import os, requests, re, cv2, asyncio, zipfile, shutil
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "" 

# Sahii ID daalein (Example: -100xxxxxxxxxx)
LOG_CHANNEL_ID = -1003506657299 

API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut", "sexy"]
DOWNLOAD_DIR = "./downloads/"
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

app = Client("A1_ULTRA_V9", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- CORE FUNCTIONS ---

async def send_to_logs(client, message, user, reason, action):
    """Log channel mein report bhejne ka fixed logic"""
    try:
        report = (
            f"🚨 **ᴀ1 sʏsᴛᴇᴍ ᴀᴄᴛɪᴏɴ ʟᴏɢ**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🛠️ **Action:** `{action}`\n"
            f"👤 **Name:** {user.first_name}\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"🔗 **Username:** @{user.username or 'None'}\n"
            f"📝 **Reason:** `{reason}`\n"
            f"📍 **Group:** {message.chat.title}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await client.send_message(LOG_CHANNEL_ID, report)
    except Exception as e:
        # Isse aapko terminal mein dikhega ki log kyun nahi ja raha
        print(f"❌ Log Channel Error: {e}. Check if Bot is Admin in Channel {LOG_CHANNEL_ID}")

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
                if n['sexual_display'] > 0.2 or n['erotica'] > 0.2: return True
    except: pass
    return False

async def a1_instant_destruction(client, message, reason):
    user = message.from_user
    chat_id = message.chat.id
    try:
        # 1. Sabse pehle user ko BAN karo (Taaki wo aur na bhej sake)
        await message.chat.ban_member(user.id)
        
        # 2. Triggering message DELETE karo
        await message.delete()
        
        # 3. HISTORY WIPE (Sirf Supergroup mein kaam karega)
        # Note: Bot ko 'Delete Messages' permission honi chahiye
        try:
            await client.delete_user_history(chat_id, user.id)
        except Exception as e:
            print(f"⚠️ History Cleanup failed: {e}. Ensure Group is a Supergroup.")

        # 4. Logs bhejo
        await send_to_logs(client, message, user, reason, "Instant Ban + History Wipe")
        
        # 5. Ban Confirmation
        await message.reply_text(f"🚫 **Banned!** {user.mention} has been removed and history cleared.")
        
    except Exception as e:
        print(f"❌ Destruction Process Error: {e}")

# --- HANDLERS ---

@app.on_message(filters.group & ~filters.service)
async def a1_guard(client, message: Message):
    if not message.from_user: return
    u_id = message.from_user.id

    is_admin = False
    try:
        member = await client.get_chat_member(message.chat.id, u_id)
        if member.status in ["administrator", "creator"]: is_admin = True
    except: pass

    # Media Scanning
    file_path = None
    try:
        if message.photo or message.sticker or message.video:
            file_path = await message.download(file_name=DOWNLOAD_DIR)
            if check_nsfw(file_path):
                if not is_admin:
                    await a1_instant_destruction(client, message, "NSFW Media Violation")
                else:
                    await message.delete()
                    await send_to_logs(client, message, message.from_user, "NSFW (Admin)", "Admin Message Deleted")
    except: pass
    finally:
        if file_path and os.path.exists(file_path): os.remove(file_path)

# Scan command to check bot health
@app.on_message(filters.command("check") & filters.group)
async def check_rights(client, message):
    me = await client.get_chat_member(message.chat.id, "me")
    report = (
        f"🛠️ **ᴀ1 ʙᴏᴛ sᴛᴀᴛᴜs ᴄʜᴇᴄᴋ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🚫 **Ban Users:** {'✅' if me.privileges.can_restrict_members else '❌'}\n"
        f"🗑️ **Delete Messages:** {'✅' if me.privileges.can_delete_messages else '❌'}\n"
        f"📊 **Supergroup:** {'✅' if message.chat.type.name == 'SUPERGROUP' else '❌'}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await message.reply(report)

print("🚀 A1 V9 (LOG & HISTORY FIX) IS LIVE...")
app.run()
