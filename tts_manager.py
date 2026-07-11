"""
tts_manager.py â€” JARVIS Neural TTS Engine Manager
Supports: ElevenLabs â†’ Piper TTS â†’ Edge TTS â†’ gTTS â†’ pyttsx3
"""

import os
import json
import asyncio
import tempfile
import threading
import subprocess
import platform
import urllib.request
import urllib.error
import zipfile
import shutil
from pathlib import Path

# â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
BASE_DIR    = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "tts_config.json"
PIPER_DIR   = BASE_DIR / "piper"

DEFAULT_CONFIG = {
    "engine": "auto",
    "elevenlabs": {
        "api_key": "",
        "voice_id": "pNInz6obpgDQGcFmaJgB",
        "voice_name": "Adam (Warm Male)",
        "model": "eleven_multilingual_v2",
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.3,
        "use_speaker_boost": True
    },
    "piper": {
        "model": "hi_IN-hindi_tdil-medium",
        "speaker_id": 0,
        "length_scale": 0.95
    },
    "edge_tts": {
        "voice": "hi-IN-MadhurNeural",
        "rate": "+18%",
        "pitch": "+2Hz"
    },
    "language": "hi"
}

# â”€â”€ Optional package imports â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _try_import(name):
    try:
        return __import__(name)
    except ImportError:
        return None

# â”€â”€ Text cleaner â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_EMOJI_STRIP = [
    "âœ…","âŒ","ðŸŽµ","ðŸ“","ðŸ”","ðŸ“…","â°","ðŸ’»","ðŸ¤–","ðŸŽ™","ðŸ”Š","ðŸ”‡","ðŸŒ¦","ðŸ“§",
    "ðŸ™","ðŸ’ª","ðŸ˜„","ðŸ˜…","ðŸ¤”","ðŸ˜Š","ðŸ‘‘","ðŸ”¥","â­","ðŸš€","ðŸ¤","â˜€","â˜•","ðŸŒ™",
    "ðŸ˜´","ðŸ“±","ðŸŽ¤","â—","â–º","â—„","â”€","â¬¡","âœ","â–¶","ðŸŽ¯","ðŸ†","âš¡","ðŸŒ","ðŸ“Š",
    "ðŸ—‘","ðŸ","ðŸ›","ðŸ’¸","ðŸ˜‚","ðŸŽ¶","ðŸ“‹","ðŸ”—","ðŸ› ","ðŸ‘¤","ðŸ“œ","ðŸ“¦","ðŸ”´","ðŸŸ¢",
    "ðŸŸ¡","âš ","â„¹","ðŸŽ™ï¸","ðŸŒ¦ï¸","ðŸ”‡","ðŸ”Š","ðŸ˜´","Lo ","Arre ","Haan ","Waah"
]

def clean_text(text: str, max_len: int = 400) -> str:
    for ch in _EMOJI_STRIP:
        text = text.replace(ch, "")
    lines = [l for l in text.split("\n") if l.strip() and not all(c in "â”€-= " for c in l)]
    text = " ".join(" ".join(lines).split())
    return text[:max_len].strip()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  TTS ENGINES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class ElevenLabsEngine:
    """ElevenLabs cloud TTS â€” best quality, requires API key."""

    NAME = "elevenlabs"

    def __init__(self, cfg: dict):
        self.cfg      = cfg
        self.api_key  = (
            os.environ.get("ELEVENLABS_API_KEY", "")
            or cfg.get("api_key", "")
        )
        self._client  = None
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
            print(f"[TTS] ElevenLabs ready âœ“  voice={self.cfg.get('voice_name','Adam')}")
        except Exception as e:
            print(f"[TTS] ElevenLabs init failed: {e}")

    def speak(self, text: str, output_path: str) -> bool:
        if not self.available:
            return False
        try:
            from elevenlabs import VoiceSettings
            audio = self._client.text_to_speech.convert(
                voice_id          = self.cfg.get("voice_id", "pNInz6obpgDQGcFmaJgB"),
                text              = text,
                model_id          = self.cfg.get("model", "eleven_multilingual_v2"),
                voice_settings    = VoiceSettings(
                    stability         = self.cfg.get("stability", 0.5),
                    similarity_boost  = self.cfg.get("similarity_boost", 0.75),
                    style             = self.cfg.get("style", 0.3),
                    use_speaker_boost = self.cfg.get("use_speaker_boost", True),
                ),
            )
            with open(output_path, "wb") as f:
                for chunk in audio:
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            print(f"[TTS] ElevenLabs speak error: {e}")
            return False


