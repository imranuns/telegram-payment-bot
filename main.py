# -*- coding: utf-8 -*-

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
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

# --- የማዋቀሪያ መረጃዎች ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

# --- የኮንቨርሴሽን ደረጃዎች (አዲስ ደረጃ ተጨምሯል) ---
SELECTING_PLATFORM, SELECTING_PACKAGE, AWAITING_CONFIRMATION = range(3)

# --- የፓኬጅ መረጃዎች ---
PACKAGES = {
    "pkg_500": {"name": "500 Subscribers", "price": 150, "members": 500},
    "pkg_1000": {"name": "1000 Subscribers", "price": 290, "members": 1000},
    "pkg_3000": {"name": "3000 Subscribers", "price": 870, "members": 3000},
    "pkg_5000": {"name": "5000 Subscribers", "price": 1450, "members": 5000},
}

# --- የቦት ተግባራት ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ /start ትዕዛዝ ሲላክ የሚሰራ። የአገልግሎት አይነት ምርጫዎችን ያሳያል። """
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)

    # ልክ በ Screenshotu ላይ እንዳየነው አይነት ቁልፎች (ReplyKeyboardMarkup)
    keyboard = [
        [KeyboardButton("🔵 Telegram"), KeyboardButton("⚫️ TikTok")],
        [KeyboardButton("🔴 YouTube"), KeyboardButton("🟣 Instagram")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    welcome_message = (
        f"👋 ሰላም {user.mention_html()}!\n\n"
        "ወደ አገልግሎት መስጫ ቦታችን እንኳን በደህና መጡ።\n"
        "እባክዎ መጀመሪያ የአገልግሎት አይነት ይምረጡ።"
    )
    
    await update.message.reply_html(welcome_message, reply_markup=reply_markup)
    
    # ወደ መጀመሪያው የውይይት ደረጃ እንሸጋገራለን
    return SELECTING_PLATFORM

async def platform_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ ተጠቃሚው የአገልግሎት አይነት ሲመርጥ የሚሰራ። """
    user = update.message.from_user
    platform = update.message.text
    context.user_data['chosen_platform'] = platform
    logger.info(f"User {user.first_name} selected platform: {platform}")

    # የፓኬጅ ምርጫ ቁልፎችን እናዘጋጃለን
    package_keyboard = [
        [InlineKeyboardButton(f"{pkg['name']} - {pkg['price']} ብር", callback_data=key)]
        for key, pkg in PACKAGES.items()
    ]
    package_keyboard.append([InlineKeyboardButton("❌ ማቋረጥ", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(package_keyboard)

    message = f"✅ {platform} выбрали. \n\nአሁን የሚፈልጉትን የ Subscribers ፓኬጅ ይምረጡ።"
    
    # ከዚህ በፊት የነበሩትን የ ReplyKeyboard ቁልፎች እናጠፋና አዲሶቹን እንልካለን
    await update.message.reply_text(message, reply_markup=reply_markup)
    
    # ወደሚቀጥለው የፓኬጅ ምርጫ ደረጃ እንሸጋገራለን
    return SELECTING_PACKAGE


async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ ተጠቃሚው ፓኬጅ ሲመርጥ የሚሰራ። """
    query = update.callback_query
    await query.answer()
    
    package_key = query.data
    context.user_data['chosen_package'] = package_key
    package_info = PACKAGES[package_key]
    platform = context.user_data.get('chosen_platform', 'ያልተገለጸ')

    logger.info(f"User {query.from_user.first_name} selected package: {package_info['name']} for {platform}")

    payment_info = (
        f"✅ እርስዎ የመረጡት: {package_info['name']} ({platform})\n"
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
    """ ተጠቃሚው የክፍያ ማረጋገጫ ሲልክ የሚሰራ። """
    user = update.message.from_user
    chosen_package_key = context.user_data.get('chosen_package')
    
    if not chosen_package_key:
        await update.message.reply_text("እባክዎ መጀመሪያ ፓኬጅ ይምረጡ። ለመጀመር /start ይበሉ።", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    package_info = PACKAGES[chosen_package_key]
    platform = context.user_data.get('chosen_platform', 'ያልተገለጸ')
    
    user_message = (
        "🙏 እናመሰግናለን!\n\n"
        "የክፍያ ማረጋገጫዎ ደርሶናል። ጥያቄዎ በቀጣይ ደቂቃዎች ውስጥ ተረጋግጦ ምላሽ ይደርስዎታል።\n\n"
        "መልካም ቀን!"
    )
    await update.message.reply_text(user_message, reply_markup=ReplyKeyboardRemove())

    admin_notification = (
        "🔔 **አዲስ የክፍያ ማረጋገጫ** 🔔\n\n"
        f"👤 **ከ:** {user.mention_html()} (ID: `{user.id}`)\n"
        f"📱 **ፕላትፎርም:** {platform}\n"
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
    """ ተጠቃሚው ስራውን ሲያቋርጥ የሚሰራ። """
    user = update.effective_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("ሂደቱ ተቋርጧል። በፈለጉት ጊዜ እንደገና ለመጀመር /start ይበሉ።", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    """ ቦቱን ማስጀመር እና እንዲሰራ ማድረግ """
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        logger.error("አስፈላጊ የሆኑ ሚስጥራዊ መረጃዎች (BOT_TOKEN, ADMIN_CHAT_ID) አልተገኙም።")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_PLATFORM: [
                MessageHandler(filters.Regex('^(🔵 Telegram|⚫️ TikTok|🔴 YouTube|🟣 Instagram)$'), platform_selected)
            ],
            SELECTING_PACKAGE: [
                CallbackQueryHandler(select_package, pattern="^pkg_"),
            ],
            AWAITING_CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, payment_confirmation),
                MessageHandler(filters.PHOTO, payment_confirmation)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    application.run_polling()


if __name__ == "__main__":
    main()
