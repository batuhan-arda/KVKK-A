import json
import os
from PyQt5.QtWidgets import QMessageBox
from config import DIR, HISTORY_FILE, MAX_HISTORY

HISTORY_PATH = os.path.join(DIR, HISTORY_FILE)


def show_error_popup(title, message):
    """Hata durumunda bir popup uyarı gösterir."""
    box = QMessageBox()
    box.setWindowTitle(title)
    box.setIcon(QMessageBox.Critical)
    box.setText(message)
    box.exec_()


def load_history():
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    if os.path.exists(HISTORY_PATH):
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            show_error_popup("Geçmiş Yüklenemedi", f"Geçmiş dosyası okunurken bir hata oluştu:\n{e}")
    return []


def save_history(history):
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    # En fazla MAX_HISTORY kadar mesaj sakla
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        show_error_popup("Geçmiş Kaydedilemedi", f"Geçmiş dosyası kaydedilirken bir hata oluştu:\n{e}")
