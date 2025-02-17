import os
import telebot
import requests
from flask import Flask, request

# Load environment variables from Heroku
TOKEN = os.getenv("BOT_TOKEN")  # Telegram Bot Token
APP_URL = os.getenv("APP_URL")  # Heroku App URL (e.g., https://your-app.herokuapp.com)

# Initialize Bot & Flask Server
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)

# Webhook Route (Telegram will send updates here)
@server.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

# Root Route (For testing if the bot is alive)
@server.route("/")
def home():
    return "Bot is running!", 200

# Bot Command: /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Hello! I am your Telegram bot running on Heroku!")

# Bot Command: /downtt (TikTok Video Downloader)
@bot.message_handler(commands=["downtt"])
def tiktok_download(message):
    try:
        # Parse the command
        command_parts = message.text.split(" ")
        if len(command_parts) == 1:
            bot.reply_to(message, "❗ Please provide a TikTok video URL.\n\nUsage: `/downtt <url>`", parse_mode="Markdown")
            return

        waiting_message = bot.reply_to(message, "⌨️ Downloading video...")

        # Call TikTok API
        url = command_parts[1]
        api_url = f"https://api.sumiproject.net/tiktok?video={url}"
        response = requests.get(api_url)
        data = response.json()

        if data["code"] == 0:
            video_data = data["data"]
            play_url = video_data.get("play", "No video URL available")
            music_url = video_data.get("music", "No music URL available")
            nickname = video_data.get("author", {}).get("nickname", "Unknown")

            bot.send_video(chat_id=message.chat.id, video=play_url, caption="🎥 Here is your TikTok video!", parse_mode="HTML")

            # Send Audio
            music_response = requests.get(music_url)
            bot.send_audio(message.chat.id, music_response.content, title="TikTok Music", performer=nickname)

        else:
            bot.send_message(message.chat.id, "⚠️ Unable to fetch video from TikTok.")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")
    finally:
        try:
            bot.delete_message(message.chat.id, waiting_message.message_id)
        except:
            pass

# Set Webhook Before Starting Flask
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}")  # Ensure webhook is set only once
    server.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))