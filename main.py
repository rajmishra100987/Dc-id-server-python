import os
import json
import uuid
import asyncio
import threading
import time
from flask import Flask, request, jsonify, Response, render_template_string

# ✅ fbchat-v2 इम्पोर्ट्स
from _core._session import dataGetHome
from _messaging._send import api as SendAPI

app = Flask(__name__)

# Active tasks स्टोर करने के लिए
tasks = {}

# ============================================================
# 🔥 EMBEDDED HTML + CSS + JS (Pink + Creamy + White Theme)
# ============================================================
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VAMPIRE RULEX — Messenger Bot</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, sans-serif; }
    body {
        background: linear-gradient(135deg, #fff5f7 0%, #fde8ef 40%, #fffaf5 100%);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    .container {
        width: 100%;
        max-width: 640px;
        background: #ffffff;
        border-radius: 22px;
        padding: 34px;
        box-shadow: 0 20px 60px rgba(255, 105, 150, 0.18), 0 4px 16px rgba(0,0,0,0.04);
        border: 1px solid #ffe3ec;
    }
    .header {
        text-align: center;
        margin-bottom: 26px;
        padding-bottom: 20px;
        border-bottom: 2px dashed #ffd6e3;
    }
    .header h1 {
        font-size: 26px;
        background: linear-gradient(90deg, #ff4d88, #ff8bb3, #ff4d88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .header .owner {
        font-size: 13px;
        color: #b86a85;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .badge {
        display: inline-block;
        background: #fff0f5;
        color: #d6336c;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        margin-top: 8px;
        border: 1px solid #ffd6e3;
    }
    label {
        display: block;
        font-size: 13px;
        font-weight: 600;
        color: #8a3e5c;
        margin-bottom: 6px;
        margin-top: 14px;
    }
    input, textarea {
        width: 100%;
        padding: 12px 14px;
        border: 1.5px solid #ffe3ec;
        border-radius: 12px;
        background: #fffafc;
        font-size: 14px;
        color: #4a2b38;
        transition: all 0.25s;
        outline: none;
    }
    input:focus, textarea:focus {
        border-color: #ff8bb3;
        background: #ffffff;
        box-shadow: 0 0 0 4px rgba(255, 139, 179, 0.12);
    }
    textarea { resize: vertical; min-height: 90px; font-family: 'Courier New', monospace; font-size: 12px; }
    .file-input {
        padding: 10px;
        cursor: pointer;
        background: #fff5f8;
    }
    .btn {
        width: 100%;
        padding: 14px;
        margin-top: 22px;
        background: linear-gradient(135deg, #ff5c8a, #ff87ad);
        color: #fff;
        border: none;
        border-radius: 12px;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 1px;
        cursor: pointer;
        transition: all 0.25s;
        box-shadow: 0 8px 20px rgba(255, 92, 138, 0.3);
    }
    .btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 28px rgba(255, 92, 138, 0.42);
    }
    .btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
    .log-box {
        margin-top: 22px;
        background: #fffaf5;
        border: 1.5px solid #ffe3ec;
        border-radius: 14px;
        padding: 14px;
        max-height: 260px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        color: #5c3040;
        display: none;
    }
    .log-box.active { display: block; }
    .log-box::-webkit-scrollbar { width: 6px; }
    .log-box::-webkit-scrollbar-thumb { background: #ffb8ce; border-radius: 10px; }
    .log-line { padding: 3px 0; border-bottom: 1px dotted #ffe3ec; }
    .footer {
        text-align: center;
        margin-top: 24px;
        padding-top: 16px;
        border-top: 1px solid #ffe3ec;
        font-size: 12px;
        color: #b86a85;
    }
    .footer b { color: #d6336c; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    @media (max-width: 520px) { .grid-2 { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🩸 VAMPIRE RULEX 🩸</h1>
        <div class="owner">Owner: Raj Mishra</div>
        <span class="badge">⚡ Messenger.com Cookie Bot</span>
    </div>

    <form id="botForm">
        <label>🍪 Messenger.com Cookies (Raw String)</label>
        <textarea id="cookies" name="cookies" placeholder="c_user=...; xs=...; fr=...; datr=...;" required></textarea>

        <div class="grid-2">
            <div>
                <label>🆔 Thread ID</label>
                <input type="text" id="thread_id" name="thread_id" placeholder="e.g. 10001234567890" required>
            </div>
            <div>
                <label>💬 Name Prefix</label>
                <input type="text" id="hater_name" name="hater_name" placeholder="e.g. Raj" required>
            </div>
        </div>

        <label>⏱️ Delay (seconds)</label>
        <input type="number" id="delay" name="delay" value="5" min="1" step="1" required>

        <label>📄 Message File (.txt)</label>
        <input type="file" id="message_file" name="message_file" class="file-input" accept=".txt" required>

        <button type="submit" class="btn" id="startBtn">🚀 START BOT</button>
    </form>

    <div class="log-box" id="logBox"></div>

    <div class="footer">
        Developed with 💖 by <b>VAMPIRE RULEX</b> • Owner: <b>Raj Mishra</b>
    </div>
</div>

<script>
    const form = document.getElementById('botForm');
    const logBox = document.getElementById('logBox');
    const startBtn = document.getElementById('startBtn');

    function appendLog(msg) {
        const line = document.createElement('div');
        line.className = 'log-line';
        line.textContent = msg;
        logBox.appendChild(line);
        logBox.scrollTop = logBox.scrollHeight;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        logBox.innerHTML = '';
        logBox.classList.add('active');
        startBtn.disabled = true;
        startBtn.textContent = '⏳ Starting...';

        const formData = new FormData(form);

        try {
            const res = await fetch('/start', { method: 'POST', body: formData });
            const data = await res.json();

            if (data.error) {
                appendLog('❌ Error: ' + data.error);
                startBtn.disabled = false;
                startBtn.textContent = '🚀 START BOT';
                return;
            }

            appendLog('✅ Task started with ID: ' + data.task_id);
            const evtSource = new EventSource('/stream/' + data.task_id);

            evtSource.onmessage = (event) => {
                appendLog(event.data);
                if (event.data.includes('[TASK STOPPED]')) {
                    evtSource.close();
                    startBtn.disabled = false;
                    startBtn.textContent = '🚀 START BOT';
                }
            };
            evtSource.onerror = () => evtSource.close();

        } catch (err) {
            appendLog('❌ Network Error: ' + err.message);
            startBtn.disabled = false;
            startBtn.textContent = '🚀 START BOT';
        }
    });
</script>
</body>
</html>
"""

# ============================================================
# 🔧 BACKEND LOGIC
# ============================================================

def validate_cookie_string(cookie_input):
    """fbchat-v2 सिर्फ raw cookie string लेता है, JSON नहीं।"""
    cookie_input = (cookie_input or "").strip()
    if not cookie_input:
        raise ValueError("Cookie string खाली है।")
    if cookie_input.startswith('[') or cookie_input.startswith('{'):
        raise ValueError("Raw cookie string चाहिए (जैसे 'c_user=...; xs=...;'), JSON नहीं।")
    return cookie_input


async def bot_worker(task_id, cookie_string, thread_id, hater_name, delay, messages):
    def log(msg):
        if task_id in tasks:
            tasks[task_id]["logs"].append(msg)

    # 1) Login via messenger.com cookies
    try:
        log("🔄 Logging in to Messenger via cookies...")
        data_fb = await dataGetHome(cookie_string)
        if data_fb is None:
            raise RuntimeError("Session नहीं बन सका — कुकीज़ अमान्य या expired हो सकती हैं।")
        log("✅ Login Successful! Session created.")
    except Exception as e:
        log(f"❌ Login Error: {str(e)}")
        tasks[task_id]["status"] = "stopped"
        return

    # 2) Messaging loop
    msg_index = 0
    while task_id in tasks and tasks[task_id]["status"] == "running":
        if not messages:
            log("❌ Error: Messages list खाली है!")
            break

        current_message = messages[msg_index].strip()
        if current_message:
            formatted_msg = f"{hater_name} {current_message}"
            try:
                await SendAPI().send(
                    data_fb,
                    formatted_msg,
                    threadID=thread_id,
                    typeChat=None,
                )
                log(f"📤 Sent: {formatted_msg}")
            except Exception as e:
                log(f"⚠️ Send Error: {str(e)}")

        msg_index = (msg_index + 1) % len(messages)
        await asyncio.sleep(delay)

    log("🛑 Task stopped.")


@app.route('/')
def index():
    return render_template_string(HTML_PAGE)


@app.route('/start', methods=['POST'])
def start_bot():
    try:
        cookie_input = request.form.get('cookies')
        thread_id = request.form.get('thread_id')
        hater_name = request.form.get('hater_name')
        delay = float(request.form.get('delay', 5))

        try:
            cookie_string = validate_cookie_string(cookie_input)
        except Exception as e:
            return jsonify({"error": str(e)}), 400

        if 'message_file' not in request.files:
            return jsonify({"error": "Message file जरूरी है!"}), 400

        file = request.files['message_file']
        if file.filename == '':
            return jsonify({"error": "कोई फाइल सेलेक्ट नहीं की गई!"}), 400

        messages = file.read().decode('utf-8').splitlines()
        messages = [m for m in messages if m.strip()]
        if not messages:
            return jsonify({"error": "अपलोड की गई फाइल खाली है!"}), 400

        task_id = str(uuid.uuid4())[:8]
        tasks[task_id] = {
            "status": "running",
            "logs": [f"🚀 Task initialized: {task_id} | Owner: Raj Mishra"],
        }

        def run_async_loop():
            asyncio.run(bot_worker(task_id, cookie_string, thread_id, hater_name, delay, messages))

        threading.Thread(target=run_async_loop, daemon=True).start()
        return jsonify({"success": True, "task_id": task_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/stream/<task_id>')
def stream(task_id):
    def generate():
        last_len = 0
        while task_id in tasks:
            logs = tasks[task_id]["logs"]
            if len(logs) > last_len:
                for i in range(last_len, len(logs)):
                    yield f"data: {logs[i]}\n\n"
                last_len = len(logs)

            if tasks[task_id]["status"] == "stopped" and last_len >= len(logs):
                yield "data: [TASK STOPPED]\n\n"
                break
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