class PiperEngine:
    """Piper TTS â€” offline, high-quality neural voice."""

    NAME    = "piper"
    EXE     = PIPER_DIR / "piper" / "piper.exe"  # extracted here by zip
    MODEL   = None   # set after download

    PIPER_RELEASE = "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
    VOICE_BASE    = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

    def __init__(self, cfg: dict):
        self.cfg       = cfg
        self.available = False
        self.model_path = None
        self._init()

    def _init(self):
        model_name = self.cfg.get("model", "hi_IN-rohan-medium")
        # voice path on HF: lang/lang_REGION/name/quality/
        # e.g. hi_IN-rohan-medium â†’ hi/hi_IN/rohan/medium/
        parts = model_name.split("-")  # ['hi_IN', 'rohan', 'medium']
        lang_region = parts[0]         # hi_IN
        name        = parts[1]         # rohan
        quality     = parts[2]         # medium
        lang        = lang_region.split("_")[0]  # hi

        onnx_file  = PIPER_DIR / f"{model_name}.onnx"
        json_file  = PIPER_DIR / f"{model_name}.onnx.json"

        PIPER_DIR.mkdir(exist_ok=True)

        # Download piper exe if missing (it extracts to piper/piper/piper.exe)
        if not self.EXE.exists():
            print("[TTS] Piper binary not found â€” downloading...")
            if not self._download_piper():
                return

        # Download voice model if missing
        if not onnx_file.exists() or not json_file.exists():
            print(f"[TTS] Piper voice '{model_name}' not found â€” downloading...")
            if not self._download_voice(model_name, lang, lang_region, name, quality, onnx_file, json_file):
                return

        self.model_path = str(onnx_file)
        self.available  = True
        print(f"[TTS] Piper TTS ready âœ“  model={model_name}")

    def _download_piper(self) -> bool:
        try:
            zip_path = PIPER_DIR / "piper.zip"
            print(f"[TTS] Downloading Piper from {self.PIPER_RELEASE}")
            urllib.request.urlretrieve(self.PIPER_RELEASE, zip_path)
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(PIPER_DIR)
            zip_path.unlink()
            # Move piper.exe to top-level piper dir if in subdir
            for p in PIPER_DIR.rglob("piper.exe"):
                if p != self.EXE:
                    shutil.move(str(p), str(self.EXE))
                    break
            return self.EXE.exists()
        except Exception as e:
            print(f"[TTS] Piper download failed: {e}")
            return False

    def _download_voice(self, model_name, lang, lang_region, name, quality, onnx_file, json_file) -> bool:
        """Download from HuggingFace: lang/lang_REGION/name/quality/model.onnx"""
        try:
            base = f"{self.VOICE_BASE}/{lang}/{lang_region}/{name}/{quality}"
            for url, dest in [
                (f"{base}/{model_name}.onnx",      onnx_file),
                (f"{base}/{model_name}.onnx.json", json_file),
            ]:
                print(f"[TTS] Downloading {dest.name} from {url}")
                urllib.request.urlretrieve(url, dest)
            return onnx_file.exists() and json_file.exists()
        except Exception as e:
            print(f"[TTS] Voice download failed: {e}")
            return False

    def speak(self, text: str, output_path: str) -> bool:
        if not self.available or not self.model_path:
            return False
        try:
            # Piper reads from stdin and writes WAV to stdout
            wav_path = output_path.replace(".mp3", ".wav")
            result = subprocess.run(
                [
                    str(self.EXE),
                    "--model",       self.model_path,
                    "--output_file", wav_path,
                    "--length_scale", str(self.cfg.get("length_scale", 0.95)),
                ],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=20,
            )
            if result.returncode == 0 and Path(wav_path).exists():
                # Play WAV
                import winsound
                winsound.PlaySound(wav_path, winsound.SND_FILENAME)
                try:
                    Path(wav_path).unlink()
                except:
                    pass
                return True
            else:
                print(f"[TTS] Piper error: {result.stderr.decode()[:200]}")
                return False
        except Exception as e:
            print(f"[TTS] Piper speak error: {e}")
            return False


class EdgeTTSEngine:
    """Microsoft Edge TTS â€” good quality, requires internet."""

    NAME = "edge_tts"

    def __init__(self, cfg: dict):
        self.cfg       = cfg
        self.available = _try_import("edge_tts") is not None
        if self.available:
            print(f"[TTS] Edge TTS ready âœ“  voice={cfg.get('voice','hi-IN-MadhurNeural')}")

    def speak(self, text: str, output_path: str) -> bool:
        if not self.available:
            return False
        try:
            import edge_tts
            async def _gen():
                comm = edge_tts.Communicate(
                    text  = text,
                    voice = self.cfg.get("voice",  "hi-IN-MadhurNeural"),
                    rate  = self.cfg.get("rate",   "+18%"),
                    pitch = self.cfg.get("pitch",  "+2Hz"),
                )
                await comm.save(output_path)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_gen())
            loop.close()
            return Path(output_path).exists() and Path(output_path).stat().st_size > 0
        except Exception as e:
            print(f"[TTS] Edge TTS error: {e}")
            return False


class GTTSEngine:
    """Google TTS â€” decent quality, requires internet."""

    NAME = "gtts"

    def __init__(self, lang="hi"):
        self.lang      = lang
        self.available = _try_import("gtts") is not None
        if self.available:
            print("[TTS] gTTS ready âœ“")

    def speak(self, text: str, output_path: str) -> bool:
        if not self.available:
            return False
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(output_path)
            return Path(output_path).exists()
        except Exception as e:
            print(f"[TTS] gTTS error: {e}")
            return False


