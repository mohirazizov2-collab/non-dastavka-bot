#!/usr/bin/env python3
"""
Non Dastavka Bot - Zakazlar guruhga tushadi
"""

import logging
import json
import os
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

BOT_TOKEN = "8895387043:AAGeu1YomhIuIv_brIxL75gzKoDyFuaLMq0"

USERS_FILE = "users_data.json"
ORDERS_FILE = "orders.json"
NON_NOMI = "🍞 Non"

# ─────────────────────────────────────────
# GURUH SOZLAMALARI
# ─────────────────────────────────────────
GROUP_CHAT_ID = -1001234567890  # <-- O'Z GURUH CHAT_ID RAQAMINI QO'YING
GROUP_THREAD_ID = None  # Agar guruhda topiclar bo'lsa, thread_id ni yozing (masalan: 12345)
# ─────────────────────────────────────────

# Conversation states
NON_SONI, TELEFON, LOKATSIYA, LOKATSIYA_YANGILASH = range(4)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────
# JSON bilan ishlash
# ─────────────────────────────────────────

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user(user_id: int):
    data = load_data(USERS_FILE)
    return data.get(str(user_id))


def save_user(user_id: int, udata: dict):
    data = load_data(USERS_FILE)
    data[str(user_id)] = udata
    save_data(USERS_FILE, data)


def add_user_location(user_id: int, lat: float, lon: float, label: str = None):
    data = load_data(USERS_FILE)
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"telefon": None, "lokatsiyalar": []}
    lokatsiyalar = data[uid].get("lokatsiyalar", [])
    for loc in lokatsiyalar:
        if abs(loc["lat"] - lat) < 0.0005 and abs(loc["lon"] - lon) < 0.0005:
            return
    lokatsiyalar.append({
        "lat": lat, "lon": lon,
        "label": label or f"Manzil {len(lokatsiyalar) + 1}"
    })
    data[uid]["lokatsiyalar"] = lokatsiyalar
    save_data(USERS_FILE, data)


def save_order(order_id: str, order: dict):
    orders = load_data(ORDERS_FILE)
    orders[order_id] = order
    save_data(ORDERS_FILE, orders)


def get_order(order_id: str):
    return load_data(ORDERS_FILE).get(order_id)


def update_order(order_id: str, fields: dict):
    orders = load_data(ORDERS_FILE)
    if order_id in orders:
        orders[order_id].update(fields)
        save_data(ORDERS_FILE, orders)


