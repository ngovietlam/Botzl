from zlapi.models import Message

def handle(client, message_object, thread_id, thread_type, args, author_id=None):
    response = "📜 **Danh sách lệnh của bot** 📜\n"
    for cmd, info in client.commands.items():
        response += f"**{client.prefix}{cmd}**: {info['desc']}\n"
    response += f"\nSử dụng `{client.prefix}<lệnh>` để gọi bot!"
    client.send(Message(text=response), thread_id, thread_type)