import datetime
import platform
import os

print("=" * 45)
print("       JARVIS - System Info Report")
print("=" * 45)

now = datetime.datetime.now()
print(f"\nDate & Time  : {now.strftime('%A, %d %B %Y | %I:%M %p')}")
print(f"OS           : {platform.system()} {platform.release()}")
print(f"Machine      : {platform.node()}")
print(f"Python       : {platform.python_version()}")
print(f"Current Dir  : {os.getcwd()}")
print(f"User         : {os.environ.get('USERNAME', 'Gopal')}")

print("\n[OK] Python script executed successfully by Jarvis!")
print("=" * 45)
