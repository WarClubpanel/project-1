from jnius import autoclass, cast, JavaException
from threading import Thread
import time
from datetime import datetime

# Loyiha modullari
from gemini_client import GeminiClient
from stt_android import AndroidSTT
from wakeword import is_wake_phrase
from file_manager import FileManager # Fayl boshqaruvi uchun qo'shildi

# ----------------------------------------------------------------------
# I. JNI VA ANDROID SINFLARI
# ----------------------------------------------------------------------

# Android sinflarini yuklash
PythonActivity = autoclass('org.kivy.android.PythonActivity')
TextToSpeech = autoclass('android.speech.tts.TextToSpeech')
Locale = autoclass('java.util.Locale')
Intent = autoclass('android.content.Intent')
PackageManager = autoclass('android.content.pm.PackageManager')

# Notification/Foreground support
Context = autoclass('android.content.Context')
NotificationManager = autoclass('android.app.NotificationManager')
NotificationChannel = autoclass('android.app.NotificationChannel')
NotificationCompatBuilder = autoclass('androidx.core.app.NotificationCompat$Builder')
NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
Build = autoclass('android.os.Build')


# ----------------------------------------------------------------------
# II. ANDROID XIZMATLARI INTERFEISLARI
# ----------------------------------------------------------------------

class AndroidTTS:
    """Android Text-to-Speech (TTS) ni boshqaradi. Til: Inglizcha (US)"""
    def __init__(self):
        self.activity = PythonActivity.mActivity
        self.tts = TextToSpeech(self.activity, None)
        try:
            self.tts.setLanguage(Locale.US)
        except Exception:
            pass 
        self.tts.setPitch(1.05)
        self.tts.setSpeechRate(1.0)

    def speak(self, text):
        if not text:
            return
        # TTS ni blokirovka qilmasdan chaqiramiz
        self.tts.speak(text, 0, None, "ari_utterance")


class ForegroundHelper:
    """Android Xizmatini fon rejimida (Foreground) ishlashini ta'minlaydi."""
    CHANNEL_ID = "ari_service_channel"
    CHANNEL_NAME = "ARI Assistant Service"

    @staticmethod
    def start_foreground(activity):
        app_context = activity.getApplicationContext()
        nm = cast(NotificationManager, app_context.getSystemService(Context.NOTIFICATION_SERVICE))

        if Build.VERSION.SDK_INT >= 26:
            channel = NotificationChannel(ForegroundHelper.CHANNEL_ID, ForegroundHelper.CHANNEL_NAME, NotificationManager.IMPORTANCE_LOW)
            nm.createNotificationChannel(channel)

        builder = NotificationCompatBuilder(app_context, ForegroundHelper.CHANNEL_ID) \
            .setContentTitle("ARI is active") \
            .setContentText("Listening for 'Ari'") \
            .setSmallIcon(activity.getApplicationInfo().icon) \
            .setPriority(NotificationCompat.PRIORITY_LOW)

        notification = builder.build()
        activity.startForeground(1, notification)


class AppLauncher:
    """Android ilovalarini ochish uchun Intentlardan foydalanadi."""
    def __init__(self, activity):
        self.activity = activity

    def launch_app(self, app_name: str) -> bool:
        pm = self.activity.getPackageManager()
        
        # Ommabop ilovalar paketlari ro'yxati
        package_map = {
            "youtube": "com.google.android.youtube",
            "chrome": "com.android.chrome",
            "settings": "com.android.settings",
            "clock": "com.google.android.deskclock", 
            "calculator": "com.google.android.calculator",
            "gmail": "com.google.android.gm",
            "maps": "com.google.android.apps.maps",
        }

        package_name = None
        for key, pkg in package_map.items():
            if key in app_name:
                package_name = pkg
                break

        if not package_name:
             return False

        try:
            intent = pm.getLaunchIntentForPackage(package_name)
            if intent:
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                self.activity.startActivity(intent)
                return True
        except (JavaException, Exception):
            return False
        
        return False


# ----------------------------------------------------------------------
# III. ASOSIY XIZMAT MANTIQI (WakeService)
# ----------------------------------------------------------------------

