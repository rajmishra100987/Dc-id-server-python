import asyncio
import os
import logging
import threading
import time
from flask import Flask, jsonify

from fbchat_v2._core._session import dataGetHome
from fbchat_v2._messaging._send import api as SendAPI

# 🔇 Terminal Silence (RAM & CPU Save)
logging.disable(logging.CRITICAL)

# ==================== FLASK WEB SERVER (For Render 200 OK) ====================
app = Flask(__name__)
START_TIME = time.time()

# ✅ GET और HEAD दोनों को सपोर्ट करने के लिए साफ-साफ मेंशन किया गया है
@app.route('/', methods=['GET', 'HEAD'])
def home():
    return "Bot is Running ✅", 200

@app.route('/ping', methods=['GET', 'HEAD'])
def ping():
    return "Pong", 200

@app.route('/health', methods=['GET', 'HEAD'])
def health():
    return jsonify({
        "status": "ONLINE",
        "uptime": round(time.time() - START_TIME),
        "message": "Server is Active!"
    }), 200
# ==============================================================================

def read_file(filename, default=""):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception:
        pass
    return default

async def bot_worker():
    while True:
        cookie_string = read_file('cookies.txt')
        thread_id = read_file('convo.txt')
        hater_name = read_file('hatersname.txt')
        
        try:
            delay = int(read_file('time.txt', '60'))
        except ValueError:
            delay = 60
            
        messages_raw = read_file('messages.txt')
        messages = [m.strip() for m in messages_raw.splitlines() if m.strip()]

        # Validation
        if not cookie_string or not thread_id or not messages:
            await asyncio.sleep(10)
            continue

        data_fb = None # ✅ Memory cleanup variable
        try:
            # Login via cookies
            data_fb = await dataGetHome(cookie_string)
            if data_fb is None:
                raise RuntimeError("Invalid Cookies")
            
            msg_index = 0
            loop_count = 1

            # ===== INNER MESSAGE LOOP =====
            while True:
                current_delay = int(read_file('time.txt', str(delay)) or 60)
                current_hater = read_file('hatersname.txt')
                current_msgs_raw = read_file('messages.txt')
                current_msgs = [m.strip() for m in current_msgs_raw.splitlines() if m.strip()] if current_msgs_raw else messages

                if not current_msgs:
                    await asyncio.sleep(10)
                    continue

                if msg_index >= len(current_msgs):
                    msg_index = 0
                    loop_count += 1

                raw_msg = current_msgs[msg_index]
                final_message = f"{current_hater} {raw_msg}" if current_hater else raw_msg

                try:
                    result = await SendAPI().send(data_fb, final_message, threadID=thread_id)
                    if result.get("error"):
                        break # Break loop on error to trigger auto-reconnect
                except Exception:
                    break # Break loop on exception to trigger auto-reconnect

                msg_index += 1
                await asyncio.sleep(current_delay)

        except Exception:
            # Wait 30 seconds before retrying (Prevents ID checkpoint)
            await asyncio.sleep(30)
        finally:
            # ✅ CRITICAL: Cleanup to prevent memory crash
            data_fb = None 
            await asyncio.sleep(2) # Short cooldown

# Function to start Flask in a separate thread so it doesn't block the bot
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    # use_reloader=False जरूरी है ताकि Render पर डबल थ्रेड शुरू न हो
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    # 1. Start Flask web server in background thread (For Render Health Check)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # 2. Start the Bot Loop
    try:
        asyncio.run(bot_worker())
    except KeyboardInterrupt:
        pass
