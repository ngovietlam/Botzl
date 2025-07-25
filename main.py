import json
import os
import threading
import time
import requests
# from flask import Flask, jsonify
from zlapi import ZaloAPI, ZaloAPIException
from zlapi.models import *
from colorama import Fore, Style, init
from googleapiclient.discovery import build
#from module import  handle_ping, handle_info, handle_say, handle_count
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
        self.message_counts = {}
        self.count_data = {}  # Thêm biến lưu trữ count cho từng user
        self.waiting_for_selection = {}
        # self.commands = {
        #     "help": {
        #         "desc": "Hiển thị danh sách lệnh",
        #         "func": handle_help
        #     },
        #     "ping": {
        #         "desc": "Kiểm tra bot có hoạt động không",
        #         "func": handle_ping
        #     },
        #     "info": {
        #         "desc": "Hiển thị thông tin về bot",
        #         "func": handle_info
        #     },
        #     "say": {
        #         "desc": "Lặp lại nội dung bạn nhập (!say <nội dung>)",
        #         "func": handle_say
        #     },
        #     "dem": {
        #         "desc": "Tăng số đếm của bạn lên 1",
        #         "func": handle_count
        #     },
        #     "check": {
        #         "desc": "Kiểm tra số đếm hiện tại của bạn",
        #         "func": handle_count
        #     },
        #     "top": {
        #         "desc": "Xem bảng xếp hạng đếm số",
        #         "func": handle_count
        #     },
        #     "reset": {
        #         "desc": "Reset tất cả count về 0 (chỉ admin)",
        #         "func": handle_count
        #     }
        # }
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

    # def handle_help(self,
    #                 message_object,
    #                 thread_id,
    #                 thread_type,
    #                 args,
    #                 author_id=None):
    #     response = "📜 **Danh sách lệnh của bot** 📜\n"
    #     for cmd, info in self.commands.items():
    #         response += f"**{self.prefix}{cmd}**: {info['desc']}\n"
    #     response += f"\nSử dụng `{self.prefix}<lệnh>` để gọi bot!"
    #     self.send(Message(text=response), thread_id, thread_type)

    # def handle_ping(self,
    #                 message_object,
    #                 thread_id,
    #                 thread_type,
    #                 args,
    #                 author_id=None):
    #     self.send(Message(text="Pong! 🏓 Bot đang hoạt động!"), thread_id,
    #               thread_type)

    # def handle_info(self,
    #                 message_object,
    #                 thread_id,
    #                 thread_type,
    #                 args,
    #                 author_id=None):
    #     response = "🤖 **Thông tin về bot** 🤖\n"
    #     response += "Tên: Zalo Bot\nPhiên bản: 1.0\nTác giả: Your Name\nPrefix: !\nMô tả: Bot cơ bản cho Zalo với tính năng đếm số."
    #     self.send(Message(text=response), thread_id, thread_type)

    # def handle_say(self,
    #                message_object,
    #                thread_id,
    #                thread_type,
    #                args,
    #                author_id=None):
    #     if args:
    #         response = "🗣️ Bạn nói: " + " ".join(args)
    #         self.send(Message(text=response), thread_id, thread_type)
    #     else:
    #         self.send(
    #             Message(text="Vui lòng nhập nội dung! Ví dụ: !say Xin chào"),
    #             thread_id, thread_type)

    # def handle_dem(self,
    #                message_object,
    #                thread_id,
    #                thread_type,
    #                args,
    #                author_id=None):
    #     """Xử lý lệnh !dem - tăng count của user lên 1"""
    #     try:
    #         # Khởi tạo count cho user nếu chưa tồn tại
    #         self.initialize_count_for_user(thread_id, author_id)

    #         # Tăng count lên 1
    #         self.count_data[thread_id][author_id] += 1
    #         current_count = self.count_data[thread_id][author_id]

    #         # Lấy tên user
    #         user_name = self.get_user_display_name(author_id)

    #         # Gửi thông báo
    #         response = f"🎯 {user_name} đã đếm! Số lần đếm hiện tại: {current_count}"
    #         self.send(Message(text=response), thread_id, thread_type)

    #         # Lưu dữ liệu
    #         self.save_data()

    #     except Exception as e:
    #         print(f"{Fore.RED}Lỗi xử lý lệnh dem: {e}")
    #         self.send(Message(text="Có lỗi xảy ra khi xử lý lệnh đếm!"),
    #                   thread_id, thread_type)

    # def handle_check(self,
    #                  message_object,
    #                  thread_id,
    #                  thread_type,
    #                  args,
    #                  author_id=None):
    #     """Xử lý lệnh !check - kiểm tra count hiện tại của user"""
    #     try:
    #         # Khởi tạo count cho user nếu chưa tồn tại
    #         self.initialize_count_for_user(thread_id, author_id)

    #         current_count = self.count_data[thread_id][author_id]
    #         user_name = self.get_user_display_name(author_id)

    #         # Gửi thông báo
    #         response = f"📊 {user_name} đã đếm tổng cộng: {current_count} lần"
    #         self.send(Message(text=response), thread_id, thread_type)

    #     except Exception as e:
    #         print(f"{Fore.RED}Lỗi xử lý lệnh check: {e}")
    #         self.send(Message(text="Có lỗi xảy ra khi kiểm tra số đếm!"),
    #                   thread_id, thread_type)

    # def handle_top(self,
    #                message_object,
    #                thread_id,
    #                thread_type,
    #                args,
    #                author_id=None):
    #     """Xử lý lệnh !top - hiển thị bảng xếp hạng"""
    #     try:
    #         if thread_id not in self.count_data or not self.count_data[
    #                 thread_id]:
    #             self.send(
    #                 Message(
    #                     text=
    #                     "📊 Chưa có dữ liệu đếm nào trong cuộc trò chuyện này!"
    #                 ), thread_id, thread_type)
    #             return

    #         # Sắp xếp theo count giảm dần
    #         sorted_users = sorted(self.count_data[thread_id].items(),
    #                               key=lambda x: x[1],
    #                               reverse=True)

    #         # Tạo bảng xếp hạng
    #         response = "🏆 BẢNG XẾP HẠNG ĐẾM SỐ 🏆\n\n"

    #         for i, (user_id, count) in enumerate(sorted_users[:10]):  # Top 10
    #             user_name = self.get_user_display_name(user_id)
    #             medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
    #             response += f"{medal} {user_name}: {count} lần\n"

    #         self.send(Message(text=response), thread_id, thread_type)

    #     except Exception as e:
    #         print(f"{Fore.RED}Lỗi xử lý lệnh top: {e}")
    #         self.send(
    #             Message(text="Có lỗi xảy ra khi hiển thị bảng xếp hạng!"),
    #             thread_id, thread_type)

    # def handle_reset(self,
    #                  message_object,
    #                  thread_id,
    #                  thread_type,
    #                  args,
    #                  author_id=None):
    #     """Xử lý lệnh !reset - reset tất cả count về 0 (chỉ admin hoặc owner)"""
    #     try:
    #         # Danh sách ID được phép reset (thay bằng ID của bạn)
    #         authorized_users = ['5218488050389102343'
    #                             ]  # Thêm ID của bạn và admin khác

    #         if author_id not in authorized_users:
    #             self.send(Message(text="❌ Chỉ admin mới có thể reset count!"),
    #                       thread_id, thread_type)
    #             return

    #         # Reset tất cả count về 0
    #         if thread_id in self.count_data:
    #             for user_id in self.count_data[thread_id]:
    #                 self.count_data[thread_id][user_id] = 0
    #             self.save_data()
    #             self.send(Message(text="🔄 Đã reset tất cả count về 0!"),
    #                       thread_id, thread_type)
    #         else:
    #             self.send(Message(text="📊 Chưa có dữ liệu đếm nào để reset!"),
    #                       thread_id, thread_type)

    #     except Exception as e:
    #         print(f"{Fore.RED}Lỗi xử lý lệnh reset: {e}")
    #         self.send(Message(text="Có lỗi xảy ra khi reset count!"),
    #                   thread_id, thread_type)

    def onMessage(self, mid, author_id, message, message_object, thread_id,
                  thread_type):
        print(f"{Fore.GREEN}Received message:\n"
              f"- Message: {Style.BRIGHT}{message}{Style.NORMAL}\n"
              f"- Author ID: {Fore.CYAN}{author_id}\n"
              f"- Thread ID: {Fore.YELLOW}{thread_id}\n"
              f"- Thread Type: {Fore.BLUE}{thread_type}\n")

        try:
            self.update_message_count(thread_id, author_id)

            # Khởi tạo count cho user khi họ gửi tin nhắn lần đầu
            self.initialize_count_for_user(thread_id, author_id)

            if hasattr(message_object, 'content') and isinstance(
                    message_object.content, str):
                content = message_object.content.strip()
                if content.startswith(self.prefix):
                    command = content[len(self.prefix):].split()[0].lower(
                    ) if content[len(self.prefix):] else ""
                    args = content[len(self.prefix) +
                                   len(command):].strip().split()
                    if command in self.commands:
                        if author_id not in self.excluded_user_ids:
                            self.commands[command]["func"](self,
                                                           message_object,
                                                           thread_id,
                                                           thread_type, args,
                                                           author_id)
                        else:
                            self.send(
                                Message(
                                    text="Bạn không được phép sử dụng bot!"),
                                thread_id, thread_type)
                    elif command:
                        self.send(
                            Message(
                                text=
                                f"Lệnh `{self.prefix}{command}` không tồn tại. Gõ `{self.prefix}help` để xem danh sách lệnh."
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


def main():
    """Hàm main để chạy bot trực tiếp"""
    def access_website_periodically():
        """Truy cập website mỗi 10 phút liên tục"""
        while True:
            time.sleep(600)  # 10 phút = 600 giây
            try:
                # Thay thế URL này bằng website bạn muốn truy cập
                website_url = "https://66dde611-6b38-4f72-b477-82cfd474e992-00-37jxjgthrls3.janeway.replit.dev/health"
                response = requests.get(website_url, timeout=10)
                utc8_time = time.strftime('%a %b %d %H:%M:%S %Y', time.localtime())
                if response.status_code == 200:
                    print(f"{Fore.GREEN}✅ Đã truy cập website thành công lúc {utc8_time}")
                else:
                    print(f"{Fore.YELLOW}⚠️ Truy cập website thất bại với status: {response.status_code}")
            except Exception as e:
                print(f"{Fore.RED}❌ Lỗi truy cập website: {e}")

    # Khởi tạo client
    client = CustomClient('api_key',
                          'secret_key',
                          imei=imei,
                          session_cookies=session_cookies)

    # Chạy thread truy cập website định kỳ
    website_thread = threading.Thread(target=access_website_periodically, daemon=True)
    website_thread.start()
    print(f"{Fore.CYAN}🕐 Đã bắt đầu truy cập website mỗi 10 phút...")

    # Chạy bot
    client.listen()

if __name__ == "__main__":
    main()