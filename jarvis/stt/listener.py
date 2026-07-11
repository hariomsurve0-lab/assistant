import threading
from jarvis.logger import logger

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

class STTListener:
    def __init__(self, language="hi-IN"):
        self.language = language
        self.recognizer = None
        self.microphone = None
        self.listening = False
        self._init_sr()

    def _init_sr(self):
        if not SR_AVAILABLE:
            logger.warning("[STT] speech_recognition library is not installed.")
            return
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.dynamic_energy_threshold = True
            # Setup microphone with 1.5s timeout for calibration
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            logger.info("[STT] SpeechRecognition listener initialized successfully.")
        except Exception as e:
            logger.error(f"[STT] Initialization failed: {e}")

    def listen_phrase(self) -> str:
        """Synchronous listening for a single phrase."""
        if not SR_AVAILABLE or not self.recognizer or not self.microphone:
            raise RuntimeError("Speech Recognition is not available on this device.")
        
        with self.microphone as source:
            logger.info("[STT] Listening...")
            audio = self.recognizer.listen(source, timeout=6.0, phrase_time_limit=8.0)
            
        logger.info("[STT] Recognising audio...")
        # Try primary Google Speech Recognition (works for Hindi out of the box)
        try:
            text = self.recognizer.recognize_google(audio, language=self.language)
            logger.info(f"[STT] Recognized: {text}")
            return text
        except Exception:
            # Try English fallback
            text = self.recognizer.recognize_google(audio, language="en-US")
            logger.info(f"[STT] Recognized (English fallback): {text}")
            return text

    def listen_async(self, on_success_callback, on_error_callback):
        """Asynchronous wrapper that executes the listener in a daemon thread."""
        def _thread_target():
            try:
                text = self.listen_phrase()
                if text:
                    on_success_callback(text)
                else:
                    on_error_callback("Suna toh par samajh nahi aaya.")
            except Exception as e:
                on_error_callback(e)

        threading.Thread(target=_thread_target, daemon=True).start()
