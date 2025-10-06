import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError

# --- የማዋቀሪያ መረጃዎች (Configuration) ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ሚስጥራዊ መረጃዎችን ከ Environment Variables እናነባለን
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
# ⚠️ ይህንን ቻናል መቀየር አለብህ!
# የቻናልህን username ከ @ ምልክቱ ጋር አስገባ (ለምሳሌ '@mychannel')
# ቻናሉ Public መሆን አለበት፤ ቦትህ ደግሞ የቻናሉ Admin መሆን አለበት።
FORCE_SUB_CHANNEL = "@skyfounders" 

# --- የኮንቨርሴሽን ደረጃዎች ---
SELECTING_PLATFORM, SELECTING_PACKAGE, AWAITING_CONFIRMATION = range(3)

# --- የፓኬጅ መረጃዎች ---
PACKAGES = {
    "pkg_500": {"name": "500 Subscribers", "price": 150, "members": 500},
    "pkg_1000": {"name": "1000 Subscribers", "price": 290, "members": 1000},
    "pkg_3000": {"name": "3000 Subscribers", "price": 870, "members": 3000},
    "pkg_5000": {"name": "5000 Subscribers", "price": 1450, "members": 5000},
}

# --- Force Subscribe ተግባር ---
async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """ ተጠቃሚው ቻናሉን መቀላቀሉን ያረጋግጣል """
    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        return False # ስህተት ካጋጠመ፣ እንዳልተቀላቀለ እንቆጥራለን

# --- ዋና ምናሌ (Main Menu) ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ ዋናውን ሜኑ ያሳያል """
    user_id = update.effective_user.id
    if not await is_user_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("✅ ቻናሉን ይቀላቀሉ", url=f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}")],
                    [InlineKeyboardButton("🔄 አረጋግጥ", callback_data="check_subscription")]]
        await update.message.reply_text(
            f"👋 እንኳን በደህና መጡ!\n\nቦቱን ለመጠቀም እባክዎ መጀመሪያ ቻናላችንን ይቀላቀሉ።",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    main_menu_keyboard = [
        [KeyboardButton("👥 Subscribers"), KeyboardButton("👍 Reaction")],
        [KeyboardButton("👁 Post View"), KeyboardButton("👤 የእኔ መረጃ")],
    ]
    reply_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)
    await update.message.reply_text("👇 እባክዎ ከምናሌው ይምረጡ:", reply_markup=reply_markup)

