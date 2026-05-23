# =========================
# TELEGRAM BOT CANH CODE XWORLD
# PREMIUM VERSION
# =========================

import telebot
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor

TOKEN = "8717258749:AAEgG8r9vXteD75bqAD6ePPJL6LT-oXzQfk"

bot = telebot.TeleBot(TOKEN)

# =========================
# DATA
# =========================

users_data = {}

# users_data format:
# {
#   chat_id: {
#       "accounts": [(uid, skey)],
#       "threshold": 5,
#       "codes": ["ABC", "XYZ"],
#       "running": True
#   }
# }

# =========================
# API FUNCTIONS
# =========================

def get_code_remaining(code):
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://xworld-app.com',
        'referer': 'https://xworld-app.com/',
        'user-agent': 'Mozilla/5.0',
    }

    json_data = {
        'code': code,
        'os_ver': 'android',
        'platform': 'h5',
        'appname': 'app',
    }

    try:
        response = requests.post(
            'https://web3task.3games.io/v1/task/redcode/detail',
            headers=headers,
            json=json_data,
            timeout=10
        ).json()

        if response.get("code") == 0:
            total = response["data"]["user_cnt"]
            progress = response["data"]["progress"]
            return total - progress

    except:
        return None

    return None


def redeem_code(user_id, secret_key, code):
    headers = {
        'accept': '*/*',
        'content-type': 'application/json',
        'origin': 'https://xworld.info',
        'referer': 'https://xworld.info/',
        'user-agent': 'Mozilla/5.0',
        'user-id': user_id,
        'user-secret-key': secret_key,
    }

    json_data = {
        'code': code,
        'os_ver': 'android',
        'platform': 'h5',
        'appname': 'app',
    }

    try:
        response = requests.post(
            'https://web3task.3games.io/v1/task/redcode/exchange',
            headers=headers,
            json=json_data,
            timeout=10
        ).json()

        if response.get("code") == 0:
            value = response["data"]["value"]
            currency = response["data"]["currency"]
            return f"✅ {user_id} | +{value} {currency}"

        else:
            return f"❌ {user_id} | Thất bại"

    except:
        return f"⚠️ {user_id} | Lỗi mạng"


# =========================
# MAIN CHECK LOOP
# =========================

def code_checker(chat_id):
    while True:

        if chat_id not in users_data:
            break

        data = users_data[chat_id]

        if not data["running"]:
            time.sleep(1)
            continue

        for code in data["codes"]:

            remaining = get_code_remaining(code)

            current_time = time.strftime("%H:%M:%S")

            if remaining is None:
                bot.send_message(
                    chat_id,
                    f"⚠️ [{current_time}] Không lấy được dữ liệu code {code}"
                )
                continue

            bot.send_message(
                chat_id,
                f"🕒 [{current_time}] Code: {code}\n🎯 Còn: {remaining} lượt"
            )

            if remaining <= data["threshold"]:

                bot.send_message(
                    chat_id,
                    f"🚀 Code {code} đã đạt ngưỡng\nBắt đầu nhập..."
                )

                results = []

                with ThreadPoolExecutor(
                    max_workers=len(data["accounts"])
                ) as executor:

                    futures = []

                    for uid, skey in data["accounts"]:
                        futures.append(
                            executor.submit(
                                redeem_code,
                                uid,
                                skey,
                                code
                            )
                        )

                    for future in futures:
                        results.append(future.result())

                bot.send_message(
                    chat_id,
                    "\n".join(results)
                )

                bot.send_message(
                    chat_id,
                    f"✅ Hoàn thành code {code}"
                )

        time.sleep(1)


# =========================
# COMMANDS
# =========================

@bot.message_handler(commands=['start'])
def start(message):

    chat_id = message.chat.id

    users_data[chat_id] = {
        "accounts": [],
        "threshold": 0,
        "codes": [],
        "running": False
    }

    text = """
🔥 BOT CANH CODE XWORLD PREMIUM 🔥

Lệnh:

/setup - Cài đặt bot
/td - Tạm dừng
/tt - Tiếp tục
/tc - Thêm code mới

Sau khi setup bot sẽ tự canh code.
"""

    bot.send_message(chat_id, text)


