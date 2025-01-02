from flask import Flask
import threading
import telebot
from yt_dlp import YoutubeDL
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

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

# استبدل بالتوكن الخاص بك
API_TOKEN = "7042669036:AAGSiKCw1dpoLTqW9O3Z6WJ4vlLSXkbWIKY"
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

# تحديث الإحصائيات
def update_stats(user_id):
    usage_stats['total_downloads'] += 1
    if user_id in usage_stats['user_downloads']:
        usage_stats['user_downloads'][user_id] += 1
    else:
        usage_stats['user_downloads'][user_id] = 1
        usage_stats['total_users'] += 1

# تحديد نوع الرابط
def detect_platform(url):
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    elif "instagram.com" in url:
        return "Instagram"
    elif "facebook.com" in url:
        return "Facebook"
    elif "tiktok.com" in url:
        return "TikTok"
    elif "twitter.com" in url:
        return "Twitter"
    else:
        return "Unknown"

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
            "📌 **YouTube, Facebook, Instagram, Twitter **\n\n"
            "🎥 أرسل الرابط وسأقوم بتحميل الفيديو لك!"
        ),
        parse_mode="Markdown",
    )

# إحصائيات الاستخدام
@bot.message_handler(commands=['stats'])
def send_stats(message):
    if message.from_user.id != bot_owner_id:
        bot.reply_to(message, "❌ ليس لديك صلاحية الوصول إلى هذه الأوامر.")
        return

    stats_message = (
        f"📊 **إحصائيات الاستخدام:**\n"
        f"👥 إجمالي عدد المستخدمين: {usage_stats['total_users']}\n"
        f"📥 إجمالي عدد التنزيلات: {usage_stats['total_downloads']}\n"
    )
    bot.reply_to(message, stats_message, parse_mode="Markdown")

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

    platform = detect_platform(url)
    bot.reply_to(message, f"⏳ جاري معالجة الفيديو من {platform}، يرجى الانتظار...")

    try:
        ydl_opts = {
            'outtmpl': 'video.mp4',  # تسمية الفيديو المؤقت
            'quiet': True,           # تشغيل بصمت
            'no_warnings': True,     # منع التحذيرات
            'format': 'best'         # أفضل جودة متاحة
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_size = info_dict.get('filesize', 0)  # حجم الفيديو بالبايت
            if video_size > 100 * 1024 * 1024:  # 100 ميجابايت
                bot.reply_to(message, "🚫 حجم الفيديو يتجاوز الحد المسموح به (100 ميجابايت).")
                return

            ydl.download([url])  # تحميل الفيديو

        # إرسال الفيديو
        with open("video.mp4", 'rb') as video:
            bot.send_video(message.chat.id, video)
            update_stats(message.from_user.id)

        # حذف الملف بعد الإرسال
        os.remove("video.mp4")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء التحميل: {e}")

# استدعاء دالة خادم الويب
keep_alive()

# بدء تشغيل البوت
bot.polling()