# --- የቦት ትዕዛዛት እና ተግባራት ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /start ትዕዛዝ ሲላክ የሚሰራ """
    await show_main_menu(update, context)

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ "አረጋግጥ" የሚለውን ቁልፍ ሲጫኑ የሚሰራ """
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_user_subscribed(user_id, context):
        await query.message.delete()  # "ቻናሉን ተቀላቀል" የሚለውን መልዕክት ያጠፋዋል
        # አሁን ዋናውን ሜኑ እናሳያለን
        main_menu_keyboard = [
            [KeyboardButton("👥 Subscribers"), KeyboardButton("👍 Reaction")],
            [KeyboardButton("👁 Post View"), KeyboardButton("👤 የእኔ መረጃ")],
        ]
        reply_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)
        await query.message.reply_text("🎉 እናመሰግናለን! አሁን ቦቱን መጠቀም ይችላሉ።\n\n👇 እባክዎ ከምናሌው ይምረጡ:", reply_markup=reply_markup)
    else:
        await query.message.reply_text("🤔 አሁንም ቻናሉን አልተቀላቀሉም። እባክዎ መጀመሪያ ቻናሉን ይቀላቀሉ።")

# --- Subscribers Conversation ---
async def subscribers_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ "Subscribers" የሚለውን ሲጫኑ የሚጀምር """
    keyboard = [
        [KeyboardButton("🔵 Telegram"), KeyboardButton("⚫️ TikTok")],
        [KeyboardButton("🔴 YouTube"), KeyboardButton("🟣 Instagram")],
        [KeyboardButton("🏠 ወደ ዋናው ሜኑ")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("እባክዎ የአገልግሎት አይነት ይምረጡ:", reply_markup=reply_markup)
    return SELECTING_PLATFORM

async def platform_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    platform = update.message.text
    context.user_data['chosen_platform'] = platform
    logger.info(f"User {user.first_name} selected platform: {platform}")

    package_keyboard = [
        [InlineKeyboardButton(f"{pkg['name']} - {pkg['price']} ብር", callback_data=key)]
        for key, pkg in PACKAGES.items()
    ]
    package_keyboard.append([InlineKeyboardButton("❌ ማቋረጥ", callback_data="cancel_package_selection")])
    reply_markup = InlineKeyboardMarkup(package_keyboard)
    
    await update.message.reply_text(f"✅ {platform} выбрали. \n\nአሁን የሚፈልጉትን ፓኬጅ ይምረጡ።", reply_markup=reply_markup)
    return SELECTING_PACKAGE

async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    package_key = query.data
    context.user_data['chosen_package'] = package_key
    package_info = PACKAGES[package_key]
    platform = context.user_data.get('chosen_platform', 'ያልተገለጸ')
    payment_info = (
        f"✅ እርስዎ የመረጡት: {package_info['name']} ({platform})\n"
        f"💰 የሚከፍሉት: {package_info['price']} ብር\n\n"
        "ክፍያውን በሚከተለው የባንክ አካውንት ይፈጽሙ:\n\n"
        "🏦 **ባንክ:** የኢትዮጵያ ንግድ ባንክ\n"
        "📝 **ስም:** ዘሪሁን\n"
        "💳 **ቁጥር:** 1000123456789\n\n"
        "ክፍያውን ከፈጸሙ በኋላ የደረሰኝ ፎቶ ወይም የትራንዛክሽን ቁጥር እዚህ ላይ ይላኩ።"
    )
    await query.edit_message_text(text=payment_info, parse_mode='Markdown')
    return AWAITING_CONFIRMATION

async def payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    package_info = PACKAGES[context.user_data['chosen_package']]
    platform = context.user_data.get('chosen_platform', 'ያልተገለጸ')
    
    await update.message.reply_text(
        "🙏 እናመሰግናለን!\n\nየክፍያ ማረጋገጫዎ ደርሶናል። በቀጣይ ደቂቃዎች ውስጥ ምላሽ ይደርስዎታል።"
    )
    
    admin_notification = (
        f"🔔 **አዲስ የክፍያ ማረጋገጫ** 🔔\n\n"
        f"👤 **ከ:** {user.mention_html()} (ID: `{user.id}`)\n"
        f"📱 **ፕላትፎርም:** {platform}\n"
        f"📦 **ፓኬጅ:** {package_info['name']}\n"
        f"💵 **መጠን:** {package_info['price']} ብር\n\n"
        "እባክዎ የተላከውን ማረጋገጫ ይመልከቱ።"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification, parse_mode='HTML')
    await context.bot.forward_message(chat_id=ADMIN_CHAT_ID, from_chat_id=user.id, message_id=update.message.message_id)
    
    await show_main_menu(update, context) # ተጠቃሚውን ወደ ዋናው ሜኑ ይመልሳል
    return ConversationHandler.END

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await show_main_menu(update, context)
    return ConversationHandler.END
    
async def cancel_package_selection_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="የፓኬጅ ምርጫው ተቋርጧል።")
    await show_main_menu(query, context) # This needs update.message to work, so we have to call it separately
    # Since query doesn't have a direct .message attribute with full update capabilities, we send a new message.
    await context.bot.send_message(chat_id=update.effective_chat.id, text="👇 እባክዎ ከምናሌው ይምረጡ:", reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton("👥 Subscribers"), KeyboardButton("👍 Reaction")],
        [KeyboardButton("👁 Post View"), KeyboardButton("👤 የእኔ መረጃ")],
    ], resize_keyboard=True))
    
    return ConversationHandler.END

# --- ሌሎች የሜኑ ተግባራት ---
async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    info_text = (
        f"👤 **የእርስዎ መረጃ**\n\n"
        f"**ስም:** {user.full_name}\n"
        f"**Username:** @{user.username if user.username else 'የለም'}\n"
        f"**Telegram ID:** `{user.id}`"
    )
    await update.message.reply_text(info_text, parse_mode='Markdown')

async def coming_soon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 ይህ አገልግሎት በዝግጅት ላይ ነው። በቅርቡ ይጠብቁን!")

