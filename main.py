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
CHECKING_SUB, PLATFORM_MENU, SERVICE_MENU, PACKAGE_MENU, AWAITING_INPUT, CONFIRMATION, AWAITING_PROOF = range(7)

# --- Button Texts ---
BACK_BUTTON = "◀️ ተመለስ"
MAIN_EXIT_BUTTON = "🏠 ዋና መውጫ"

# --- Data (Prices and Packages) ---
PRICES = {
    "telegram": {
        "members": {"500": 120, "1000": 250, "3000": 600, "5000": 1050, "10000": 1800, "20000": 4500},
        "post view (1 last)": {"1000": 5, "5000": 25, "10000": 50, "50000": 100},
        "post view (5 last)": {"1000": 15, "5000": 30, "10000": 70, "50000": 300},
        "reaction (❤️)": {"500": 20, "1000": 40, "3000": 100, "5000": 150, "10000": 320},
        "reaction (👍)": {"500": 20, "1000": 40, "3000": 100, "5000": 150, "10000": 320},
        "reaction (🤣)": {"500": 25, "1000": 50, "3000": 120, "5000": 200, "10000": 400},
    },
    "tiktok": {
        "followers": {"500": 240, "1000": 450, "3000": 1500, "5000": 2000, "10000": 5000},
        "like": {"500": 70, "1000": 110, "3000": 170, "5000": 200, "10000": 270, "20000": 400},
        "video view": {"500": 30, "1000": 70, "3000": 120, "5000": 150, "10000": 200, "20000": 300},
    },
    "instagram": {
        "views": {"500": 40, "1000": 80, "3000": 120, "5000": 170, "10000": 220, "20000": 300, "40000": 500},
        "like": {"500": 60, "1000": 110, "3000": 300, "5000": 500, "10000": 900, "20000": 1900},
        "followers": {"500": 240, "1000": 450, "3000": 1500, "5000": 2000, "10000": 5000},
    },
    "youtube": {}
}

# --- Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log Errors caused by Updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)


