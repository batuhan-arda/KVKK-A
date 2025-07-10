import json
import os
from PyQt5.QtWidgets import QMessageBox
from config import DIR, SETTINGS_FILE, DEFAULT_SETTINGS

SETTINGS_PATH = os.path.join(DIR, SETTINGS_FILE)


def show_error_popup(title, message):
    """Hata durumunda bir popup uyarı gösterir."""
    box = QMessageBox()
    box.setWindowTitle(title)
    box.setIcon(QMessageBox.Critical)
    box.setText(message)
    box.exec_()


def load_settings():
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return {**DEFAULT_SETTINGS, **data}
        except Exception as e:
            show_error_popup("Ayarlar Yüklenemedi", f"Ayarlar dosyası okunurken bir hata oluştu:\n{e}")
    return DEFAULT_SETTINGS.copy()


def save_settings(data):
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        show_error_popup("Ayarlar Kaydedilemedi", f"Ayarlar dosyası kaydedilirken bir hata oluştu:\n{e}")
