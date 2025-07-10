from chat_initializer import message_queue, response_queue

def start_ui():
    print("KVKK-A Chat Başlatıldı.")
    print("Çıkmak için 'çık' veya 'exit' yaz.\n")

    while True:
        try:
            user_input = input("Sen: ").strip()
            if user_input.lower() in ("çık", "exit"):
                print("Görüşme sonlandırıldı.")
                break

            # Kullanıcı mesajını chat kuyruğuna ekle
            message_queue.put(user_input)

            print("Asistan yazıyor...\n")

            # Asistan cevabını bekle
            while response_queue.empty():
                pass  # blokla ama bekle

            assistant_reply = response_queue.get()
            print("Asistan:", assistant_reply, "\n")

        except KeyboardInterrupt:
            print("\nSohbet sonlandırıldı.")
            break
