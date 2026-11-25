import base64
import ctypes
from datetime import datetime
import os
import re
import subprocess
import tempfile
import tkinter as tk
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from playsound import playsound
import psutil
import pyautogui
import pyperclip
import pywhatkit
import requests
import speech_recognition as sr


AWS_JARVIS_URL = os.environ.get(
    "AWS_JARVIS_URL",
    "https://amazonaws.com",
)


class JarvisHUD:

  def __init__(self):
    self.root = tk.Tk()
    self.root.overrideredirect(True)
    self.root.attributes("-topmost", True)
    self.root.attributes("-alpha", 0.90)
    self.root.configure(bg="#070b14")

    self.muted = False
    self.current_color = "#00d4ff"
    self.wave_phase = 0

    screen_w = self.root.winfo_screenwidth()
    win_w, win_h = 410, 134
    self.root.geometry(f"{win_w}x{win_h}+{screen_w - win_w - 20}+20")

    self.border = tk.Frame(self.root, bg="#00d4ff", padx=2, pady=2)
    self.border.pack(fill="both", expand=True)

    self.inner = tk.Frame(self.border, bg="#070b14", padx=12, pady=8)
    self.inner.pack(fill="both", expand=True)

    # Top Row: Status Title + Clickable Mute Button
    top_row = tk.Frame(self.inner, bg="#070b14")
    top_row.pack(fill="x")

    self.status_label = tk.Label(
        top_row,
        text="● JARVIS ONLINE",
        fg="#00d4ff",
        bg="#070b14",
        font=("Consolas", 10, "bold"),
        anchor="w",
    )
    self.status_label.pack(side="left", fill="x", expand=True)

    self.mute_btn = tk.Button(
        top_row,
        text="🎙️ LIVE",
        fg="#00ff88",
        bg="#111827",
        activebackground="#1f2937",
        activeforeground="#00ff88",
        font=("Consolas", 8, "bold"),
        bd=0,
        padx=6,
        pady=1,
        cursor="hand2",
        command=self.toggle_mute,
    )
    self.mute_btn.pack(side="right")

    # Command Detail Text
    self.detail_label = tk.Label(
        self.inner,
        text="Standing by...",
        fg="#e2e8f0",
        bg="#070b14",
        font=("Segoe UI", 9),
        anchor="w",
    )
    self.detail_label.pack(fill="x", pady=(2, 4))

    # Animated Audio Waveform Canvas
    self.canvas = tk.Canvas(
        self.inner, width=382, height=24, bg="#0b1221", highlightthickness=0
    )
    self.canvas.pack(fill="x", pady=(0, 6))
    self.bars = []
    for i in range(32):
      x0 = 6 + i * 11.5
      bar = self.canvas.create_rectangle(
          x0, 10, x0 + 6, 14, fill="#00d4ff", outline=""
      )
      self.bars.append(bar)

    # Bottom Telemetry Bar: CPU | RAM | BAT
    self.metrics_label = tk.Label(
        self.inner,
        text="CPU: --%   |   RAM: --%   |   BAT: --%",
        fg="#94a3b8",
        bg="#070b14",
        font=("Consolas", 8, "bold"),
        anchor="w",
    )
    self.metrics_label.pack(fill="x")

    self._animate_wave()
    self._update_telemetry()
    self.root.update()

  def toggle_mute(self):
    self.muted = not self.muted
    if self.muted:
      self.mute_btn.configure(text="🔇 MUTED", fg="#f87171")
      self.update_status("⏸️ MIC MUTED", "Click MUTED to resume", "#f87171")
    else:
      self.mute_btn.configure(text="🎙️ LIVE", fg="#00ff88")
      self.update_status("🎙️ LISTENING...", "Say 'Jarvis' + command", "#00d4ff")

  def _animate_wave(self):
    try:
      import math
      self.wave_phase += 0.45
      is_active = self.current_color in ["#00ff88", "#facc15"]
      for i, bar in enumerate(self.bars):
        if self.muted:
          amp = 1
        elif is_active:
          amp = int(3 + 8 * abs(math.sin(self.wave_phase + i * 0.45)))
        else:
          amp = int(1 + 3 * abs(math.sin(self.wave_phase * 0.5 + i * 0.3)))
        x0, _, x1, _ = self.canvas.coords(bar)
        self.canvas.coords(bar, x0, 12 - amp, x1, 12 + amp)
        self.canvas.itemconfig(bar, fill=self.current_color)
      self.root.after(70, self._animate_wave)
    except Exception:
      pass

  def _update_telemetry(self):
    try:
      cpu = int(psutil.cpu_percent(interval=None))
      ram = int(psutil.virtual_memory().percent)
      bat = psutil.sensors_battery()
      bat_str = f"{int(bat.percent)}%{'⚡' if bat.power_plugged else ''}" if bat else "AC"
      self.metrics_label.configure(
          text=f"CPU: {cpu:02d}%   |   RAM: {ram:02d}%   |   BAT: {bat_str}"
      )
      self.root.after(2500, self._update_telemetry)
    except Exception:
      pass

  def update_status(self, title, detail="", color="#00d4ff"):
    try:
      self.current_color = color
      self.border.configure(bg=color)
      self.status_label.configure(text=title, fg=color)
      self.detail_label.configure(text=detail[:48])
      self.root.update_idletasks()
      self.root.update()
    except Exception:
      pass

  def close(self):
    try:
      self.root.destroy()
    except Exception:
      pass


