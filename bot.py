import sqlite3
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.error import TelegramError
import logging

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Replace these with your own values
BOT_TOKEN = 'YOUR_BOT_TOKEN_HERE'  # Replace with your bot token
BROADCAST_CHANNEL = '@your_broadcast_channel'  # Replace with your broadcast channel username

# Database initialization
def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, credits INTEGER DEFAULT 0, referrer_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS channels
                 (channel_id INTEGER PRIMARY KEY, user_id INTEGER, channel_username TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (post_id INTEGER PRIMARY KEY AUTOINCREMENT, channel_id INTEGER, post_time TIMESTAMP)''')
    conn.commit()
    conn.close()

# Check if the bot is an admin of a channel
def is_bot_admin(bot: Bot, channel_username: str) -> bool:
    try:
        chat = bot.get_chat(channel_username)
        member = bot.get_chat_member(chat.id, bot.id)
        return member.status in ['administrator', 'creator']
    except TelegramError as e:
        logger.error(f"Error checking admin status: {e}")
        return False

# /start command - Handles new users and referrals
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if c.fetchone() is None:
        # New user
        c.execute("INSERT INTO users (user_id, credits) VALUES (?, 0)", (user_id,))
        args = context.args
        if args and args[0].isdigit():
            referrer_id = int(args[0])
            if referrer_id != user_id:
                c.execute("UPDATE users SET credits = credits + 10 WHERE user_id = ?", (referrer_id,))
                update.message.reply_text("Welcome! You've joined via a referral. Your referrer has received 10 credits.")
            else:
                update.message.reply_text("Welcome! Use /register <channel_username> to register your channel.")
        else:
            update.message.reply_text("Welcome! Use /register <channel_username> to register your channel.")
    else:
        update.message.reply_text("You are already registered. Use /register <channel_username> to register your channel.")
    conn.commit()
    conn.close()

# /register command - Register a channel
def register(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if len(context.args) != 1:
        update.message.reply_text("Usage: /register <channel_username>")
        return
    channel_username = context.args[0]
    if not channel_username.startswith('@'):
        channel_username = '@' + channel_username
    bot = context.bot
    try:
        chat = bot.get_chat(channel_username)
        admins = bot.get_chat_administrators(chat.id)
        is_admin = any(admin.user.id == user_id for admin in admins)
        if is_admin:
            with sqlite3.connect('bot.db') as conn:
                c = conn.cursor()
                c.execute("INSERT INTO channels (channel_id, user_id, channel_username) VALUES (?, ?, ?)",
                          (chat.id, user_id, channel_username))
                conn.commit()
            update.message.reply_text(f"Channel {channel_username} registered successfully.")
        else:
            update.message.reply_text("You are not an admin of this channel.")
    except TelegramError as e:
        update.message.reply_text(f"Error: {e}")

# /post command - Post a channel to the broadcast channel
def post(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if len(context.args) != 1:
        update.message.reply_text("Usage: /post <channel_username>")
        return
    channel_username = context.args[0]
    if not channel_username.startswith('@'):
        channel_username = '@' + channel_username
    bot = context.bot
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM channels WHERE channel_username = ? AND user_id = ?", (channel_username, user_id))
        channel = c.fetchone()
        if not channel:
            update.message.reply_text("Channel not registered or you are not the owner.")
            return
        if is_bot_admin(bot, channel_username):
            # Post without deducting credits
            try:
                bot.send_message(chat_id=BROADCAST_CHANNEL, text=f"Check out {channel_username}")
                update.message.reply_text("Posted successfully without deducting credits since bot is admin.")
            except TelegramError as e:
                update.message.reply_text(f"Error posting: {e}")
        else:
            c.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
            result = c.fetchone()
            if result is None:
                update.message.reply_text("You are not registered. Use /start to register.")
                return
            credits = result[0]
            if credits >= 4:
                c.execute("UPDATE users SET credits = credits - 4 WHERE user_id = ?", (user_id,))
                try:
                    bot.send_message(chat_id=BROADCAST_CHANNEL, text=f"Check out {channel_username}")
                    update.message.reply_text("Posted successfully. 4 credits deducted.")
                except TelegramError as e:
                    update.message.reply_text(f"Error posting: {e}")
            else:
                update.message.reply_text("Not enough credits. Invite more users to earn credits or make the bot admin of your channel.")
        conn.commit()

# /referral command - Generate a referral link
def referral(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"
    update.message.reply_text(f"Your referral link: {referral_link}")

# Main function - Start the bot
def main() -> None:
    init_db()
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("register", register))
    dp.add_handler(CommandHandler("post", post))
    dp.add_handler(CommandHandler("referral", referral))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()