import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

# ========== SOZLAMALAR ==========
TOKEN = "8895387043:AAGeu1YomhIuIv_brIxL75gzKoDyFuaLMq0"
GROUP_CHAT_ID = None  # GURUH ID SINI SHU YERGA YOZING!

bot = telebot.TeleBot(TOKEN)

# Ma'lumotlar fayli
DATA_FILE = "user_data.json"

# Ma'lumotlarni yuklash
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Ma'lumotlarni saqlash
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

user_data = load_data()

# ========== TUGMALAR ==========
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🍞 Non buyurtma qilish", callback_data="order"),
        InlineKeyboardButton("📋 Mening ma'lumotlarim", callback_data="my_info"),
        InlineKeyboardButton("❓ Yordam", callback_data="help")
    )
    return keyboard

# ========== BUYRUQLAR ==========
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"🇺🇿 Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "Non zakaz qilish botiga xush kelibsiz!\n\n"
        "📌 Buyurtma qilish uchun tugmalardan foydalaning.",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['myid'])
def show_chat_id(message):
    """Guruh ID sini ko'rsatish"""
    bot.reply_to(
        message,
        f"🆔 Chat ID: `{message.chat.id}`\n"
        f"📌 Type: `{message.chat.type}`",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['setgroup'])
def set_group_id(message):
    """Admin uchun: guruh ID sini saqlash"""
    if message.from_user.id == 6514150973:  # Farrukh ID
        parts = message.text.split()
        if len(parts) == 2:
            global GROUP_CHAT_ID
            GROUP_CHAT_ID = int(parts[1])
            bot.reply_to(message, f"✅ Guruh ID saqlandi: {GROUP_CHAT_ID}")
        else:
            bot.reply_to(message, "❌ /setgroup -1001234567890")
    else:
        bot.reply_to(message, "❌ Siz admin emassiz!")

# ========== CALLBACKLAR ==========
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    user_id = str(call.from_user.id)

    if call.data == "order":
        bot.edit_message_text(
            "🍞 **Non buyurtma qilish**\n\n"
            "📍 Iltimos, manzilingizni yuboring:\n"
            "(📍 joylashuv tugmasini bosing)",
            chat_id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=location_button()
        )

    elif call.data == "my_info":
        if user_id in user_data:
            data = user_data[user_id]
            msg = f"📋 **Sizning ma'lumotlaringiz:**\n\n"
            msg += f"📞 Telefon: {data.get('phone', '❌ Yo‘q')}\n"
            msg += f"📍 Manzil: {data.get('address', '❌ Yo‘q')}"
        else:
            msg = "❌ Siz hali ma'lumot saqlamagansiz.\n\nBirinchi buyurtmadan keyin saqlanadi."
        bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=main_menu())

    elif call.data == "help":
        msg = "❓ **Yordam**\n\n"
        msg += "• «Non buyurtma qilish» tugmasini bosing\n"
        msg += "• Manzilingizni lokatsiya sifatida yuboring\n"
        msg += "• Telefon raqamingiz birinchi buyurtmadan keyin saqlanadi\n\n"
        msg += "📞 Savollar uchun: @admin"
        bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=main_menu())

    elif call.data == "back":
        bot.edit_message_text("Bosh menyu", chat_id, call.message.message_id, reply_markup=main_menu())

    elif call.data == "enter_phone":
        msg = bot.send_message(chat_id, "📞 Telefon raqamingizni yuboring:\nMasalan: +998901234567")
        bot.register_next_step_handler(msg, save_phone)

def location_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📍 Manzil yuborish", request_location=True))
    keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data="back"))
    return keyboard

