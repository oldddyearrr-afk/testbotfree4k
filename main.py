import os, time, subprocess, threading, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- الإعدادات ---
TOKEN = '8516406148:AAHy6sSBYIxLqBI6BasQLjvDCjx9aspkNB8'
ID = 5747051433
URL = 'https://rmtv.akamaized.net/hls/live/2043153/rmtv-es-web/bitrate_3.m3u8'

bot = telebot.TeleBot(TOKEN)
is_running = False
ffmpeg_process = None
target_ids = {ID}

# --- خادم ويب خفيف جداً لـ Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Lite Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), SimpleHandler)
    httpd.serve_forever()

# --- خيط الإرسال (اقتصادي جداً في الرام) ---
def snd_worker():
    while True:
        if is_running:
            files = sorted([f for f in os.listdir('.') if f.startswith('seg_') and f.endswith('.mp4')])
            if len(files) > 1:
                f_name = files[0]
                try:
                    # الإرسال لجميع المستلمين بدون تحميل الملف كاملاً في الرام
                    for tid in list(target_ids):
                        with open(f_name, 'rb') as v:
                            bot.send_video(tid, v, timeout=60)
                    os.remove(f_name)
                except: pass
        time.sleep(1)

# --- الأوامر ---
@bot.message_handler(commands=['setlive'])
def set_live(m):
    if m.chat.id == ID:
        msg = bot.reply_to(m, "🔗 أرسل رابط البث الجديد:")
        bot.register_next_step_handler(msg, update_url)

def update_url(m):
    global URL
    if m.text.startswith('http'):
        URL = m.text
        bot.reply_to(m, f"✅ تم التحديث بنجاح.")

@bot.message_handler(commands=['multilive'])
def add_id(m):
    if m.chat.id == ID:
        msg = bot.reply_to(m, "👤 أرسل الأيدي الجديد:")
        bot.register_next_step_handler(msg, save_id)

def save_id(m):
    try:
        new_id = int(m.text)
        target_ids.add(new_id)
        bot.reply_to(m, f"✅ تم إضافة {new_id}")
    except: bot.reply_to(m, "❌ أيدي غير صحيح")

@bot.message_handler(commands=['listlive'])
def list_live(m):
    if m.chat.id == ID:
        bot.reply_to(m, f"📋 الرابط: {URL}\n👥 المستلمون: {len(target_ids)}")

@bot.message_handler(commands=['startlive'])
def start(m):
    global is_running
    if m.chat.id == ID and not is_running:
        is_running = True
        bot.reply_to(m, "🎬 بدأ التسجيل الخفيف...")
        threading.Thread(target=rec_worker, daemon=True).start()

@bot.message_handler(commands=['stoplive'])
def stop(m):
    global is_running, ffmpeg_process
    if m.chat.id == ID:
        is_running = False
        if ffmpeg_process: ffmpeg_process.terminate()
        # مسح البقايا
        for f in os.listdir('.'):
            if f.startswith('seg_'): os.remove(f)
        bot.reply_to(m, "🛑 توقف وتنظيف.")

def rec_worker():
    global ffmpeg_process
    # أوامر FFmpeg محسنة لتقليل استهلاك الذاكرة وسرعة الاتصال
    cmd = [
        'ffmpeg', '-reconnect', '1', '-reconnect_streamed', '1', 
        '-nobuffer', '-flags', 'low_delay', 
        '-i', URL, '-c', 'copy', '-f', 'segment', 
        '-segment_time', '21', '-reset_timestamps', '1', 'seg_%03d.mp4'
    ]
    while is_running:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ffmpeg_process.wait()
        time.sleep(2)

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=snd_worker, daemon=True).start()
    bot.polling(non_stop=True)
