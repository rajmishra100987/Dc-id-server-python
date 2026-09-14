import os
import json
import uuid
import asyncio
import threading
import time
from flask import Flask, render_template, request, jsonify, Response
import fbchat

app = Flask(__name__)

# Active tasks store karne ke liye dictionary
tasks = {}

async def bot_worker(task_id, cookies, thread_id, hater_name, delay, messages):
    def log(msg):
        if task_id in tasks:
            tasks[task_id]["logs"].append(msg)

    try:
        log("🔄 Logging in to Messenger via cookies...")
        session = await fbchat.Session.from_cookies(cookies, domain="messenger.com")
        log("✅ Login Successful!")
    except Exception as e:
        log(f"❌ Login Error / Bug: {str(e)}")
        tasks[task_id]["status"] = "stopped"
        return

    msg_index = 0
    while task_id in tasks and tasks[task_id]["status"] == "running":
        if not messages:
            log("❌ Error: Messages list is empty!")
            break

        current_message = messages[msg_index].strip()
        if current_message:
            formatted_msg = f"{hater_name} {current_message}"
            try:
                # Correct method: Pehle thread fetch karein, phir text bhejein
                thread = await session.fetch_thread(thread_id)
                await thread.send_text(formatted_msg)
                log(f"📤 Sent: {formatted_msg}")
            except Exception as e:
                log(f"⚠️ Message Send Error / Bug: {str(e)}")

        # Index update for infinite loop
        msg_index = (msg_index + 1) % len(messages)
        
        # Time delay handling
        await asyncio.sleep(delay)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_bot():
    try:
        cookies_input = request.form.get('cookies')
        thread_id = request.form.get('thread_id')
        hater_name = request.form.get('hater_name')
        delay = float(request.form.get('delay', 5))
        
        # Parse JSON cookies
        try:
            cookies = json.loads(cookies_input)
        except Exception as e:
            return jsonify({"error": "Invalid JSON format in cookies!"}), 400

        # Handle message file upload
        if 'message_file' not in request.files:
            return jsonify({"error": "Message file is required!"}), 400
        
        file = request.files['message_file']
        if file.filename == '':
            return jsonify({"error": "No file selected!"}), 400

        messages = file.read().decode('utf-8').splitlines()
        messages = [msg for msg in messages if msg.strip()]

        if not messages:
            return jsonify({"error": "Uploaded file is empty!"}), 400

        # Generate unique Task ID
        task_id = str(uuid.uuid4())[:8]
        
        tasks[task_id] = {
            "status": "running",
            "logs": [f"🚀 Task initialized with ID: {task_id}"]
        }

        # Background thread execution
        def run_async_loop():
            asyncio.run(bot_worker(task_id, cookies, thread_id, hater_name, delay, messages))

        thread = threading.Thread(target=run_async_loop)
        thread.daemon = True
        thread.start()

        return jsonify({"success": True, "task_id": task_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stream/<task_id>')
def stream(task_id):
    def generate():
        last_len = 0
        while task_id in tasks:
            current_logs = tasks[task_id]["logs"]
            if len(current_logs) > last_len:
                for i in range(last_len, len(current_logs)):
                    yield f"data: {current_logs[i]}\n\n"
                last_len = len(current_logs)
            
            if tasks[task_id]["status"] == "stopped" and last_len >= len(current_logs):
                yield "data: [TASK STOPPED]\n\n"
                break
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
