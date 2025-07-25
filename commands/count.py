from zlapi.models import Message
from colorama import Fore
from utils.user_info import fetch_user_info

def handle_count(client, message_object, thread_id, thread_type, args, author_id=None):
    try:
        if thread_id not in client.message_counts:
            client.message_counts[thread_id] = {}
        counts = client.message_counts[thread_id]
        if not counts:
            response = "Chưa có tin nhắn nào trong nhóm này."
        else:
            sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10]
            response = "📊 Top 10 người gửi tin nhắn nhiều nhất 📊\n"
            for user_id, count in sorted_counts:
                display_name = fetch_user_info(client, user_id)
                response += f"{display_name} ({user_id}): {count} tin nhắn\n"
        client.send(Message(text=response), thread_id, thread_type)
        client.data_handler.save_data()
    except Exception as e:
        client.send(Message(text=f"Lỗi: {str(e)}"), thread_id, thread_type)
        print(f"{Fore.RED}Lỗi xử lý !count: {e}")