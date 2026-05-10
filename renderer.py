"""
renderer.py — Visual effects engine
Handles: particles, floating text, screen shake, transitions, draw utilities
"""
import pygame
import math
import random
from constants import *


# ── Palette ──────────────────────────────────────────────────────────────────
GOLD        = (255, 210, 50)
DARK_GOLD   = (180, 140, 20)
CRIMSON     = (200, 30, 50)
NEON_GREEN  = (50, 255, 100)
DEEP_BLUE   = (10, 12, 30)
PANEL_COL   = (18, 20, 40)
PANEL_EDGE  = (60, 70, 120)
HP_HIGH     = (60, 220, 80)
HP_MID      = (220, 200, 40)
HP_LOW      = (220, 50, 50)
XP_COL      = (100, 80, 220)
SKY_TOP     = (8, 10, 28)
SKY_BOT     = (20, 30, 60)


# ── Helpers ───────────────────────────────────────────────────────────────────
def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i]) * t) for i in range(3))

def draw_text_shadow(surf, text, font, color, x, y, shadow_col=(0,0,0), offset=2):
    s = font.render(text, True, shadow_col)
    surf.blit(s, (x+offset, y+offset))
    t = font.render(text, True, color)
    surf.blit(t, (x, y))
    return t.get_width(), t.get_height()

def draw_panel(surf, x, y, w, h, col=None, edge=None, alpha=220, radius=10):
    col  = col  or PANEL_COL
    edge = edge or PANEL_EDGE
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*col, alpha), (0, 0, w, h), border_radius=radius)
    pygame.draw.rect(panel, (*edge, 255),  (0, 0, w, h), 2, border_radius=radius)
    surf.blit(panel, (x, y))

def draw_bar(surf, x, y, w, h, ratio, high_col, low_col=None, bg_col=(40,10,10), radius=4):
    low_col = low_col or high_col
    t = max(0.0, min(1.0, ratio))
    col = lerp_color(low_col, high_col, t)
    pygame.draw.rect(surf, bg_col, (x, y, w, h), border_radius=radius)
    if t > 0:
        pygame.draw.rect(surf, col, (x, y, max(radius*2, int(w*t)), h), border_radius=radius)
    pygame.draw.rect(surf, (0,0,0,180), (x, y, w, h), 1, border_radius=radius)

def hp_color(ratio):
    if ratio > 0.5:
        return lerp_color(HP_MID, HP_HIGH, (ratio - 0.5) * 2)
    return lerp_color(HP_LOW, HP_MID, ratio * 2)

def glow_circle(surf, color, center, radius, strength=80):
    glow = pygame.Surface((radius*4, radius*4), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        alpha = int(strength * (1 - r/radius) * 0.4)
        pygame.draw.circle(glow, (*color, alpha), (radius*2, radius*2), r)
    surf.blit(glow, (center[0]-radius*2, center[1]-radius*2), special_flags=pygame.BLEND_ADD)


# ── Particles ─────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, vx, vy, color, life, size=3, fade=True, gravity=0.0):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.color  = color
        self.life   = life
        self.max_life = life
        self.size   = size
        self.fade   = fade
        self.gravity= gravity
        self.alive  = True

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += self.gravity
        self.vx *= 0.96
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        alpha = 255 if not self.fade else int(255 * (self.life / self.max_life))
        size  = max(1, int(self.size * (self.life / self.max_life)))
        s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, self.color, (size, size), size)
        s.set_alpha(alpha)
        surf.blit(s, (int(self.x)-size, int(self.y)-size))


