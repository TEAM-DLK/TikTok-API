import requests
from datetime import datetime
from io import BytesIO
import telebot
from telebot.types import Message

# Replace with your bot token
TOKEN = "8000339832:AAGmbTBiXluVTGfB54xgXgJtFzU7AR3aCKg"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['downtt'])
def tiktok_download(message: Message):
    waiting_message = None
    try:
        # Check if URL is provided
        command_parts = message.text.split(' ')
        if len(command_parts) == 1:
            bot.reply_to(
                message,
                "❗ Vui lòng nhập URL của video TikTok.\n\nCách sử dụng: /downtt <url>",
                parse_mode='Markdown'
            )
            return

        waiting_message = bot.reply_to(message, '⌨️ Đang tải video...')
        url = ' '.join(command_parts[1:])
        api_url = f"https://api.sumiproject.net/tiktok?video={url}"
        
        response = requests.get(api_url)
        try:
            data = response.json()
        except ValueError:
            bot.send_message(message.chat.id, "Không thể phân tích dữ liệu từ API.")
            return

        if data['code'] == 0:
            video_data = data['data']
            author = video_data.get('author', {})
            title = video_data.get('title', 'Không có tiêu đề')
            region = video_data.get('region', 'Không rõ khu vực')
            play_url = video_data.get('play', '')
            music_url = video_data.get('music', '')
            create_time = video_data.get('create_time', 0)
            nickname = author.get('nickname', 'Không có tên tác giả')
            create_time_formatted = datetime.utcfromtimestamp(create_time).strftime('%H:%M:%S | %d/%m/%Y')

            # Validate URLs
            if not play_url.startswith("http"):
                bot.send_message(message.chat.id, "Video không khả dụng.")
                return
            if not music_url.startswith("http"):
                bot.send_message(message.chat.id, "Nhạc không khả dụng.")
                return

            caption = (
                f"<b>🎥 {title}</b>\n\n"
                f"<blockquote>\n"
                f"📅 Ngày Đăng: {create_time_formatted}\n\n"
                f"👤 <b>Tác giả:</b> {nickname}\n"
                f"🌍 <b>Khu Vực:</b> {region}\n"
                f"⏱️ <b>Độ Dài Video:</b> {video_data.get('duration', 'Không rõ')} Giây\n\n"
                f"👁 <b>Views:</b> {video_data.get('play_count', 0):,}\n"
                f"❤️ <b>Likes:</b> {video_data.get('digg_count', 0):,}\n"
                f"💬 <b>Comments:</b> {video_data.get('comment_count', 0):,}\n"
                f"🔗 <b>Shares:</b> {video_data.get('share_count', 0):,}\n"
                f"📥 <b>Downloads:</b> {video_data.get('download_count', 0):,}\n"
                f"📑 <b>Lưu vào bộ sưu tập:</b> {video_data.get('collect_count', 0):,}\n"
                f"</blockquote>\n"
                f"🎵 <a href='{music_url}'>Nhạc By Video</a>"
            )

            bot.send_video(chat_id=message.chat.id, video=play_url, caption=caption, parse_mode='HTML')

            # Download and send audio
            music_response = requests.get(music_url)
            audio_data = BytesIO(music_response.content)
            audio_data.seek(0)
            bot.send_audio(message.chat.id, audio_data, title="Nhạc nền từ video", performer=nickname)
        else:
            bot.send_message(message.chat.id, "Không thể lấy thông tin video từ TikTok.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Đã có lỗi xảy ra: {str(e)}")
    finally:
        if waiting_message:
            try:
                bot.delete_message(message.chat.id, waiting_message.message_id)
            except Exception:
                pass

if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)