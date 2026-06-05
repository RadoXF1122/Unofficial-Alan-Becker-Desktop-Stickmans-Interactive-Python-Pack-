import tkinter as tk
import math
import ctypes
import random

class AvAYellowEngine:
    def __init__(self):
        # Wymuszenie idealnego skalowania Windowsa co do 1 piksela
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        self.root = tk.Tk()
        self.root.title("AvA Yellow")
        
        # Wymiary małego okienka dającego stałe 60 FPS
        self.box_size = 140
        self.half_box = self.box_size // 2
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.taskbar_floor = self.screen_height - 40  
        
        # Okienko overlay bez ramek podróżujące za Yellowem
        self.root.geometry(f"{self.box_size}x{self.box_size}+{self.screen_width//5}+{self.taskbar_floor - self.box_size}")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        # Specjalne tło eliminujące kropki/artefakty
        self.trans_color = "#010101"
        self.root.wm_attributes("-transparentcolor", self.trans_color)
        self.canvas = tk.Canvas(self.root, width=self.box_size, height=self.box_size, bg=self.trans_color, highlightthickness=0)
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.key_states = {"p": False, "s": False, "u": False}
        self.scale = 1.4
        self.x = self.screen_width // 5
        self.y = self.taskbar_floor
        self.vx = 0
        self.vy = 0
        self.gravity = 0.65
        self.bounce_friction = 0.5
        
        self.state = "WANDER"
        self.anim_time = 0
        self.has_laptop = False
        self.think_timer = 0
        self.walk_direction = 1  
        self.platforms = []
        
        # NAPRAWIONE: Zmienne myszy zadeklarowane PRZED pętlą gry
        self.last_mx = 0
        self.last_my = 0
        self.mouse_vx = 0
        self.mouse_vy = 0
        
        # Start pętli na samym dole sekcji init
        self.update_loop()
        self.root.mainloop()

    def on_press(self, event):
        self.state = "GRABBED"
        self.vx = 0
        self.vy = 0
        self.think_timer = 0

    def on_release(self, event):
        if self.state == "GRABBED":
            self.state = "FALLING"
            self.vx = self.mouse_vx * 0.85
            self.vy = self.mouse_vy * 0.85

    def is_key_pressed(self, key_code):
        return (ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000) != 0

    def check_laser_collision(self):
        if self.is_key_pressed(0x31): 
            mx, my = self.get_cursor_pos()
            cx = self.x
            cy = self.y - (25 * self.scale)
            if (cx - 30 <= mx <= cx + 30) and (cy - 45 <= my <= cy + 45):
                self.root.destroy()
                exit()

    def check_global_keys(self):
        keys = {"p": 0x50, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            if not pressed: 
                self.key_states[key] = False
                continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                if key == "p":
                    self.has_laptop = not self.has_laptop
                    if self.has_laptop and self.state == "WANDER": 
                        self.vx = self.walk_direction * 1.5
                elif key == "s": 
                    left_p = max(0, mx - 175)
                    right_p = min(self.screen_width, mx + 175)
                    self.platforms.append((left_p, right_p, my))
                elif key == "u": 
                    self.platforms.clear()
                    if self.state == "WANDER": 
                        self.state = "FALLING"

    def find_current_floor(self):
        best_floor = self.taskbar_floor
        for left, right, top in self.platforms:
            if left <= self.x <= right:
                tolerance = max(6.0, abs(self.vy) + 2)
                if top - 3 <= self.y <= top + tolerance:
                    if top < best_floor: 
                        best_floor = top
        return best_floor

    def get_cursor_pos(self):
        class POINT(ctypes.Structure): 
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def update_loop(self):
        self.check_global_keys()
        self.check_laser_collision()
        
        mx, my = self.get_cursor_pos()
        self.mouse_vx = mx - self.last_mx
        self.mouse_vy = my - self.last_my
        self.last_mx = mx
        self.last_my = my
        
        floor = self.find_current_floor()

        if self.state == "GRABBED":
            self.x = mx
            self.y = my + 45
        else:
            if self.y < floor: 
                self.vy += self.gravity
            else:
                if self.state == "FALLING": 
                    self.state = "WANDER"
                self.vy = 0
                self.y = floor
                
            if self.state == "FALLING":
                self.vx *= 0.99
            elif self.state == "WANDER":
                if self.has_laptop:
                    if self.think_timer > 0:
                        self.think_timer -= 1
                        self.vx = 0
                    else:
                        if random.random() < 0.008: 
                            self.think_timer = random.randint(40, 90)
                        self.vx = self.walk_direction * 1.5
                else:
                    if self.anim_time % 120 == 0: 
                        self.vx = random.choice([-2.0, 2.0, 0])
                        if self.vx != 0: 
                            self.walk_direction = 1 if self.vx > 0 else -1
                    if self.vx != 0: 
                        self.vx *= 0.96
                        
            self.x += self.vx
            self.y += self.vy
            
            if self.x < 35: 
                self.x = 35
                self.vx = -self.vx * self.bounce_friction
                self.walk_direction = 1
            elif self.x > self.screen_width - 35: 
                self.x = self.screen_width - 35
                self.vx = -self.vx * self.bounce_friction
                self.walk_direction = -1
                
            if self.y < 40: 
                self.y = 40
                self.vy = -self.vy * self.bounce_friction
                
        self.root.geometry(f"+{int(self.x - self.half_box)}+{int(self.y - self.box_size)}")
        self.canvas.delete("all")
        self.anim_time += 1
        self.draw_vector_yellow()
        self.root.after(16, self.update_loop)
    def draw_vector_yellow(self):
        color = "#FFCC00"  # CZYSYTY ŻÓŁTY COLOR TSC GANGU
        w = 4
        s = self.scale
        
        cx = self.half_box
        cy = self.box_size - 2

        # Pozycje lokalne stawów (przed przesunięciem)
        hx = 0
        hy = -(52 * s)          
        neck_x = 0
        neck_y = -(42 * s)  
        pelvis_x = 0
        pelvis_y = -(18 * s) 

        l_foot_x = -(11 * s)
        l_foot_y = 0
        r_foot_x = (11 * s)
        r_foot_y = 0
        l_hand_x = -(14 * s)
        l_hand_y = -(28 * s)
        r_hand_x = (14 * s)
        r_hand_y = -(28 * s)
        
        # Obliczanie klatek pod animacje kroków
        if self.state == "GRABBED":
            wave = self.anim_time * 0.55
            l_foot_x = -(8 * s) + math.sin(wave) * 7
            r_foot_x = (8 * s) - math.sin(wave) * 7
            l_foot_y = (8 * s)
            r_foot_y = (8 * s)
            l_hand_y = -(42 * s) + math.cos(wave) * 4
            r_hand_y = -(42 * s) - math.cos(wave) * 4
        elif self.state == "FALLING" or abs(self.vy) > 2:
            l_foot_y = -(6 * s)
            r_foot_y = -(4 * s)
            l_hand_y = -(42 * s)
            r_hand_y = -(42 * s)
        elif self.state == "WANDER":
            if self.has_laptop:
                # Sylwetka pochylona do komputera
                hy = -(49 * s)
                l_hand_x = (6 * s) * self.walk_direction
                r_hand_x = (14 * s) * self.walk_direction
                l_hand_y = -(32 * s)
                r_hand_y = -(32 * s)
                
                lap_x = cx + (18 * s) * self.walk_direction
                lap_y = cy - (32 * s)
                
                # Rysowanie laptopa na płótnie
                self.canvas.create_line(lap_x - 6 * s, lap_y, lap_x + 6 * s, lap_y, fill="#888888", width=2)
                self.canvas.create_line(lap_x + 2 * s, lap_y, lap_x + 6 * s, lap_y - 8 * s, fill="#AAAAAA", width=2)
                
                # Kod mrugający na zielono
                if self.anim_time % 10 < 6:
                    self.canvas.create_text(lap_x + 3 * s, lap_y - 4 * s, text="..", fill="#00FF33", font=("Arial", int(5 * s), "bold"))
                if self.anim_time % 14 < 8:
                    self.canvas.create_text(lap_x + 4 * s, lap_y - 6 * s, text="...", fill="#00FF33", font=("Arial", int(4 * s), "bold"))
                
                # Tryb rozmyślania nad skryptem (drapanie się po głowie)
                if self.think_timer > 0:
                    l_foot_x = -(4 * s)
                    r_foot_x = (4 * s)
                    if self.walk_direction == 1:
                        r_hand_x = (2 * s)
                        r_hand_y = -(60 * s)
                    else:
                        l_hand_x = -(2 * s)
                        l_hand_y = -(60 * s)
                else:
                    wave = self.anim_time * 0.18
                    l_foot_x = math.sin(wave) * 7 * s
                    r_foot_x = -math.sin(wave) * 7 * s
            elif self.vx != 0:
                wave = self.anim_time * 0.22
                l_foot_x = math.sin(wave) * 9 * s
                r_foot_x = -math.sin(wave) * 9 * s

        # Mapowanie na współrzędne okna
        ghx = hx + cx
        ghy = hy + cy
        gneck_x = neck_x + cx
        gneck_y = neck_y + cy
        gpelvis_x = pelvis_x + cx
        gpelvis_y = pelvis_y + cy
        glf_x = l_foot_x + cx
        glf_y = l_foot_y + cy
        grf_x = r_foot_x + cx
        grf_y = r_foot_y + cy
        glh_x = l_hand_x + cx
        glh_y = l_hand_y + cy
        grh_x = r_hand_x + cx
        grh_y = r_hand_y + cy

        # Rysowanie głowy (100% pełna w środku)
        head_r = 8.5 * s
        self.canvas.create_oval(ghx - head_r, ghy - head_r, ghx + head_r, ghy + head_r, outline=color, fill=color, width=w)
        
        # Rysowanie struktury kości
        self.canvas.create_line(gneck_x, gneck_y, gpelvis_x, gpelvis_y, fill=color, width=w)
        self.canvas.create_line(gneck_x, gneck_y, glh_x, glh_y, fill=color, width=w)
        self.canvas.create_line(gneck_x, gneck_y, grh_x, grh_y, fill=color, width=w)
        self.canvas.create_line(gpelvis_x, gpelvis_y, glf_x, glf_y, fill=color, width=w)
        self.canvas.create_line(gpelvis_x, gpelvis_y, grf_x, grf_y, fill=color, width=w)

if __name__ == "__main__":
    AvAYellowEngine()
