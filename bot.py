#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nova-Bot - ربات چند منظوره سروش پلاس
نسخه 1.0
"""

import os
import json
import time
import random
import logging
from io import BytesIO

import requests
from sseclient import SSEClient
from dotenv import load_dotenv
import qrcode

# ==================== تنظیمات ====================
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("توکن ربات پیدا نشد! فایل .env را بررسی کنید.")

BASE_URL = f"https://bot.sapp.ir/{TOKEN}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("NovaBot")

# ==================== متن‌ها ====================

WELCOME_TEXT = """✨ سلام! به **Nova-Bot** خوش آمدید.

من یک ربات چند منظوره هستم که می‌تونم کمکت کنم:

🎵 جستجوی آهنگ
🤣 جوک و سرگرمی
🎮 بازی
📱 ساخت QR کد
🔮 فال
🛡️ مدیریت گروه

از منوی زیر یکی رو انتخاب کن."""

HELP_TEXT = """📖 **راهنمای Nova-Bot**

• برای جستجوی آهنگ روی دکمه «جستجوی آهنگ» بزن و نام آهنگ را بفرست.
• برای ساخت QR کد، متن یا لینک را ارسال کن.
• در گروه‌ها می‌تونی ربات را ادمین کنی تا از قابلیت‌های مدیریتی استفاده کند.

اگر سوالی داری یا مشکلی پیش آمد، به مالک ربات پیام بده."""

RULES_TEXT = """📜 **قوانین استفاده از Nova-Bot**

1. از ربات برای مقاصد مخرب استفاده نکنید.
2. ارسال اسپم و تبلیغات ممنوع است.
3. حریم به حریم کاربران را رعایت کنید.
4. در گروه‌ها از قوانین گروه پیروی کنید.
5. مسئولیت استفاده صحیح از ربات بر عهده کاربر است.

با رعایت از قوانین، همه بهتر لذت می‌بریم ❤️"""

JOKES = [
    "یه روز یه نفر میره پزشک میگه: آقای چند میشه این پزشک؟\nپزشک میگه: نمی‌دونم، من فقط یه پزشکم!",
    "معلم به شاگرد گفت: چرا دیر آمدی؟\nگفت: چون میگه خوبه، منم گفتم!",
    "یه نفر رفت پزشک و گفت: کدوم زودترینه؟\nپزشک: من!\nگفت: پس چرا تو رفتی؟",
    "پدر به پسرش: چرا مشقت نمی‌خونی؟\nپسر: چون میگه اگه مشق بشم، دیگه می‌خوام برم!",
]

FAL_LIST = [
    "امروز روز خوبی برات هست. از فرصت‌های جدید نترس!",
    "یک خبر خوب در راه ه. صبور باش.",
    "امروز روز مناسبی برای شروع کارهای جدید است.",
    "به غریبه‌هات گوش بده، جوابش رو می‌گیری.",
    "امروز روز از نظر مالی وضعیت خوبی داری.",
]

# ==================== توابع ارسال ====================

def send_text(to: str, text: str, keyboard=None):
    data = {"to": to, "type": "TEXT", "body": text}
    if keyboard:
        data["keyboard"] = keyboard
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", json=data, timeout=15)
        return r.status_code == 200
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False


def make_main_keyboard():
    return {
        "keyboard": [
            [{"text": "🎵 جستجوی آهنگ"}, {"text": "🤣 جوک و سرگرمی"}],
            [{"text": "🎮 بازی"}, {"text": "📱 QR کد"}],
            [{"text": "🔮 فال"}, {"text": "🛡️ مدیریت گروه"}],
            [{"text": "📜 قوانین"}, {"text": "📖 راهنما"}],
            [{"text": "🔄 شروع مجدد"}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }


def make_back_keyboard():
    return {
        "keyboard": [[{"text": "🔙 بازگشت"}]],
        "resize_keyboard": True
    }

# ==================== دستورات ====================

def handle_start(user_id: str):
    send_text(user_id, WELCOME_TEXT, make_main_keyboard())


def handle_joke(user_id: str):
    joke = random.choice(JOKES)
    send_text(user_id, f"🤣 {joke}", make_back_keyboard())


def handle_fal(user_id: str):
    fal = random.choice(FAL_LIST)
    send_text(user_id, f"🔮 **فال امروز شما:**\n\n{fal}", make_back_keyboard())


def handle_help(user_id: str):
    send_text(user_id, HELP_TEXT, make_back_keyboard())


def handle_rules(user_id: str):
    send_text(user_id, RULES_TEXT, make_back_keyboard())


def handle_qr(user_id: str, text: str = None):
    if not text or text in ["📱 QR کد", "🔙 بازگشت"]:
        send_text(user_id, "لطفا متن یا لینکی که می‌خوای QR کدش ساخته بشه رو بفرست:", make_back_keyboard())
        return "waiting_qr"

    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        files = {"file": ("qrcode.png", buffer, "image/png")}
        r = requests.post(f"{BASE_URL}/uploadFile", files=files, timeout=30)

        if r.status_code == 200:
            result = r.json()
            file_url = result.get("url") or result.get("fileUrl")
            if file_url:
                data = {
                    "to": user_id,
                    "type": "FILE",
                    "fileUrl": file_url,
                    "fileName": "qrcode.png",
                    "fileType": "IMAGE",
                    "body": "QR کد شما آماده شد ✅"
                }
                requests.post(f"{BASE_URL}/sendMessage", json=data, timeout=15)
            else:
                send_text(user_id, "QR کد ساخته شد، اما در ارسال مشکلی پیش آمد.", make_main_keyboard())
        else:
            send_text(user_id, "خطا در ساخت QR کد. لطفا دوباره تلاش کن.", make_main_keyboard())
    except Exception as e:
        logger.error(f"QR Error: {e}")
        send_text(user_id, "خطا در ساخت QR کد.", make_main_keyboard())

    return None


def handle_music(user_id: str, text: str = None):
    if not text or text == "🎵 جستجوی آهنگ":
        send_text(user_id, "🎵 نام آهنگ یا خواننده را بفرست:", make_back_keyboard())
        return "waiting_music"

    query = text.strip()
    reply = f"""🎵 نتیجه جستجو برای: **{query}**

