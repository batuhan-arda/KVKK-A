from chat_initializer import start_chat_loop
from ui_initializer import start_ui
import threading

if __name__ == "__main__":
    ui_thread = threading.Thread(target=start_ui)
    chat_thread = threading.Thread(target=start_chat_loop)

    ui_thread.start()
    chat_thread.start()

    ui_thread.join()
    chat_thread.join()