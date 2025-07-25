from zlapi.models import Message
from colorama import Fore
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import os
from utils.youtube_downloader import download_mp3

def handle_sing(client, message_object, thread_id, thread_type, args, author_id):
    if not args:
        client.send(Message(text="Vui lòng nhập từ khóa! Ví dụ: !sing mơ"), thread_id, thread_type)
        return

    keyword = "sing " + " ".join(args)
    try:
        request = client.youtube.search().list(
            part="snippet",
            q=keyword,
            maxResults=5,
            type="video"
        )
        response = request.execute()

        if not response.get('items'):
            client.send(Message(text="Không tìm thấy video nào!"), thread_id, thread_type)
            return

        videos = []
        response_text = "🎵 Kết quả tìm kiếm YouTube 🎵\n"
        for idx, item in enumerate(response['items'], 1):
            title = item['snippet']['title']
            video_id = item['id']['videoId']
            videos.append({"title": title, "video_id": video_id})
            response_text += f"{idx}. {title}\n"

        response_text += "\nGửi số (1-5) để chọn video và tải MP3!"
        client.send(Message(text=response_text), thread_id, thread_type)

        client.waiting_for_selection[thread_id] = {
            "author_id": author_id,
            "videos": videos,
            "state": "waiting_for_selection"
        }

    except Exception as e:
        client.send(Message(text=f"Lỗi tìm kiếm YouTube: {str(e)}"), thread_id, thread_type)
        print(f"{Fore.RED}Lỗi xử lý !sing: {e}")

def get_y2mate_mp3_url(video_id):
    try:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        
        # Truy cập trang y2mate.nu
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }
        response = session.get('https://y2mate.nu/en-00uN/', headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"{Fore.RED}Lỗi truy cập y2mate.nu: Mã trạng thái {response.status_code}")
            return None
        
        # Mô phỏng gửi URL video
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form', {'id': 'search-form'})
        if not form:
            print(f"{Fore.RED}Lỗi: Không tìm thấy form tìm kiếm trên y2mate.nu")
            return None
        
        # Gửi yêu cầu tìm kiếm
        search_url = 'https://y2mate.nu/en-00uN/search'
        data = {
            'url': youtube_url,
            # Có thể cần thêm các trường ẩn từ form nếu y2mate yêu cầu
        }
        response = session.post(search_url, headers=headers, data=data, timeout=10)
        if response.status_code != 200:
            print(f"{Fore.RED}Lỗi tìm kiếm trên y2mate.nu: Mã trạng thái {response.status_code}")
            return None
        
        # Lấy link MP3
        soup = BeautifulSoup(response.text, 'html.parser')
        mp3_link = soup.find('a', {'class': 'download-btn', 'data-ftype': 'mp3'})
        if mp3_link and 'href' in mp3_link.attrs:
            mp3_url = mp3_link['href']
            print(f"{Fore.GREEN}Lấy URL MP3 từ y2mate.nu thành công: {mp3_url}")
            return mp3_url
        else:
            print(f"{Fore.RED}Lỗi: Không tìm thấy link MP3 trên y2mate.nu")
            return None
    except Exception as e:
        print(f"{Fore.RED}Lỗi khi lấy MP3 từ y2mate.nu: {e}")
        return None

