import json
import os
from config import HISTORY_DIR, HISTORY_FILE, MAX_HISTORY

HISTORY_PATH = os.path.join(HISTORY_DIR, HISTORY_FILE)

def load_history():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[!] Geçmiş yüklenirken hata: {e}")
    return []

def save_history(history):
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

    # En fazla MAX_HISTORY kadar mesaj sakla
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[!] Geçmiş kaydedilirken hata: {e}")