# ========== LOKATSIYA QABUL QILISH ==========
@bot.message_handler(content_types=['location'])
def handle_location(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    lat = message.location.latitude
    lon = message.location.longitude

    # Manzilni saqlash
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['address'] = f"{lat}, {lon}"

    # Telefon raqam so'rash
    msg = bot.send_message(
        chat_id,
        "📍 Manzil saqlandi!\n\n📞 Endi telefon raqamingizni yuboring:",
        reply_markup=phone_button()
    )
    bot.register_next_step_handler(msg, save_phone_after_location, lat, lon)

def phone_button():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📞 Telefon raqam yuborish", request_contact=True))
    return keyboard

def save_phone_after_location(message, lat, lon):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    user = message.from_user

    phone = None
    if message.contact:
        phone = message.contact.phone_number
    elif message.text and message.text.replace("+", "").isdigit():
        phone = message.text
    else:
        bot.send_message(chat_id, "❌ Telefon raqamni to'g'ri yuboring! /start bilan qaytadan boshlang.")
        return

    # Telefonni saqlash
    user_data[user_id]['phone'] = phone
    save_data(user_data)

    # Guruhga buyurtma yuborish
    if GROUP_CHAT_ID:
        order_text = f"🆕 **YANGI BUYURTMA!**\n\n"
        order_text += f"👤 Mijoz: {user.first_name}"
        if user.username:
            order_text += f" (@{user.username})"
        order_text += f"\n"
        order_text += f"📞 Telefon: {phone}\n"
        order_text += f"🆔 ID: `{user.id}`\n\n"
        order_text += f"🍞 Mahsulot: Non\n"
        order_text += f"🔢 Soni: 1 dona (standart)\n\n"
        order_text += f"📍 Manzil:\n"
        order_text += f"🗺 Xaritada ko'rish\n"
        order_text += f"https://maps.google.com/?q={lat},{lon}"

        try:
            bot.send_message(GROUP_CHAT_ID, order_text, parse_mode='Markdown')
        except Exception as e:
            print(f"Guruhga yuborishda xato: {e}")

    # Foydalanuvchiga javob
    bot.send_message(
        chat_id,
        f"✅ **Buyurtmangiz qabul qilindi!**\n\n"
        f"🍞 Non: 1 dona\n"
        f"📍 Manzil: {lat}, {lon}\n"
        f"📞 Telefon: {phone}\n\n"
        "Tez orada yetkazib beriladi! 🚀",
        parse_mode='Markdown',
        reply_markup=main_menu()
    )

def save_phone(message):
    """Telefon raqamni saqlash"""
    chat_id = message.chat.id
    user_id = str(message.from_user.id)

    if message.contact:
        phone = message.contact.phone_number
    elif message.text and message.text.replace("+", "").isdigit():
        phone = message.text
    else:
        bot.send_message(chat_id, "❌ Telefon raqamni to'g'ri yuboring!")
        return

    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['phone'] = phone
    save_data(user_data)

    bot.send_message(chat_id, f"✅ Telefon raqam saqlandi: {phone}", reply_markup=main_menu())

# ========== MATNLI XABARLAR ==========
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)

    # Telefon raqam tekshirish
    if message.text.replace("+", "").replace(" ", "").isdigit() and len(message.text.replace("+", "")) >= 9:
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['phone'] = message.text
        save_data(user_data)
        bot.send_message(chat_id, f"✅ Telefon raqam saqlandi: {message.text}", reply_markup=main_menu())
    else:
        bot.send_message(chat_id, "❌ Iltimos, tugmalardan foydalaning!", reply_markup=main_menu())

# ========== BOTNI ISHGA TUSHIRISH ==========
if __name__ == "__main__":
    print("🚀 Bot ishga tushdi...")
    print(f"📌 Token: {TOKEN[:10]}...")
    print("📌 Guruh ID: ", GROUP_CHAT_ID if GROUP_CHAT_ID else "❌ O'rnatilmagan")
    print("\n💡 Guruh ID sini olish uchun guruhda /myid buyrug'ini yozing")
    print("💡 So'ng /setgroup -100xxxxxxx bilan o'rnating")
    bot.infinity_polling()
