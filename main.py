import json
import os
import threading
import time
import requests
import random  # Thêm import random nếu chưa có
# from flask import Flask, jsonify
from zlapi import ZaloAPI, ZaloAPIException
from zlapi.models import *
from colorama import Fore, Style, init
from googleapiclient.discovery import build
from module import handle_help, handle_ping, handle_info, handle_say, handle_count
from config import imei, session_cookies
# Tạo Flask app cho keep-alive
# app = Flask(__name__)

# @app.route('/ping')
# def ping():
#     return jsonify({
#         'status': 'alive',
#         'message': 'Bot is running',
#         'timestamp': time.time()
#     })

# @app.route('/keep-alive')
# def keep_alive():
#     return jsonify({
#         'status': 'ok',
#         'uptime': time.time(),
#         'bot_status': 'running'
#     })

# @app.route('/')
# def home():
#     return jsonify({
#         'message': 'Zalo Bot Server',
#         'endpoints': ['/ping', '/keep-alive'],
#         'status': 'running'
#     })

# def run_flask():
#     """Chạy Flask server trong thread riêng"""
#     app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

# def keep_alive_ping():
#     """Gửi ping request định kỳ để giữ server alive"""
#     # Thay YOUR_REPL_URL bằng URL thực tế của Replit project
#     repl_url = "https://your-project-name.your-username.repl.co"

#     while True:
#         try:
#             time.sleep(300)  # Đợi 5 phút
#             response = requests.get(f"{repl_url}/ping", timeout=10)
#             if response.status_code == 200:
#                 print(
#                     f"{Fore.GREEN}Keep-alive ping successful at {time.ctime()}"
#                 )
#             else:
#                 print(
#                     f"{Fore.YELLOW}Keep-alive ping failed with status: {response.status_code}"
#                 )
#         except requests.exceptions.RequestException as e:
#             print(f"{Fore.RED}Keep-alive ping error: {e}")
#         except Exception as e:
#             print(f"{Fore.RED}Unexpected error in keep-alive: {e}")


