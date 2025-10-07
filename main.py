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
FORCE_SUB_CHANNEL = "@skyfounders"

# --- Conversation States ---
MAIN_MENU, PLATFORM_MENU, SERVICE_MENU, PACKAGE_MENU, AWAITING_INPUT, CONFIRMATION = range(6)

# --- Button Texts ---
BACK_BUTTON = "◀️ ተመለስ"
HOME_BUTTON = "🏠 ዋና መውጫ"

# --- Data (Prices and Packages) ---
PRICES = {
    "telegram": {
        "reaction": {"500": 50, "1000": 100, "3000": 300, "5000": 500, "10000": 1000},
        "post_view": {"500": 15, "1000": 30, "5000": 150, "10000": 250, "20000": 480, "50000": 990, "100000": 1800},
        "subscribers": {"500": 150, "1000": 290, "3000": 870, "5000": 1450}, # Example
    },
    "tiktok": {
        "followers": {"500": 350, "1000": 700, "3000": 2100, "5000": 3500, "10000": 7000},
        "like": {"500": 110, "1000": 220, "3000": 500, "5000": 700, "10000": 1400, "20000": 2800},
        "video_view": {"1000": 50, "5000": 250, "10000": 500}, # Example
    },
    "instagram": {
        "followers": {"500": 350, "1000": 700, "3000": 2100, "5000": 3500, "10000": 7000},
        "like": {"500": 110, "1000": 220, "3000": 500, "5000": 700, "10000": 1400, "20000": 2800},
    },
    "youtube": {} # Can be added later
}

