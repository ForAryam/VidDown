from flask import Flask
import threading
import telebot
from yt_dlp import YoutubeDL
from pytube import YouTube  # مكتبة pytube
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv  # مكتبة dotenv لتحميل المتغيرات البيئية

# تحميل المتغيرات البيئية من ملف .env
load_dotenv()

# إنشاء تطبيق Flask
app = Flask('')

# تعريف الصفحة الرئيسية
@app.route('/')
def home():
    return "Bot is running!"

# تشغيل السيرفر
def run():
    app.run(host='0.0.0.0', port=8080)

# إبقاء السيرفر نشطًا
def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# الحصول على التوكن من ملف .env
API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ التوكن غير موجود في ملف .env. يرجى التحقق!")

bot = telebot.TeleBot(API_TOKEN)

# رابط القناة
channel_url = "https://t.me/Nillionaire_ar"
bot_owner_id = 5592854910  # استبدل برقم تعريفك كمستخدم

# إحصائيات
usage_stats = {
    'total_users': 0,
    'total_downloads': 0,
    'user_downloads': {}
}

# التحقق من الاشتراك في القناة
def is_subscribed(user_id):
    if user_id == bot_owner_id:
        return True
    try:
        status = bot.get_chat_member(chat_id="@Nillionaire_ar", user_id=user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

# تحميل الفيديو مع دعم مكتبات متعددة
def download_with_fallback(url):
    try:
        # المحاولة باستخدام yt_dlp
        ydl_opts = {
            'outtmpl': 'video.mp4',
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'cookiefile': 'cookies.txt',  # مسار ملف الكوكيز
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        try:
            # المحاولة باستخدام pytube
            yt = YouTube(url)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            stream.download(filename="video.mp4")
        except Exception as fallback_error:
            raise Exception(f"❌ فشل التحميل باستخدام جميع المكتبات. الخطأ: {fallback_error}")

# رسالة الترحيب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔔 اشترك في القناة", url=channel_url))
        bot.reply_to(
            message,
            "للاستفادة من خدمات البوت، يرجى الاشتراك في [القناة](https://t.me/Nillionaire_ar).",
            parse_mode="Markdown",
            reply_markup=markup,
        )
        return

    bot.reply_to(
        message,
        (
            "🎉 مرحبًا بك!\n"
            "أنا بوت لتحميل الفيديوهات من المنصات التالية:\n"
            "📌 **YouTube, Facebook, Instagram, Twitter**\n\n"
            "🎥 أرسل الرابط وسأقوم بتحميل الفيديو لك!"
        ),
        parse_mode="Markdown",
    )

# تنزيل الفيديوهات
@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def download_video(message):
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔔 اشترك في القناة", url=channel_url))
        bot.reply_to(
            message,
            "للاستفادة من خدمات البوت، يرجى الاشتراك في [القناة](https://t.me/Nillionaire_ar).",
            parse_mode="Markdown",
            reply_markup=markup,
        )
        return

    url = message.text.strip()

    # التحقق من صحة الرابط
    if not url.startswith("http"):
        bot.reply_to(message, "🚫 الرجاء إرسال رابط فيديو صالح.")
        return

    bot.reply_to(message, "⏳ جاري معالجة الفيديو، يرجى الانتظار...")

    try:
        download_with_fallback(url)

        # إرسال الفيديو
        with open("video.mp4", 'rb') as video:
            bot.send_video(message.chat.id, video)
            usage_stats['total_downloads'] += 1
            usage_stats['user_downloads'][message.from_user.id] = usage_stats['user_downloads'].get(message.from_user.id, 0) + 1

        # حذف الملف بعد الإرسال
        os.remove("video.mp4")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء التحميل: {e}")

# استدعاء دالة خادم الويب
keep_alive()

# بدء تشغيل البوت
bot.polling()
