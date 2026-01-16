import os
import requests
import re
from pyrogram import Client, filters
from pyrogram.types import Message, ChatPermissions

# --- CONFIGURATION ---
API_ID = 27209067
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"
BOT_TOKEN = "" 

# Sightengine Keys (Aapki keys use ki hain)
API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

# --- BAD WORDS LIST (Gande Words) ---
# Aap yahan aur bhi words add kar sakte hain
BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi"]

app = Client("advanced_nsfw_guard", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# AI Media Check Function
def check_nsfw(file_path):
    params = {
        'models': 'nudity-2.0,wad', # nudity aur weapons/alcohol/drugs
        'api_user': API_USER,
        'api_secret': API_SECRET,
    }
    files = {'media': open(file_path, 'rb')}
    try:
        r = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params)
        output = r.json()
        if output.get('status') == 'success':
            nudity = output['nudity']
            # Detection threshold: 50% probability
            if nudity['sexual_display'] > 0.5 or nudity['erotica'] > 0.5:
                return True
    except Exception as e:
        print(f"API Error: {e}")
    return False

# 1. COMMANDS
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("🛡️ **Advanced NSFW Guard Active!**\nBhai, main group ko gande content se bachaunga. Bas mujhe Admin bana do.")

@app.on_message(filters.command("status") & filters.group)
async def status_cmd(client, message):
    await message.reply("✅ **System Online**\nScanning: Photos, Videos, Stickers & Bad Words.")

# 2. TEXT MODERATION (Gande Words Detector)
@app.on_message(filters.group & filters.text & ~filters.service)
async def text_mod(client, message: Message):
    for word in BAD_WORDS:
        if re.search(rf"\b{word}\b", message.text.lower()):
            try:
                await message.chat.ban_member(message.from_user.id)
                await message.delete()
                await message.reply(f"🚫 **User Banned!**\nReason: Using prohibited words.")
            except Exception as e:
                print(f"Ban Error: {e}")
            break

# 3. MEDIA MODERATION (Photo, Video, Sticker)
@app.on_message(filters.group & (filters.photo | filters.video | filters.sticker))
async def media_mod(client, message: Message):
    # Download file for scanning
    msg = await message.reply("🔍 `Scanning Media...`", quote=True)
    file_path = await message.download()
    
    if check_nsfw(file_path):
        try:
            await message.chat.ban_member(message.from_user.id)
            await message.delete()
            await msg.edit(f"🚫 **NSFW Detected!**\nUser {message.from_user.mention} has been banned.")
        except Exception as e:
            await msg.edit("❌ I need Ban permissions!")
    else:
        await msg.delete() # Agar safe hai to message delete kar do

    if os.path.exists(file_path):
        os.remove(file_path)

# 4. NEW MEMBER PROFILE SCAN
@app.on_message(filters.group & filters.new_chat_members)
async def profile_mod(client, message: Message):
    for user in message.new_chat_members:
        photos = [p async for p in client.get_chat_photos(user.id, limit=1)]
        if photos:
            file_path = await client.download_media(photos[0].file_id)
            if check_nsfw(file_path):
                try:
                    await message.chat.ban_member(user.id)
                    await message.reply(f"🚫 **Auto-Ban!**\n{user.mention} has an NSFW profile picture.")
                except Exception:
                    pass
            if os.path.exists(file_path):
                os.remove(file_path)

print("--- ADVANCED NSFW BOT STARTED ---")
app.run()
