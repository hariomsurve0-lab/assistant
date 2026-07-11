"""
jarvis/tts/manager.py — JARVIS Neural TTS Engine Manager
"""

import os
import asyncio
import tempfile
import threading
import subprocess
import zipfile
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from jarvis.logger import logger
from jarvis.config import get_config, save_config

BASE_DIR = Path(__file__).parent.parent.parent
PIPER_DIR = BASE_DIR / "piper"

# ── Optional package imports ───────────────────────────────────────────────────
def _try_import(name):
    try:
        return __import__(name)
    except ImportError:
        return None

# ── Text cleaner & Hindi Number Converter ──────────────────────────────────────
_EMOJI_STRIP = [
    "✅","❌","🎵","📝","🔍","📅","⏰","💻","🤖","🎙","🔊","🔇","🌦","📧",
    "🐙","💪","😄","😅","🤔","😊","👑","🔥","⭐","🚀","🤝","☀","☕","🌙",
    "😴","📱","🎤","●","►","◄","─","⬡","✍","▶","🎯","🏆","⚡","🌐","📊",
    "🗑","🐍","🐛","💸","😂","🎶","📋","🔗","🛠","👤","📜","📦","🔴","🟢",
    "🟡","⚠","ℹ","🎙️","🌦️","🔇","🔊","😴","Lo ","Arre ","Haan ","Waah"
]

import re

_HINDI_ONES = {
    0: 'शून्य', 1: 'एक', 2: 'दो', 3: 'तीन', 4: 'चार', 5: 'पाँच', 6: 'छह', 7: 'सात', 8: 'आठ', 9: 'नौ',
    10: 'दस', 11: 'ग्यारह', 12: 'बारह', 13: 'तेरह', 14: 'चौदह', 15: 'पंद्रह', 16: 'सोलह', 17: 'सत्रह',
    18: 'अठारह', 19: 'उन्नीस', 20: 'बीस', 21: 'इक्कीस', 22: 'बाईस', 23: 'तेईस', 24: 'चौबीस', 25: 'पच्चीस',
    26: 'छब्बीस', 27: 'सत्ताईस', 28: 'अठ्ठाईस', 29: 'उनतीस', 30: 'तीस', 31: 'इकतीस', 32: 'बत्तीस',
    33: 'तेतीस', 34: 'चौंतीस', 35: 'पैंतीस', 36: 'छत्तीस', 37: 'सैंतीस', 38: 'अड़तीस', 39: 'उनतालीस',
    40: 'चालीस', 41: 'इकतालीस', 42: 'बयालीस', 43: 'तेनतालीस', 44: 'चियालीस', 45: 'पैंतालीस', 46: 'छियालीस',
    47: 'सैंतालीस', 48: 'अड़तालीस', 49: 'उनचाas', 50: 'पचास', 51: 'इक्यावन', 52: 'बावन', 53: 'तिरेपन',
    54: 'चौवन', 55: 'बचपन', 56: 'छप्पन', 57: 'सत्तावन', 58: 'अठ्ठावन', 59: 'उनसठ', 60: 'साठ',
    61: 'इक्सठ', 62: 'बासठ', 63: 'तिरेसठ', 64: 'चौnsठ', 65: 'पैंसठ', 66: 'छियासठ', 67: 'सरसठ',
    68: 'अड़सठ', 69: 'उनहत्तर', 70: 'सत्तर', 71: 'इकहत्तर', 72: 'बहत्तर', 73: 'तिहत्तर', 74: 'चौहत्तर',
    75: 'पचहत्तर', 76: 'छिहत्तर', 77: 'सतहत्तर', 78: 'अठहत्तर', 79: 'उन्यासी', 80: 'अस्सी', 81: 'इक्यासी',
    82: 'बयासी', 83: 'तिरासी', 84: 'चौरासी', 85: 'पचासी', 86: 'छियासी', 87: 'सत्तासी', 88: 'अठ्ठासी',
    89: 'नवासी', 90: 'नब्बे', 91: 'इक्यानवे', 92: 'बयानवे', 93: 'तिरानवे', 94: 'चौरानवे', 95: 'पंचानवे',
    96: 'छियानवे', 97: 'सत्तानवे', 98: 'अठ्ठानवे', 99: 'निन्यानवे'
}

