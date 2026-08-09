import os
import asyncio
from threading import Thread
import urllib.parse
import urllib.request
import re
from flask import Flask
from pyrogram import Client, filters
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

@app_bot.on_message(filters.command("start"))
def start(client, message):
    message.reply_text("سلام رفیق! لینک اینستاگرام یا پادکست کست‌باکس رو بفرست تا برات دانلود کنم.")

@app_bot.on_message(filters.text & ~filters.command("start"))
def download_and_send(client, message):
    raw_url = message.text.strip()
    
    if not raw_url.startswith("http"):
        message.reply_text("❗ رفیق، لطفاً یه لینک معتبر بفرست.")
        return

    msg = message.reply_text("⏳ در حال پردازش و استخراج لینک... صبور باش رفیق.")
    
    output_dir = "downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # === بخش ویژه و ایزوله برای کست‌باکس ===
    if "castbox.fm" in raw_url:
        try:
            target_url = raw_url
            if "d.castbox.fm" in raw_url:
                parsed = urllib.parse.urlparse(raw_url)
                qs = urllib.parse.parse_qs(parsed.query)
                if 'link' in qs:
                    target_url = urllib.parse.unquote(qs['link'][0])
            
            req = urllib.request.Request(
                target_url, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
            
            audio_url = None
            match = re.search(r'(https?://[^\s<>"]+?\.mp3[^\s<>"]*)', html_content)
            if match:
                audio_url = match.group(1).replace('\\u0026', '&')
            else:
                match2 = re.search(r'"(?:enurl|audio|media_url|url)"\s*:\s*"([^"]+)"', html_content)
                if match2:
                    audio_url = match2.group(1).replace('\\u0026', '&').replace('\\/', '/')
            
            if audio_url:
                file_path = os.path.join(output_dir, "podcast.mp3")
                msg.edit_text("⏳ در حال دانلود فایل پادکست...")
                
                req_audio = urllib.request.Request(audio_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req_audio) as resp, open(file_path, 'wb') as f:
                    f.write(resp.read())
                
                msg.edit_text("✅ دانلود انجام شد. در حال ارسال به تلگرام...")
                client.send_audio(
                    chat_id=message.chat.id,
                    audio=file_path,
                    caption="🎧 پادکست کست‌باکس آماده‌ست رفیق!"
                )
                os.remove(file_path)
                msg.delete()
                return
            else:
                msg.edit_text("❌ رفیق، لینک فایل صوتی این اپیزود در کست‌باکس محافظت شده است و امکان دانلود مستقیمش با این متد نیست.")
                return
        except Exception as e:
            msg.edit_text(f"❌ خطا در پردازش کست‌باکس:\n{str(e)[:120]}")
            return

    # === بخش دانلود ویدیو و سایر لینک‌ها با yt_dlp ===
    ydl_opts = {
        'format': 'best[ext=mp4]/best', 
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(raw_url, download=True)
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
        msg.edit_text(f"❌ خطا هنگام پردازش:\n{str(e)[:120]}")

if __name__ == "__main__":
    print("🌐 در حال روشن کردن وب‌سرور...")
    Thread(target=run_web).start()
    
    print("🤖 ربات با موفقیت استارت خورد...")
    app_bot.run()
