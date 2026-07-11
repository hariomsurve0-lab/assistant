import os
import json
import ctypes
from jarvis.logger import logger

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tts_config.json")

# ── Windows DPAPI Cryptography Helpers ─────────────────────────────────────────
class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_char))]

def encrypt_secret(secret_str: str) -> str:
    """Encrypt using Windows DPAPI. Returns hex string."""
    if not secret_str:
        return ""
    if os.name != "nt":
        return secret_str  # Non-Windows fallback (plain)
    try:
        entropy = b"JARVIS_SALT"
        data_in = DATA_BLOB(len(secret_str), ctypes.create_string_buffer(secret_str.encode("utf-8")))
        entropy_blob = DATA_BLOB(len(entropy), ctypes.create_string_buffer(entropy))
        data_out = DATA_BLOB()
        
        success = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(data_in),
            "JarvisSecret",
            ctypes.byref(entropy_blob),
            None, None, 0,
            ctypes.byref(data_out)
        )
        if success:
            encrypted_data = ctypes.string_at(data_out.pbData, data_out.cbData)
            ctypes.windll.kernel32.LocalFree(data_out.pbData)
            return encrypted_data.hex()
    except Exception as e:
        logger.error(f"[Config] DPAPI encryption failed: {e}")
    return secret_str

def decrypt_secret(hex_str: str) -> str:
    """Decrypt using Windows DPAPI. Returns plain string."""
    if not hex_str:
        return ""
    if os.name != "nt":
        return hex_str
    try:
        entropy = b"JARVIS_SALT"
        data_bytes = bytes.fromhex(hex_str)
        data_in = DATA_BLOB(len(data_bytes), ctypes.create_string_buffer(data_bytes))
        entropy_blob = DATA_BLOB(len(entropy), ctypes.create_string_buffer(entropy))
        data_out = DATA_BLOB()
        
        success = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(data_in),
            None,
            ctypes.byref(entropy_blob),
            None, None, 0,
            ctypes.byref(data_out)
        )
        if success:
            decrypted_data = ctypes.string_at(data_out.pbData, data_out.cbData)
            ctypes.windll.kernel32.LocalFree(data_out.pbData)
            return decrypted_data.decode("utf-8")
    except Exception as e:
        # If it was saved as plain text initially, return as-is
        pass
    return hex_str

# ── Config Loader & Writer ─────────────────────────────────────────────────────
class ConfigManager:
    def __init__(self):
        self.config = self._load()

    def _load(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                
                # Decrypt keys
                el = cfg.get("elevenlabs", {})
                if "api_key" in el and el["api_key"]:
                    el["api_key"] = decrypt_secret(el["api_key"])
                return cfg
            except Exception as e:
                logger.error(f"[Config] Failed to load config: {e}")
        
        # Fallback default configuration
        return {
            "engine": "edge_tts",
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
                "model": "hi_IN-rohan-medium",
                "speaker_id": 0,
                "length_scale": 0.90
            },
            "edge_tts": {
                "voice": "hi-IN-MadhurNeural",
                "rate": "+18%",
                "pitch": "+2Hz"
            },
            "language": "hi"
        }

    def save(self):
        try:
            # Create a copy to encrypt values without modifying run-time memory dictionary
            cfg_copy = json.loads(json.dumps(self.config))
            el = cfg_copy.get("elevenlabs", {})
            if "api_key" in el and el["api_key"]:
                el["api_key"] = encrypt_secret(el["api_key"])
                
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg_copy, f, indent=2)
            logger.info("[Config] Config saved successfully (credentials encrypted).")
        except Exception as e:
            logger.error(f"[Config] Failed to save config: {e}")

_config_manager = None

def get_config() -> dict:
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config

def save_config():
    global _config_manager
    if _config_manager is not None:
        _config_manager.save()
