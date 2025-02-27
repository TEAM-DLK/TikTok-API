import requests
import re
from datetime import datetime
from io import BytesIO
import telebot
from telebot.types import Message

# Replace with your bot token
TOKEN = "XXXXXX:AAGmbTBiXluVTGfB54xgXgJtFzU7AR3aCKg"

bot = telebot.TeleBot(TOKEN)

# TikTok URL validation regex
TIKTOK_REGEX = r"(https?:\/\/)?(www\.)?(tiktok\.com\/.*|vm\.tiktok\.com\/.*)"

# /downtt command
@bot.message_handler(commands=['downtt'])
def tiktok_download(message):
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

        url = command_parts[1]

        # Validate URL format
        if not re.match(TIKTOK_REGEX, url):
            bot.reply_to(message, "❗ Vui lòng nhập một URL TikTok hợp lệ.")
            return

        waiting_message = bot.reply_to(message, '⌨️ Đang tải video...')

        # Call API
        api_url = f"https://api.sumiproject.net/tiktok?video={url}"
        response = requests.get(api_url)
        
        # Print API response for debugging
        print("API Response:", response.text)  # This will help debug the issue

        # Check if API responded correctly
        if response.status_code != 200:
            bot.send_message(message.chat.id, f"❌ API lỗi: {response.status_code}. Vui lòng thử lại sau.")
            return
        
        try:
            data = response.json()
        except ValueError:
            bot.send_message(message.chat.id, "❌ API không trả về dữ liệu hợp lệ. Vui lòng thử lại sau.")
            print("API Response:", response.text)  # Debugging
            return

        # Check if API returned video data
        if 'code' not in data or data['code'] != 0:
            bot.send_message(message.chat.id, "❌ Không thể lấy thông tin video từ TikTok.")
            return

        video_data = data['data']
        author = video_data.get('author', {})
        title = video_data.get('title', 'Không có tiêu đề')
        region = video_data.get('region', 'Không rõ khu vực')
        play_url = video_data.get('play', None)
        music_url = video_data.get('music', None)
        create_time = video_data.get('create_time', 0)
        nickname = author.get('nickname', 'Không có tên tác giả')
        create_time_formatted = datetime.utcfromtimestamp(create_time).strftime('%H:%M:%S | %d/%m/%Y')

        if not play_url:
            bot.send_message(message.chat.id, "❌ Video không khả dụng hoặc không thể tải xuống.")
            return

        # Check file size before sending video
        video_response = requests.get(play_url, stream=True)
        file_size = int(video_response.headers.get('content-length', 0))

        if file_size > 50 * 1024 * 1024:  # 50MB limit for Telegram videos
            bot.send_message(message.chat.id, "❌ Video quá lớn để gửi qua Telegram.")
            return

        # Construct caption
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
            f"</blockquote>"
            f"🎵 <a href='{music_url}'>Nhạc By Video</a>"
        )

        # Send video
        bot.send_video(chat_id=message.chat.id, video=play_url, caption=caption, parse_mode='HTML')

        # Send music (if available)
        if music_url:
            music_response = requests.get(music_url)
            if music_response.status_code == 200:
                audio_data = BytesIO(music_response.content)
                audio_data.seek(0)
                bot.send_audio(message.chat.id, audio_data, title="Nhạc nền từ video", performer=nickname)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Đã có lỗi xảy ra: {str(e)}")
        print("Error:", str(e))  # Debugging
    finally:
        # Delete "Loading..." message if it exists
        if waiting_message:
            try:
                bot.delete_message(message.chat.id, waiting_message.message_id)
            except Exception:
                pass

if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)