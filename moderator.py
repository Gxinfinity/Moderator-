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

# Sightengine Keys
API_USER = "1641898842"
API_SECRET = "BrqWQkJqe3Epgse73zWTwrsYbDgpZG6X"

# Bad Words List
BAD_WORDS = ["nude", "sex", "porn", "pussy", "dick", "fucker", "gandu", "bc", "mc", "randi", "loda", "chut"]

app = Client("A1_NSFW_DIRECTOR", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- HELPER FUNCTIONS ---

def check_nsfw(file_path):
    """AI logic to check image/sticker nudity"""
    if not file_path or not os.path.exists(file_path):
        return False
    params = {'models': 'nudity-2.0', 'api_user': API_USER, 'api_secret': API_SECRET}
    with open(file_path, 'rb') as f:
        try:
            r = requests.post('https://api.sightengine.com/1.0/check.json', files={'media': f}, data=params)
            output = r.json()
            if output.get('status') == 'success':
                nudity = output['nudity']
                if nudity['sexual_display'] > 0.5 or nudity['erotica'] > 0.5:
                    return True
        except Exception as e:
            print(f"Sightengine Error: {e}")
    return False

def check_video_nsfw(video_path):
    """Extract frames from video and scan them"""
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # Scan 3 frames (Start, Middle, End)
    for i in [frame_count//4, frame_count//2, (3*frame_count)//4]:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            temp_frame = f"frame_{i}.jpg"
            cv2.imwrite(temp_frame, frame)
            is_bad = check_nsfw(temp_frame)
            os.remove(temp_frame)
            if is_bad:
                cap.release()
                return True
    cap.release()
    return False

# --- HANDLERS ---

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply("🛡️ **A1 Ultra NSFW Director Active!**\nBhai, main group ko har gande media aur text se bachaunga.")

@app.on_message(filters.command("status") & filters.group)
async def status_cmd(client, message):
    await message.reply("✅ **A1 System Online**\nMonitoring: Text, Photos, Stickers, Videos, ZIPs, & DPs.")

# 1. TEXT MODERATION
@app.on_message(filters.group & filters.text & ~filters.service)
async def text_mod(client, message: Message):
    for word in BAD_WORDS:
        if re.search(rf"\b{word}\b", message.text.lower()):
            try:
                await message.chat.ban_member(message.from_user.id)
                await message.delete()
                await message.reply(f"🚫 **User Banned!**\nReason: Prohibited language used.")
            except: pass
            break

# 2. ULTRA MEDIA MODERATION
@app.on_message(filters.group & (filters.photo | filters.video | filters.sticker | filters.document))
async def media_mod(client, message: Message):
    file_path = None
    try:
        # ZIP File Check
        if message.document and message.document.file_name and message.document.file_name.endswith('.zip'):
            file_path = await message.download()
            temp_dir = f"unzip_{message.id}"
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                            if check_nsfw(os.path.join(root, file)):
                                await message.chat.ban_member(message.from_user.id)
                                await message.delete()
                                await message.reply("🚫 **Banned!** NSFW found inside ZIP.")
                                shutil.rmtree(temp_dir)
                                return
            shutil.rmtree(temp_dir)

        # Photo & Sticker Check
        elif message.photo or message.sticker:
            file_path = await message.download()
            if check_nsfw(file_path):
                await message.chat.ban_member(message.from_user.id)
                await message.delete()
                await message.reply(f"🚫 **Banned!** NSFW Media/Sticker detected.")

        # Video Check (MP4, WebM, etc)
        elif message.video or (message.document and message.document.mime_type and message.document.mime_type.startswith('video/')):
            file_path = await message.download()
            if check_video_nsfw(file_path):
                await message.chat.ban_member(message.from_user.id)
                await message.delete()
                await message.reply("🚫 **Banned!** NSFW Video detected.")

    except Exception as e:
        print(f"System Error: {e}")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# 3. NEW MEMBER PROFILE GUARD
@app.on_message(filters.group & filters.new_chat_members)
async def profile_guard(client, message: Message):
    for user in message.new_chat_members:
        photos = [p async for p in client.get_chat_photos(user.id, limit=1)]
        if photos:
            path = await client.download_media(photos[0].file_id)
            if check_nsfw(path):
                try:
                    await message.chat.ban_member(user.id)
                    await message.reply(f"🚫 **Auto-Ban!** {user.mention} has an NSFW profile picture.")
                except: pass
            if os.path.exists(path):
                os.remove(path)

print("🚀 A1 ULTRA ADVANCE BOT STARTED...")
app.run()
