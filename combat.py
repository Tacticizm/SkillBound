"""
combat.py — Cinematic turn-based Pokemon-style combat
"""
import pygame
import math
import random
from constants import *
from renderer import (draw_text_shadow, draw_panel, draw_bar, hp_color,
                      glow_circle, ParticleSystem, ScreenShake,
                      GOLD, DARK_GOLD, CRIMSON, NEON_GREEN, PANEL_COL,
                      PANEL_EDGE, XP_COL, DEEP_BLUE, lerp_color)

WHITE  = (255,255,255)
GRAY   = (160,160,180)
BLACK  = (0,0,0)

ENEMY_PORTRAITS = {
    "Goblin":    [(60,160,60),(40,120,40),(80,200,80)],
    "Cow":       [(220,220,200),(180,180,160),(240,240,220)],
    "Wolf":      [(100,100,120),(70,70,90),(130,130,150)],
    "Guard":     [(60,80,180),(40,60,140),(80,100,200)],
    "Dark Mage": [(120,30,160),(80,20,120),(160,40,200)],
}

def draw_enemy_portrait(surf, enemy, cx, cy, size, flash=False, tick=0):
    """Draw a stylized enemy portrait."""
    colors = ENEMY_PORTRAITS.get(enemy.name, [(100,100,100)])
    base, dark, light = colors[0], colors[min(1,len(colors)-1)], colors[min(2,len(colors)-1)]
    if flash:
        base = WHITE; dark = (200,200,200); light = WHITE

    # Shadow
    sh = pygame.Surface((size+20, size//3+10), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0,0,0,80), (0,0,size+20,size//3+10))
    surf.blit(sh, (cx-size//2-10, cy+size//2-5))

    # Body shape per enemy type
    if enemy.name == "Goblin":
        # Stocky humanoid
        pygame.draw.ellipse(surf, base, (cx-size//3, cy-size//3, size*2//3, size*2//3))
        pygame.draw.ellipse(surf, dark, (cx-size//4, cy+size//6, size//2, size//3))
        pygame.draw.ellipse(surf, light, (cx-size//5, cy-size//3-4, size*2//5, size//3))
        # Eyes
        pygame.draw.circle(surf, (255,50,50), (cx-12, cy-size//4), 5)
        pygame.draw.circle(surf, (255,50,50), (cx+12, cy-size//4), 5)
        pygame.draw.circle(surf, BLACK, (cx-12, cy-size//4), 2)
        pygame.draw.circle(surf, BLACK, (cx+12, cy-size//4), 2)
        # Ears
        pygame.draw.polygon(surf, dark, [(cx-size//3,cy-size//4),(cx-size//2,cy-size//2),(cx-size//4,cy-size//6)])
        pygame.draw.polygon(surf, dark, [(cx+size//3,cy-size//4),(cx+size//2,cy-size//2),(cx+size//4,cy-size//6)])

    elif enemy.name == "Cow":
        # Boxy body
        pygame.draw.rect(surf, base, (cx-size//2+4, cy-size//3, size-8, size*2//3), border_radius=10)
        pygame.draw.rect(surf, dark, (cx-size//4, cy+size//6, size//2, size//4), border_radius=6)
        # Head
        pygame.draw.ellipse(surf, base, (cx-size//3, cy-size//2, size*2//3, size//2))
        pygame.draw.circle(surf, BLACK, (cx-10, cy-size//3), 5)
        pygame.draw.circle(surf, BLACK, (cx+10, cy-size//3), 5)
        # Horns
        pygame.draw.line(surf, dark, (cx-14,cy-size//2),(cx-22,cy-size//2-14),3)
        pygame.draw.line(surf, dark, (cx+14,cy-size//2),(cx+22,cy-size//2-14),3)
        # Spots
        pygame.draw.circle(surf, dark, (cx+10, cy), 8)
        pygame.draw.circle(surf, dark, (cx-15, cy+10), 6)

    elif enemy.name == "Wolf":
        # Sleek body
        points = [(cx-size//2,cy+size//3),(cx,cy-size//2),(cx+size//2,cy+size//3)]
        pygame.draw.polygon(surf, base, points)
        pygame.draw.ellipse(surf, dark, (cx-size//3,cy-size//2+4,size*2//3,size//2))
        # Eyes (glowing)
        glow_circle(surf, (255,200,0), (cx-10, cy-size//4), 12, 60)
        pygame.draw.circle(surf, (240,200,0), (cx-10, cy-size//4), 5)
        glow_circle(surf, (255,200,0), (cx+10, cy-size//4), 12, 60)
        pygame.draw.circle(surf, (240,200,0), (cx+10, cy-size//4), 5)
        # Snout
        pygame.draw.ellipse(surf, light, (cx-12,cy-size//5,24,14))
        pygame.draw.circle(surf, dark, (cx,cy-size//5+4),4)

    elif enemy.name == "Guard":
        # Armoured humanoid
        pygame.draw.rect(surf, base, (cx-size//3,cy-size//3,size*2//3,size*2//3), border_radius=4)
        pygame.draw.rect(surf, dark, (cx-size//3,cy-size//3,size*2//3,size//4), border_radius=4)
        pygame.draw.rect(surf, (180,180,200),(cx-size//3+2,cy-size//3+2,size*2//3-4,size*2//3-4), 3)
        pygame.draw.ellipse(surf, base, (cx-size//5,cy-size//2-2,size*2//5,size//2))
        # Visor
        pygame.draw.rect(surf, (30,30,60),(cx-size//5+4,cy-size//2+8,size*2//5-8,8))
        pygame.draw.rect(surf, (100,120,220),(cx-size//5+4,cy-size//2+9,size*2//5-8,5))

    elif enemy.name == "Dark Mage":
        # Robed figure with glow
        t = tick * 0.06
        glow_r = int(40+20*math.sin(t))
        glow_circle(surf, base, (cx, cy), size//2+10, glow_r)
        pygame.draw.ellipse(surf, dark, (cx-size//3,cy-size//4,size*2//3,size*2//3))
        pygame.draw.polygon(surf, base, [(cx,cy-size//2-10),(cx-size//2,cy+size//3),(cx+size//2,cy+size//3)])
        pygame.draw.ellipse(surf, dark, (cx-size//5,cy-size//2,size*2//5,size//2))
        # Glowing eyes
        glow_circle(surf, (200,100,255),(cx-10,cy-size//4),15,80)
        glow_circle(surf, (200,100,255),(cx+10,cy-size//4),15,80)
        pygame.draw.circle(surf,(220,180,255),(cx-10,cy-size//4),5)
        pygame.draw.circle(surf,(220,180,255),(cx+10,cy-size//4),5)
        # Floating orb
        ox = cx + int(30*math.cos(t))
        oy = cy - 20 + int(10*math.sin(t*0.7))
        glow_circle(surf, (180,80,255),(ox,oy),14,60)
        pygame.draw.circle(surf,(200,120,255),(ox,oy),6)


class CombatSystem:
    ACTIONS = ["Attack", "Item", "Run"]

    def __init__(self):
        self.particles = ParticleSystem()
        self.shake     = ScreenShake()
        self.reset()

    def reset(self):
        self.active      = False
        self.enemy       = None
        self.player      = None
        self.world       = None
        self.log         = []
        self.phase       = "select"
        self.selected    = 0
        self.item_cursor = 0
        self.show_items  = False
        self.outcome     = None
        self.xp_gained   = 0
        self.gold_gained = 0
        self.loot        = []
        self.tick        = 0
        self.enemy_flash = 0
        self.player_flash= 0
        self.particles   = ParticleSystem()
        self.shake       = ScreenShake()

    def start(self, player, enemy, world):
        self.reset()
        self.active = True
        self.player = player
        self.enemy  = enemy
        self.world  = world
        self.log    = [f"⚔  A wild {enemy.name} appears!"]
        self.phase  = "select"

    def _player_damage(self):
        p = self.player
        roll = random.randint(max(1, p.attack_bonus//2), max(1, p.attack_bonus))
        red  = random.randint(0, max(0, self.enemy.defense//2))
        return max(1, roll - red)

    def _enemy_damage(self):
        roll = random.randint(max(1, self.enemy.atk//2), max(1, self.enemy.atk))
        red  = random.randint(0, max(0, self.player.defence_bonus//2))
        return max(1, roll - red)

    def _enemy_turn(self):
        dmg = self._enemy_damage()
        self.player.hp = max(0, self.player.hp - dmg)
        self.log.append(f"💢 {self.enemy.name} hits you for {dmg}!")
        self.player_flash = 10
        self.shake.shake(6, 14)
        # Particle at center-bottom of screen
        self.particles.damage_number(SCREEN_W//2 + 80, SCREEN_H - 230, dmg, is_player_hit=True)
        self.particles.burst(SCREEN_W//2 + 80, SCREEN_H - 230, CRIMSON, count=8, speed=2.0)

    def _finish_win(self):
        p = self.player
        xp = self.enemy.xp
        p.add_xp(SK_ATK, xp//2)
        p.add_xp(SK_DEF, xp//4)
        p.add_xp(SK_HP,  xp//4)
        self.xp_gained = xp
        loot = self.enemy.loot()
        for name, qty in loot:
            if name == "Gold Coin":
                p.gold += qty; self.gold_gained += qty
            else:
                p.inventory.add(name, qty); self.loot.append((name, qty))
        self.enemy.alive = False
        msg = f"✦ Victory! +{xp} XP"
        if self.gold_gained: msg += f"  🪙+{self.gold_gained}gp"
        self.log.append(msg)
        self.outcome = "win"
        self.phase   = "result"
        # Win burst
        ex, ey = SCREEN_W//2 - 80, SCREEN_H//2 - 60
        self.particles.burst(ex, ey, GOLD,       count=24, speed=5.0)
        self.particles.burst(ex, ey, (255,255,200), count=12, speed=3.0)
        self.particles.xp_text(ex, ey, "Combat", xp)

    # Action button rects (kept in sync with _draw_action_menu)
    def _action_btn_rect(self, i):
        bx = SCREEN_W - 310; by = SCREEN_H - 108
        return (bx + 12 + i * 92, by + 18, 80, 56)

    def _item_row_rect(self, i):
        mw = 320; mx = SCREEN_W//2 - mw//2; my = SCREEN_H//2 - 130
        return (mx+8, my+44+i*32, mw-16, 28)

    def handle_event(self, event):
        if not self.active or self.phase == "result":
            return

        # ── Touch / mouse clicks ──
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            if event.type == pygame.FINGERDOWN:
                pos = (int(event.x * SCREEN_W), int(event.y * SCREEN_H))
            else:
                pos = event.pos

            if self.show_items:
                usable = [i for i in self.player.inventory.slots if i.type in ("food","potion")]
                for i in range(min(len(usable), 6)):
                    rx, ry, rw, rh = self._item_row_rect(i)
                    if rx <= pos[0] <= rx+rw and ry <= pos[1] <= ry+rh:
                        if self.item_cursor == i:
                            # second tap = confirm
                            item = usable[i]
                            heal = self.player.use_consumable(item)
                            if heal:
                                self.log.append(f"💊 You use {item.name}, restoring {heal} HP.")
                                self.particles.sparkle(SCREEN_W//2+80, SCREEN_H-220, NEON_GREEN, 10)
                                self.show_items = False
                                self._enemy_turn(); self._check_dead()
                        else:
                            self.item_cursor = i
                        return
                self.show_items = False   # tap outside = close
                return

            for i, action in enumerate(self.ACTIONS):
                rx, ry, rw, rh = self._action_btn_rect(i)
                if rx <= pos[0] <= rx+rw and ry <= pos[1] <= ry+rh:
                    if self.selected == i:
                        self._execute()
                    else:
                        self.selected = i
                    return
            return

        if event.type != pygame.KEYDOWN:
            return

        # ── Keyboard ──
        if self.show_items:
            usable = [i for i in self.player.inventory.slots if i.type in ("food","potion")]
            if event.key == pygame.K_ESCAPE:
                self.show_items = False
            elif event.key == pygame.K_UP:
                self.item_cursor = max(0, self.item_cursor-1)
            elif event.key == pygame.K_DOWN:
                self.item_cursor = min(len(usable)-1, self.item_cursor+1)
            elif event.key in (pygame.K_RETURN, pygame.K_z):
                if usable:
                    item = usable[self.item_cursor]
                    heal = self.player.use_consumable(item)
                    if heal:
                        self.log.append(f"💊 You use {item.name}, restoring {heal} HP.")
                        self.particles.sparkle(SCREEN_W//2+80, SCREEN_H-220, NEON_GREEN, count=10)
                        self.show_items = False
                        self._enemy_turn()
                        self._check_dead()
            return

        if event.key in (pygame.K_LEFT, pygame.K_a):
            self.selected = (self.selected-1) % len(self.ACTIONS)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.selected = (self.selected+1) % len(self.ACTIONS)
        elif event.key in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE):
            self._execute()

    def _execute(self):
        action = self.ACTIONS[self.selected]
        if action == "Attack":
            dmg = self._player_damage()
            self.enemy.hp = max(0, self.enemy.hp - dmg)
            self.log.append(f"⚔ You strike {self.enemy.name} for {dmg} damage!")
            self.enemy_flash = 10
            # Particles on enemy
            ex, ey = SCREEN_W//2 - 80, SCREEN_H//2 - 60
            self.particles.damage_number(ex, ey-30, dmg, is_player_hit=False)
            self.particles.burst(ex, ey, (255,200,50), count=10, speed=2.5)
            if self.enemy.hp <= 0:
                self._finish_win(); return
            self._enemy_turn()
            self._check_dead()

        elif action == "Item":
            self.show_items = True
            self.item_cursor = 0

        elif action == "Run":
            flee = 0.5 + (self.player.skills[SK_ATK].level - self.enemy.atk) * 0.04
            if random.random() < max(0.1, min(0.9, flee)):
                self.log.append("💨 You flee successfully!")
                self.outcome = "run"; self.phase = "result"
            else:
                self.log.append("❌ You couldn't escape!")
                self._enemy_turn()
                self._check_dead()

    def _check_dead(self):
        if self.player.hp <= 0:
            self.log.append("💀 You have been defeated... respawning.")
            self.player.hp = self.player.max_hp // 2
            self.outcome = "lose"; self.phase = "result"
            self.shake.shake(10, 25)

    def update(self):
        self.tick += 1
        self.particles.update()
        self.shake.update()
        if self.enemy_flash  > 0: self.enemy_flash  -= 1
        if self.player_flash > 0: self.player_flash -= 1

    # ── Draw ─────────────────────────────────────────────────────────────────
    def draw(self, surf):
        if not self.active: return

        ox, oy = self.shake.offset()
        t = self.tick

        # Dimmed world background
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 15, 200))
        surf.blit(overlay, (0,0))

        # Battle arena background gradient
        arena = pygame.Surface((SCREEN_W, SCREEN_H//2 + 80), pygame.SRCALPHA)
        for y in range(SCREEN_H//2 + 80):
            alpha = int(120 * (1 - y / (SCREEN_H//2 + 80)))
            t2 = y/(SCREEN_H//2+80)
            col = lerp_color((10,5,30),(30,10,10),t2)
            pygame.draw.line(arena, (*col, alpha), (0,y),(SCREEN_W,y))
        surf.blit(arena, (ox, oy))

        # Ground line
        gy = SCREEN_H//2 + 40
        pygame.draw.line(surf, (60,50,40), (0, gy+oy), (SCREEN_W, gy+oy), 2)

        # Enemy side (left of center, upper)
        ecx = SCREEN_W//2 - 120 + ox
        ecy = SCREEN_H//2 - 60  + oy
        draw_enemy_portrait(surf, self.enemy, ecx, ecy, 100,
                            flash=(self.enemy_flash > 0 and self.enemy_flash % 2==0),
                            tick=t)

        # Enemy info card (top left)
        ex0, ey0, ew, eh = 16+ox, 16+oy, 280, 110
        draw_panel(surf, ex0, ey0, ew, eh, alpha=230, radius=10)
        font_b = pygame.font.SysFont("Arial", 22, bold=True)
        font_s = pygame.font.SysFont("Arial", 17)
        draw_text_shadow(surf, self.enemy.name, font_b, WHITE, ex0+10, ey0+8, offset=2)
        ratio_e = self.enemy.hp / max(1, self.enemy.max_hp)
        draw_bar(surf, ex0+10, ey0+36, ew-20, 16, ratio_e,
                 hp_color(ratio_e), low_col=CRIMSON, radius=6)
        hp_lbl = font_s.render(f"{self.enemy.hp} / {self.enemy.max_hp}", True, WHITE)
        surf.blit(hp_lbl, (ex0+10+(ew-20)//2-hp_lbl.get_width()//2, ey0+37))
        draw_text_shadow(surf, f"ATK {self.enemy.atk}   DEF {self.enemy.defense}   XP {self.enemy.xp}",
                         font_s, GRAY, ex0+10, ey0+60, offset=1)
        draw_text_shadow(surf, f"Lv {min(30, self.enemy.atk+self.enemy.defense)}",
                         pygame.font.SysFont("Arial",16), (180,160,255), ex0+10, ey0+82, offset=1)

        # Player info card (bottom right)
        px0 = SCREEN_W - 310 + ox
        py0 = SCREEN_H - 230 + oy
        pf  = self.player_flash > 0 and self.player_flash % 2 == 0
        draw_panel(surf, px0, py0, 290, 120,
                   col=(60,10,10) if pf else PANEL_COL,
                   edge=CRIMSON if pf else GOLD, alpha=235, radius=10)
        draw_text_shadow(surf, "You", font_b, WHITE, px0+10, py0+8, offset=2)
        ratio_p = self.player.hp / max(1, self.player.max_hp)
        draw_bar(surf, px0+10, py0+36, 268, 16, ratio_p,
                 hp_color(ratio_p), low_col=CRIMSON, radius=6)
        hp_p = font_s.render(f"{self.player.hp} / {self.player.max_hp}", True, WHITE)
        surf.blit(hp_p, (px0+10+268//2-hp_p.get_width()//2, py0+37))
        draw_text_shadow(surf, f"ATK {self.player.attack_bonus}   DEF {self.player.defence_bonus}",
                         font_s, GRAY, px0+10, py0+60, offset=1)
        # Player avatar icon
        pygame.draw.rect(surf, (60,100,200), (px0+240, py0+70, 36, 40), border_radius=5)
        pygame.draw.circle(surf, TAN, (px0+258, py0+70), 10)

        # Action menu / item list
        if self.show_items:
            self._draw_item_menu(surf, ox, oy)
        elif self.phase == "select":
            self._draw_action_menu(surf, ox, oy)

        # Battle log
        self._draw_log(surf, ox, oy)

        # Particles
        self.particles.draw(surf)

        # Result overlay
        if self.phase == "result":
            self._draw_result(surf)

    def _draw_action_menu(self, surf, ox, oy):
        t = self.tick
        bx = SCREEN_W - 310 + ox
        by = SCREEN_H - 108 + oy
        bw, bh = 290, 96
        draw_panel(surf, bx, by, bw, bh, alpha=240, radius=10)
        font = pygame.font.SysFont("Arial", 24, bold=True)
        icons = {"Attack":"⚔", "Item":"💊", "Run":"💨"}
        colors= {"Attack":CRIMSON, "Item":NEON_GREEN, "Run":GOLD}
        for i, action in enumerate(self.ACTIONS):
            ix = bx + 12 + i * 92
            iy = by + 18
            sel = (i == self.selected)
            col = colors[action]
            if sel:
                pulse = int(20*math.sin(t*0.1))
                pygame.draw.rect(surf, (*col, 60+pulse),
                                 (ix-4, iy-4, 84, 60), border_radius=8)
                pygame.draw.rect(surf, col, (ix-4, iy-4, 84, 60), 2, border_radius=8)
            icon_s = pygame.font.SysFont("Arial",22).render(icons[action], True, col)
            surf.blit(icon_s, (ix+12, iy+2))
            lbl = font.render(action, True, WHITE if sel else GRAY)
            surf.blit(lbl, (ix + 40 - lbl.get_width()//2, iy+30))

    def _draw_item_menu(self, surf, ox, oy):
        usable = [i for i in self.player.inventory.slots if i.type in ("food","potion")]
        font_b = pygame.font.SysFont("Arial", 22, bold=True)
        font_s = pygame.font.SysFont("Arial", 18)
        mw, mh = 320, min(260, 50 + len(usable)*32 + 20)
        mx = SCREEN_W//2 - mw//2 + ox
        my = SCREEN_H//2 - mh//2 + oy
        draw_panel(surf, mx, my, mw, mh, alpha=245, radius=10)
        draw_text_shadow(surf, "Use Item", font_b, GOLD, mx+12, my+10, offset=2)
        pygame.draw.line(surf, DARK_GOLD, (mx+10, my+38), (mx+mw-10, my+38), 1)
        if not usable:
            surf.blit(font_s.render("No usable items.", True, GRAY), (mx+14, my+48))
        for i, item in enumerate(usable[:6]):
            iy = my+44+i*32
            sel = (i == self.item_cursor)
            bg = (60,50,10) if sel else (24,26,44)
            draw_panel(surf, mx+8, iy, mw-16, 28, col=bg,
                       edge=GOLD if sel else PANEL_EDGE, alpha=220, radius=6)
            col = GOLD if sel else WHITE
            draw_text_shadow(surf, f"{item.name}  x{item.qty}  (+{item.bonus} HP)",
                             font_s, col, mx+16, iy+6, offset=1)
        draw_text_shadow(surf, "[ESC] Back   [↑↓] Select   [Enter] Use",
                         pygame.font.SysFont("Arial",14), GRAY, mx+10, my+mh-24, offset=1)

    def _draw_log(self, surf, ox, oy):
        lx = 16 + ox
        ly = SCREEN_H - 108 + oy
        lw = SCREEN_W - 330
        lh = 96
        draw_panel(surf, lx, ly, lw, lh, alpha=230, radius=10)
        font = pygame.font.SysFont("Arial", 17)
        for i, line in enumerate(self.log[-4:]):
            alpha = 255 if i == len(self.log[-4:])-1 else int(180 - i*30)
            col   = GOLD if "Victory" in line or "✦" in line else \
                    CRIMSON if "hits you" in line or "💀" in line else \
                    NEON_GREEN if "💊" in line else WHITE
            lbl = font.render(line, True, col)
            lbl.set_alpha(alpha)
            surf.blit(lbl, (lx+12, ly+10+i*20))

    def _draw_result(self, surf):
        t = self.tick
        configs = {
            "win":  (GOLD,    "✦  VICTORY  ✦",   "Enemy defeated!"),
            "lose": (CRIMSON, "✖  DEFEATED  ✖",  "Respawning at town..."),
            "run":  (GOLD,    "💨  ESCAPED  💨",  "You fled the battle."),
        }
        col, title, subtitle = configs.get(self.outcome, (WHITE,"",""))

        # Overlay
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0,0,0, int(160 + 40*math.sin(t*0.05))))
        surf.blit(ov, (0,0))

        font_big = pygame.font.SysFont("Georgia", 52, bold=True)
        font_sub = pygame.font.SysFont("Arial",   24)
        font_sml = pygame.font.SysFont("Arial",   18)

        # Glow
        glow_circle(surf, col, (SCREEN_W//2, SCREEN_H//2-40), 120, 80)

        draw_text_shadow(surf, title,
                         font_big, col,
                         SCREEN_W//2 - font_big.size(title)[0]//2,
                         SCREEN_H//2 - 80, shadow_col=(0,0,0), offset=4)

        draw_text_shadow(surf, subtitle,
                         font_sub, WHITE,
                         SCREEN_W//2 - font_sub.size(subtitle)[0]//2,
                         SCREEN_H//2 - 16, offset=2)

        if self.outcome == "win":
            reward_lines = [f"+{self.xp_gained} XP"]
            if self.gold_gained: reward_lines.append(f"🪙 +{self.gold_gained}gp")
            for name,qty in self.loot:  reward_lines.append(f"  {name} x{qty}")
            for i, r in enumerate(reward_lines):
                rc = GOLD if "XP" in r or "gp" in r else WHITE
                draw_text_shadow(surf, r, font_sml, rc,
                                 SCREEN_W//2 - font_sml.size(r)[0]//2,
                                 SCREEN_H//2 + 18 + i*24, offset=1)

        blink = int(160+80*math.sin(t*0.07))
        hint = font_sml.render("[ ENTER ] Continue", True, (blink,blink,blink))
        surf.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H//2 + 120))
        self.particles.draw(surf)
