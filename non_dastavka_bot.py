#!/usr/bin/env python3
"""
Non Dastavka Bot - Mijoz ma'lumotlari saqlanadi, lokatsiya yangilanadi
"""

import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

BOT_TOKEN = "8895387043:AAHLZ9romIgd-fR4gtpHX3fQ_lu9a5skTPU"
DELIVERCHI_CHAT_ID = 6514150973

# Foydalanuvchi ma'lumotlari saqlanadigan fayl
USERS_FILE = "users_data.json"

# Conversation states
NON_TURI, NON_SONI, TELEFON, LOKATSIYA, LOKATSIYA_YANGILASH = range(5)

NON_TURLARI = {
    "🍞 Oq non": 1500,
    "🥖 Bugʻdoy non": 2000,
    "🫓 Lavaş": 1000,
    "🥐 Boʻlka": 1200,
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────
# Foydalanuvchi ma'lumotlarini boshqarish (JSON)
# ───────────────────────────────────────────────

def load_users() -> dict:
    """JSON fayldan barcha foydalanuvchilarni yuklash"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users: dict):
    """Barcha foydalanuvchilarni JSON faylga saqlash"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def get_user(user_id: int) -> dict | None:
    """Bitta foydalanuvchini olish"""
    users = load_users()
    return users.get(str(user_id))


def save_user(user_id: int, data: dict):
    """Bitta foydalanuvchini saqlash/yangilash"""
    users = load_users()
    users[str(user_id)] = data
    save_users(users)


def add_user_location(user_id: int, lat: float, lon: float, label: str = None):
    """
    Foydalanuvchiga yangi lokatsiya qo'shish.
    Har bir lokatsiya {'lat', 'lon', 'label'} ko'rinishida saqlanadi.
    """
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"telefon": None, "lokatsiyalar": []}

    lokatsiyalar = users[uid].get("lokatsiyalar", [])

    # Takroriy lokatsiya tekshiruvi (~50m farq)
    for loc in lokatsiyalar:
        if abs(loc["lat"] - lat) < 0.0005 and abs(loc["lon"] - lon) < 0.0005:
            return  # Allaqachon bor

    lokatsiyalar.append({
        "lat": lat,
        "lon": lon,
        "label": label or f"Manzil {len(lokatsiyalar) + 1}"
    })
    users[uid]["lokatsiyalar"] = lokatsiyalar
    save_users(users)


# ───────────────────────────────────────────────
# Handlers
# ───────────────────────────────────────────────

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


async def mening_malumotlarim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    saved = get_user(user.id)

    if not saved or not saved.get("telefon"):
        await update.message.reply_text(
            "📭 Sizning ma'lumotlaringiz hali saqlanmagan.\n"
            "Birinchi buyurtma bergandan so'ng avtomatik saqlanadi."
        )
        return

    lokatsiyalar = saved.get("lokatsiyalar", [])
    loc_text = ""
    for i, loc in enumerate(lokatsiyalar, 1):
        maps_link = f"https://maps.google.com/?q={loc['lat']},{loc['lon']}"
        loc_text += f"  {i}. [{loc['label']}]({maps_link})\n"

    keyboard = [
        [InlineKeyboardButton("📍 Yangi lokatsiya qo'shish", callback_data="lokatsiya_qosh")],
        [InlineKeyboardButton("🗑 Barcha lokatsiyalarni o'chirish", callback_data="lokatsiya_tozala")],
    ]

    await update.message.reply_text(
        f"👤 *Sizning ma'lumotlaringiz:*\n\n"
        f"📱 Telefon: `{saved['telefon']}`\n"
        f"📍 Saqlangan manzillar ({len(lokatsiyalar)} ta):\n"
        f"{loc_text if loc_text else 'Hech qanday manzil yoq'}\n",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )


async def lokatsiya_qosh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]]
    await query.message.reply_text(
        "📍 *Yangi manzilni yuboring:*\n\n"
        "Tugmani bosing yoki xaritadan lokatsiya yuboring.",
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
        f"📌 [{label}]({maps_link})\n"
        f"🗺 Koordinatalar: `{lat:.6f}, {lon:.6f}`",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        disable_web_page_preview=True
    )
    return ConversationHandler.END


