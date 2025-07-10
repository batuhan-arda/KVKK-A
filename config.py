SYSTEM_PROMPT = "Sen bir KVKK uyum uzmanısın. Kullanıcının verdiği metni ilgili KVKK kanun maddelerine göre değerlendir."

DIR = "data"
HISTORY_FILE = "chat_history.json"
MAX_HISTORY = 100  # toplam mesaj adedi (user + assistant)

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "theme": "Sistem Teması",
    "hide_history": False,
    "gemini_model": "gemini-2.5-flash",
    "api_key": ""
}

TEXT_MODELS = {
    "Gemini 2.5 Pro": "gemini-2.5-pro",
    "Gemini 2.5 Flash": "gemini-2.5-flash",
    "Gemini 2.5 Flash Lite Preview": "gemini-2.5-flash-lite-preview-06-17",
    "Gemini 2.0 Flash": "gemini-2.0-flash",
    "Gemini 2.0 Flash-Lite": "gemini-2.0-flash-lite",
    "Gemini 1.5 Flash": "gemini-1.5-flash",
    "Gemini 1.5 Flash-8B": "gemini-1.5-flash-8b",
    "Gemini 1.5 Pro": "gemini-1.5-pro",
}
