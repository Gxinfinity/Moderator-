import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

# --- TELEGRAM CONFIGURATION (Fill these 3) ---
API_ID =  27209067            
API_HASH = "0bb2571bd490320a5c9209d4bf07902e"  
BOT_TOKEN = ""  

# --- SIGHTENGINE CONFIGURATION (Updated with your keys) ---
API_USER = ""
API_SECRET = ""

app = Client("nsfw_guard", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def check_nsfw(file_path):
    params = {
        'models': 'nudity-2.0',
        'api_user': API_USER,
        'api_secret': API_SECRET,
    }
    files = {'media': open(file_path, 'rb')}
    try:
        r = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params)
        output = r.json()
        if output.get('status') == 'success':
            # Nudity detect hone par True return karega
            nudity = output['nudity']
            if nudity['sexual_display'] > 0.5 or nudity['erotica'] > 0.5:
                return True
    except Exception as e:
        print(f"Error checking image: {e}")
    return False

# 1. Chat mein Photo/Video scan karna
@app.on_message(filters.group & (filters.photo | filters.video))
async def scan_media(client, message: Message):
    file_path = await message.download()
    if check_nsfw(file_path):
        try:
            await message.chat.ban_member(message.from_user.id)
            await message.delete()
            await message.reply(f"🚫 **User Banned!**\nReason: NSFW Content detected.")
        except Exception as e:
            print(f"Permission Error: {e}")
    if os.path.exists(file_path):
        os.remove(file_path)

# 2. Join hone wale users ki Profile Pic scan karna
@app.on_message(filters.group & filters.new_chat_members)
async def scan_profile(client, message: Message):
    for user in message.new_chat_members:
        photos = [p async for p in client.get_chat_photos(user.id, limit=1)]
        if photos:
            file_path = await client.download_media(photos[0].file_id)
            if check_nsfw(file_path):
                try:
                    await message.chat.ban_member(user.id)
                    await message.reply(f"🚫 **User Banned!**\n{user.mention} has an NSFW profile picture.")
                except Exception as e:
                    print(f"Permission Error: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)

print("Bot is running and protecting your group...")
app.run()
