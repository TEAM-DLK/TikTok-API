import os
import requests
from datetime import datetime
from io import BytesIO
from telebot import TeleBot, types
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")  # Get the token from Heroku environment variables
bot = TeleBot(TOKEN)
server = Flask(__name__)

@bot.message_handler(commands=['downtt'])
def tiktok_download(message: types.Message):
    try:
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) == 1:
            bot.reply_to(
                message, 
                "❗ Please enter the TikTok video URL.\n\nUsage: `/downtt <url>`",
                parse_mode='Markdown'
            )
            return

        url = command_parts[1]
        waiting_message = bot.reply_to(message, "⌨️ Downloading video...")

        api_url = f"https://api.sumiproject.net/tiktok?video={url}"
        response = requests.get(api_url)

        if response.status_code != 200:
            bot.send_message(message.chat.id, "❌ Unable to connect to the API.")
            return

        data = response.json()
        if data.get("code") != 0:
            bot.send_message(message.chat.id, "❌ Failed to fetch video details from TikTok.")
            return

        video_data = data["data"]
        author = video_data.get("author", {})
        title = video_data.get("title", "No title available")
        region = video_data.get("region", "Unknown region")
        play_url = video_data.get("play")
        music_url = video_data.get("music")
        create_time = video_data.get("create_time", 0)
        nickname = author.get("nickname", "Unknown author")

        if not play_url:
            bot.send_message(message.chat.id, "❌ No video URL found.")
            return

        create_time_formatted = datetime.utcfromtimestamp(create_time).strftime("%H:%M:%S | %d/%m/%Y")
        caption = (
            f"<b>🎥 {title}</b>\n\n"
            f"<blockquote>\n"
            f"📅 <b>Upload Date:</b> {create_time_formatted}\n\n"
            f"👤 <b>Author:</b> {nickname}\n"
            f"🌍 <b>Region:</b> {region}\n"
            f"⏱️ <b>Duration:</b> {video_data.get('duration', 'Unknown')} seconds\n\n"
            f"👁 <b>Views:</b> {video_data.get('play_count', 0):,}\n"
            f"❤️ <b>Likes:</b> {video_data.get('digg_count', 0):,}\n"
            f"💬 <b>Comments:</b> {video_data.get('comment_count', 0):,}\n"
            f"🔗 <b>Shares:</b> {video_data.get('share_count', 0):,}\n"
            f"📥 <b>Downloads:</b> {video_data.get('download_count', 0):,}\n"
            f"📑 <b>Saved to Collections:</b> {video_data.get('collect_count', 0):,}\n"
            f"</blockquote>"
        )

        bot.send_video(chat_id=message.chat.id, video=play_url, caption=caption, parse_mode="HTML")

        if music_url:
            music_response = requests.get(music_url)
            if music_response.status_code == 200:
                audio_data = BytesIO(music_response.content)
                audio_data.seek(0)
                bot.send_audio(message.chat.id, audio_data, title="Background Music", performer=nickname)

    except requests.exceptions.RequestException:
        bot.send_message(message.chat.id, "❌ Network error, please try again.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ An error occurred: {str(e)}")
    finally:
        try:
            bot.delete_message(message.chat.id, waiting_message.message_id)
        except:
            pass

# Webhook route
@server.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    bot.process_new_updates([types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "OK", 200

# Start webhook
@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{os.getenv('APP_URL')}/{TOKEN}")
    return "Webhook set!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
