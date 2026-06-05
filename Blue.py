import tkinter as tk
import math
import ctypes
import random

class AvABlueEngine:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        self.root = tk.Tk()
        self.root.title("AvA Blue")
        
        self.box_size = 140
        self.half_box = self.box_size // 2
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.taskbar_floor = self.screen_height - 40  
        
        self.root.geometry(f"{self.box_size}x{self.box_size}+{self.screen_width//3}+{self.taskbar_floor - self.box_size}")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        self.trans_color = "#010101"
        self.root.wm_attributes("-transparentcolor", self.trans_color)
        self.canvas = tk.Canvas(self.root, width=self.box_size, height=self.box_size, bg=self.trans_color, highlightthickness=0)
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", lambda e: self.set_state("GRABBED"))
        self.canvas.bind("<ButtonRelease-1>", lambda e: self.set_state("FALLING_RELEASE"))

        self.key_states = {"o": False, "s": False, "u": False}
        self.scale, self.x, self.y = 1.8, self.screen_width // 3, self.taskbar_floor
        self.vx, self.vy, self.gravity, self.bounce_friction = 0, 0, 0.65, 0.5
        self.state, self.anim_time, self.is_sonic = "WANDER", 0, False
        self.ghosts = []       
        self.last_mx, self.last_my = 0, 0
        self.mouse_vx, self.mouse_vy = 0, 0
        self.platforms = []
        self.update_loop()
        self.root.mainloop()

    def set_state(self, new_state):
        if new_state == "GRABBED":
            self.state, self.vx, self.vy = "GRABBED", 0, 0
            self.ghosts.clear()
        elif new_state == "FALLING_RELEASE":
            self.state = "FALLING"
            self.vx, self.vy = self.mouse_vx * 0.85, self.mouse_vy * 0.85

    def is_key_pressed(self, key_code):
        return (ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000) != 0

    def check_laser_collision(self):
        if self.is_key_pressed(0x31): 
            mx, my = self.get_cursor_pos()
            cx, cy = self.x, self.y - (25 * self.scale)
            if (cx - 30 <= mx <= cx + 45) and (cy - 65 <= my <= cy + 65):
                self.root.destroy()
                exit()

    def check_global_keys(self):
        keys = {"o": 0x4F, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            if not pressed: self.key_states[key] = False; continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                if key == "o": self.is_sonic = not self.is_sonic
                elif key == "s": self.platforms.append((max(0, mx - 175), min(self.screen_width, mx + 175), my))
                elif key == "u": 
                    self.platforms.clear()
                    if self.state == "WANDER": self.state = "FALLING"

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
        class POINT(ctypes.Structure): _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT(); ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def update_loop(self):
        self.check_global_keys(); self.check_laser_collision()
        mx, my = self.get_cursor_pos()
        self.mouse_vx, self.mouse_vy = mx - self.last_mx, my - self.last_my
        self.last_mx, self.last_my = mx, my
        
        # WPISANY OD NOWA POPRAWNY WARUNEK DETEKCJI PLATFORM
        current_floor = self.find_current_floor()

        if self.state == "GRABBED":
            self.x, self.y = mx, my + 45
            self.ghosts.clear()
        else:
            if self.y < current_floor: self.vy += self.gravity
            else:
                if self.state == "FALLING": self.state = "WANDER"
                self.vy, self.y = 0, current_floor
            if self.state == "FALLING":
                self.vx *= 0.99
            elif self.state == "WANDER":
                if self.is_sonic:
                    if self.vx == 0 or self.anim_time % 60 == 0: self.vx = random.choice([-15.0, 15.0])  
                else:
                    if self.anim_time % 120 == 0: self.vx = random.choice([-2.2, 2.2, 0])
                    if self.vx != 0: self.vx *= 0.96
            self.x += self.vx; self.y += self.vy
            if self.x < 35: self.x = 35; self.vx = -self.vx * self.bounce_friction
            elif self.x > self.screen_width - 35: self.x = self.screen_width - 35; self.vx = -self.vx * self.bounce_friction
            if self.y < 40: self.y = 40; self.vy = -self.vy * self.bounce_friction

        if self.is_sonic and self.state == "WANDER" and self.vx != 0:
            self.ghosts.append((self.half_box, self.box_size - 2, self.vx, self.anim_time))
            if len(self.ghosts) > 4: self.ghosts.pop(0)
        else:
            self.ghosts.clear()
        self.root.geometry(f"+{int(self.x - self.half_box)}+{int(self.y - self.box_size)}")
        self.canvas.delete("all"); self.anim_time += 1; self.draw_vector_blue(); self.root.after(16, self.update_loop)

    def draw_vector_blue(self):
        color, w, s = "#45BFEE", 4, self.scale
        cx, cy = self.half_box, self.box_size - 2
        if self.is_sonic and self.state == "WANDER" and self.vx != 0:
            for i, (gx, gy, gvx, gtime) in enumerate(self.ghosts):
                ghost_color = ["#155070", "#2A7E9E", "#3BB0CE", "#A9E5FC"][i]
                gw = 2 
                offset_x = (len(self.ghosts) - i) * (8 * s) * (1 if gvx > 0 else -1)
                ghx, ghy = cx - offset_x, gy - (52 * s)
                gneck_x, gneck_y = cx - offset_x, gy - (42 * s)
                gpelvis_x, gpelvis_y = cx - offset_x, gy - (18 * s)
                wave = gtime * 0.7  
                glf_x = cx - offset_x + math.sin(wave) * 9 * s
                grf_x = cx - offset_x - math.sin(wave) * 9 * s
                self.canvas.create_oval(ghx - 8.5*s, ghy - 8.5*s, ghx + 8.5*s, ghy + 8.5*s, outline=ghost_color, fill=ghost_color, width=gw)
                self.canvas.create_line(gneck_x, gneck_y, gpelvis_x, gpelvis_y, fill=ghost_color, width=gw)
                self.canvas.create_line(gneck_x, gneck_y, cx - offset_x - 14*s, gy - 28*s, fill=ghost_color, width=gw)
                self.canvas.create_line(gneck_x, gneck_y, cx - offset_x + 14*s, gy - 28*s, fill=ghost_color, width=gw)
                self.canvas.create_line(gpelvis_x, gpelvis_y, glf_x, gy, fill=ghost_color, width=gw)
                self.canvas.create_line(gpelvis_x, gpelvis_y, grf_x, gy, fill=ghost_color, width=gw)

        hx, hy, neck_x, neck_y, pelvis_x, pelvis_y = 0, -(52 * s), 0, -(42 * s), 0, -(18 * s)
        l_foot_x, l_foot_y, r_foot_x, r_foot_y = -(11 * s), 0, (11 * s), 0
        l_hand_x, l_hand_y, r_hand_x, r_hand_y = -(14 * s), -(28 * s), (14 * s), -(28 * s)
        if self.state == "GRABBED":
            wave = self.anim_time * 0.55
            l_foot_x, r_foot_x = -(8 * s) + math.sin(wave)*7, (8 * s) - math.sin(wave)*7
            l_foot_y, r_foot_y = (8 * s), (8 * s)
            l_hand_y, r_hand_y = -(42 * s) + math.cos(wave)*4, -(42 * s) - math.cos(wave)*4
        elif self.state == "FALLING" or abs(self.vy) > 2:
            l_foot_y, r_foot_y = -(6 * s), -(4 * s)
            l_hand_y, r_hand_y = -(42 * s), -(42 * s)
        elif self.state == "WANDER" and self.vx != 0:
            wave = self.anim_time * (0.7 if self.is_sonic else 0.22)
            l_foot_x, r_foot_x = math.sin(wave) * (12 * s if self.is_sonic else 9 * s), -math.sin(wave) * (12 * s if self.is_sonic else 9 * s)
            if self.is_sonic:
                run_dir = 1 if self.vx > 0 else -1
                hx += 8 * s * run_dir
                neck_x += 5 * s * run_dir
                l_hand_x, r_hand_x = -(18 * s) * run_dir, -(10 * s) * run_dir

        ghx, ghy = hx + cx, hy + cy
        gneck_x, gneck_y = neck_x + cx, neck_y + cy
        gpelvis_x, gpelvis_y = pelvis_x + cx, pelvis_y + cy
        glf_x, glf_y = l_foot_x + cx, l_foot_y + cy
        grf_x, grf_y = r_foot_x + cx, r_foot_y + cy
        glh_x, glh_y = l_hand_x + cx, l_hand_y + cy
        grh_x, grh_y = r_hand_x + cx, r_hand_y + cy
        head_r = 8.5 * s
        self.canvas.create_oval(ghx - head_r, ghy - head_r, ghx + head_r, ghy + head_r, outline=color, fill=color, width=w)
        self.canvas.create_line(gneck_x, gneck_y, gpelvis_x, gpelvis_y, fill=color, width=w)
        self.canvas.create_line(gneck_x, gneck_y, glh_x, glh_y, fill=color, width=w)
        self.canvas.create_line(gneck_x, gneck_y, grh_x, grh_y, fill=color, width=w)
        self.canvas.create_line(gpelvis_x, gpelvis_y, glf_x, glf_y, fill=color, width=w)
        self.canvas.create_line(gpelvis_x, gpelvis_y, grf_x, grf_y, fill=color, width=w)

if __name__ == "__main__":
    AvABlueEngine()
