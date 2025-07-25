import json
from colorama import Fore

def fetch_user_info(client, user_id):
    try:
        user_info = client.fetchUserInfo(user_id)
        if isinstance(user_info, str):
            user_info = json.loads(user_info)
        if 'changed_profiles' in user_info and user_id in user_info['changed_profiles']:
            zalo_name = user_info['changed_profiles'][user_id].get('zaloName', None)
            return zalo_name or user_info['changed_profiles'][user_id].get('displayName', user_id)
        return user_id
    except Exception as e:
        print(f"{Fore.RED}Lỗi lấy thông tin người dùng: {e}")
        return user_id