hud = None


def speak_with_polly(text, action="speak"):
  if hud and action != "ask_ai":
    hud.update_status("⚡ JARVIS RESPONDING", text, "#00ff88")
  elif hud and action == "ask_ai":
    hud.update_status("🧠 CLOUD AI THINKING", text, "#a855f7")
  try:
    res = requests.post(
        AWS_JARVIS_URL, json={"action": action, "content": text}, timeout=12
    )
    data = res.json()
    
    final_reply = data.get("reply", text)

    if hud:
      hud.update_status("⚡ JARVIS RESPONDING", final_reply, "#00ff88")
    print(f"JARVIS: {final_reply}")

    if "audio_base64" in data:
      audio_bytes = base64.b64decode(data["audio_base64"])
      with tempfile.NamedTemporaryFile(
          delete=False, suffix=".mp3"
      ) as tmp_file:
        tmp_file.write(audio_bytes)
        temp_path = tmp_file.name

      playsound(temp_path)
      os.remove(temp_path)
  except Exception as e:
    print(f"[Audio/Cloud Error]: {e}")


def listen():
  recognizer = sr.Recognizer()
  recognizer.pause_threshold = 1.2
  recognizer.dynamic_energy_threshold = True
  with sr.Microphone() as source:
    if hud and not hud.muted:
      hud.update_status("🎙️ LISTENING...", "Say 'Jarvis' + command", "#00d4ff")
    print("\nListening for 'Jarvis'...")
    recognizer.adjust_for_ambient_noise(source, duration=0.5)
    while True:
      if hud:
        hud.root.update()
        if hud.muted:
          time.sleep(0.15)
          continue
      try:
        audio = recognizer.listen(source, timeout=0.6, phrase_time_limit=8)
        if hud:
          hud.update_status(
              "⚙️ PROCESSING...", "Translating speech...", "#f59e0b"
          )
        command = recognizer.recognize_google(audio).lower()
        print(f"You said: {command}")
        if hud:
          hud.update_status("▶ RUNNING COMMAND", f'"{command}"', "#facc15")
        return command
      except (sr.WaitTimeoutError, sr.UnknownValueError):
        continue
      except sr.RequestError:
        print("Speech recognition network error.")
        return ""


def set_timer_thread(seconds, label):
  time.sleep(seconds)
  speak_with_polly(f"Excuse me, sir. Your timer for {label} is complete.")


