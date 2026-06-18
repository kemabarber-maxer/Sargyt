import os
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
import httpx
import json

# Logging sazlamalary
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Çykyş üýtgeýjileri (Railway'de sazlanýar)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
MARZBAN_PANEL_URL = os.environ.get("MARZBAN_PANEL_URL", "https://luxuryy.turkmen-tagamlary.xyz:8443")
MARZBAN_ADMIN_USERNAME = os.environ.get("MARZBAN_ADMIN_USERNAME")
MARZBAN_ADMIN_PASSWORD = os.environ.get("MARZBAN_ADMIN_PASSWORD")
ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID")

# Dymyky sazlamalar
DEFAULT_DATA_LIMIT_GB = 125
DEFAULT_EXPIRE_DAYS = 30

# ConversationHandler ýagdaýlary
ASK_USERNAME = 1

# Marzban API Client
class MarzbanAPI:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token = None
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)

    async def get_token(self):
        """Marzban panelinden JWT token al"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/admin/token",
                data={
                    "username": self.username,
                    "password": self.password
                }
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("access_token")
            return self.token
        except Exception as e:
            logger.error(f"Token alma ýalňyşlygy: {e}")
            return None

    async def create_user(self, username, data_limit_gb=125, expire_days=30):
        """Täze ulanyjy döret"""
        if not self.token:
            await self.get_token()

        # Data limiti byte (125 GB)
        data_limit_bytes = data_limit_gb * 1024 * 1024 * 1024

        # Gutarýan senesi (timestamp)
        expire_timestamp = int((datetime.now() + timedelta(days=expire_days)).timestamp())

        user_data = {
            "username": username,
            "status": "active",
            "note": f"Telegram bot bilen döredildi - {datetime.now().strftime('%Y-%m-%d')}",
            "data_limit": data_limit_bytes,
            "expire": expire_timestamp,
            "data_limit_reset_strategy": "no_reset",
            "proxies": {
                "vless": {"id": ""},
                "shadowsocks": {"password": "", "method": "chacha20-ietf-poly1305"}
            },
            "inbounds": {
                "vless": ["VLESS TCP REALITY"],
                "shadowsocks": ["Shadowsocks TCP"]
            }
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/api/user",
                json=user_data,
                headers={"Authorization": f"Bearer {self.token}"}
            )

            if response.status_code == 401:
                # Token gutardy, täzeden al we gaýtadan synanş
                await self.get_token()
                response = await self.client.post(
                    f"{self.base_url}/api/user",
                    json=user_data,
                    headers={"Authorization": f"Bearer {self.token}"}
                )

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ulanyjy döretme ýalňyşlygy: {e}")
            return None

    async def get_user(self, username):
        """Ulanyjy maglumatlaryny getir"""
        if not self.token:
            await self.get_token()

        try:
            response = await self.client.get(
                f"{self.base_url}/api/user/{username}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ulanyjy getirme ýalňyşlygy: {e}")
            return None

    async def close(self):
        await self.client.aclose()

# Global Marzban client
marzban_client = None

def get_marzban_client():
    global marzban_client
    if marzban_client is None:
        marzban_client = MarzbanAPI(
            MARZBAN_PANEL_URL,
            MARZBAN_ADMIN_USERNAME,
            MARZBAN_ADMIN_PASSWORD
        )
    return marzban_client

# Admin barlagy
def is_admin(user_id):
    if ADMIN_TELEGRAM_ID:
        return str(user_id) == str(ADMIN_TELEGRAM_ID)
    return True  # Admin ID sazlanmadyk bolsa hemmä rugsat ber

# Buýruklar
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("⛔ Bu bota giriş rugsadyňyz ýok.")
        return

    welcome_text = f"""
👋 Salam {user.first_name}!

🤖 **Marzban VPN Boty**

Bu bot bilen awtomatiki usulda VPN ulanyjylary döredip bilersiňiz.

📋 **Buýruklar:**
• `/create` - Täze ulanyjy döret
• `/status` - Bot ýagdaýyny barla
• `/help` - Kömek menýusy