async def lokatsiya_tozala_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("✅ Ha, o'chirish", callback_data="lokatsiya_tozala_ha"),
            InlineKeyboardButton("❌ Yo'q", callback_data="lokatsiya_tozala_yoq"),
        ]
    ]
    await query.edit_message_text(
        "⚠️ *Barcha saqlangan manzillarni o'chirasizmi?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def lokatsiya_tozala_ha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    users = load_users()
    uid = str(user.id)
    if uid in users:
        users[uid]["lokatsiyalar"] = []
        save_users(users)

    await query.edit_message_text("🗑 *Barcha manzillar o'chirildi.*", parse_mode="Markdown")


async def lokatsiya_tozala_yoq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Bekor qilindi. Manzillar saqlanib qoldi.")


async def yordam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Yordam*\n\n"
        "📦 Buyurtma qilish: «Non buyurtma qilish» tugmasini bosing\n"
        "👤 Ma'lumotlarim: saqlangan raqam va manzillarni ko'rish\n"
        "📱 Telefon raqamingiz birinchi buyurtmadan keyin saqlanadi\n"
        "📍 Manzil qo'shish: «Mening ma'lumotlarim» → «Yangi lokatsiya qo'shish»\n\n"
        "Savollar uchun: @admin",
        parse_mode="Markdown"
    )


# ───────────────────────────────────────────────
# Buyurtma jarayoni
# ───────────────────────────────────────────────

