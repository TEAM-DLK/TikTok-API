import requests
import telebot
from datetime import datetime
from io import BytesIO



TOKEN_BOT_LQH = "8000339832:AAGmbTBiXluVTGfB54xgXgJtFzU7AR3aCKg" 
bot = telebot.TeleBot(TOKEN_BOT_LQH)

@bot.message_handler(commands=['downtt'])
def tiktok_download(message):
    try:
        # Kiểm tra nếu không có URL trong lệnh
        command_parts = message.text.split(' ')
        if len(command_parts) == 1:
            bot.reply_to(
                message,
                "❗ Vui lòng nhập URL của video TikTok.\n\nCách sử dụng: /downtt <url>",
                parse_mode='Markdown'
            )
            return
        waiting_message = bot.reply_to(message, '⌨️ Đang tải video...')
        url = command_parts[1]
        api_url = f"https://api.sumiproject.net/tiktok?video={url}"
        response = requests.get(api_url)
        data = response.json() 
        if data['code'] == 0:
            video_data = data['data']
            author = video_data.get('author', {})
            title = video_data.get('title', 'Không có tiêu đề')
            region = video_data.get('region', 'Không rõ khu vực')
            play_url = video_data.get('play', 'Không có URL phát video')
            music_url = video_data.get('music', 'Không có URL nhạc')
            create_time = video_data.get('create_time', 0)
            nickname = author.get('nickname', 'Không có tên tác giả')
            create_time_formatted = datetime.utcfromtimestamp(create_time).strftime('%H:%M:%S | %d/%m/%Y')
            haha = (
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
            bot.send_video(chat_id=message.chat.id, video=play_url, caption=haha, parse_mode='HTML')
            music_response = requests.get(music_url)
            audio_data = BytesIO(music_response.content)
            audio_data.seek(0)
            bot.send_audio(message.chat.id, audio_data, title="Nhạc nền từ video", performer=nickname)
        else:
            bot.send_message(message.chat.id, "Không thể lấy thông tin video từ TikTok.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Đã có lỗi xảy ra: {str(e)}")
    finally:
        try:
            bot.delete_message(message.chat.id, waiting_message.message_id)
        except Exception:
            pass



bot.polling(none_stop=True)