from zlapi.models import Message
from config import PREFIX

def handle_help(client, message_object, thread_id, thread_type, args, author_id=None):
    response = "📜 Danh sách lệnh của bot 📜\n"
    for cmd, info in client.commands.items():
        response += f"{PREFIX}{cmd}: {info['desc']}\n"
    response += f"\nSử dụng {PREFIX}<lệnh> để gọi bot!"
    client.send(Message(text=response), thread_id, thread_type)