def handle_command(command):
  # --- 1. EVERYDAY WINDOWS APPLICATIONS ---
  if "open chrome" in command:
    speak_with_polly("Opening Google Chrome, sir.")
    os.system("start chrome")

  elif "open notepad" in command:
    speak_with_polly("Opening Notepad.")
    os.system("start notepad")

  elif "open command prompt" in command or "open terminal" in command:
    speak_with_polly("Launching Command Prompt.")
    os.system("start cmd")

  elif "open calculator" in command:
    speak_with_polly("Opening Calculator.")
    os.system("start calc")

  elif "open keyboard" in command or "on screen keyboard" in command:
    speak_with_polly("Opening the on-screen keyboard.")
    os.system("start osk")

  elif "open settings" in command:
    speak_with_polly("Opening Windows Settings.")
    os.system("start ms-settings:")

  elif (
      "open file explorer" in command
      or "open files" in command
      or "open my computer" in command
  ):
    speak_with_polly("Opening File Explorer.")
    os.system("start explorer")

  elif "open task manager" in command:
    speak_with_polly("Opening Task Manager.")
    os.system("start taskmgr")

  elif "open vs code" in command or "open visual studio" in command:
    speak_with_polly("Launching Visual Studio Code.")
    os.system("start code")

  elif "open packet tracer" in command:
    speak_with_polly("Launching Cisco Packet Tracer.")
    os.system("start packettracer")

  elif "open word" in command:
    speak_with_polly("Opening Microsoft Word.")
    os.system("start winword")

  elif "open excel" in command:
    speak_with_polly("Opening Microsoft Excel.")
    os.system("start excel")

  # --- 2. EVERYDAY WEBSITES & SOCIAL ---
  elif "open youtube" in command and "play" not in command:
    speak_with_polly("Opening YouTube.")
    webbrowser.open("https://youtube.com")

  elif "open gmail" in command or "open email" in command:
    speak_with_polly("Opening Gmail.")
    webbrowser.open("https://mail.google.com/mail/u/0/#inbox")

  elif "open whatsapp" in command:
    speak_with_polly("Opening WhatsApp application, sir.")
    os.system("start whatsapp:")

  elif "open linkedin" in command:
    speak_with_polly("Opening your LinkedIn feed.")
    webbrowser.open("https://www.linkedin.com/feed/")

  elif "open github" in command:
    speak_with_polly("Opening your GitHub profile.")
    webbrowser.open("https://github.com/DeriJeswin")

  elif "open aws" in command or "open console" in command:
    speak_with_polly("Opening the AWS Management Console.")
    webbrowser.open("https://amazon.com")

  elif "open cloud project" in command:
    speak_with_polly("Launching your serverless contact form on Amazon S3.")
    webbrowser.open(
        "https://deri-serverless-contact-form.s3.ap-southeast-2.amazonaws.com/index.html"
    )
  elif "open my stocks" in command or "open stocks" in command:
    speak_with_polly("Opening your stocks dashboard, sir.")
    webbrowser.open("https://www.angelone.in/trade/tradeone/chart")

  elif "open my sip" in command or "open sip" in command:
    speak_with_polly("Opening your SIP dashboard, sir.")
    webbrowser.open("https://groww.in/mutual-funds/user/dashboard")

  elif "market mode" in command or "trading" in command:
    speak_with_polly(
        "Launching your market workspace with Angel One and Groww, sir."
    )
    webbrowser.open("https://www.angelone.in/trade/tradeone/chart")
    webbrowser.open("https://groww.in/mutual-funds/user/dashboard")

  elif "calculate" in command or (
      "what is" in command
      and any(
          op in command
          for op in [
              "+",
              "-",
              "*",
              "/",
              " x ",
              "plus",
              "minus",
              "times",
              "into",
              "divided by",
          ]
      )
  ):
    expr = (
        command.replace("calculate", "")
        .replace("what is", "")
        .replace("plus", "+")
        .replace("minus", "-")
        .replace("multiplied by", "*")
        .replace("times", "*")
        .replace("into", "*")
        .replace(" x ", "*")
        .replace("divided by", "/")
        .replace("by", "/")
        .strip()
    )
    try:
      if all(c in "0123456789.+-*/() " for c in expr):
        ans = round(eval(expr), 2)
        speak_with_polly(f"The answer is {ans}, sir.")
      else:
        os.system(
            f'start chrome "https://google.com/search?q={urllib.parse.quote(expr)}"'
        )
    except Exception:
      speak_with_polly("I couldn't calculate that expression, sir.")

                                       

  # --- 3. MUSIC & WEB SEARCH ---
  elif "play" in command and ("youtube" in command or "music" in command):
    song = (
        command.replace("play", "")
        .replace("from youtube", "")
        .replace("in youtube", "")
        .replace("on youtube", "")
        .strip()
    )
    if not song or song == "a":
      song = "trending music"
    speak_with_polly(f"Opening Brave and playing {song} on YouTube, sir.")

    # Open Brave directly to the YouTube search results page for your song
    search_url = (
        f"https://youtube.com/results?search_query={urllib.parse.quote(song)}"
    )

    brave_paths = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.join(
            os.path.expanduser("~"),
            r"AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
        ),
    ]
    brave_exe = next((p for p in brave_paths if os.path.exists(p)), None)

    if brave_exe:
      subprocess.Popen([brave_exe, search_url])
    else:
      os.system(f'start brave "{search_url}"')

    # Wait for Brave to load the results, click the center-left video title, and press Enter
    time.sleep(5)
    screen_w, screen_h = pyautogui.size()
    pyautogui.click(int(screen_w * 0.45), int(screen_h * 0.32))
    time.sleep(1.5)
    pyautogui.press("k")


  elif (
      command.startswith("search google about ")
      or command.startswith("search google for ")
      or command.startswith("google ")
  ):
    query = (
        command.replace("search google about ", "", 1)
        .replace("search google for ", "", 1)
        .replace("google ", "", 1)
        .strip()
    )
    speak_with_polly(f"Opening Chrome and searching Google for {query}, sir.")
    search_url = f"https://google.com/search?q={urllib.parse.quote(query)}"
    os.system(f'start chrome "{search_url}"')

  # --- 4. WINDOW, TAB & KEYBOARD AUTOMATION ---
  elif "new tab" in command:
    pyautogui.hotkey("ctrl", "t")
    speak_with_polly("Opened a new tab.")

  elif "close tab" in command:
    pyautogui.hotkey("ctrl", "w")
    speak_with_polly("Closed the tab.")

  elif "close window" in command or "close this" in command:
    pyautogui.hotkey("alt", "f4")
    speak_with_polly("Closed the active window.")

  elif "switch window" in command or "alt tab" in command:
    pyautogui.hotkey("alt", "tab")

  elif "minimize all" in command or "show desktop" in command:
    pyautogui.hotkey("win", "d")
    speak_with_polly("Minimized all windows.")

  elif "copy this" in command or "copy that" in command:
    pyautogui.hotkey("ctrl", "c")
    speak_with_polly("Copied to clipboard.")

  elif "paste this" in command or "paste here" in command:
    pyautogui.hotkey("ctrl", "v")
    speak_with_polly("Pasted.")

  elif "read clipboard" in command or "what did i copy" in command:
    copied_text = pyperclip.paste()
    if copied_text:
      speak_with_polly(f"Your clipboard contains: {copied_text[:200]}")
    else:
      speak_with_polly("Your clipboard is currently empty, sir.")

  elif command.startswith("type "):
    text_to_type = command.replace("type ", "", 1)
    press_enter = False
    if text_to_type.endswith(" and press enter"):
      text_to_type = text_to_type.replace(" and press enter", "")
      press_enter = True
    speak_with_polly("Typing now.")
    time.sleep(0.4)
    pyautogui.write(text_to_type, interval=0.03)
    if press_enter:
      pyautogui.press("enter")

  # --- 5. SCREENSHOT, TIME, DATE, BATTERY & TIMERS ---
  elif "internet speed" in command or "speed test" in command:
    speak_with_polly("Opening Fast.com to test your internet speed, sir.")
    webbrowser.open("https://fast.com")

  elif "flip a coin" in command or "toss a coin" in command:
    import random
    result = random.choice(["Heads", "Tails"])
    speak_with_polly(f"I flipped a coin, and it landed on {result}, sir.")

  elif "screenshot" in command:
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      onedrive_desktop = os.path.join(
          os.path.expanduser("~"), "OneDrive", "Desktop"
      )
      desktop_dir = (
          onedrive_desktop
          if os.path.exists(onedrive_desktop)
          else os.path.join(os.path.expanduser("~"), "Desktop")
      )
      os.makedirs(desktop_dir, exist_ok=True)
      save_path = os.path.join(desktop_dir, f"jarvis_capture_{timestamp}.png")
      pyautogui.screenshot(save_path)
      speak_with_polly("Screenshot captured and saved to your Desktop, sir.")

  elif "what time" in command or "current time" in command:
    now = datetime.now().strftime("%I:%M %p")
    speak_with_polly(f"The current time is {now}, sir.")

  elif (
      "what date" in command
      or "today's date" in command
      or "what day" in command
  ):
    today = datetime.now().strftime("%A, %B %d, %Y")
    speak_with_polly(f"Today is {today}, sir.")

  elif "battery" in command or "power status" in command:
    battery = psutil.sensors_battery()
    if battery:
      status = "plugged in" if battery.power_plugged else "on battery power"
      speak_with_polly(
          f"Your system battery is at {battery.percent} percent and is"
          f" currently {status}."
      )
    else:
      speak_with_polly("Battery metrics are unavailable on this system.")

  elif "set a timer for" in command or "set timer for" in command:
    words = command.split()
    try:
      mins = next(int(w) for w in words if w.isdigit())
      speak_with_polly(f"Timer set for {mins} minutes, sir.")
      threading.Thread(
          target=set_timer_thread,
          args=(mins * 60, f"{mins} minutes"),
          daemon=True,
      ).start()
    except StopIteration:
      speak_with_polly("Please specify how many minutes, sir.")

  # --- 6. SYSTEM AUDIO & POWER CONTROLS ---
  elif "volume up" in command or "increase volume" in command:
    for _ in range(5):
      pyautogui.press("volumeup")
    speak_with_polly("Volume increased.")

  elif "volume down" in command or "decrease volume" in command:
    for _ in range(5):
      pyautogui.press("volumedown")
    speak_with_polly("Volume decreased.")

  elif "mute" in command or "unmute" in command:
    pyautogui.press("volumemute")
    speak_with_polly("Audio toggled.")

  elif "lock my pc" in command or "lock computer" in command:
    speak_with_polly("Locking your workstation now, sir.")
    time.sleep(1)
    ctypes.windll.user32.LockWorkStation()

  elif "sleep my pc" in command or "put computer to sleep" in command:
    speak_with_polly("Putting the computer to sleep.")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

  elif "restart my pc" in command or "restart computer" in command:
    speak_with_polly("Restarting your computer in 5 seconds, sir.")
    os.system("shutdown /r /t 5")

  elif "shutdown my pc" in command or "shut down computer" in command:
    speak_with_polly("Shutting down your computer in 5 seconds, sir.")
    os.system("shutdown /s /t 5")

  elif "cancel shutdown" in command:
    os.system("shutdown /a")
    speak_with_polly("Scheduled shutdown cancelled, sir.")

   # --- 7. AWS DYNAMODB CLOUD MEMORY ---
  elif any(
      phrase in command
      for phrase in ["save note", "save a note", "save my note", "take a note"]
  ):
    note = command
    for phrase in ["save note", "save a note", "save my note", "take a note"]:
      note = note.replace(phrase, "")
    note = note.strip()
    if note:
      speak_with_polly(note, action="save_note")
    else:
      speak_with_polly("What would you like me to save, sir?")

  elif any(
      phrase in command
      for phrase in ["read note", "read notes", "my notes", "check notes"]
  ):
    speak_with_polly("", action="read_notes")

  # --- 8. EXIT JARVIS ---
  elif (
      "go to sleep" in command or "exit" in command or "stop listening" in command
  ):
    speak_with_polly("Powering down all systems. Have a good day, sir.")
    time.sleep(1.5)
    return False

  else:
    speak_with_polly(command, action="ask_ai")


  return True


