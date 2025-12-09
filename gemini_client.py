import requests
import json

class GeminiClient:
    def __init__(self):
        # !!! Bu yerga o'zingizning haqiqiy Gemini API kalitingizni kiriting !!!
        self.api_key = "AIzaSyAiXG7haf4ykQ8Ut91V2lVPl5OTRXFWjDs" 
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def ask(self, prompt, streaming_callback=None):
        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }
        params = {"key": self.api_key}
        headers = {"Content-Type": "application/json"}

        # Non-stream
        if not streaming_callback:
            try:
                r = requests.post(self.base_url, params=params, headers=headers, data=json.dumps(payload), timeout=30)
                r.raise_for_status()
                data = r.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                text = "Failed to receive a proper response from the AI." # English error message
            return text

        # Simple chunking stream: split sentences
        try:
            r = requests.post(self.base_url, params=params, headers=headers, data=json.dumps(payload), timeout=30)
            r.raise_for_status()
            data = r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            text = "I am having trouble connecting to the AI."
        
        # Olingan matnni gaplar bo'yicha bo'lib, ovoz chiqarish uchun uzatadi
        for chunk in text.split(". "):
            c = chunk.strip()
            if c:
                if not text.endswith(chunk):
                    c += "."
                streaming_callback(c)