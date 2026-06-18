import os
import logging
import sys
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

# Logging sazlamalary
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Cikis utgeyjileri
TELEGRAM_BOT_TOKEN = os.environ.get("8761065175:AAHcSfuX2SSu1x4cJCGcAVAnwgNmzjTHhXU")
MARZBAN_PANEL_URL = os.environ.get("MARZBAN_PANEL_URL", "https://luxuryy.turkmen-tagamlary.xyz:8443/chacakdyaie/ajehaishsel/#/")
MARZBAN_ADMIN_USERNAME = os.environ.get("kema87")
MARZBAN_ADMIN_PASSWORD = os.environ.get("frost")
ADMIN_TELEGRAM_ID = os.environ.get("8216327129")

# Dymyky sazlamalar
DEFAULT_DATA_LIMIT_GB = 125
DEFAULT_EXPIRE_DAYS = 30

ASK_USERNAME = 1


class MarzbanAPI:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token = None
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)

    async def get_token(self):
        try:
            response = await self.client.post(
                f"{self.base_url}/api/admin/token",
                data={"username": self.username, "password": self.password}
            )
            response.raise_for_status()
            data = response.json()
            self.token = data.get("access_token")
            return self.token
        except Exception as e:
            logger.error(f"Token alma yalnyshlygy: {e}")
            return None

    async def create_user(self, username, data_limit_gb=125, expire_days=30):
        if not self.token:
            await self.get_token()

        data_limit_bytes = data_limit_gb * 1024 * 1024 * 1024
        expire_timestamp = int((datetime.now() + timedelta(days=expire_days)).timestamp())

        user_data = {
            "username": username,
            "status": "active",
            "note": f"Telegram bot bilen doredildi - {datetime.now().strftime('%Y-%m-%d')}",
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
                await self.get_token()
                response = await self.client.post(
                    f"{self.base_url}/api/user",
                    json=user_data,
                    headers={"Authorization": f"Bearer {self.token}"}
                )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ulanyjy doretme yalnyshlygy: {e}")
            return None

    async def get_user(self, username):
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
            logger.error(f"Ulanyjy getirme yalnyshlygy: {e}")
            return None

    async def close(self):
        await self.client.aclose()


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


def is_admin(user_id):
    if ADMIN_TELEGRAM_ID:
        return str(user_id) == str(ADMIN_TELEGRAM_ID)
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("Bu bota girish rugsadyňyz yok.")
        return

    welcome_text = (
        f"Salam {user.first_name}!\n\n"
        f"Marzban VPN Boty\n\n"
        f"Bu bot bilen awtomatik usulda VPN ulanyjylary doredip bilersiňiz.\n\n"
        f"Buyruklar:\n"
        f"• /create - Teze ulanyjy doret\n"
        f"• /status - Bot yagdayyny barla\n"
        f"• /help - Komek menyusy\n\n"
        f"Dymyky Sazlamalar:\n"
        f"• Data Limit: {DEFAULT_DATA_LIMIT_GB} GB\n"
        f"• Wagt: {DEFAULT_EXPIRE_DAYS} gun"
    )
    keyboard = [
        [InlineKeyboardButton("Teze Ulanyjy Doret", callback_data="create_user")],
        [InlineKeyboardButton("Yagday Barla", callback_data="check_status")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Bu bota girish rugsadyňyz yok.")
        return

    help_text = (
        "Komek Menyusy\n\n"
        "Buyruklar:\n"
        "• /start - Boty bashlat\n"
        "• /create - Teze VPN ulanyjysy doret\n"
        "• /status - Bot we panel baglanyshyk yagdayyny barla\n"
        "• /help - Bu komek menyusy\n\n"
        "Ulanyjy Doretme:\n"
        "1. /create buyrugyny iberiň\n"
        "2. Ulanyjy adyny yazyn\n"
        "3. Bot awtomatik ulanyjyny doreder\n\n"
        "Awtomatik Sazlamalar:\n"
        "• Data Limit: 125 GB\n"
        "• Wagt: 30 gun\n"
        "• Protokollar: VLESS, Shadowsocks"
    )
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Bu bota girish rugsadyňyz yok.")
        return

    status_message = await update.message.reply_text("Panel baglanyshygy barlanyar...")

    try:
        client = get_marzban_client()
        token = await client.get_token()
        if token:
            msg = (
                "Bot Yagdayy: Aktiv\n\n"
                "Telegram Bot: Bagly\n"
                "Marzban Panel: Bagly\n"
                f"Panel URL: {MARZBAN_PANEL_URL}\n"
                f"Admin: {MARZBAN_ADMIN_USERNAME}"
            )
            await status_message.edit_text(msg)
        else:
            await status_message.edit_text(
                "Bot Yagdayy: Bolekce Aktiv\n\n"
                "Telegram Bot: Bagly\n"
                "Marzban Panel: Baglanyshyk Yalnyshlygy\n"
                "Admin maglumatlaryny barlan."
            )
    except Exception as e:
        await status_message.edit_text(f"Yalnyshlyk: {str(e)}")


async def create_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Bu bota girish rugsadyňyz yok.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Teze Ulanyjy Doretme\n\n"
        "Ulanyjy adyny yazyn:\n"
        "(Mysal: ahmet123, user_2024)\n\n"
        "Yatyrmak ucin /cancel yazyn."
    )
    return ASK_USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip()

    if not username or " " in username or len(username) < 3:
        await update.message.reply_text(
            "Nadogry ulanyjy ady!\n"
            "In az 3 harp, boshluk bolmaly dal.\n"
            "Gaytadan synanyshyn ya-da /cancel bilen yatyr."
        )
        return ASK_USERNAME

    processing_msg = await update.message.reply_text(
        f"{username} ucin ulanyjy doredilyar..."
    )

    try:
        client = get_marzban_client()
        existing_user = await client.get_user(username)
        if existing_user:
            await processing_msg.edit_text(
                f"{username} atly ulanyjy eyyam bar!\n"
                "Bashga ulanyjy adyny synanyshyn."
            )
            return ASK_USERNAME

        result = await client.create_user(
            username=username,
            data_limit_gb=DEFAULT_DATA_LIMIT_GB,
            expire_days=DEFAULT_EXPIRE_DAYS
        )

        if result:
            user_info = await client.get_user(username)
            if user_info:
                subscription_url = user_info.get("subscription_url", "")
                links = user_info.get("links", [])
                expire_timestamp = user_info.get("expire", 0)
                expire_date = datetime.fromtimestamp(expire_timestamp).strftime("%Y-%m-%d %H:%M") if expire_timestamp else "Nabelli"
                data_limit = user_info.get("data_limit", 0)
                data_limit_gb = round(data_limit / (1024**3), 2) if data_limit else 0

                message = (
                    f"Ulanyjy Ustunlikli Doredildi!\n\n"
                    f"Ulanyjy Ady: {username}\n"
                    f"Data Limit: {data_limit_gb} GB\n"
                    f"Gutaryan Sene: {expire_date}\n"
                    f"Yagdayy: Aktiv\n\n"
                    f"Abunalyk Linki:\n"
                    f"{subscription_url}\n\n"
                    f"Konfigurasiýa Linkleri:\n"
                )
                for link in links[:5]:
                    message += f"\n{link}"
                if len(links) > 5:
                    message += f"\n\n...we {len(links) - 5} sany beyleki"

                message += (
                    "\n\nNadip Ulanylýar?\n"
                    "1. V2RayNG, Nekoray ya-da menzes programma yuklen\n"
                    "2. Abunalyk linkini ya-da konfigurasiýa linklerini programa goshun\n"
                    "3. Baglanyn we ulanmaga bashlan!"
                )

                await processing_msg.edit_text(message)
            else:
                await processing_msg.edit_text(
                    f"Ulanyjy {username} doredildi!\n"
                    "Emma jikme-jiklikleri alanda yalnyshlyk boldy."
                )
        else:
            await processing_msg.edit_text(
                "Ulanyjy doredilende yalnyshlyk boldy!\n"
                "Panel baglanyshygyny we admin maglumatlaryny barlan."
            )
    except Exception as e:
        logger.error(f"Ulanyjy doretme yalnyshlygy: {e}")
        await processing_msg.edit_text(
            f"Yalnyshlyk: {str(e)}\n\n"
            "Gaytadan synanyshyn."
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Amal yatyryldy.")
    return ConversationHandler.END


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update.effective_user.id):
        await query.edit_message_text("Bu bota girish rugsadyňyz yok.")
        return

    if query.data == "create_user":
        await query.edit_message_text(
            "Teze Ulanyjy Doretme\n\n"
            "Ulanyjy adyny yazyn:\n"
            "(Mysal: ahmet123)\n\n"
            "Yatyrmak ucin /cancel"
        )
        return ASK_USERNAME

    elif query.data == "check_status":
        try:
            client = get_marzban_client()
            token = await client.get_token()
            if token:
                await query.edit_message_text(
                    "Bot Yagdayy: Aktiv\n\n"
                    "Telegram Bot: Bagly\n"
                    "Marzban Panel: Bagly"
                )
            else:
                await query.edit_message_text(
                    "Panel baglanyshygy gurulyp bilmedi."
                )
        except Exception as e:
            await query.edit_message_text(f"Yalnyshlyk: {str(e)}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} yalnyshlyk doretdi {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Yalnyshlyk boldy. Gaytadan synanyshyn.")


def main():
    logger.info("=== BOT BASLADYLYAR ===")
    logger.info(f"TELEGRAM_BOT_TOKEN bar: {bool(TELEGRAM_BOT_TOKEN)}")
    logger.info(f"MARZBAN_PANEL_URL: {MARZBAN_PANEL_URL}")
    logger.info(f"MARZBAN_ADMIN_USERNAME bar: {bool(MARZBAN_ADMIN_USERNAME)}")
    logger.info(f"MARZBAN_ADMIN_PASSWORD bar: {bool(MARZBAN_ADMIN_PASSWORD)}")

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN cikis utgeyjisi sazlanmady!")
        return

    if not MARZBAN_ADMIN_USERNAME or not MARZBAN_ADMIN_PASSWORD:
        logger.error("MARZBAN_ADMIN_USERNAME we MARZBAN_ADMIN_PASSWORD sazlanmady!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

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

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_callback, pattern="^check_status$"))
    application.add_error_handler(error_handler)

    logger.info("Bot bashladyl yar...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
