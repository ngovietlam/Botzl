from zlapi.models import Message

def handle(client, message_object, thread_id, thread_type, args, author_id=None):
    if thread_id not in client.count_data or not client.count_data[thread_id]:
        client.send(Message(text="❌ Chưa có ai đếm trong nhóm này!"), thread_id, thread_type)
        return

    sorted_users = sorted(client.count_data[thread_id].items(), key=lambda x: x[1], reverse=True)
    top_text = "🏆 Bảng xếp hạng đếm số:\n"
    for i, (user_id, count) in enumerate(sorted_users[:5], start=1):
        user_name = client.get_user_display_name(user_id)
        top_text += f"{i}. {user_name}: {count}\n"
    client.send(Message(text=top_text), thread_id, thread_type)