# =========================
# SETUP
# =========================

@bot.message_handler(commands=['setup'])
def setup(message):

    chat_id = message.chat.id

    msg = bot.send_message(
        chat_id,
        "📌 Nhập số lượng acc:"
    )

    bot.register_next_step_handler(
        msg,
        process_account_amount
    )


def process_account_amount(message):

    chat_id = message.chat.id

    try:
        amount = int(message.text)

        users_data[chat_id]["temp_amount"] = amount
        users_data[chat_id]["temp_accounts"] = []

        ask_account(chat_id, 1)

    except:
        bot.send_message(chat_id, "❌ Sai định dạng")


def ask_account(chat_id, index):

    amount = users_data[chat_id]["temp_amount"]

    if index > amount:

        msg = bot.send_message(
            chat_id,
            "🎯 Nhập số lượt còn lại để auto nhập:"
        )

        bot.register_next_step_handler(
            msg,
            process_threshold
        )

        return

    msg = bot.send_message(
        chat_id,
        f"🔗 Gửi link acc thứ {index}:"
    )

    bot.register_next_step_handler(
        msg,
        lambda m: process_account_link(m, index)
    )


def process_account_link(message, index):

    chat_id = message.chat.id

    try:
        link = message.text.strip()

        uid = link.split('?userId=')[1].split('&')[0]
        skey = link.split('secretKey=')[1].split('&')[0]

        users_data[chat_id]["temp_accounts"].append(
            (uid, skey)
        )

        bot.send_message(
            chat_id,
            f"✅ Đã thêm acc {index}"
        )

        ask_account(chat_id, index + 1)

    except:
        bot.send_message(
            chat_id,
            "❌ Link sai định dạng"
        )


def process_threshold(message):

    chat_id = message.chat.id

    try:
        threshold = int(message.text)

        users_data[chat_id]["threshold"] = threshold
        users_data[chat_id]["accounts"] = users_data[chat_id]["temp_accounts"]

        msg = bot.send_message(
            chat_id,
            "🎟 Nhập code cần canh:"
        )

        bot.register_next_step_handler(
            msg,
            process_first_code
        )

    except:
        bot.send_message(chat_id, "❌ Sai định dạng")


def process_first_code(message):

    chat_id = message.chat.id

    code = message.text.strip()

    users_data[chat_id]["codes"] = [code]
    users_data[chat_id]["running"] = True

    bot.send_message(
        chat_id,
        f"🚀 Bắt đầu canh code:\n{code}"
    )

    thread = threading.Thread(
        target=code_checker,
        args=(chat_id,),
        daemon=True
    )

    thread.start()


# =========================
# PAUSE / RESUME
# =========================

@bot.message_handler(commands=['td'])
def pause_bot(message):

    chat_id = message.chat.id

    if chat_id in users_data:
        users_data[chat_id]["running"] = False

    bot.send_message(chat_id, "⏸ Đã tạm dừng")


@bot.message_handler(commands=['tt'])
def resume_bot(message):

    chat_id = message.chat.id

    if chat_id in users_data:
        users_data[chat_id]["running"] = True

    bot.send_message(chat_id, "▶️ Đã tiếp tục")


# =========================
# ADD MORE CODE
# =========================

@bot.message_handler(commands=['tc'])
def add_code(message):

    chat_id = message.chat.id

    msg = bot.send_message(
        chat_id,
        "🎟 Nhập code muốn thêm:"
    )

    bot.register_next_step_handler(
        msg,
        process_add_code
    )


def process_add_code(message):

    chat_id = message.chat.id

    code = message.text.strip()

    users_data[chat_id]["codes"].append(code)

    bot.send_message(
        chat_id,
        f"✅ Đã thêm code: {code}"
    )


# =========================
# RUN BOT
# =========================

print("BOT ĐANG CHẠY...")

bot.infinity_polling()
