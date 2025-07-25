from zlapi.models import Message

def handle(client, message_object, thread_id, thread_type, args, author_id=None):
    client.send(Message(text="✅ Bot đang hoạt động!"), thread_id, thread_type)
