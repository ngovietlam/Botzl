import os
import yt_dlp
import shutil
from zlapi.models import Message
from colorama import Fore
from config import FFMPEG_PATH, DOWNLOAD_DIR

def download_mp3(video_id, thread_id, thread_type, client):
    try:
        ffmpeg_path = FFMPEG_PATH
        if os.path.exists(ffmpeg_path):
            print(f"{Fore.GREEN}Đã tìm thấy ffmpeg tại: {ffmpeg_path}")
        else:
            ffmpeg_path = shutil.which("ffmpeg")
            if ffmpeg_path:
                print(f"{Fore.GREEN}Đã tìm thấy ffmpeg trong PATH tại: {ffmpeg_path}")
            else:
                client.send(Message(text="Lỗi: Không tìm thấy ffmpeg trên hệ thống."), thread_id, thread_type)
                return None

        video_url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'ffmpeg_location': ffmpeg_path,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            if 'ext' in info:
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            else:
                file_path = file_path.replace('.webm', '.mp3').replace('.m4a', '.mp3')

        if not os.path.exists(file_path):
            client.send(Message(text=f"Lỗi tải MP3: File không tồn tại tại {file_path}. Kiểm tra log để biết chi tiết."), thread_id, thread_type)
            return None
        return file_path
    except Exception as e:
        print(f"{Fore.RED}Lỗi tải MP3: {e}")
        client.send(Message(text=f"Lỗi tải MP3: {str(e)}"), thread_id, thread_type)
        return None