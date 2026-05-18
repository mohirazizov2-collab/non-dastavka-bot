#!/usr/bin/env python3
"""
Non Dastavka Bot - Telegram bot for bread delivery orders
Mijoz non buyurtma qiladi, buyurtma deliverychiga yuboriladi
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

# Bot token
BOT_TOKEN = "8895387043:AAHLZ9romIgd-fR4gtpHX3fQ_lu9a5skTPU"

# ⚠️  DELIVERCHI TELEGRAM ID sini shu yerga kiriting!
# Deliverchining Telegram ID sini bilish uchun @userinfobot ga /start yuboring
DELIVERCHI_CHAT_ID = 123456789  # <-- BU YERNI O'ZGARTIRING!

# Conversation states
LOCATION, NON_SONI = range(2)

# Non turlari
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot boshlanganda"""
    user = update.effective_user
    keyboard = [
        [KeyboardButton("📦 Non buyurtma qilish")],
        [KeyboardButton("ℹ️ Yordam")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "🍞 *Non Dastavka Botiga xush kelibsiz!*\n\n"
        "Bu bot orqali siz non buyurtma berishingiz mumkin.\n"
        "Buyurtmangiz darhol deliverchiga yuboriladi.\n\n"
        "Buyurtma qilish uchun tugmani bosing 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def yordam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam"""
    await update.message.reply_text(
        "ℹ️ *Yordam*\n\n"
        "📦 *Buyurtma qilish:* «Non buyurtma qilish» tugmasini bosing\n"
        "📍 *Lokatsiya:* Joylashuvingizni yuboring\n"
        "🔢 *Soni:* Nechtadan non kerakligini kiriting\n\n"
        "Savollar uchun: @admin",
        parse_mode="Markdown"
    )


async def buyurtma_boshlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buyurtma jarayonini boshlash - non turini tanlash"""
    keyboard = []
    for non_turi in NON_TURLARI:
        narx = NON_TURLARI[non_turi]
        keyboard.append([InlineKeyboardButton(
            f"{non_turi} — {narx:,} so'm",
            callback_data=f"non_{non_turi}"
        )])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🍞 *Qaysi turdagi non kerak?*\n\nQuyidagilardan birini tanlang:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def non_tanlash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Non turi tanlanganda"""
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
    """Non soni kiritilganda"""
    try:
        soni = int(update.message.text.strip())
        if soni <= 0 or soni > 100:
            await update.message.reply_text("⚠️ Iltimos, 1 dan 100 gacha raqam kiriting.")
            return NON_SONI
    except ValueError:
        await update.message.reply_text("⚠️ Iltimos, faqat *raqam* kiriting (masalan: 3)", parse_mode="Markdown")
        return NON_SONI

    context.user_data["soni"] = soni
    narx = context.user_data["narx"]
    jami = narx * soni

    keyboard = [[KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"✅ *{soni} dona {context.user_data['non_turi']}*\n"
        f"💰 Jami: *{jami:,} so'm*\n\n"
        "📍 *Manzilingizni yuboring*\n"
        "«Lokatsiyamni yuborish» tugmasini bosing:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return LOCATION


async def lokatsiya_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lokatsiya qabul qilinganda"""
    location = update.message.location
    user = update.effective_user

    non_turi = context.user_data.get("non_turi", "Noma'lum")
    soni = context.user_data.get("soni", 0)
    narx = context.user_data.get("narx", 0)
    jami = narx * soni

    lat = location.latitude
    lon = location.longitude
    maps_link = f"https://maps.google.com/?q={lat},{lon}"

    # Mijozga tasdiqlash xabari
    keyboard = [[InlineKeyboardButton("📦 Yana buyurtma", callback_data="restart")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✅ *Buyurtmangiz qabul qilindi!*\n\n"
        f"🍞 Mahsulot: {non_turi}\n"
        f"🔢 Soni: {soni} dona\n"
        f"💰 Jami: {jami:,} so'm\n\n"
        "🚚 Deliverchi tez orada siz bilan bog'lanadi!",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    # Deliverchiga xabar yuborish
    deliverchi_xabar = (
        "🔔 *YANGI BUYURTMA!*\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"👤 Mijoz: {user.full_name}\n"
        f"📱 Username: @{user.username if user.username else 'yo\'q'}\n"
        f"🆔 ID: `{user.id}`\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"🍞 Mahsulot: {non_turi}\n"
        f"🔢 Soni: *{soni} dona*\n"
        f"💰 Jami: *{jami:,} so'm*\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"📍 [Xaritada ko'rish]({maps_link})\n"
        f"📌 Koordinatalar: `{lat:.6f}, {lon:.6f}`"
    )

    try:
        await context.bot.send_message(
            chat_id=DELIVERCHI_CHAT_ID,
            text=deliverchi_xabar,
            parse_mode="Markdown"
        )
        # Lokatsiyani ham yuborish
        await context.bot.send_location(
            chat_id=DELIVERCHI_CHAT_ID,
            latitude=lat,
            longitude=lon
        )
        logger.info(f"Buyurtma deliverchiga yuborildi: {user.id} -> {DELIVERCHI_CHAT_ID}")
    except Exception as e:
        logger.error(f"Deliverchiga yuborishda xatolik: {e}")
        await update.message.reply_text(
            "⚠️ Buyurtmangiz qabul qilindi, lekin deliverchiga yuborishda muammo bo'ldi. "
            "Iltimos, admin bilan bog'laning: @admin"
        )

    context.user_data.clear()
    return ConversationHandler.END


async def bekor_qilish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buyurtmani bekor qilish"""
    context.user_data.clear()
    keyboard = [
        [KeyboardButton("📦 Non buyurtma qilish")],
        [KeyboardButton("ℹ️ Yordam")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "❌ Buyurtma bekor qilindi.\n\nBoshqatdan boshlash uchun tugmani bosing.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


async def restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Qayta buyurtma"""
    query = update.callback_query
    await query.answer()
    await buyurtma_boshlash_callback(update, context)


async def buyurtma_boshlash_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for non_turi in NON_TURLARI:
        narx = NON_TURLARI[non_turi]
        keyboard.append([InlineKeyboardButton(
            f"{non_turi} — {narx:,} so'm",
            callback_data=f"non_{non_turi}"
        )])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(
        "🍞 *Qaysi turdagi non kerak?*\n\nQuyidagilardan birini tanlang:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


def main():
    """Botni ishga tushirish"""
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📦 Non buyurtma qilish$"), buyurtma_boshlash),
        ],
        states={
            NON_SONI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, non_soni_qabul),
                CallbackQueryHandler(non_tanlash, pattern="^non_"),
            ],
            LOCATION: [
                MessageHandler(filters.LOCATION, lokatsiya_qabul),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: u.message.reply_text(
                    "📍 Iltimos, «Lokatsiyamni yuborish» tugmasini bosing."
                )),
            ],
        },
        fallbacks=[
            CommandHandler("bekor", bekor_qilish),
            MessageHandler(filters.Regex("^❌ Bekor qilish$"), bekor_qilish),
        ],
    )

    # Handlerlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yordam", yordam))
    app.add_handler(CallbackQueryHandler(non_tanlash, pattern="^non_"))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Yordam$"), yordam))

    logger.info("🤖 Non Dastavka Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