def num_to_hindi_words(n):
    if n < 0:
        return "ऋण " + num_to_hindi_words(-n)
    if n < 100:
        return _HINDI_ONES.get(n, str(n))
    if n < 1000:
        hundreds = n // 100
        rem = n % 100
        h_str = _HINDI_ONES[hundreds] + " सौ"
        if rem > 0:
            h_str += " " + num_to_hindi_words(rem)
        return h_str
    if n < 100000:
        thousands = n // 1000
        rem = n % 1000
        t_str = num_to_hindi_words(thousands) + " हज़ार"
        if rem > 0:
            t_str += " " + num_to_hindi_words(rem)
        return t_str
    if n < 10000000:
        lakhs = n // 100000
        rem = n % 100000
        l_str = num_to_hindi_words(lakhs) + " लाख"
        if rem > 0:
            l_str += " " + num_to_hindi_words(rem)
        return l_str
    return str(n)

def convert_numbers_to_hindi(text):
    def replace_match(match):
        num_str = match.group(0)
        try:
            val = int(num_str)
            return num_to_hindi_words(val)
        except ValueError:
            return num_str
    return re.sub(r'\b\d+\b', replace_match, text)

def clean_text(text: str, max_len: int = 400) -> str:
    for ch in _EMOJI_STRIP:
        text = text.replace(ch, "")
    lines = [l for l in text.split("\n") if l.strip() and not all(c in "─-= " for c in l)]
    text = " ".join(" ".join(lines).split())
    text = convert_numbers_to_hindi(text)
    return text[:max_len].strip()


# ── ElevenLabs Engine ─────────────────────────────────────────────────────────
class ElevenLabsEngine:
    NAME = "elevenlabs"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.api_key = os.environ.get("ELEVENLABS_API_KEY", "") or cfg.get("api_key", "")
        self._client = None
        self.available = False
        self._init()

    def _init(self):
        if not self.api_key:
            return
        el = _try_import("elevenlabs")
        if el is None:
            return
        try:
            from elevenlabs.client import ElevenLabs
            self._client = ElevenLabs(api_key=self.api_key)
            self.available = True
            logger.info(f"[TTS] ElevenLabs ready. Voice={self.cfg.get('voice_name','Adam')}")
        except Exception as e:
            logger.error(f"[TTS] ElevenLabs init failed: {e}")

    def speak(self, text: str, output_path: str) -> bool:
        if not self.available:
            return False
        try:
            from elevenlabs import VoiceSettings
            audio = self._client.text_to_speech.convert(
                voice_id = self.cfg.get("voice_id", "pNInz6obpgDQGcFmaJgB"),
                text = text,
                model_id = self.cfg.get("model", "eleven_multilingual_v2"),
                voice_settings = VoiceSettings(
                    stability = self.cfg.get("stability", 0.5),
                    similarity_boost = self.cfg.get("similarity_boost", 0.75),
                    style = self.cfg.get("style", 0.3),
                    use_speaker_boost = self.cfg.get("use_speaker_boost", True),
                ),
            )
            with open(output_path, "wb") as f:
                for chunk in audio:
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            logger.error(f"[TTS] ElevenLabs speak error: {e}")
            return False


# ── Piper Engine ──────────────────────────────────────────────────────────────
class PiperEngine:
    NAME = "piper"
    EXE = PIPER_DIR / "piper" / "piper.exe"
    VOICE_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.available = False
        self.model_path = None
        self._init()

    def _init(self):
        model_name = self.cfg.get("model", "hi_IN-rohan-medium")
        parts = model_name.split("-")
        if len(parts) < 3:
            return
        lang_region = parts[0]
        name = parts[1]
        quality = parts[2]
        lang = lang_region.split("_")[0]

        onnx_file = PIPER_DIR / f"{model_name}.onnx"
        json_file = PIPER_DIR / f"{model_name}.onnx.json"

        PIPER_DIR.mkdir(exist_ok=True)

        if not self.EXE.exists():
            return  # Will download on demand if needed

        self.model_path = str(onnx_file)
        if onnx_file.exists() and json_file.exists():
            self.available = True
            logger.info(f"[TTS] Piper TTS ready. Model={model_name}")

    def speak(self, text: str, output_path: str) -> bool:
        if not self.available or not self.model_path:
            return False
        try:
            wav_path = output_path.replace(".mp3", ".wav")
            result = subprocess.run(
                [
                    str(self.EXE),
                    "--model", self.model_path,
                    "--output_file", wav_path,
                    "--length_scale", str(self.cfg.get("length_scale", 0.90)),
                ],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=20,
            )
            if result.returncode == 0 and Path(wav_path).exists():
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                try:
                    Path(wav_path).unlink()
                except:
                    pass
                return True
            else:
                logger.error(f"[TTS] Piper error: {result.stderr.decode()[:200]}")
                return False
        except Exception as e:
            logger.error(f"[TTS] Piper speak error: {e}")
            return False


