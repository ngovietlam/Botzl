from zlapi.models import Message

def handle(client, message_object, thread_id, thread_type, args, author_id=None):
    client.initialize_count_for_user(thread_id, author_id)
    client.count_data[thread_id][author_id] += 1
    count = client.count_data[thread_id][author_id]
    client.save_data()
    client.send(Message(text=f"🧮 Bạn đã đếm được: {count}"), thread_id, thread_type)
