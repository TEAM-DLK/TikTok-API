import os
import requests
import telebot
from io import BytesIO
from datetime import datetime

TOKEN = os.getenv("TOKEN")  # Load your bot token from Heroku environment variables
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['downtt'])
def tiktok_download(message):
    try:
        # Check if no URL is provided
        command_parts = message.text.split(' ')
        if len(command_parts) == 1:
            bot.reply_to(
                message,
                "❗ Please enter a TikTok video URL.\n\nUsage: `/downtt <url>`",
                parse_mode='Markdown'
            )
            return
        
        waiting_message = bot.reply_to(message, '⌨️ Downloading video...')
        
        url = command_parts[1]
        if 'tiktok.com' not in url:
            bot.reply_to(message, "❌ Please provide a valid TikTok URL.")
            return

        api_url = f"https://api.sumiproject.net/tiktok?video={url}"
        response = requests.get(api_url)
        
        # Check if the response is successful
        if response.status_code != 200:
            bot.send_message(message.chat.id, "❌ Failed to fetch video data from the API.")
            return
        
        data = response.json()

        if data['code'] == 0:
            video_data = data['data']
            author = video_data.get('author', {})
            title = video_data.get('title', 'No Title')
            region = video_data.get('region', 'Unknown Region')
            play_url = video_data.get('play', 'No Video URL')
            music_url = video_data.get('music', 'No Music URL')
            create_time = video_data.get('create_time', 0)
            nickname = author.get('nickname', 'Unknown Author')
            create_time_formatted = datetime.utcfromtimestamp(create_time).strftime('%H:%M:%S | %d/%m/%Y')

            caption_text = (
                f"<b>🎥 {title}</b>\n\n"
                f"<blockquote>\n"
                f"📅 <b>Uploaded:</b> {create_time_formatted}\n"
                f"👤 <b>Author:</b> {nickname}\n"
                f"🌍 <b>Region:</b> {region}\n"
                f"⏱️ <b>Duration:</b> {video_data.get('duration', 'Unknown')} seconds\n\n"
                f"👁 <b>Views:</b> {video_data.get('play_count', 0):,}\n"
                f"❤️ <b>Likes:</b> {video_data.get('digg_count', 0):,}\n"
                f"💬 <b>Comments:</b> {video_data.get('comment_count', 0):,}\n"
                f"🔗 <b>Shares:</b> {video_data.get('share_count', 0):,}\n"
                f"📥 <b>Downloads:</b> {video_data.get('download_count', 0):,}\n"
                f"📑 <b>Saved:</b> {video_data.get('collect_count', 0):,}\n"
                f"</blockquote>\n"
                f"🎵 <a href='{music_url}'>Background Music</a>"
            )

            bot.send_video(chat_id=message.chat.id, video=play_url, caption=caption_text, parse_mode='HTML')

            # Download and send the background music
            music_response = requests.get(music_url)
            if music_response.status_code == 200:
                audio_data = BytesIO(music_response.content)
                audio_data.seek(0)
                bot.send_audio(message.chat.id, audio_data, title="TikTok Background Music", performer=nickname)
            else:
                bot.send_message(message.chat.id, "❌ Failed to download background music.")
        
        else:
            bot.send_message(message.chat.id, "❌ Unable to fetch video information from TikTok.")
    
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ An error occurred: {str(e)}")
    
    finally:
        # Delete the "Downloading video..." message
        try:
            bot.delete_message(message.chat.id, waiting_message.message_id)
        except Exception:
            pass

# Add polling to keep the bot running
bot.polling(non_stop=True)