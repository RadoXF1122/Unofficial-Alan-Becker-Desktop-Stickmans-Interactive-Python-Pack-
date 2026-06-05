import tkinter as tk
import math
import ctypes
from ctypes import wintypes  
import random
import pygame

class AvATSCEngine:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        pygame.mixer.init()
        
        self.root = tk.Tk()
        self.root.title("AvA TSC")
        
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

        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.key_states = {"f": False, "1": False, "2": False, "3": False, "s": False, "u": False}
        
        self.base_scale = 1.9
        self.scale = self.base_scale
        self.x = self.screen_width // 2
        self.y = self.taskbar_floor
        self.vx = 0
        self.vy = 0
        self.gravity = 0.65
        self.bounce_friction = 0.5
        
        self.state = "WANDER"
        self.anim_time = 0
        
        self.awakened = False        
        self.shoot_laser = False     
        self.super_flight = False    
        
        self.walk_direction = 1
        self.last_mx, self.last_my = 0, 0
        self.mouse_vx, self.mouse_vy = 0, 0
        self.platforms = []
        
        self.laser_sound = None
        try:
            self.laser_sound = pygame.mixer.Sound("sounds/laser.wav")
            self.laser_sound.set_volume(1.0)
        except:
            pass

        self.update_loop()
        self.root.mainloop()

    def on_canvas_click(self, event):
        if (self.screen_width - 50 <= event.x <= self.screen_width - 10) and (10 <= event.y <= 40):
            if self.laser_sound: pygame.mixer.stop()
            self.root.destroy()
            exit()

    def set_state(self, new_state):
        if new_state == "GRABBED":
            self.state = "GRABBED"
            self.vx, self.vy = 0, 0
            if self.laser_sound: pygame.mixer.stop()
        elif new_state == "FALLING_RELEASE":
            self.state = "FALLING"
            self.vx = self.mouse_vx * 0.85
            self.vy = self.mouse_vy * 0.85

    def is_key_pressed(self, key_code):
        return (ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000) != 0

    def check_global_keys(self):
        keys = {"f": 0x46, "1": 0x31, "2": 0x32, "3": 0x33, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            
            if key == "1":
                was_shooting = self.shoot_laser
                self.shoot_laser = pressed if self.awakened else False
                
                if self.shoot_laser and not was_shooting:
                    if self.laser_sound: self.laser_sound.play(loops=-1)
                elif not self.shoot_laser and was_shooting:
                    if self.laser_sound: pygame.mixer.stop() 
                continue

            if not pressed: self.key_states[key] = False; continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                
                if key == "f":
                    self.awakened = not self.awakened
                    if not self.awakened:
                        self.shoot_laser = False
                        self.super_flight = False
                        if self.laser_sound: pygame.mixer.stop()
                        if self.state == "FLIGHT": self.state = "FALLING"
                elif key == "2" and self.awakened:
                    self.super_flight = not self.super_flight
                    self.state = "FLIGHT" if self.super_flight else "FALLING"
                elif key == "3":
                    if self.state != "FAN_MODE":
                        self.state = "FAN_MODE"
                        self.scale = 1.1  
                    else:
                        self.state = "WANDER"
                        self.scale = self.base_scale  
                    self.super_flight = False
                    if self.laser_sound: pygame.mixer.stop()
                elif key == "s":
                    self.platforms.append((max(0, mx - 175), min(self.screen_width, mx + 175), my))
                elif key == "u":
                    self.platforms.clear()
                    if self.state == "WANDER" or self.state == "FLIGHT": self.state = "FALLING"

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
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def check_laser_beam_collisions(self, hx, hy, mx, my):
        if not (self.shoot_laser and self.awakened): return
        dx = mx - hx; dy = my - hy
        dist = math.sqrt(dx**2 + dy**2)
        if dist == 0: return
        try:
            with open("pos.txt", "w") as f:
                f.write(f"TSC_LASER_BEAM,{hx},{hy},{mx},{my}\n")
        except: pass

    def update_loop(self):
        self.check_global_keys()
        mx, my = self.get_cursor_pos()
        self.mouse_vx, self.mouse_vy = mx - self.last_mx, my - self.last_my
        self.last_mx, self.last_my = mx, my
        
        current_floor = self.find_current_floor()
        lpm_pressed = self.is_key_pressed(0x01) 
        cx, cy = self.x, self.y - (25 * self.scale)
        hx, hy = self.x, self.y - (52 * self.scale)
        
        if lpm_pressed and (self.state == "GRABBED" or ((cx - 35 <= mx <= cx + 35) and (cy - 50 <= my <= cy + 50))):
            if not (self.screen_width - 60 <= mx <= self.screen_width and my <= 50):
                self.state = "GRABBED"
                self.x, self.y = mx, my + 45
                self.vx, self.vy = 0, 0
        else:
            if self.state == "GRABBED": self.set_state("FALLING_RELEASE")

            if self.shoot_laser:
                self.vx, self.vy = 0, 0  
                self.check_laser_beam_collisions(hx, hy, mx, my)
            elif self.state == "FAN_MODE":
                target_x = self.screen_width - 80
                target_y = self.taskbar_floor
                self.x += (target_x - self.x) * 0.08
                self.y += (target_y - self.y) * 0.08
                self.vx, self.vy = 0, 0
            elif self.state == "FLIGHT" and self.super_flight:
                if self.anim_time % 90 == 0:
                    self.vx = random.uniform(-4.5, 4.5)
                    self.vy = random.uniform(-3.0, 3.0)
                    if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                if self.y > current_floor - 40: self.vy = -2.0
            else:
                if self.y < current_floor: self.vy += self.gravity
                else:
                    if self.state == "FALLING": self.state = "WANDER"
                    self.vy, self.y = 0, current_floor

                if self.state == "FALLING":
                    self.vx *= 0.99
                elif self.state == "WANDER":
                    if self.anim_time % 120 == 0:
                        speed_mod = 3.5 if self.awakened else 1.8
                        self.vx = random.choice([-speed_mod, speed_mod, 0])
                        if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                    if self.vx != 0: self.vx *= 0.96

            self.x += self.vx; self.y += self.vy

        if self.x < 35: self.x = 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = 1
        elif self.x > self.screen_width - 35: self.x = self.screen_width - 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = -1
        
        if self.state == "FLIGHT" and self.y < 60: self.y = 60; self.vy = 1.0
        elif self.state != "FLIGHT" and self.y < 40: self.y = 40; self.vy = -self.vy * self.bounce_friction

        self.canvas.delete("all"); self.anim_time += 1; self.draw_vector_tsc(); self.root.after(16, self.update_loop)
    def draw_vector_tsc(self):
        color_tsc = "#FF8000"
        w = 3 
        s = self.scale
        cx, cy = self.x, self.y
        mx, my = self.get_cursor_pos()

        # --- 1. RENDERING PRZYCISKU [ X ] ---
        bx1, by1 = self.screen_width - 50, 10
        bx2, by2 = self.screen_width - 10, 40
        self.canvas.create_rectangle(bx1, by1, bx2, by2, fill="red", outline="black", width=2)
        self.canvas.create_line(bx1 + 10, by1 + 8, bx2 - 10, by2 - 8, fill="white", width=3, capstyle="round")
        self.canvas.create_line(bx1 + 10, by2 - 8, bx2 - 10, by1 + 8, fill="white", width=3, capstyle="round")

        # --- 2. RYSOWANIE PIORUNÓW Z ALAN BECKER AVA 8 ---
        if self.awakened and self.state != "FAN_MODE":
            random.seed(self.anim_time // 3)
            for _ in range(6):
                lx, ly = cx + random.uniform(-15*s, 15*s), cy - random.uniform(0, 60*s)
                points = [(lx, ly)]
                for i in range(4):
                    lx += random.uniform(-10*s, 10*s)
                    ly += random.uniform(-12*s, 5*s)
                    points.append((lx, ly))
                for i in range(len(points)-1):
                    self.canvas.create_line(points[i], points[i], points[i+1], points[i+1], fill="#00FF00", width=int(2*s), capstyle="round")
            for _ in range(4):
                ix = cx + random.uniform(-25*s, 25*s)
                iy = cy - random.uniform(0, 65*s)
                self.canvas.create_line(ix, iy, ix, iy + random.uniform(2*s, 6*s), fill="#00FF00", width=int(1.5*s))

        # --- 3. PRZELICZANIE KOŚCI SYSTEMOWYCH ---
        hx, hy = cx, cy - (52 * s)          
        neck_x, neck_y = cx, cy - (42 * s)  
        pelvis_x, pelvis_y = cx, cy - (18 * s) 

        l_knee_x, l_knee_y = cx - (6 * s), cy - (9 * s)
        r_knee_x, r_knee_y = cx + (6 * s), cy - (9 * s)
        l_foot_x, l_foot_y = cx - (11 * s), cy
        r_foot_x, r_foot_y = cx + (11 * s), cy
        
        l_hand_x, l_hand_y = cx - (14 * s), cy - (28 * s)
        r_hand_x, r_hand_y = cx + (14 * s), cy - (28 * s)

        if self.state == "GRABBED":
            wave = self.anim_time * 0.55
            l_foot_x = cx - (8 * s) + math.sin(wave) * 7
            r_foot_x = cx + (8 * s) - math.sin(wave) * 7
            l_foot_y, r_foot_y = cy + (8 * s), cy + (8 * s)
            l_knee_y, r_knee_y = cy + (2 * s), cy + (2 * s)
            l_hand_y = cy - (42 * s) + math.cos(wave) * 4
            r_hand_y = cy - (42 * s) - math.sin(wave) * 4
        elif self.shoot_laser and self.awakened:
            l_hand_x, r_hand_x = cx - (18 * s), cx + (18 * s)
            l_hand_y, r_hand_y = cy - (22 * s), cy - (22 * s)
        elif self.state == "FAN_MODE":
            # 📍 POPRAWIONO: KLASYCZNY SIAD BOCZNY - OBIE NOGI SKIEROWANE W LEWĄ STRONĘ!
            pelvis_y = cy - (6 * s)  # Tyłek opada na podłogę
            neck_y = cy - (28 * s)
            hx, hy = cx, cy - (38 * s)  # Ciało siedzi ładnie pionowo i prosto
            
            # Kolana wysunięte ostro w lewo
            l_knee_x, l_knee_y = cx - (15 * s), cy - (6 * s)
            r_knee_x, r_knee_y = cx - (13 * s), cy - (8 * s) # Lekkie przesunięcie dla efektu 3D
            
            # Łydki i stopy ułożone poziomo w lewą stronę wzdłuż linii podłogi
            l_foot_x, l_foot_y = cx - (26 * s), cy
            r_foot_x, r_foot_y = cx - (24 * s), cy
            
            wave = self.anim_time * 0.3
            l_hand_x, l_hand_y = cx - (10 * s), cy - (20 * s) + math.sin(wave) * 6
            r_hand_x, r_hand_y = cx + (10 * s), cy - (20 * s) + math.cos(wave) * 6
        elif self.state == "FLIGHT" and self.super_flight:
            l_foot_y, r_foot_y = cy - (4 * s), cy - (6 * s)
            l_knee_y, r_knee_y = cy - (10 * s), cy - (12 * s)
            l_hand_x, r_hand_x = cx - (6 * s) * self.walk_direction, cx - (4 * s) * self.walk_direction
            l_hand_y, r_hand_y = cy - (15 * s), cy - (12 * s)
        elif self.state == "FALLING" or abs(self.vy) > 2:
            l_foot_y, r_foot_y = cy - (6 * s), cy - (4 * s)
        elif self.state == "WANDER" and self.vx != 0:
            wave = self.anim_time * (0.32 if self.awakened else 0.18)
            stride = math.sin(wave) * (9 * s)
            l_foot_x += stride; r_foot_x -= stride
            l_knee_x += stride * 0.5; r_knee_x -= stride * 0.5

        # --- 4. RENDERING GEOMETRII KLASYCZNEGO TSC (PUSTA W ŚRODKU POMARAŃCZOWA GŁOWA) ---
        head_r = 8.5 * s
        self.canvas.create_oval(hx - head_r, hy - head_r, hx + head_r, hy + head_r, outline=color_tsc, width=w)
        
        self.canvas.create_line(neck_x, neck_y, pelvis_x, pelvis_y, fill=color_tsc, width=w)
        self.canvas.create_line(neck_x, neck_y, l_hand_x, l_hand_y, fill=color_tsc, width=w)
        self.canvas.create_line(neck_x, neck_y, r_hand_x, r_hand_y, fill=color_tsc, width=w)
        
        self.canvas.create_line(pelvis_x, pelvis_y, l_knee_x, l_knee_y, fill=color_tsc, width=w)
        self.canvas.create_line(l_knee_x, l_knee_y, l_foot_x, l_foot_y, fill=color_tsc, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, r_knee_x, r_knee_y, fill=color_tsc, width=w)
        self.canvas.create_line(r_knee_x, r_knee_y, r_foot_x, r_foot_y, fill=color_tsc, width=w)

        # --- 5. WYSTRZAŁ ZIELONEGO PROMIENIA LASERA BEZ LIMITU ZASIĘGU (Klawisz 1) ---
        if self.shoot_laser and self.awakened:
            dx = mx - hx; dy = my - hy
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                end_x = hx + (dx / dist) * 5000
                end_y = hy + (dy / dist) * 5000
                self.canvas.create_line(hx, hy, end_x, end_y, fill="#00FF00", width=int(14*s), capstyle="round")
                self.canvas.create_line(hx, hy, end_x, end_y, fill="white", width=int(5*s), capstyle="round")
                if self.anim_time % 6 < 3:
                    self.canvas.create_oval(hx - 14*s, hy - 14*s, hx + 14*s, hy + 14*s, outline="#A9FCD4", width=2)

if __name__ == "__main__":
    AvATSCEngine()
