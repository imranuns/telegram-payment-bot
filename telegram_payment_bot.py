# -*- coding: utf-8 -*-

import logging
import os  # <-- ይሄ ሚስጥራዊ መረጃዎችን ከአካባቢው ለማንበብ ታክሏል
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ሎጊንግን ማዋቀር
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- የማዋቀሪያ መረጃዎች (Configuration) ---
# ሚስጥራዊ መረጃዎችን ከ Environment Variables እናነባለን
# Pella.app ላይ ስናስቀምጣቸው እናዋቅራቸዋለን
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

# --- የኮንቨርሴሽን ደረጃዎች ---
SELECTING_PACKAGE, AWAITING_CONFIRMATION = range(2)

# --- የፓኬጅ መረጃዎች ---
PACKAGES = {
    "pkg_500": {"name": "500 Subscribers", "price": 150, "members": 500},
    "pkg_1000": {"name": "1000 Subscribers", "price": 290, "members": 1000},
    "pkg_3000": {"name": "3000 Subscribers", "price": 870, "members": 3000},
    "pkg_5000": {"name": "5000 Subscribers", "price": 1450, "members": 5000},
}

# --- የቦት ተግባራት ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    keyboard = [
        [InlineKeyboardButton(f"{pkg['name']} - {pkg['price']} ብር", callback_data=key)]
        for key, pkg in PACKAGES.items()
    ]
    keyboard.append([InlineKeyboardButton("❌ ማቋረጥ", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_message = (
        f"👋 ሰላም {user.mention_html()}!\n\n"
        "ወደ አገልግሎት መስጫ ቦታችን እንኳን በደህና መጡ።\n"
        "የሚፈልጉትን የ Subscribers ፓኬጅ ይምረጡ።"
    )
    await update.message.reply_html(welcome_message, reply_markup=reply_markup)
    return SELECTING_PACKAGE

async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    package_key = query.data
    context.user_data['chosen_package'] = package_key
    package_info = PACKAGES[package_key]
    logger.info(f"User {query.from_user.first_name} selected package: {package_info['name']}")
    payment_info = (
        f"✅ እርስዎ የመረጡት: {package_info['name']}\n"
        f"💰 የሚከፍሉት: {package_info['price']} ብር\n\n"
        "እባክዎ ክፍያውን በሚከተለው የባንክ አካውንት ይፈጽሙ:\n\n"
        "🏦 **ባንክ:** የኢትዮጵያ ንግድ ባንክ\n"
        "📝 **ስም:** ዘሪሁን\n"
        "💳 **ቁጥር:** 1000123456789\n\n"
        "ክፍያውን ከፈጸሙ በኋላ የደረሰኝ ፎቶ ወይም የትራንዛክሽን ቁጥር (Transaction ID) እዚህ ላይ ይላኩ።"
    )
    await query.edit_message_text(text=payment_info, parse_mode='Markdown')
    return AWAITING_CONFIRMATION

async def payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    chosen_package_key = context.user_data.get('chosen_package')
    if not chosen_package_key:
        await update.message.reply_text("እባክዎ መጀመሪያ ፓኬጅ ይምረጡ። ለመጀመር /start ይበሉ።")
        return ConversationHandler.END
    package_info = PACKAGES[chosen_package_key]
    user_message = (
        "🙏 እናመሰግናለን!\n\n"
        "የክፍያ ማረጋገጫዎ ደርሶናል። ጥያቄዎ በቀጣይ ደቂቃዎች ውስጥ ተረጋግጦ ምላሽ ይደርስዎታል።\n\n"
        "መልካም ቀን!"
    )
    await update.message.reply_text(user_message)
    admin_notification = (
        "🔔 **አዲስ የክፍያ ማረጋገጫ** 🔔\n\n"
        f"👤 **ከ:** {user.mention_html()} (ID: `{user.id}`)\n"
        f"📦 **የተመረጠ ፓኬጅ:** {package_info['name']}\n"
        f"💵 **የክፍያ መጠን:** {package_info['price']} ብር\n\n"
        "እባክዎ የተላከውን ማረጋገጫ በማየት አገልግሎቱን ይስጡ።"
    )
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_notification,
        parse_mode='HTML'
    )
    if update.message.photo:
        await context.bot.forward_message(chat_id=ADMIN_CHAT_ID, from_chat_id=user.id, message_id=update.message.message_id)
    elif update.message.text:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"**የተጠቃሚው ማረጋገጫ ጽሁፍ:**\n`{update.message.text}`", parse_mode='Markdown')
    logger.info(f"Confirmation received from {user.first_name}. Notified admin.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user = query.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await query.edit_message_text(text="ሂደቱ ተቋርጧል። በፈለጉት ጊዜ እንደገና ለመጀመር /start ይበሉ።")
    return ConversationHandler.END

def main() -> None:
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        logger.error("አስፈላጊ የሆኑ ሚስጥራዊ መረጃዎች (BOT_TOKEN, ADMIN_CHAT_ID) አልተገኙም። እባክዎ ያረጋግጡ።")
        return

    application = Application.builder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_PACKAGE: [
                CallbackQueryHandler(select_package, pattern="^pkg_"),
                CallbackQueryHandler(cancel, pattern="^cancel$")
            ],
            AWAITING_CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, payment_confirmation),
                MessageHandler(filters.PHOTO, payment_confirmation)
            ],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(cancel, pattern="^cancel$")],
    )
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
