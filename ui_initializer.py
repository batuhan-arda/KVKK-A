from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit,
    QPushButton, QLabel, QHBoxLayout,
    QScrollArea, QSizePolicy, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
import sys
import threading
from chat_initializer import message_queue, response_queue
from history_manager import load_history
from PyQt5.QtCore import QTimer


class SettingsWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ayarlar")
        self.setGeometry(100, 100, 300, 200)
        
        layout = QVBoxLayout()
        
        test_button = QPushButton("Test Butonu")
        test_button.clicked.connect(self.test_action)
        layout.addWidget(test_button)
        
        self.setLayout(layout)
    
    def test_action(self):
        print("Test butonu tıklandı!")


class ChatBubble(QLabel):
    def __init__(self, text, is_user):
        super().__init__(text)
        self.setWordWrap(True)
        self.setMargin(0)
        self.setContentsMargins(0, 0, 0, 0)
        
        # Bubble stilini ayarla
        self.setStyleSheet(
            "background-color: %s; border-radius: 10px; padding: 8px; margin: 2px;" %
            ("#DCF8C6" if is_user else "#F1F0F0")
        )

        # Boyut politikasını ayarla
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        # Metin seçilebilir yap
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Metni hizala: kullanıcı sağa, asistan sola
        self.setAlignment(Qt.AlignRight if is_user else Qt.AlignLeft)
        
        # Metin boyutuna göre otomatik boyutlandır
        self.adjustSize()


class ChatWindow(QWidget):
    message_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KVKK-A Chat")
        self.setGeometry(300, 100, 800, 600)
        QTimer.singleShot(0, self.scroll_to_bottom)

        # Ana layout
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        # Sağ kenar
        self.sidebar = QVBoxLayout()
        self.sidebar.setAlignment(Qt.AlignTop)

        self.settings_button = QPushButton("Ayarlar")
        self.settings_button.setMaximumWidth(120)  # Butonu küçült
        self.settings_button.clicked.connect(self.open_settings)
        self.sidebar.addWidget(self.settings_button)

        self.about_label = QLabel("<i>KVKK-A uygulaması...</i>")
        self.about_label.setWordWrap(True)
        self.sidebar.addWidget(self.about_label)

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
        self.listen_thread = threading.Thread(target=self.listen_response, daemon=True)
        self.listen_thread.start()

    def resizeEvent(self, event):
        # Bubble'ları yeniden boyutlandır
        available_width = self.scroll_area.width() - 40  # Scroll bar için boşluk
        max_bubble_width = int(available_width * 0.8)  # %80'ini kullan
        
        for i in range(self.chat_area.count()):
            widget = self.chat_area.itemAt(i).widget()
            if widget and hasattr(widget, 'layout') and widget.layout():
                # Container widget'ın layout'una erişim
                container_layout = widget.layout()
                for j in range(container_layout.count()):
                    item = container_layout.itemAt(j)
                    if item and item.widget() and isinstance(item.widget(), ChatBubble):
                        bubble = item.widget()
                        bubble.setMaximumWidth(max_bubble_width)
                        bubble.adjustSize()  # Metne göre yeniden boyutlandır
        return super().resizeEvent(event)

    def adjust_input_height(self):
        doc_height = self.input_field.document().size().height()
        new_height = min(max(40, int(doc_height + 10)), 150)
        self.input_field.setFixedHeight(new_height)

    def open_settings(self):
        self.settings_window = SettingsWindow()
        self.settings_window.exec_()

    def send_message(self):
        text = self.input_field.toPlainText().strip()
        if not text:
            return

        # Kullanıcı mesajı için container
        user_container = QWidget()
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(0, 2, 0, 2)  # Minimum margin
        
        user_bubble = ChatBubble(text, is_user=True)
        # Bubble'ın doğal boyutunu al
        user_bubble.adjustSize()
        
        # Maksimum genişlik sınırı koy ama minimum yok
        available_width = self.scroll_area.width() - 40
        user_bubble.setMaximumWidth(int(available_width * 0.8))
        
        user_layout.addStretch()  # Sol tarafta esnek boşluk
        user_layout.addWidget(user_bubble)  # Bubble'ı sağa yasla
        
        self.chat_area.addWidget(user_container)

        message_queue.put(text)
        self.input_field.clear()

        # "Asistan yazıyor..." balonu
        if hasattr(self, "typing_bubble") and self.typing_bubble:
            self.typing_bubble.setParent(None)

        # Asistan mesajı için container
        typing_container = QWidget()
        typing_layout = QHBoxLayout(typing_container)
        typing_layout.setContentsMargins(0, 2, 0, 2)  # Minimum margin
        
        self.typing_bubble = ChatBubble("Asistan yazıyor...", is_user=False)
        self.typing_bubble.adjustSize()
        
        typing_layout.addWidget(self.typing_bubble)  # Bubble'ı sola yasla
        typing_layout.addStretch()  # Sağ tarafta esnek boşluk
        
        self.chat_area.addWidget(typing_container)
        self.scroll_to_bottom()

    def listen_response(self):
        while True:
            if not response_queue.empty():
                reply = response_queue.get()
                self.message_received.emit(reply)

    @pyqtSlot(str)
    def display_assistant_reply(self, reply):
        if hasattr(self, "typing_bubble") and self.typing_bubble:
            self.typing_bubble.parent().setParent(None)  # Container'ı kaldır
            self.typing_bubble = None

        # Asistan cevabı için container
        assistant_container = QWidget()
        assistant_layout = QHBoxLayout(assistant_container)
        assistant_layout.setContentsMargins(0, 2, 0, 2)  # Minimum margin
        
        assistant_bubble = ChatBubble(reply, is_user=False)
        assistant_bubble.adjustSize()
        
        # Asistan bubble'ı için maksimum genişlik
        available_width = self.scroll_area.width() - 40
        assistant_bubble.setMaximumWidth(int(available_width * 0.8))
        
        assistant_layout.addWidget(assistant_bubble)  # Bubble'ı sola yasla
        assistant_layout.addStretch()  # Sağ tarafta esnek boşluk
        
        self.chat_area.addWidget(assistant_container)
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        vsb = self.scroll_area.verticalScrollBar()
        vsb.setValue(vsb.maximum())

    def load_old_messages(self):
        history = load_history()
        for msg in history:
            bubble = ChatBubble(msg["content"], is_user=(msg["role"] == "user"))
            
            # Her mesaj için container oluştur
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 2, 0, 2)  # Minimum margin
            
            bubble.adjustSize()  # Bubble'ı metne göre boyutlandır
            
            if msg["role"] == "user":
                # User bubble'ı maksimum genişlik sınırı
                available_width = self.scroll_area.width() - 40
                bubble.setMaximumWidth(int(available_width * 0.8))
                
                layout.addStretch()  # Sol tarafta esnek boşluk
                layout.addWidget(bubble)  # Bubble'ı sağa yasla
            else:
                # Asistan bubble'ı maksimum genişlik sınırı
                available_width = self.scroll_area.width() - 40
                bubble.setMaximumWidth(int(available_width * 0.8))
                
                layout.addWidget(bubble)  # Bubble'ı sola yasla
                layout.addStretch()  # Sağ tarafta esnek boşluk
            
            self.chat_area.addWidget(container)
        self.scroll_to_bottom()


def start_ui():
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec_())