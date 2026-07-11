import datetime
import random
from jarvis.logger import logger
from jarvis.core.plugins import get_plugin_manager

# ── Tapori Dialogues ──────────────────────────────────────────────────────────
GREETINGS = [
    "Namaste Sir! Bolo, kya sewa karein aapki?",
    "Arre Sir! Hazir hoon aapke liye! Boliye, kya orders hain?",
    "Namaste Sir! Boliye na, aaj computer mein kya tabahi machani hai?",
    "Oho Sir! Swagat hai aapka! Aadesh dijiye, Jarvis taiyar hai!"
]

JOKES = [
    "Sir, ek mast joke suniye: Ek baar exam mein pucha gaya - Gandhi ji ka janam kab hua? Ek bacche ne likha - Jab unki mummy ko pain hua! Marks: 100/100!",
    "Sir, Doctor ne Gopal bhai se pucha: Aapko kaunsi bimari hai? Gopal bhai bole: Doctor Sahab, mobile se time dekhne ki aadat hai. Doctor: Toh? Gopal bhai: Ghadi dekhne par lagta hai battery low ho gayi!",
    "Teacher: Sabse bada dushman kaun hai? Student: Chinni! Teacher: Chinni? Kyun? Student: Sir, kyunki yeh har ek ladki ko 'Sweet' bol kar fansa leti hai!",
    "Sir, ek aur: Pappu doctor ke paas gaya. Doctor: Aapko kaunsi bimari hai? Pappu: Sir, mujhe sapne mein bhoot dikhte hain aur woh mujhe football khilate hain. Doctor: Yeh tablet raat ko sone se pehle lena. Pappu: Kal se le sakta hoon? Aaj final match hai!"
]

MOTIVATION = [
    "Sir, suniye: Darrte kyun ho yaar? Jo hona hai woh toh hoke rahega, bas apna best do aur baaki sab mere pe chhod do!",
    "Arre Sir! Haar nahi maan ne ka! Jab tak todenge nahi, tab tak chhodenge nahi! Lage raho!",
    "Sir, Gopal bhai kehte hain - Sapne unke sach hote hain jinke sapno mein jaan hoti hai, pankho se kuch nahi hota hauslo se udaan hoti hai!",
    "Sir, life mein tension toh aati rahegi, par apna mood ekdum jhakaas rakhne ka! Chalo kaam shuru karo!"
]