async def buyurtma_boshlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for non_turi, narx in NON_TURLARI.items():
        keyboard.append([InlineKeyboardButton(f"{non_turi} — {narx:,} so'm", callback_data=f"non_{non_turi}")])
    await update.message.reply_text(
        "🍞 *Qaysi turdagi non kerak?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return NON_TURI


async def non_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    non_turi = query.data.replace("non_", "")
    context.user_data["non_turi"] = non_turi
    context.user_data["narx"] = NON_TURLARI[non_turi]
    await query.edit_message_text(
        f"✅ *{non_turi}* tanlandi!\n\n"
        f"💵 Narxi: {NON_TURLARI[non_turi]:,} so'm/dona\n\n"
        "🔢 *Nechtadan kerak?* (raqam kiriting, masalan: 3)",
        parse_mode="Markdown"
    )
    return NON_SONI


async def non_soni_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        soni = int(update.message.text.strip())
        if soni <= 0 or soni > 100:
            await update.message.reply_text("⚠️ Iltimos, 1 dan 100 gacha raqam kiriting.")
            return NON_SONI
    except ValueError:
        await update.message.reply_text("⚠️ Iltimos, faqat *raqam* kiriting.", parse_mode="Markdown")
        return NON_SONI

    context.user_data["soni"] = soni
    context.user_data["jami"] = context.user_data["narx"] * soni

    user = update.effective_user
    saved = get_user(user.id)

    # Telefon allaqachon saqlangan bo'lsa, o'tkazib yuborish
    if saved and saved.get("telefon"):
        context.user_data["telefon"] = saved["telefon"]
        context.user_data["skip_telefon"] = True

        lokatsiyalar = saved.get("lokatsiyalar", [])
        if lokatsiyalar:
            # Saqlangan manzillar mavjud — tanlash imkonini ber
            keyboard = []
            for i, loc in enumerate(lokatsiyalar):
                keyboard.append([InlineKeyboardButton(
                    f"📍 {loc['label']}",
                    callback_data=f"saved_loc_{i}"
                )])
            keyboard.append([InlineKeyboardButton("📍 Yangi lokatsiya yuborish", callback_data="yangi_loc")])

            jami = context.user_data["jami"]
            await update.message.reply_text(
                f"✅ *{soni} dona {context.user_data['non_turi']}*\n"
                f"💰 Jami: *{jami:,} so'm*\n\n"
                f"📱 Telefon: `{saved['telefon']}` *(saqlangan)*\n\n"
                "📍 *Qaysi manzilga yetkazish kerak?*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return LOKATSIYA
        else:
            # Telefon bor, lokatsiya yo'q
            keyboard = [[KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]]
            jami = context.user_data["jami"]
            await update.message.reply_text(
                f"✅ *{soni} dona {context.user_data['non_turi']}*\n"
                f"💰 Jami: *{jami:,} so'm*\n\n"
                f"📱 Telefon: `{saved['telefon']}` *(saqlangan)*\n\n"
                "📍 *Manzilingizni yuboring:*",
                parse_mode="Markdown",
                reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            )
            return LOKATSIYA
    else:
        # Yangi foydalanuvchi — telefon so'rash
        keyboard = [[KeyboardButton("📱 Telefon raqamimni yuborish", request_contact=True)]]
        jami = context.user_data["jami"]
        await update.message.reply_text(
            f"✅ *{soni} dona {context.user_data['non_turi']}*\n"
            f"💰 Jami: *{jami:,} so'm*\n\n"
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
    if "lokatsiyalar" not in saved:
        saved["lokatsiyalar"] = []
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
    """Saqlangan manzildan birini tanlash"""
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    idx = int(query.data.replace("saved_loc_", ""))
    saved = get_user(user.id)
    lokatsiya = saved["lokatsiyalar"][idx]

    context.user_data["lokatsiya"] = lokatsiya
    await query.edit_message_reply_markup(reply_markup=None)
    await _buyurtma_yuborish(update, context, lokatsiya["lat"], lokatsiya["lon"])
    return ConversationHandler.END


async def yangi_loc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yangi lokatsiya yuborish uchun tugma"""
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

    # Yangi lokatsiyani profilda saqlash
    saved = get_user(user.id) or {}
    saved.setdefault("lokatsiyalar", [])
    save_user(user.id, saved)
    add_user_location(user.id, lat, lon)

    await _buyurtma_yuborish(update, context, lat, lon)
    return ConversationHandler.END


async def _buyurtma_yuborish(update: Update, context: ContextTypes.DEFAULT_TYPE, lat: float, lon: float):
    """Buyurtmani mijozga va deliverchiga yuborish"""
    user = update.effective_user
    non_turi = context.user_data.get("non_turi")
    soni = context.user_data.get("soni")
    jami = context.user_data.get("jami")
    telefon = context.user_data.get("telefon")
    maps_link = f"https://maps.google.com/?q={lat},{lon}"

    keyboard = [[InlineKeyboardButton("📦 Yana buyurtma", callback_data="restart")]]

    # Callback query yoki oddiy message ekanligini tekshirish
    msg = update.callback_query.message if update.callback_query else update.message
    await msg.reply_text(
        "✅ *Buyurtmangiz qabul qilindi!*\n\n"
        f"🍞 {non_turi} — {soni} dona\n"
        f"💰 Jami: {jami:,} so'm\n\n"
        "🚚 Deliverchi tez orada bog'lanadi!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    deliverchi_xabar = (
        "🔔 *YANGI BUYURTMA!*\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"👤 Mijoz: {user.full_name}\n"
        f"📱 Telefon: `{telefon}`\n"
        f"🆔 Telegram ID: `{user.id}`\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"🍞 Mahsulot: {non_turi}\n"
        f"🔢 Soni: *{soni} dona*\n"
        f"💰 Jami: *{jami:,} so'm*\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"📍 [Xaritada ko'rish]({maps_link})\n"
        f"📌 Koordinatalar: `{lat:.6f}, {lon:.6f}`"
    )

    try:
        from telegram.ext import ContextTypes
        await context.bot.send_message(
            chat_id=DELIVERCHI_CHAT_ID,
            text=deliverchi_xabar,
            parse_mode="Markdown"
        )
        await context.bot.send_location(
            chat_id=DELIVERCHI_CHAT_ID,
            latitude=lat,
            longitude=lon
        )
    except Exception as e:
        logger.error(f"Deliverchiga yuborishda xatolik: {e}")

    context.user_data.clear()


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
    keyboard = []
    for non_turi, narx in NON_TURLARI.items():
        keyboard.append([InlineKeyboardButton(f"{non_turi} — {narx:,} so'm", callback_data=f"non_{non_turi}")])
    await query.edit_message_text(
        "🍞 *Qaysi turdagi non kerak?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return NON_TURI


# ───────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Lokatsiya qo'shish uchun alohida conversation
    lokatsiya_qosh_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(lokatsiya_qosh_callback, pattern="^lokatsiya_qosh$")],
        states={
            LOKATSIYA_YANGILASH: [
                MessageHandler(filters.LOCATION, lokatsiya_yangilash_qabul),
            ],
        },
        fallbacks=[CommandHandler("bekor", bekor_qilish)],
    )

    # Asosiy buyurtma conversation
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📦 Non buyurtma qilish$"), buyurtma_boshlash),
            CallbackQueryHandler(restart_callback, pattern="^restart$"),
        ],
        states={
            NON_TURI: [
                CallbackQueryHandler(non_tanlash, pattern="^non_"),
            ],
            NON_SONI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, non_soni_qabul),
            ],
            TELEFON: [
                MessageHandler(filters.CONTACT, telefon_qabul),
            ],
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
    app.add_handler(CallbackQueryHandler(lokatsiya_tozala_callback, pattern="^lokatsiya_tozala$"))
    app.add_handler(CallbackQueryHandler(lokatsiya_tozala_ha, pattern="^lokatsiya_tozala_ha$"))
    app.add_handler(CallbackQueryHandler(lokatsiya_tozala_yoq, pattern="^lokatsiya_tozala_yoq$"))

    logger.info("🤖 Non Dastavka Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
