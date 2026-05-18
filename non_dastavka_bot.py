#!/usr/bin/env python3
"""
Non Dastavka Bot - Mijoz non buyurtma qiladi, deliverychiga yuboriladi
"""
 
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
 
BOT_TOKEN = "8895387043:AAHLZ9romIgd-fR4gtpHX3fQ_lu9a5skTPU"
DELIVERCHI_CHAT_ID = 6514150973
 
# Conversation states
NON_TURI, NON_SONI, TELEFON, LOKATSIYA = range(4)
 
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
    keyboard = [
        [KeyboardButton("📦 Non buyurtma qilish")],
        [KeyboardButton("ℹ️ Yordam")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"Assalomu alaykum, {update.effective_user.first_name}! 👋\n\n"
        "🍞 *Non Dastavka Botiga xush kelibsiz!*\n\n"
        "Bot orqali non buyurtma bering — deliverchi yetkazib beradi.\n\n"
        "Buyurtma qilish uchun tugmani bosing 👇",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
 
 
async def yordam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Yordam*\n\n"
        "📦 Buyurtma qilish: «Non buyurtma qilish» tugmasini bosing\n"
        "📱 Telefon: raqamingizni yuboring\n"
        "📍 Lokatsiya: joylashuvingizni yuboring\n\n"
        "Savollar uchun: @admin",
        parse_mode="Markdown"
    )
 
 
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
    jami = context.user_data["narx"] * soni
    context.user_data["jami"] = jami
 
    keyboard = [[KeyboardButton("📱 Telefon raqamimni yuborish", request_contact=True)]]
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
 
    keyboard = [[KeyboardButton("📍 Lokatsiyamni yuborish", request_location=True)]]
    await update.message.reply_text(
        f"✅ Telefon: *{telefon}*\n\n"
        "📍 *Manzilingizni yuboring:*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return LOKATSIYA
 
 
async def lokatsiya_qabul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = update.message.location
    user = update.effective_user
 
    non_turi = context.user_data.get("non_turi")
    soni = context.user_data.get("soni")
    jami = context.user_data.get("jami")
    telefon = context.user_data.get("telefon")
    lat = location.latitude
    lon = location.longitude
    maps_link = f"https://maps.google.com/?q={lat},{lon}"
 
    keyboard = [[InlineKeyboardButton("📦 Yana buyurtma", callback_data="restart")]]
    await update.message.reply_text(
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
    return ConversationHandler.END
 
 
async def bekor_qilish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    keyboard = [
        [KeyboardButton("📦 Non buyurtma qilish")],
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
 
 
def main():
    app = Application.builder().token(BOT_TOKEN).build()
 
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
            ],
        },
        fallbacks=[
            CommandHandler("bekor", bekor_qilish),
            MessageHandler(filters.Regex("^❌ Bekor qilish$"), bekor_qilish),
        ],
    )
 
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("yordam", yordam))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Yordam$"), yordam))
 
    logger.info("🤖 Non Dastavka Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
 
 
if __name__ == "__main__":
    main()
