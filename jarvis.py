"""
JARVIS - Gopal ka AI Dost
Hindi Voice Assistant with friendly personality
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import datetime
import os
import subprocess
import webbrowser
import platform
import json
import urllib.request
import urllib.parse
import tempfile
import random
import sys

# ── OPTIONAL IMPORTS ──────────────────────────────────────────────────────────
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except Exception:
    PYTTSX3_AVAILABLE = False

try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except Exception:
    PLAYSOUND_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
#  THEME
# ─────────────────────────────────────────────────────────────────────────────
BG       = "#0a0e1a"
BG2      = "#111827"
BG3      = "#1e293b"
ACCENT   = "#00d4ff"
ACCENT2  = "#7c3aed"
TEXT     = "#e2e8f0"
TEXT_DIM = "#64748b"
GREEN    = "#10b981"
RED      = "#ef4444"
YELLOW   = "#f59e0b"
ORANGE   = "#f97316"
FONT     = ("Segoe UI", 11)
FONT_B   = ("Segoe UI", 11, "bold")
FONT_T   = ("Segoe UI", 13, "bold")
FONT_S   = ("Segoe UI", 9)

# ─────────────────────────────────────────────────────────────────────────────
#  NOTES
# ─────────────────────────────────────────────────────────────────────────────
NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_notes.json")

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────────────────────────────────────────
#  TEXT-TO-SPEECH (Hindi) — 3 fallback methods
# ─────────────────────────────────────────────────────────────────────────────
_speak_lock = threading.Lock()

def _clean_text(text):
    """Remove emojis and normalize text for TTS."""
    for ch in ["✅","❌","🎵","📝","🔍","📅","⏰","💻","🤖","🎙",
               "🔊","🔇","🌦","📧","🐙","💪","😄","😅","🤔","😊",
               "👑","🔥","⭐","🚀","🤝","☀","☕","🌙","😴","📱","🎤",
               "●","►","◄","─","⬡","✍","▶"]:
        text = text.replace(ch, "")
    return " ".join(text.split())[:400]

def speak(text, lang="hi"):
    """
    Speak text in Hindi:
    1. gTTS (Google TTS) + playsound  ← best quality Hindi
    2. pyttsx3 offline fallback
    """
    def _do_speak():
        with _speak_lock:
            clean = _clean_text(text)
            if not clean.strip():
                return

            # Method 1: gTTS + playsound (best Hindi quality)
            if GTTS_AVAILABLE and PLAYSOUND_AVAILABLE:
                tmp_path = None
                try:
                    tts = gTTS(text=clean, lang=lang, slow=False)
                    tmp = tempfile.NamedTemporaryFile(
                        delete=False, suffix=".mp3",
                        dir=tempfile.gettempdir(), prefix="jarvis_"
                    )
                    tmp.close()
                    tmp_path = tmp.name
                    tts.save(tmp_path)
                    playsound(tmp_path)
                    return
                except Exception as e:
                    print(f"[TTS] gTTS+playsound error: {e}")
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                        except:
                            pass

            # Method 2: pyttsx3 (offline, no internet needed)
            if PYTTSX3_AVAILABLE:
                try:
                    engine = pyttsx3.init()
                    engine.setProperty('rate', 160)
                    engine.setProperty('volume', 1.0)
                    engine.say(clean)
                    engine.runAndWait()
                    engine.stop()
                    return
                except Exception as e:
                    print(f"[TTS] pyttsx3 error: {e}")

    threading.Thread(target=_do_speak, daemon=True).start()

# ─────────────────────────────────────────────────────────────────────────────
#  HINDI RESPONSES BANK
# ─────────────────────────────────────────────────────────────────────────────
GREETINGS = [
    "Arre wah Gopal bhai! Aa gaye aap! Kya haal hai? Main bilkul ready hoon seva ke liye!",
    "Haan haan Gopal bhai, bolo bolo! Kya kaam hai aaj?",
    "Namaste Gopal bhai! Main Jarvis hoon, hamesha aapki seva mein taiyaar!",
    "Oh ho! Gopal bhai khud aa gaye! Batao kya chahiye?",
    "Ji Gopal bhai! Ek dum mast hoon main. Aap sunao, kya seva karein?",
]

JOKES = [
    "Ek programmer apni girlfriend ko bola - Main tumse pyaar karta hoon. Girlfriend ne kaha - Prove karo. Programmer ne kaha - bool love = True! Lekin girlfriend ne kaha - Yeh toh compiled nahi hoga! Ha ha ha!",
    "Teacher ne pucha - Computer kya hai? Gopal bhai ne kaha - Sir, woh machine hai jo tab kaam karta hai jab hum kaam nahi karna chahte! Ha ha!",
    "Ek coder raat bhar jaagta raha. Subah biwi ne pucha - Kya hua? Coder bola - Ek missing semicolon dhundh raha tha. Biwi boli - Toh mila? Coder - Haan, line 1 mein tha! Itni raat barbaad!",
    "Python developer ne doctor se kaha - Doctor saab mera bug theek karo. Doctor ne kaha - Main insaan theek karta hoon, code nahi! Aur developer bola - Kya fark hai?",
]

MOTIVATION = [
    "Gopal bhai, yaad rakho - Koshish karne walon ki kabhi haar nahi hoti! Aap kar sakte ho!",
    "Arre yaar, chhote chhote kadam bade sapne tak pahunchate hain. Chalte raho bhai!",
    "Gopal bhai, code likhna band mat karo. Ek din duniya dekhegi aapka kaam!",
    "Mushkilein aati hain toh samjho ki aap sahi raaste par ho! Keep going bhai!",
    "Bhai, success woh hai jo aap define karo. Apni terms par jiyo!",
]

THANKS_RESP = [
    "Arre Gopal bhai, thanks mat boliye! Main toh aapka hi hoon!",
    "Koi baat nahi bhai! Yeh toh mera kaam hai. Aur kuch kaam ho toh batao!",
    "Ji ji, aapki seva mein bahut khushi milti hai mujhe!",
]

HOWRU_RESP = [
    "Main bilkul mast hoon Gopal bhai! Ekdum fit aur ready! Aap sunao?",
    "Arre main toh ek dum zabardast hoon bhai! Aap kaise ho?",
    "Mast hoon yaar! Aapka wait kar raha tha! Batao kya kaam hai?",
]

# ─────────────────────────────────────────────────────────────────────────────
#  COMMAND PROCESSOR
# ─────────────────────────────────────────────────────────────────────────────
def process_command(cmd):
    cmd = cmd.strip()
    low = cmd.lower()

    # ── GREETINGS ────────────────────────────────────────────────────────────
    if any(x in low for x in ["hello","hi","hey","hii","namaste","namaskar",
                                "good morning","good evening","good night",
                                "subah","raat","salam","kya haal"]):
        hour = datetime.datetime.now().hour
        if any(x in low for x in ["good night","raat","sone"]):
            return "Good night Gopal bhai! Kal phir milenge. Bahut accha kaam kiya aaj aapne! Achhe sapne aayein!"
        if any(x in low for x in ["good morning","subah"]):
            return "Subah bakhair Gopal bhai! Chai pi li? Toh chalte hain kaam pe! Aaj ka din bahut accha jayega!"
        return random.choice(GREETINGS)

    # ── HOW ARE YOU ───────────────────────────────────────────────────────────
    if any(x in low for x in ["how are you","kaisa hai","kya haal","theek ho","kaisa chal"]):
        return random.choice(HOWRU_RESP)

    # ── THANKS ────────────────────────────────────────────────────────────────
    if any(x in low for x in ["thanks","thank you","shukriya","dhanyawad","bahut accha","wah"]):
        return random.choice(THANKS_RESP)

    # ── TIME ─────────────────────────────────────────────────────────────────
    if any(x in low for x in ["time","kitne baje","samay","ghadi","kya time","time batao"]):
        now = datetime.datetime.now()
        return (f"Gopal bhai, abhi {now.strftime('%I:%M %p')} baje hain!\n"
                f"Aur aaj {now.strftime('%A, %d %B %Y')} hai.\n\n"
                f"{'Subah ka time hai, chai piyo!' if now.hour < 12 else 'Shaam ho gayi bhai!' if now.hour > 17 else 'Din mein kaam karo bhai!'}")

    # ── DATE ─────────────────────────────────────────────────────────────────
    if any(x in low for x in ["date","aaj","today","din","tarikh","mahina","kaunsa din"]):
        now = datetime.datetime.now()
        return f"Aaj {now.strftime('%A, %d %B %Y')} hai Gopal bhai!\nMahina hai {now.strftime('%B')} aur saal {now.year}."

    # ── WEATHER ──────────────────────────────────────────────────────────────
    if any(x in low for x in ["weather","mausam","barish","temperature","garmi","sardi","baarish"]):
        city = "Pune"
        stop = {"weather","mausam","barish","temperature","garmi","sardi","baarish",
                "in","at","for","the","what","is","today","ka","mein","ki","batao","hai"}
        for w in low.split():
            if w not in stop and len(w) > 2:
                city = w.capitalize(); break
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
            with urllib.request.urlopen(url, timeout=5) as r:
                result = r.read().decode()
            return (f"Gopal bhai, {city} ka mausam dekho:\n\n"
                    f"  {result}\n\n"
                    f"Baarish ho toh chhaata le jaana! Apna khayal rakhna!")
        except:
            return f"Arey yaar! {city} ka mausam nahi mila. Internet check karo bhai!"

    # ── OPEN APPS ────────────────────────────────────────────────────────────
    app_map = {
        "chrome":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "google":       r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "notepad":      "notepad.exe",
        "calculator":   "calc.exe",
        "paint":        "mspaint.exe",
        "explorer":     "explorer.exe",
        "files":        "explorer.exe",
        "task manager": "taskmgr.exe",
        "cmd":          "cmd.exe",
        "powershell":   "powershell.exe",
        "vs code":      "code",
        "vscode":       "code",
    }
    for app, path in app_map.items():
        if app in low and any(x in low for x in ["open","launch","start","kholo","chalu"]):
            try:
                subprocess.Popen(path, shell=True)
                return f"Haan Gopal bhai! {app.capitalize()} khol diya aapke liye! Lo use karo!"
            except:
                return f"Yaar, {app} nahi khul raha. Installed hai na?"

    # ── YOUTUBE ──────────────────────────────────────────────────────────────
    if any(x in low for x in ["youtube","gana","music","song","bajao","play"]):
        query = low
        for w in ["play","open","youtube","gana","music","song","bajao","on","bhai","mujhe","please"]:
            query = query.replace(w,"").strip()
        if query:
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
            return f"Gopal bhai ke liye '{query}' YouTube pe search kar diya! Enjoy karo!"
        else:
            webbrowser.open("https://www.youtube.com")
            return "YouTube khol diya Gopal bhai! Kaunsa gana sunna hai?"

    # ── WEB SEARCH ───────────────────────────────────────────────────────────
    if any(x in low for x in ["search","google","dhundho","find","look up","batao","dhundh"]):
        query = low
        for w in ["search for","search","google","dhundho","find","look up","batao","bhai","please","dhundh"]:
            query = query.replace(w,"").strip()
        if query:
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            return f"Haan bhai! '{query}' Google pe dhundh diya! Dekho kya mila!"
        else:
            webbrowser.open("https://www.google.com")
            return "Google khol diya! Ab dhundho jo bhi chahiye!"

    # ── GMAIL ────────────────────────────────────────────────────────────────
    if any(x in low for x in ["gmail","mail","email","inbox"]):
        webbrowser.open("https://mail.google.com")
        return "Gopal bhai ka Gmail khol diya! Koi important message toh nahi aaya na?"

    # ── GITHUB ───────────────────────────────────────────────────────────────
    if "github" in low:
        webbrowser.open("https://github.com/hariomsurve0-lab")
        return "Gopal bhai ka GitHub profile khol diya! Waah, kitna accha kaam hai aapka!"

    # ── SYSTEM INFO ──────────────────────────────────────────────────────────
    if any(x in low for x in ["system","cpu","ram","memory","battery","computer"]):
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=1)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            bat  = psutil.sensors_battery()
            bat_s = f"{bat.percent:.0f}% ({'Charging' if bat.power_plugged else 'Battery pe'}) " if bat else "N/A"
            status = "Sab theek hai bhai! Computer mast chal raha hai!" if cpu < 80 and ram.percent < 80 \
                     else "Bhai thoda load zyada hai! Kuch apps band karo!"
            return (f"Gopal bhai, aapke computer ZORO ki report:\n\n"
                    f"  OS       : {platform.system()} {platform.release()}\n"
                    f"  CPU      : {cpu}% chal raha hai\n"
                    f"  RAM      : {ram.percent}% use ({ram.used//1024//1024} MB / {ram.total//1024//1024} MB)\n"
                    f"  Disk C:  : {disk.percent}% bhara ({disk.used//1024//1024//1024} GB / {disk.total//1024//1024//1024} GB)\n"
                    f"  Battery  : {bat_s}\n\n"
                    f"  {status}")
        except ImportError:
            return (f"Gopal bhai, basic info:\n\n"
                    f"  OS      : {platform.system()} {platform.release()}\n"
                    f"  Machine : {platform.node()}\n"
                    f"  Python  : {platform.python_version()}\n"
                    f"  User    : {os.environ.get('USERNAME','Gopal')}\n\n"
                    f"Full stats ke liye 'pip install psutil' run karo bhai!")

    # ── NOTES ADD ────────────────────────────────────────────────────────────
    if any(low.startswith(x) for x in ["note:","add note","remember","yaad rakhna","note kar","save note","note rakhna"]):
        note_text = cmd
        for p in ["note:","add note","remember","yaad rakhna","note kar","save note","note rakhna"]:
            note_text = note_text.lower().replace(p,"").strip()
        note_text = cmd[cmd.lower().index(note_text):] if note_text and note_text in cmd.lower() else note_text
        notes = load_notes()
        notes.append({"text": note_text or cmd, "time": datetime.datetime.now().strftime("%d %b %Y %I:%M %p")})
        save_notes(notes)
        return f"Note likh liya Gopal bhai!\n\n  \"{note_text or cmd}\"\n\nYaad rahega, chinta mat karo!"

    # ── NOTES SHOW ───────────────────────────────────────────────────────────
    if any(x in low for x in ["show notes","my notes","notes dikhao","meri notes","notes batao"]):
        notes = load_notes()
        if not notes:
            return "Bhai, koi note nahi hai abhi! Kuch yaad dilana ho toh 'note: kuch bhi' bolke save karo!"
        result = f"Gopal bhai ke {len(notes)} notes hain:\n"
        for i, n in enumerate(notes, 1):
            result += f"\n  {i}. [{n['time']}]\n     {n['text']}"
        return result + "\n\n'Notes hatao' bolne par delete ho jayenge!"

    # ── NOTES CLEAR ──────────────────────────────────────────────────────────
    if any(x in low for x in ["clear notes","delete notes","notes hatao","notes delete"]):
        save_notes([])
        return "Sab notes delete kar diye Gopal bhai! Fresh start! Naye notes likho ab!"

    # ── JOKE ─────────────────────────────────────────────────────────────────
    if any(x in low for x in ["joke","funny","hasao","mazak","chutkula","haso","hanso"]):
        return random.choice(JOKES)

    # ── MOTIVATION ───────────────────────────────────────────────────────────
    if any(x in low for x in ["motivate","motivation","inspire","quote","himmat","hosla","inspire"]):
        return random.choice(MOTIVATION)

    # ── WHO ARE YOU ──────────────────────────────────────────────────────────
    if any(x in low for x in ["who are you","tum kaun","aap kaun","jarvis kaun","introduce","parichay"]):
        return ("Main hoon Jarvis - Gopal bhai ka personal AI dost!\n\n"
                "Iron Man wale Jarvis ki tarah hoon, bas aapke laptop pe!\n"
                "Main Hindi mein bolun ga, samjhunga bhi, aur dost ki tarah baat karunga!\n\n"
                "Apps kholna, search karna, mausam batana, notes likhna -\n"
                "sab kuch kar sakta hoon main aapke liye!\n\n"
                "Dost ki tarah baat karo mujhse, main hamesha ready hoon!")

    # ── HELP ─────────────────────────────────────────────────────────────────
    if any(x in low for x in ["help","kya kar sakte","features","commands","kya karta"]):
        return ("Gopal bhai, yeh sab kar sakta hoon main:\n\n"
                "  Time/Date  : 'kitne baje hain', 'aaj kya date hai'\n"
                "  Mausam     : 'Bangalore ka mausam batao'\n"
                "  Apps       : 'chrome kholo', 'notepad kholo'\n"
                "  Search     : 'Python tutorials dhundho'\n"
                "  Music      : 'lofi music YouTube pe bajao'\n"
                "  Gmail      : 'gmail kholo'\n"
                "  System     : 'system info batao'\n"
                "  Notes      : 'note: grocery lena hai', 'notes dikhao'\n"
                "  Joke       : 'ek joke sunao'\n"
                "  Motivate   : 'mujhe motivate karo'\n"
                "  Voice      : Mic button dabao aur bolte jao!\n\n"
                "Dost ki tarah baat karo, main samjhunga!")

    # ── DEFAULT ──────────────────────────────────────────────────────────────
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(cmd)}")
    return (f"Hmm, '{cmd}' exactly samajh nahi aaya bhai!\n"
            f"Lekin Google pe dhundh diya aapke liye!\n\n"
            f"'Help' bologe toh sab commands bata dunga!")

# ─────────────────────────────────────────────────────────────────────────────
#  JARVIS GUI
# ─────────────────────────────────────────────────────────────────────────────
class JarvisApp:
    def __init__(self, root):
        self.root      = root
        self.listening = False
        self.mute      = False
        self.root.title("JARVIS — Gopal ka AI Dost")
        self.root.geometry("880x700")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(660, 540)
        self._build_ui()
        self._welcome()

    def _build_ui(self):
        # HEADER
        hdr = tk.Frame(self.root, bg=ACCENT2, height=72)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        lf = tk.Frame(hdr, bg=ACCENT2)
        lf.pack(side="left", padx=18, pady=10)
        tk.Label(lf, text="⬡  JARVIS", font=("Segoe UI", 20, "bold"),
                 bg=ACCENT2, fg="white").pack(anchor="w")
        tk.Label(lf, text="Gopal ka AI Dost  •  Hindi Voice Assistant",
                 font=FONT_S, bg=ACCENT2, fg="#c4b5fd").pack(anchor="w")

        rf = tk.Frame(hdr, bg=ACCENT2)
        rf.pack(side="right", padx=18)
        self.status_dot = tk.Label(rf, text="● ONLINE", font=FONT_S, bg=ACCENT2, fg=GREEN)
        self.status_dot.pack(anchor="e")
        self.time_lbl = tk.Label(rf, text="", font=FONT_S, bg=ACCENT2, fg="#c4b5fd")
        self.time_lbl.pack(anchor="e")
        self._tick()

        # QUICK BAR
        qbar = tk.Frame(self.root, bg=BG2, pady=8)
        qbar.pack(fill="x")
        tk.Label(qbar, text="Quick:", font=FONT_S, bg=BG2, fg=TEXT_DIM).pack(side="left", padx=12)
        for q in ["Kitne baje hain","Mausam batao","System info","Notes dikhao","Joke sunao","Motivate karo","Help"]:
            tk.Button(qbar, text=q, font=FONT_S, bg=BG3, fg=ACCENT,
                      relief="flat", bd=0, cursor="hand2", padx=9, pady=5,
                      activebackground=ACCENT2, activeforeground="white",
                      command=lambda c=q: self._quick(c)).pack(side="left", padx=3)

        # CHAT
        self.chat = scrolledtext.ScrolledText(
            self.root, font=FONT, bg=BG, fg=TEXT, relief="flat", bd=0,
            padx=16, pady=12, state="disabled", wrap="word")
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_config("jarvis", foreground=ACCENT,   font=FONT_B)
        self.chat.tag_config("user",   foreground=ORANGE,   font=FONT_B)
        self.chat.tag_config("voice",  foreground=GREEN,    font=FONT_B)
        self.chat.tag_config("msg",    foreground=TEXT,     font=FONT)
        self.chat.tag_config("dim",    foreground=TEXT_DIM, font=FONT_S)
        self.chat.tag_config("system", foreground=YELLOW,   font=FONT_S)

        # INPUT BAR
        bar = tk.Frame(self.root, bg=BG2, pady=10)
        bar.pack(fill="x")

        self.mute_btn = tk.Button(bar, text="🔊", font=("Segoe UI",14),
                                  bg=BG3, fg=GREEN, relief="flat", bd=0,
                                  padx=10, pady=7, cursor="hand2",
                                  command=self._toggle_mute)
        self.mute_btn.pack(side="left", padx=(12,4))

        self.mic_btn = tk.Button(bar, text="🎙 Bolo",
                                 font=FONT_B, bg=GREEN, fg="white",
                                 relief="flat", bd=0, padx=14, pady=7,
                                 cursor="hand2", command=self._start_listen,
                                 state="normal" if SR_AVAILABLE else "disabled")
        self.mic_btn.pack(side="left", padx=4)

        self.entry = tk.Entry(bar, font=FONT_T, bg=BG3, fg=TEXT, relief="flat", bd=0,
                              insertbackground=ACCENT, highlightthickness=2,
                              highlightcolor=ACCENT, highlightbackground=BG2)
        self.entry.pack(side="left", fill="x", expand=True, padx=8, ipady=10)
        self.entry.bind("<Return>", lambda e: self._send())

        tk.Button(bar, text="▶  Bhejo", font=FONT_B, bg=ACCENT2, fg="white",
                  relief="flat", bd=0, padx=18, pady=7, cursor="hand2",
                  activebackground="#6d28d9", command=self._send
                  ).pack(side="right", padx=(4,12))

        # FOOTER
        gtts_ok = "✅ gTTS Hindi" if GTTS_AVAILABLE else "❌ gTTS"
        stt_ok  = "✅ Voice Input" if SR_AVAILABLE  else "❌ Voice (install pyaudio)"
        pyt_ok  = "✅ pyttsx3"     if PYTTSX3_AVAILABLE else ""
        status  = "  |  ".join(filter(None, [stt_ok, gtts_ok, pyt_ok]))
        tk.Label(self.root, text=status + "   |   'help' type karo",
                 font=FONT_S, bg=BG, fg=TEXT_DIM).pack(pady=(0,6))

        self.entry.focus()

    def _tick(self):
        self.time_lbl.config(text=datetime.datetime.now().strftime("%I:%M:%S %p"))
        self.root.after(1000, self._tick)

    def _welcome(self):
        now  = datetime.datetime.now()
        hour = now.hour
        g = ("Subah bakhair" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening")
        msg = (f"{g} Gopal bhai!\n"
               f"Main hoon JARVIS — aapka AI dost!\n\n"
               f"Aaj {now.strftime('%A, %d %B %Y')} hai aur abhi {now.strftime('%I:%M %p')} baje hain.\n\n"
               f"Main Hindi mein bolun ga aur samjhunga bhi!\n"
               f"Mic button dabao ya type karo — main hamesha taiyaar hoon!\n"
               f"'Help' type karo sab commands dekhne ke liye.")
        self._jarvis_msg(msg)
        speak("Namaste Gopal bhai! Main Jarvis hoon, aapka A I dost. Kya seva karein aaj?")

    def _append(self, text, tag="msg"):
        self.chat.config(state="normal")
        self.chat.insert("end", text, tag)
        self.chat.config(state="disabled")
        self.chat.see("end")

    def _jarvis_msg(self, msg):
        ts = datetime.datetime.now().strftime("%I:%M %p")
        self._append(f"\nJARVIS  ", "jarvis")
        self._append(f"[{ts}]\n", "dim")
        self._append(f"{msg}\n", "msg")
        self._append("─" * 66 + "\n", "dim")

    def _user_msg(self, msg, via_voice=False):
        ts = datetime.datetime.now().strftime("%I:%M %p")
        label = "🎙 Gopal (Voice)" if via_voice else "✍ Gopal"
        tag   = "voice" if via_voice else "user"
        self._append(f"\n{label}  ", tag)
        self._append(f"[{ts}]\n", "dim")
        self._append(f"{msg}\n", "msg")

    def _quick(self, cmd):
        self.entry.delete(0, "end")
        self.entry.insert(0, cmd)
        self._send()

    def _send(self, via_voice=False):
        cmd = self.entry.get().strip()
        if not cmd: return
        self.entry.delete(0, "end")
        self._user_msg(cmd, via_voice=via_voice)
        threading.Thread(target=self._respond, args=(cmd,), daemon=True).start()

    def _respond(self, cmd):
        self.root.after(0, lambda: self.status_dot.config(text="● Soch raha hoon...", fg=YELLOW))
        try:
            response = process_command(cmd)
        except Exception as e:
            response = f"Arey yaar kuch gadbad ho gayi! Error: {e}"
        self.root.after(0, lambda: self._jarvis_msg(response))
        self.root.after(0, lambda: self.status_dot.config(text="● ONLINE", fg=GREEN))
        if not self.mute:
            speak(response)

    def _start_listen(self):
        if self.listening: return
        self.listening = True
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _listen_thread(self):
        self.root.after(0, lambda: self.mic_btn.config(text="🔴 Sun raha hoon...", bg=RED))
        self.root.after(0, lambda: self.status_dot.config(text="● Sun raha hoon...", fg=RED))
        self.root.after(0, lambda: self._append("\n🎙 Jarvis sun raha hai... boliye Gopal bhai!\n", "system"))
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=12)
            text = None
            for lang in ["hi-IN", "en-IN", "en-US"]:
                try:
                    text = recognizer.recognize_google(audio, language=lang)
                    break
                except:
                    continue
            if text:
                self.root.after(0, lambda t=text: self._fill_and_send(t))
            else:
                self.root.after(0, lambda: self._jarvis_msg(
                    "Bhai kuch suna nahi! Thoda seedha aur clear bolna! 😄"))
                speak("Bhai kuch suna nahi, thoda clear bolna!")
        except Exception as e:
            if "WaitTimeoutError" in str(type(e)):
                self.root.after(0, lambda: self._jarvis_msg(
                    "Arey Gopal bhai, kuch bola hi nahi! Darrte kyun ho? 😄"))
            else:
                self.root.after(0, lambda: self._jarvis_msg(
                    f"Microphone mein thoda problem hai bhai!\nCheck karo: {e}"))
        finally:
            self.listening = False
            self.root.after(0, lambda: self.mic_btn.config(text="🎙 Bolo", bg=GREEN))
            self.root.after(0, lambda: self.status_dot.config(text="● ONLINE", fg=GREEN))

    def _fill_and_send(self, text):
        self.entry.delete(0, "end")
        self.entry.insert(0, text)
        self._send(via_voice=True)

    def _toggle_mute(self):
        self.mute = not self.mute
        if self.mute:
            self.mute_btn.config(text="🔇", fg=RED)
            self._jarvis_msg("Mute kar diya! Ab main bolun ga nahi, sirf likhun ga. 🔇")
        else:
            self.mute_btn.config(text="🔊", fg=GREEN)
            self._jarvis_msg("Unmute ho gaya! Ab phir se bolun ga main! 🔊")
            speak("Wapas aa gaya main Gopal bhai!")

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = JarvisApp(root)
    root.mainloop()