class WakeService:
    def __init__(self):
        self.activity = PythonActivity.mActivity
        self.tts = AndroidTTS()
        self.gemini = GeminiClient()
        self.stt = AndroidSTT(self.activity)
        self.app_launcher = AppLauncher(self.activity)
        self.file_manager = FileManager()
        self.running = False

    def get_greeting(self):
        """Vaqtga qarab salomlashish matnini qaytaradi."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_of_day = "Morning"
        elif 12 <= hour < 17:
            time_of_day = "Afternoon"
        else:
            time_of_day = "Evening"
        return f"Good {time_of_day} Sir, I am Ari, your personal assistant. How can I assist you today?"


    def start(self):
        self.running = True
        try:
            ForegroundHelper.start_foreground(self.activity)
        except Exception:
            pass
        Thread(target=self._run, daemon=True).start()

    def stop(self):
        self.running = False
        try:
            self.stt.stop()
        except Exception:
            pass
        try:
            self.activity.stopForeground(True)
        except Exception:
            pass

    def _run(self):
        """Asosiy tinglash sikli."""
        self.tts.speak("Ari service started.")
        self.stt.start()
        while self.running:
            phrase = self.stt.take_result(timeout_sec=10)
            if not phrase:
                time.sleep(0.3)
                continue

            lower = phrase.strip().lower()

            if is_wake_phrase(lower):
                # Faqat uyg'onish so'zi aytilganini tekshirish
                is_just_wake_word = any(lower == w for w in ["ari", "hey ari", "ari assistant"])

                if is_just_wake_word:
                    # Holat 1: Faqat "Ari" - To'liq salom berish
                    greeting = self.get_greeting()
                    self.tts.speak(greeting)
                    continue
                else:
                    # Holat 2: "Ari [buyruq]" - Buyruqni ajratib olish
                    command = ""
                    for w in ["ari ", "hey ari ", "ari assistant "]:
                        if lower.startswith(w):
                            command = lower[len(w):].strip()
                            break
                    
                    if command:
                        self.handle_command(command)
                    continue
    
    # ------------------------------------------------------------------
    # IV. BUYRUQ BAJARUVCHI METODLAR
    # ------------------------------------------------------------------

    def handle_command(self, command: str):
        """Buyruqni tahlil qiladi va tegishli funksiyaga yo'naltiradi."""
        if not command:
            return
        
        lower_command = command.lower()

        # 1. Fayl Boshqaruvi
        if any(keyword in lower_command for keyword in ["create file", "save note", "read file", "delete file", "list files", "edit file", "add to"]):
            self.tts.speak("Processing file management request...")
            response = self._handle_file_command(command)
            self.tts.speak(response)
            return

        # 2. Ilova ochish
        if "open" in lower_command or "launch" in lower_command:
            self.tts.speak(f"Attempting to launch application: {lower_command}")
            if self.app_launcher.launch_app(lower_command):
                self.tts.speak(f"Successfully opened {lower_command}.")
                return
            self.tts.speak(f"I couldn't find an application to launch matching {lower_command}. I will search online.")

        # 3. Umumiy AI / Gemini suhbati
        self._handle_gemini_command(command)


    def _handle_file_command(self, command: str) -> str:
        """Fayl boshqaruvi buyruqlarini ijro etadi (FileManager'dan foydalanadi)."""
        
        lower = command.lower()
        parts = lower.split()
        
        if "list files" in lower:
            return self.file_manager.list_files()
            
        elif "read file" in lower:
            try:
                filename = parts[parts.index('file') + 1]
                return self.file_manager.read_file(filename)
            except (ValueError, IndexError):
                return "Please specify which file you want to read. For example: Read file my_notes."

        elif "delete file" in lower:
            try:
                filename = parts[parts.index('file') + 1]
                return self.file_manager.delete_file(filename)
            except (ValueError, IndexError):
                return "Please specify which file you want to delete. For example: Delete file old_list."

        elif "create file" in lower or "save note" in lower:
            try:
                name_index = parts.index('file') + 1 if 'file' in parts else parts.index('note') + 1
                content_start_index = parts.index('content') + 1 if 'content' in parts else len(parts)

                filename = parts[name_index]
                content = " ".join(parts[content_start_index:])
                
                return self.file_manager.create_file(filename, content)
            except Exception:
                return "I could not understand the file name or content. Try saying: Create file [name] with content [text]."

        elif "edit file" in lower or "add to" in lower:
            try:
                name_index = parts.index('file') + 1 if 'file' in parts else parts.index('to') + 1
                content_start_index = parts.index('add') + 1 if 'add' in parts else parts.index('and') + 1

                filename = parts[name_index]
                new_content = " ".join(parts[content_start_index:])
                
                if not new_content:
                    return "What content should I add to the file?"
                    
                return self.file_manager.append_to_file(filename, new_content)
            except Exception:
                return "I could not understand the file name or content to add. Try saying: Edit file [name] and add [text]."

        return "I recognized a file command but couldn't process it. Please try again."

    
    def _handle_gemini_command(self, command: str):
        """Gemini API ga buyruqni yuboradi va javobni oqim sifatida qaytaradi."""
        try:
            def stream_cb(chunk):
                if chunk and len(chunk.strip()) > 2:
                    self.tts.speak(chunk.strip())

            self.gemini.ask(command, streaming_callback=stream_cb)
        except Exception:
            self.tts.speak("I encountered an error while connecting to the server.")