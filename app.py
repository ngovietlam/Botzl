from flask import Flask, jsonify
import threading
import time
import requests
from datetime import datetime, timezone, timedelta
from main import CustomClient
from config import imei, session_cookies

app = Flask(__name__)

# Biến global để lưu trữ bot client
bot_client = None
bot_thread = None
keep_alive_thread = None

@app.route('/')
def home():
    return jsonify({
        'message': 'Zalo Bot Server đang chạy',
        'status': 'running',
        'bot_status': 'active' if bot_client else 'stopped'
    })

@app.route('/ping')
def ping():
    utc8_time = datetime.now(timezone(timedelta(hours=8)))
    print(f"✅ Ping endpoint được gọi lúc {utc8_time.strftime('%a %b %d %H:%M:%S %Y')} (UTC+8)")
    return jsonify({
        'status': 'alive',
        'message': 'Bot is running',
        'timestamp': time.time(),
        'local_time': utc8_time.strftime('%Y-%m-%d %H:%M:%S UTC+8')
    })

@app.route('/health')
def health():
    """Endpoint đơn giản cho UptimeRobot - luôn trả về 200 OK"""
    try:
        utc8_time = datetime.now(timezone(timedelta(hours=8)))
        print(f"✅ Health check lúc {utc8_time.strftime('%a %b %d %H:%M:%S %Y')} (UTC+8)")
        return "OK", 200
    except Exception as e:
        # Ngay cả khi có lỗi, vẫn trả về OK để UptimeRobot không báo down
        print(f"⚠️ Health check có lỗi nhưng vẫn trả về OK: {e}")
        return "OK", 200

@app.route('/status')
def status():
    return jsonify({
        'bot_running': bot_client is not None,
        'thread_alive': bot_thread.is_alive() if bot_thread else False,
        'keep_alive_active': keep_alive_thread.is_alive() if keep_alive_thread else False,
        'uptime': time.time()
    })

@app.route('/restart')
def restart_bot():
    global bot_client, bot_thread
    try:
        # Dừng bot cũ nếu có
        if bot_client:
            bot_client.stop_listening()

        # Khởi tạo bot mới
        bot_client = CustomClient('api_key', 'secret_key', imei=imei, session_cookies=session_cookies)

        # Chạy bot trong thread riêng
        bot_thread = threading.Thread(target=bot_client.listen, daemon=True)
        bot_thread.start()

        return jsonify({
            'status': 'success',
            'message': 'Bot đã được khởi động lại'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Lỗi khởi động bot: {str(e)}'
        }), 500

def external_keep_alive():
    """Gửi ping định kỳ để giữ bot không bị ngủ"""
    current_repl_url = "https://66dde611-6b38-4f72-b477-82cfd474e992-00-37jxjgthrls3.janeway.replit.dev"  # URL development của Replit

    while True:
        try:
            time.sleep(900)  # 15 phút ping một lần
            response = requests.get(f"{current_repl_url}/ping", timeout=10)
            utc8_time = datetime.now(timezone(timedelta(hours=8)))
            if response.status_code == 200:
                print(f"✅ Keep-alive ping thành công lúc {utc8_time.strftime('%a %b %d %H:%M:%S %Y')} (UTC+8)")
            else:
                print(f"⚠️ Keep-alive ping thất bại với status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi keep-alive ping: {e}")
        except Exception as e:
            print(f"❌ Lỗi không mong muốn trong keep-alive: {e}")

def start_bot():
    """Khởi động bot trong thread riêng"""
    global bot_client, bot_thread, keep_alive_thread
    try:
        bot_client = CustomClient('api_key', 'secret_key', imei=imei, session_cookies=session_cookies)
        bot_thread = threading.Thread(target=bot_client.listen, daemon=True)
        bot_thread.start()

        # Khởi động keep-alive thread
        keep_alive_thread = threading.Thread(target=external_keep_alive, daemon=True)
        keep_alive_thread.start()

        print("✅ Bot đã được khởi động thành công!")
        print("🔄 Keep-alive mechanism đã được kích hoạt!")
    except Exception as e:
        print(f"❌ Lỗi khởi động bot: {e}")

if __name__ == '__main__':
    # Khởi động bot trước
    start_bot()

    # Chạy Flask server với binding rõ ràng
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)