⚙️ **Dymyky Sazlamalar:**
• 📊 Data Limit: {DEFAULT_DATA_LIMIT_GB} GB
• ⏰ Wagt: {DEFAULT_EXPIRE_DAYS} gün
"""

    keyboard = [
        [InlineKeyboardButton("➕ Täze Ulanyjy Döret", callback_data="create_user")],
        [InlineKeyboardButton("📊 Ýagdaý Barla", callback_data="check_status")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Bu bota giriş rugsadyňyz ýok.")
        return

    help_text = """
📖 **Kömek Menýusy**

**Buýruklar:**
• `/start` - Boty başlat
• `/create` - Täze VPN ulanyjysy döret
• `/status` - Bot we panel baglanyşyk ýagdaýyny barla
• `/help` - Bu kömek menýusy

**Ulanyjy Döretme:**
1. `/create` buýrugyny iberiň
2. Ulanyjy adyny ýazyň
3. Bot awtomatiki ulanyjyny döreder

**Awtomatiki Sazlamalar:**
• Data Limit: 125 GB
• Wagt: 30 gün
• Protokollar: VLESS, Shadowsocks
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Bu bota giriş rugsadyňyz ýok.")
        return

    status_message = await update.message.reply_text("🔄 Panel baglanyşygy barlanýar...")

    try:
        client = get_marzban_client()
        token = await client.get_token()

        if token:
            await status_message.edit_text(
                "✅ **Bot Ýagdaýy: Aktiw**\n\n"
                "🟢 Telegram Bot: Bagly\n"
                "🟢 Marzban Panel: Bagly\n"
                f"🔗 Panel URL: `{MARZBAN_PANEL_URL}`\n"
                f"👤 Admin: `{MARZBAN_ADMIN_USERNAME}`",
                parse_mode="Markdown"
            )
        else:
            await status_message.edit_text(
                "⚠️ **Bot Ýagdaýy: Bölekçe Aktiw**\n\n"
                "🟢 Telegram Bot: Bagly\n"
                "🔴 Marzban Panel: Baglanyşyk Ýalňyşlygy\n"
                "Admin maglumatlaryny barlaň.",
                parse_mode="Markdown"
            )
    except Exception as e:
        await status_message.edit_text(
            f"❌ **Ýalňyşlyk:**\n`{str(e)}`",
            parse_mode="Markdown"
        )

# Söhbet: Ulanyjy döretme
async def create_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Bu bota giriş rugsadyňyz ýok.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 **Täze Ulanyjy Döretme**\n\n"
        "Ulanyjy adyny ýazyň:\n"
        "(Mysal: `ahmet123`, `user_2024`)\n\n"
        "Ýatyrmak üçin `/cancel` ýazyň.",
        parse_mode="Markdown"
    )
    return ASK_USERNAME