# --- Helper Functions ---
async def is_user_subscribed(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except TelegramError:
        return False

# --- Start & Main Menu ---
async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
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
        return CHECKING_SUB
    return await start_bot(update, context)

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if await is_user_subscribed(query.from_user.id, context):
        await query.message.delete()
        return await start_bot(update, context)
    else:
        await query.answer("🤔 አሁንም ቻናሉን አልተቀላቀሉም።", show_alert=True)
        return CHECKING_SUB

async def platform_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    platform = update.message.text.lower().replace('🔵 ', '').replace('⚫️ ', '').replace('🔴 ', '').replace('🟣 ', '')
    
    if platform == "youtube":
        await update.message.reply_text("ይህ አገልግሎት በቅርቡ ይጀመራል። እባክዎ ሌላ ፕላትፎርም ይምረጡ።")
        return PLATFORM_MENU

    context.user_data['platform'] = platform
    
    keyboards = {
        "telegram": [
            [KeyboardButton("👍 Reaction"), KeyboardButton("🤣 reaction"), KeyboardButton("❤️ reaction")],
            [KeyboardButton("👁 Post View"), KeyboardButton("👁 5 last Posts")],
            [KeyboardButton("👥 members")],
            [KeyboardButton(BACK_BUTTON), KeyboardButton(MAIN_EXIT_BUTTON)]
        ],
        "tiktok": [
            [KeyboardButton("👥 Followers"), KeyboardButton("❤️ Likes")],
            [KeyboardButton("👁 Video Views"), KeyboardButton(BACK_BUTTON), KeyboardButton(MAIN_EXIT_BUTTON)]
        ],
        "instagram": [
            [KeyboardButton("👥 Followers"), KeyboardButton("❤️ Likes")],
            [KeyboardButton("👁 Views"), KeyboardButton(BACK_BUTTON), KeyboardButton(MAIN_EXIT_BUTTON)]
        ],
    }
    keyboard = keyboards.get(platform)
        
    await update.message.reply_text(f"✨ {platform.title()} выбрали.\n\nአሁን የሚፈልጉትን አገልግሎት ይምረጡ።",
                                     reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SERVICE_MENU

async def service_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    service_text = update.message.text
    normalized_text = service_text.lower()
    
    service_map = {
        # Telegram
        "👍 reaction": "reaction (👍)", "🤣 reaction": "reaction (🤣)", "❤️ reaction": "reaction (❤️)",
        "👁 post view": "post view (1 last)", "👁 5 last posts": "post view (5 last)", "👥 members": "members",
        # Instagram & TikTok
        "👥 followers": "followers", "❤️ likes": "like",
        "👁 views": "views", # Instagram specific
        "👁 video views": "video view", # TikTok specific
    }
    
    service = service_map.get(normalized_text)

    if not service:
        await update.message.reply_text("የተሳሳተ ምርጫ። እባክዎ እንደገና ይሞክሩ።")
        return SERVICE_MENU
        
    context.user_data['service'] = service
    context.user_data['service_text'] = service_text
    platform = context.user_data['platform']
    package_prices = PRICES.get(platform, {}).get(service, {})
    
    if not package_prices:
        await update.message.reply_text("ይቅርታ, ለዚህ አገልግሎት ፓኬጆች በቅርቡ ይዘጋጃሉ።")
        return SERVICE_MENU
    
    unit = "Items" # Default
    if "reaction" in service: unit = "Reactions"
    elif "view" in service: unit = "Views"
    elif service in ["members", "followers"]: unit = service.title()
    elif service == "like": unit = "Likes"

    keyboard = [[KeyboardButton(f"{amount} {unit} | {price} ETB")] for amount, price in package_prices.items()]
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

    # --- Custom Prompts Logic ---
    prompt = ""
    example = ""
    service_text = context.user_data.get('service_text', 'Items')

    if platform == "telegram":
        if service == "members":
            prompt = "🔗 Public የሆነ የቻናል ሊንክ ይላኩ"
            example = "ለምሳሌ:- https://t.me/skyFounders"
        else:
            prompt = f"🔗 {service_text} የሚጨመርበትን የTelegram Post link ያስገቡ❓"
            example = "ለምሳሌ: https://t.me/channel_name/123"
    elif platform == "tiktok":
        if service == "followers":
            prompt = "🔗 👥 Followers የሚጨመርበትን የ Tiktok Account username ያስገቡ❓"
            example = "ለምሳሌ: @username"
        elif service == "like":
            prompt = "🔗 የ Tik Tok like የሚጨመርበትን የvideo link ያስገቡ❓"
            example = "ለምሳሌ: https://vm.tiktok.com/..."
        elif service == "video view":
            prompt = "🔗 የTik Tok View የሚጨመርበትን የvideo link ያስገቡ❓"
            example = "ለምሳሌ: https://vm.tiktok.com/..."
    elif platform == "instagram":
        if service == "followers":
            prompt = "🔗 👥 Followers የሚጨመርበትን የ Instagram Account username ያስገቡ❓"
            example = "ለምሳሌ: @username"
        elif service == "like":
            prompt = "🔗 የinstagram like የሚጨመርበትን የvideo link ያስገቡ❓"
            example = "ለምሳሌ: https://www.instagram.com/p/..."
        elif service == "views":
            prompt = "🔗 የinstagram View የሚጨመርበትን የvideo link ያስገቡ❓"
            example = "ለምሳሌ: https://www.instagram.com/p/..."
    
    await update.message.reply_text(f"{prompt}\n\n{example}", reply_markup=ReplyKeyboardMarkup([[KeyboardButton(BACK_BUTTON)]], resize_keyboard=True))
    return AWAITING_INPUT

async def awaiting_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    platform = context.user_data['platform']
    service = context.user_data['service']
    
    error_message = ""

    # --- Validation Logic ---
    if platform == 'telegram':
        if not user_input.startswith(('http://t.me/', 'https://t.me/')):
            error_message = "⚠️ ትክክለኛ የቴሌግራም ሊንክ አላስገቡም። ሊንኩ በ https://t.me/ መጀመር አለበት።\n\nእባክዎ እንደገና ይሞክሩ።"
    
    elif platform == 'tiktok':
        if service == 'followers':
            if not user_input.startswith('@'):
                error_message = "⚠️ ትክክለኛ Username አላስገቡም። Username በ @ መጀመር አለበት።\n\nእባክዎ እንደገና ይሞክሩ።"
        elif service in ['like', 'video view']:
            if not user_input.startswith(('https://www.tiktok.com/', 'https://vm.tiktok.com/')):
                error_message = "⚠️ ትክክለኛ የTikTok ሊንክ አላስገቡም። ሊንኩ በ https://vm.tiktok.com/ ወይም https://www.tiktok.com/ መጀመር አለበት።\n\nእባክዎ እንደገና ይሞክሩ።"

    elif platform == 'instagram':
        if service == 'followers':
            if not user_input.startswith('@'):
                error_message = "⚠️ ትክክለኛ Username አላስገቡም። Username በ @ መጀመር አለበት።\n\nእባክዎ እንደገና ይሞክሩ።"
        elif service in ['like', 'views']:
            if not user_input.startswith('https://www.instagram.com/'):
                error_message = "⚠️ ትክክለኛ የInstagram ሊንክ አላስገቡም። ሊንኩ በ https://www.instagram.com/ መጀመር አለበት።\n\nእባክዎ እንደገና ይሞክሩ።"

    if error_message:
        await update.message.reply_text(error_message)
        return AWAITING_INPUT

    # --- If valid, continue ---
    context.user_data['user_input'] = user_input
    amount = context.user_data['amount']
    price = PRICES[platform][service][amount]
    service_text = context.user_data.get('service_text', service.title())
    
    input_type = "Post ሊንክ" if service != 'followers' else "Account"
    if platform == 'telegram' and service == 'members': input_type = "ቻናል ሊንክ"

    confirmation_text = (f"🔵 {platform.title()} | {service_text}\n\n"
                         f"👤 መጠን: {amount}\n"
                         f"🔗 {input_type}: {user_input}\n"
                         f"💸 ጠቅላላ ክፍያ: {price} ETB\n\n"
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
                    f"💰 **የሚከፍሉት የብር መጠን: {price} ETB**\n\n"
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
    
    platform = context.user_data.get('platform', 'N/A')
    service = context.user_data.get('service', 'N/A')
    service_text = context.user_data.get('service_text', service.title())
    amount = context.user_data.get('amount', 'N/A')
    price = PRICES.get(platform, {}).get(service, {}).get(amount, 'N/A')
    user_input = context.user_data.get('user_input', 'N/A')
    
    admin_notification = (f"🔔 **አዲስ የክፍያ ማረጋገጫ** 🔔\n\n"
                          f"👤 **ከ:** {user.mention_html()} (ID: `{user.id}`)\n"
                          f"🆔 **የትዕዛዝ ቁጥር:** {order_id}\n"
                          f"--- ትዕዛዝ --- \n"
                          f"📱 **አገልግሎት:** {platform.title()} - {service_text}\n"
                          f"🔢 **መጠን:** {amount}\n"
                          f"🔗 **ሊንክ/Username:** `{user_input}`\n"
                          f"💵 **ክፍያ:** {price} ETB")

    keyboard = [[InlineKeyboardButton("✅ ክፍያ ተረጋግጧል", callback_data=f"approve_{user.id}_{order_id}")],
                [InlineKeyboardButton("🚫 ክፍያ አልተፈጸመም", callback_data=f"reject_{user.id}_{order_id}_{user.username or user.first_name}")]]
    
    await context.bot.forward_message(chat_id=ADMIN_CHAT_ID, from_chat_id=user.id, message_id=update.message.message_id)
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_notification, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    await start_bot(update, context)
    return PLATFORM_MENU # Important: Return to a state in the conversation

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

# --- Back Button Handlers ---
async def back_to_platform_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await start_bot(update, context)

async def back_to_service_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    platform = context.user_data.get('platform')
    if not platform: return await start_bot(update, context)
    
    keyboards = {
        "telegram": [
            [KeyboardButton("👍 Reaction"), KeyboardButton("🤣 reaction"), KeyboardButton("❤️ reaction")],
            [KeyboardButton("👁 Post View"), KeyboardButton("👁 5 last Posts")],
            [KeyboardButton("👥 members")],
            [KeyboardButton(BACK_BUTTON), KeyboardButton(MAIN_EXIT_BUTTON)]
        ],
        "tiktok": [
            [KeyboardButton("👥 Followers"), KeyboardButton("❤️ Likes")],
            [KeyboardButton("👁 Video Views"), KeyboardButton(BACK_BUTTON), KeyboardButton(MAIN_EXIT_BUTTON)]
        ],
        "instagram": [
            [KeyboardButton("👥 Followers"), KeyboardButton("❤️ Likes")],
            [KeyboardButton("👁 Views"), KeyboardButton(BACK_BUTTON), KeyboardButton(MAIN_EXIT_BUTTON)]
        ],
    }
    keyboard = keyboards.get(platform)
    await update.message.reply_text(f"✨ {platform.title()} выбрали.\n\nአሁን የሚፈልጉትን አገልግሎት ይምረጡ።",
                                     reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return SERVICE_MENU


async def back_to_package_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    service_text = context.user_data.get('service_text')
    service = context.user_data.get('service')
    platform = context.user_data.get('platform')
    if not all([service_text, service, platform]): return await start_bot(update, context)
    
    package_prices = PRICES.get(platform, {}).get(service, {})
    
    unit = "Items" # Default
    if "reaction" in service: unit = "Reactions"
    elif "view" in service: unit = "Views"
    elif service in ["members", "followers"]: unit = service.title()
    elif service == "like": unit = "Likes"

    keyboard = [[KeyboardButton(f"{amount} {unit} | {price} ETB")] for amount, price in package_prices.items()]
    keyboard.append([KeyboardButton(BACK_BUTTON)])
    await update.message.reply_text(f"💖 {service_text} выбрали.\n\nየሚፈልጉትን ፓኬጅ ይምረጡ:",
                                     reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return PACKAGE_MENU


async def back_to_awaiting_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # This function regenerates the prompt for the link/username
    return await package_menu(update, context)


def main() -> None:
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        logger.error("FATAL: BOT_TOKEN or ADMIN_CHAT_ID environment variable not set.")
        return
        
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHECKING_SUB: [CallbackQueryHandler(check_subscription_callback, pattern="^check_subscription$")],
            PLATFORM_MENU: [MessageHandler(filters.Regex("^(🔵 Telegram|⚫️ TikTok|🔴 YouTube|🟣 Instagram)$"), platform_menu)],
            SERVICE_MENU: [
                MessageHandler(filters.Regex(f"^({BACK_BUTTON}|{MAIN_EXIT_BUTTON})$"), back_to_platform_menu), 
                MessageHandler(filters.TEXT & ~filters.COMMAND, service_menu)
            ],
            PACKAGE_MENU: [
                MessageHandler(filters.Regex(f"^{BACK_BUTTON}$"), back_to_service_menu), 
                MessageHandler(filters.TEXT & ~filters.COMMAND, package_menu)
            ],
            AWAITING_INPUT: [
                MessageHandler(filters.Regex(f"^{BACK_BUTTON}$"), back_to_package_menu), 
                MessageHandler(filters.TEXT & ~filters.COMMAND, awaiting_input)
            ],
            CONFIRMATION: [
                MessageHandler(filters.Regex(f"^{BACK_BUTTON}$"), back_to_awaiting_input), 
                MessageHandler(filters.Regex("^✅ አረጋግጥ$"), confirmation)
            ],
            AWAITING_PROOF: [MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), awaiting_proof)]
        },
        fallbacks=[CommandHandler('start', start)],
        persistent=False,
        name="main_conversation"
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(admin_handler, pattern="^(approve_|reject_)"))
    application.add_error_handler(error_handler)
    
    application.run_polling()

if __name__ == "__main__":
    main()
