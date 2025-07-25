import os

# Cấu hình bot
PREFIX = "!"
EXCLUDED_USER_IDS = ['207754413506549669']
DATA_FILE = 'user_data.json'
YOUTUBE_API_KEY = "AIzaSyDTyGAr1O5JAkcrT4uSz2YS9MfZjPhzoTg"  # Thay bằng API Key thực
FFMPEG_PATH = r"C:\ffmpeg\ffmpeg.exe"  # Đường dẫn đến ffmpeg
DOWNLOAD_DIR = 'downloads'

# Đảm bảo thư mục tải xuống tồn tại
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

imei = "f8ac1ce2-a461-4f01-8886-cd9e7d759463-2ce1fd67485cfe92adf700d716e9f29f"
session_cookies = {
    "__zi":
    "3000.SSZzejyD7CmYdFp-qHGMXIcMlVhI71hAP8lpzCfVHjXknR_tmnSAqcJ0jl-C5WNNASUqyuqN2TOqDW.1",
    "__zi-legacy":
    "3000.SSZzejyD7CmYdFp-qHGMXIcMlVhI71hAP8lpzCfVHjXknR_tmnSAqcJ0jl-C5WNNASUqyuqN2TOqDW.1",
    "_ga":
    "GA1.2.519723396.1677726969",
    "_ga_RYD7END4JE":
    "GS2.2.s1747336411$o4$g0$t1747336411$j60$l0$h0",
    "zoaw_sek":
    "mOId.1030188869.2.BTUNeT4FZ4MKOEjuqG-CHT4FZ4NH3un5q2VhVBaFZ4K",
    "zoaw_type":
    "0",
    "_zlang":
    "vn",
    "app.event.zalo.me":
    "6882565181904122122",
    "_gid":
    "GA1.2.1864125658.1748775857",
    "_gat":
    "1",
    "zpsid":
    "kAdA.395093091.15.FhrgNLvk0oGzoeypKcu392iTSHTdMpCTRLuw5Iqdh-I8UN-3Nwum63Pk0oG",
    "zpw_sek":
    "Ltja.395093091.a0.dPZPRagM5y0fCflNQvONm36qSgjeh3M36-nYc27uPuGindcP0_fzxmFZGPGjgohYD-LVTzRG1aGMboNbCFuNm0"
}