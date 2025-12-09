import os
import time
# service.py faylidan AndroidTTS ni import qilish kerak
try:
    from service import AndroidTTS
except ImportError:
    class AndroidTTS:
        def speak(self, text):
            print(f"TTS: {text}")

WAKE_PHRASES = ["ari", "hey ari", "ari assistant"]

def interactive_enroll_flow(store_path):
    if not os.path.exists(store_path):
        os.makedirs(store_path)
    tts = AndroidTTS()
    # Inglizcha matnlar
    tts.speak("Wake word voice model is not set up. Let's practice the phrase 'Ari'.")
    for i in range(3):
        tts.speak(f"Sample {i+1}, please say 'Ari'.")
        time.sleep(2)
    tts.speak("Enrollment complete.")

def is_wake_phrase(text: str) -> bool:
    if not text:
        return False
    t = text.strip().lower()
    return any(t == w or t.startswith(w + " ") for w in WAKE_PHRASES)