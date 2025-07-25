from zlapi.models import Message

def handle(client, message_object, thread_id, thread_type, args, author_id=None):
    client.send(Message(
        text="🤖 Bot Python mẫu của bạn.\n"
             "📚 Viết bằng zlapi (Zalo bot API wrapper)\n"
             "🧠 Hỗ trợ lưu dữ liệu, xử lý lệnh cơ bản, nhóm đếm số...\n"
             f"📅 Bot khởi động lần đầu: {client.start_time.strftime('%d/%m/%Y %H:%M:%S')}"
    ), thread_id, thread_type)