def process_command(cmd: str) -> str:
    cmd_clean = cmd.lower().strip()
    logger.info(f"[Processor] Processing command: '{cmd_clean}'")
    
    pm = get_plugin_manager()
    
    # ── 1. GREETINGS ──────────────────────────────────────────────────────────
    if any(x in cmd_clean for x in ["namaste", "hello", "hey", "hi", "hazir"]):
        return random.choice(GREETINGS)
        
    # ── 2. DATE & TIME ────────────────────────────────────────────────────────
    elif any(x in cmd_clean for x in ["kitne baje", "samay", "time", "date", "tarikh"]):
        now = datetime.datetime.now()
        day = now.strftime('%A')
        time_str = now.strftime('%I:%M %p')
        return f"Sir, abhi {time_str} baje hain, aur aaj pyaara sa {day} hai!"
        
    # ── 3. JOKES ──────────────────────────────────────────────────────────────
    elif any(x in cmd_clean for x in ["joke", "chutkila", "chutkule"]):
        return random.choice(JOKES)
        
    # ── 4. MOTIVATION ─────────────────────────────────────────────────────────
    elif any(x in cmd_clean for x in ["motivate", "motivation", "shayari"]):
        return random.choice(MOTIVATION)
        
    # ── 5. SYSTEM REPORT / METRICS ────────────────────────────────────────────
    elif any(x in cmd_clean for x in ["system info", "stats", "hardware", "report"]):
        if "get_system_report" in pm.commands:
            return pm.commands["get_system_report"]()
        return "Sir, system skill loaded nahi hai."

    # ── 6. APPLICATION AUTOMATION ─────────────────────────────────────────────
    elif "kholo" in cmd_clean or "open" in cmd_clean or "launch" in cmd_clean:
        # Extract app name
        app_name = cmd_clean.replace("kholo", "").replace("open", "").replace("launch", "").strip()
        if "open_application" in pm.commands:
            return pm.commands["open_application"](app_name)
        return "Sir, application launcher offline hai."

    # ── 7. WEATHER REPORT ─────────────────────────────────────────────────────
    elif "mausam" in cmd_clean or "weather" in cmd_clean:
        # Check if user specified a city
        city = "Mumbai"
        for word in cmd_clean.split():
            if word not in ["mausam", "batao", "ka", "weather", "report"]:
                city = word.capitalize()
                break
        if "get_weather_report" in pm.commands:
            return pm.commands["get_weather_report"](city)
        return "Sir, weather skill offline hai."

    # ── 8. GOOGLE SEARCH ──────────────────────────────────────────────────────
    elif "search" in cmd_clean or "google" in cmd_clean:
        query = cmd_clean.replace("search", "").replace("google", "").strip()
        if "search_google" in pm.commands:
            return pm.commands["search_google"](query)
        return "Sir, web skill offline hai."

    # ── 9. YOUTUBE NAVIGATION ─────────────────────────────────────────────────
    elif "youtube" in cmd_clean or "song" in cmd_clean or "gana" in cmd_clean:
        query = cmd_clean.replace("youtube", "").replace("play", "").replace("gana", "").replace("song", "").strip()
        if "open_youtube" in pm.commands:
            return pm.commands["open_youtube"](query)
        return "Sir, web skill offline hai."

    # ── 10. NOTES MANAGEMENT ──────────────────────────────────────────────────
    elif "notes dikhao" in cmd_clean or "list notes" in cmd_clean or "view notes" in cmd_clean:
        if "list_all_notes" in pm.commands:
            return pm.commands["list_all_notes"]()
        return "Sir, notes database offline hai."
        
    elif "note likho" in cmd_clean or "write note" in cmd_clean or "save note" in cmd_clean:
        # Expect note format: "note likho <title> content <content>" or similar
        note_data = cmd_clean.replace("note likho", "").replace("write note", "").replace("save note", "").strip()
        if "content" in note_data:
            parts = note_data.split("content", 1)
            title = parts[0].strip()
            content = parts[1].strip()
        else:
            title = "Personal Note"
            content = note_data
            
        if "save_new_note" in pm.commands:
            return pm.commands["save_new_note"](title, content)
        return "Sir, notes database offline hai."

    elif "note delete" in cmd_clean or "remove note" in cmd_clean:
        title = cmd_clean.replace("note delete", "").replace("remove note", "").strip()
        if "remove_note" in pm.commands:
            return pm.commands["remove_note"](title)
        return "Sir, notes database offline hai."

    # ── 11. HELP DIRECTIVE ────────────────────────────────────────────────────
    elif any(x in cmd_clean for x in ["help", "madad", "commands", "kaam"]):
        return (
            "Sir, aap niche diye commands use kar sakte hain:\n\n"
            "● 'Namaste' — Greeting\n"
            "● 'Time' — Samay check karne ke liye\n"
            "● 'Mausam <City>' — Weather check\n"
            "● 'System info' — CPU & memory stats\n"
            "● 'Open Chrome' — App launch\n"
            "● 'Joke' — Mast chutkila suniye\n"
            "● 'Search <topic>' — Google query\n"
            "● 'Youtube <video>' — Play media\n"
            "● 'Note likho <title> content <text>' — Save notes\n"
            "● 'Notes dikhao' — Saved notes list\n"
            "● 'Note delete <title>' — Delete note\n"
            "● 'Help' — Yeh list dekhne ke liye"
        )
        
    # ── 12. CHAT FALLBACK ─────────────────────────────────────────────────────
    else:
        replies = [
            "Arre Sir! Suna toh, par ye mere list mein nahi mila. 'help' bol kar dekh lo kya kar sakta hoon!",
            "Sir, samajh nahi aaya! Thoda clear bolo na, ya phir kuch aur try karo!",
            "Sir, kya mast baat boli aapne, par main yeh command abhi tak seekh raha hoon! 'help' try karo!"
        ]
        return random.choice(replies)
