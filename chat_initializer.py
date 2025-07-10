import queue
import time
from history_manager import load_history, save_history
from settings import load_settings
from config import SYSTEM_PROMPT
import google.generativeai as genai

# Mesaj ve cevap kuyrukları
message_queue = queue.Queue()
response_queue = queue.Queue()
status_queue = queue.Queue()  # Yeni: durum bildirimi için

# Mesaj geçmişi
history = load_history()

def ask_model(messages, model, prompt):
    try:
        # Son 5 kullanıcı ve 5 asistan mesajı
        user_msgs = [msg for msg in messages if msg["role"] == "user"][-5:]
        assistant_msgs = [msg for msg in messages if msg["role"] == "assistant"][-5:]

        # Zaman sırasını koruyarak birleştir
        last_messages = []
        user_i = assi_i = 0
        for msg in messages[::-1]:
            if msg in user_msgs and msg not in last_messages:
                last_messages.insert(0, msg)
                user_i += 1
            elif msg in assistant_msgs and msg not in last_messages:
                last_messages.insert(0, msg)
                assi_i += 1
            if user_i >= len(user_msgs) and assi_i >= len(assistant_msgs):
                break

        # Prompt + geçmiş mesajlar
        full_prompt = prompt + "\n\n"
        for msg in last_messages:
            if msg["role"] == "user":
                full_prompt += f"Kullanıcı: {msg['content']}\n"
            elif msg["role"] == "assistant":
                full_prompt += f"Asistan: {msg['content']}\n"

        status_queue.put(("thinking", "🤔 Yapay zeka düşünüyor..."))
        response = model.generate_content(full_prompt)
        status_queue.put(("ready", "✅ Hazır"))
        return response.text.strip()
    
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg.lower():
            status_queue.put(("error", "🔑 API anahtarı hatası"))
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            status_queue.put(("error", "⚠️ API kotası doldu"))
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            status_queue.put(("error", "🌐 Bağlantı hatası"))
        else:
            status_queue.put(("error", f"❌ Hata: {error_msg[:50]}..."))
        raise

def start_chat_loop():
    while True:
        if not message_queue.empty():
            try:
                user_msg = message_queue.get()
                history.append({"role": "user", "content": user_msg})

                # En güncel ayarları oku
                settings = load_settings()
                api_key = settings.get("api_key", "")
                model_name = settings.get("gemini_model", "gemini-2.5-flash")
                system_prompt = SYSTEM_PROMPT

                if not api_key:
                    status_queue.put(("error", "🔑 API anahtarı eksik"))
                    response_queue.put("API anahtarı ayarlanmamış. Lütfen ayarlardan API anahtarınızı girin.")
                    continue

                status_queue.put(("connecting", "🔄 Gemini'ye bağlanıyor..."))
                
                # Gemini'yı yapılandır
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)

                # Modelden cevap al
                response = ask_model(history, model, system_prompt)
                history.append({"role": "assistant", "content": response})

                # Kaydet & sıraya ekle
                save_history(history)
                response_queue.put(response)
                status_queue.put(("ready", "✅ Hazır"))

            except Exception as e:
                error_msg = str(e)
                if "API key" in error_msg.lower():
                    status_queue.put(("error", "🔑 API anahtarı geçersiz"))
                    response_queue.put("API anahtarı geçersiz. Lütfen ayarlardan kontrol edin.")
                elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                    status_queue.put(("error", "⚠️ API kotası doldu"))
                    response_queue.put("API kotanız dolmuş. Lütfen daha sonra tekrar deneyin.")
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    status_queue.put(("error", "🌐 İnternet bağlantı sorunu"))
                    response_queue.put("İnternet bağlantısı sorunu. Lütfen bağlantınızı kontrol edin.")
                else:
                    status_queue.put(("error", f"❌ Bilinmeyen hata"))
                    response_queue.put(f"Bir hata oluştu: {error_msg}")

        time.sleep(0.1)