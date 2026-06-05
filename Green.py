import tkinter as tk
import math
import ctypes
import random

class AvAGreenEngine:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        self.root = tk.Tk()
        self.root.title("AvA Green")
        
        self.box_size = 140
        self.half_box = self.box_size // 2
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.taskbar_floor = self.screen_height - 40  
        
        self.root.geometry(f"{self.box_size}x{self.box_size}+{self.screen_width//2}+{self.taskbar_floor - self.box_size}")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        
        self.trans_color = "#010101"
        self.root.wm_attributes("-transparentcolor", self.trans_color)
        self.canvas = tk.Canvas(self.root, width=self.box_size, height=self.box_size, bg=self.trans_color, highlightthickness=0)
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", lambda e: self.set_state("GRABBED"))
        self.canvas.bind("<ButtonRelease-1>", lambda e: self.set_state("FALLING_RELEASE"))

        self.key_states = {"y": False, "s": False, "u": False}
        self.scale, self.x, self.y = 1.4, self.screen_width // 2, self.taskbar_floor
        self.vx, self.vy, self.gravity, self.bounce_friction = 0, 0, 0.65, 0.5
        self.state, self.anim_time, self.has_phone, self.trip_timer = "WANDER", 0, False, 0
        self.walk_direction = 1  
        self.last_mx, self.last_my = 0, 0
        self.mouse_vx, self.mouse_vy = 0, 0
        self.platforms = []
        self.update_loop()
        self.root.mainloop()

    def set_state(self, new_state):
        if new_state == "GRABBED":
            self.state, self.vx, self.vy, self.trip_timer = "GRABBED", 0, 0, 0
        elif new_state == "FALLING_RELEASE":
            self.state = "FALLING"
            self.vx, self.vy = self.mouse_vx * 0.85, self.mouse_vy * 0.85

    def is_key_pressed(self, key_code):
        return (ctypes.windll.user32.GetAsyncKeyState(key_code) & 0x8000) != 0

    def check_laser_collision(self):
        if self.is_key_pressed(0x31): 
            mx, my = self.get_cursor_pos()
            cx, cy = self.x, self.y - (25 * self.scale)
            if (cx - 30 <= mx <= cx + 30) and (cy - 45 <= my <= cy + 45):
                self.root.destroy()
                exit()

    def check_global_keys(self):
        keys = {"y": 0x59, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            if not pressed: self.key_states[key] = False; continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                if key == "y":
                    self.has_phone = not self.has_phone
                    if self.has_phone and self.state == "WANDER": self.vx = self.walk_direction * 1.8
                elif key == "s": self.platforms.append((max(0, mx - 175), min(self.screen_width, mx + 175), my))
                elif key == "u": 
                    self.platforms.clear()
                    if self.state == "WANDER": self.state = "FALLING"

    def get_cursor_pos(self):
        class POINT(ctypes.Structure): _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT(); ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def update_loop(self):
        self.check_global_keys(); self.check_laser_collision()
        mx, my = self.get_cursor_pos()
        self.mouse_vx, self.mouse_vy = mx - self.last_mx, my - self.last_my
        self.last_mx, self.last_my = mx, my
        
        # WPISANY OD NOWA Z ODPOWIEDNIKIEM TSC POPRAWNY WARUNEK PLATFORM
        current_floor = self.taskbar_floor
        for left, right, top in self.platforms:
            if left <= self.x <= right:
                tolerance = max(6.0, abs(self.vy) + 2)
                if top - 3 <= self.y <= top + tolerance:
                    if top < current_floor:
                        current_floor = top

        if self.state == "GRABBED":
            self.x, self.y = mx, my + 45
        else:
            if self.y < current_floor: self.vy += self.gravity
            else:
                if self.state == "FALLING" or self.state == "TRIP": self.state = "WANDER"
                self.vy, self.y = 0, current_floor
            if self.state == "FALLING":
                self.vx *= 0.99
            elif self.state == "TRIP":
                self.trip_timer -= 1
                if self.trip_timer <= 0: self.state = "WANDER"
            elif self.state == "WANDER":
                if self.has_phone: self.vx = self.walk_direction * 1.8
                else:
                    if self.anim_time % 130 == 0: 
                        self.vx = random.choice([-2.0, 2.0, 0])
                        if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                    if self.vx != 0: self.vx *= 0.96
            self.x += self.vx; self.y += self.vy
            if self.x < 35:
                self.x = 35
                if self.has_phone and self.state != "TRIP": self.state, self.trip_timer, self.vx, self.vy, self.walk_direction = "TRIP", 35, 4.0, -3.5, 1
                else: self.vx = -self.vx * self.bounce_friction; self.walk_direction = 1
            elif self.x > self.screen_width - 35:
                self.x = self.screen_width - 35
                if self.has_phone and self.state != "TRIP": self.state, self.trip_timer, self.vx, self.vy, self.walk_direction = "TRIP", 35, -4.0, -3.5, -1
                else: self.vx = -self.vx * self.bounce_friction; self.walk_direction = -1
            if self.y < 40: self.y = 40; self.vy = -self.vy * self.bounce_friction
        self.root.geometry(f"+{int(self.x - self.half_box)}+{int(self.y - self.box_size)}")
        self.canvas.delete("all"); self.anim_time += 1; self.draw_vector_green(); self.root.after(16, self.update_loop)

    def draw_vector_green(self):
        color, w, s = "#00FF00", 4, self.scale # PRZYWRÓCONY ORYGINALNY JASKRAWY ZIELONY
        cx, cy = self.half_box, self.box_size - 2
        hx, hy, neck_x, neck_y, pelvis_x, pelvis_y = 0, -(52 * s), 0, -(42 * s), 0, -(18 * s)
        l_foot_x, l_foot_y, r_foot_x, r_foot_y = -(11 * s), 0, (11 * s), 0
        l_hand_x, l_hand_y, r_hand_x, r_hand_y = -(14 * s), -(28 * s), (14 * s), -(28 * s)
        if self.state == "GRABBED":
            wave = self.anim_time * 0.55
            l_foot_x, r_foot_x = -(8 * s) + math.sin(wave)*7, (8 * s) - math.sin(wave)*7
            l_foot_y, r_foot_y = (8 * s), (8 * s)
            l_hand_y, r_hand_y = -(42 * s) + math.cos(wave)*4, -(42 * s) - math.cos(wave)*4
        elif self.state == "TRIP":
            hy = -(46 * s)
            neck_x, neck_y = -(10 * s) * self.walk_direction, -(38 * s)
            pelvis_x, pelvis_y = -(5 * s) * self.walk_direction, -(16 * s)
            l_hand_x, l_hand_y = -(18 * s) * self.walk_direction, -(55 * s)
            r_hand_x, r_hand_y = (5 * s) * self.walk_direction, -(58 * s)
            l_foot_y, r_foot_y = -(4 * s), -(8 * s)
            phone_w = math.sin(self.anim_time * 0.4) * 15 * s
            px, py = cx - (30 * s) * self.walk_direction, cy - (60 * s) + phone_w
            self.canvas.create_rectangle(px - 3, py - 5, px + 3, py + 5, outline="#FFFFFF", fill="#444444", width=2)
        elif self.state == "FALLING" or abs(self.vy) > 2:
            l_foot_y, r_foot_y = -(6 * s), -(4 * s)
            l_hand_y, r_hand_y = -(42 * s), -(42 * s)
        elif self.state == "WANDER":
            if self.has_phone:
                hy = -(48 * s)
                l_hand_x, r_hand_x = (8 * s) * self.walk_direction, (12 * s) * self.walk_direction
                l_hand_y, r_hand_y = -(34 * s), -(34 * s)
                ph_x, ph_y = cx + (15 * s) * self.walk_direction, cy - (34 * s)
                self.canvas.create_rectangle(ph_x - 2, ph_y - 4, ph_x + 2, ph_y + 4, outline="#FFFFFF", fill="#333333", width=1.5)
                self.canvas.create_oval(ph_x - 5, ph_y - 5, ph_x + 5, ph_y + 5, outline="#00FFFF", width=1)
                wave = self.anim_time * 0.2
                l_foot_x, r_foot_x = math.sin(wave) * 6 * s, -math.sin(wave) * 6 * s
            elif self.vx != 0:
                wave = self.anim_time * 0.22
                l_foot_x, r_foot_x = math.sin(wave) * 9 * s, -math.sin(wave) * 9 * s
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
    AvAGreenEngine()
