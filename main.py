# -*- coding: utf-8 -*-

import logging
import os
import random
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
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
PLATFORM_MENU, SERVICE_MENU, PACKAGE_MENU, AWAITING_INPUT, CONFIRMATION, AWAITING_PROOF = range(6)

# --- Button Texts ---
BACK_BUTTON = "◀️ ተመለስ"

# --- Data (Prices and Packages) ---
PRICES = {
    "telegram": {
        "reaction": {"500": 50, "1000": 100, "3000": 300, "5000": 500, "10000": 1000},
        "post view": {"500": 15, "1000": 30, "5000": 150, "10000": 250, "20000": 480, "50000": 990, "100000": 1800},
        "subscribers": {"500": 150, "1000": 290, "3000": 870, "5000": 1450},
    },
    "tiktok": {
        "followers": {"500": 350, "1000": 700, "3000": 2100, "5000": 3500, "10000": 7000},
        "like": {"500": 110, "1000": 220, "3000": 500, "5000": 700, "10000": 1400, "20000": 2800},
        "video view": {"1000": 50, "5000": 250, "10000": 500},
    },
    "instagram": {
        "followers": {"500": 350, "1000": 700, "3000": 2100, "5000": 3500, "10000": 7000},
        "like": {"500": 110, "1000": 220, "3000": 500, "5000": 700, "10000": 1400, "20000": 2800},
    },
    "youtube": {}
}

# --- Helper Functions ---
async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError:
        return False

# --- Start & Main Menu ---
async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [KeyboardButton("🔵 Telegram"), KeyboardButton("⚫️ TikTok")],
        [KeyboardButton("🔴 YouTube"), KeyboardButton("🟣 Instagram")]
    ]
    message = update.message or update.callback_query.message
    await message.reply_text(
        "👋 እንኳን በደህና መጡ!\n\nእባክዎ አገልግሎት የሚፈልጉበትን ፕላትፎርም ይምረጡ።",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return PLATFORM_MENU
    
# --- Main Conversation Flow ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if not await is_user_subscribed(user.id, context):
        keyboard = [[InlineKeyboardButton("✅ ቻናሉን ይቀላቀሉ", url=f"https://t.me/{FORCE_SUB_CHANNEL.lstrip('@')}")],
                    [InlineKeyboardButton("🔄 አረጋግጥ", callback_data="check_subscription")]]
        await update.message.reply_text(
            f"👋 እንኳን በደህና መጡ {user.mention_html()}!\n\nቦቱን ለመጠቀም እባክዎ መጀመሪያ ቻናላችንን ይቀላቀሉ።",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML'
        )
        return ConversationHandler.END
    return await start_bot(update, context)

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if await is_user_subscribed(query.from_user.id, context):
        await query.message.delete()
        keyboard = [
            [KeyboardButton("🔵 Telegram"), KeyboardButton("⚫️ TikTok")],
            [KeyboardButton("🔴 YouTube"), KeyboardButton("🟣 Instagram")]
        ]
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="👋 እንኳን በደህና መጡ!\n\nእባክዎ አገልግሎት የሚፈልጉበትን ፕላትፎርም ይምረጡ።",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return PLATFORM_MENU
    else:
        await query.message.reply_text("🤔 አሁንም ቻናሉን አልተቀላቀሉም።")
        return ConversationHandler.END

async def platform_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    platform = update.message.text.lower().replace('🔵 ', '').replace('⚫️ ', '').replace('🔴 ', '').replace('🟣 ', '')
    context.user_data['platform'] = platform
    
    keyboards = {
        "telegram": [[KeyboardButton("👍 Reaction"), KeyboardButton("👁 Post View")], [KeyboardButton("👥 Subscribers"), KeyboardButton(BACK_BUTTON)]],
        "tiktok": [[KeyboardButton("👥 Followers"), KeyboardButton("❤️ Like")], [KeyboardButton("👁 Video View"), KeyboardButton(BACK_BUTTON)]],
        "instagram": [[KeyboardButton("👥 Followers"), KeyboardButton("❤️ Like")], [KeyboardButton(BACK_BUTTON)]],
        "youtube": [[KeyboardButton(BACK_BUTTON)]]
    }
    keyboard = keyboards.get(platform)
    if not keyboard:
        await update.message.reply_text("ይህ አገልግሎት በቅርቡ ይጀመራል።")
        return PLATFORM_MENU
        
    await update.message.reply_text(f"✨ {platform.title()} выбрали.\n\nአሁን የሚፈልጉትን አገልግሎት ይምረጡ።",
                                     reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SERVICE_MENU

async def service_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    service_text = update.message.text
    service = service_text.lower().replace('👍 ', '').replace('👁 ', '').replace('👥 ', '').replace('❤️ ', '')
    context.user_data['service'] = service
    platform = context.user_data['platform']
    package_prices = PRICES.get(platform, {}).get(service, {})
    
    if not package_prices:
        await update.message.reply_text("ይቅርታ, ለዚህ አገልግሎት ፓኬጆች በቅርቡ ይዘጋጃሉ።")
        return SERVICE_MENU

    keyboard = [[KeyboardButton(f"{amount} {service.title()} | {price} ብር")] for amount, price in package_prices.items()]
    keyboard.append([KeyboardButton(BACK_BUTTON)])
    await update.message.reply_text(f"💖 {service_text} выбрали.\n\nየሚፈልጉትን ፓኬጅ ይምረጡ:",
                                     reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return PACKAGE_MENU

async def package_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        parts = update.message.text.split(' ')
        amount = parts[0]
        service = context.user_data['service']
        platform = context.user_data['platform']
        if amount not in PRICES[platform][service]:
            raise ValueError("Invalid package selected")
        context.user_data['amount'] = amount
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ የተሳሳተ ምርጫ። እባክዎ ከታች ካሉት ቁልፎች አንዱን ይምረጡ።")
        return PACKAGE_MENU

    prompt, example = "", ""
    if platform == "telegram":
        prompt = f"🔗 {amount} {service.title()} የሚጨመርበትን የTelegram Post link ያስገቡ❓"
        example = "ለምሳሌ: https://t.me/channel_name/123"
    else:
        prompt = f"🔗 {amount} {service.title()} የሚጨመርበትን የ {platform.title()} Account username ያስገቡ❓"
        example = "ለምሳሌ: @username"
    
    await update.message.reply_text(f"{prompt}\n\n{example}", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BACK_BUTTON)]], resize_keyboard=True))
    return AWAITING_INPUT

