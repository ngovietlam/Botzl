from zlapi.models import Message

def handle(client, message_object, thread_id, thread_type, args, author_id=None):
    if not client.is_admin(author_id):
        client.send(Message(text="⛔ Bạn không có quyền reset."), thread_id, thread_type)
        return

    if thread_id in client.count_data:
        for uid in client.count_data[thread_id]:
            client.count_data[thread_id][uid] = 0
        client.save_data()
        client.send(Message(text="🔄 Đã reset tất cả số đếm về 0!"), thread_id, thread_type)
    else:
        client.send(Message(text="⚠️ Không có dữ liệu nào để reset."), thread_id, thread_type)
