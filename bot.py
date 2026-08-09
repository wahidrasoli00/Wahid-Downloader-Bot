import os
import asyncio
from threading import Thread
from flask import Flask
from pyrogram import Client, filters
import yt_dlp

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

@app_bot.on_message(filters.command("start"))
def start(client, message):
    message.reply_text("سلام رفیق! لینک ویدیو یا پادکست رو بفرست تا بدون افت کیفیت دانلودش کنم.")

@app_bot.on_message(filters.text & ~filters.command("start"))
def download_and_send(client, message):
    url = message.text.strip()
    
    if not url.startswith("http"):
        message.reply_text("❗ رفیق، لطفاً یه لینک معتبر بفرست.")
        return

    msg = message.reply_text("⏳ در حال پردازش و دانلود... صبور باش رفیق.")
    
    output_dir = "downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'format': 'best', 
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            msg.edit_text("✅ دانلود انجام شد. در حال ارسال به تلگرام...")
            
            client.send_document(
                chat_id=message.chat.id,
                document=file_path,
                caption="🎬 بفرما رفیق!"
            )
            
            os.remove(file_path)
            msg.delete()
            
    except Exception as e:
        msg.edit_text(f"❌ خطا هنگام پردازش:\n{str(e)[:100]}")

if __name__ == "__main__":
    print("🌐 در حال روشن کردن وب‌سرور...")
    Thread(target=run_web).start()
    
    print("🤖 ربات با موفقیت استارت خورد...")
    
    # حل مشکل Event Loop در پایتون‌های جدید
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    app_bot.run()
