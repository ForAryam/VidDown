from flask import Flask
import threading
import telebot
from yt_dlp import YoutubeDL
from pytube import YouTube
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
if not API_TOKEN:
    raise ValueError("❌ التوكن غير موجود في ملف .env. يرجى التحقق!")

bot = telebot.TeleBot(API_TOKEN)

channel_url = "https://t.me/Nillionaire_ar"
bot_owner_id = 5592854910  # استبدل برقم تعريفك كمستخدم

usage_stats = {
    'total_users': 0,
    'total_downloads': 0,
    'user_downloads': {}
}

def is_subscribed(user_id):
    if user_id == bot_owner_id:
        return True
    try:
        status = bot.get_chat_member(chat_id="@Nillionaire_ar", user_id=user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

def download_with_fallback(url):
    try:
        ydl_opts = {
            'outtmpl': 'video.mp4',
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'cookiefile': 'cookies.txt',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        try:
            yt = YouTube(url)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            stream.download(filename="video.mp4")
        except Exception as fallback_error:
            raise Exception(f"❌ فشل التحميل: {fallback_error}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔔 اشترك في القناة", url=channel_url))
        bot.reply_to(
            message,
            "⚠️ للاستخدام، يرجى الاشتراك في القناة أولًا:\n"
            "[القناة](https://t.me/Nillionaire_ar)",
            parse_mode="Markdown",
            reply_markup=markup,
        )
        return

    usage_stats['total_users'] += 1  # زيادة عداد المستخدمين
    bot.reply_to(
        message,
        "🎉 مرحبًا بك! أنا بوت لتحميل الفيديوهات من YouTube وغيرها.\n"
        "📥 أرسل الرابط لتحميل الفيديو.\n"
        "📊 عدد المستخدمين الحاليين: {0}".format(usage_stats['total_users']),
        parse_mode="Markdown",
    )

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def download_video(message):
    if not is_subscribed(message.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔔 اشترك في القناة", url=channel_url))
        bot.reply_to(
            message,
            "⚠️ للاستخدام، يرجى الاشتراك في القناة أولًا:\n"
            "[القناة](https://t.me/Nillionaire_ar)",
            parse_mode="Markdown",
            reply_markup=markup,
        )
        return

    url = message.text.strip()

    if not url.startswith("http"):
        bot.reply_to(message, "❌ الرجاء إرسال رابط صالح.")
        return

    bot.reply_to(message, "⏳ جاري معالجة الفيديو...")

    try:
        download_with_fallback(url)

        with open("video.mp4", 'rb') as video:
            bot.send_video(message.chat.id, video)
            usage_stats['total_downloads'] += 1
            usage_stats['user_downloads'][message.from_user.id] = usage_stats['user_downloads'].get(message.from_user.id, 0) + 1

        os.remove("video.mp4")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء التحميل: {e}")

# إرسال إشعارات للمشتركين
def send_notification_to_subscribers(text):
    for user_id in usage_stats['user_downloads'].keys():
        try:
            bot.send_message(user_id, text)
        except Exception as e:
            print(f"❌ فشل إرسال رسالة للمستخدم {user_id}: {e}")

# أوامر التحكم
@bot.message_handler(commands=['stats'])
def send_stats(message):
    if message.from_user.id == bot_owner_id:
        total_users = usage_stats['total_users']
        total_downloads = usage_stats['total_downloads']
        bot.send_message(
            message.chat.id,
            f"📊 إحصائيات البوت:\n"
            f"عدد المستخدمين الكلي: {total_users}\n"
            f"إجمالي التحميلات: {total_downloads}",
        )
    else:
        bot.send_message(message.chat.id, "🚫 ليس لديك صلاحيات للوصول إلى الإحصائيات.")

@bot.message_handler(commands=['send_message'])
def send_message_to_all(message):
    if message.from_user.id == bot_owner_id:
        msg_text = message.text[len('/send_message '):]  # استخراج النص من الأمر
        send_notification_to_subscribers(msg_text)
        bot.send_message(message.chat.id, "✅ تم إرسال الرسالة لجميع المشتركين.")
    else:
        bot.send_message(message.chat.id, "🚫 ليس لديك صلاحيات لإرسال رسائل لجميع المشتركين.")

@bot.message_handler(commands=['restart'])
def restart_bot(message):
    if message.from_user.id == bot_owner_id:
        bot.send_message(message.chat.id, "🔄 إعادة تشغيل البوت...")
        os.system("sudo reboot")  # إعادة تشغيل الخادم
    else:
        bot.send_message(message.chat.id, "🚫 ليس لديك صلاحيات لإعادة تشغيل البوت.")

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    if message.from_user.id == bot_owner_id:
        bot.send_message(message.chat.id, "⛔️ إيقاف البوت...")
        exit()  # إيقاف البوت
    else:
        bot.send_message(message.chat.id, "🚫 ليس لديك صلاحيات لإيقاف البوت.")

keep_alive()
bot.polling()
