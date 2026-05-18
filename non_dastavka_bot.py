import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

TOKEN = "8895387043:AAGeu1YomhIuIv_brIxL75gzKoDyFuaLMq0"
GROUP_CHAT_ID = None  # Bu yerga guruh ID sini qo'yaman

bot = telebot.TeleBot(TOKEN)

# Saqlangan ma'lumotlar
user_data = {}

# Foydalanuvchi ma'lumotlarini saqlash
def save_user(chat_id, phone, address):
    user_data[chat_id] = {
        'phone': phone,
        'address': address
    }

# Asosiy menyu tugmalari
def main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🍞 Non buyurtma qilish", callback_data="order_bread"),
        InlineKeyboardButton("📋 Mening ma'lumotlarim", callback_data="my_info"),
        InlineKeyboardButton("❓ Yordam", callback_data="help")
    )
    return keyboard

# Buyurtma shakli
def order_menu():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔢 Soni kiriting", callback_data="enter_quantity"),
        InlineKeyboardButton("📍 Manzilni yuborish", callback_data="send_location"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="back")
    )
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    bot.send_message(
        chat_id,
        f"🇺🇿 Assalomu alaykum, {message.from_user.first_name}!\n\n"
        "Non zakas qilish botiga xush kelibsiz!\n\n"
        "Buyurtma qilish uchun tugmalardan foydalaning.",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['myid'])
def show_id(message):
    bot.reply_to(
        message,
        f"🆔 Chat ID: `{message.chat.id}`\n"
        f"📌 Type: `{message.chat.type}`",
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    user = call.from_user
    
    if call.data == "order_bread":
        bot.edit_message_text(
            "🍞 **Non buyurtma qilish**\n\n"
            "Buyurtma ma'lumotlarini kiriting:",
            chat_id,
            call.message.message_id,
            parse_mode='Markdown',
            reply_markup=order_menu()
        )
    
    elif call.data == "my_info":
        if chat_id in user_data:
            data = user_data[chat_id]
            msg = f"📋 **Sizning ma'lumotlaringiz:**\n\n"
            msg += f"📞 Telefon: `{data['phone']}`\n"
            msg += f"📍 Manzil: `{data['address']}`"
        else:
            msg = "❌ Siz hali ma'lumot saqlamagansiz.\n\n"
            msg += "Birinchi buyurtmadan keyin ma'lumotlaringiz saqlanadi."
        bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=main_menu())
    
    elif call.data == "help":
        msg = "❓ **Yordam**\n\n"
        msg += "• «Non buyurtma qilish» tugmasini bosing\n"
        msg += "• «Mening ma'lumotlarim» - saqlangan raqam va manzillarni ko'rish\n"
        msg += "• Telefon raqamingiz birinchi buyurtmadan keyin saqlanadi\n\n"
        msg += "Savollar uchun: @admin"
        bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode='Markdown', reply_markup=main_menu())
    
    elif call.data == "enter_quantity":
        msg = bot.send_message(chat_id, "🍞 **Necha dona non kerak?**\n\nRaqam kiriting:")
        bot.register_next_step_handler(msg, get_quantity)
    
    elif call.data == "send_location":
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("📍 Manzilni yuborish", callback_data="share_location"))
        bot.edit_message_text(
            "📍 Iltimos, manzilingizni yuboring:",
            chat_id,
            call.message.message_id,
            reply_markup=keyboard
        )
    
    elif call.data == "share_location":
        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton("📍 Manzilni yuborish", request_location=True)
        keyboard.add(button)
        bot.send_message(chat_id, "📍 Manzilingizni yuboring:", reply_markup=keyboard)
        bot.register_next_step_handler(call.message, get_location)
    
    elif call.data == "back":
        bot.edit_message_text(
            "Bosh menyu",
            chat_id,
            call.message.message_id,
            reply_markup=main_menu()
        )

def get_quantity(message):
    chat_id = message.chat.id
    try:
        quantity = int(message.text)
        if quantity > 0:
            bot.user_data = bot.user_data if hasattr(bot, 'user_data') else {}
            bot.user_data[chat_id] = {'quantity': quantity}
            msg = bot.send_message(
                chat_id,
                f"✅ {quantity} dona non tanlandi.\n\n📍 Endi manzilingizni yuboring:",
                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("📍 Manzil yuborish", request_location=True))
            )
            bot.register_next_step_handler(msg, get_location)
        else:
            bot.send_message(chat_id, "❌ Iltimos, musbat raqam kiriting!")
    except:
        bot.send_message(chat_id, "❌ Iltimos, faqat raqam kiriting!")

def get_location(message):
    chat_id = message.chat.id
    user = message.from_user
    
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        
        quantity = getattr(bot, 'user_data', {}).get(chat_id, {}).get('quantity', 1)
        
        # Guruhga buyurtma ma'lumotlarini yuborish
        if GROUP_CHAT_ID:
            order_msg = f"🆕 **YANGI BUYURTMA!**\n\n"
            order_msg += f"👤 Mijoz: {user.first_name}\n"
            if user.username:
                order_msg += f"🆔 Username: @{user.username}\n"
            order_msg += f"📞 Telefon: {user_data.get(chat_id, {}).get('phone', 'Saqlanmagan')}\n"
            order_msg += f"🆔 ID: `{user.id}`\n\n"
            order_msg += f"🍞 Mahsulot: Non\n"
            order_msg += f"🔢 Soni: {quantity} dona\n\n"
            order_msg += f"📍 Manzil:\n"
            order_msg += f"https://maps.google.com/?q={lat},{lon}"
            
            bot.send_message(GROUP_CHAT_ID, order_msg, parse_mode='Markdown')
        
        # Foydalanuvchiga tasdiq xabari
        bot.send_message(
            chat_id,
            f"✅ Buyurtmangiz qabul qilindi!\n\n"
            f"🍞 Non: {quantity} dona\n"
            f"📍 Manzilingiz: {lat}, {lon}\n\n"
            "Tez orada yetkazib beriladi.",
            reply_markup=main_menu()
        )
        
        # Tozalash
        if hasattr(bot, 'user_data') and chat_id in bot.user_data:
            del bot.user_data[chat_id]
        
    elif message.text:
        # Telefon raqam yoki manzil matn sifatida kelsa
        if len(message.text) >= 10 and message.text.isdigit():
            if chat_id not in user_data:
                user_data[chat_id] = {}
            user_data[chat_id]['phone'] = message.text
            bot.send_message(chat_id, f"✅ Telefon raqam saqlandi: {message.text}")
        
        bot.send_message(
            chat_id,
            "📍 Iltimos, manzilingizni lokatsiya sifatida yuboring (📍 tugmasini bosing)!",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("📍 Manzil yuborish", request_location=True))
        )
    else:
        bot.send_message(chat_id, "❌ Iltimos, manzilingizni lokatsiya sifatida yuboring!")

@bot.message_handler(func=lambda m: m.text and m.text.isdigit() and len(m.text) >= 10)
def save_phone(message):
    chat_id = message.chat.id
    phone = message.text
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['phone'] = phone
    bot.send_message(chat_id, f"✅ Telefon raqam saqlandi: {phone}")

print("Bot ishga tushdi...")
bot.infinity_polling()
