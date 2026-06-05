import tkinter as tk
import math
import ctypes
from ctypes import wintypes  
import random

class AvATDLEngine:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        self.root = tk.Tk()
        self.root.title("AvA TDL")
        
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

        self.key_states = {"x": False, "c": False, "v": False, "9": False, "`": False, "-": False, "s": False, "u": False}
        
        self.scale = 1.5
        self.x = self.screen_width // 2
        self.y = self.taskbar_floor
        self.vx = 0
        self.vy = 0
        self.gravity = 0.65
        self.bounce_friction = 0.5
        
        self.state = "WANDER"
        self.anim_time = 0
        
        self.has_blades = False      
        self.is_flying = False       
        self.x_slashes = []          
        self.virabots = []           
        self.tdl_fireballs = []      
        
        self.damaged_timer = 0       
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
        """KANONICZNE ZASADY: Laser TSC usuwa TDL od razu. Ogień TCO tylko go oszałamia."""
        tsc_laser = self.is_key_pressed(0x31)
        tco_fire = self.is_key_pressed(0x4C) 
        
        if (tsc_laser or tco_fire):
            mx, my = self.get_cursor_pos()
            cx, cy = self.x, self.y - (25 * self.scale)
            
            if (cx - 35 <= mx <= cx + 35) and (cy - 55 <= my <= cy + 55):
                if tsc_laser:
                    # KANON: Potężny laser TSC natychmiast KASUJE I ZAMYKA okno TDL!
                    self.root.destroy()
                    exit()
                elif self.damaged_timer == 0:
                    # KANON: Atak ognia od TCO daje tylko 2 sekundy paraliżu!
                    self.damaged_timer = 120  
                    self.vx, self.vy = 0, 0
                    self.is_flying = False

    def check_global_keys(self):
        keys = {"x": 0x58, "c": 0x43, "v": 0x56, "9": 0x39, "`": 0xC0, "-": 0xBD, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            
            if key == "9":
                if pressed and not self.key_states["9"]:
                    self.key_states["9"] = True
                    if self.damaged_timer == 0:
                        sx = self.x
                        sy = self.y - (25 * self.scale)
                        dx = mx - sx
                        dy = my - sy
                        dist = math.sqrt(dx**2 + dy**2)
                        if dist > 0:
                            speed = 12.0
                            self.tdl_fireballs.append({
                                "x": sx, "y": sy, 
                                "vx": (dx / dist) * speed, 
                                "vy": (dy / dist) * speed
                            })
                elif not pressed:
                    self.key_states["9"] = False
                continue

            if not pressed: self.key_states[key] = False; continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                if self.damaged_timer > 0: continue 
                
                if key == "x":
                    self.has_blades = not self.has_blades
                elif key == "c" and len(self.virabots) < 3:
                    self.virabots.append({"x": self.x, "y": self.y - 10, "vx": random.choice([-5, 5]), "vy": -6, "anim": 0})
                elif key == "`":
                    self.virabots.clear()
                elif key == "-":
                    self.is_flying = not self.is_flying
                    if not self.is_flying: self.state = "WANDER"
                elif key == "v":
                    self.x_slashes.append({"x": self.x, "y": self.y - (28 * self.scale), "vx": self.walk_direction * 14.0})
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
        
        floor = self.find_current_floor()
        lpm_pressed = self.is_key_pressed(0x01) 
        cx, cy = self.x, self.y - (25 * self.scale)
        
        if lpm_pressed and (self.state == "GRABBED" or ((cx - 35 <= mx <= cx + 35) and (cy - 50 <= my <= cy + 50))):
            self.state = "GRABBED"
            self.x, self.y = mx, my + 45
            self.vx, self.vy = 0, 0
            self.damaged_timer = 0
            self.is_flying = False
        else:
            if self.state == "GRABBED": self.set_state("FALLING_RELEASE")

            if self.damaged_timer > 0:
                self.damaged_timer -= 1
                self.vx = random.uniform(-1.5, 1.5) 
                self.vy = 0
                if self.damaged_timer == 0: self.state = "WANDER"
            elif self.is_flying:
                if self.anim_time % 90 == 0:
                    speed_mod = 5.5 if self.has_blades else 3.0
                    self.vx = random.choice([-speed_mod, speed_mod, 0])
                    self.vy = random.choice([-1.5, 1.5, 0])
                    if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                if self.y > floor - 100:
                    self.vy = -2.0
            else:
                if self.y < floor: self.vy += self.gravity
                else:
                    if self.state == "FALLING": self.state = "WANDER"
                    self.vy, self.y = 0, floor

                if self.state == "FALLING":
                    self.vx *= 0.99
                elif self.state == "WANDER":
                    if self.anim_time % 120 == 0:
                        speed_mod = 5.0 if self.has_blades else 2.2
                        self.vx = random.choice([-speed_mod, speed_mod, 0])
                        if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                        if self.has_blades and self.vx != 0 and self.y >= floor and random.random() < 0.4:
                            self.vy = -12.5
                    if self.vx != 0: self.vx *= 0.96

            self.x += self.vx; self.y += self.vy

        if self.x < 35: self.x = 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = 1
        elif self.x > self.screen_width - 35: self.x = self.screen_width - 35; self.vx = -self.vx * self.bounce_friction; self.walk_direction = -1
        
        if self.is_flying and self.y < 80: self.y = 80; self.vy = 1.0
        elif not self.is_flying and self.y < 40: self.y = 40; self.vy = -self.vy * self.bounce_friction

        self.canvas.delete("all"); self.anim_time += 1; self.draw_vector_tdl(); self.root.after(16, self.update_loop)
    def draw_vector_tdl(self):
        color_red = "#FF0000"
        color_black = "#000000"
        w = 4
        s = self.scale
        cx, cy = self.x, self.y
        mx, my = self.get_cursor_pos()

        # --- 1. RYSOWANIE HAKERSKICH KUL OGNIA (Klawisz 9) ---
        for fb in self.tdl_fireballs[:]:
            fb["x"] += fb["vx"]
            fb["y"] += fb["vy"]
            self.canvas.create_oval(fb["x"] - 7*s, fb["y"] - 7*s, fb["x"] + 7*s, fb["y"] + 7*s, fill="#FFCC00", outline="")
            self.canvas.create_oval(fb["x"] - 4*s, fb["y"] - 4*s, fb["x"] + 4*s, fb["y"] + 4*s, fill=color_red, outline="")
            if fb["x"] < 0 or fb["x"] > self.screen_width or fb["y"] < 0 or fb["y"] > self.screen_height:
                self.tdl_fireballs.remove(fb)

        # --- 2. RYSOWANIE X-SLASHY (Klawisz V) ---
        for slash in self.x_slashes[:]:
            slash["x"] += slash["vx"]
            sx, sy = slash["x"], slash["y"]
            self.canvas.create_line(sx - 25*s, sy - 25*s, sx + 25*s, sy + 25*s, fill=color_red, width=int(5*s))
            self.canvas.create_line(sx + 25*s, sy - 25*s, sx - 25*s, sy + 25*s, fill=color_red, width=int(5*s))
            self.canvas.create_line(sx - 20*s, sy - 20*s, sx + 20*s, sy + 20*s, fill="white", width=int(1.5*s))
            self.canvas.create_line(sx + 20*s, sy - 20*s, sx - 20*s, sy + 20*s, fill="white", width=int(1.5*s))
            if sx < -100 or sx > self.screen_width + 100:
                self.x_slashes.remove(slash)

        # --- 3. RYSOWANIE VIRABOTÓW (Klawisz C) ---
        for spider in self.virabots:
            spider["anim"] += 1
            spider["vy"] += 0.45  
            spider["x"] += spider["vx"]
            spider["y"] += spider["vy"]

            if spider["y"] > self.taskbar_floor:
                spider["y"] = self.taskbar_floor
                spider["vy"] = -random.uniform(5.5, 8.5) 
            if spider["x"] < 20 or spider["x"] > self.screen_width - 20:
                spider["vx"] = -spider["vx"]

            sp_x, sp_y = spider["x"], spider["y"]
            self.canvas.create_oval(sp_x - 6*s, sp_y - 12*s, sp_x + 6*s, sp_y, fill=color_red, outline=color_black, width=1.5)
            eye_color = "white" if spider["anim"] % 20 < 12 else color_black
            self.canvas.create_oval(sp_x - 2*s, sp_y - 9*s, sp_x + 2*s, sp_y - 5*s, fill=eye_color, outline="")
            
            leg_wave = math.sin(spider["anim"] * 0.4) * 4 * s
            self.canvas.create_line(sp_x - 5*s, sp_y - 4*s, sp_x - 12*s, sp_y - 2*s + leg_wave, fill=color_black, width=2)
            self.canvas.create_line(sp_x + 5*s, sp_y - 4*s, sp_x + 12*s, sp_y - 2*s - leg_wave, fill=color_black, width=2)
            self.canvas.create_line(sp_x - 5*s, sp_y - 8*s, sp_x - 14*s, sp_y - 9*s - leg_wave, fill=color_black, width=2)
            self.canvas.create_line(sp_x + 5*s, sp_y - 8*s, sp_x + 14*s, sp_y - 9*s + leg_wave, fill=color_black, width=2)

        # --- 4. PRZELICZANIE POZYCJI KOŚCI ---
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
        elif self.damaged_timer > 0:
            hy += random.randint(-2, 2)
            l_hand_y, r_hand_y = cy - (48 * s), cy - (50 * s)
            l_foot_x, r_foot_x = cx - (6 * s), cx + (6 * s)
            if self.anim_time % 4 < 2:
                self.canvas.create_text(hx, hy - 15*s, text="ERROR", fill=color_red, font=("Courier", int(7*s), "bold"))
        elif self.is_flying:
            hy += 4 * s
            l_hand_x, r_hand_x = cx - (2 * s) * self.walk_direction, cx - (4 * s) * self.walk_direction
            l_hand_y, r_hand_y = cy - (48 * s), cy - (50 * s)
            l_foot_x, r_foot_x = cx - (6 * s) * self.walk_direction, cx - (4 * s) * self.walk_direction
            l_foot_y, r_foot_y = cy - (10 * s), cy - (12 * s)
        elif self.has_blades:
            hy += 3 * s
            neck_y += 2 * s
            l_hand_x = cx - (18 * s) * self.walk_direction
            r_hand_x = cx + (18 * s) * self.walk_direction
            l_hand_y, r_hand_y = cy - (32 * s), cy - (32 * s)
            if self.vx != 0:
                wave = self.anim_time * 0.45  
                l_foot_x = cx + math.sin(wave) * 11 * s
                r_foot_x = cx - math.sin(wave) * 11 * s
        elif self.state == "FALLING" or abs(self.vy) > 2:
            l_foot_y = cy - (6 * s)
            r_foot_y = cy - (4 * s)
            l_hand_y = cy - (42 * s)
            r_hand_y = cy - (42 * s)
        elif self.state == "WANDER" and self.vx != 0:
            wave = self.anim_time * 0.22
            l_foot_x = cx + math.sin(wave) * 9 * s
            r_foot_x = cx - math.sin(wave) * 9 * s

        # --- 5. RYSOWANIE CZARNYCH OSTRZY (Klawisz X) ---
        if self.has_blades and self.damaged_timer == 0:
            for h_x, h_y in [(l_hand_x, l_hand_y), (r_hand_x, r_hand_y)]:
                ox = h_x + (25 * s) * self.walk_direction
                oy = h_y - (4 * s)
                if self.is_flying: 
                    ox = h_x + (15 * s) * self.walk_direction
                    oy = h_y + (15 * s)
                self.canvas.create_line(h_x, h_y, ox, oy, fill=color_black, width=int(5.5 * s))
                self.canvas.create_line(h_x, h_y - 2*s, ox, oy, fill=color_red, width=int(1.5 * s)) 
                if random.random() < 0.6:
                    ix = ox + random.randint(-5, 5)
                    iy = oy + random.randint(0, 15)
                    self.canvas.create_rectangle(ix, iy, ix+2*s, iy+2*s, fill=color_red, outline="")

        # --- 6. RENDERING KOŚCI I CZARNYCH DŁONI TDL ---
        head_r = 8.5 * s
        self.canvas.create_oval(hx - head_r, hy - head_r, hx + head_r, hy + head_r, outline=color_red, fill="#010101", width=w)
        self.canvas.create_line(neck_x, neck_y, pelvis_x, pelvis_y, fill=color_red, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, l_foot_x, l_foot_y, fill=color_red, width=w)
        self.canvas.create_line(pelvis_x, pelvis_y, r_foot_x, r_foot_y, fill=color_red, width=w)
        self.canvas.create_line(neck_x, neck_y, l_hand_x, l_hand_y, fill=color_red, width=w)
        self.canvas.create_line(neck_x, neck_y, r_hand_x, r_hand_y, fill=color_red, width=w)
        self.canvas.create_oval(l_hand_x - 3.5*s, l_hand_y - 3.5*s, l_hand_x + 3.5*s, l_hand_y + 3.5*s, fill=color_black, outline="")
        self.canvas.create_oval(r_hand_x - 3.5*s, r_hand_y - 3.5*s, r_hand_x + 3.5*s, r_hand_y + 3.5*s, fill=color_black, outline="")

if __name__ == "__main__":
    AvATDLEngine()
