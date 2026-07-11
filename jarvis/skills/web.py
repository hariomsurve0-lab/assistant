import webbrowser
import urllib.parse
import urllib.request
import json
from jarvis.logger import logger

def search_google(query: str) -> str:
    if not query:
        return "Sir, kya search karna hai? Kuch bolna toh padega na!"
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"Arre Sir, Google pe '{query}' search kar diya hai! Browser mein check karo!"
    except Exception as e:
        logger.error(f"[Skill - Web] Google search failed: {e}")
        return f"Sir, Google search nahi khul paya: {e}"

def open_youtube(query: str = "") -> str:
    try:
        if query:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Lo Sir, YouTube pe '{query}' play kar raha hoon!"
        else:
            webbrowser.open("https://www.youtube.com")
            return "YouTube khol diya hai Sir! Enjoy karo."
    except Exception as e:
        logger.error(f"[Skill - Web] YouTube failed: {e}")
        return f"Sir, YouTube load nahi hua: {e}"

def get_weather_report(city: str = "Mumbai") -> str:
    city = city.strip()
    try:
        # Fetching free public weather metadata (no key required for lookup)
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        current = data['current_condition'][0]
        temp = current['temp_C']
        desc = current['weatherDesc'][0]['value']
        humidity = current['humidity']
        
        report = (
            f"Sir, {city} ka mausam bata raha hoon!\n\n"
            f"● Temperature : {temp}°C\n"
            f"● Condition : {desc}\n"
            f"● Humidity : {humidity}%\n\n"
            f"Sab badhiya hai Sir, maze karo!"
        )
        return report
    except Exception as e:
        logger.error(f"[Skill - Web] Weather report failed: {e}")
        return f"Sir, weather fetch karne mein network issue aa gaya yaar! wttr.in check nahi ho paa raha."
