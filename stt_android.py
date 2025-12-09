from jnius import autoclass, PythonJavaClass, java_method, cast
from queue import Queue, Empty
import time

PythonActivity = autoclass('org.kivy.android.PythonActivity')
SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
RecognizerIntent = autoclass('android.speech.RecognizerIntent')
Locale = autoclass('java.util.Locale')

class RecognitionListener(PythonJavaClass):
    __javaclass__ = 'android/speech/RecognitionListener'
    __javainterfaces__ = ['android/speech/RecognitionListener']

    def __init__(self, result_queue):
        super().__init__()
        self.result_queue = result_queue

    @java_method('()V')
    def onReadyForSpeech(self):
        pass

    @java_method('()V')
    def onBeginningOfSpeech(self):
        pass

    @java_method('(F)V')
    def onRmsChanged(self, rms):
        pass

    @java_method('([B)V')
    def onBufferReceived(self, buffer):
        pass

    @java_method('()V')
    def onEndOfSpeech(self):
        pass

    @java_method('(I)V')
    def onError(self, error):
        self.result_queue.put(None)

    @java_method('(Landroid/os/Bundle;)V')
    def onResults(self, results):
        if results:
            list_key = "results_recognition"
            strings = results.getStringArrayList(list_key)
            if strings and strings.size() > 0:
                first = strings.get(0)
                self.result_queue.put(first)

    @java_method('(Landroid/os/Bundle;)V')
    def onPartialResults(self, partial):
        if partial:
            list_key = "results_recognition"
            strings = partial.getStringArrayList(list_key)
            if strings and strings.size() > 0:
                first = strings.get(0)
                self.result_queue.put(first)

    @java_method('(ILandroid/os/Bundle;)V')
    def onEvent(self, eventType, params):
        pass


class AndroidSTT:
    def __init__(self, activity):
        self.activity = activity
        self.recognizer = SpeechRecognizer.createSpeechRecognizer(activity)
        self.queue = Queue()
        self.listener = RecognitionListener(self.queue)
        self.recognizer.setRecognitionListener(self.listener)
        self.running = False

    def start(self):
        self.running = True
        self._start_listening_cycle()

    def _start_listening_cycle(self):
        intent = autoclass('android.content.Intent')("android.speech.action.RECOGNIZE_SPEECH")
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
        # Tilni Inglizchaga sozlash
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "en-US") 
        intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, True)
        self.recognizer.startListening(intent)

    def stop(self):
        self.running = False
        try:
            self.recognizer.stopListening()
            self.recognizer.cancel()
            self.recognizer.destroy()
        except Exception:
            pass

    def take_result(self, timeout_sec=5):
        try:
            res = self.queue.get(timeout=timeout_sec)
            self._start_listening_cycle()
            return res
        except Empty:
            self._start_listening_cycle()
            return None