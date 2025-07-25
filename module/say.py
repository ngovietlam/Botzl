from zlapi.models import Message

def handle(client, message_object, thread_id, thread_type, args, author_id=None):
    if args:
            response = "🗣️ Bạn nói: " + " ".join(args)
            client.send(Message(text=response), thread_id, thread_type)
    else:
            client.send(
                Message(text="Vui lòng nhập nội dung! Ví dụ: !say Xin chào"),
                thread_id, thread_type)