# ─────────────────────────────────────────
# /start
# ─────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    saved = get_user(user.id)

    keyboard = [
        [KeyboardButton("📦 Non buyurtma qilish")],
        [KeyboardButton("👤 Mening ma'lumotlarim")],
        [KeyboardButton("ℹ️ Yordam")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if saved and saved.get("telefon"):
        await update.message.reply_text(
            f"Qaytib keldingiz, *{user.first_name}*! 👋\n\n"
            f"📱 Saqlangan raqam: `{saved['telefon']}`\n"
            f"📍 Saqlangan manzillar: *{len(saved.get('lokatsiyalar', []))} ta*\n\n"
            "Buyurtma qilish uchun tugmani bosing 👇",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"Assalomu alaykum, *{user.first_name}*! 👋\n\n"
            "🍞 *Non Dastavka Botiga xush kelibsiz!*\n\n"
            "Bot orqali non buyurtma bering — deliverchi yetkazib beradi.\n\n"
            "Buyurtma qilish uchun tugmani bosing 👇",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


# ─────────────────────────────────────────
# Ma'lumotlarim
# ─────────────────────────────────────────

async def mening_malumotlarim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    saved = get_user(user.id)

    if not saved or not saved.get("telefon"):
        await update.message.reply_text(
            "📭 Sizning ma'lumotlaringiz hali saqlanmagan.\n"
            "Birinchi buyurtma bergandan keyin avtomatik saqlanadi."
        )
        return

    lokatsiyalar = saved.get("lokatsiyalar", [])
    loc_text = ""
    for i, loc in enumerate(lokatsiyalar, 1):
        maps_link = f"https://maps.google.com/?q={loc['lat']},{loc['lon']}"
        loc_text += f"  {i}. [{loc['label']}]({maps_link})\n"

    keyboard = [
        [InlineKeyboardButton("📍 Yangi lokatsiya qo'shish", callback_data="lokatsiya_qosh")],
        [InlineKeyboardButton("Barcha lokatsiyalarni o'chirish", callback_data="lokatsiya_tozala")],
    ]
    manzil_text = loc_text if loc_text else "Hech qanday manzil yoq"

    await update.message.reply_text(
        f"👤 *Sizning ma'lumotlaringiz:*\n\n"
        f"📱 Telefon: `{saved['telefon']}`\n"
        f"📍 Saqlangan manzillar ({len(lokatsiyalar)} ta):\n"
        f"{manzil_text}\n",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )


async def lokatsiya_qosh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]]
    await query.message.reply_text(
        "📍 *Yangi manzilni yuboring:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return LOKATSIYA_YANGILASH


async def lokatsiya_yangilash_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    user = update.effective_user
    lat, lon = location.latitude, location.longitude

    saved = get_user(user.id)
    lokatsiyalar = saved.get("lokatsiyalar", []) if saved else []
    label = f"Manzil {len(lokatsiyalar) + 1}"
    add_user_location(user.id, lat, lon, label)

    maps_link = f"https://maps.google.com/?q={lat},{lon}"
    keyboard = [
        [KeyboardButton("📦 Non buyurtma qilish")],
        [KeyboardButton("👤 Mening ma'lumotlarim")],
        [KeyboardButton("ℹ️ Yordam")],
    ]
    await update.message.reply_text(
        f"✅ *Yangi manzil saqlandi!*\n\n"
        f"📌 [{label}]({maps_link})",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        disable_web_page_preview=True
    )
    return ConversationHandler.END


async def lokatsiya_tozala_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[
        InlineKeyboardButton("✅ Ha", callback_data="lokatsiya_tozala_ha"),
        InlineKeyboardButton("Yoq", callback_data="lokatsiya_tozala_yoq"),
    ]]
    await query.edit_message_text(
        "⚠️ *Barcha manzillarni o'chirasizmi?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def lokatsiya_tozala_ha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data(USERS_FILE)
    uid = str(update.effective_user.id)
    if uid in data:
        data[uid]["lokatsiyalar"] = []
        save_data(USERS_FILE, data)
    await query.edit_message_text("Barcha manzillar o'chirildi.")


async def lokatsiya_tozala_yoq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Bekor qilindi.")


async def yordam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Yordam*\n\n"
        "📦 Buyurtma qilish: «Non buyurtma qilish» tugmasini bosing\n"
        "👤 Ma'lumotlarim: saqlangan raqam va manzillarni ko'rish\n"
        "📱 Telefon raqamingiz birinchi buyurtmadan keyin saqlanadi\n\n"
        "Savollar uchun: @admin",
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────
# Buyurtma jarayoni
# ─────────────────────────────────────────

async def buyurtma_boshlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🍞 *{NON_NOMI}*\n\n"
        "🔢 *Nechtadan kerak?*\n"
        "Raqam kiriting (masalan: 3)",
        parse_mode="Markdown"
    )
    return NON_SONI


async def non_soni_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        soni = int(update.message.text.strip())
        if soni <= 0 or soni > 100:
            await update.message.reply_text("⚠️ 1 dan 100 gacha raqam kiriting.")
            return NON_SONI
    except ValueError:
        await update.message.reply_text("⚠️ Faqat *raqam* kiriting.", parse_mode="Markdown")
        return NON_SONI

    context.user_data["soni"] = soni
    user = update.effective_user
    saved = get_user(user.id)

    if saved and saved.get("telefon"):
        context.user_data["telefon"] = saved["telefon"]
        lokatsiyalar = saved.get("lokatsiyalar", [])
        if lokatsiyalar:
            keyboard = []
            for i, loc in enumerate(lokatsiyalar):
                keyboard.append([InlineKeyboardButton(f"📍 {loc['label']}", callback_data=f"saved_loc_{i}")])
            keyboard.append([InlineKeyboardButton("📍 Yangi lokatsiya yuborish", callback_data="yangi_loc")])
            await update.message.reply_text(
                f"✅ *{soni} dona {NON_NOMI}*\n\n"
                f"📱 Telefon: `{saved['telefon']}` *(saqlangan)*\n\n"
                "📍 *Qaysi manzilga yetkazish kerak?*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return LOKATSIYA
        else:
            keyboard = [[KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]]
            await update.message.reply_text(
                f"✅ *{soni} dona {NON_NOMI}*\n\n"
                f"📱 Telefon: `{saved['telefon']}` *(saqlangan)*\n\n"
                "📍 *Manzilingizni yuboring:*",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
            return LOKATSIYA
    else:
        keyboard = [[KeyboardButton("📱 Telefon raqamimni yuborish", request_contact=True)]]
        await update.message.reply_text(
            f"✅ *{soni} dona {NON_NOMI}*\n\n"
            "📱 *Telefon raqamingizni yuboring:*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return TELEFON


async def telefon_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    telefon = contact.phone_number
    context.user_data["telefon"] = telefon

    user = update.effective_user
    saved = get_user(user.id) or {}
    saved["telefon"] = telefon
    saved.setdefault("lokatsiyalar", [])
    save_user(user.id, saved)

    lokatsiyalar = saved.get("lokatsiyalar", [])
    if lokatsiyalar:
        keyboard = []
        for i, loc in enumerate(lokatsiyalar):
            keyboard.append([InlineKeyboardButton(f"📍 {loc['label']}", callback_data=f"saved_loc_{i}")])
        keyboard.append([InlineKeyboardButton("📍 Yangi lokatsiya yuborish", callback_data="yangi_loc")])
        await update.message.reply_text(
            f"✅ Telefon: *{telefon}* *(saqlandi)*\n\n"
            "📍 *Qaysi manzilga yetkazish kerak?*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        keyboard = [[KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]]
        await update.message.reply_text(
            f"✅ Telefon: *{telefon}* *(saqlandi)*\n\n"
            "📍 *Manzilingizni yuboring:*",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
    return LOKATSIYA


async def saved_loc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    idx = int(query.data.replace("saved_loc_", ""))
    saved = get_user(user.id)
    lokatsiya = saved["lokatsiyalar"][idx]
    await query.edit_message_reply_markup(reply_markup=None)
    await _buyurtma_yuborish(update, context, lokatsiya["lat"], lokatsiya["lon"])
    return ConversationHandler.END


async def yangi_loc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]]
    await query.message.reply_text(
        "📍 *Yangi manzilingizni yuboring:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return LOKATSIYA


async def lokatsiya_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    user = update.effective_user
    lat, lon = location.latitude, location.longitude
    saved = get_user(user.id) or {}
    saved.setdefault("lokatsiyalar", [])
    save_user(user.id, saved)
    add_user_location(user.id, lat, lon)
    await _buyurtma_yuborish(update, context, lat, lon)
    return ConversationHandler.END


async def _buyurtma_yuborish(update: Update, context: ContextTypes.DEFAULT_TYPE, lat: float, lon: float):
    user = update.effective_user
    soni = context.user_data.get("soni")
    telefon = context.user_data.get("telefon")
    maps_link = f"https://maps.google.com/?q={lat},{lon}"

    order_id = str(int(time.time()))

    order = {
        "order_id": order_id,
        "mijoz_id": user.id,
        "mijoz_ismi": user.full_name,
        "mijoz_username": user.username or "",
        "telefon": telefon,
        "soni": soni,
        "lat": lat,
        "lon": lon,
        "status": "kutilmoqda"
    }
    save_order(order_id, order)

    # Mijozga tasdiqlash
    keyboard = [[InlineKeyboardButton("📦 Yana buyurtma", callback_data="restart")]]
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "✅ *Buyurtmangiz qabul qilindi!*\n\n"
        f"🍞 {NON_NOMI} — {soni} dona\n\n"
        "🚚 Deliverchi tez orada bog'lanadi!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Guruhga yuborish
    await _guruhga_yuborish(context, order_id, order)
    context.user_data.clear()


# ─────────────────────────────────────────
# ZAKAZNI GURUHGA YUBORISH (ASOSIY O'ZGARISH)
# ─────────────────────────────────────────

async def _guruhga_yuborish(context, order_id: str, order: dict):
    """Zakaz ma'lumotlarini guruhga yuborish"""
    maps_link = f"https://maps.google.com/?q={order['lat']},{order['lon']}"
    username_text = f"@{order['mijoz_username']}" if order['mijoz_username'] else "username yoq"

    xabar = (
        f"🔔 *YANGI ZAKAZ!* (#{order_id[-4:]})\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"👤 Mijoz: {order['mijoz_ismi']}\n"
        f"📱 Telefon: `{order['telefon']}`\n"
        f"💬 Telegram: {username_text}\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"🍞 {NON_NOMI} — *{order['soni']} dona*\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"📍 [Xaritada ko'rish]({maps_link})\n"
        f"📌 `{order['lat']:.6f}, {order['lon']:.6f}`"
    )

    # Tugmalar
    keyboard = [[InlineKeyboardButton("✅ Qabul qildim", callback_data=f"driver_accept_{order_id}")]]

    try:
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=GROUP_THREAD_ID,  # Topic bo'lmasa None
            text=xabar,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await context.bot.send_location(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=GROUP_THREAD_ID,
            latitude=order["lat"],
            longitude=order["lon"]
        )
        update_order(order_id, {"status": "yuborildi"})
        logger.info(f"Zakaz #{order_id[-4:]} guruhga yuborildi")
    except Exception as e:
        logger.error(f"Guruhga yuborishda xatolik: {e}")


# ─────────────────────────────────────────
# Driver tugmalari
# ─────────────────────────────────────────

async def driver_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Driver zakaz qabul qildi (guruhdagi tugma orqali)"""
    query = update.callback_query
    await query.answer("✅ Qabul qildingiz!")
    order_id = query.data.replace("driver_accept_", "")
    order = get_order(order_id)

    driver = update.effective_user
    driver_name = f"@{driver.username}" if driver.username else driver.full_name

    update_order(order_id, {"status": "qabul_qilindi", "driver": driver_name})

    await query.edit_message_text(
        query.message.text + f"\n\n✅ *{driver_name} qabul qildi!*\n"
        f"📱 Mijoz tel: `{order['telefon']}`",
        parse_mode="Markdown"
    )

    # Mijozga xabar
    try:
        await context.bot.send_message(
            chat_id=order["mijoz_id"],
            text=f"🚗 *Deliverchi zakazingizni qabul qildi!*\n\n"
                 f"Tez orada yetkazib beriladi.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Mijozga xabar berishda xatolik: {e}")


# ─────────────────────────────────────────
# Bekor qilish
# ─────────────────────────────────────────

async def bekor_qilish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [KeyboardButton("📦 Non buyurtma qilish")],
        [KeyboardButton("👤 Mening ma'lumotlarim")],
        [KeyboardButton("ℹ️ Yordam")],
    ]
    await update.message.reply_text(
        "❌ Buyurtma bekor qilindi.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return ConversationHandler.END


async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"🍞 *{NON_NOMI}*\n\n"
        "🔢 *Nechtadan kerak?*\n"
        "Raqam kiriting (masalan: 3)",
        parse_mode="Markdown"
    )
    return NON_SONI


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    lokatsiya_qosh_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(lokatsiya_qosh_callback, pattern="^lokatsiya_qosh$")],
        states={
            LOKATSIYA_YANGILASH: [MessageHandler(filters.LOCATION, lokatsiya_yangilash_qabul)],
        },
        fallbacks=[CommandHandler("bekor", bekor_qilish)],
    )

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📦 Non buyurtma qilish$"), buyurtma_boshlash),
            CallbackQueryHandler(restart_callback, pattern="^restart$"),
        ],
        states={
            NON_SONI: [MessageHandler(filters.TEXT & ~filters.COMMAND, non_soni_qabul)],
            TELEFON:  [MessageHandler(filters.CONTACT, telefon_qabul)],
            LOKATSIYA: [
                MessageHandler(filters.LOCATION, lokatsiya_qabul),
                CallbackQueryHandler(saved_loc_callback, pattern="^saved_loc_"),
                CallbackQueryHandler(yangi_loc_callback, pattern="^yangi_loc$"),
            ],
        },
        fallbacks=[
            CommandHandler("bekor", bekor_qilish),
            MessageHandler(filters.Regex("^❌ Bekor qilish$"), bekor_qilish),
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yordam", yordam))
    app.add_handler(lokatsiya_qosh_conv)
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Yordam$"), yordam))
    app.add_handler(MessageHandler(filters.Regex("^👤 Mening ma'lumotlarim$"), mening_malumotlarim))
    app.add_handler(CallbackQueryHandler(driver_accept, pattern="^driver_accept_"))
    app.add_handler(CallbackQueryHandler(lokatsiya_tozala_callback, pattern="^lokatsiya_tozala$"))
    app.add_handler(CallbackQueryHandler(lokatsiya_tozala_ha, pattern="^lokatsiya_tozala_ha$"))
    app.add_handler(CallbackQueryHandler(lokatsiya_tozala_yoq, pattern="^lokatsiya_tozala_yoq$"))

    logger.info("🤖 Non Dastavka Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