class CustomClient(ZaloAPI):

    def __init__(self, phone, password, imei, session_cookies):
        try:
            super().__init__(phone=phone,
                             password=password,
                             imei=imei,
                             session_cookies=session_cookies)
        except ZaloAPIException as e:
            print(f"{Fore.RED}Lỗi đăng nhập Zalo: {e}")
            raise
        self.prefix = "!"
        self.excluded_user_ids = ['207754413506549669']
        self.data_file = 'user_data.json'
        self.training_data_file = 'ai_training_data.json'  # File lưu dữ liệu huấn luyện AI
        self.message_counts = {}
        self.count_data = {}
        self.waiting_for_selection = {}
        self.user_histories = {}

        # Làm sạch dữ liệu AI khi khởi tạo bot
        with open(self.training_data_file, 'w') as f:
            json.dump([], f)  # Ghi một mảng rỗng vào file

        self.commands = {
            "help": {
                "desc": "Hiển thị danh sách lệnh",
                "func": handle_help
            },
            "ping": {
                "desc": "Kiểm tra bot có hoạt động không",
                "func": handle_ping
            },
            "info": {
                "desc": "Hiển thị thông tin về bot",
                "func": handle_info
            },
            "say": {
                "desc": "Lặp lại nội dung bạn nhập (!say <nội dung>)",
                "func": handle_say
            },
            "dem": {
                "desc": "Tăng số đếm của bạn lên 1",
                "func": handle_count
            },
            "check": {
                "desc": "Kiểm tra số đếm hiện tại của bạn",
                "func": handle_count
            },
            "top": {
                "desc": "Xem bảng xếp hạng đếm số",
                "func": handle_count
            },
            "reset": {
                "desc": "Reset tất cả count về 0 (chỉ admin)",
                "func": handle_count
            }
        }
        self.load_data()

    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.message_counts = data.get('message_counts', {})
                self.count_data = data.get('count_data',
                                           {})  # Tải dữ liệu count
        except (FileNotFoundError, json.JSONDecodeError):
            self.message_counts = {}
            self.count_data = {}

    def save_data(self):
        with open(self.data_file, 'w') as f:
            json.dump(
                {
                    'message_counts': self.message_counts,
                    'count_data': self.count_data  # Lưu dữ liệu count
                },
                f,
                indent=4)

    def update_message_count(self, thread_id, author_id):
        if thread_id not in self.message_counts:
            self.message_counts[thread_id] = {}
        if author_id not in self.message_counts[thread_id]:
            self.message_counts[thread_id][author_id] = 0
        self.message_counts[thread_id][author_id] += 1

    def initialize_count_for_user(self, thread_id, author_id):
        """Khởi tạo count = 0 cho user nếu chưa tồn tại"""
        if thread_id not in self.count_data:
            self.count_data[thread_id] = {}
        if author_id not in self.count_data[thread_id]:
            self.count_data[thread_id][author_id] = 0

    def get_user_display_name(self, userId):
        """Lấy tên hiển thị của user"""
        try:
            user_info = super().fetchUserInfo(userId)
            if isinstance(user_info, str):
                user_info = json.loads(user_info)
            if 'changed_profiles' in user_info and userId in user_info[
                    'changed_profiles']:
                zalo_name = user_info['changed_profiles'][userId].get(
                    'zaloName', None)
                return zalo_name or user_info['changed_profiles'][userId].get(
                    'displayName', 'Unknown')
            return 'Unknown'
        except Exception as e:
            print(f"{Fore.RED}Lỗi lấy thông tin người dùng: {e}")
            return 'Unknown'
    def ask_ai(self, author_id):
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": "Bearer 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",
            "Content-Type": "application/json"
        }

        # Lấy lịch sử hội thoại của user
        history = self.user_histories.get(author_id, [])
        messages = [{"role": "user", "content": msg} for msg in history]

        # Thêm dữ liệu huấn luyện từ file
        with open(self.training_data_file, 'r') as f:
            training_data = json.load(f)
        for training_msg in training_data:
            messages.insert(0, {"role": "system", "content": training_msg})

        # Thêm hướng dẫn trả lời tiếng Việt
        messages.insert(0, {"role": "system", "content": "Hãy nhập vai là một cậu học sinh, 18 tuổi, chúng ta là bạn bè rất thân, cậu rất quan tâm đến tôi, hay tán gẫu, hãy nói chuyện thật tự nhiên với tôi bằng tiếng Việt."})

        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": messages
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[AI] Lỗi gọi API: {e}")
            return "Xin lỗi, tôi không thể phản hồi ngay lúc này."

    def fetchUserInfo(self, userId):
        try:
            user_info = super().fetchUserInfo(userId)
            if isinstance(user_info, str):
                user_info = json.loads(user_info)
            if 'changed_profiles' in user_info and userId in user_info[
                    'changed_profiles']:
                zalo_name = user_info['changed_profiles'][userId].get(
                    'zaloName', None)
                return zalo_name or user_info['changed_profiles'][userId].get(
                    'displayName', userId)
            return userId
        except Exception as e:
            print(f"{Fore.RED}Lỗi lấy thông tin người dùng: {e}")
            return userId

    

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        print(f"{Fore.GREEN}Received message:\n"
              f"- Message: {Style.BRIGHT}{message}{Style.NORMAL}\n"
              f"- Author ID: {Fore.CYAN}{author_id}\n"
              f"- Thread ID: {Fore.YELLOW}{thread_id}\n"
              f"- Thread Type: {Fore.BLUE}{thread_type}\n")
        content = ""
        if hasattr(message_object, 'content') and isinstance(message_object.content, str):
            content = message_object.content.strip()
        else:
            content = str(message).strip()

        # Lưu tin nhắn vào file huấn luyện
        if author_id != str(self.uid) and not content.startswith(self.prefix):
            with open(self.training_data_file, 'r') as f:
                training_data = json.load(f)
            training_data.append(content)
            with open(self.training_data_file, 'w') as f:
                json.dump(training_data, f, indent=4)

        # Chỉ phản hồi AI nếu không phải tin nhắn của bot, không phải lệnh
        if author_id != str(self.uid) and not content.startswith(self.prefix):
            if author_id not in self.user_histories:
                self.user_histories[author_id] = []
            self.user_histories[author_id].append(content)
            self.user_histories[author_id] = self.user_histories[author_id][-10:]

            # Thêm độ trễ ngẫu nhiên trước khi gọi AI
            delay = random.randint(5, 20)  # Độ trễ từ 5 đến 20 giây
            print(f"{Fore.YELLOW}Đợi {delay} giây trước khi gọi AI...")
            time.sleep(delay)

            ai_reply = self.ask_ai(author_id)
            self.send(Message(text=ai_reply), thread_id, thread_type)

        # Xử lý các lệnh khác
        try:
            self.update_message_count(thread_id, author_id)
            self.initialize_count_for_user(thread_id, author_id)
            if content.startswith(self.prefix):
                command = content[len(self.prefix):].split()[0].lower() if content[len(self.prefix):] else ""
                args = content[len(self.prefix) + len(command):].strip().split()
                if command in self.commands:
                    if author_id not in self.excluded_user_ids:
                        self.commands[command]["func"](self, message_object, thread_id, thread_type, args, author_id)
                    else:
                        self.send(Message(text="Bạn không được phép sử dụng bot!"), thread_id, thread_type)
                elif command:
                    self.send(
                        Message(
                            text=f"Lệnh `{self.prefix}{command}` không tồn tại. Gõ `{self.prefix}help` để xem danh sách lệnh."
                        ), thread_id, thread_type)
            self.save_data()
        except Exception as ex:
            print(f"{Fore.RED}Lỗi xử lý tin nhắn: {ex}")
            self.send(Message(text=f"Lỗi: {str(ex)}"), thread_id, thread_type)

    def onGroupJoin(self, mid, added_ids, author_id, thread_id, **kwargs):
        """Xử lý khi bot được thêm vào nhóm hoặc có thành viên mới"""
        try:
            # Khởi tạo count cho các thành viên mới
            for user_id in added_ids:
                self.initialize_count_for_user(thread_id, user_id)

            # Nếu bot được thêm vào nhóm, gửi thông báo chào mừng
            if str(self.uid) in added_ids:
                welcome_msg = ("🤖 Xin chào! Tôi là bot đếm số!\n\n"
                               "📝 Các lệnh có thể sử dụng:\n"
                               "• !dem - Tăng số đếm của bạn\n"
                               "• !check - Xem số đếm hiện tại\n"
                               "• !top - Xem bảng xếp hạng\n"
                               "• !reset - Reset tất cả (chỉ admin)\n"
                               "• !help - Xem tất cả lệnh\n\n"
                               "🎯 Hãy bắt đầu đếm nào!")
                self.send(Message(text=welcome_msg), thread_id,
                          ThreadType.GROUP)

            self.save_data()

        except Exception as e:
            print(f"{Fore.RED}Lỗi xử lý sự kiện join group: {e}")

    def stop_listening(self):
        """Dừng bot listener"""
        try:
            if hasattr(self, 'listening') and self.listening:
                self.listening = False
                print(f"{Fore.YELLOW}Bot đã dừng listening")
        except Exception as e:
            print(f"{Fore.RED}Lỗi dừng bot: {e}")

