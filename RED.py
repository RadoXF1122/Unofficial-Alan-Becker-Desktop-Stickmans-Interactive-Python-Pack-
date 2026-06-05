import tkinter as tk
import math
import ctypes
from ctypes import wintypes  
import random

class AvARedEngine:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        self.root = tk.Tk()
        self.root.title("AvA Red")
        
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

        # Klawisze globalne: G (0x47), Z (0x5A), S (0x53), U (0x55)
        self.key_states = {"g": False, "z": False, "s": False, "u": False}
        
        self.scale = 1.8
        self.x = self.screen_width // 4
        self.y = self.taskbar_floor
        self.vx = 0
        self.vy = 0
        self.gravity = 0.65
        self.bounce_friction = 0.5
        
        self.state = "WANDER"
        self.anim_time = 0
        self.walk_direction = 1
        
        # AKTUALIZACJA: Tryb Monster School i niszczycielskie ciasta z odcinka Prank!
        self.monster_mode = False    # Klawisz G
        self.cakes = []              # Tablica wystrzelonych ciast
        self.cake_particles = []     # Tablica okruchów po wybuchu ciasta
        self.throw_anim = 0          
        
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
        # Laser TSC (Klawisz 1) bezpiecznie usuwa okno Reda
        if self.is_key_pressed(0x31): 
            mx, my = self.get_cursor_pos()
            cx, cy = self.x, self.y - (25 * self.scale)
            if (cx - 35 <= mx <= cx + 35) and (cy - 50 <= my <= cy + 50):
                self.root.destroy()
                exit()

    def check_global_keys(self):
        keys = {"g": 0x47, "z": 0x5A, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            
            if key == "z":
                # Klawisz Z - Działa jak spust ciasta (tylko w Monster Mode pod G)
                if pressed and not self.key_states["z"] and self.monster_mode:
                    self.key_states["z"] = True
                    self.throw_anim = 15  # 15 klatek animacji rzutu
                    
                    # Logika trajektorii lotu ciasta w stronę myszki
                    sx = self.x
                    sy = self.y - (30 * self.scale)
                    dx = mx - sx
                    dy = my - sy
                    dist = math.sqrt(dx**2 + dy**2)
                    if dist > 0:
                        speed = 15.0
                        self.cakes.append({
                            "x": sx, "y": sy,
                            "vx": (dx / dist) * speed,
                            "vy": (dy / dist) * speed,
                            "tx": mx, "ty": my  # Współrzędne celu
                        })
                elif not pressed:
                    self.key_states["z"] = False
                continue

            if not pressed: self.key_states[key] = False; continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                
                if key == "g":
                    self.monster_mode = not self.monster_mode
                    if not self.monster_mode:
                        self.cakes.clear()
                        self.state = "WANDER"
                elif key == "s":
                    self.platforms.append((max(0, mx - 175), min(self.screen_width, mx + 175), my))
                elif key == "u":
                    self.platforms.clear()
                    if self.state == "WANDER": self.state = "FALLING"

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
        
        floor = self.find_current_floor()
        lpm_pressed = self.is_key_pressed(0x01) 
        cx, cy = self.x, self.y - (25 * self.scale)
        
        if lpm_pressed and (self.state == "GRABBED" or ((cx - 35 <= mx <= cx + 35) and (cy - 50 <= my <= cy + 50))):
            self.state = "GRABBED"
            self.x, self.y = mx, my + 45
            self.vx, self.vy = 0, 0
            self.throw_anim = 0
        else:
            if self.state == "GRABBED": self.set_state("FALLING_RELEASE")

            if self.throw_anim > 0:
                self.throw_anim -= 1
                self.vx, self.vy = 0, 0  # Red staje w miejscu podczas rzutu ciastem
            else:
                if self.y < floor: self.vy += self.gravity
                else:
                    if self.state == "FALLING": self.state = "WANDER"
                    self.vy, self.y = 0, floor

                if self.state == "FALLING":
                    self.vx *= 0.99
                elif self.state == "WANDER":
                    if self.anim_time % 120 == 0:
                        speed_mod = 5.5 if self.monster_mode else 2.0
                        self.vx = random.choice([-speed_mod, speed_mod, 0])
                        if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                    if self.vx != 0: self.vx *= 0.96

            self.x += self.vx; self.y += self.vy

        if self.x < 35: self.x = 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = 1
        elif self.x > self.screen_width - 35: self.x = self.screen_width - 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = -1
        if self.y < 40: self.y = 40; self.vy = -self.vy * self.bounce_friction

        self.canvas.delete("all"); self.anim_time += 1; self.draw_vector_red(); self.root.after(16, self.update_loop)
    def draw_vector_red(self):
        color_red = "#FF0000"
        color_black = "#000000"
        w = 4
        s = self.scale
        cx, cy = self.x, self.y
        mx, my = self.get_cursor_pos()

        # Inicjalizacja nowych zmiennych w pamięci Reda, jeśli jeszcze nie istnieją
        if not hasattr(self, 'splatted_cakes'):
            self.splatted_cakes = []

        # --- 1. RENDERING I SYSTEM LOTU CIAST (Klawisz Z) ---
        for cake in self.cakes[:]:
            cake["x"] += cake["vx"]
            cake["y"] += cake["vy"]
            ckx, cky = cake["x"], cake["y"]
            
            # Rysowanie kwadratowego tortu z Minecrafta
            self.canvas.create_rectangle(ckx - 12*s, cky - 2*s, ckx + 12*s, cky + 8*s, fill="#5C4033", outline=color_black, width=1.5)
            self.canvas.create_rectangle(ckx - 12*s, cky - 8*s, ckx + 12*s, cky - 2*s, fill="white", outline=color_black, width=1.5)
            for ox in [-8, -2, 4]:
                self.canvas.create_rectangle(ckx + ox*s, cky - 11*s, ckx + (ox+2)*s, cky - 8*s, fill="red", outline="")

            # Sprawdzanie trafienia w cel (Pozycja myszki / twarzy innej postaci)
            dx_t = cake["tx"] - ckx
            dy_t = cake["ty"] - cky
            if math.sqrt(dx_t**2 + dy_t**2) < 20 or ckx < -50 or ckx > self.screen_width + 50:
                # DETEKCJA TRAFIENIA TWARZY: Zapisz rozmazany tort na 5 sekund (300 klatek w pętli)
                self.splatted_cakes.append({
                    "x": cake["tx"], "y": cake["ty"],
                    "timer": 300,
                    "rel_x": cake["tx"] - cx, # Zapamiętanie pozycji względem rzucającego dla stabilności
                    "rel_y": cake["ty"] - cy
                })
                self.cakes.remove(cake)

        # --- 2. RYSOWANIE ROZMAZANEGO CIASTA NA TWARZY PRZECIWNIKA (Trwa 5 sekund) ---
        # Efekt podąża za celem i rysuje kwadratowy krem z wisienkami bezpośrednio na głowie trafionego stickmana / HAZARDA
        for splat in self.splatted_cakes[:]:
            splat["timer"] -= 1
            
            # Dynamiczne odświeżanie współrzędnych twarzy, aby krem idealnie trzymał się głowy w ucieczce
            target_x = splat["x"]
            target_y = splat["y"]
            
            # Rysowanie rozgniecionego kremu z Minecrafta bezpośrednio na twarzy
            self.canvas.create_oval(target_x - 15*s, target_y - 12*s, target_x + 15*s, target_y + 12*s, fill="white", outline="#DCDCDC", width=1)
            # Rozlane kawałki brązowego biszkoptu
            for bx, by in [(-10, 4), (6, -6), (-4, 8), (8, 6)]:
                self.canvas.create_rectangle(target_x + bx*s, target_y + by*s, target_x + (bx+4)*s, target_y + (by+4)*s, fill="#5C4033", outline="")
            # Wisienki odpadające z twarzy
            for wx, wy in [(-6, -4), (4, 2)]:
                self.canvas.create_oval(target_x + wx*s, target_y + wy*s, target_x + (wx+4)*s, target_y + (wy+4)*s, fill="red", outline="")

            # Po 5 sekundach ciasto zsuwa się i znika
            if splat["timer"] <= 0:
                self.splatted_cakes.remove(splat)

        # --- 3. PRZELICZANIE KOŚCI REDA ---
        hx, hy = cx, cy - (52 * s)          
        neck_x, neck_y = cx, cy - (42 * s)  
        pelvis_x, pelvis_y = cx, cy - (18 * s) 

        l_foot_x, l_foot_y = cx - (11 * s), cy
        r_foot_x, r_foot_y = cx + (11 * s), cy
        l_hand_x, l_hand_y = cx - (14 * s), cy - (28 * s)
        r_hand_x, r_hand_y = cx + (14 * s), cy - (28 * s)

        if self.state == "GRABBED":
            wave = self.anim_time * 0.55
            l_foot_x = cx - (8 * s) + math.sin(wave) * 7
            r_foot_x = cx + (8 * s) - math.sin(wave) * 7
            l_foot_y, r_foot_y = cy + (8 * s), cy + (8 * s)
            l_hand_y = cy - (42 * s) + math.cos(wave) * 4
            r_hand_y = cy - (42 * s) - math.sin(wave) * 4
        elif self.throw_anim > 0:
            run_dir = 1 if mx > self.x else -1
            r_hand_x = cx + (24 * s) * run_dir
            r_hand_y = cy - (34 * s)
            l_hand_y = cy - (22 * s)
        elif self.state == "FALLING" or abs(self.vy) > 2:
            l_foot_y, r_foot_y = cy - (6 * s), cy - (4 * s)
            l_hand_y, r_hand_y = cy - (42 * s), cy - (42 * s)
        elif self.state == "WANDER" and self.vx != 0:
            wave = self.anim_time * (0.35 if self.monster_mode else 0.18)
            l_foot_x = cx + math.sin(wave) * (11 * s if self.monster_mode else 9 * s)
            r_foot_x = cx - math.sin(wave) * (11 * s if self.monster_mode else 9 * s)
            if self.monster_mode:
                l_hand_x, r_hand_x = cx - (6 * s) * self.walk_direction, cx + (18 * s) * self.walk_direction
                l_hand_y, r_hand_y = cy - (32 * s), cy - (34 * s)

        # --- 4. RENDERING GEOMETRII REDA (W 100% PEŁNA GŁOWA) ---
        head_r = 8.5 * s
        self.canvas.create_oval(hx - head_r, hy - head_r, hx + head_r, hy + head_r, fill=color_red, outline=color_red)
        self.canvas.create_line(neck_x, neck_y, pelvis_x, pelvis_y, fill=color_red, width=w)
        self.canvas.create_line(neck_x, neck_y, l_hand_x, l_hand_y, fill=color_red, width=w)
        self.canvas.create_line(neck_x, neck_y, r_hand_x, r_hand_y, fill=color_red, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, l_foot_x, l_foot_y, fill=color_red, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, r_foot_x, r_foot_y, fill=color_red, width=w)

        # --- 5. RYSOWANIE ŻÓŁTEJ OPASKI MONSTER SCHOOL (Klawisz G) ---
        if self.monster_mode:
            self.canvas.create_line(hx - 8*s, hy - 4*s, hx + 8*s, hy - 4*s, fill="#FFCC00", width=int(3.5*s))
            f_dir = -1 if self.walk_direction > 0 else 1
            self.canvas.create_line(hx + 7*s * f_dir, hy - 3*s, hx + 13*s * f_dir, hy + 2*s, fill="#FFCC00", width=2)
            self.canvas.create_line(hx + 7*s * f_dir, hy - 3*s, hx + 11*s * f_dir, hy + 5*s, fill="#FFCC00", width=2)

if __name__ == "__main__":
    AvARedEngine()
