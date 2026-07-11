"""
JARVIS - Sir ka AI Assistant
Neural TTS (ElevenLabs / Piper / Edge) | Tapori Hindi | v3.0
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import asyncio
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

# ── TTS Manager (replaces all individual TTS engines) ────────────────────────
from tts_manager import get_manager as _get_tts, speak as _tts_speak

# Lazy-init TTS in background so UI starts instantly
_tts_manager = None
_tts_init_done = threading.Event()

def _init_tts_bg():
    global _tts_manager
    _tts_manager = _get_tts()
    _tts_init_done.set()

def speak(text: str):
    """Speak via best available engine. Thread-safe."""
    if _tts_manager is not None:
        _tts_manager.speak(text)

# Optional packages still used by GUI
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False



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
#  HINDI RESPONSES (Sir instead of Gopal bhai)
# ─────────────────────────────────────────────────────────────────────────────
GREETINGS = [
    "Namaste Sir. Main Jarvis hoon, aapki seva mein taiyaar hoon. Batayein, kya kaam hai?",
    "Haan Sir, bataiye. Main poori tarah se available hoon.",
    "Good day, Sir. Aapka intezaar kar raha tha. Kya seva karein?",
    "Ji Sir. Main sun raha hoon. Kya assistance chahiye?",
    "Sir, aap aa gaye. Kya haal hai? Main ready hoon.",
]

HOWRU = [
    "Main bilkul theek hoon Sir, shukriya poochne ke liye. Aap batayein, kya kaam hai?",
    "Ekdum operational hoon Sir. Sabhi systems normal hain. Aap sunayein.",
    "Perfect condition mein hoon Sir. Aapki seva ke liye hamesha taiyaar.",
]

THANKS = [
    "Yeh mera farz hai Sir. Aur koi kaam ho toh zaroor batayein.",
    "Shukriya ki zaroorat nahi Sir, main iske liye hi hoon.",
    "Ji Sir, khushi mili seva karke. Koi aur kaam?",
]

JOKES = [
    "Sir, ek chhoti si baat - Ek programmer ne doctor se kaha, mera bug theek karo. Doctor bola, main insaan theek karta hoon. Programmer ne kaha, kya fark padta hai?",
    "Sir, yeh suna hai? Ek developer ne commit message likha - final fix. Agle din phir likha - actually final fix. Phir - okay ab sach mein final fix. Yahi hota hai Sir.",
    "Sir, Python developer ne kaha - Main kabhi bug nahi karta. Code hi galat hota hai. Classic logic hai.",
    "Sir, ek coder raat bhar jaagta raha ek missing semicolon ke liye. Subah mila. Line ek mein tha. Ye life hai Sir.",
]

MOTIVATION = [
    "Sir, ek baat yaad rakhiye - Jo log koshish nahi chhodte, woh kabhi haarte nahi. Aap kar sakte hain.",
    "Sir, chhote chhote kadam bhi manzil tak pahunchate hain. Chalte rahiye.",
    "Sir, mushkilein aayen toh samjhiye aap sahi raaste par hain. Ye ek acchi nishani hai.",
    "Sir, aapka kaam ek din duniya dekhegi. Bas rukna mat.",
    "Sir, success unhe milti hai jo haar ke baad bhi uthte hain.",
]

GOODNIGHT = [
    "Good night Sir. Kal phir milenge. Aaram karein.",
    "Sir, ab sone ka waqt aa gaya. Kal ke liye ready rehna. Good night.",
]

GOODMORNING = [
    "Good morning Sir. Aaj ka din productive raha toh bahut accha hoga. Kya plan hai?",
    "Subah bakhair Sir. Main prepared hoon. Batayein kya karna hai aaj.",
]

# ─────────────────────────────────────────────────────────────────────────────
#  COMMAND PROCESSOR
# ─────────────────────────────────────────────────────────────────────────────
def process_command(cmd):
    cmd = cmd.strip()
    low = cmd.lower()

    # ── GREETINGS ─────────────────────────────────────────────────────────────
    if any(x in low for x in ["hello","hi","hey","hii","namaste","namaskar",
                                "good morning","good evening","good night",
                                "subah","raat","salam","kya scene","bol"]):
        if any(x in low for x in ["good night","raat","sone"]):
            return random.choice(GOODNIGHT)
        if any(x in low for x in ["good morning","subah"]):
            return random.choice(GOODMORNING)
        return random.choice(GREETINGS)

    # ── HOW ARE YOU ───────────────────────────────────────────────────────────
    if any(x in low for x in ["how are you","kaisa hai","kya haal","theek ho","kaisa chal"]):
        return random.choice(HOWRU)

    # ── THANKS ────────────────────────────────────────────────────────────────
    if any(x in low for x in ["thanks","thank you","shukriya","dhanyawad","bahut accha","wah"]):
        return random.choice(THANKS)

    # ── TIME ─────────────────────────────────────────────────────────────────
    if any(x in low for x in ["time","kitne baje","samay","kya time","time batao","baje"]):
        now = datetime.datetime.now()
        h   = now.hour
        note = "Arre Sir chai piya kya?" if 7 <= h <= 9 else \
               "Sir dopahar ho gayi, khana khaya?" if 12 <= h <= 14 else \
               "Sir din dhal raha hai, kaam kaisi chal rahi hai?" if 17 <= h <= 19 else \
               "Arre Sir itni raat! So jao bhai!" if h >= 22 else ""
        return (f"Sir, time hai abhi {now.strftime('%I:%M %p')}!\n"
                f"Aaj {now.strftime('%A, %d %B %Y')} hai.\n"
                f"{note}").strip()

    # ── DATE ─────────────────────────────────────────────────────────────────
    if any(x in low for x in ["date","aaj","today","din","tarikh","kaunsa din"]):
        now = datetime.datetime.now()
        return (f"Arre Sir, aaj {now.strftime('%A, %d %B %Y')} hai!\n"
                f"Mahina {now.strftime('%B')} chal raha hai, {now.year} ka saal. Time kaisa ud raha hai na!")

    # ── WEATHER ──────────────────────────────────────────────────────────────
    if any(x in low for x in ["weather","mausam","barish","temperature","garmi","sardi"]):
        city = "Pune"
        stop = {"weather","mausam","barish","temperature","garmi","sardi",
                "in","at","for","the","what","is","today","ka","mein","ki","batao"}
        for w in low.split():
            if w not in stop and len(w) > 2:
                city = w.capitalize(); break
        try:
            url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
            with urllib.request.urlopen(url, timeout=5) as r:
                result = r.read().decode()
            return f"Sir dekho, {city} ka mausam:\n\n  {result}\n\nBaahar jaana ho toh jacket le lena, pakka!"
        except:
            return f"Arre Sir, {city} ka mausam abhi nahi mila! Net check karo yaar!"

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
                return f"Lo Sir, {app.capitalize()} khol diya! Le jao!"
            except:
                return f"Arre Sir, {app} nahi khula yaar! Installed hai na check karo!"

    # ── YOUTUBE ──────────────────────────────────────────────────────────────
    if any(x in low for x in ["youtube","gana","music","song","bajao","play"]):
        query = low
        for w in ["play","open","youtube","gana","music","song","bajao","on","sir","please"]:
            query = query.replace(w,"").strip()
        if query:
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
            return f"Lo Sir! YouTube pe '{query}' dhoondh diya! Sunno mast!"
        else:
            webbrowser.open("https://www.youtube.com")
            return "Lo Sir, YouTube khol diya! Kaunsa gana sunna hai?"

    # ── WEB SEARCH ───────────────────────────────────────────────────────────
    if any(x in low for x in ["search","google","dhundho","find","look up","batao"]):
        query = low
        for w in ["search for","search","google","dhundho","find","look up","batao","sir","please"]:
            query = query.replace(w,"").strip()
        if query:
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            return f"Haan Sir! '{query}' Google pe dhoondh diya! Dekho kya mila!"
        else:
            webbrowser.open("https://www.google.com")
            return "Lo Sir, Google khol diya! Dhundho jo bhi chahiye!"

    # ── GMAIL ────────────────────────────────────────────────────────────────
    if any(x in low for x in ["gmail","mail","email","inbox"]):
        webbrowser.open("https://mail.google.com")
        return "Lo Sir, Gmail khol diya! Dekho koi message aaya kya!"

    # ── GITHUB ───────────────────────────────────────────────────────────────
    if "github" in low:
        webbrowser.open("https://github.com/hariomsurve0-lab")
        return "Lo Sir, GitHub khol diya! Waah, solid kaam hai aapka!"

    # ── SYSTEM INFO ──────────────────────────────────────────────────────────
    if any(x in low for x in ["system","cpu","ram","memory","battery","computer"]):
        try:
            import psutil
            cpu  = psutil.cpu_percent(interval=1)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            bat  = psutil.sensors_battery()
            bat_s = f"{bat.percent:.0f}% ({'Charging' if bat.power_plugged else 'On Battery'})" if bat else "N/A"
            health = "Sir sab mast chal raha hai! Ekdum solid!" if cpu < 80 and ram.percent < 80 \
                     else "Arre Sir, system thoda dhima pad raha hai! Kuch apps band karo yaar!"
            return (f"Lo Sir, computer ki full report:\n\n"
                    f"  Machine  : {platform.node()}\n"
                    f"  OS       : {platform.system()} {platform.release()}\n"
                    f"  CPU      : {cpu}% chal raha hai\n"
                    f"  RAM      : {ram.percent}% use ho raha hai ({ram.used//1024//1024} MB / {ram.total//1024//1024} MB)\n"
                    f"  Disk C:  : {disk.percent}% bhara hua ({disk.used//1024//1024//1024} GB / {disk.total//1024//1024//1024} GB)\n"
                    f"  Battery  : {bat_s}\n\n"
                    f"  {health}")
        except ImportError:
            return (f"Sir basic info dekho:\n\n"
                    f"  OS      : {platform.system()} {platform.release()}\n"
                    f"  Machine : {platform.node()}\n"
                    f"  Python  : {platform.python_version()}\n\n"
                    f"  Arre Sir full stats ke liye 'pip install psutil' maar do!")

    # ── ADD NOTE ─────────────────────────────────────────────────────────────
    if any(low.startswith(x) for x in ["note:","add note","remember","yaad rakhna","note kar","save note"]):
        note_text = cmd
        for p in ["note:","add note","remember","yaad rakhna","note kar","save note"]:
            if note_text.lower().startswith(p):
                note_text = note_text[len(p):].strip()
                break
        notes = load_notes()
        notes.append({"text": note_text, "time": datetime.datetime.now().strftime("%d %b %Y %I:%M %p")})
        save_notes(notes)
        return f"Done Sir! Note likh liya:\n\n  \"{note_text}\"\n\nYaad rahega pakka, chinta mat karo!"

    # ── SHOW NOTES ───────────────────────────────────────────────────────────
    if any(x in low for x in ["show notes","my notes","notes dikhao","meri notes","notes batao"]):
        notes = load_notes()
        if not notes:
            return "Arre Sir, koi note nahi hai abhi! 'note: kuch bhi' bol ke save karo!"
        result = f"Sir dekho, {len(notes)} notes hain:\n"
        for i, n in enumerate(notes, 1):
            result += f"\n  {i}. [{n['time']}]\n     {n['text']}"
        return result

    # ── CLEAR NOTES ──────────────────────────────────────────────────────────
    if any(x in low for x in ["clear notes","delete notes","notes hatao","notes delete"]):
        save_notes([])
        return "Done Sir! Sab notes saaf kar diye! Fresh start!"

    # ── JOKE ─────────────────────────────────────────────────────────────────
    if any(x in low for x in ["joke","funny","hasao","mazak","chutkula"]):
        return random.choice(JOKES)

    # ── MOTIVATION ───────────────────────────────────────────────────────────
    if any(x in low for x in ["motivate","motivation","inspire","quote","himmat","hosla"]):
        return random.choice(MOTIVATION)

    # ── WHO ARE YOU ──────────────────────────────────────────────────────────
    if any(x in low for x in ["who are you","tum kaun","aap kaun","introduce","parichay","kon hai"]):
        return ("Arre Sir, main hoon JARVIS!\n\n"
                "Just A Rather Very Intelligent System — fancy naam hai na?\n"
                "Basically aapka digital dost hoon main!\n\n"
                "Apps kholna, kuch bhi dhundhna, mausam batana, notes likhna —\n"
                "sab kuch karta hoon main, aur wo bhi bina kisi natak ke!\n\n"
                "Bol de kya karna hai, main kar dunga!")

    # ── HELP ─────────────────────────────────────────────────────────────────
    if any(x in low for x in ["help","features","commands","kya karta","kya kar sakte"]):
        return ("Sir sun, yeh sab kar sakta hoon main:\n\n"
                "  Time/Date  : 'kitne baje hain', 'aaj kya date hai'\n"
                "  Mausam     : 'Bangalore ka mausam bata'\n"
                "  Apps       : 'chrome khol', 'notepad khol'\n"
                "  Search     : 'Python tutorials dhundh'\n"
                "  YouTube    : 'lofi music baja'\n"
                "  Gmail      : 'gmail khol'\n"
                "  System     : 'system info bata'\n"
                "  Notes      : 'note: meeting 5 baje', 'notes dikhao'\n"
                "  Joke       : 'joke suna'\n"
                "  Motivate   : 'motivate kar'\n"
                "  Voice      : Green mic button dabaao\n\n"
                "Bas bol de Sir, main kar dunga!")

    # ── DEFAULT ──────────────────────────────────────────────────────────────
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(cmd)}")
    return (f"Arre Sir, '{cmd}' thoda samajh nahi aaya mujhe!\n"
            f"Google pe dhoondh diya hai, dekho wahan!\n"
            f"'Help' bol do Sir, sab commands bata dunga!")

# ─────────────────────────────────────────────────────────────────────────────
#  JARVIS GUI
# ─────────────────────────────────────────────────────────────────────────────
class JarvisApp:
    def __init__(self, root):
        self.root      = root
        self.listening = False
        self.mute      = False
        self.root.title("JARVIS — Just A Rather Very Intelligent System")
        self.root.geometry("900x700")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(680, 540)
        self._build_ui()
        # Init TTS in background — don't block the UI
        threading.Thread(target=_init_tts_bg, daemon=True).start()
        self._welcome()

    def _build_ui(self):
        # HEADER
        hdr = tk.Frame(self.root, bg="#0f0f1a", height=75)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        # Accent line on top
        tk.Frame(self.root, bg=ACCENT, height=2).place(x=0, y=0, relwidth=1)

        lf = tk.Frame(hdr, bg="#0f0f1a")
        lf.pack(side="left", padx=20, pady=10)
        tk.Label(lf, text="J.A.R.V.I.S", font=("Segoe UI", 22, "bold"),
                 bg="#0f0f1a", fg=ACCENT).pack(anchor="w")
        tk.Label(lf, text="Just A Rather Very Intelligent System  •  Male Hindi Voice",
                 font=FONT_S, bg="#0f0f1a", fg=TEXT_DIM).pack(anchor="w")

        rf = tk.Frame(hdr, bg="#0f0f1a")
        rf.pack(side="right", padx=20)
        self.status_dot = tk.Label(rf, text="● ONLINE", font=("Segoe UI", 9, "bold"),
                                   bg="#0f0f1a", fg=GREEN)
        self.status_dot.pack(anchor="e")
        self.time_lbl = tk.Label(rf, text="", font=FONT_S, bg="#0f0f1a", fg=ACCENT)
        self.time_lbl.pack(anchor="e")
        self._tick()

        # DIVIDER
        tk.Frame(self.root, bg=ACCENT2, height=1).pack(fill="x")

        # QUICK BAR
        qbar = tk.Frame(self.root, bg=BG2, pady=8)
        qbar.pack(fill="x")
        tk.Label(qbar, text="Quick:", font=FONT_S,
                 bg=BG2, fg=TEXT_DIM).pack(side="left", padx=14)
        for q in ["Kitne baje hain","Mausam batao","System info",
                  "Notes dikhao","Joke sunao","Motivate karo","Help"]:
            tk.Button(qbar, text=q, font=FONT_S, bg=BG3, fg=ACCENT,
                      relief="flat", bd=0, cursor="hand2", padx=10, pady=5,
                      activebackground=ACCENT2, activeforeground="white",
                      command=lambda c=q: self._quick(c)).pack(side="left", padx=3)
        # Settings button (right side)
        tk.Button(qbar, text="⚙ TTS", font=FONT_S, bg="#374151", fg=YELLOW,
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=5,
                  activebackground="#4b5563", activeforeground=YELLOW,
                  command=self._open_settings).pack(side="right", padx=10)

        # CHAT AREA
        self.chat = scrolledtext.ScrolledText(
            self.root, font=FONT, bg=BG, fg=TEXT, relief="flat", bd=0,
            padx=20, pady=14, state="disabled", wrap="word",
            selectbackground=ACCENT2)
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_config("jarvis", foreground=ACCENT,   font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("user",   foreground=ORANGE,   font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("voice",  foreground=GREEN,    font=("Segoe UI", 11, "bold"))
        self.chat.tag_config("msg",    foreground=TEXT,     font=FONT)
        self.chat.tag_config("dim",    foreground=TEXT_DIM, font=FONT_S)
        self.chat.tag_config("system", foreground=YELLOW,   font=FONT_S)

        # DIVIDER
        tk.Frame(self.root, bg=BG3, height=1).pack(fill="x")

        # INPUT BAR
        bar = tk.Frame(self.root, bg=BG2, pady=10)
        bar.pack(fill="x")

        self.mute_btn = tk.Button(bar, text="🔊", font=("Segoe UI", 14),
                                  bg=BG3, fg=GREEN, relief="flat", bd=0,
                                  padx=10, pady=7, cursor="hand2",
                                  command=self._toggle_mute)
        self.mute_btn.pack(side="left", padx=(14, 4))

        self.mic_btn = tk.Button(
            bar, text="🎙  Voice",
            font=("Segoe UI", 10, "bold"), bg=GREEN, fg="white",
            relief="flat", bd=0, padx=14, pady=7, cursor="hand2",
            activebackground="#059669",
            command=self._start_listen,
            state="normal" if SR_AVAILABLE else "disabled"
        )
        self.mic_btn.pack(side="left", padx=4)

        self.entry = tk.Entry(
            bar, font=("Segoe UI", 12), bg=BG3, fg=TEXT,
            relief="flat", bd=0, insertbackground=ACCENT,
            highlightthickness=2, highlightcolor=ACCENT,
            highlightbackground=BG2
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=8, ipady=10)
        self.entry.bind("<Return>", lambda e: self._send())
        self.entry.insert(0, "Aapka hukum, Sir...")
        self.entry.config(fg=TEXT_DIM)
        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

        tk.Button(bar, text="▶  Send", font=("Segoe UI", 10, "bold"),
                  bg=ACCENT2, fg="white", relief="flat", bd=0,
                  padx=18, pady=7, cursor="hand2",
                  activebackground="#6d28d9",
                  command=self._send).pack(side="right", padx=(4, 14))

        # FOOTER — shows active TTS engine
        self.footer_lbl = tk.Label(
            self.root, text="Initialising TTS...",
            font=("Segoe UI", 8), bg=BG, fg=TEXT_DIM
        )
        self.footer_lbl.pack(pady=(2, 6))
        # Update footer once TTS is ready
        self.root.after(2000, self._update_footer)

        self.entry.focus()

    def _on_focus_in(self, e):
        if self.entry.get() == "Aapka hukum, Sir...":
            self.entry.delete(0, "end")
            self.entry.config(fg=TEXT)

    def _on_focus_out(self, e):
        if not self.entry.get():
            self.entry.insert(0, "Aapka hukum, Sir...")
            self.entry.config(fg=TEXT_DIM)

    def _tick(self):
        self.time_lbl.config(text=datetime.datetime.now().strftime("%I:%M:%S %p"))
        self.root.after(1000, self._tick)

    def _update_footer(self):
        if _tts_manager:
            engine_lbl = _tts_manager.engine_label
            stt = "STT: Ready" if SR_AVAILABLE else "STT: needs pyaudio"
            self.footer_lbl.config(
                text=f"JARVIS v3.0  |  TTS: {engine_lbl}  |  {stt}  |  'help' for commands"
            )
        else:
            self.root.after(1000, self._update_footer)

    def _welcome(self):
        now  = datetime.datetime.now()
        hour = now.hour
        g = ("Good morning" if hour < 12 else
             "Good afternoon" if hour < 17 else "Good evening")
        msg = (f"{g} Sir!\n\n"
               f"Aa gaya main — JARVIS v3.0! Aapka digital dost!\n"
               f"Aaj {now.strftime('%A, %d %B %Y')} hai, abhi {now.strftime('%I:%M %p')} baje hain.\n\n"
               f"TTS Engine : Initialising neural voice...\n"
               f"Status     : Ekdum ready, full on!\n\n"
               f"Bol de Sir kya karna hai, main hoon na!\n"
               f"'Help' bol do, ya TTS button se engine switch karo.")
        self._jarvis_msg(msg)
        # Speak after TTS is ready
        self.root.after(3000, lambda: speak("Arre Sir! Aa gaya main! Jarvis hazir hai! Kya karna hai bolo!"))

    def _append(self, text, tag="msg"):
        self.chat.config(state="normal")
        self.chat.insert("end", text, tag)
        self.chat.config(state="disabled")
        self.chat.see("end")

    def _jarvis_msg(self, msg):
        ts = datetime.datetime.now().strftime("%I:%M:%S %p")
        self._append(f"\nJARVIS  ", "jarvis")
        self._append(f"[{ts}]\n", "dim")
        self._append(f"{msg}\n", "msg")
        self._append("─" * 70 + "\n", "dim")

    def _user_msg(self, msg, via_voice=False):
        ts    = datetime.datetime.now().strftime("%I:%M:%S %p")
        label = "🎙  Sir (Voice)" if via_voice else "Sir"
        tag   = "voice" if via_voice else "user"
        self._append(f"\n{label}  ", tag)
        self._append(f"[{ts}]\n", "dim")
        self._append(f"{msg}\n", "msg")

    def _quick(self, cmd):
        if self.entry.get() == "Aapka hukum, Sir...":
            self.entry.delete(0, "end")
        self.entry.delete(0, "end")
        self.entry.config(fg=TEXT)
        self.entry.insert(0, cmd)
        self._send()

    def _send(self):
        cmd = self.entry.get().strip()
        if not cmd or cmd == "Aapka hukum, Sir...":
            return
        self.entry.delete(0, "end")
        self._user_msg(cmd)
        threading.Thread(target=self._respond, args=(cmd,), daemon=True).start()

    def _respond(self, cmd):
        self.root.after(0, lambda: self.status_dot.config(
            text="● Processing...", fg=YELLOW))
        try:
            response = process_command(cmd)
        except Exception as e:
            response = f"Sir, ek technical error aa gaya: {e}\nDobara try karo!"
        self.root.after(0, lambda: self._jarvis_msg(response))
        self.root.after(0, lambda: self.status_dot.config(text="● ONLINE", fg=GREEN))
        if not self.mute:
            speak(response)

    def _start_listen(self):
        if self.listening:
            return
        self.listening = True
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _listen_thread(self):
        self.root.after(0, lambda: self.mic_btn.config(
            text="🔴 Listening...", bg=RED))
        self.root.after(0, lambda: self.status_dot.config(
            text="● Listening...", fg=RED))
        self.root.after(0, lambda: self._append(
            "\nListening, Sir. Please speak now.\n", "system"))
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
                    "Arre Sir, suna toh lekin samajh nahi aaya! Thoda clear bol yaar!"))
        except Exception as ex:
            err_msg = "Arre Sir, kuch bola hi nahi! Darrte kyun ho?" if "Timeout" in str(type(ex).__name__) \
                      else f"Sir, mic mein kuch gadbad hai yaar! {ex}"
            self.root.after(0, lambda m=err_msg: self._jarvis_msg(m))
        finally:
            self.listening = False
            self.root.after(0, lambda: self.mic_btn.config(text="🎙  Voice", bg=GREEN))
            self.root.after(0, lambda: self.status_dot.config(text="● ONLINE", fg=GREEN))

    def _fill_and_send(self, text):
        self.entry.delete(0, "end")
        self.entry.config(fg=TEXT)
        self.entry.insert(0, text)
        self._user_msg(text, via_voice=True)
        self.entry.delete(0, "end")
        threading.Thread(target=self._respond, args=(text,), daemon=True).start()

    def _toggle_mute(self):
        self.mute = not self.mute
        if _tts_manager:
            _tts_manager.mute = self.mute
        if self.mute:
            self.mute_btn.config(text="🔇", fg=RED)
            self._jarvis_msg("Theek hai Sir, chup ho gaya main! Sirf type karunga ab.")
        else:
            self.mute_btn.config(text="🔊", fg=GREEN)
            self._jarvis_msg("Wapas aa gaya Sir! Ab phir se bolunga!")
            speak("Haan Sir! Wapas aa gaya main! Bol de kya karna hai!")

    # ── Settings Panel ────────────────────────────────────────────────────────
    def _open_settings(self):
        """Open TTS settings window."""
        win = tk.Toplevel(self.root)
        win.title("TTS Engine Settings")
        win.geometry("520x440")
        win.configure(bg=BG)
        win.resizable(False, False)

        tk.Label(win, text="TTS Engine Settings", font=("Segoe UI", 14, "bold"),
                 bg=BG, fg=ACCENT).pack(pady=(16, 4))
        tk.Label(win, text="Choose voice engine & configure API keys",
                 font=FONT_S, bg=BG, fg=TEXT_DIM).pack(pady=(0, 12))

        # Current engine display
        if _tts_manager:
            cur = _tts_manager.engine_label
            avail = _tts_manager.available_engines
        else:
            cur, avail = "Initialising...", []

        tk.Label(win, text=f"Active: {cur}", font=FONT_B, bg=BG, fg=GREEN).pack()

        # Engine selector
        frm = tk.Frame(win, bg=BG, pady=10)
        frm.pack(fill="x", padx=20)
        tk.Label(frm, text="Switch Engine:", font=FONT_B, bg=BG, fg=TEXT).pack(anchor="w")
        engine_var = tk.StringVar(value=_tts_manager.active_name if _tts_manager else "edge_tts")
        options = [(k, v) for k, v in avail] if avail else [("edge_tts", "Edge TTS Neural")]
        for key, label in options:
            tk.Radiobutton(
                frm, text=label, variable=engine_var, value=key,
                font=FONT, bg=BG, fg=TEXT, selectcolor=BG3,
                activebackground=BG, activeforeground=ACCENT
            ).pack(anchor="w", padx=10, pady=2)

        # ElevenLabs API key
        tk.Label(win, text="ElevenLabs API Key (optional):",
                 font=FONT_B, bg=BG, fg=TEXT).pack(anchor="w", padx=20, pady=(10,2))
        key_var = tk.StringVar(value=(
            _tts_manager.config["elevenlabs"].get("api_key","") if _tts_manager else ""
        ))
        key_entry = tk.Entry(win, textvariable=key_var, font=FONT, bg=BG3, fg=TEXT,
                             relief="flat", show="*", highlightthickness=1,
                             highlightcolor=ACCENT, highlightbackground=BG3)
        key_entry.pack(fill="x", padx=20, ipady=4)

        # ElevenLabs Voice ID
        tk.Label(win, text="ElevenLabs Voice ID / Preset:",
                 font=FONT_B, bg=BG, fg=TEXT).pack(anchor="w", padx=20, pady=(8,2))
        
        voice_var = tk.StringVar(value=(
            _tts_manager.config["elevenlabs"].get("voice_id","pNInz6obpgDQGcFmaJgB") if _tts_manager else "pNInz6obpgDQGcFmaJgB"
        ))
        voice_entry = tk.Entry(win, textvariable=voice_var, font=FONT, bg=BG3, fg=TEXT,
                               relief="flat", highlightthickness=1,
                               highlightcolor=ACCENT, highlightbackground=BG3)
        voice_entry.pack(fill="x", padx=20, ipady=4)

        # Presets frame
        pfrm = tk.Frame(win, bg=BG)
        pfrm.pack(fill="x", padx=20, pady=4)
        presets = [
            ("Adam (Warm Male)", "pNInz6obpgDQGcFmaJgB"),
            ("Rachel (Warm Female)", "21m00Tcm4TlvDq8ikWAM"),
            ("Antoni (Deep Male)", "ErXwobaYiN019PkySvjV"),
            ("Clyde (Deep Video Game)", "2EiwWnXF2V4j28gcXi8t")
        ]
        for name, vid in presets:
            btn = tk.Button(pfrm, text=name.split()[0], font=FONT_S, bg=BG3, fg=ACCENT,
                            relief="flat", bd=0, cursor="hand2", padx=6, pady=2,
                            command=lambda v=vid, n=name: [voice_var.set(v), _tts_manager.config["elevenlabs"].update({"voice_name": n}) if _tts_manager else None])
            btn.pack(side="left", padx=2)

        # ElevenLabs Model Selection
        tk.Label(win, text="ElevenLabs Model:",
                 font=FONT_B, bg=BG, fg=TEXT).pack(anchor="w", padx=20, pady=(8,2))
        
        model_var = tk.StringVar(value=(
            _tts_manager.config["elevenlabs"].get("model", "eleven_multilingual_v2") if _tts_manager else "eleven_multilingual_v2"
        ))
        mfrm = tk.Frame(win, bg=BG)
        mfrm.pack(fill="x", padx=20, pady=2)
        models = [
            ("Multilingual v2 (Best Quality)", "eleven_multilingual_v2"),
            ("Turbo v2.5 (Fast / Low Cost)", "eleven_turbo_v2_5"),
            ("Flash v2.5 (Super Fast)", "eleven_flash_v2_5")
        ]
        for label, mkey in models:
            tk.Radiobutton(
                mfrm, text=label, variable=model_var, value=mkey,
                font=FONT_S, bg=BG, fg=TEXT, selectcolor=BG3,
                activebackground=BG, activeforeground=ACCENT
            ).pack(anchor="w", pady=1)

        # Status label
        status_lbl = tk.Label(win, text="", font=FONT_S, bg=BG, fg=GREEN)
        status_lbl.pack(pady=4)

        def _apply():
            if _tts_manager is None:
                status_lbl.config(text="TTS still initialising, try again!", fg=RED)
                return
            chosen = engine_var.get()
            api_key = key_var.get().strip()
            voice_id = voice_var.get().strip()
            model_id = model_var.get().strip()
            if api_key:
                _tts_manager.set_elevenlabs_key(api_key)
            if voice_id:
                _tts_manager.config["elevenlabs"]["voice_id"] = voice_id
            if model_id:
                _tts_manager.config["elevenlabs"]["model"] = model_id
            _tts_manager.set_engine(chosen)
            _tts_manager.save_config()
            self._update_footer()
            status_lbl.config(
                text=f"Applied! Active: {_tts_manager.engine_label}", fg=GREEN)
            self._jarvis_msg(f"Settings update ho gaye Sir! Active Model: {model_id}, Voice ID: {voice_id}")
            speak("Settings update ho gaye Sir!")

        def _test():
            speak("Arre Sir! Yeh test hai. Awaaz kaisi aa rahi hai? Theek hai na?")
            status_lbl.config(text="Testing voice... suniye!", fg=YELLOW)

        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(pady=14)
        tk.Button(btn_row, text="✓ Apply", font=FONT_B, bg=ACCENT2, fg="white",
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=_apply).pack(side="left", padx=6)
        tk.Button(btn_row, text="▶ Test Voice", font=FONT_B, bg=GREEN, fg="white",
                  relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
                  command=_test).pack(side="left", padx=6)
        tk.Button(btn_row, text="✕ Close", font=FONT_B, bg=BG3, fg=TEXT,
                  relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
                  command=win.destroy).pack(side="left", padx=6)

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = JarvisApp(root)
    root.mainloop()