# --- Helper Functions ---
async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if not await is_user_subscribed(user_id, context):
        keyboard = [[InlineKeyboardButton("✅ ቻናሉን ይቀላቀሉ", url=f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}")],
                    [InlineKeyboardButton("🔄 አረጋግጥ", callback_data="check_subscription")]]
        await update.message.reply_text(
            f"👋 እንኳን በደህና መጡ!\n\nቦቱን ለመጠቀም እባክዎ መጀመሪያ ቻናላችንን ይቀላቀሉ።",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END
    
    keyboard = [
        [KeyboardButton("🔵 Telegram"), KeyboardButton("⚫️ TikTok")],
        [KeyboardButton("🔴 YouTube"), KeyboardButton("🟣 Instagram")]
    ]
    await update.message.reply_text(
        "👋 እንኳን በደህና መጡ!\n\nእባክዎ አገልግሎት የሚፈልጉበትን ፕላትፎርም ይምረጡ።",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return PLATFORM_MENU

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if await is_user_subscribed(user_id, context):
        await query.message.delete()
        keyboard = [
            [KeyboardButton("🔵 Telegram"), KeyboardButton("⚫️ TikTok")],
            [KeyboardButton("🔴 YouTube"), KeyboardButton("🟣 Instagram")]
        ]
        await query.message.reply_text(
            "🎉 እናመሰግናለን! አሁን ቦቱን መጠቀም ይችላሉ።\n\nእባክዎ አገልግሎት የሚፈልጉበትን ፕላትፎርም ይምረጡ።",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return PLATFORM_MENU
    else:
        await query.message.reply_text("🤔 አሁንም ቻናሉን አልተቀላቀሉም። እባክዎ መጀመሪያ ቻናሉን ይቀላቀሉ።")
        return ConversationHandler.END

async def platform_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    platform = update.message.text.lower().split(" ")[1]
    context.user_data['platform'] = platform
    
    keyboards = {
        "telegram": [
            [KeyboardButton("👍 Reaction"), KeyboardButton("👁 Post View")],
            [KeyboardButton("👥 Subscribers"), KeyboardButton(BACK_BUTTON)],
        ],
        "tiktok": [
            [KeyboardButton("👥 Followers"), KeyboardButton("❤️ Like")],
            [KeyboardButton("👁 Video View"), KeyboardButton(BACK_BUTTON)],
        ],
        "instagram": [
            [KeyboardButton("👥 Followers"), KeyboardButton("❤️ Like")],
            [KeyboardButton(BACK_BUTTON)],
        ],
        "youtube": [[KeyboardButton(BACK_BUTTON)]]
    }
    
    keyboard = keyboards.get(platform, [[KeyboardButton(BACK_BUTTON)]])
    
    await update.message.reply_text(f"✨ {platform.title()} выбрали.\n\nአሁን የሚፈልጉትን አገልግሎት ይምረጡ።",
                                    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SERVICE_MENU

async def service_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    service = update.message.text.lower().replace('👍 ', '').replace('👁 ', '').replace('👥 ', '').replace('❤️ ', '')
    context.user_data['service'] = service
    platform = context.user_data['platform']
    
    package_prices = PRICES.get(platform, {}).get(service.replace(' ', '_'), {})
    
    if not package_prices:
        await update.message.reply_text("ይቅርታ, ለዚህ አገልግሎት ፓኬጆች በቅርቡ ይዘጋጃሉ።")
        return SERVICE_MENU # Stay on the same menu

    keyboard = []
    for amount, price in package_prices.items():
        keyboard.append([InlineKeyboardButton(f"{amount} {service.title()} | {price} ብር", callback_data=f"pkg_{amount}")])
    
    keyboard.append([InlineKeyboardButton(BACK_BUTTON, callback_data="back_to_platform")])
    
    await update.message.reply_text(f"💖 {service.title()} выбрали.\n\nየሚፈልጉትን ፓኬጅ ይምረጡ:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return PACKAGE_MENU

async def package_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_platform':
        platform = context.user_data.get('platform', 'telegram')
        keyboards = {
            "telegram": [
                [KeyboardButton("👍 Reaction"), KeyboardButton("👁 Post View")],
                [KeyboardButton("👥 Subscribers"), KeyboardButton(BACK_BUTTON)],
            ],
            "tiktok": [
                [KeyboardButton("👥 Followers"), KeyboardButton("❤️ Like")],
                [KeyboardButton("👁 Video View"), KeyboardButton(BACK_BUTTON)],
            ],
            "instagram": [
                [KeyboardButton("👥 Followers"), KeyboardButton("❤️ Like")],
                [KeyboardButton(BACK_BUTTON)],
            ],
            "youtube": [[KeyboardButton(BACK_BUTTON)]]
        }
        keyboard = keyboards.get(platform, [[KeyboardButton(BACK_BUTTON)]])
        await query.message.reply_text(f"✨ {platform.title()} выбрали.\n\nአሁን የሚፈልጉትን አገልግሎት ይምረጡ።",
                                        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
        return SERVICE_MENU

    amount = query.data.split('_')[1]
    context.user_data['amount'] = amount
    platform = context.user_data['platform']
    service = context.user_data['service']
    
    prompt = "የሚፈልጉትን ሊንክ ወይም Username ያስገቡ"
    example = ""
    
    if platform == "telegram":
        prompt = f"🔗 {amount} {service.title()} የሚጨመርበትን የTelegram Post link ያስገቡ❓"
        example = "ለምሳሌ: https://t.me/channel_name/123"
    elif platform in ["tiktok", "instagram"]:
        prompt = f"🔗 {amount} {service.title()} የሚጨመርበትን የ {platform.title()} Account username ያስገቡ❓"
        example = "ለምሳሌ: @username"
        
    await query.edit_message_text(f"{prompt}\n\n{example}")
    return AWAITING_INPUT

async def awaiting_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    context.user_data['user_input'] = user_input
    
    platform = context.user_data['platform']
    service = context.user_data['service']
    amount = context.user_data['amount']
    price = PRICES[platform][service.replace(' ', '_')][amount]
    
    input_type = "Post ሊንክ" if platform == "telegram" else "Account"
    
    confirmation_text = (
        f"🔵 {platform.title()} | {service.title()}\n\n"
        f"👤 መጠን: {amount} {service.title()}\n"
        f"🔗 {input_type}: {user_input}\n"
        f"💸 ጠቅላላ ክፍያ: {price} ብር\n\n"
        f"♻️ ለመቀጠል ከፈለጉ ❮ ✅ አረጋግጥ ❯ የሚለውን በተን ይንኩ"
    )
    keyboard = [[InlineKeyboardButton("✅ አረጋግጥ", callback_data="confirm"), InlineKeyboardButton(BACK_BUTTON, callback_data="back_to_packages")]]
    await update.message.reply_text(confirmation_text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRMATION
    
async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'back_to_packages':
        platform = context.user_data['platform']
        service = context.user_data['service']
        package_prices = PRICES.get(platform, {}).get(service.replace(' ', '_'), {})
        keyboard = []
        for amount, price in package_prices.items():
            keyboard.append([InlineKeyboardButton(f"{amount} {service.title()} | {price} ብር", callback_data=f"pkg_{amount}")])
        keyboard.append([InlineKeyboardButton(BACK_BUTTON, callback_data="back_to_platform")])
        await query.edit_message_text(f"💖 {service.title()} выбрали.\n\nየሚፈልጉትን ፓኬጅ ይምረጡ:",
                                        reply_markup=InlineKeyboardMarkup(keyboard))
        return PACKAGE_MENU

    price = PRICES[context.user_data['platform']][context.user_data['service'].replace(' ', '_')][context.user_data['amount']]
    
    payment_info = (
        f"🏦 **የባንክ መረጃዎች**\n\n"
        f"- **የባንክ ስም:** CBE\n"
        f"- **ስልክ ቁጥር:** 0973961645\n"
        f"- **የአካውንት ስም:** Zerihun\n\n"
        f"💰 **የሚከፍሉት የብር መጠን: {price}**\n\n"
        f"🧾 የክፍያ ማረጋገጫ የላኩበትን Screenshot እዚህ ጋር ይላኩ።"
    )
    await query.edit_message_text(payment_info, parse_mode='Markdown')
    # This state should ideally lead to awaiting for a photo/document
    return ConversationHandler.END # For now, we end here.

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$")],
        states={
            PLATFORM_MENU: [MessageHandler(filters.Regex("^(🔵 Telegram|⚫️ TikTok|🔴 YouTube|🟣 Instagram)$"), platform_menu)],
            SERVICE_MENU: [
                MessageHandler(filters.Regex(f"^{BACK_BUTTON}$"), start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, service_menu),
            ],
            PACKAGE_MENU: [CallbackQueryHandler(package_menu)],
            AWAITING_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, awaiting_input)],
            CONFIRMATION: [CallbackQueryHandler(confirmation)],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()


