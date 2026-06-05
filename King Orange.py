import tkinter as tk
import math
import ctypes
from ctypes import wintypes  
import random

class AvAKingEngine:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        self.root = tk.Tk()
        self.root.title("AvA King Orange")
        
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

        self.key_states = {"h": False, "k": False, "/": False, "+": False, "s": False, "u": False}
        
        # POPRAWIONA SKALA NA 1.7 - Wielki potężny szef!
        self.scale = 1.7
        self.x = self.screen_width // 2
        self.y = self.taskbar_floor
        self.vx = 0
        self.vy = 0
        self.gravity = 0.65
        self.bounce_friction = 0.5
        
        self.state = "WANDER"
        self.anim_time = 0
        
        self.king_mode = False       
        self.shoot_beam = False      
        self.is_flying = False       
        self.obsidian_walls = []     
        
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
        if self.is_key_pressed(0x31) and not self.king_mode: 
            mx, my = self.get_cursor_pos()
            cx, cy = self.x, self.y - (25 * self.scale)
            if (cx - 35 <= mx <= cx + 35) and (cy - 50 <= my <= cy + 50):
                self.root.destroy()
                exit()

    def check_global_keys(self):
        keys = {"h": 0x48, "k": 0x4B, "/": 0xBF, "+": 0xBB, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            
            if key == "k":
                self.shoot_beam = pressed if self.king_mode else False
                continue

            if not pressed: self.key_states[key] = False; continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                
                if key == "h":
                    self.king_mode = not self.king_mode
                    if not self.king_mode:
                        self.shoot_beam = False
                        self.is_flying = False
                        self.obsidian_walls.clear()
                elif key == "+" and self.king_mode:
                    self.is_flying = not self.is_flying
                    if not self.is_flying: self.state = "WANDER"
                elif key == "/" and self.king_mode:
                    self.obsidian_walls.append({"x": mx, "timer": 300})
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
        
        for wall in self.obsidian_walls[:]:
            wall["timer"] -= 1
            if wall["timer"] <= 0:
                self.obsidian_walls.remove(wall)
            else:
                if abs(self.x - wall["x"]) < 16:
                    self.x = wall["x"] + (16 if self.vx < 0 else -16)
                    self.vx = -self.vx * 0.2

        current_floor = self.find_current_floor()
        lpm_pressed = self.is_key_pressed(0x01) 
        cx, cy = self.x, self.y - (25 * self.scale)
        
        if lpm_pressed and (self.state == "GRABBED" or ((cx - 35 <= mx <= cx + 35) and (cy - 50 <= my <= cy + 50))):
            self.state = "GRABBED"
            self.x, self.y = mx, my + 45
            self.vx, self.vy = 0, 0
            self.is_flying = False
        else:
            if self.state == "GRABBED": self.set_state("FALLING_RELEASE")

            if self.shoot_beam:
                self.vx, self.vy = 0, 0  
            elif self.is_flying and self.king_mode:
                if self.anim_time % 90 == 0:
                    speed_mod = 5.0 if self.king_mode else 2.5
                    self.vx = random.choice([-speed_mod, speed_mod, 0])
                    self.vy = random.choice([-1.5, 1.5, 0])
                    if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                if self.y > current_floor - 110:
                    self.vy = -2.0
            else:
                if self.y < current_floor: self.vy += self.gravity
                else:
                    if self.state == "FALLING": self.state = "WANDER"
                    self.vy, self.y = 0, current_floor

                if self.state == "FALLING":
                    self.vx *= 0.99
                elif self.state == "WANDER":
                    if self.anim_time % 120 == 0:
                        speed_mod = 2.8 if self.king_mode else 1.6
                        self.vx = random.choice([-speed_mod, speed_mod, 0])
                        if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                    if self.vx != 0: self.vx *= 0.96

            self.x += self.vx; self.y += self.vy

        if self.x < 35: self.x = 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = 1
        elif self.x > self.screen_width - 35: self.x = self.screen_width - 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = -1
        
        if self.is_flying and self.y < 80: self.y = 80; self.vy = 1.0
        elif not self.is_flying and self.y < 40: self.y = 40; self.vy = -self.vy * self.bounce_friction

        self.canvas.delete("all"); self.anim_time += 1; self.draw_vector_king(); self.root.after(16, self.update_loop)
    def draw_vector_king(self):
        # AUTENTYCZNE KOLORY Z TWÓJGO ZDJĘCIA
        color_king = "#D46909"
        color_crown = "#FFCC00"
        color_staff = "#6C2E3E"
        w = 4
        s = self.scale
        cx, cy = self.x, self.y
        mx, my = self.get_cursor_pos()

        # --- 1. RYSOWANIE PASKÓW OBSYDIANU (Klawisz / - Tylko w King Mode) ---
        if self.king_mode:
            for wall in self.obsidian_walls:
                wx = wall["x"]
                self.canvas.create_line(wx, 0, wx, self.screen_height, fill="#1A0D2E", width=18)
                self.canvas.create_line(wx, 0, wx, self.screen_height, fill="#10051C", width=10)
                for offset in range(-6, 7, 4):
                    if self.anim_time % 10 < 5:
                        self.canvas.create_line(wx + offset, 0, wx + offset, self.screen_height, fill="#4A148C", width=1)

        # --- 2. PRZELICZANIE STRUCTURY KOŚCI STRUPIESZA (Skala 1.7!) ---
        hx, hy = cx, cy - (52 * s)          
        neck_x, neck_y = cx, cy - (42 * s)  
        pelvis_x, pelvis_y = cx, cy - (18 * s) 

        l_foot_x, l_foot_y = cx - (11 * s), cy
        r_foot_x, r_foot_y = cx + (11 * s), cy
        l_hand_x, l_hand_y = cx - (14 * s), cy - (28 * s)
        r_hand_x, r_hand_y = cx + (14 * s), cy - (28 * s)

        # Dopasowanie rąk pod trzymanie kostury po transformacji (H)
        if self.king_mode:
            l_hand_x, l_hand_y = cx - (14 * s), cy - (28 * s)
            r_hand_x, r_hand_y = cx + (16 * s), cy - (32 * s)

        if self.state == "GRABBED":
            wave = self.anim_time * 0.55
            l_foot_x = cx - (8 * s) + math.sin(wave) * 7
            r_foot_x = cx + (8 * s) - math.sin(wave) * 7
            l_foot_y, r_foot_y = cy + (8 * s), cy + (8 * s)
            l_hand_y = cy - (42 * s) + math.cos(wave) * 4
        elif self.shoot_beam and self.king_mode:
            run_dir = 1 if mx > self.x else -1
            r_hand_x = cx + (22 * s) * run_dir
            r_hand_y = cy - (36 * s)
        elif self.is_flying and self.king_mode:
            l_foot_y, r_foot_y = cy - (4 * s), cy - (6 * s)
            r_hand_y = cy - (40 * s)
        elif self.state == "FALLING" or abs(self.vy) > 2:
            l_foot_y, r_foot_y = cy - (6 * s), cy - (4 * s)
        elif self.state == "WANDER" and self.vx != 0:
            wave = self.anim_time * 0.18
            l_foot_x = cx + math.sin(wave) * 9 * s
            r_foot_x = cx - math.sin(wave) * 9 * s

        # --- 3. RENDERING UNIKALNYCH ELEMENTÓW TRANSFORMAJI (Tylko w King Mode pod H) ---
        bx, by = r_hand_x, r_hand_y  # Koordynaty startowe dla lasera z dłoni na wypadek awarii
        
        if self.king_mode:
            # RYSOWANIE I ZAAWANSOWANE CIENIOWANIE KOSTURY (STAFF) ZE ZDJĘCIA
            staff_base_x = r_hand_x - (15 * s) * self.walk_direction
            staff_base_y = r_hand_y + (20 * s)
            staff_top_x = r_hand_x + (25 * s) * self.walk_direction
            staff_top_y = r_hand_y - (25 * s)
            bx, by = staff_top_x, staff_top_y
            
            # Wektorowe cieniowanie kija kostury (Trzy linie obok siebie dające efekt 3D)
            self.canvas.create_line(staff_base_x, staff_base_y, staff_top_x, staff_top_y, fill="#451A24", width=7)
            self.canvas.create_line(staff_base_x, staff_base_y, staff_top_x, staff_top_y, fill=color_staff, width=5)
            self.canvas.create_line(staff_base_x+1*s, staff_base_y-1*s, staff_top_x+1*s, staff_top_y-1*s, fill="#8C3F51", width=1.5)
            
            # Kwadratowe gniazdo Minecraftowe na szczycie
            self.canvas.create_rectangle(bx - 10*s, by - 10*s, bx + 10*s, by + 10*s, outline=color_staff, fill="white", width=3)
            # IKONA MC ZE ZDJĘCIA: Blok ziemi i trawy z Minecrafta
            self.canvas.create_rectangle(bx - 8*s, by - 3*s, bx + 8*s, by + 8*s, fill="#5C4033", outline="") # Ziemia
            self.canvas.create_rectangle(bx - 8*s, by - 8*s, bx + 8*s, by - 3*s, fill="#4CAF50", outline="") # Trawa

        # --- 4. POTĘŻNY STRZAŁ BIAŁEGO STOŻKA Z ZYGZAKOWATYMI PRĄDAMI (Klawisz K) ---
        if self.shoot_beam and self.king_mode:
            dx = mx - bx
            dy = my - by
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                ang = math.atan2(dy, dx)
                perp_ang = ang + math.pi / 2
                
                # Laser bije na odległość 1500px (pełen ekran)
                end_x = bx + math.cos(ang) * 1500
                end_y = by + math.sin(ang) * 1500
                
                spread = 95 * s
                p1_x = end_x + math.cos(perp_ang) * spread
                p1_y = end_y + math.sin(perp_ang) * spread
                p2_x = end_x - math.cos(perp_ang) * spread
                p2_y = end_y - math.sin(perp_ang) * spread
                
                # Rysowanie głównego biało-pomarańczowego stożka energii
                self.canvas.create_polygon(bx, by, p1_x, p1_y, p2_x, p2_y, fill="#FF8000", stipple="gray25")
                self.canvas.create_polygon(bx, by, p1_x, p1_y, p2_x, p2_y, fill="white", outline="#FFCC00", width=2)
                
                # NOWOŚĆ: Generowanie losowych, błyszczących błękitno-białych wyładowań prądu wewnątrz stożka!
                for _ in range(3):
                    cur_x, cur_y = bx, by
                    segments = 8
                    for i in range(1, segments + 1):
                        ratio = i / segments
                        # Punkt centralny segmentu w osi lasera
                        target_x = bx + math.cos(ang) * dist * ratio * 2
                        target_y = by + math.sin(ang) * dist * ratio * 2
                        # Maksymalne rozszerzanie się piorunów wraz z odległością stożka
                        current_spread = spread * ratio * 0.7
                        nx_p = target_x + random.uniform(-current_spread, current_spread) * math.cos(perp_ang)
                        ny_p = target_y + random.uniform(-current_spread, current_spread) * math.sin(perp_ang)
                        
                        # Rysowanie gałęzi prądu elektrycznego
                        self.canvas.create_line(cur_x, cur_y, nx_p, ny_p, fill="#A9E5FC", width=2)
                        self.canvas.create_line(cur_x, cur_y, nx_p, ny_p, fill="white", width=1)
                        cur_x, cur_y = nx_p, ny_p

        # --- 5. RYSOWANIE GEOMETRII SZKIELETU (STYL POMARAŃCZOWEGO STRUPIESZA) ---
        head_r = 8.5 * s
        # Głowa: W 100% PEŁNA W ŚRODKU (fill=color_king) zgodnie z Twoimi wytycznymi!
        self.canvas.create_oval(hx - head_r, hy - head_r, hx + head_r, hy + head_r, outline=color_king, fill=color_king, width=w)
        
        self.canvas.create_line(neck_x, neck_y, pelvis_x, pelvis_y, fill=color_king, width=w)
        self.canvas.create_line(neck_x, neck_y, l_hand_x, l_hand_y, fill=color_king, width=w)
        self.canvas.create_line(neck_x, neck_y, r_hand_x, r_hand_y, fill=color_king, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, l_foot_x, l_foot_y, fill=color_king, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, r_foot_x, r_foot_y, fill=color_king, width=w)

        # --- 6. RYSOWANIE TRÓJRAMIENNEJ ZŁOTEJ KORONY ZE ZDJĘCIA (Tylko w King Mode под H) ---
        if self.king_mode and not self.state == "GRABBED":
            tx, ty = hx, hy - head_r + 2*s
            self.canvas.create_polygon(
                tx - 7*s, ty,
                tx - 8*s, ty - 22*s,   # Lewe ramię
                tx - 2*s, ty - 8*s,
                tx, ty - 25*s,         # Środkowe najwyższe ramię
                tx + 2*s, ty - 8*s,
                tx + 8*s, ty - 22*s,   # Prawe ramię
                tx + 7*s, ty,
                fill=color_crown, outline=""
            )
            # Trzy idealne ozdobne kółeczka na czubkach ramion korony ze zdjęcia
            self.canvas.create_oval(tx - 9.5*s, ty - 24*s, tx - 6.5*s, ty - 21*s, fill=color_crown, outline="")
            self.canvas.create_oval(tx - 1.5*s, ty - 27*s, tx + 1.5*s, ty - 24*s, fill=color_crown, outline="")
            self.canvas.create_oval(tx + 6.5*s, ty - 24*s, tx + 9.5*s, ty - 21*s, fill=color_crown, outline="")

        # --- 7. POŚWIATA ENERGII KOSTEK (Klawisz H) ---
        if self.king_mode and self.anim_time % 10 < 6:
            self.canvas.create_rectangle(bx - 16*s, by - 16*s, bx + 16*s, by + 16*s, outline="#FF6600", width=2)
            self.canvas.create_rectangle(bx - 20*s, by - 20*s, bx + 20*s, by + 20*s, outline="#9C27B0", width=1)

if __name__ == "__main__":
    AvAKingEngine()