class FloatingText:
    def __init__(self, x, y, text, color, size=24, life=80):
        self.x, self.y = float(x), float(y)
        self.text  = text
        self.color = color
        self.size  = size
        self.life  = life
        self.max_life = life
        self.alive = True
        self.vy    = -1.5

    def update(self):
        self.y  += self.vy
        self.vy *= 0.96
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        alpha = int(255 * (self.life / self.max_life))
        font  = pygame.font.SysFont("Arial", self.size, bold=True)
        img   = font.render(self.text, True, self.color)
        tmp   = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        tmp.blit(img, (0,0))
        tmp.set_alpha(alpha)
        # shadow
        sh = font.render(self.text, True, (0,0,0))
        sh_tmp = pygame.Surface(sh.get_size(), pygame.SRCALPHA)
        sh_tmp.blit(sh, (0,0))
        sh_tmp.set_alpha(alpha // 2)
        surf.blit(sh_tmp, (int(self.x) - img.get_width()//2 + 2, int(self.y) + 2))
        surf.blit(tmp,    (int(self.x) - img.get_width()//2,     int(self.y)))


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.texts     = []

    def burst(self, x, y, color, count=12, speed=3.0, size=4, gravity=0.08):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            s = random.uniform(0.5, speed)
            life = random.randint(25, 55)
            self.particles.append(Particle(x, y,
                math.cos(angle)*s, math.sin(angle)*s,
                color, life, size=size, gravity=gravity))

    def sparkle(self, x, y, color, count=6):
        for _ in range(count):
            vx = random.uniform(-1, 1)
            vy = random.uniform(-2.5, -0.5)
            self.particles.append(Particle(x + random.randint(-8,8), y,
                vx, vy, color, random.randint(20, 40), size=2, gravity=0.05))

    def damage_number(self, x, y, amount, is_player_hit=False):
        col = CRIMSON if is_player_hit else GOLD
        size = 30 if amount >= 10 else 24
        self.texts.append(FloatingText(x, y - 20, f"-{amount}", col, size=size, life=90))

    def xp_text(self, x, y, skill, amount):
        self.texts.append(FloatingText(x, y - 30, f"+{amount} {skill} XP",
                                       (180, 140, 255), size=18, life=120))

    def level_up_burst(self, x, y):
        self.burst(x, y, GOLD, count=30, speed=4.0, size=5)
        self.burst(x, y, WHITE, count=15, speed=2.0, size=3)
        self.texts.append(FloatingText(x, y - 50, "LEVEL UP!", GOLD, size=36, life=160))

    def update(self):
        self.particles = [p for p in self.particles if p.alive]
        self.texts     = [t for t in self.texts     if t.alive]
        for p in self.particles: p.update()
        for t in self.texts:     t.update()

    def draw(self, surf):
        for p in self.particles: p.draw(surf)
        for t in self.texts:     t.draw(surf)


# ── Screen shake ──────────────────────────────────────────────────────────────
class ScreenShake:
    def __init__(self):
        self.intensity = 0
        self.duration  = 0

    def shake(self, intensity=6, duration=12):
        self.intensity = max(self.intensity, intensity)
        self.duration  = max(self.duration, duration)

    def update(self):
        if self.duration > 0:
            self.duration -= 1
            if self.duration == 0:
                self.intensity = 0

    def offset(self):
        if self.duration > 0:
            t = self.duration / 12
            ox = random.randint(-int(self.intensity*t), int(self.intensity*t))
            oy = random.randint(-int(self.intensity*t), int(self.intensity*t))
            return ox, oy
        return 0, 0


# ── Transition ────────────────────────────────────────────────────────────────
class Transition:
    def __init__(self):
        self.alpha   = 0
        self.fading  = None   # "in" | "out"
        self.speed   = 8
        self.done    = True
        self.callback= None

    def fade_out(self, callback=None, speed=8):
        self.alpha    = 0
        self.fading   = "out"
        self.speed    = speed
        self.done     = False
        self.callback = callback

    def fade_in(self, speed=8):
        self.alpha  = 255
        self.fading = "in"
        self.speed  = speed
        self.done   = False

    def update(self):
        if self.fading == "out":
            self.alpha = min(255, self.alpha + self.speed)
            if self.alpha >= 255:
                self.done = True
                if self.callback:
                    self.callback()
                    self.callback = None
        elif self.fading == "in":
            self.alpha = max(0, self.alpha - self.speed)
            if self.alpha <= 0:
                self.done = True
                self.fading = None

    def draw(self, surf):
        if self.alpha > 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(self.alpha)
            surf.blit(overlay, (0, 0))


# ── Vignette ──────────────────────────────────────────────────────────────────
_vignette_cache = None
def draw_vignette(surf, strength=160):
    global _vignette_cache
    if _vignette_cache is None or _vignette_cache.get_size() != (SCREEN_W, SCREEN_H):
        _vignette_cache = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        cx, cy = SCREEN_W//2, SCREEN_H//2
        max_r = math.hypot(cx, cy)
        for r in range(int(max_r), 0, -4):
            alpha = int(strength * (r / max_r) ** 2.2)
            pygame.draw.circle(_vignette_cache, (0,0,0, min(255,alpha)), (cx, cy), r, 4)
    surf.blit(_vignette_cache, (0,0))


# ── Animated background (title screen) ───────────────────────────────────────
class StarField:
    def __init__(self, count=200):
        self.stars = [
            [random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
             random.uniform(0.2, 1.5), random.uniform(0.1, 0.5)]
            for _ in range(count)
        ]
        self.t = 0

    def update(self):
        self.t += 1
        for s in self.stars:
            s[0] -= s[3]
            if s[0] < 0:
                s[0] = SCREEN_W
                s[1] = random.randint(0, SCREEN_H)

    def draw(self, surf):
        for x, y, size, speed in self.stars:
            alpha = int(120 + 80 * math.sin(self.t * 0.02 + x * 0.01))
            brightness = int(150 + 80 * (speed / 0.5))
            col = (min(255, brightness), min(255, brightness), min(255, brightness+30))
            r = max(1, int(size))
            pygame.draw.circle(surf, col, (int(x), int(y)), r)


# ── Tile sprite renderer (better looking tiles) ───────────────────────────────
_tile_cache = {}

TILE_PALETTES = {
    TILE_GRASS: [(34,85,34), (28,75,28), (40,95,40), (45,100,35)],
    TILE_PATH:  [(160,130,80),(150,120,70),(170,140,90)],
    TILE_SAND:  [(210,190,120),(200,180,110),(220,200,130)],
    TILE_FLOOR: [(90,70,50),(80,60,40),(100,80,55)],
    TILE_WATER: [(20,50,140),(25,55,150),(15,45,130)],
}

def get_tile_surf(tid, tick=0):
    key = (tid, tick // 20 if tid == TILE_WATER else 0)
    if key in _tile_cache:
        return _tile_cache[key]

    s = pygame.Surface((TILE_SIZE, TILE_SIZE))
    if tid in TILE_PALETTES:
        pal = TILE_PALETTES[tid]
        base = pal[0]
        s.fill(base)
        rng = random.Random(tid * 7 + key[1])
        for _ in range(20):
            col = rng.choice(pal)
            rx = rng.randint(0, TILE_SIZE-4)
            ry = rng.randint(0, TILE_SIZE-4)
            pygame.draw.rect(s, col, (rx, ry, rng.randint(2,6), rng.randint(2,6)))
    elif tid == TILE_TREE:
        s.fill((28,75,28))
        pygame.draw.circle(s, (20,100,20), (TILE_SIZE//2, TILE_SIZE//2), 14)
        pygame.draw.circle(s, (30,120,30), (TILE_SIZE//2-3, TILE_SIZE//2-3), 8)
        pygame.draw.rect(s, (90,55,20), (TILE_SIZE//2-3, TILE_SIZE-10, 6, 10))
    elif tid == TILE_ROCK:
        s.fill((28,75,28))
        pygame.draw.ellipse(s, (80,80,90), (4,8,24,18))
        pygame.draw.ellipse(s, (100,100,110),(6,10,20,14))
        pygame.draw.line(s, (130,130,140),(9,13),(19,13),2)
    elif tid == TILE_WALL:
        s.fill((50,52,60))
        for row in range(2):
            offset = (row % 2) * 8
            for col in range(3):
                bx = offset + col*14 - 2
                by = row*12 + 4
                pygame.draw.rect(s, (70,72,82),(bx,by,12,9))
                pygame.draw.rect(s, (35,37,45),(bx,by,12,9),1)
    elif tid == TILE_FLOOR:
        s.fill((85,65,45))
        rng = random.Random(13)
        for _ in range(6):
            pygame.draw.rect(s,(95,75,50),(rng.randint(0,28),rng.randint(0,28),4,4))
    elif tid == TILE_DOOR:
        s.fill((110,75,35))
        pygame.draw.rect(s,(80,50,20),(4,2,24,28))
        pygame.draw.circle(s,(200,170,50),(22,16),3)
        pygame.draw.line(s,(60,35,10),(4,2),(28,2),2)
    elif tid == TILE_STUMP:
        s.fill((28,75,28))
        pygame.draw.circle(s,(90,55,20),(TILE_SIZE//2,TILE_SIZE//2+4),8)
        pygame.draw.circle(s,(110,70,25),(TILE_SIZE//2,TILE_SIZE//2+4),5)
    elif tid == TILE_ORE:
        s.fill((45,45,55))
        pygame.draw.ellipse(s,(80,80,90),(4,8,24,18))
        pygame.draw.circle(s,(200,140,40),(18,12),4)
        pygame.draw.circle(s,(220,170,60),(20,13),2)
    elif tid == TILE_BUSH:
        s.fill((28,75,28))
        pygame.draw.circle(s,(25,110,25),(TILE_SIZE//2,TILE_SIZE//2),10)
        pygame.draw.circle(s,(30,130,30),(TILE_SIZE//2-4,TILE_SIZE//2-2),6)
        pygame.draw.circle(s,(20,90,20),(TILE_SIZE//2+4,TILE_SIZE//2+2),5)
    else:
        s.fill((10,12,30))

    # Water animation overlay
    if tid == TILE_WATER:
        wave_phase = (tick // 20) % 4
        for i in range(3):
            wy = 8 + i*8 + wave_phase * 2
            pygame.draw.line(s,(50,100,200),(2,wy),(TILE_SIZE-2,wy),1)

    _tile_cache[key] = s
    return s
