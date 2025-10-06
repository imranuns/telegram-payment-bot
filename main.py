# -*- coding: utf-8 -*-

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

# --- Basic Configuration ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Environment Variables ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
FORCE_SUB_CHANNEL = "@skyfounders"  # Your channel username is set here

# --- Conversation States ---
SELECTING_SERVICE, SELECTING_PLATFORM, SELECTING_PACKAGE, AWAITING_LINK, AWAITING_CONFIRMATION = range(5)
TIKTOK_MENU, TIKTOK_SELECT_PACKAGE, TIKTOK_AWAITING_USERNAME, TIKTOK_AWAITING_CONFIRMATION = range(5, 9)


# --- Data (Prices and Packages) ---
PRICES = {
    "telegram": {
        "reaction": {"500": 50, "1000": 100, "3000": 300, "5000": 500, "10000": 1000},
        "post_view": {"500": 15, "1000": 30, "5000": 150, "10000": 250, "20000": 480, "50000": 990, "100000": 1800},
    },
    "tiktok": {
        "followers": {"500": 350, "1000": 700, "3000": 2100, "5000": 3500, "10000": 7000},
        "like": {"500": 110, "1000": 220, "3000": 500, "5000": 700, "10000": 1400, "20000": 2800},
        "video_view": {"1000": 50, "5000": 250, "10000": 500}, # Example prices
    },
    "instagram": { # As per instruction, same as TikTok
        "followers": {"500": 350, "1000": 700, "3000": 2100, "5000": 3500, "10000": 7000},
        "like": {"500": 110, "1000": 220, "3000": 500, "5000": 700, "10000": 1400, "20000": 2800},
    }
}

BACK_BUTTON = "◀️ ተመለስ"
HOME_BUTTON = "🏠 ዋና መውጫ"

# --- Helper Functions ---
async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        return False

async def force_sub_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("✅ ቻናሉን ይቀላቀሉ", url=f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}")],
                [InlineKeyboardButton("🔄 አረጋግጥ", callback_data="check_subscription")]]
    await update.message.reply_text(
        f"👋 እንኳን በደህና መጡ!\n\nቦቱን ለመጠቀም እባክዎ መጀመሪያ ቻናላችንን ይቀላቀሉ።",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message_id=None):
    main_menu_keyboard = [
        [KeyboardButton("👥 Subscribers"), KeyboardButton("👍 Reaction")],
        [KeyboardButton("👁 Post View"), KeyboardButton("👤 የእኔ መረጃ")],
    ]
    reply_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)
    
    chat_id = update.effective_chat.id
    text = "🏠 ወደ ዋናው መውጫ ተመልሰዋል\n\n🔘ለመቀጠል ከስር ካሉት በተኑች ይንኩ"
    
    if message_id:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, reply_markup=reply_markup)
    else:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)

# --- Main Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_subscribed(user_id, context):
        await force_sub_handler(update, context)
        return

    await show_main_menu(update, context)

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_user_subscribed(user_id, context):
        await query.message.delete()
        await show_main_menu(update, context)
    else:
        await query.message.reply_text("🤔 አሁንም ቻናሉን አልተቀላቀሉም። እባክዎ መጀመሪያ ቻናሉን ይቀላቀሉ።")

