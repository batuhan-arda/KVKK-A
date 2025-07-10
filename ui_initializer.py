from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit,
    QPushButton, QLabel, QHBoxLayout,
    QScrollArea, QSizePolicy, QDialog, QComboBox,
    QCheckBox, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPalette, QColor
import sys
import threading
from chat_initializer import message_queue, response_queue, status_queue
from history_manager import load_history
from PyQt5.QtCore import QTimer
from settings import load_settings, save_settings
from config import TEXT_MODELS

def apply_theme(app, theme_name):
    dark = theme_name == "Koyu Tema"

    if dark:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 45))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(45, 45, 45))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)
        app.setStyle("Fusion")
    else:
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())

    # Global stil (butonlar, yazı kutuları, vs.)
    app.setStyleSheet(f"""
        QWidget {{
            color: {"white" if dark else "black"};
            background-color: {"#2e2e2e" if dark else "white"};
        }}
        QPushButton {{
            background-color: {"#3a3a3a" if dark else "#e0e0e0"};
            color: {"white" if dark else "black"};
            border: 1px solid {"#5c5c5c" if dark else "#b0b0b0"};
            padding: 6px 12px;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: {"#505050" if dark else "#d6d6d6"};
        }}
        QLineEdit, QTextEdit {{
            background-color: {"#3a3a3a" if dark else "white"};
            color: {"white" if dark else "black"};
            border: 1px solid {"#5c5c5c" if dark else "#ccc"};
            border-radius: 3px;
        }}
        QScrollArea {{
            background-color: transparent;
        }}
        QLabel {{
            color: {"white" if dark else "black"};
        }}
        QComboBox {{
            background-color: {"#3a3a3a" if dark else "white"};
            color: {"white" if dark else "black"};
            border: 1px solid {"#5c5c5c" if dark else "#ccc"};
        }}
        QCheckBox {{
            color: {"white" if dark else "black"};
        }}
    """)

class SettingsWindow(QDialog):
    # Tema değişikliği sinyali
    theme_changed = pyqtSignal(str)
    # Ayar değişikliği sinyali
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setGeometry(100, 100, 400, 350)

        self.settings = load_settings()
        self.dark_theme = self.settings.get("theme", "Açık Tema") == "Koyu Tema"

        layout = QVBoxLayout()

        # === Arayüz Bölmesi ===
        layout.addWidget(QLabel("<b>Arayüz</b>"))

        self.theme_dropdown = QComboBox()
        self.theme_dropdown.addItems(["Açık Tema", "Koyu Tema"])
        self.theme_dropdown.setCurrentText(self.settings.get("theme", "Sistem Teması"))
        layout.addWidget(QLabel("Renk Teması"))
        layout.addWidget(self.theme_dropdown)

        self.hide_history_checkbox = QCheckBox("Eski mesajları gösterme")
        self.hide_history_checkbox.setChecked(self.settings.get("hide_history", False))
        layout.addWidget(self.hide_history_checkbox)

        layout.addSpacing(20)

        # === Yapay Zeka Bölmesi ===
        layout.addWidget(QLabel("<b>Yapay Zeka</b>"))

        self.model_dropdown = QComboBox()
        for label in TEXT_MODELS:
            self.model_dropdown.addItem(label)
        current_model_id = self.settings.get("gemini_model", "gemini-2.5-pro")
        current_label = next((k for k, v in TEXT_MODELS.items() if v == current_model_id), "Gemini 2.5 Pro")
        self.model_dropdown.setCurrentText(current_label)
        layout.addWidget(QLabel("Gemini Modeli"))
        layout.addWidget(self.model_dropdown)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(self.settings.get("api_key", ""))
        layout.addWidget(QLabel("API Anahtarı"))
        layout.addWidget(self.api_key_input)

        layout.addStretch()

        save_btn = QPushButton("Kaydet ve Kapat")
        save_btn.clicked.connect(self.save_and_close)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_and_close(self):
        selected_label = self.model_dropdown.currentText()
        selected_model_id = TEXT_MODELS[selected_label]

        updated_settings = {
            "theme": self.theme_dropdown.currentText(),
            "hide_history": self.hide_history_checkbox.isChecked(),
            "gemini_model": selected_model_id,
            "api_key": self.api_key_input.text()
        }

        save_settings(updated_settings)
        apply_theme(QApplication.instance(), updated_settings["theme"])
        
        # Tema değişikliği sinyalini gönder
        self.theme_changed.emit(updated_settings["theme"])
        
        # Ayar değişikliği sinyalini gönder
        self.settings_changed.emit()
        
        self.accept()