conversation_starters = [
    "Chào Minh! Hôm nay cậu thế nào?",
    "Cậu đang làm gì vậy?",
    "Minh đã ăn gì chưa? Nhớ ăn uống đầy đủ nhé!",
    "Hôm nay có gì vui không? Kể mình nghe với!",
    "Cậu có đang bận không? Mình muốn trò chuyện với cậu.",
    "Cậu có thích nghe nhạc không? Gần đây mình nghe được bài rất hay!",
    "Minh có kế hoạch gì cho ngày hôm nay không?",
    "Cậu có muốn chia sẻ điều gì thú vị không?",
    "Cậu có đang cảm thấy vui không? Nếu không, mình ở đây để lắng nghe cậu.",
    "Cậu có muốn mình kể một câu chuyện vui không?"
]
def main():
    """Hàm main để chạy bot trực tiếp"""
    # Khởi tạo client
    client = CustomClient('api_key',
                          'secret_key',
                          imei=imei,
                          session_cookies=session_cookies)

    # Chạy thread nhắn tin chủ động
    bot_thread = threading.Thread(target=bot_initiate_conversation, args=(client,), daemon=True)
    bot_thread.start()
    print(f"{Fore.CYAN}🕐 Bot đã bắt đầu chủ động nhắn tin mỗi phút với xác suất 50%.")

    # Chạy bot
    client.listen()

def bot_initiate_conversation(client):
    """Bot chủ động nhắn tin với xác suất 50% mỗi phút"""
    while True:
        time.sleep(60)  # Chờ 1 phút
        if random.random() < 0.5:  # 50% xác suất
            try:
                message = random.choice(conversation_starters)
                thread_id = "124370956160882574"  # Thay bằng ID của bạn
                thread_type = ThreadType.GROUP  # Loại thread (USER hoặc GROUP)
                client.send(Message(text=message), thread_id, thread_type)
                print(f"{Fore.CYAN}Bot đã chủ động nhắn tin: {message}")
            except Exception as e:
                print(f"{Fore.RED}Lỗi khi bot chủ động nhắn tin: {e}")

if __name__ == "__main__":
    main()