# --- ዋናው የማስጀመሪያ ተግባር ---
def main() -> None:
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        logger.error("አስፈላጊ ሚስጥራዊ መረጃዎች (BOT_TOKEN, ADMIN_CHAT_ID) አልተገኙም።")
        return
    if not FORCE_SUB_CHANNEL:
        logger.error("FORCE_SUB_CHANNEL አልተገለጸም። እባክዎ በኮዱ ውስጥ ያስተካክሉ።")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Subscribers conversation handler
    subscribers_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^👥 Subscribers$"), subscribers_start)],
        states={
            SELECTING_PLATFORM: [MessageHandler(filters.Regex("^(🔵 Telegram|⚫️ TikTok|🔴 YouTube|🟣 Instagram)$"), platform_selected)],
            SELECTING_PACKAGE: [CallbackQueryHandler(select_package, pattern="^pkg_")],
            AWAITING_CONFIRMATION: [MessageHandler(filters.TEXT | filters.PHOTO, payment_confirmation)],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^🏠 ወደ ዋናው ሜኑ$"), back_to_main_menu),
            CallbackQueryHandler(cancel_package_selection_inline, pattern="^cancel_package_selection$")
        ],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    application.add_handler(subscribers_conv_handler)
    application.add_handler(MessageHandler(filters.Regex("^👤 የእኔ መረጃ$"), my_info))
    application.add_handler(MessageHandler(filters.Regex("^(👍 Reaction|👁 Post View)$"), coming_soon))

    application.run_polling()

if __name__ == "__main__":
    main()
```

### በጣም ወሳኝ ማስተካከያ!

ከላይ ባለው ኮድ ውስጥ፣ መስመር 23 ላይ፣ የኔን የቻናል ስም አስገብቻለሁ። አንተ **የራስህን የቻናል username ማስገባት አለብህ።**
```python
# መስመር 23
FORCE_SUB_CHANNEL = "@skyfounders" # ⚠️ ይህንን በራስህ ቻናል ቀይረው!
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import TelegramError

# --- የማዋቀሪያ መረጃዎች (Configuration) ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ሚስጥራዊ መረጃዎችን ከ Environment Variables እናነባለን
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
# ⚠️ ይህንን ቻናል መቀየር አለብህ!
# የቻናልህን username ከ @ ምልክቱ ጋር አስገባ (ለምሳሌ '@mychannel')
# ቻናሉ Public መሆን አለበት፤ ቦትህ ደግሞ የቻናሉ Admin መሆን አለበት።
FORCE_SUB_CHANNEL = "@skyfounders" 

# --- የኮንቨርሴሽን ደረጃዎች ---
SELECTING_PLATFORM, SELECTING_PACKAGE, AWAITING_CONFIRMATION = range(3)

# --- የፓኬጅ መረጃዎች ---
PACKAGES = {
    "pkg_500": {"name": "500 Subscribers", "price": 150, "members": 500},
    "pkg_1000": {"name": "1000 Subscribers", "price": 290, "members": 1000},
    "pkg_3000": {"name": "3000 Subscribers", "price": 870, "members": 3000},
    "pkg_5000": {"name": "5000 Subscribers", "price": 1450, "members": 5000},
}

# --- Force Subscribe ተግባር ---
async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """ ተጠቃሚው ቻናሉን መቀላቀሉን ያረጋግጣል """
    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        return False # ስህተት ካጋጠመ፣ እንዳልተቀላቀለ እንቆጥራለን

