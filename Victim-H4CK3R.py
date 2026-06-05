import tkinter as tk
import math
import ctypes
from ctypes import wintypes  
import random

class AvAVictimEngine:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        self.root = tk.Tk()
        self.root.title("AvA Victim")
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.taskbar_floor = self.screen_height - 40  
        
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        self.trans_color = "#010101"
        self.root.wm_attributes("-transparentcolor", self.trans_color)

        hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
        styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles | 0x20 | 0x80000)

        self.canvas = tk.Canvas(self.root, width=self.screen_width, height=self.screen_height, bg=self.trans_color, highlightthickness=0)
        self.canvas.pack()

        self.key_states = {"6": False, "5": False, "m": False, "n": False, "b": False, "s": False, "u": False}
        
        self.scale = 1.5
        self.x = self.screen_width // 2
        self.y = self.taskbar_floor
        self.vx, self.vy, self.gravity, self.bounce_friction = 0, 0, 0.65, 0.5
        
        self.state = "WANDER"
        self.anim_time = 0
        self.is_hacker_mode = False  
        self.is_flying = False       
        
        self.hacker_cages = []       
        self.hijack_timer = 0        
        
        self.walk_direction = 1
        self.last_mx, self.last_my = 0, 0
        self.mouse_vx, self.mouse_vy = 0, 0
        self.platforms = []
        self.update_loop()
        self.root.mainloop()

    def set_state(self, new_state):
        if new_state == "GRABBED":
            self.state, self.vx, self.vy = "GRABBED", 0, 0
        elif new_state == "FALLING_RELEASE":
            self.state = "FALLING"
            self.vx = self.mouse_vx * 0.85
            self.vy = self.mouse_vy * 0.85

    def is_key_pressed(self, key_code):
        return (ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000) != 0

    def check_laser_collision(self):
        if self.is_key_pressed(0x31): 
            mx, my = self.get_cursor_pos()
            cx, cy = self.x, self.y - (25 * self.scale)
            if (cx - 35 <= mx <= cx + 35) and (cy - 50 <= my <= cy + 50):
                ctypes.windll.user32.ClipCursor(None)
                self.root.destroy()
                exit()

    def check_global_keys(self):
        keys = {"5": 0x35, "6": 0x36, "m": 0x4D, "n": 0x4E, "b": 0x42, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            if not pressed: self.key_states[key] = False; continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                
                if key == "6":
                    self.is_hacker_mode = not self.is_hacker_mode
                    if not self.is_hacker_mode:
                        self.is_flying = False
                        self.hacker_cages.clear()
                        self.hijack_timer = 0
                        ctypes.windll.user32.ClipCursor(None)
                elif key == "5" and self.is_hacker_mode:
                    self.is_flying = not self.is_flying
                elif key == "m" and self.is_hacker_mode:
                    class RECT(ctypes.Structure):
                        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), 
                                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
                    rect = RECT(mx - 90, my - 90, mx + 90, my + 90)
                    ctypes.windll.user32.ClipCursor(ctypes.byref(rect))
                    self.hacker_cages.append({"x": mx, "y": my, "timer": 900})
                elif key == "n" and self.is_hacker_mode:
                    self.hacker_cages.clear()
                    ctypes.windll.user32.ClipCursor(None)
                elif key == "b" and self.is_hacker_mode:
                    self.hijack_timer = 180
                elif key == "s":
                    self.platforms.append((max(0, mx - 175), min(self.screen_width, mx + 175), my))
                elif key == "u":
                    self.platforms.clear()
                    if self.state == "WANDER" and not self.is_flying: self.state = "FALLING"

    def find_current_floor(self):
        best_floor = self.taskbar_floor
        for left, right, top in self.platforms:
            if left <= self.x <= right:
                tolerance = max(6.0, abs(self.vy) + 2)
                if top - 3 <= self.y <= top + tolerance:
                    if top < best_floor: best_floor = top
        return best_floor

    def get_cursor_pos(self):
        class POINT(ctypes.Structure): _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT(); ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def update_loop(self):
        self.check_global_keys(); self.check_laser_collision()
        mx, my = self.get_cursor_pos()
        self.mouse_vx, self.mouse_vy = mx - self.last_mx, my - self.last_my
        self.last_mx, self.last_my = mx, my
        
        if self.hijack_timer > 0 and self.is_hacker_mode:
            self.hijack_timer -= 1
            ctypes.windll.user32.SetCursorPos(mx + random.randint(-12, 12), my + random.randint(-12, 12))
        
        # --- OSTATECZNA POPRAWKA TIMERA: Klatka znika z tablicy i ekranu po 15 sekundach ---
        if self.is_hacker_mode:
            active_cages = False
            for cage in self.hacker_cages[:]:
                cage["timer"] -= 1
                if cage["timer"] <= 0:
                    self.hacker_cages.remove(cage)
                else:
                    active_cages = True
            
            if not active_cages and self.anim_time % 5 == 0:
                ctypes.windll.user32.ClipCursor(None)

        floor = self.find_current_floor()
        lpm_pressed = self.is_key_pressed(0x01) 
        cx, cy = self.x, self.y - (25 * self.scale)
        
        if lpm_pressed and (self.state == "GRABBED" or ((cx - 35 <= mx <= cx + 35) and (cy - 50 <= my <= cy + 50))):
            self.state = "GRABBED"
            self.x, self.y = mx, my + 45
            self.vx, self.vy = 0, 0
            self.is_flying = False
        else:
            if self.state == "GRABBED": self.set_state("FALLING_RELEASE")

            if self.is_flying and self.is_hacker_mode:
                if self.anim_time % 90 == 0:
                    speed_mod = 5.0 if self.is_hacker_mode else 2.5
                    self.vx = random.choice([-speed_mod, speed_mod, 0])
                    self.vy = random.choice([-1.5, 1.5, 0])
                    if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                if self.y > floor - 110: self.vy = -2.0
            else:
                if self.y < floor: self.vy += self.gravity
                else:
                    if self.state == "FALLING": self.state = "WANDER"
                    self.vy, self.y = 0, floor

                if self.state == "FALLING":
                    self.vx *= 0.99
                elif self.state == "WANDER":
                    if self.anim_time % 120 == 0:
                        speed_mod = 3.5 if self.is_hacker_mode else 1.8
                        self.vx = random.choice([-speed_mod, speed_mod, 0])
                        if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                    if self.vx != 0: self.vx *= 0.96

            self.x += self.vx; self.y += self.vy

        if self.x < 35: self.x = 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = 1
        elif self.x > self.screen_width - 35: self.x = self.screen_width - 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = -1
        if self.is_flying and self.y < 80: self.y = 80; self.vy = 1.0
        elif not self.is_flying and self.y < 40: self.y = 40; self.vy = -self.vy * self.bounce_friction

        self.canvas.delete("all"); self.anim_time += 1; self.draw_vector_victim(); self.root.after(16, self.update_loop)
    def draw_vector_victim(self):
        color_grey = "#4F4F4F"
        w = 4
        s = self.scale
        cx, cy = self.x, self.y
        mx, my = self.get_cursor_pos()

        # Pozycje lokalne stawów (przeliczane globalnie na ekran monitora)
        hx, hy = cx, cy - (52 * s)          
        neck_x, neck_y = cx, cy - (42 * s)  
        pelvis_x, pelvis_y = cx, cy - (18 * s) 

        l_foot_x, l_foot_y = cx - (11 * s), cy
        r_foot_x, r_foot_y = cx + (11 * s), cy
        l_hand_x, l_hand_y = cx - (14 * s), cy - (28 * s)
        r_hand_x, r_hand_y = cx + (14 * s), cy - (28 * s)

        # Dopasowanie klatek pod animacje i lot (Ręce naturalnie w dole w obu stanach!)
        if self.state == "GRABBED":
            wave = self.anim_time * 0.55
            l_foot_x = cx - (8 * s) + math.sin(wave) * 7
            r_foot_x = cx + (8 * s) - math.sin(wave) * 7
            l_foot_y, r_foot_y = cy + (8 * s), cy + (8 * s)
            l_hand_y = cy - (42 * s) + math.cos(wave) * 4
            r_hand_y = cy - (42 * s) - math.sin(wave) * 4
        elif self.is_flying and self.is_hacker_mode:
            l_foot_y, r_foot_y = cy - (2 * s), cy - (2 * s)
        elif self.state == "FALLING" or abs(self.vy) > 2:
            l_foot_y, r_foot_y = cy - (6 * s), cy - (4 * s)
            l_hand_y, r_hand_y = cy - (42 * s), cy - (42 * s)
        elif self.state == "WANDER" and self.vx != 0:
            wave = self.anim_time * 0.18
            l_foot_x = cx + math.sin(wave) * 9 * s
            r_foot_x = cx - math.sin(wave) * 9 * s

        # --- 1. RYSOWANIE HAKERSKICH KLATEK WIĘZIENNYCH (Znikają całkowicie po wykasowaniu z tablicy) ---
        if self.is_hacker_mode:
            for cage in self.hacker_cages:
                kx, ky = cage["x"], cage["y"]
                # Rysowanie neonowych, błękitnych ścian klatki
                self.canvas.create_rectangle(kx - 90, ky - 90, kx + 90, ky + 90, outline="#00FFFF", width=4)
                self.canvas.create_rectangle(kx - 86, ky - 86, kx + 86, ky + 86, outline="#010101", fill="", width=2)
                
                # Wektorowe kraty hakerskie blokujące kursor myszy gracza
                for offset in range(-60, 90, 30):
                    self.canvas.create_line(kx + offset, ky - 90, kx + offset, ky + 90, fill="#00FFFF", width=2)

        # --- 2. RYSOWANIE EFEKTÓW MOUSE HIJACK (Klawisz B) ---
        if self.hijack_timer > 0 and self.is_hacker_mode:
            for _ in range(3):
                tx = mx + random.randint(-40, 40)
                ty = my + random.randint(-40, 40)
                h_char = random.choice(["0", "1", "X", "ERROR", "#", "!", "FAIL"])
                self.canvas.create_text(tx, ty, text=h_char, fill="#FF0000", font=("Courier", random.randint(8, 11), "bold"))

        # --- 3. EFEKTY GRAFICZNE AWAKENING H4CK3R MODE (Klawisz 6) ---
        if self.is_hacker_mode:
            aura_pulse = math.sin(self.anim_time * 0.2) * 5 * s
            head_r_a = (8.5 * s) + 4 * s + aura_pulse
            self.canvas.create_oval(hx - head_r_a, hy - head_r_a, hx + head_r_a, hy + head_r_a, outline="#00FFFF", width=2)
            self.canvas.create_line(neck_x, neck_y - 4*s, pelvis_x, pelvis_y + 4*s, fill="#00FFFF", width=w+4)
            self.canvas.create_line(neck_x, neck_y, l_hand_x, l_hand_y, fill="#00FFFF", width=w+2)
            self.canvas.create_line(neck_x, neck_y, r_hand_x, r_hand_y, fill="#00FFFF", width=w+2)
            self.canvas.create_line(pelvis_x, pelvis_y, l_foot_x, l_foot_y, fill="#00FFFF", width=w+2)
            self.canvas.create_line(pelvis_x, pelvis_y, r_foot_x, r_foot_y, fill="#00FFFF", width=w+2)

            for start_x, start_y in [(l_hand_x, l_hand_y), (r_hand_x, r_hand_y), (l_foot_x, l_foot_y), (r_foot_x, r_foot_y)]:
                if random.random() < 0.4:
                    lx, ly = start_x, start_y
                    for _ in range(3):
                        nx_p = lx + random.randint(-15, 15)
                        ny_p = ly + random.randint(-10, 15)
                        self.canvas.create_line(lx, ly, nx_p, ny_p, fill="#A9E5FC", width=2)
                        lx, ly = nx_p, ny_p

            if random.random() < 0.5:
                px = cx + random.randint(-40, 40)
                py = cy - random.randint(10, 80)
                p_size = random.randint(3, 6)
                self.canvas.create_rectangle(px, py, px + p_size, py + p_size, fill="#00FFFF", outline="")

        # --- 4. RYSOWANIE GEOMETRII SZKIELETU (STYL SZAREGO TSC Z PUSTĄ GŁOWĄ) ---
        head_r = 8.5 * s
        self.canvas.create_oval(hx - head_r, hy - head_r, hx + head_r, hy + head_r, outline=color_grey, fill="#010101", width=w)
        self.canvas.create_line(neck_x, neck_y, pelvis_x, pelvis_y, fill=color_grey, width=w)
        self.canvas.create_line(neck_x, neck_y, l_hand_x, l_hand_y, fill=color_grey, width=w)
        self.canvas.create_line(neck_x, neck_y, r_hand_x, r_hand_y, fill=color_grey, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, l_foot_x, l_foot_y, fill=color_grey, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, r_foot_x, r_foot_y, fill=color_grey, width=w)

        # --- 5. BŁĘKITNY MONOKL CYBER-OKULARU (Klawisz 6) ---
        if self.is_hacker_mode:
            self.canvas.create_rectangle(hx + 1*s, hy - 4*s, hx + 8*s, hy + 2*s, outline="#00FFFF", fill="#010101", width=2)
            self.canvas.create_line(hx + 4*s, hy - 1*s, hx + 12*s, hy - 1*s, fill="#00FFFF", width=1.5)

if __name__ == "__main__":
    AvAVictimEngine()
