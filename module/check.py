from zlapi.models import Message

def handle(client, message_object, thread_id, thread_type, args, author_id=None):
    client.initialize_count_for_user(thread_id, author_id)
    count = client.count_data[thread_id][author_id]
    client.send(Message(text=f"🔍 Số hiện tại của bạn: {count}"), thread_id, thread_type)
