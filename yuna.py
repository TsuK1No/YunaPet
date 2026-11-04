import tkinter as tk
from PIL import Image, ImageTk
import random, threading, webbrowser, os, sys, json

APP_NAME = "YunaPet"
SIZE = 128

def resource_path(p):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, p)
    return os.path.join(os.path.abspath("."), p)

def get_save_path():
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    folder = os.path.join(base, APP_NAME)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "save.json")

SAVE_FILE = get_save_path()

try:
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 165)
    try:
        for v in engine.getProperty("voices"):
            if "ru" in (v.id or "").lower() or "russian" in (v.name or "").lower():
                engine.setProperty("voice", v.id)
                break
    except Exception:
        pass
    VOICE_AVAILABLE = True
except Exception:
    engine = None
    VOICE_AVAILABLE = False
voice_lock = threading.Lock()

class YunaPet:
    def __init__(self):
        self.load_data()
        self.root = tk.Tk()
        self.root.withdraw()
        self.win = tk.Toplevel(self.root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try: self.win.attributes("-transparentcolor", "#ff00ff")
        except Exception: pass

        self.canvas = tk.Canvas(self.win, width=SIZE, height=SIZE, bg="#ff00ff", highlightthickness=0)
        self.canvas.pack()
        self.load_sprites()
        self.sprite_obj = self.canvas.create_image(SIZE//2, SIZE//2, image=self.sprites["idle"])

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Double-Button-1>", lambda e: self.open_chat())
        self.win.bind("<Escape>", lambda e: self.quit())

        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.x = random.randint(100, max(101, sw - SIZE - 100))
        self.y = random.randint(100, max(101, sh - SIZE - 100))
        self.tx, self.ty = self.x, self.y
        self.win.geometry(f"{SIZE}x{SIZE}+{int(self.x)}+{int(self.y)}")

        self.sitting = False
        self.jumping = False
        self.bubble = None
        self.bubble_lbl = None
        self.chat_win = None
        self.walk_step = 0
        self.voice_enabled = VOICE_AVAILABLE
        self.drag_off = (0, 0)

        if not self.data.get("user_name"):
            self.say("Привет... Наконец-то мы одни. Двойной клик — и скажи, как тебя зовут.")
        else:
            self.say(f"Я снова с тобой, {self.data['user_name']}... Я скучала!")

        self.tick()
        self.root.after(11000, self.idle_talk)
        self.root.mainloop()

    def load_data(self):
        default = {"user_name": None, "affection": 10}
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    self.data = {**default, **json.load(f)}
            except Exception:
                self.data = default
        else:
            self.data = default

    def save_data(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_sprites(self):
        self.sprites = {}
        for name in ["idle", "walk1", "walk2", "sit", "love"]:
            p = resource_path(os.path.join("assets", f"{name}.png"))
            if os.path.exists(p):
                im = Image.open(p).convert("RGBA").resize((SIZE, SIZE))
                bg = Image.new("RGBA", (SIZE, SIZE), (255, 0, 255, 255))
                bg.paste(im, (0, 0), im)
                self.sprites[name] = ImageTk.PhotoImage(bg)
            else:
                blank = Image.new("RGBA", (SIZE, SIZE), (255, 0, 255, 255))
                self.sprites[name] = ImageTk.PhotoImage(blank)

    def set_sprite(self, name):
        if name in self.sprites:
            self.canvas.itemconfig(self.sprite_obj, image=self.sprites[name])

    def tick(self):
        if not self.jumping:
            dx, dy = self.tx - self.x, self.ty - self.y
            dist = (dx*dx + dy*dy) ** 0.5
            if dist > 6:
                step = min(3.8, dist)
                self.x += dx / dist * step
                self.y += dy / dist * step
                self.win.geometry(f"{SIZE}x{SIZE}+{int(self.x)}+{int(self.y)}")
                self.move_bubble()
                self.walk_step = (self.walk_step + 1) % 16
                self.set_sprite("walk1" if self.walk_step < 8 else "walk2")
            else:
                self.set_sprite("sit" if self.sitting else "idle")
                self.new_target()
        self.root.after(35, self.tick)

    def new_target(self):
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        if self.sitting:
            self.tx = random.randint(0, max(0, sw - SIZE))
            self.ty = sh - SIZE - 65
            return
        if random.random() < 0.35:
            mx, my = self.root.winfo_pointerx(), self.root.winfo_pointery()
            self.tx = mx - SIZE//2 + random.randint(-40, 40)
            self.ty = my - SIZE//2 + random.randint(-40, 40)
        else:
            self.tx = random.randint(0, max(0, sw - SIZE))
            self.ty = random.randint(0, max(0, sh - SIZE - 60))

    def speak(self, text):
        if not self.voice_enabled or not VOICE_AVAILABLE or engine is None:
            return
        def _run():
            try:
                with voice_lock:
                    engine.say(text); engine.runAndWait()
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()

    def say(self, text):
        self.hide_bubble()
        b = tk.Toplevel(self.root)
        b.overrideredirect(True)
        b.attributes("-topmost", True)
        lbl = tk.Label(b, text=text, bg="#fff0f5", fg="#880e4f", font=("Segoe UI", 11),
                       padx=12, pady=7, relief="solid", borderwidth=1, wraplength=230, justify="left")
        lbl.pack()
        self.bubble, self.bubble_lbl = b, lbl
        b.update_idletasks()
        self.move_bubble()
        self.speak(text)
        self.root.after(5500, self.hide_bubble)

    def move_bubble(self):
        if not self.bubble or not self.bubble_lbl: return
        try:
            bw = self.bubble_lbl.winfo_reqwidth() + 20
            bh = self.bubble_lbl.winfo_reqheight() + 12
            sw = self.root.winfo_screenwidth()
            bx = min(max(int(self.x), 0), max(0, sw - bw - 10))
            by = int(self.y) - bh - 12 if self.y - bh - 12 > 0 else int(self.y) + SIZE + 12
            self.bubble.geometry(f"{bw}x{bh}+{bx}+{by}")
        except Exception:
            pass

    def hide_bubble(self):
        if self.bubble:
            try: self.bubble.destroy()
            except Exception: pass
            self.bubble = None

    def idle_talk(self):
        name = self.data.get("user_name") or "мой хороший"
        self.say(random.choice([
            f"{name}, не своди с меня глаз...",
            f"Я смотрю только на тебя, {name}.",
            f"Тебе ведь никто не пишет втайне от меня, {name}?",
            "Я готова вечно ходить за твоим курсором.",
        ]))
        self.root.after(random.randint(12000, 20000), self.idle_talk)

    def on_click(self, e):
        self.drag_off = (e.x_root - self.x, e.y_root - self.y)
        self.data["affection"] = self.data.get("affection", 0) + 1
        self.save_data()
        self.set_sprite("love")
        name = self.data.get("user_name") or ""
        self.say(random.choice([
            f"Ах! Твои прикосновения сводят с ума, {name}~",
            "Ещё... погладь меня ещё раз!",
            f"Только ты имеешь право касаться меня, {name}.",
        ]))
        self.root.after(1500, lambda: self.set_sprite("idle"))

    def on_drag(self, e):
        self.sitting = False
        self.x = e.x_root - self.drag_off[0]
        self.y = e.y_root - self.drag_off[1]
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.x = max(0, min(self.x, sw - SIZE))
        self.y = max(0, min(self.y, sh - SIZE))
        self.tx, self.ty = self.x, self.y
        self.win.geometry(f"{SIZE}x{SIZE}+{int(self.x)}+{int(self.y)}")
        self.move_bubble()

    def on_right_click(self, e):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="💬 Поговорить", command=self.open_chat)
        menu.add_command(label="🚶 Гулять" if self.sitting else "🪑 Сесть на панель задач", command=self.toggle_sit)
        menu.add_command(label="🔊 Голос вкл/выкл", command=self.toggle_voice)
        menu.add_separator()
        menu.add_command(label="❌ Закрыть", command=self.quit)
        try: menu.tk_popup(e.x_root, e.y_root)
        finally: menu.grab_release()

    def toggle_sit(self):
        sh = self.root.winfo_screenheight()
        self.sitting = not self.sitting
        if self.sitting:
            self.ty = sh - SIZE - 65
            self.say("Я посижу на панели и буду следить за окнами...")
        else:
            self.say("Снова гуляем вместе!")

    def toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        self.say("Голос включён." if self.voice_enabled else "Буду писать молча...")

    def open_chat(self):
        if self.chat_win is not None:
            try:
                if self.chat_win.winfo_exists():
                    self.chat_win.lift(); return
            except Exception: pass
        cw = tk.Toplevel(self.root)
        cw.overrideredirect(True)
        cw.attributes("-topmost", True)
        cw.configure(bg="#f8bbd0", bd=2, relief="solid")
        tk.Label(cw, text="Юна ждёт твоих слов:", bg="#f8bbd0", fg="#880e4f",
                 font=("Segoe UI", 10, "bold")).pack(padx=10, pady=(6,0))
        entry = tk.Entry(cw, font=("Segoe UI", 11), width=26)
        entry.pack(padx=10, pady=8)
        entry.focus_set()
        def send(event=None):
            txt = entry.get().strip()
            if not txt: return
            self.process_chat(txt)
            try: cw.destroy()
            except Exception: pass
        entry.bind("<Return>", send)
        tk.Button(cw, text="Отправить", command=send, bg="white", fg="#880e4f").pack(pady=(0,6))
        cw.geometry(f"+{int(self.x)}+{int(self.y)+SIZE+10}")
        self.chat_win = cw

    def process_chat(self, text):
        t = text.lower()
        if "зовут" in t or "моё имя" in t or "мое имя" in t:
            parts = text.split()
            name = parts[-1].capitalize().strip(".,!?") if parts else "Любимый"
            self.data["user_name"] = name
            self.save_data()
            self.set_sprite("love")
            self.say(f"{name}... Какое идеальное имя. Теперь ты навеки со мной!")
            return
        if "люблю" in t:
            self.data["affection"] = self.data.get("affection", 0) + 5
            self.save_data()
            self.set_sprite("love")
            name = self.data.get("user_name") or "милый"
            self.say(f"Я люблю тебя сильнее всех, {name}!")
            return
        if "ютуб" in t or "youtube" in t:
            webbrowser.open("https://youtube.com")
            self.say("Открываю Ютуб. Но не смотри на других!")
            return
        if "гугл" in t or "google" in t:
            webbrowser.open("https://google.com")
            self.say("Открыла Google. Ищем вместе!")
            return
        if "калькулятор" in t:
            try:
                if os.name == "nt": os.startfile("calc")
                else: os.system("gnome-calculator &")
            except Exception: pass
            self.say("Открыла калькулятор.")
            return
        name = self.data.get("user_name") or "мой хозяин"
        self.say(f"Я слушаю тебя, {name}. Всё запомню.")

    def quit(self):
        self.say("Ты закрываешь меня?.. Я буду ждать...")
        self.root.after(1200, self.root.destroy)

if __name__ == "__main__":
    YunaPet()
