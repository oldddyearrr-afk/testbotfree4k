import os, time, subprocess, threading, telebot
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- الإعدادات الأساسية ---
TOKEN = '7957457845:AAGTe2_4avne8h5MxZCnEY8lCzACOTBKKxo'
ID = 5747051433
URL = 'https://rmtv.akamaized.net/hls/live/2043153/rmtv-es-web/bitrate_3.m3u8'

bot = telebot.TeleBot(TOKEN)
is_running = False
ffmpeg_process = None
target_ids = {ID}

# --- خادم ويب لفتح البورت في Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Lite 1080p Active")

def run_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('0.0.0.0', port), SimpleHandler)
    httpd.serve_forever()

# --- خيط الإرسال الاقتصادي (قراءة مباشرة من القرص) ---
def snd_worker():
    while True:
        if is_running:
            # جلب الملفات المسجلة وترتيبها
            files = sorted([f for f in os.listdir('.') if f.startswith('seg_') and f.endswith('.mp4')])
            if len(files) > 1:
                f_name = files[0]
                try:
                    # الإرسال لجميع الأيديهات المضافة
                    for tid in list(target_ids):
                        with open(f_name, 'rb') as v:
                            bot.send_video(tid, v, timeout=90)
                    os.remove(f_name) # حذف الملف فوراً بعد الإرسال لتوفير المساحة
                except Exception as e:
                    print(f"Send Error: {e}")
        time.sleep(1)

# --- أوامر التحكم (الأونر فقط) ---

@bot.message_handler(commands=['setlive'])
def set_live(m):
    if m.chat.id == ID:
        msg = bot.reply_to(m, "🔗 أرسل رابط البث الجديد (m3u8, mpd, ts):")
        bot.register_next_step_handler(msg, update_url)

def update_url(m):
    global URL
    if m.text.startswith('http'):
        URL = m.text
        bot.reply_to(m, f"✅ تم تحديث الرابط بنجاح.")
    else:
        bot.reply_to(m, "❌ رابط غير صحيح.")

@bot.message_handler(commands=['multilive'])
def add_id(m):
    if m.chat.id == ID:
        msg = bot.reply_to(m, "👤 أرسل الأيدي الجديد لإضافته للقائمة:")
        bot.register_next_step_handler(msg, save_id)

def save_id(m):
    try:
        new_id = int(m.text)
        target_ids.add(new_id)
        bot.reply_to(m, f"✅ تم إضافة الأيدي {new_id} بنجاح.")
    except:
        bot.reply_to(m, "❌ يرجى إرسال أيدي رقمي صحيح.")

@bot.message_handler(commands=['listlive'])
def list_live(m):
    if m.chat.id == ID:
        ids_str = "\n".join([str(i) for i in target_ids])
        bot.reply_to(m, f"📋 الرابط الحالي:\n{URL}\n\n👥 المستلمون:\n{ids_str}")

@bot.message_handler(commands=['startlive'])
def start(m):
    global is_running
    if m.chat.id == ID and not is_running:
        is_running = True
        bot.reply_to(m, "🎬 بدأ تسجيل البث بدقة 1080p...")
        threading.Thread(target=rec_worker, daemon=True).start()

@bot.message_handler(commands=['stoplive'])
def stop(m):
    global is_running, ffmpeg_process
    if m.chat.id == ID:
        is_running = False
        if ffmpeg_process:
            ffmpeg_process.terminate()
        # تنظيف مساحة القرص من جميع المقاطع
        for f in os.listdir('.'):
            if f.startswith('seg_'):
                try: os.remove(f)
                except: pass
        bot.reply_to(m, "🛑 تم إيقاف التسجيل وتنظيف المساحة.")

# --- محرك التسجيل المحسن لرام 512MB ودقة 1080p ---
def rec_worker():
    global ffmpeg_process, is_running
    # إعدادات FFmpeg لتقليل استهلاك الذاكرة وحفظ الجودة الأصلية
    cmd = [
        'ffmpeg',
        '-reconnect', '1', '-reconnect_streamed', '1', '-reconnect_delay_max', '5',
        '-fflags', 'nobuffer+genpts', 
        '-flags', 'low_delay',
        '-i', URL,
        '-c', 'copy', # نسخ بدون تحويل (خفيف جداً على المعالج والرام)
        '-f', 'segment',
        '-segment_time', '21',
        '-reset_timestamps', '1',
        '-segment_format_options', 'movflags=+faststart',
        'seg_%03d.mp4'
    ]
    
    while is_running:
        try:
            ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ffmpeg_process.wait()
            if not is_running: break
            time.sleep(5)
        except:
            time.sleep(5)

if __name__ == "__main__":
    # تشغيل خادم الويب في خيط منفصل
    threading.Thread(target=run_server, daemon=True).start()
    # تشغيل خيط الإرسال في خيط منفصل
    threading.Thread(target=snd_worker, daemon=True).start()
    print("🤖 Bot is Online...")
    bot.polling(non_stop=True)