# ── Edge TTS Engine ───────────────────────────────────────────────────────────
class EdgeTTSEngine:
    NAME = "edge_tts"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.available = _try_import("edge_tts") is not None
        if self.available:
            logger.info(f"[TTS] Edge TTS ready. Voice={cfg.get('voice','hi-IN-MadhurNeural')}")

    def speak(self, text: str, output_path: str) -> bool:
        if not self.available:
            return False
        try:
            import edge_tts
            async def _gen():
                comm = edge_tts.Communicate(
                    text = text,
                    voice = self.cfg.get("voice", "hi-IN-MadhurNeural"),
                    rate = self.cfg.get("rate", "+18%"),
                    pitch = self.cfg.get("pitch", "+2Hz"),
                )
                await comm.save(output_path)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_gen())
            loop.close()
            return Path(output_path).exists() and Path(output_path).stat().st_size > 0
        except Exception as e:
            logger.error(f"[TTS] Edge TTS error: {e}")
            return False


# ── gTTS Engine ───────────────────────────────────────────────────────────────
class GTTSEngine:
    NAME = "gtts"

    def __init__(self, lang="hi"):
        self.lang = lang
        self.available = _try_import("gtts") is not None
        if self.available:
            logger.info("[TTS] gTTS ready.")

    def speak(self, text: str, output_path: str) -> bool:
        if not self.available:
            return False
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(output_path)
            return Path(output_path).exists()
        except Exception as e:
            logger.error(f"[TTS] gTTS error: {e}")
            return False


# ── pyttsx3 Engine ────────────────────────────────────────────────────────────
class Pyttsx3Engine:
    NAME = "pyttsx3"

    def __init__(self):
        self.available = False
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self.available = True
            logger.info("[TTS] pyttsx3 ready.")
        except Exception as e:
            logger.error(f"[TTS] pyttsx3 init failed: {e}")

    def speak_direct(self, text: str) -> bool:
        if not self.available:
            return False
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 1.0)
            voices = engine.getProperty("voices")
            for v in voices:
                if "male" in v.name.lower() or "david" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            return True
        except Exception as e:
            logger.error(f"[TTS] pyttsx3 speak error: {e}")
            return False


