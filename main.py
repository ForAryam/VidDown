from flask import Flask
import threading
import telebot
from yt_dlp import YoutubeDL
from pytube import YouTube
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import sqlite3
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد Flask
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# إعداد البوت
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ التوكن غير موجود في ملف .env. يرجى التحقق!")

bot = telebot.TeleBot(API_TOKEN)

channel_url = "https://t.me/Nillionaire_ar"
bot_owner_id = 5592854910  # استبدل برقم تعريفك

# إنشاء قاعدة بيانات
def init_db():
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_stats (
            user_id INTEGER PRIMARY KEY,
            downloads INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# تخزين معرف المستخدم في قاعدة البيانات
def add_user_to_db(user_id):
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM usage_stats WHERE user_id = ?', (user_id,))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO usage_stats (user_id, downloads) VALUES (?, ?)', (user_id, 0))
    conn.commit()
    conn.close()

# تحديث عدد التنزيلات
def update_downloads(user_id):
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE usage_stats SET downloads = downloads + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# إحصائيات شاملة
def get_stats():
    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(user_id), SUM(downloads) FROM usage_stats')
    stats = cursor.fetchone()
    conn.close()
    return stats

# التحقق من الاشتراك
def is_subscribed(user_id):
    if user_id == bot_owner_id:
        return True
    try:
        status = bot.get_chat_member(chat_id="@Nillionaire_ar", user_id=user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# تحميل الفيديو باستخدام الكوكيز
def download_with_fallback(url):
    try:
        ydl_opts = {
            'outtmpl': 'video.mp4',
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'cookiefile': 'cookies.txt',  # إضافة ملف الكوكيز هنا
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        stream.download(filename="video.mp4")

# دالة ترحيب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user_to_db(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔔 اشترك في القناة", url=channel_url))
        bot.reply_to(message, "للاستفادة من خدمات البوت، يرجى الاشتراك في [القناة](https://t.me/Nillionaire_ar).", parse_mode="Markdown", reply_markup=markup)
        return
    bot.reply_to(message, "🎉 مرحبًا بك! أرسل الرابط وسأقوم بتحميله!")

# تنزيل الفيديوهات
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def download_video(message):
    add_user_to_db(message.from_user.id)
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔔 اشترك في القناة", url=channel_url))
        bot.reply_to(message, "للاستفادة من خدمات البوت، يرجى الاشتراك في [القناة](https://t.me/Nillionaire_ar).", parse_mode="Markdown", reply_markup=markup)
        return

    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "🚫 الرجاء إرسال رابط فيديو صالح.")
        return

    bot.reply_to(message, "⏳ جاري معالجة الفيديو، يرجى الانتظار...")

    try:
        download_with_fallback(url)
        with open("video.mp4", 'rb') as video:
            bot.send_video(message.chat.id, video)
            update_downloads(message.from_user.id)
        os.remove("video.mp4")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء التحميل: {e}")

# عرض الإحصائيات للمالك
@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != bot_owner_id:
        bot.reply_to(message, "🚫 ليس لديك صلاحية الوصول إلى الإحصائيات.")
        return
    stats = get_stats()
    bot.reply_to(message, f"📊 إجمالي المستخدمين: {stats[0]}\n📥 إجمالي التنزيلات: {stats[1]}")

# إرسال رسالة لجميع المستخدمين
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id != bot_owner_id:
        bot.reply_to(message, "🚫 ليس لديك صلاحية إرسال الرسائل.")
        return

    conn = sqlite3.connect('stats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM usage_stats')
    user_ids = cursor.fetchall()
    conn.close()

    message_text = message.text[10:].strip()
    if not message_text:
        bot.reply_to(message, "❌ يرجى إدخال رسالة لإرسالها.")
        return

    for user_id in user_ids:
        try:
            bot.send_message(user_id[0], message_text)
        except Exception as e:
            print(f"❌ خطأ في الإرسال إلى {user_id[0]}: {e}")

    bot.reply_to(message, f"✅ تم إرسال الرسالة إلى {len(user_ids)} مستخدم.")

# بدء التشغيل
keep_alive()
bot.polling()
