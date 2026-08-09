import os
import asyncio
from threading import Thread
from flask import Flask
from pyrogram import Client, filters, types
import yt_dlp

# حل اصولی مشکل Event Loop در پایتون
try:
    asyncio.get_running_loop()
except RuntimeError:
    try:
        loop = asyncio.get_event_loop_policy().get_event_loop()
        if loop.is_closed():
            raise RuntimeError()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

# === بخش وب‌سرور (برای روشن موندن تو رندر) ===
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot is running perfectly, Wahid!"

def run_web():
    port = int(os.environ.get("PORT", 8000))
    app_web.run(host="0.0.0.0", port=port)

# === اطلاعات شخصی ربات تو ===
API_ID = 36362511
API_HASH = "afd96a31d309f97fd72a4a6faaf91fc7"
BOT_TOKEN = "8722548773:AAEC1iX3kGW4wP-jKfWysqFAO4WFz3q-nDE"

# === بخش ربات تلگرام ===
app_bot = Client(
    "wahid_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# دیتای موقت برای نگه داشتن لینک کاربر
user_states = {}

@app_bot.on_message(filters.command("start"))
def start(client, message):
    message.reply_text("سلام رفیق! لینک ویدیو رو بفرست تا بپرسم ویدیوش رو می‌خوای یا آهنگ روش رو.")

@app_bot.on_message(filters.text & ~filters.command("start"))
def ask_choice(client, message):
    url = message.text.strip()
    
    if not url.startswith("http"):
        message.reply_text("❗ رفیق، لطفاً یه لینک معتبر بفرست.")
        return

    # ذخیره لینک کاربر
    user_states[message.chat.id] = url
    
    # ساخت دکمه‌های انتخاب
    keyboard = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("🎬 دانلود ویدیو", callback_data="download_video"),
            types.InlineKeyboardButton("🎵 آهنگ این ویدیو", callback_data="download_audio")
        ]
    ])
    
    message.reply_text("رفیق، از این لینک چی می‌خوای؟", reply_markup=keyboard)

@app_bot.on_callback_query()
def handle_choice(client, callback_query):
    chat_id = callback_query.message.chat.id
    url = user_states.get(chat_id)
    
    if not url:
        callback_query.answer("لینک منقضی شده رفیق، دوباره بفرستش.")
        return

    callback_query.answer("در حال پردازش...")
    callback_query.message.edit_text("⏳ در حال استخراج و دانلود... صبور باش.")
    
    mode = callback_query.data
    output_dir = "downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # تنظیمات هوشمند yt_dlp بدون نیاز به ffmpeg
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }

    if mode == "download_audio":
        ydl_opts['format'] = 'bestaudio'
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            callback_query.message.edit_text("✅ دانلود انجام شد. در حال ارسال به تلگرام...")
            
            if mode == "download_audio":
                client.send_audio(
                    chat_id=chat_id,
                    audio=file_path,
                    caption="🎵 بفرما رفیق، اینم آهنگِ روی این ویدیو!"
                )
            else:
                client.send_document(
                    chat_id=chat_id,
                    document=file_path,
                    caption="🎬 بفرما رفیق، اینم خود ویدیو!"
                )
            
            os.remove(file_path)
            callback_query.message.delete()
            
            if chat_id in user_states:
                del user_states[chat_id]
            
    except Exception as e:
        callback_query.message.edit_text(f"❌ خطا هنگام پردازش:\n{str(e)[:120]}")

if __name__ == "__main__":
    print("🌐 در حال روشن کردن وب‌سرور...")
    Thread(target=run_web).start()
    
    print("🤖 ربات با موفقیت استارت خورد...")
    app_bot.run()