async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()

    # Ulanyjy ady barlagy
    if not username or " " in username or len(username) < 3:
        await update.message.reply_text(
            "⚠️ Nädogry ulanyjy ady!\n"
            "Iň az 3 harp, boşluk bolmaly däl.\n"
            "Gaýtadan synanyşyň ýa-da `/cancel` bilen ýatyryň."
        )
        return ASK_USERNAME

    processing_msg = await update.message.reply_text(
        f"⏳ `{username}` üçin ulanyjy döredilýär...",
        parse_mode="Markdown"
    )

    try:
        client = get_marzban_client()

        # Öň ulanyjynyň bar bolýan-olmadygyny barla
        existing_user = await client.get_user(username)
        if existing_user:
            await processing_msg.edit_text(
                f"⚠️ **`{username}`** atly ulanyjy eýýäm bar!\n"
                "Başga ulanyjy adyny synanyşyň.",
                parse_mode="Markdown"
            )
            return ASK_USERNAME

        # Ulanyjy döret
        result = await client.create_user(
            username=username,
            data_limit_gb=DEFAULT_DATA_LIMIT_GB,
            expire_days=DEFAULT_EXPIRE_DAYS
        )

        if result:
            # Ulanyjy maglumatlaryny al
            user_info = await client.get_user(username)

            if user_info:
                subscription_url = user_info.get("subscription_url", "")
                links = user_info.get("links", [])

                # Gutarýan senesi
                expire_timestamp = user_info.get("expire", 0)
                expire_date = datetime.fromtimestamp(expire_timestamp).strftime("%Y-%m-%d %H:%M") if expire_timestamp else "Näbelli"

                # Data limit
                data_limit = user_info.get("data_limit", 0)
                data_limit_gb = round(data_limit / (1024**3), 2) if data_limit else 0

                # Habar döret
                message = f"""
✅ **Ulanyjy Üstünlikli Döredildi!**

👤 **Ulanyjy Ady:** `{username}`
📊 **Data Limit:** {data_limit_gb} GB
⏰ **Gutarýan Sene:** {expire_date}
📱 **Ýagdaýy:** Aktiw

🔗 **Abunalyk Linki:**
`{subscription_url}`

📋 **Konfigurasiýa Linkleri:**
"""
                for i, link in enumerate(links[:5], 1):
                    message += f"\n`{link}`"

                if len(links) > 5:
                    message += f"\n\n...we {len(links) - 5} sany beýleki"

                message += "\n\n💡 **Nädip Ulanylýar?**\n"
                message += "1. V2RayNG, Nekoray ýa-da meňzeş programma ýükläň\n"
                message += "2. Abunalyk linkini ýa-da konfigurasiýa linklerini programa goşuň\n"
                message += "3. Baglanyň we ulanmaga başlaň!"

                await processing_msg.edit_text(message, parse_mode="Markdown")
            else:
                await processing_msg.edit_text(
                    f"✅ Ulanyjy `{username}` döredildi!\n"
                    "Emma jikme-jiklikleri alanda ýalňyşlyk boldy.",
                    parse_mode="Markdown"
                )
        else:
            await processing_msg.edit_text(
                "❌ Ulanyjy döredilende ýalňyşlyk boldy!\n"
                "Panel baglanyşygyny we admin maglumatlaryny barlaň."
            )

    except Exception as e:
        logger.error(f"Ulanyjy döretme ýalňyşlygy: {e}")
        await processing_msg.edit_text(
            f"❌ **Ýalňyşlyk:**\n`{str(e)}`\n\n"
            "Gaýtadan synanyşyň."
        )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Amal ýatyryldy.")
    return ConversationHandler.END

# Callback işleýjiler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("⛔ Bu bota giriş rugsadyňyz ýok.")
        return

    if query.data == "create_user":
        await query.edit_message_text(
            "📝 **Täze Ulanyjy Döretme**\n\n"
            "Ulanyjy adyny ýazyň:\n"
            "(Mysal: `ahmet123`)\n\n"
            "Ýatyrmak üçin `/cancel`",
            parse_mode="Markdown"
        )
        return ASK_USERNAME

    elif query.data == "check_status":
        try:
            client = get_marzban_client()
            token = await client.get_token()

            if token:
                await query.edit_message_text(
                    "✅ **Bot Ýagdaýy: Aktiw**\n\n"
                    "🟢 Telegram Bot: Bagly\n"
                    "🟢 Marzban Panel: Bagly",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    "⚠️ Panel baglanyşygy gurulyp bilmedi.",
                    parse_mode="Markdown"
                )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ýalňyşlyk: `{str(e)}`",
                parse_mode="Markdown"
            )

# Ýalňyşlyk tutuşy
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} ýalňyşlyk döretdi {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Ýalňyşlyk boldy. Gaýtadan synanyşyň."
        )

def main():
    # Token barlagy
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN çykyş üýtgeýjisi sazlanmady!")
        return

    if not MARZBAN_ADMIN_USERNAME or not MARZBAN_ADMIN_PASSWORD:
        logger.error("MARZBAN_ADMIN_USERNAME we MARZBAN_ADMIN_PASSWORD sazlanmady!")
        return

    # Bot programmasyny döret
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("create", create_user_start),
            CallbackQueryHandler(button_callback, pattern="^create_user$")
        ],
        states={
            ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Işleýjiler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^check_status$"))
    application.add_error_handler(error_handler)

    logger.info("Bot başladylýar...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
