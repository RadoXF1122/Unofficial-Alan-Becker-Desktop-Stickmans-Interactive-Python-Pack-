import tkinter as tk
import math
import ctypes
from ctypes import wintypes  
import random

class AvATCOEngine:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        self.root = tk.Tk()
        self.root.title("AvA TCO")
        
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

        self.key_states = {"t": False, "r": False, "l": False, "s": False, "u": False}
        
        self.scale = 1.5
        self.x = self.screen_width // 3
        self.y = self.taskbar_floor
        self.vx = 0
        self.vy = 0
        self.gravity = 0.65
        self.bounce_friction = 0.5
        
        self.state = "WANDER"
        self.anim_time = 0
        self.is_flying = False       
        self.shoot_laser = False     
        self.shoot_fire = False      
        self.walk_direction = 1
        
        self.damaged_timer = 0       
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
            self.vx, self.vy = self.mouse_vx * 0.85, self.mouse_vy * 0.85

    def is_key_pressed(self, key_code):
        return (ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000) != 0

    def check_laser_collision(self):
        """KANONICZNE ZASADY: TSC usuwa TCO od razu. Ataki TDL tylko oszałamiają na 2 sekundy."""
        tsc_laser = self.is_key_pressed(0x31)
        tdl_blades = self.is_key_pressed(0x58) 
        tdl_fire = self.is_key_pressed(0x39)   
        tdl_slash = self.is_key_pressed(0x56)  
        
        if (tsc_laser or tdl_blades or tdl_fire or tdl_slash):
            mx, my = self.get_cursor_pos()
            cx = self.x
            cy = self.y - (25 * self.scale)
            
            if (cx - 40 <= mx <= cx + 40) and (cy - 60 <= my <= cy + 60):
                if tsc_laser:
                    # KANON: Potężny laser TSC całkowicie USUWA TCO z pulpitu!
                    self.root.destroy()
                    exit()
                elif self.damaged_timer == 0:
                    # KANON: Ataki TDL dają tylko 2 sekundy paraliżu!
                    self.damaged_timer = 120  
                    self.vx, self.vy = 0, 0
                    self.is_flying = False

    def check_global_keys(self):
        keys = {"t": 0x54, "r": 0x52, "l": 0x4C, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            
            if key == "r":
                self.shoot_laser = pressed
                continue
            if key == "l":
                self.shoot_fire = False if self.is_flying else pressed
                continue

            if not pressed: self.key_states[key] = False; continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                if self.damaged_timer > 0: continue
                
                if key == "t":
                    self.is_flying = not self.is_flying
                    if not self.is_flying: self.state = "WANDER"
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
        
        current_floor = self.find_current_floor()
        lpm_pressed = self.is_key_pressed(0x01) 
        cx, cy = self.x, self.y - (25 * self.scale)
        
        if lpm_pressed and (self.state == "GRABBED" or ((cx - 35 <= mx <= cx + 35) and (cy - 50 <= my <= cy + 50))):
            self.state = "GRABBED"
            self.x, self.y = mx, my + 45
            self.vx, self.vy = 0, 0
            self.is_flying = False
            self.damaged_timer = 0
        else:
            if self.state == "GRABBED": self.set_state("FALLING_RELEASE")

            if self.damaged_timer > 0:
                self.damaged_timer -= 1
                self.vx = random.uniform(-1.5, 1.5)
                self.vy = 0
                if self.damaged_timer == 0: self.state = "WANDER"
            elif self.shoot_fire:
                self.vx, self.vy = 0, 0
            elif self.is_flying:
                if self.anim_time % 100 == 0:
                    self.vx = random.choice([-3.5, 3.5, 0])
                    self.vy = random.choice([-1.5, 1.5, 0])
                    if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                if self.y > current_floor - 120: self.vy = -2.0
            else:
                if self.y < current_floor: self.vy += self.gravity
                else:
                    if self.state == "FALLING": self.state = "WANDER"
                    self.vy, self.y = 0, current_floor

                if self.state == "FALLING":
                    self.vx *= 0.99
                elif self.state == "WANDER":
                    if self.anim_time % 120 == 0:
                        self.vx = random.choice([-2.2, 2.2, 0])
                        if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                    if self.vx != 0: self.vx *= 0.96

            self.x += self.vx; self.y += self.vy

        if self.x < 35: self.x = 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = 1
        elif self.x > self.screen_width - 35: self.x = self.screen_width - 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = -1
        if self.is_flying and self.y < 80: self.y = 80; self.vy = 1.0
        elif not self.is_flying and self.y < 40: self.y = 40; self.vy = -self.vy * self.bounce_friction

        self.canvas.delete("all"); self.anim_time += 1; self.draw_vector_tco(); self.root.after(16, self.update_loop)
    def draw_vector_tco(self):
        color = "#000000"
        w = 4
        s = self.scale
        cx = self.x
        cy = self.y
        mx, my = self.get_cursor_pos()

        # Pozycje lokalne stawów
        hx = cx
        hy = cy - (52 * s)          
        neck_x = cx
        neck_y = cy - (42 * s)  
        pelvis_x = cx
        pelvis_y = cy - (18 * s) 

        l_foot_x = cx - (11 * s)
        l_foot_y = cy
        r_foot_x = cx + (11 * s)
        r_foot_y = cy
        l_hand_x = cx - (14 * s)
        l_hand_y = cy - (28 * s)
        r_hand_x = cx + (14 * s)
        r_hand_y = cy - (28 * s)

        # Dopasowanie klatek pod animacje, lot i paraliż
        if self.state == "GRABBED":
            wave = self.anim_time * 0.55
            l_foot_x = cx - (8 * s) + math.sin(wave) * 7
            r_foot_x = cx + (8 * s) - math.sin(wave) * 7
            l_foot_y = cy + (8 * s)
            r_foot_y = cy + (8 * s)
            l_hand_y = cy - (42 * s) + math.cos(wave) * 4
            r_hand_y = cy - (42 * s) - math.sin(wave) * 4
        elif self.damaged_timer > 0:
            # ANIMACJA PARALIŻU TCO: Drży z bólu w nieskończonych starciach
            hy += random.randint(-1, 1)
            l_hand_y = cy - (45 * s)
            r_hand_y = cy - (47 * s)
            l_foot_x = cx - (5 * s)
            r_foot_x = cx + (5 * s)
            if self.anim_time % 6 < 3:
                self.canvas.create_text(hx, hy - 15*s, text="GLITCH", fill="#00FFFF", font=("Courier", int(8*s), "bold"))
        elif self.is_flying and not self.shoot_fire:
            l_hand_x = cx - (6 * s)
            r_hand_x = cx + (6 * s)
            l_hand_y = cy - (15 * s)
            r_hand_y = cy - (15 * s)
            l_foot_y = cy - (2 * s)
            r_foot_y = cy - (2 * s)
        elif self.shoot_fire:
            run_dir = 1 if mx > self.x else -1
            l_hand_x = cx + (16 * s) * run_dir
            r_hand_x = cx + (20 * s) * run_dir
            l_hand_y = cy - (38 * s)
            r_hand_y = cy - (38 * s)
        elif self.state == "FALLING" or abs(self.vy) > 2:
            l_foot_y = cy - (6 * s)
            r_foot_y = cy - (4 * s)
            l_hand_y = cy - (42 * s)
            r_hand_y = cy - (42 * s)
        elif self.state == "WANDER" and self.vx != 0:
            wave = self.anim_time * 0.22
            stride = math.sin(wave) * 9 * s
            l_foot_x = cx + stride
            r_foot_x = cx - stride

        # Ogień z dłoni w dół (Gdy lot T jest włączony)
        if self.is_flying and not self.shoot_fire and self.damaged_timer == 0:
            for h_x, h_y in [(l_hand_x, l_hand_y), (r_hand_x, r_hand_y)]:
                for _ in range(3):
                    f_len = random.randint(15, 35)
                    f_off = random.randint(-4, 4)
                    f_color = random.choice(["#FF3300", "#FF9900", "#FFCC00"])
                    self.canvas.create_line(h_x + f_off, h_y, h_x + f_off, h_y + f_len, fill=f_color, width=2)

        # Strumień ognia w kursor myszy (Klawisz L)
        if self.shoot_fire and not self.is_flying and self.damaged_timer == 0:
            for h_x, h_y in [(l_hand_x, l_hand_y), (r_hand_x, r_hand_y)]:
                dx_f = mx - h_x
                dy_f = my - h_y
                dist_f = math.sqrt(dx_f**2 + dy_f**2)
                if dist_f < 50: dist_f = 50
                    
                for _ in range(4):
                    rand_ang = random.uniform(-0.15, 0.15)
                    c = math.cos(rand_ang)
                    s_a = math.sin(rand_ang)
                    rx = (dx_f * c - dy_f * s_a) / dist_f
                    ry = (dx_f * s_a + dy_f * c) / dist_f
                    f_len = random.randint(50, min(350, int(dist_f)))
                    f_color = random.choice(["#FF1A00", "#FF7F00", "#FFD700"])
                    self.canvas.create_line(h_x, h_y, h_x + rx * f_len, h_y + ry * f_len, fill=f_color, width=3)

        # Laser z oczu bez limitu zasięgu (Klawisz R)
        if self.shoot_laser and self.damaged_timer == 0:
            self.canvas.create_line(hx, hy, mx, my, fill="#FF0000", width=6)
            self.canvas.create_line(hx, hy, mx, my, fill="white", width=2)

        # Głowa (Pusta) i kości Czarnego TSC
        head_r = 8.5 * s
        self.canvas.create_oval(hx - head_r, hy - head_r, hx + head_r, hy + head_r, outline=color, fill="#010101", width=w)
        self.canvas.create_line(neck_x, neck_y, pelvis_x, pelvis_y, fill=color, width=w)
        self.canvas.create_line(neck_x, neck_y, l_hand_x, l_hand_y, fill=color, width=w)
        self.canvas.create_line(neck_x, neck_y, r_hand_x, r_hand_y, fill=color, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, l_foot_x, l_foot_y, fill=color, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, r_foot_x, r_foot_y, fill=color, width=w)

if __name__ == "__main__":
    AvATCOEngine()
