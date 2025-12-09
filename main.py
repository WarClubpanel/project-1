import os
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView 
from android.permissions import request_permissions, Permission

from service import WakeService, ForegroundHelper 
from wakeword import interactive_enroll_flow

STORE_PATH = "/sdcard/ARI_Store"

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=12, spacing=8, **kwargs)

        self.lbl = Label(text="A.R.I. Assistant", font_size='24sp', size_hint=(1, 0.15))
        self.add_widget(self.lbl)

        btn_layout = BoxLayout(size_hint=(1, 0.15), spacing=12)
        btn_start = Button(text="Start Service", background_color=(0.2,0.6,0.2,1))
        btn_start.bind(on_press=self.do_start)
        btn_stop = Button(text="Stop Service", background_color=(0.8,0.2,0.2,1))
        btn_stop.bind(on_press=self.do_stop)
        btn_enroll = Button(text="Enroll Wake Word", background_color=(0.2,0.4,0.8,1))
        btn_enroll.bind(on_press=self.do_enroll)
        btn_layout.add_widget(btn_start)
        btn_layout.add_widget(btn_stop)
        btn_layout.add_widget(btn_enroll)
        self.add_widget(btn_layout)

        # Loglar uchun ScrollView
        scroll_view = ScrollView(size_hint=(1, 0.7))
        self.log = Label(text="Logs will appear here", size_hint_y=None, height=self.texture_size[1], halign='left', valign='top', text_size=(self.width, None))
        scroll_view.add_widget(self.log)
        self.add_widget(scroll_view)

        self.service = None

        # Ruxsatlarni so'rash
        Clock.schedule_once(lambda dt: request_permissions([
            Permission.RECORD_AUDIO,
            Permission.INTERNET,
            Permission.FOREGROUND_SERVICE,
            Permission.SYSTEM_ALERT_WINDOW,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.ACCESS_NETWORK_STATE,
            Permission.WAKE_LOCK
        ]), 0.5)

        if not os.path.exists(STORE_PATH):
            threading.Thread(target=lambda: interactive_enroll_flow(STORE_PATH), daemon=True).start()

    def do_start(self, *args):
        self.log.text = "Starting service..."
        threading.Thread(target=self._start_thread, daemon=True).start()

    def _start_thread(self):
        try:
            self.service = WakeService()
            self.service.start()
            self.log.text = "Service started!"
        except Exception as e:
            self.log.text = f"Failed to start service: {str(e)}"

    def do_stop(self, *args):
        self.log.text = "Stopping service..."
        threading.Thread(target=self._stop_thread, daemon=True).start()

    def _stop_thread(self):
        if self.service:
            self.service.stop()
            self.log.text = "Service stopped."
            self.service = None
        else:
            self.log.text = "Service not running."

    def do_enroll(self, *args):
        self.log.text = "Enrollment started..."
        threading.Thread(target=self._enroll_thread, daemon=True).start()

    def _enroll_thread(self):
        try:
            interactive_enroll_flow(STORE_PATH)
            self.log.text = "Enrollment completed!"
        except Exception as e:
            self.log.text = f"Enrollment error: {str(e)}"


class AriApp(App):
    def build(self):
        Window.softinput_mode = "below_target"
        return MainLayout()


if __name__ == "__main__":
    AriApp().run()