if __name__ == "__main__":
  hud = JarvisHUD()
  speak_with_polly(
      "All cloud and local systems are online. How may I assist you?"
  )
  wake_words = ["jarvis", "hey jarvis", "service", "travis", "40", "24", "20"]
  direct_triggers = [
      "open ",
      "play ",
      "search ",
      "google ",
      "type ",
      "screenshot",
      "note",
      "notes",
      "volume ",
      "mute",
      "unmute",
      "minimize",
      "lock ",
      "sleep my pc",
      "restart ",
      "shutdown ",
      "cancel shutdown",
      "what time",
      "what date",
      "what day",
      "battery",
      "speed",
      "coin",
      "timer",
      "new tab",
      "close tab",
      "close window",
      "switch window",
      "trading ",
      "copy ",
      "paste ",
      "calculate",
      "what is",
      "clipboard",
      "go to sleep",
  ]
  active = True
  while active:
    heard = listen()
    if not heard:
      continue

    matched_wake = next((w for w in wake_words if w in heard), None)
    if matched_wake:
      clean_cmd = heard.replace(matched_wake, "").strip()
      if clean_cmd:
        active = handle_command(clean_cmd)
      else:
        speak_with_polly("Yes, sir?")
    elif any(trigger in heard for trigger in direct_triggers):
      active = handle_command(heard)

  if hud:
    hud.close()