# --- Service Selection Logic (Reaction, Post View, etc.) ---
async def service_selector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service_name = update.message.text.lower().replace('👍 ', '').replace('👁 ', '')
    context.user_data['service'] = service_name
    
    platforms = {
        'reaction': ["🔵 Telegram"],
        'post view': ["🔵 Telegram"],
        'subscribers': ["🔵 Telegram", "⚫️ TikTok", "🟣 Instagram"] # Assuming subscribers is also a choice
    }
    
    service_key = service_name.replace(' ', '_')
    if service_key not in PRICES['telegram']: # Simple check
         await update.message.reply_text("ይቅርታ, ይህ አገልግሎት አይገኝም።")
         return ConversationHandler.END

    keyboard = [[KeyboardButton(p)] for p in platforms.get(service_name, [])]
    keyboard.append([KeyboardButton(HOME_BUTTON)])
    
    await update.message.reply_text(
        f"✨ የመረጡት አገልግሎት: {update.message.text}!\n\nእባክዎ ፕላትፎርሙን ይምረጡ።",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return SELECTING_PACKAGE # We go to package selection as platform is mostly Telegram

async def show_packages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    platform_name = update.message.text.replace('🔵 ', '').replace('⚫️ ', '').replace('🟣 ', '').lower()
    service_name = context.user_data['service']
    
    context.user_data['platform'] = platform_name
    
    package_prices = PRICES.get(platform_name, {}).get(service_name.replace(' ', '_'), {})
    
    if not package_prices:
        await update.message.reply_text("ይቅርታ, ለዚህ ምርጫ ፓኬጆች አልተገኙም።")
        return ConversationHandler.END
        
    keyboard = []
    for amount, price in package_prices.items():
        keyboard.append([InlineKeyboardButton(f"{amount} {service_name.title()} | {price} ብር", callback_data=f"pkg_{amount}")])
    
    keyboard.append([InlineKeyboardButton(BACK_BUTTON, callback_data="back_to_platform_select"), InlineKeyboardButton(HOME_BUTTON, callback_data="go_home")])
    
    await update.message.reply_text(
        f"💖 የመረጡት: {service_name.title()}\n\nእባክዎ የሚፈልጉትን መጠን ይምረጡ።",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return AWAITING_LINK

async def ask_for_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    package_amount = query.data.split('_')[1]
    context.user_data['package_amount'] = package_amount

    service = context.user_data['service']
    platform = context.user_data['platform']
    
    prompt = ""
    example = ""
    if platform == "telegram":
        prompt = f"🔗 {package_amount} {service.title()} የሚጨመርበትን የTelegram Post link ያስገቡ❓"
        example = "ለምሳሌ: https://t.me/moonsmsinfo/2"
    elif platform in ["tiktok", "instagram"]:
        prompt = f"🔗 {package_amount} {service.title()} የሚጨመርበትን የ {platform.title()} Account username ያስገቡ❓"
        example = "ለምሳሌ: @funny_video100"

    await query.edit_message_text(f"{prompt}\n\n{example}")
    
    return AWAITING_CONFIRMATION

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text # This is the link or username
    context.user_data['user_input'] = user_input
    
    service = context.user_data['service']
    platform = context.user_data['platform']
    amount = context.user_data['package_amount']
    price = PRICES[platform][service.replace(' ', '_')][amount]
    
    confirmation_text = (
        f"🔵 {platform.title()} | {service.title()}\n\n"
        f"👤 መጠን: {amount} {service.title()}\n"
        f"🔗 Post ሊንክ: {user_input}\n"
        f"💸 ጠቅላላ ክፍያ: {price} ብር\n\n"
        f"♻️ ለመቀጠል ከፈለጉ ❮ ✅ አረጋግጥ ❯ የሚለውን በተን ይንኩ"
    )
    
    keyboard = [[InlineKeyboardButton("✅ አረጋግጥ", callback_data="final_confirm"), InlineKeyboardButton(BACK_BUTTON, callback_data="back_to_packages")]]
    
    await update.message.reply_text(confirmation_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END # End here for simplicity, can be extended

async def show_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    service = context.user_data.get('service', 'አገልግሎት')
    platform = context.user_data.get('platform', 'ፕላትፎርም')
    amount = context.user_data.get('package_amount', '0')
    price = PRICES.get(platform, {}).get(service.replace(' ', '_'), {}).get(amount, 0)
    link = context.user_data.get('user_input', 'ሊንክ')
    user = query.from_user

    payment_info = (
        f"ክፍያውን በሚከተለው የባንክ አካውንት ይፈጽሙ:\n\n"
        "🏦 **ባንክ:** የኢትዮጵያ ንግድ ባንክ\n"
        "📝 **ስም:** ዘሪሁን\n"
        "💳 **ቁጥር:** 0973961645\n\n"
        f"💰 የሚከፍሉት የብር መጠን: {price}\n\n"
        "ክፍያውን ከፈጸሙ በኋላ የደረሰኝ ፎቶ ወይም የትራንዛክሽን ቁጥር እዚህ ላይ ይላኩ።\n\n"
        "⚠️ ትዕዛዝዎ እስከሚጠናቀቅ ድረስ ከቦቱ መውጣትም ሆነ መረጃ ማጥፋት አይፈቀድም!"
    )
    
    await query.edit_message_text(payment_info, parse_mode='Markdown')
    # Here you'd transition to a state awaiting payment proof
    # For now, we will just send notification to admin
    
    admin_notification = (
        f"🔔 **አዲስ ትዕዛዝ** 🔔\n\n"
        f"👤 **ከ:** {user.mention_html()} (ID: `{user.id}`)\n"
        f"📱 **አገልግሎት:** {platform.title()} - {service.title()}\n"
        f"🔢 **መጠን:** {amount}\n"
        f"🔗 **ሊንክ/Username:** `{link}`\n"
        f"💵 **ክፍያ:** {price} ብር\n\n"
        "ተጠቃሚው የክፍያ መረጃ ገጽ ላይ ነው። ማረጋገጫ በመጠበቅ ላይ..."
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification, parse_mode='HTML')

# --- Other Menu Handlers ---
async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    info_text = (
        f"👤 **የእርስዎ መረጃ**\n\n"
        f"**ስም:** {user.full_name}\n"
        f"**Username:** @{user.username if user.username else 'የለም'}\n"
        f"**Telegram ID:** `{user.id}`"
    )
    await update.message.reply_text(info_text, parse_mode='Markdown')

async def go_home_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)
    return ConversationHandler.END
    
# --- Application Setup ---
def main() -> None:
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        logger.error("BOT_TOKEN or ADMIN_CHAT_ID not found in environment variables.")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Conversation handler for services like Reaction, Post View
    service_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^(👍 Reaction|👁 Post View|👥 Subscribers)$"), service_selector)],
        states={
            SELECTING_PACKAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, show_packages)],
            AWAITING_LINK: [CallbackQueryHandler(ask_for_link, pattern="^pkg_")],
            AWAITING_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
        },
        fallbacks=[
            MessageHandler(filters.Regex(f"^{HOME_BUTTON}$"), go_home_handler),
            # Add back handlers here
        ]
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    application.add_handler(CallbackQueryHandler(show_payment_info, pattern="^final_confirm$"))
    application.add_handler(MessageHandler(filters.Regex("^👤 የእኔ መረጃ$"), my_info))
    
    # Add the main conversation handler
    application.add_handler(service_conv_handler)
    
    # Must be the last handler
    application.add_handler(MessageHandler(filters.Regex(f"^{HOME_BUTTON}$"), go_home_handler))


    application.run_polling()

if __name__ == "__main__":
    main()

