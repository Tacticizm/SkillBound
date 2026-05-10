"""
titlescreen.py — Animated title screen & main menu
"""
import pygame
import math
import random
from constants import SCREEN_W, SCREEN_H
from renderer import (StarField, draw_text_shadow, draw_panel,
                      GOLD, DARK_GOLD, DEEP_BLUE, PANEL_COL, PANEL_EDGE,
                      SKY_TOP, SKY_BOT, lerp_color, CRIMSON)

WHITE  = (255, 255, 255)
GRAY   = (160, 160, 180)
BLACK  = (0, 0, 0)


class TitleScreen:
    MENU_ITEMS = ["New Game", "Controls", "Quit"]

    def __init__(self):
        self.stars   = StarField(250)
        self.cursor  = 0
        self.tick    = 0
        self.state   = "title"     # "title" | "controls"
        self.done    = False
        self.action  = None        # "start" | "quit"
        self.particles = []
        self._spawn_ambient()

        # Pre-render title glyphs
        self.font_title = pygame.font.SysFont("Georgia", 72, bold=True)
        self.font_sub   = pygame.font.SysFont("Georgia", 26, italic=True)
        self.font_menu  = pygame.font.SysFont("Arial",   32, bold=True)
        self.font_small = pygame.font.SysFont("Arial",   20)

    def _spawn_ambient(self):
        for _ in range(40):
            self.particles.append({
                "x": random.randint(0, SCREEN_W),
                "y": random.randint(0, SCREEN_H),
                "vy": random.uniform(-0.3, -0.8),
                "vx": random.uniform(-0.2, 0.2),
                "life": random.randint(60, 200),
                "max": random.randint(60, 200),
                "col": random.choice([(255,210,50),(180,140,20),(200,200,255),(100,200,255)]),
                "size": random.uniform(1.0, 2.5),
            })

    def _update_particles(self):
        alive = []
        for p in self.particles:
            p["x"] += p["vx"]; p["y"] += p["vy"]; p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
            else:
                # respawn
                alive.append({
                    "x": random.randint(0, SCREEN_W),
                    "y": SCREEN_H + 10,
                    "vy": random.uniform(-0.3, -0.8),
                    "vx": random.uniform(-0.2, 0.2),
                    "life": random.randint(80, 220),
                    "max": random.randint(80, 220),
                    "col": random.choice([(255,210,50),(180,140,20),(200,200,255),(100,200,255)]),
                    "size": random.uniform(1.0, 2.5),
                })
        self.particles = alive

    def _menu_item_rect(self, i):
        panel_w = 320
        px = SCREEN_W//2 - panel_w//2
        py = 300
        return (px+10, py + 26 + i*56 - 4, panel_w-20, 44)

    def handle_event(self, event):
        if self.state == "controls":
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                self.state = "title"
            return

        # Mouse / touch click on menu items
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            if event.type == pygame.FINGERDOWN:
                pos = (int(event.x * SCREEN_W), int(event.y * SCREEN_H))
            else:
                pos = event.pos
            for i in range(len(self.MENU_ITEMS)):
                rx, ry, rw, rh = self._menu_item_rect(i)
                if rx <= pos[0] <= rx+rw and ry <= pos[1] <= ry+rh:
                    self.cursor = i
                    self._select()
                    return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.cursor = (self.cursor - 1) % len(self.MENU_ITEMS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.cursor = (self.cursor + 1) % len(self.MENU_ITEMS)
            elif event.key in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE):
                self._select()

    def _select(self):
        item = self.MENU_ITEMS[self.cursor]
        if item == "New Game":
            self.done   = True
            self.action = "start"
        elif item == "Controls":
            self.state = "controls"
        elif item == "Quit":
            self.done   = True
            self.action = "quit"

    def update(self):
        self.tick += 1
        self.stars.update()
        self._update_particles()

    def draw(self, surf):
        # Sky gradient
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            col = lerp_color(SKY_TOP, SKY_BOT, t)
            pygame.draw.line(surf, col, (0, y), (SCREEN_W, y))

        self.stars.draw(surf)
        self._draw_particles(surf)

        if self.state == "controls":
            self._draw_controls(surf)
        else:
            self._draw_title(surf)
            self._draw_menu(surf)
            self._draw_footer(surf)

    def _draw_particles(self, surf):
        for p in self.particles:
            alpha = max(0, min(255, int(200 * (p["life"] / max(1, p["max"])))))
            size  = max(1, int(p["size"]))
            s = pygame.Surface((size*2+1, size*2+1), pygame.SRCALPHA)
            pygame.draw.circle(s, p["col"], (size, size), size)
            s.set_alpha(alpha)
            surf.blit(s, (int(p["x"])-size, int(p["y"])-size))

    def _draw_title(self, surf):
        t = self.tick
        # Glow pulse
        glow_alpha = int(60 + 40 * math.sin(t * 0.03))
        glow = pygame.Surface((600, 120), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*GOLD, glow_alpha), (0, 0, 600, 120))
        surf.blit(glow, (SCREEN_W//2 - 300, 80), special_flags=pygame.BLEND_ADD)

        # Title text with shimmer
        shimmer = int(210 + 45 * math.sin(t * 0.04))
        title_col = (shimmer, int(shimmer*0.82), 40)

        # Line decoration
        deco_y = 72
        pygame.draw.line(surf, DARK_GOLD, (SCREEN_W//2-260, deco_y), (SCREEN_W//2-10, deco_y), 2)
        pygame.draw.line(surf, DARK_GOLD, (SCREEN_W//2+10,  deco_y), (SCREEN_W//2+260, deco_y), 2)
        pygame.draw.circle(surf, GOLD, (SCREEN_W//2, deco_y), 5)

        draw_text_shadow(surf, "SKILL", self.font_title, title_col,
                         SCREEN_W//2 - 160, 78, shadow_col=(0,0,0), offset=4)
        draw_text_shadow(surf, "BOUND", self.font_title, title_col,
                         SCREEN_W//2 - 170, 148, shadow_col=(0,0,0), offset=4)

        # Subtitle with flicker
        sub_alpha = int(180 + 40 * math.sin(t * 0.05))
        sub_surf = self.font_sub.render("Master Every Skill. Conquer Every Quest.", True, (180,160,255))
        sub_surf.set_alpha(sub_alpha)
        surf.blit(sub_surf, (SCREEN_W//2 - sub_surf.get_width()//2, 230))

        # Decorative bottom line
        deco_y2 = 260
        pygame.draw.line(surf, DARK_GOLD, (SCREEN_W//2-200, deco_y2), (SCREEN_W//2+200, deco_y2), 1)

    def _draw_menu(self, surf):
        t = self.tick
        panel_w, panel_h = 320, 200
        px = SCREEN_W//2 - panel_w//2
        py = 300
        draw_panel(surf, px, py, panel_w, panel_h, alpha=200, radius=12)

        for i, item in enumerate(self.MENU_ITEMS):
            iy = py + 26 + i * 56
            selected = (i == self.cursor)

            if selected:
                # Animated selection highlight
                pulse = int(30 + 20 * math.sin(t * 0.08))
                highlight = pygame.Surface((panel_w - 20, 44), pygame.SRCALPHA)
                pygame.draw.rect(highlight, (GOLD[0]//4, GOLD[1]//4, 0, 160+pulse),
                                 (0,0,panel_w-20,44), border_radius=8)
                pygame.draw.rect(highlight, (*GOLD, 200),
                                 (0,0,panel_w-20,44), 2, border_radius=8)
                surf.blit(highlight, (px+10, iy-4))

                # Arrow indicator
                ax = px + 20 + int(4 * math.sin(t * 0.1))
                draw_text_shadow(surf, "▶", self.font_menu, GOLD, ax, iy, offset=2)
                draw_text_shadow(surf, item, self.font_menu, WHITE, px+52, iy, offset=2)
            else:
                draw_text_shadow(surf, item, self.font_menu, GRAY, px+52, iy,
                                 shadow_col=(0,0,0), offset=2)

    def _draw_footer(self, surf):
        t = self.tick
        blink = int(180 + 60 * math.sin(t * 0.06))
        hint = self.font_small.render("↑↓ Navigate   ENTER Select", True, (blink, blink, blink))
        surf.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 40))

        ver = self.font_small.render("v1.0  |  © 2026 SkillBound Studios", True, (80,80,100))
        surf.blit(ver, (SCREEN_W//2 - ver.get_width()//2, SCREEN_H - 20))

    def _draw_controls(self, surf):
        # Sky gradient (same)
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            col = lerp_color(SKY_TOP, SKY_BOT, t)
            pygame.draw.line(surf, col, (0, y), (SCREEN_W, y))
        self.stars.draw(surf)

        pw, ph = 620, 460
        px, py = SCREEN_W//2 - pw//2, SCREEN_H//2 - ph//2
        draw_panel(surf, px, py, pw, ph, alpha=240, radius=14)

        font_h = pygame.font.SysFont("Georgia", 32, bold=True)
        font_b = pygame.font.SysFont("Arial",   22, bold=True)
        font_s = pygame.font.SysFont("Arial",   20)

        draw_text_shadow(surf, "Controls", font_h, GOLD,
                         SCREEN_W//2 - 60, py+14, offset=3)
        pygame.draw.line(surf, DARK_GOLD, (px+16, py+54), (px+pw-16, py+54), 1)

        controls = [
            ("Movement",   "WASD  /  Arrow Keys"),
            ("Interact",   "E  —  Talk · Gather · Attack"),
            ("Inventory",  "I"),
            ("Skills",     "K"),
            ("Quest Log",  "Q"),
            ("Combat",     ""),
            ("  Attack",   "ENTER / Z"),
            ("  Use Item", "ENTER (in Item menu)"),
            ("  Run",      "Select Run, then ENTER"),
            ("Menus",      "ESC  —  Close any menu"),
        ]
        for i, (key, val) in enumerate(controls):
            cy2 = py + 66 + i * 36
            is_header = val == ""
            col_k = GOLD if is_header else (180, 180, 220)
            col_v = WHITE
            draw_text_shadow(surf, key, font_b if is_header else font_s, col_k, px+24, cy2, offset=1)
            if val:
                draw_text_shadow(surf, val, font_s, col_v, px+280, cy2, offset=1)

        hint = font_s.render("Press any key to return", True, GRAY)
        surf.blit(hint, (SCREEN_W//2 - hint.get_width()//2, py+ph-34))