# --- ዋና ምናሌ (Main Menu) ---
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ ዋናውን ሜኑ ያሳያል """
    user_id = update.effective_user.id
    if not await is_user_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("✅ ቻናሉን ይቀላቀሉ", url=f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}")],
                    [InlineKeyboardButton("🔄 አረጋግጥ", callback_data="check_subscription")]]
        await update.message.reply_text(
            f"👋 እንኳን በደህና መጡ!\n\nቦቱን ለመጠቀም እባክዎ መጀመሪያ ቻናላችንን ይቀላቀሉ።",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    main_menu_keyboard = [
        [KeyboardButton("👥 Subscribers"), KeyboardButton("👍 Reaction")],
        [KeyboardButton("👁 Post View"), KeyboardButton("👤 የእኔ መረጃ")],
    ]
    reply_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)
    await update.message.reply_text("👇 እባክዎ ከምናሌው ይምረጡ:", reply_markup=reply_markup)

# --- የቦት ትዕዛዛት እና ተግባራት ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /start ትዕዛዝ ሲላክ የሚሰራ """
    await show_main_menu(update, context)

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ "አረጋግጥ" የሚለውን ቁልፍ ሲጫኑ የሚሰራ """
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_user_subscribed(user_id, context):
        await query.message.delete()  # "ቻናሉን ተቀላቀል" የሚለውን መልዕክት ያጠፋዋል
        # አሁን ዋናውን ሜኑ እናሳያለን
        main_menu_keyboard = [
            [KeyboardButton("👥 Subscribers"), KeyboardButton("👍 Reaction")],
            [KeyboardButton("👁 Post View"), KeyboardButton("👤 የእኔ መረጃ")],
        ]
        reply_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)
        await query.message.reply_text("🎉 እናመሰግናለን! አሁን ቦቱን መጠቀም ይችላሉ።\n\n👇 እባክዎ ከምናሌው ይምረጡ:", reply_markup=reply_markup)
    else:
        await query.message.reply_text("🤔 አሁንም ቻናሉን አልተቀላቀሉም። እባክዎ መጀመሪያ ቻናሉን ይቀላቀሉ።")

# --- Subscribers Conversation ---
async def subscribers_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ "Subscribers" የሚለውን ሲጫኑ የሚጀምር """
    keyboard = [
        [KeyboardButton("🔵 Telegram"), KeyboardButton("⚫️ TikTok")],
        [KeyboardButton("🔴 YouTube"), KeyboardButton("🟣 Instagram")],
        [KeyboardButton("🏠 ወደ ዋናው ሜኑ")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("እባክዎ የአገልግሎት አይነት ይምረጡ:", reply_markup=reply_markup)
    return SELECTING_PLATFORM

async def platform_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    platform = update.message.text
    context.user_data['chosen_platform'] = platform
    logger.info(f"User {user.first_name} selected platform: {platform}")

    package_keyboard = [
        [InlineKeyboardButton(f"{pkg['name']} - {pkg['price']} ብር", callback_data=key)]
        for key, pkg in PACKAGES.items()
    ]
    package_keyboard.append([InlineKeyboardButton("❌ ማቋረጥ", callback_data="cancel_package_selection")])
    reply_markup = InlineKeyboardMarkup(package_keyboard)
    
    await update.message.reply_text(f"✅ {platform} выбрали. \n\nአሁን የሚፈልጉትን ፓኬጅ ይምረጡ።", reply_markup=reply_markup)
    return SELECTING_PACKAGE

async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    package_key = query.data
    context.user_data['chosen_package'] = package_key
    package_info = PACKAGES[package_key]
    platform = context.user_data.get('chosen_platform', 'ያልተገለጸ')
    payment_info = (
        f"✅ እርስዎ የመረጡት: {package_info['name']} ({platform})\n"
        f"💰 የሚከፍሉት: {package_info['price']} ብር\n\n"
        "ክፍያውን በሚከተለው የባንክ አካውንት ይፈጽሙ:\n\n"
        "🏦 **ባንክ:** የኢትዮጵያ ንግድ ባንክ\n"
        "📝 **ስም:** ዘሪሁን\n"
        "💳 **ቁጥር:** 1000123456789\n\n"
        "ክፍያውን ከፈጸሙ በኋላ የደረሰኝ ፎቶ ወይም የትራንዛክሽን ቁጥር እዚህ ላይ ይላኩ።"
    )
    await query.edit_message_text(text=payment_info, parse_mode='Markdown')
    return AWAITING_CONFIRMATION

async def payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    package_info = PACKAGES[context.user_data['chosen_package']]
    platform = context.user_data.get('chosen_platform', 'ያልተገለጸ')
    
    await update.message.reply_text(
        "🙏 እናመሰግናለን!\n\nየክፍያ ማረጋገጫዎ ደርሶናል። በቀጣይ ደቂቃዎች ውስጥ ምላሽ ይደርስዎታል።"
    )
    
    admin_notification = (
        f"🔔 **አዲስ የክፍያ ማረጋገጫ** 🔔\n\n"
        f"👤 **ከ:** {user.mention_html()} (ID: `{user.id}`)\n"
        f"📱 **ፕላትፎርም:** {platform}\n"
        f"📦 **ፓኬጅ:** {package_info['name']}\n"
        f"💵 **መጠን:** {package_info['price']} ብር\n\n"
        "እባክዎ የተላከውን ማረጋገጫ ይመልከቱ።"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification, parse_mode='HTML')
    await context.bot.forward_message(chat_id=ADMIN_CHAT_ID, from_chat_id=user.id, message_id=update.message.message_id)
    
    await show_main_menu(update, context) # ተጠቃሚውን ወደ ዋናው ሜኑ ይመልሳል
    return ConversationHandler.END

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await show_main_menu(update, context)
    return ConversationHandler.END
    
async def cancel_package_selection_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="የፓኬጅ ምርጫው ተቋርጧል።")
    await show_main_menu(query, context) # This needs update.message to work, so we have to call it separately
    # Since query doesn't have a direct .message attribute with full update capabilities, we send a new message.
    await context.bot.send_message(chat_id=update.effective_chat.id, text="👇 እባክዎ ከምናሌው ይምረጡ:", reply_markup=ReplyKeyboardMarkup([
        [KeyboardButton("👥 Subscribers"), KeyboardButton("👍 Reaction")],
        [KeyboardButton("👁 Post View"), KeyboardButton("👤 የእኔ መረጃ")],
    ], resize_keyboard=True))
    
    return ConversationHandler.END

# --- ሌሎች የሜኑ ተግባራት ---
async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    info_text = (
        f"👤 **የእርስዎ መረጃ**\n\n"
        f"**ስም:** {user.full_name}\n"
        f"**Username:** @{user.username if user.username else 'የለም'}\n"
        f"**Telegram ID:** `{user.id}`"
    )
    await update.message.reply_text(info_text, parse_mode='Markdown')

async def coming_soon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🙏 ይህ አገልግሎት በዝግጅት ላይ ነው። በቅርቡ ይጠብቁን!")

# --- ዋናው የማስጀመሪያ ተግባር ---
def main() -> None:
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        logger.error("አስፈላጊ ሚስጥራዊ መረጃዎች (BOT_TOKEN, ADMIN_CHAT_ID) አልተገኙም።")
        return
    if not FORCE_SUB_CHANNEL:
        logger.error("FORCE_SUB_CHANNEL አልተገለጸም። እባክዎ በኮዱ ውስጥ ያስተካክሉ።")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Subscribers conversation handler
    subscribers_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^👥 Subscribers$"), subscribers_start)],
        states={
            SELECTING_PLATFORM: [MessageHandler(filters.Regex("^(🔵 Telegram|⚫️ TikTok|🔴 YouTube|🟣 Instagram)$"), platform_selected)],
            SELECTING_PACKAGE: [CallbackQueryHandler(select_package, pattern="^pkg_")],
            AWAITING_CONFIRMATION: [MessageHandler(filters.TEXT | filters.PHOTO, payment_confirmation)],
        },
        fallbacks=[
            MessageHandler(filters.Regex("^🏠 ወደ ዋናው ሜኑ$"), back_to_main_menu),
            CallbackQueryHandler(cancel_package_selection_inline, pattern="^cancel_package_selection$")
        ],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    application.add_handler(subscribers_conv_handler)
    application.add_handler(MessageHandler(filters.Regex("^👤 የእኔ መረጃ$"), my_info))
    application.add_handler(MessageHandler(filters.Regex("^(👍 Reaction|👁 Post View)$"), coming_soon))

    application.run_polling()

if __name__ == "__main__":
    main()
```

### በጣም ወሳኝ ማስተካከያ!

ከላይ ባለው ኮድ ውስጥ፣ መስመር 23 ላይ፣ የኔን የቻናል ስም አስገብቻለሁ። አንተ **የራስህን የቻናል username ማስገባት አለብህ።**
```python
# መስመር 23
FORCE_SUB_CHANNEL = "@Skyfounders" # ⚠️ ይህንን በራስህ ቻናል ቀይረው!