class Pyttsx3Engine:
    """Offline Windows SAPI TTS â€” no internet, lower quality."""

    NAME = "pyttsx3"

    def __init__(self):
        self.available = False
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 165)
            self._engine.setProperty("volume", 1.0)
            # Try to select male voice
            for v in self._engine.getProperty("voices"):
                if any(x in v.name.lower() for x in ["david", "male", "mark"]):
                    self._engine.setProperty("voice", v.id)
                    break
            self.available = True
            print("[TTS] pyttsx3 ready âœ“ (offline fallback)")
        except Exception as e:
            print(f"[TTS] pyttsx3 init failed: {e}")

    def speak_direct(self, text: str) -> bool:
        if not self.available:
            return False
        try:
            engine = __import__("pyttsx3").init()
            engine.setProperty("rate", 165)
            engine.setProperty("volume", 1.0)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            return True
        except Exception as e:
            print(f"[TTS] pyttsx3 speak error: {e}")
            return False


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
#  MAIN TTS MANAGER
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TTSManager:
    """
    Manages all TTS engines with auto-detection and fallback chain.
    Thread-safe: one speech at a time via lock.
    """

    def __init__(self, config_path: str = None):
        self.config      = self._load_config(config_path or str(CONFIG_FILE))
        self.lock        = threading.Lock()
        self.mute        = False
        self.active_name = "none"

        # Initialise engines
        self.eleven  = ElevenLabsEngine(self.config.get("elevenlabs", {}))
        self.piper   = PiperEngine(self.config.get("piper", {}))
        self.edge    = EdgeTTSEngine(self.config.get("edge_tts", {}))
        self.gtts    = GTTSEngine(self.config.get("language", "hi"))
        self.pyttsx3 = Pyttsx3Engine()

        self.active_name = self._resolve_engine()
        print(f"[TTS] Active engine: {self.active_name.upper()}")

    # â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def _load_config(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            # Merge with defaults for any missing keys
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
        except Exception:
            return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(str(CONFIG_FILE), "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[TTS] Config save error: {e}")

    # â”€â”€ Engine resolution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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

        # Auto-detect best available
        if self.eleven.available:  return "elevenlabs"
        if self.piper.available:   return "piper"
        if self.edge.available:    return "edge_tts"
        if self.gtts.available:    return "gtts"
        if self.pyttsx3.available: return "pyttsx3"
        return "none"

    def set_engine(self, engine_name: str):
        """Switch engine at runtime."""
        self.config["engine"] = engine_name
        self.active_name = self._resolve_engine()
        self.save_config()
        print(f"[TTS] Switched to: {self.active_name}")

    def set_elevenlabs_key(self, api_key: str):
        """Update ElevenLabs API key and reinitialise engine."""
        self.config["elevenlabs"]["api_key"] = api_key
        os.environ["ELEVENLABS_API_KEY"] = api_key
        self.eleven = ElevenLabsEngine(self.config["elevenlabs"])
        self.active_name = self._resolve_engine()
        self.save_config()

    # â”€â”€ Core speak â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    def speak(self, text: str):
        """Speak text asynchronously (non-blocking)."""
        if self.mute or self.active_name == "none":
            return
        threading.Thread(target=self._speak_sync, args=(text,), daemon=True).start()

    def _speak_sync(self, text: str):
        """Internal blocking speak â€” runs in thread."""
        with self.lock:
            clean = clean_text(text)
            if not clean:
                return
            self._execute_speak(clean)

    def _execute_speak(self, text: str):
        """Try engines in priority order."""
        # pyttsx3 doesn't need a temp file
        if self.active_name == "pyttsx3":
            self.pyttsx3.speak_direct(text)
            return

        # All other engines write to a temp MP3 file, then play it
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
                "piper":      self.piper,
                "edge_tts":   self.edge,
                "gtts":       self.gtts,
            }.get(self.active_name)

            if engine_obj and engine_obj.speak(text, tmp_path):
                # piper plays internally via winsound (WAV), others need playsound/mpv
                if self.active_name != "piper":
                    played = self._play_audio(tmp_path)
                else:
                    played = True  # piper already played

            # Fallback chain if primary engine failed
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
                import os as _os
                _os.unlink(tmp_path)
            except:
                pass

    def _play_audio(self, path: str) -> bool:
        """Play an audio file (MP3/WAV) using best available method."""
        # Method 1: playsound
        try:
            from playsound import playsound
            playsound(path)
            return True
        except Exception:
            pass

        # Method 2: Windows Media Player via PowerShell
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

    # â”€â”€ Status â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ Singleton convenience â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_manager: TTSManager | None = None

def get_manager() -> TTSManager:
    global _manager
    if _manager is None:
        _manager = TTSManager()
    return _manager

def speak(text: str):
    """Global speak function â€” drop-in replacement."""
    get_manager().speak(text)
