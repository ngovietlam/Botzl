from zlapi.models import Message
from config import PREFIX

def handle_info(client, message_object, thread_id, thread_type, args, author_id=None):
    response = "🤖 Thông tin về bot 🤖\n"
    response += f"Tên: Zalo Bot\nPhiên bản: 1.0\nTác giả: Hoàng Minh\nPrefix: {PREFIX}\nMô tả: Bot cơ bản cho Zalo."
    client.send(Message(text=response), thread_id, thread_type)