لینک‌های دانلود (نمونه):

1. 🎧 دانلود با کیفیت 320
2. 🎧 دانلود با کیفیت 128

> توضیح: این بخش در نسخه‌های بعدی به API واقعی موزیک وصل می‌شود."""
    send_text(user_id, reply, make_main_keyboard())
    return None


def handle_game(user_id: str):
    games = [
        "🎲 بازی ساده: عدد بین ۱ تا ۱۰ رو حدس بزن!",
        "✊ سنگ کاغذ قیچی بازی کنیم؟",
        "🧠 یه سوال: پایتخت ایران کجاست؟"
    ]
    send_text(user_id, random.choice(games), make_back_keyboard())


def handle_group_management(user_id: str):
    text = """🛡️ **مدیریت گروه**

برای فعال‌سازی این بخش:
1. ربات را به گروه اضافه کن
2. ربات را ادمین کن

قابلیت‌های فعلی (نسخه ۱):
• خوش‌آمدگویی به اعضای جدید
• حذف لینک و تبلیغات
• حذف فحش
• پاکسازی پیام‌ها
• تنظیم قوانین گروه

> این بخش در نسخه‌های بعدی کامل‌تر خواهد شد."""
    send_text(user_id, text, make_back_keyboard())

# ==================== حالت کاربران ====================
user_states = {}

# ==================== حلقه اصلی ====================

def process_message(msg: dict):
    try:
        data = msg if isinstance(msg, dict) else json.loads(msg)

        msg_type = data.get("type")
        user_id = data.get("from")
        body = data.get("body", "").strip()

        if not user_id:
            return

        if msg_type == "START":
            handle_start(user_id)
            user_states.pop(user_id, None)
            return

        if msg_type == "HEALTH_CHECK":
            return

        if msg_type != "TEXT":
            return

        state = user_states.get(user_id)

        if state == "waiting_qr":
            new_state = handle_qr(user_id, body)
            if new_state is None:
                user_states.pop(user_id, None)
            return

        if state == "waiting_music":
            new_state = handle_music(user_id, body)
            if new_state is None:
                user_states.pop(user_id, None)
            return

        if body in ["/start", "🔄 شروع مجدد", "شروع"]:
            handle_start(user_id)
            user_states.pop(user_id, None)

        elif body == "🔙 بازگشت":
            handle_start(user_id)
            user_states.pop(user_id, None)

        elif body == "🤣 جوک و سرگرمی":
            handle_joke(user_id)

        elif body == "🔮 فال":
            handle_fal(user_id)

        elif body == "📖 راهنما":
            handle_help(user_id)

        elif body == "📜 قوانین":
            handle_rules(user_id)

        elif body == "📱 QR کد":
            state = handle_qr(user_id)
            if state:
                user_states[user_id] = state

        elif body == "🎵 جستجوی آهنگ":
            state = handle_music(user_id)
            if state:
                user_states[user_id] = state

        elif body == "🎮 بازی":
            handle_game(user_id)

        elif body == "🛡️ مدیریت گروه":
            handle_group_management(user_id)

        else:
            send_text(user_id, "دستور شناخته نشده. از منو استفاده کن یا روی «شروع مجدد» بزن.", make_main_keyboard())

    except Exception as e:
        logger.error(f"Error processing message: {e}")


def main():
    logger.info("Nova-Bot شروع به کار کرد...")
    logger.info(f"Token: {TOKEN[:12]}...")

    while True:
        try:
            url = f"{BASE_URL}/v2/getMessage"
            headers = {
                "Content-Type": "application/stream+json",
                "Accept": "application/stream+json"
            }

            response = requests.get(url, stream=True, headers=headers, timeout=60)
            client = SSEClient(response)

            for event in client.events():
                if event.data:
                    try:
                        data = json.loads(event.data)
                        process_message(data)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Connection error: {e}")
            logger.info("تلاش مجدد برای اتصال در ۵ ثانیه...")
            time.sleep(5)


if __name__ == "__main__":
    main()