def handle_video_selection(client, message, message_object, thread_id, thread_type, author_id):
    if thread_id in client.waiting_for_selection and author_id == client.waiting_for_selection[thread_id]["author_id"]:
        if client.waiting_for_selection[thread_id]["state"] == "waiting_for_selection":
            try:
                choice = int(message.strip()) - 1
                videos = client.waiting_for_selection[thread_id]["videos"]
                if 0 <= choice < len(videos):
                    video_id = videos[choice]["video_id"]
                    title = videos[choice]["title"]
                    client.send(Message(text=f"Đang xử lý MP3: {title}..."), thread_id, thread_type)

                    # Kiểm tra video ID hợp lệ
                    if not video_id or len(video_id) != 11:
                        client.send(Message(text="Lỗi: Video ID không hợp lệ."), thread_id, thread_type)
                        return True

                    # Thử lấy URL MP3 từ y2mate.nu
                    mp3_url = get_y2mate_mp3_url(video_id)
                    file_size = None
                    session = requests.Session()
                    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
                    session.mount('https://', HTTPAdapter(max_retries=retries))

                    # Nếu y2mate thất bại, thử RapidAPI
                    if not mp3_url:
                        print(f"{Fore.YELLOW}Thử RapidAPI vì y2mate thất bại")
                        api_url = f"https://yt-mp3-api.p.rapidapi.com/download?video_id={video_id}"
                        headers = {
                            "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",  # Thay bằng API key của bạn
                            "X-RapidAPI-Host": "yt-mp3-api.p.rapidapi.com"
                        }
                        response = session.get(api_url, headers=headers, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            mp3_url = data.get('url') or data.get('download_url') or data.get('mp3_url')
                            if mp3_url:
                                print(f"{Fore.GREEN}Lấy URL MP3 từ RapidAPI thành công")
                            else:
                                print(f"{Fore.RED}Lỗi: Phản hồi RapidAPI không chứa URL - {data}")
                        else:
                            print(f"{Fore.RED}Lỗi RapidAPI: Mã trạng thái {response.status_code} - {response.text}")

                    # Nếu cả y2mate và RapidAPI thất bại, dùng yt-dlp
                    if not mp3_url:
                        print(f"{Fore.YELLOW}Thử yt-dlp vì các API thất bại")
                        file_path = download_mp3(video_id, thread_id, thread_type, client)
                        if file_path and os.path.exists(file_path):
                            mp3_url = f"file://{file_path}"  # Giả định sendRemoteVoice hỗ trợ file cục bộ
                            file_size = os.path.getsize(file_path)
                        else:
                            client.send(Message(text="Lỗi: Không thể tải MP3 bằng yt-dlp."), thread_id, thread_type)
                            return True

                    # Lấy kích thước file nếu chưa có
                    if not file_size:
                        head_response = session.head(mp3_url, timeout=5)
                        if not head_response.headers.get('Content-Length'):
                            client.send(Message(text="Lỗi: Không thể lấy kích thước file MP3."), thread_id, thread_type)
                            print(f"{Fore.RED}Lỗi: Không có Content-Length trong phản hồi HEAD")
                            return True
                        file_size = int(head_response.headers.get('Content-Length', 0))

                    # Gửi file MP3 bằng sendRemoteVoice
                    youtube_link = f"https://www.youtube.com/watch?v={video_id}"
                    try:
                        client.sendRemoteVoice(
                            voiceUrl=mp3_url,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            fileSize=file_size
                        )
                        client.send(
                            Message(text=f"Đã gửi MP3: {title}\nLink YouTube: {youtube_link}"),
                            thread_id,
                            thread_type
                        )
                        # Xóa file cục bộ nếu dùng yt-dlp
                        if mp3_url.startswith('file://'):
                            os.remove(file_path)
                    except ZaloAPIException as e:
                        client.send(
                            Message(text=f"Lỗi gửi tin nhắn thoại: {str(e)}\nLink YouTube: {youtube_link}"),
                            thread_id,
                            thread_type
                        )
                        print(f"{Fore.RED}Lỗi sendRemoteVoice: {e}")
                    del client.waiting_for_selection[thread_id]
                else:
                    client.send(Message(text="Lựa chọn không hợp lệ! Gửi số từ 1 đến 5."), thread_id, thread_type)
                return True
            except ValueError:
                client.send(Message(text="Vui lòng gửi số hợp lệ (1-5)!"), thread_id, thread_type)
                return True
            except Exception as e:
                client.send(Message(text=f"Lỗi xử lý MP3: {str(e)}"), thread_id, thread_type)
                print(f"{Fore.RED}Lỗi xử lý MP3: {e}")
                return True
    return False