# ── TTS Manager ───────────────────────────────────────────────────────────────
class TTSManager:
    def __init__(self):
        self.config = get_config()
        self.lock = threading.Lock()
        self.mute = False
        self.active_name = "none"

        self.eleven = ElevenLabsEngine(self.config.get("elevenlabs", {}))
        self.piper = PiperEngine(self.config.get("piper", {}))
        self.edge = EdgeTTSEngine(self.config.get("edge_tts", {}))
        self.gtts = GTTSEngine(self.config.get("language", "hi"))
        self.pyttsx3 = Pyttsx3Engine()

        self.active_name = self._resolve_engine()
        logger.info(f"[TTS] Active engine: {self.active_name.upper()}")

    def _resolve_engine(self) -> str:
        pref = self.config.get("engine", "auto")
        if pref == "elevenlabs" and self.eleven.available:
            return "elevenlabs"
        if pref == "piper" and self.piper.available:
            return "piper"
        if pref == "edge_tts" and self.edge.available:
            return "edge_tts"
        if pref == "gtts" and self.gtts.available:
            return "gtts"
        if pref == "pyttsx3" and self.pyttsx3.available:
            return "pyttsx3"

        if self.eleven.available: return "elevenlabs"
        if self.piper.available:  return "piper"
        if self.edge.available:   return "edge_tts"
        if self.gtts.available:   return "gtts"
        if self.pyttsx3.available: return "pyttsx3"
        return "none"

    def set_engine(self, engine_name: str):
        self.config["engine"] = engine_name
        self.active_name = self._resolve_engine()
        save_config()
        logger.info(f"[TTS] Switched to: {self.active_name}")

    def set_elevenlabs_key(self, api_key: str):
        self.config["elevenlabs"]["api_key"] = api_key
        os.environ["ELEVENLABS_API_KEY"] = api_key
        self.eleven = ElevenLabsEngine(self.config["elevenlabs"])
        self.active_name = self._resolve_engine()
        save_config()

    def update_elevenlabs_settings(self, api_key: str, voice_id: str, model_id: str):
        self.config["elevenlabs"]["api_key"] = api_key
        self.config["elevenlabs"]["voice_id"] = voice_id
        self.config["elevenlabs"]["model"] = model_id
        os.environ["ELEVENLABS_API_KEY"] = api_key
        self.eleven = ElevenLabsEngine(self.config["elevenlabs"])
        self.active_name = self._resolve_engine()
        save_config()

    def fetch_elevenlabs_voices(self) -> list:
        if not self.eleven.available or not self.eleven._client:
            return []
        try:
            res = self.eleven._client.voices.get_all()
            return [(v.voice_id, v.name) for v in res.voices]
        except Exception as e:
            logger.error(f"[TTS] Error fetching voices: {e}")
            return []

    def speak(self, text: str):
        if self.mute or self.active_name == "none":
            return
        threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()

    def _speak_sync(self, text: str):
        with self.lock:
            clean = clean_text(text)
            if not clean:
                return
            self._execute_speak(clean)

    def _execute_speak(self, text: str):
        if self.active_name == "pyttsx3":
            self.pyttsx3.speak_direct(text)
            return

        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".mp3",
            dir=tempfile.gettempdir(), prefix="jarvis_tts_"
        )
        tmp.close()
        tmp_path = tmp.name

        played = False
        try:
            engine_obj = {
                "elevenlabs": self.eleven,
                "piper": self.piper,
                "edge_tts": self.edge,
                "gtts": self.gtts,
            }.get(self.active_name)

            if engine_obj and engine_obj.speak(text, tmp_path):
                if self.active_name != "piper":
                    played = self._play_audio(tmp_path)
                else:
                    played = True

            if not played:
                for fallback in [self.edge, self.gtts]:
                    if fallback.available and fallback.NAME != self.active_name:
                        if fallback.speak(text, tmp_path):
                            if self._play_audio(tmp_path):
                                break
                if not played:
                    self.pyttsx3.speak_direct(text)
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _play_audio(self, path: str) -> bool:
        try:
            from playsound import playsound
            playsound(path)
            return True
        except Exception:
            pass

        try:
            ps = (
                f"$mp = New-Object System.Windows.Media.MediaPlayer;"
                f"$mp.Open([uri]'{path}'); $mp.Play(); Start-Sleep 8; $mp.Stop()"
            )
            subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps],
                timeout=12, capture_output=True
            )
            return True
        except Exception:
            pass
        return False

    @property
    def engine_label(self) -> str:
        labels = {
            "elevenlabs": "ElevenLabs Neural",
            "piper":      "Piper TTS (Offline)",
            "edge_tts":   "Edge TTS Neural",
            "gtts":       "Google TTS",
            "pyttsx3":    "System SAPI (Offline)",
            "none":       "No TTS",
        }
        return labels.get(self.active_name, self.active_name)

    @property
    def available_engines(self) -> list:
        avail = []
        if self.eleven.available:  avail.append(("elevenlabs", "ElevenLabs Neural"))
        if self.piper.available:   avail.append(("piper",      "Piper TTS (Offline)"))
        if self.edge.available:    avail.append(("edge_tts",   "Edge TTS Neural"))
        if self.gtts.available:    avail.append(("gtts",       "Google TTS"))
        if self.pyttsx3.available: avail.append(("pyttsx3",    "System SAPI"))
        return avail

_manager = None

def get_manager() -> TTSManager:
    global _manager
    if _manager is None:
        _manager = TTSManager()
    return _manager

def speak(text: str):
    get_manager().speak(text)
