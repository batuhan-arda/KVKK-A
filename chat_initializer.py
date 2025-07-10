import queue
import time
from history_manager import load_history, save_history

message_queue = queue.Queue()
response_queue = queue.Queue()

history = load_history()

import google.generativeai as genai
from config import API_KEY, MODEL_NAME, SYSTEM_PROMPT

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME)

def ask_model(messages):
    # Son 10 mesajı almak için kullanıcı ve asistan mesajlarını ayrı filtrele
    user_msgs = [msg for msg in messages if msg["role"] == "user"]
    assistant_msgs = [msg for msg in messages if msg["role"] == "assistant"]

    # last 5 messages
    last_users = user_msgs[-5:]
    last_assistants = assistant_msgs[-5:]

    # Mesajları zaman sırasına göre sıralamak için orijinal sırayla yeniden oluştur
    last_messages = []
    user_i = 0
    assi_i = 0
    for msg in messages[::-1]:  # sondan başa
        if msg in last_users and msg not in last_messages:
            last_messages.insert(0, msg)
            user_i += 1
        elif msg in last_assistants and msg not in last_messages:
            last_messages.insert(0, msg)
            assi_i += 1
        if user_i >= len(last_users) and assi_i >= len(last_assistants):
            break

    full_prompt = SYSTEM_PROMPT + "\n\n"
    for msg in last_messages:
        if msg["role"] == "user":
            full_prompt += f"Kullanıcı: {msg['content']}\n"
        elif msg["role"] == "assistant":
            full_prompt += f"Asistan: {msg['content']}\n"

    response = model.generate_content(full_prompt)
    return response.text.strip()

def start_chat_loop():
    while True:
        if not message_queue.empty():
            user_msg = message_queue.get()
            history.append({"role": "user", "content": user_msg})

            response = ask_model(history)
            history.append({"role": "assistant", "content": response})

            save_history(history)
            response_queue.put(response)

        time.sleep(0.1)
