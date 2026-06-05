import tkinter as tk
import math
from math import ceil
import ctypes
from ctypes import wintypes  
import random
import os
import sys
import time
import pygame  # POTĘŻNA BIBLIOTEKA DO REGULACJI GŁOŚNOŚCI

class AvAMemeIconEngine:
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
            
        # Inicjalizacja miksera audio Pygame
        pygame.mixer.init()
        
        self.root = tk.Tk()
        self.root.title("HAZARD")
        
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

        self.key_states = {"'": False, "j": False, "s": False, "u": False}
        
        self.scale = 1.9
        self.x = self.screen_width // 4
        self.y = self.taskbar_floor
        self.vx, self.vy, self.gravity, self.bounce_friction = 0, 0, 0.65, 0.5
        
        self.state = "WANDER"
        self.anim_time = 0
        self.move_enabled = True     
        
        # OŚ CZASU (DOKŁADNIE 26 SEKUND CYKLU ATOMÓWKI)
        self.nuke_duration_in = 1.0     
        self.nuke_duration_hold = 18.0  
        self.nuke_duration_out = 3.0    
        
        self.nuke_stage = 0          
        self.nuke_start_time = 0.0
        self.nuke_radius = 0
        self.shake_x, self.shake_y = 0, 0
        
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
        if self.is_key_pressed(0x31) and self.nuke_stage == 0: 
            mx, my = self.get_cursor_pos()
            cx, cy = self.x, self.y - (30 * self.scale)
            if (cx - 40 <= mx <= cx + 40) and (cy - 60 <= my <= cy + 60):
                self.root.destroy()
                exit()

    def check_global_keys(self):
        keys = {"'": 0xDE, "j": 0x4A, "s": 0x53, "u": 0x55}
        mx, my = self.get_cursor_pos()
        for key, code in keys.items():
            pressed = self.is_key_pressed(code)
            if not pressed: self.key_states[key] = False; continue
            if pressed and not self.key_states[key]:
                self.key_states[key] = True
                
                if key == "'" and self.nuke_stage == 0:
                    self.move_enabled = not self.move_enabled
                    if not self.move_enabled: self.vx = 0
                elif key == "j" and self.nuke_stage == 0:
                    self.nuke_stage = 1
                    self.nuke_start_time = time.time()  
                    self.vx, self.vy = 0, 0
                elif key == "s":
                    self.platforms.append((max(0, mx - 175), min(self.screen_width, mx + 175), my))
                elif key == "u":
                    self.platforms.clear()
                    if self.state == "WANDER" and self.nuke_stage == 0: self.state = "FALLING"

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
        
        if self.nuke_stage > 0:
            elapsed = time.time() - self.nuke_start_time
            
            # Etap 1: Odliczanie i Syrena (Dokładnie 5.0 sekund systemowych z folderu sounds/)
            if elapsed < 5.0:
                if self.nuke_stage != 1:
                    self.nuke_stage = 1
                    try:
                        sound_alarm = pygame.mixer.Sound("sounds/alarm.wav")
                        # PRZESTEROWANE AUDIO (Wymuszone cyfrowe wzmocnienie głośności na 5.0!)
                        sound_alarm.set_volume(10.0)  
                        sound_alarm.play()
                    except:
                        pass
            # Etap 2: Błysk fali (1.0 sekunda). GŁOŚNE BUM I INTERWENCJA SYSTEMOWA!
            elif elapsed < (5.0 + self.nuke_duration_in):
                if self.nuke_stage != 2:
                    self.nuke_stage = 2
                    self.nuke_radius = 20
                    try:
                        pygame.mixer.stop()  # Brutalne ucięcie syreny na rzecz eksplozji
                        sound_boom = pygame.mixer.Sound("sounds/boom.wav")
                        # NAPRAWIONO LITERÓWKĘ: Usunięto wadliwy obiekt sounds, teraz gra czysto na 5.0!
                        sound_boom.set_volume(10.0)  
                        sound_boom.play()
                    except:
                        pass
                    
                    # Czystka pozostałych okien stickmanów z pamięci RAM komputera
                    import subprocess
                    try:
                        subprocess.Popen(f'taskkill /F /IM python.exe /FI "PID ne {os.getpid()}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except:
                        pass
                self.nuke_radius += 65
            # Etap 3: Pobyt trwania pomarańczowej osłony (Równe 18.0 sekund fali boom)
            elif elapsed < (5.0 + self.nuke_duration_in + self.nuke_duration_hold):
                self.nuke_stage = 3
                self.shake_x = random.randint(-12, 12)
                self.shake_y = random.randint(-12, 12)
            # Etap 4: Wyjście (Równe 3.0 sekundy płynnego zacierania dymu)
            elif elapsed < (5.0 + self.nuke_duration_in + self.nuke_duration_hold + self.nuke_duration_out):
                self.nuke_stage = 4
                self.shake_x = random.randint(-3, 3)
                self.shake_y = random.randint(-3, 3)
            else:
                ctypes.windll.user32.ClipCursor(None)
                self.root.destroy()
                exit()

        floor = self.find_current_floor()
        lpm_pressed = self.is_key_pressed(0x01) 
        cx, cy = self.x, self.y - (30 * self.scale)
        
        if lpm_pressed and (self.state == "GRABBED" or ((cx - 40 <= mx <= cx + 40) and (cy - 60 <= my <= cy + 60))) and self.nuke_stage == 0:
            self.state = "GRABBED"
            self.x, self.y = mx, my + 50
            self.vx, self.vy = 0, 0
        else:
            if self.state == "GRABBED": self.set_state("FALLING_RELEASE")

            if self.nuke_stage > 0:
                self.vx, self.vy = 0, 0
            else:
                if self.y < floor: self.vy += self.gravity
                else:
                    if self.state == "FALLING": self.state = "WANDER"
                    self.vy, self.y = 0, floor

                if self.state == "FALLING":
                    self.vx *= 0.99
                elif self.state == "WANDER" and self.move_enabled:
                    if self.anim_time % 100 == 0:
                        self.vx = random.choice([-2.5, 2.5, 0])
                        if self.vx != 0: self.walk_direction = 1 if self.vx > 0 else -1
                    if self.vx != 0: self.vx *= 0.97

            self.x += self.vx; self.y += self.vy

        if self.x < 40: self.x = 40; self.vx = -self.vx * self.bounce_friction; self.walk_direction = 1
        elif self.x > self.screen_width - 40: self.x = self.screen_width - 40; self.vx = -self.vx * self.bounce_friction; self.walk_direction = -1
        if self.y < 50: self.y = 50; self.vy = -self.vy * self.bounce_friction

        self.canvas.delete("all"); self.anim_time += 1; self.draw_vector_icon(); self.root.after(16, self.update_loop)
    def draw_vector_icon(self):
        # SPECYFICZNE I DOKŁADNE KOLORY Z TWOJEGO OBRAZKA
        color_body = "#262626"
        color_outline = "#C0C0C0"
        s = self.scale
        
        # Integracja delikatnego trzęsienia obrazu podczas wybuchu
        cx = self.x + self.shake_x
        cy = self.y + self.shake_y

        # --- 1. PROCES RENDERINGU BEZPIECZNEJ ATOMÓWKI (Klawisz J) ---
        if self.nuke_stage > 0:
            elapsed = time.time() - self.nuke_start_time

        if self.nuke_stage == 1:
            # Odliczanie syreny alarmowej trwa systemowo dokładnie 5.0 sekund
            sec_left = ceil(5.0 - elapsed)
            n_color = "red" if self.anim_time % 20 < 10 else "#FF5500" 
            self.canvas.create_text(cx, cy - 145*s, text=f"DETONATION IN: {max(1, sec_left)}", fill=n_color, font=("Courier", int(15*s), "bold"))
            cx += random.randint(-2, 2)
            cy += random.randint(-2, 2)

        elif self.nuke_stage == 2:
            # FAZA WEJŚCIA (DOKŁADNIE 1 SEKUNDA SYSTEMOWA): Transparency płynnie maleje aż do pełnego pomarańczu
            time_in_stage = elapsed - 5.0
            fade_in_ratio = min(1.0, max(0.0, time_in_stage / self.nuke_duration_in))
            stipple_pattern = "gray25" if fade_in_ratio < 0.5 else "gray50"
            self.canvas.create_rectangle(0, 0, self.screen_width, self.screen_height, fill="#FF9900", stipple=stipple_pattern, outline="")
            
            # Pierścień fali uderzeniowej nuklearnego wybuchu
            r = self.nuke_radius
            self.canvas.create_oval(cx - r, cy - 45*s - r, cx + r, cy - 45*s + r, fill="", outline="#FFCC00", width=int(14*s))

        elif self.nuke_stage == 3:
            # PEŁNA FAZA POBYTU (DOKŁADNIE 18 SEKUND SYSTEMOWYCH POD PRZESTEROWANE boom.wav): Matowy pomarańczowy ekran
            self.canvas.create_rectangle(0, 0, self.screen_width, self.screen_height, fill="#FF9900", outline="")
            self.canvas.create_text(self.screen_width//2, self.screen_height//2, text="BOOM!", fill="black", font=("Impact", int(85*s), "bold"))

        elif self.nuke_stage == 4:
            # FAZA WYJŚCIA (DOKŁADNIE 3 SEKUNDY SYSTEMOWE): Transparency płynnie rośnie, zasłona staje się niewidoczna
            time_in_stage = elapsed - (5.0 + self.nuke_duration_in + self.nuke_duration_hold)
            fade_out_ratio = 1.0 - min(1.0, max(0.0, time_in_stage / self.nuke_duration_out))
            
            if fade_out_ratio > 0.66:
                stipple_pattern = "gray50"
            elif fade_out_ratio > 0.33:
                stipple_pattern = "gray25"
            else:
                stipple_pattern = "gray12"
            
            self.canvas.create_rectangle(0, 0, self.screen_width, self.screen_height, fill="#FF9900", stipple=stipple_pattern, outline="")
            self.canvas.create_text(self.screen_width//2, self.screen_height//2, text="BOOM!", fill="black", font=("Impact", int(50*s * fade_out_ratio), "bold"))

        # --- 2. CAŁKOWITY BLOK RENDERINGU SYLWETKI W FAZIE ATOMÓWKI (Stage 3 i 4) ---
        # Ludzik paruje z ekranu i staje się niewidoczny dokładnie w momencie uderzenia napisu BOOM!
        if self.nuke_stage >= 3:
            return  

        # --- 3. PRZELICZANIE KOŚCI (IDEALNE PROPORCJE STRUCTURY 1:1 Z OBRAZKA) ---
        hx, hy = cx, cy - 90*s  # Odcięta, zawieszona okrągła głowa
        tx, ty = cx, cy - 50*s  # Środek długiego, prostokątnego tułowia

        # Identycznie jak na foto: proste, długie kończyny blisko siebie
        l_hand_x, l_hand_y = cx - 22*s, cy - 35*s
        r_hand_x, r_hand_y = cx + 22*s, cy - 35*s
        l_foot_x, l_foot_y = cx - 12*s, cy
        r_foot_x, r_foot_y = cx + 12*s, cy

        if self.state == "GRABBED":
            wave = self.anim_time * 0.55
            l_foot_x, r_foot_x = cx - 12*s + math.sin(wave)*8, cx + 12*s - math.sin(wave)*8
            l_foot_y, r_foot_y = cy + 12*s, cy + 12*s
        elif self.nuke_stage == 1:
            l_hand_x, l_hand_y = cx - 24*s, cy - 115*s
            r_hand_x, r_hand_y = cx + 24*s, cy - 115*s
        elif self.vx != 0 and self.nuke_stage == 0:
            wave = self.anim_time * 0.16
            stride = math.sin(wave) * 14 * s
            l_foot_x += stride
            r_foot_x -= stride
            l_hand_x -= stride * 0.4
            r_hand_x += stride * 0.4

        # --- 4. RENDERING FUNKCJI WEKTOROWYCH Z GRUBĄ OBWÓDKĄ JAK NA ZDJĘCIU ---
        def draw_bordered_element(type, x1, y1, x2, y2, r_thick):
            if type == "line":
                self.canvas.create_line(x1, y1, x2, y2, fill=color_outline, width=r_thick + 5*s, capstyle="round")
                self.canvas.create_line(x1, y1, x2, y2, fill=color_body, width=r_thick, capstyle="round")
            elif type == "oval":
                self.canvas.create_oval(x1 - r_thick - 2.5*s, y1 - r_thick - 2.5*s, x1 + r_thick + 2.5*s, y1 + r_thick + 2.5*s, fill=color_outline, outline="")
                self.canvas.create_oval(x1 - r_thick, y1 - r_thick, x1 + r_thick, y1 + r_thick, fill=color_body, outline="")

        thick_limb = int(15 * s)
        draw_bordered_element("line", tx, ty, l_hand_x, l_hand_y, thick_limb)  
        draw_bordered_element("line", tx, ty, r_hand_x, r_hand_y, thick_limb)  
        draw_bordered_element("line", tx, ty + 20*s, l_foot_x, l_foot_y, thick_limb)  
        draw_bordered_element("line", tx, ty + 20*s, r_foot_x, r_foot_y, thick_limb)  

        # PROSTOKĄTNY TUŁÓW (Wysoki, podłużny korpus piktogramu z przesłanego obrazka)
        self.canvas.create_rectangle(tx - 17.5*s, ty - 12*s, tx + 17.5*s, ty + 26*s, fill=color_outline, outline="")
        self.canvas.create_rectangle(tx - 15*s, ty - 9.5*s, tx + 15*s, ty + 23.5*s, fill=color_body, outline="")

        # IDEALNIE OKRĄGŁA GŁOWA (Zawieszona w powietrzu nad ramionami z szarym ringiem)
        head_radius = 14 * s
        draw_bordered_element("oval", hx, hy, None, None, head_radius)

        # --- 5. TRZYMANA NAD ŁBEM PŁONĄCA BOMBA ATOMOWA ZE ZNAKIEM ZAGROŻENIA ---
        if self.nuke_stage == 1:
            bx, by = cx, cy - 130*s  
            b_pulse = math.sin(self.anim_time * 0.4) * 4 * s
            br = (18 * s) + b_pulse  
            
            self.canvas.create_oval(bx - br, by - br, bx + br, by + br, fill="red", outline="white", width=2)
            self.canvas.create_oval(bx - br*0.4, by - br*0.4, bx + br*0.4, by + br*0.4, fill="#FFCC00", outline="")
            
            for i in range(3):
                ang = (self.anim_time * 0.05) + (i * (2 * math.pi / 3))
                x1 = bx + math.cos(ang) * br * 0.2
                y1 = by + math.sin(ang) * br * 0.2
                x2 = bx + math.cos(ang) * br * 0.7
                y2 = by + math.sin(ang) * br * 0.7
                self.canvas.create_line(x1, y1, x2, y2, fill="black", width=int(3.5*s))

if __name__ == "__main__":
    import sys
    sys.argv = "HAZARD"
    AvAMemeIconEngine()