async def awaiting_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    platform = context.user_data['platform']
    
    if platform == 'telegram' and not user_input.startswith(('http://t.me/', 'https://t.me/')):
        await update.message.reply_text("⚠️ ትክክለኛ የቴሌግራም ሊንክ አላስገቡም። ሊንኩ በ https://t.me/ መጀመር አለበት።\n\nእባክዎ እንደገና ይሞክሩ።")
        return AWAITING_INPUT
    if platform in ['tiktok', 'instagram'] and not user_input.startswith('@'):
        await update.message.reply_text("⚠️ ትክክለኛ Username አላስገቡም። Username በ @ መጀመር አለበት።\n\nእባክዎ እንደገና ይሞክሩ።")
        return AWAITING_INPUT

    context.user_data['user_input'] = user_input
    service = context.user_data['service']
    amount = context.user_data['amount']
    price = PRICES[platform][service][amount]
    
    input_type = "Post ሊንክ" if platform == "telegram" else "Account"
    confirmation_text = (f"🔵 {platform.title()} | {service.title()}\n\n"
                         f"👤 መጠን: {amount} {service.title()}\n"
                         f"🔗 {input_type}: {user_input}\n"
                         f"💸 ጠቅላላ ክፍያ: {price} ብር\n\n"
                         f"♻️ ለመቀጠል ከፈለጉ ❮ ✅ አረጋግጥ ❯ የሚለውን በተን ይንኩ")
    keyboard = [[KeyboardButton("✅ አረጋግጥ"), KeyboardButton(BACK_BUTTON)]]
    await update.message.reply_text(confirmation_text, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return CONFIRMATION

async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price = PRICES[context.user_data['platform']][context.user_data['service']][context.user_data['amount']]
    payment_info = (f"🏦 **የባንክ መረጃዎች**\n\n"
                    f"- **የባንክ ስም:** CBE\n"
                    f"- **ስልክ ቁጥር:** 0973961645\n"
                    f"- **የአካውንት ስም:** Zerihun\n\n"
                    f"💰 **የሚከፍሉት የብር መጠን: {price}**\n\n"
                    f"🧾 የክፍያ ማረጋገጫ የላኩበትን Screenshot ወይም የትራንዛክሽን መረጃ እዚህ ጋር ይላኩ።")
    await update.message.reply_text(payment_info, parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
    return AWAITING_PROOF

async def awaiting_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    order_id = f"#ID{random.randint(10000, 99999)}"
    
    user_message = (f"✅ትዕዛዝዎ ተልዕኮል\n\n"
                    f"🆔የትዕዛዝ ቁጥር: {order_id}\n"
                    f"📯የትዕዛዝ ሁኔታ: ⏳በሂደት ላይ\n\n"
                    f"❗️ትዕዛዝዎ እንደተጠናቀቀ የማረጋገጫ መልዕክት ይደርሶታል")
    await update.message.reply_text(user_message)
    
    await start_bot(update, context)
    
    platform = context.user_data.get('platform', 'N/A')
    service = context.user_data.get('service', 'N/A')
    amount = context.user_data.get('amount', 'N/A')
    price = PRICES.get(platform, {}).get(service, {}).get(amount, 'N/A')
    user_input = context.user_data.get('user_input', 'N/A')
    
    admin_notification = (f"🔔 **አዲስ የክፍያ ማረጋገጫ** 🔔\n\n"
                          f"👤 **ከ:** {user.mention_html()} (ID: `{user.id}`)\n"
                          f"🆔 **የትዕዛዝ ቁጥር:** {order_id}\n"
                          f"--- ትዕዛዝ --- \n"
                          f"📱 **አገልግሎት:** {platform.title()} - {service.title()}\n"
                          f"🔢 **መጠን:** {amount}\n"
                          f"🔗 **ሊንክ/Username:** `{user_input}`\n"
                          f"💵 **ክፍያ:** {price} ብር")

    keyboard = [[InlineKeyboardButton("✅ ክፍያ ተረጋግጧል", callback_data=f"approve_{user.id}_{order_id}")],
                [InlineKeyboardButton("🚫 ክፍያ አልተፈጸመም", callback_data=f"reject_{user.id}_{order_id}_{user.username or user.first_name}")]]
    
    await context.bot.forward_message(chat_id=ADMIN_CHAT_ID, from_chat_id=user.id, message_id=update.message.message_id)
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    return ConversationHandler.END

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("ውሳኔዎ ተመዝግቧል።")
    
    action, user_id, order_id, *rest = query.data.split('_')
    user_id = int(user_id)
    username = rest[0] if rest else "User"

    if action == "approve":
        message_to_user = f"🎉 እንኳን ደስ አለዎት!\n\nየትዕዛዝ ቁጥር ({order_id}) በተሳካ ሁኔታ ተጠናቋል!"
        await context.bot.send_message(chat_id=user_id, text=message_to_user)
        await query.edit_message_text(text=f"{query.message.text}\n\n--- \n✅ ትዕዛዝ {order_id} ጸድቋል።")
    elif action == "reject":
        message_to_user = (f"👤 ውድ @{username}\n\n"
                           f"⚠️ባስገቡት የክፍያ ማረጋገጫ ምንም አይነት ክፍያ ስላልተፈጸመ order Id:- {order_id}\n\n"
                           f"🚫Cancel ተደርጓል እባክዎ እንደገና በትክክል ትዕዛዝ ይስጡ!")
        await context.bot.send_message(chat_id=user_id, text=message_to_user)
        await query.edit_message_text(text=f"{query.message.text}\n\n--- \n🚫 ትዕዛዝ {order_id} ውድቅ ተደርጓል።")

# --- Back Button Handlers for Correct Navigation ---

async def back_to_service_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Navigates back to the service selection menu by reconstructing the previous state."""
    platform = context.user_data.get('platform')
    
    if platform == 'telegram':
        update.message.text = "🔵 Telegram"
    elif platform == 'tiktok':
        update.message.text = "⚫️ TikTok"
    elif platform == 'instagram':
        update.message.text = "🟣 Instagram"
    elif platform == 'youtube':
        update.message.text = "🔴 YouTube"
    else:
        return await start_bot(update, context) # Fallback
        
    return await platform_menu(update, context)


async def back_to_package_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Navigates back to the package selection menu by reconstructing the previous state."""
    service = context.user_data.get('service')
    if service:
        service_map = {
            "reaction": "👍 Reaction", "post view": "👁 Post View", "subscribers": "👥 Subscribers",
            "followers": "👥 Followers", "like": "❤️ Like", "video view": "👁 Video View"
        }
        update.message.text = service_map.get(service, service)
    return await service_menu(update, context)


async def back_to_awaiting_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Navigates back to the user input prompt by reconstructing the previous state."""
    service = context.user_data.get('service')
    amount = context.user_data.get('amount')
    platform = context.user_data.get('platform')
    if all([service, amount, platform]):
        price = PRICES[platform][service][amount]
        update.message.text = f"{amount} {service.title()} | {price} ብር"
    return await package_menu(update, context)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PLATFORM_MENU: [MessageHandler(filters.Regex("^(🔵 Telegram|⚫️ TikTok|🔴 YouTube|🟣 Instagram)$"), platform_menu)],
            
            # **FIXED**: The generic text handlers now explicitly IGNORE the back button text,
            # ensuring the correct, specific handler for the back button is always used.
            SERVICE_MENU: [
                MessageHandler(filters.Regex(f"^{BACK_BUTTON}$"), start_bot), 
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(f"^{BACK_BUTTON}$"), service_menu)
            ],
            PACKAGE_MENU: [
                MessageHandler(filters.Regex(f"^{BACK_BUTTON}$"), back_to_service_menu), 
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(f"^{BACK_BUTTON}$"), package_menu)
            ],
            AWAITING_INPUT: [
                MessageHandler(filters.Regex(f"^{BACK_BUTTON}$"), back_to_package_menu), 
                MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex(f"^{BACK_BUTTON}$"), awaiting_input)
            ],
            CONFIRMATION: [
                MessageHandler(filters.Regex(f"^{BACK_BUTTON}$"), back_to_awaiting_input), 
                MessageHandler(filters.Regex("^✅ አረጋግጥ$"), confirmation)
            ],
            AWAITING_PROOF: [MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), awaiting_proof)]
        },
        fallbacks=[CommandHandler('start', start)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$"))
    application.add_handler(CallbackQueryHandler(admin_handler, pattern="^(approve_|reject_)"))
    
    application.run_polling()

if __name__ == "__main__":
    main()