class ChatBubble(QLabel):
    def __init__(self, text, is_user, dark_theme=False):
        super().__init__(text)
        self.is_user = is_user
        self.dark_theme = dark_theme
        self.setWordWrap(True)
        self.setMargin(0)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setAlignment(Qt.AlignRight if is_user else Qt.AlignLeft)

        self.apply_style()

    def apply_style(self):
        if self.dark_theme:
            user_color = "#5E9E60"
            assistant_color = "#3C3C3C"
            text_color = "white"
        else:
            user_color = "#DCF8C6"
            assistant_color = "#F1F0F0"
            text_color = "black"

        bg_color = user_color if self.is_user else assistant_color

        self.setStyleSheet(f"""
            background-color: {bg_color};
            color: {text_color};
            border-radius: 10px;
            padding: 8px;
            margin: 2px;
        """)

    def update_theme(self, dark_theme):
        self.dark_theme = dark_theme
        self.apply_style()


class ChatWindow(QWidget):
    message_received = pyqtSignal(str)
    status_received = pyqtSignal(str, str)  # Yeni: durum sinyali (tip, mesaj)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KVKK-A Chat")
        self.setGeometry(300, 100, 800, 600)

        self.settings = load_settings()
        self.dark_theme = self.settings.get("theme", "Açık Tema") == "Koyu Tema"

        QTimer.singleShot(0, self.scroll_to_bottom)

        # Ana layout
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        # Sağ kenar
        self.sidebar = QVBoxLayout()
        self.sidebar.setAlignment(Qt.AlignTop)

        self.settings_button = QPushButton("Ayarlar")
        self.settings_button.setMaximumWidth(120)
        self.settings_button.clicked.connect(self.open_settings)
        self.sidebar.addWidget(self.settings_button)

        # Durum göstergesi
        self.status_label = QLabel("✅ Hazır")
        self.status_label.setWordWrap(True)
        self.sidebar.addWidget(self.status_label)

        # Sohbet alanı
        self.chat_area = QVBoxLayout()
        self.chat_area.setAlignment(Qt.AlignTop)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.chat_area)
        self.scroll_area.setWidget(self.scroll_widget)

        # Mesaj giriş alanı
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("Mesaj yaz...")
        self.input_field.setFixedHeight(40)
        self.input_field.textChanged.connect(self.adjust_input_height)

        self.send_button = QPushButton("Gönder")
        self.send_button.clicked.connect(self.send_message)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        # Sol taraf
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(self.scroll_area)
        self.left_layout.addLayout(input_layout)

        self.main_layout.addLayout(self.left_layout, 5)
        self.main_layout.addLayout(self.sidebar, 1)

        # Geçmiş mesajları yükle
        self.load_old_messages()

        # Asistan cevaplarını dinleyen thread
        self.message_received.connect(self.display_assistant_reply)
        self.status_received.connect(self.update_status)
        self.listen_thread = threading.Thread(target=self.listen_response, daemon=True)
        self.listen_thread.start()

    def update_all_bubbles_theme(self, theme_name):
        """Tüm bubble'ların temasını günceller"""
        self.dark_theme = theme_name == "Koyu Tema"
        
        # Chat area'daki tüm bubble'ları bul ve güncelle
        for i in range(self.chat_area.count()):
            widget = self.chat_area.itemAt(i).widget()
            if widget and hasattr(widget, 'layout') and widget.layout():
                container_layout = widget.layout()
                for j in range(container_layout.count()):
                    item = container_layout.itemAt(j)
                    if item and item.widget() and isinstance(item.widget(), ChatBubble):
                        bubble = item.widget()
                        bubble.update_theme(self.dark_theme)

    def resizeEvent(self, event):
        # Bubble'ları yeniden boyutlandır
        available_width = self.scroll_area.width() - 40
        max_bubble_width = int(available_width * 0.8)
        
        for i in range(self.chat_area.count()):
            widget = self.chat_area.itemAt(i).widget()
            if widget and hasattr(widget, 'layout') and widget.layout():
                container_layout = widget.layout()
                for j in range(container_layout.count()):
                    item = container_layout.itemAt(j)
                    if item and item.widget() and isinstance(item.widget(), ChatBubble):
                        bubble = item.widget()
                        bubble.setMaximumWidth(max_bubble_width)
                        bubble.update_theme(self.dark_theme)
                        bubble.adjustSize()

        return super().resizeEvent(event)

    def adjust_input_height(self):
        doc_height = self.input_field.document().size().height()
        new_height = min(max(40, int(doc_height + 10)), 150)
        self.input_field.setFixedHeight(new_height)

    def open_settings(self):
        self.settings_window = SettingsWindow(self)
        # Tema değişikliği sinyalini bağla
        self.settings_window.theme_changed.connect(self.update_all_bubbles_theme)
        # Ayar değişikliği sinyalini bağla
        self.settings_window.settings_changed.connect(self.reload_chat_history)
        self.settings_window.exec_()

    def send_message(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return

        # Kullanıcı mesajı için container
        user_container = QWidget()
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 2, 0, 2)
        
        user_bubble = ChatBubble(text, is_user=True, dark_theme=self.dark_theme)
        user_bubble.adjustSize()
        
        available_width = self.scroll_area.width() - 40
        user_bubble.setMaximumWidth(int(available_width * 0.8))
        
        user_layout.addStretch()
        user_layout.addWidget(user_bubble)
        
        self.chat_area.addWidget(user_container)

        message_queue.put(text)
        self.input_field.clear()

        # "Asistan yazıyor..." balonu
        if hasattr(self, "typing_bubble") and self.typing_bubble:
            self.typing_bubble.setParent(None)

        typing_container = QWidget()
        typing_layout = QHBoxLayout(typing_container)
        typing_layout.setContentsMargins(0, 2, 0, 2)
        
        self.typing_bubble = ChatBubble("Asistan yazıyor...", is_user=False, dark_theme=self.dark_theme)
        self.typing_bubble.adjustSize()
        
        typing_layout.addWidget(self.typing_bubble)
        typing_layout.addStretch()
        
        self.chat_area.addWidget(typing_container)
        self.scroll_to_bottom()

    def listen_response(self):
        while True:
            # Mesaj kuyruğunu dinle
            if not response_queue.empty():
                reply = response_queue.get()
                self.message_received.emit(reply)
            
            # Durum kuyruğunu dinle
            if not status_queue.empty():
                status_type, status_msg = status_queue.get()
                self.status_received.emit(status_type, status_msg)

    @pyqtSlot(str, str)
    def update_status(self, status_type, status_msg):
        """Durum göstergesini günceller"""
        self.status_label.setText(status_msg)
        
        # Durum tipine göre renk değiştir
        if status_type == "error":
            color = "#ff6b6b" if self.dark_theme else "#d73027"
        elif status_type == "thinking":
            color = "#4ecdc4" if self.dark_theme else "#1a9850"
        elif status_type == "connecting":
            color = "#45b7d1" if self.dark_theme else "#313695"
        else:  # ready
            color = "#96ceb4" if self.dark_theme else "#74add1"
        
        self.status_label.setStyleSheet(f"""
            font-size: 12px; 
            padding: 5px; 
            color: {color}; 
            font-weight: bold;
        """)

    @pyqtSlot(str)
    def display_assistant_reply(self, reply):
        if hasattr(self, "typing_bubble") and self.typing_bubble:
            self.typing_bubble.parent().setParent(None)
            self.typing_bubble = None

        assistant_container = QWidget()
        assistant_layout = QHBoxLayout(assistant_container)
        assistant_layout.setContentsMargins(0, 2, 0, 2)
        
        assistant_bubble = ChatBubble(reply, is_user=False, dark_theme=self.dark_theme)
        assistant_bubble.adjustSize()
        
        available_width = self.scroll_area.width() - 40
        assistant_bubble.setMaximumWidth(int(available_width * 0.8))
        
        assistant_layout.addWidget(assistant_bubble)
        assistant_layout.addStretch()
        
        self.chat_area.addWidget(assistant_container)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        vsb = self.scroll_area.verticalScrollBar()
        vsb.setValue(vsb.maximum())

    def reload_chat_history(self):
        """Sohbet geçmişini yeniden yükler"""
        # Mevcut tüm mesajları temizle
        self.clear_chat_area()
        
        # Ayarları yeniden yükle ve geçmişi göster
        self.load_old_messages()
    
    def clear_chat_area(self):
        """Sohbet alanındaki tüm mesajları temizler"""
        while self.chat_area.count():
            child = self.chat_area.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def load_old_messages(self):
        history = load_history()
        
        # Ayarları kontrol et - "Eski mesajları gösterme" seçeneği
        current_settings = load_settings()
        hide_history = current_settings.get("hide_history", False)
        
        # Eğer "Eski mesajları gösterme" seçeneği açıksa, sadece son 2 mesajı göster
        if hide_history and len(history) > 2:
            history = history[-2:]
        
        for msg in history:
            bubble = ChatBubble(msg["content"], is_user=(msg["role"] == "user"), dark_theme=self.dark_theme)
            
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 2, 0, 2)
            
            bubble.adjustSize()
            
            if msg["role"] == "user":
                available_width = self.scroll_area.width() - 40
                bubble.setMaximumWidth(int(available_width * 0.8))
                
                layout.addStretch()
                layout.addWidget(bubble)
            else:
                available_width = self.scroll_area.width() - 40
                bubble.setMaximumWidth(int(available_width * 0.8))
                
                layout.addWidget(bubble)
                layout.addStretch()
            
            self.chat_area.addWidget(container)
        self.scroll_to_bottom()


def start_ui():
    app = QApplication(sys.argv)

    settings = load_settings()
    apply_theme(app, settings.get("theme", "Sistem Teması"))

    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())