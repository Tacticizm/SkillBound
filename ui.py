"""
ui.py — Redesigned professional HUD and menus
"""
import pygame
import math
from constants import *
from renderer import (draw_text_shadow, draw_panel, draw_bar, hp_color,
                      glow_circle, GOLD, DARK_GOLD, CRIMSON, NEON_GREEN,
                      PANEL_COL, PANEL_EDGE, XP_COL, DEEP_BLUE,
                      lerp_color)

WHITE  = (255,255,255)
GRAY   = (160,160,180)
BLACK  = (0,0,0)
LGRAY  = (200,200,220)

SKILL_ICONS = {
    SK_ATK:   ("⚔", CRIMSON),
    SK_DEF:   ("🛡", (60,120,220)),
    SK_HP:    ("♥", (220,60,80)),
    SK_WC:    ("🌲", (80,180,80)),
    SK_MIN:   ("⛏", (160,160,180)),
    SK_FISH:  ("🐟", (60,200,220)),
    SK_COOK:  ("🍖", (220,140,60)),
    SK_RANGE: ("🏹", (180,220,60)),
}

SKILL_COLORS = {
    SK_ATK:   CRIMSON,
    SK_DEF:   (60,120,220),
    SK_HP:    (220,60,80),
    SK_WC:    (80,180,80),
    SK_MIN:   (160,160,180),
    SK_FISH:  (60,200,220),
    SK_COOK:  (220,140,60),
    SK_RANGE: (180,220,60),
}


class HUD:
    def __init__(self):
        self.tick = 0
        self._mm_cache = None

    def draw(self, surf, player, world, cam_x, cam_y):
        self.tick += 1
        self._draw_status_panel(surf, player)
        self._draw_minimap(surf, player, world)
        self._draw_hotbar_hints(surf)

    def _draw_status_panel(self, surf, player):
        pw, ph = 230, 110
        draw_panel(surf, 8, 8, pw, ph, alpha=210, radius=10)

        font_b = pygame.font.SysFont("Arial", 20, bold=True)
        font_s = pygame.font.SysFont("Arial", 16)

        # HP label + bar
        ratio_hp = player.hp / max(1, player.max_hp)
        col_hp   = hp_color(ratio_hp)
        draw_text_shadow(surf, "HP", font_b, col_hp, 16, 14, offset=1)
        draw_bar(surf, 42, 18, pw-52, 16, ratio_hp, col_hp,
                 low_col=CRIMSON, bg_col=(40,10,10), radius=6)
        hp_txt = font_s.render(f"{player.hp}/{player.max_hp}", True, WHITE)
        surf.blit(hp_txt, (42 + (pw-52)//2 - hp_txt.get_width()//2, 19))

        # Prayer / MP placeholder bar (aesthetic)
        draw_text_shadow(surf, "SP", font_b, (60,120,220), 16, 40, offset=1)
        sp_val = min(1.0, player.skills[SK_DEF].level / 99)
        draw_bar(surf, 42, 44, pw-52, 12, sp_val, (80,160,255),
                 low_col=(30,60,180), bg_col=(10,10,40), radius=5)

        # Stats row
        w_name = player.equipment.get("weapon")
        a_name = player.equipment.get("armour")
        wstr = w_name.name[:14] if w_name else "Unarmed"
        astr = a_name.name[:14] if a_name else "No Armour"
        draw_text_shadow(surf, f"⚔ {player.attack_bonus:2d}  🛡 {player.defence_bonus:2d}",
                         font_b, LGRAY, 14, 62, offset=1)
        draw_text_shadow(surf, wstr, font_s, GOLD, 14, 82, offset=1)
        draw_text_shadow(surf, astr, font_s, (160,160,200), 14, 98, offset=1)

        # Gold (top right of panel)
        gold_font = pygame.font.SysFont("Arial", 18, bold=True)
        draw_text_shadow(surf, f"🪙 {player.gold}gp", gold_font, GOLD, pw-90, 14, offset=1)

    def _draw_minimap(self, surf, player, world):
        mw, mh = 150, 150
        mx, my = SCREEN_W - mw - 10, 10
        draw_panel(surf, mx-4, my-4, mw+8, mh+8+20, alpha=220, radius=8)
        font_lbl = pygame.font.SysFont("Arial", 13)
        draw_text_shadow(surf, "MAP", font_lbl, GOLD, mx + mw//2 - 14, my+mh+5, offset=1)

        scale_x = mw / world.width
        scale_y = mh / world.height

        mm = pygame.Surface((mw, mh))
        mm.fill((15,25,15))

        MINI = {
            TILE_WATER: (20,50,160),
            TILE_PATH:  (160,140,90),
            TILE_WALL:  (70,70,80),
            TILE_FLOOR: (130,100,60),
            TILE_TREE:  (15,80,20),
            TILE_ROCK:  (80,80,90),
            TILE_ORE:   (160,100,30),
            TILE_SAND:  (200,175,100),
            TILE_STUMP: (80,55,25),
            TILE_BUSH:  (25,110,25),
        }
        for ty in range(world.height):
            for tx in range(world.width):
                t = world.tile(tx, ty)
                c = MINI.get(t, (30,60,30))
                px2 = int(tx * scale_x)
                py2 = int(ty * scale_y)
                mm.set_at((min(mw-1,px2), min(mh-1,py2)), c)

        for e in world.enemies:
            if e.alive:
                ex = min(mw-1, int(e.tx * scale_x))
                ey = min(mh-1, int(e.ty * scale_y))
                mm.set_at((ex, ey), (220,50,50))

        ptx, pty = player.get_tile_pos()
        px2 = max(1, min(mw-2, int(ptx * scale_x)))
        py2 = max(1, min(mh-2, int(pty * scale_y)))
        pygame.draw.circle(mm, WHITE, (px2, py2), 2)
        pygame.draw.circle(mm, GOLD, (px2, py2), 2, 1)

        surf.blit(mm, (mx, my))
        pygame.draw.rect(surf, DARK_GOLD, (mx, my, mw, mh), 1)

    def _draw_hotbar_hints(self, surf):
        items = [("E","Interact"),("I","Inventory"),("K","Skills"),("Q","Quests")]
        font = pygame.font.SysFont("Arial", 14)
        total_w = len(items) * 96
        start_x = SCREEN_W//2 - total_w//2
        y = SCREEN_H - 36
        draw_panel(surf, start_x-6, y-6, total_w+12, 34, alpha=180, radius=8)
        for i,(key,label) in enumerate(items):
            x = start_x + i*96
            pygame.draw.rect(surf, (60,62,80), (x, y, 28, 22), border_radius=4)
            pygame.draw.rect(surf, GOLD,       (x, y, 28, 22), 1, border_radius=4)
            kf = pygame.font.SysFont("Arial", 14, bold=True)
            k  = kf.render(key, True, GOLD)
            surf.blit(k, (x+14-k.get_width()//2, y+3))
            lbl = font.render(label, True, GRAY)
            surf.blit(lbl, (x+32, y+4))

    # _draw_levelup removed — level-up messages now use the Notification system
    # and a single particle burst, avoiding the per-frame particle spam that caused lag.


# ── Inventory ─────────────────────────────────────────────────────────────────
class InventoryMenu:
    def __init__(self):
        self.active  = False
        self.cursor  = 0
        self.message = ""
        self.msg_timer=0

    def toggle(self):
        self.active = not self.active
        self.cursor = 0

    def handle_event(self, event, player):
        if not self.active: return
        if event.type != pygame.KEYDOWN: return
        inv = player.inventory.slots
        if event.key in (pygame.K_ESCAPE, pygame.K_i):
            self.active = False
        elif event.key == pygame.K_UP:
            self.cursor = max(0, self.cursor-1)
        elif event.key == pygame.K_DOWN:
            self.cursor = min(len(inv)-1, self.cursor+1)
        elif event.key in (pygame.K_RETURN, pygame.K_z):
            if inv and self.cursor < len(inv):
                item = inv[self.cursor]
                if item.type in ("food","potion"):
                    heal = player.use_consumable(item)
                    self.message = f"Used {item.name} — +{heal} HP restored."
                    self.msg_timer = 140
                elif item.type in ("weapon","armour"):
                    player.equip(item)
                    self.message = f"Equipped: {item.name}"
                    self.msg_timer = 140
                else:
                    self.message = "Can't use this outside combat."
                    self.msg_timer = 100

    def handle_click(self, pos, player):
        """Touch/mouse click on an inventory cell."""
        if not self.active: return
        px, py = (SCREEN_W-560)//2, (SCREEN_H-460)//2
        pw = 560
        cols, cell_w, cell_h = 4, (pw-24)//4, 54
        inv = player.inventory.slots
        for i, item in enumerate(inv[:28]):
            col_i = i % cols; row_i = i // cols
            ix = px + 12 + col_i * cell_w
            iy = py + 54 + row_i * cell_h
            if ix <= pos[0] <= ix+cell_w-6 and iy <= pos[1] <= iy+cell_h-6:
                self.cursor = i
                # Double-tap same slot = use
                if item.type in ("food","potion"):
                    heal = player.use_consumable(item)
                    self.message = f"Used {item.name} — +{heal} HP restored."
                    self.msg_timer = 140
                elif item.type in ("weapon","armour"):
                    player.equip(item)
                    self.message = f"Equipped: {item.name}"
                    self.msg_timer = 140
                return
        # Close button area (top-right corner of panel)
        if px+560-40 <= pos[0] <= px+560 and py <= pos[1] <= py+40:
            self.active = False

    def update(self):
        if self.msg_timer > 0: self.msg_timer -= 1

    def draw(self, surf, player):
        if not self.active: return
        font_b = pygame.font.SysFont("Georgia", 26, bold=True)
        font_s = pygame.font.SysFont("Arial",   20)
        font_t = pygame.font.SysFont("Arial",   16)
        pw, ph = 560, 460
        px, py = (SCREEN_W-pw)//2, (SCREEN_H-ph)//2
        draw_panel(surf, px, py, pw, ph, alpha=240, radius=14)

        # Header
        draw_text_shadow(surf, "Inventory", font_b, GOLD, px+16, py+12, offset=2)
        pygame.draw.line(surf, DARK_GOLD, (px+14, py+46), (px+pw-14, py+46), 1)
        draw_text_shadow(surf, f"🪙 {player.gold}gp", font_s, GOLD, px+pw-120, py+14, offset=1)
        draw_text_shadow(surf, "[ESC/I] Close   [↑↓] Navigate   [Enter] Use/Equip",
                         font_t, GRAY, px+14, py+ph-28, offset=1)

        inv = player.inventory.slots
        cols = 4
        cell_w = (pw-24)//cols
        cell_h = 54

        for i, item in enumerate(inv[:28]):
            col_i  = i % cols
            row_i  = i // cols
            ix = px + 12 + col_i * cell_w
            iy = py + 54 + row_i * cell_h
            is_sel = (i == self.cursor)
            is_eq  = any(eq and eq.name == item.name for eq in player.equipment.values())

            bg = (70,65,20) if is_sel else (28,30,50)
            draw_panel(surf, ix, iy, cell_w-6, cell_h-6,
                       col=bg, edge=GOLD if is_sel else PANEL_EDGE,
                       alpha=220, radius=6)

            # Color swatch
            pygame.draw.rect(surf, item.color, (ix+6, iy+10, 18, 18), border_radius=3)
            pygame.draw.rect(surf, (0,0,0), (ix+6, iy+10, 18, 18), 1, border_radius=3)

            # Name + qty
            col_txt = GOLD if is_sel else WHITE
            name_s = font_t.render(item.name[:13], True, col_txt)
            surf.blit(name_s, (ix+28, iy+8))
            if item.qty > 1:
                qty_s = font_t.render(f"x{item.qty}", True, (180,180,220))
                surf.blit(qty_s, (ix+28, iy+28))
            # Equipped badge
            if is_eq:
                eb = pygame.font.SysFont("Arial",12).render("EQ", True, BLACK)
                pygame.draw.rect(surf, GOLD, (ix+cell_w-28, iy+6, 20, 14), border_radius=3)
                surf.blit(eb, (ix+cell_w-26, iy+7))
            # Bonus hint
            if item.bonus > 0:
                bonus_s = pygame.font.SysFont("Arial",13).render(f"+{item.bonus}", True, NEON_GREEN)
                surf.blit(bonus_s, (ix+28, iy+28))

        # Message bar
        if self.msg_timer > 0:
            mc = NEON_GREEN if any(w in self.message for w in ("Used","Equipped")) else CRIMSON
            draw_text_shadow(surf, self.message, font_s, mc, px+14, py+ph-52, offset=1)


# ── Skills ────────────────────────────────────────────────────────────────────
class SkillsMenu:
    def __init__(self):
        self.active = False
        self.tick   = 0

    def toggle(self):
        self.active = not self.active

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_k):
            self.active = False

    def draw(self, surf, player):
        if not self.active: return
        self.tick += 1
        font_b = pygame.font.SysFont("Georgia", 26, bold=True)
        font_s = pygame.font.SysFont("Arial",   18, bold=True)
        font_t = pygame.font.SysFont("Arial",   14)
        pw, ph = 520, 460
        px, py = (SCREEN_W-pw)//2, (SCREEN_H-ph)//2
        draw_panel(surf, px, py, pw, ph, alpha=245, radius=14)
        draw_text_shadow(surf, "Skills", font_b, GOLD, px+16, py+12, offset=2)
        pygame.draw.line(surf, DARK_GOLD, (px+14, py+46), (px+pw-14, py+46), 1)
        draw_text_shadow(surf, "[ESC/K] Close", font_t, GRAY, px+pw-130, py+16, offset=1)

        # Total level
        total = sum(s.level for s in player.skills.values())
        draw_text_shadow(surf, f"Total Level: {total}", font_s,
                         (180,160,255), px+pw//2-60, py+14, offset=1)

        for i, sk_name in enumerate(SKILLS):
            sk    = player.skills[sk_name]
            lvl   = sk.level
            col   = SKILL_COLORS.get(sk_name, WHITE)
            col_i = i % 2
            row_i = i // 2
            sx = px + 12 + col_i * 250
            sy = py + 54 + row_i * 68

            # Card
            is_max = lvl >= 99
            bg = (20,25,35)
            draw_panel(surf, sx, sy, 238, 60, col=bg,
                       edge=col if not is_max else GOLD,
                       alpha=230, radius=8)

            # Colored left stripe
            pygame.draw.rect(surf, col, (sx, sy, 5, 60), border_radius=8)

            # Skill name
            draw_text_shadow(surf, sk_name, font_s, col, sx+12, sy+8, offset=1)

            # Level number (large)
            lvl_font = pygame.font.SysFont("Arial", 28, bold=True)
            draw_text_shadow(surf, str(lvl), lvl_font, WHITE if not is_max else GOLD,
                             sx+195, sy+8, offset=2)

            # XP bar
            if lvl < 99:
                xp_have = sk.xp - XP_TABLE[lvl-1]
                xp_need = XP_TABLE[lvl] - XP_TABLE[lvl-1]
                ratio = min(1.0, xp_have / max(1, xp_need))
                draw_bar(surf, sx+12, sy+42, 180, 10, ratio, col,
                         low_col=lerp_color((0,0,0), col, 0.4),
                         bg_col=(10,12,20), radius=4)
                xp_s = font_t.render(f"{sk.xp:,} xp", True, (140,140,170))
                surf.blit(xp_s, (sx+12, sy+44))
            else:
                mx = font_t.render("MAX", True, GOLD)
                surf.blit(mx, (sx+12, sy+42))


# ── Quest Log ─────────────────────────────────────────────────────────────────
class QuestMenu:
    def __init__(self):
        self.active = False
        self.cursor = 0

    def toggle(self):
        self.active = not self.active

    def handle_event(self, event, quest_mgr):
        if event.type != pygame.KEYDOWN: return
        if event.key in (pygame.K_ESCAPE, pygame.K_q):
            self.active = False
        quests = list(quest_mgr.quests.values())
        if event.key == pygame.K_UP:
            self.cursor = max(0, self.cursor-1)
        elif event.key == pygame.K_DOWN:
            self.cursor = min(len(quests)-1, self.cursor+1)

    def draw(self, surf, quest_mgr):
        if not self.active: return
        font_b = pygame.font.SysFont("Georgia", 26, bold=True)
        font_m = pygame.font.SysFont("Arial",   20, bold=True)
        font_s = pygame.font.SysFont("Arial",   17)
        font_t = pygame.font.SysFont("Arial",   14)
        pw, ph = 660, 480
        px, py = (SCREEN_W-pw)//2, (SCREEN_H-ph)//2
        draw_panel(surf, px, py, pw, ph, alpha=245, radius=14)
        draw_text_shadow(surf, "Quest Journal", font_b, GOLD, px+16, py+12, offset=2)
        pygame.draw.line(surf, DARK_GOLD, (px+14, py+46), (px+pw-14, py+46), 1)

        STATUS_COL = {
            "available": (160,160,180),
            "active":    GOLD,
            "ready":     NEON_GREEN,
            "complete":  (100,200,255),
        }
        STATUS_LBL = {
            "available": "AVAILABLE",
            "active":    "IN PROGRESS",
            "ready":     "READY TO CLAIM",
            "complete":  "COMPLETE",
        }

        quests = list(quest_mgr.quests.values())
        list_h = len(quests) * 38 + 10
        # Left pane — quest list
        for i, q in enumerate(quests):
            qy = py + 54 + i*38
            is_sel = (i == self.cursor)
            bg = (60,50,10) if is_sel else (22,24,40)
            draw_panel(surf, px+10, qy, 240, 34, col=bg,
                       edge=GOLD if is_sel else PANEL_EDGE, alpha=220, radius=6)
            sc = STATUS_COL.get(q.status, WHITE)
            draw_text_shadow(surf, q.title, font_s, WHITE if is_sel else GRAY,
                             px+18, qy+8, offset=1)
            dot = pygame.font.SysFont("Arial",10).render("●", True, sc)
            surf.blit(dot, (px+224, qy+12))

        # Divider
        pygame.draw.line(surf, PANEL_EDGE, (px+260, py+50), (px+260, py+ph-14), 1)

        # Right pane — detail
        if quests and self.cursor < len(quests):
            q = quests[self.cursor]
            rx = px + 272
            ry = py + 54
            sc = STATUS_COL.get(q.status, WHITE)
            sl = STATUS_LBL.get(q.status, "")

            # Status badge
            sb_w = font_t.size(sl)[0] + 16
            pygame.draw.rect(surf, sc, (rx, ry, sb_w, 22), border_radius=5)
            status_lbl = font_t.render(sl, True, BLACK)
            surf.blit(status_lbl, (rx+8, ry+4))

            draw_text_shadow(surf, q.title, font_m, WHITE, rx, ry+28, offset=2)
            pygame.draw.line(surf, DARK_GOLD, (rx, ry+54), (rx+pw-290, ry+54), 1)

            # Description
            draw_text_shadow(surf, q.description, font_s, GRAY, rx, ry+62, offset=1)

            # Objectives
            draw_text_shadow(surf, "Objectives:", font_s, (180,180,220), rx, ry+90, offset=1)
            for j, obj in enumerate(q.objectives):
                oy = ry + 112 + j*32
                done = obj["done"]
                box_col = NEON_GREEN if done else (80,80,100)
                pygame.draw.rect(surf, box_col, (rx, oy+2, 16, 16), border_radius=3)
                if done:
                    pygame.draw.line(surf, BLACK, (rx+3,oy+10),(rx+7,oy+14),2)
                    pygame.draw.line(surf, BLACK, (rx+7,oy+14),(rx+13,oy+6),2)
                txt_col = (180,200,180) if done else WHITE
                draw_text_shadow(surf, obj["desc"], font_s, txt_col, rx+24, oy+2, offset=1)
                if not done and obj["qty"] > 0:
                    qty_s = font_t.render(f"  ({obj['qty']} remaining)", True, (160,160,160))
                    surf.blit(qty_s, (rx+24 + font_s.size(obj["desc"])[0], oy+5))

            # Rewards
            ry2 = ry + 112 + len(q.objectives)*32 + 14
            pygame.draw.line(surf, PANEL_EDGE, (rx, ry2-6), (rx+pw-290, ry2-6), 1)
            draw_text_shadow(surf, "Rewards:", font_s, (180,180,220), rx, ry2, offset=1)
            r = q.rewards
            if r.get("gold"):
                draw_text_shadow(surf, f"🪙 {r['gold']} Gold", font_s, GOLD, rx, ry2+24, offset=1)
            xp_text = "  ".join(f"+{v} {k}" for k,v in r.get("xp",{}).items())
            if xp_text:
                draw_text_shadow(surf, xp_text, font_t, (180,140,255), rx, ry2+48, offset=1)

        draw_text_shadow(surf, "[ESC/Q] Close   [↑↓] Select Quest",
                         font_t, GRAY, px+16, py+ph-28, offset=1)


# ── Dialog box ────────────────────────────────────────────────────────────────
class DialogBox:
    def __init__(self):
        self.active   = False
        self.lines    = []
        self.page     = 0
        self.per_page = 6
        self.tick     = 0

    def open(self, lines):
        self.active = True
        self.lines  = lines
        self.page   = 0
        self.tick   = 0

    def close(self):
        self.active = False

    def handle_event(self, event):
        if not self.active: return
        if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_RETURN, pygame.K_z, pygame.K_ESCAPE, pygame.K_SPACE):
            total = max(1, (len(self.lines)+self.per_page-1)//self.per_page)
            if self.page < total-1:
                self.page += 1
            else:
                self.close()

    def draw(self, surf):
        if not self.active: return
        self.tick += 1
        font_s = pygame.font.SysFont("Georgia", 22)
        font_t = pygame.font.SysFont("Arial",   16)
        bw, bh = 740, 190
        bx, by = (SCREEN_W-bw)//2, SCREEN_H-bh-18
        draw_panel(surf, bx, by, bw, bh, alpha=245, radius=12)
        pygame.draw.line(surf, DARK_GOLD, (bx+14, by+42), (bx+bw-14, by+42), 1)

        # Speaker icon area
        pygame.draw.rect(surf, (40,42,60), (bx+8, by+8, 30, 30), border_radius=6)
        pygame.draw.rect(surf, GOLD,       (bx+8, by+8, 30, 30), 1, border_radius=6)
        spk = pygame.font.SysFont("Arial",18).render("💬", True, WHITE)
        surf.blit(spk, (bx+10, by+9))

        start = self.page * self.per_page
        visible = self.lines[start:start+self.per_page]
        for i, line in enumerate(visible):
            col = GOLD if i == 0 and self.page == 0 else WHITE
            draw_text_shadow(surf, line, font_s, col, bx+52, by+10+i*28, offset=1)

        total = max(1, (len(self.lines)+self.per_page-1)//self.per_page)
        blink = int(180+60*math.sin(self.tick*0.1))
        more = "▼ Next" if self.page < total-1 else "✕ Close"
        hint = font_t.render(f"{more}  [ENTER]", True, (blink, blink, 80))
        surf.blit(hint, (bx+bw-hint.get_width()-14, by+bh-24))

        if total > 1:
            pg = font_t.render(f"{self.page+1}/{total}", True, GRAY)
            surf.blit(pg, (bx+16, by+bh-24))


# ── Skill Badge Bar ───────────────────────────────────────────────────────────
class SkillBadgeBar:
    """Circular skill badges shown at the bottom-center of the screen.

    Each badge shows the skill letter icon inside a gold-outlined circle,
    with the level number. When a relevant resource node is nearby the badge
    for that skill is highlighted and shows a 'SkillName Lvl X' label.
    """

    BADGE_RADIUS   = 28
    BADGE_SPACING  = 70
    Y_CENTER       = SCREEN_H - 45

    # ASCII letter icons to use (emoji cause font issues on many systems)
    SKILL_LETTERS = {
        SK_ATK:  "A",
        SK_DEF:  "D",
        SK_HP:   "H",
        SK_WC:   "W",
        SK_MIN:  "M",
        SK_FISH: "F",
        SK_COOK: "C",
        SK_RANGE:"R",
    }

    def __init__(self):
        self.tick = 0

    def draw(self, surf, player, nearby_skill=None):
        """Draw badge bar.

        nearby_skill: skill name string (e.g. SK_WC) that is contextually
                      active (player is next to a matching resource node).
        """
        self.tick += 1
        n = len(SKILLS)
        total_w = (n - 1) * self.BADGE_SPACING
        start_x = SCREEN_W // 2 - total_w // 2

        for i, sk_name in enumerate(SKILLS):
            cx = start_x + i * self.BADGE_SPACING
            cy = self.Y_CENTER
            sk   = player.skills[sk_name]
            lvl  = sk.level
            col  = SKILL_COLORS.get(sk_name, WHITE)
            letter = self.SKILL_LETTERS.get(sk_name, "?")
            highlighted = (sk_name == nearby_skill)

            # --- Semi-transparent backing circle ---
            bg_surf = pygame.Surface((self.BADGE_RADIUS * 2 + 8,
                                      self.BADGE_RADIUS * 2 + 8), pygame.SRCALPHA)
            bg_cx = bg_cy = self.BADGE_RADIUS + 4
            pygame.draw.circle(bg_surf, (0, 0, 0, 140),
                               (bg_cx, bg_cy), self.BADGE_RADIUS + 2)
            surf.blit(bg_surf, (cx - self.BADGE_RADIUS - 4,
                                cy - self.BADGE_RADIUS - 4))

            # --- Outer gold ring (thicker when highlighted) ---
            ring_w = 4 if highlighted else 2
            ring_col = GOLD
            if highlighted:
                pulse = int(30 * abs(math.sin(self.tick * 0.12)))
                ring_col = (
                    min(255, 255),
                    min(255, 210 + pulse),
                    min(255, 50),
                )
            pygame.draw.circle(surf, ring_col, (cx, cy),
                               self.BADGE_RADIUS, ring_w)

            # --- Inner filled circle (skill color, dimmed) ---
            inner_surf = pygame.Surface((self.BADGE_RADIUS * 2,
                                         self.BADGE_RADIUS * 2), pygame.SRCALPHA)
            r, g, b = col
            inner_alpha = 200 if highlighted else 140
            pygame.draw.circle(inner_surf, (r, g, b, inner_alpha),
                               (self.BADGE_RADIUS, self.BADGE_RADIUS),
                               self.BADGE_RADIUS - ring_w - 1)
            surf.blit(inner_surf, (cx - self.BADGE_RADIUS,
                                   cy - self.BADGE_RADIUS))

            # --- Skill letter icon ---
            icon_size = 20 if highlighted else 17
            font_icon = pygame.font.SysFont("Arial", icon_size, bold=True)
            icon_lbl  = font_icon.render(letter, True, WHITE)
            # shadow
            sh = font_icon.render(letter, True, BLACK)
            surf.blit(sh, (cx - icon_lbl.get_width() // 2 + 1,
                           cy - icon_lbl.get_height() // 2 - 4 + 1))
            surf.blit(icon_lbl, (cx - icon_lbl.get_width() // 2,
                                 cy - icon_lbl.get_height() // 2 - 4))

            # --- Level number ---
            font_lvl = pygame.font.SysFont("Arial", 12, bold=True)
            lvl_lbl  = font_lvl.render(str(lvl), True, GOLD)
            surf.blit(lvl_lbl, (cx - lvl_lbl.get_width() // 2,
                                cy + self.BADGE_RADIUS // 2 - 2))

            # --- Highlighted label: "SkillName Lvl X" ---
            if highlighted:
                font_lbl2 = pygame.font.SysFont("Arial", 15, bold=True)
                label_str = f"{sk_name} Lvl {lvl}"
                lbl_surf  = font_lbl2.render(label_str, True, GOLD)
                lx = cx - lbl_surf.get_width() // 2
                ly = cy - self.BADGE_RADIUS - 22
                # Backing pill
                pill = pygame.Surface((lbl_surf.get_width() + 14,
                                        lbl_surf.get_height() + 6),
                                       pygame.SRCALPHA)
                pygame.draw.rect(pill, (0, 0, 0, 180),
                                 (0, 0, pill.get_width(), pill.get_height()),
                                 border_radius=6)
                surf.blit(pill, (lx - 7, ly - 3))
                surf.blit(lbl_surf, (lx, ly))


# ── Shop ──────────────────────────────────────────────────────────────────────
class ShopMenu:
    def __init__(self):
        self.active    = False
        self.npc       = None
        self.player    = None
        self.cursor    = 0
        self.tab       = "buy"
        self.message   = ""
        self.msg_timer = 0

    def open(self, npc, player):
        self.active = True; self.npc = npc; self.player = player
        self.cursor = 0;    self.tab = "buy"; self.message = ""

    def close(self): self.active = False

    def handle_event(self, event):
        if not self.active: return
        if event.type != pygame.KEYDOWN: return
        if event.key == pygame.K_ESCAPE:
            self.close(); return
        items = self._current_list()
        if event.key == pygame.K_UP:   self.cursor = max(0, self.cursor-1)
        elif event.key == pygame.K_DOWN: self.cursor = min(len(items)-1, self.cursor+1)
        elif event.key == pygame.K_TAB:
            self.tab = "sell" if self.tab=="buy" else "buy"; self.cursor=0
        elif event.key in (pygame.K_RETURN, pygame.K_z):
            self._transact(items)

    def _current_list(self):
        if self.tab == "buy":
            from player import Item
            return [Item(n) for n in self.npc.shop_inv]
        return [i for i in self.player.inventory.slots if i.type != "currency"]

    def _transact(self, items):
        if not items or self.cursor >= len(items): return
        item = items[self.cursor]
        if self.tab == "buy":
            cost = item.value * 2
            if self.player.gold >= cost:
                self.player.gold -= cost
                self.player.inventory.add(item.name)
                self.message = f"Purchased {item.name} for {cost}gp."
            else:
                self.message = f"Need {cost}gp — you have {self.player.gold}gp."
        else:
            price = max(1, item.value)
            self.player.gold += price
            self.player.inventory.remove(item.name)
            self.message = f"Sold {item.name} for {price}gp."
        self.msg_timer = 130

    def handle_click(self, pos):
        """Touch/mouse: tap an item row to select & buy/sell, tap tabs to switch."""
        if not self.active: return
        pw, ph = 620, 460
        px, py = (SCREEN_W-pw)//2, (SCREEN_H-ph)//2
        mx, my = pos
        # Tab buttons
        for i, t in enumerate(["buy","sell"]):
            tx = px+14 + i*110
            if tx <= mx <= tx+100 and py+52 <= my <= py+84:
                self.tab = t; self.cursor = 0; return
        # Item rows
        items = self._current_list()
        for i in range(min(len(items), 12)):
            iy = py+94 + i*28
            if px+10 <= mx <= px+pw-10 and iy <= my <= iy+26:
                if self.cursor == i:
                    self._transact(items)   # second tap = buy/sell
                else:
                    self.cursor = i
                return
        # Close tap (outside panel)
        if not (px <= mx <= px+pw and py <= my <= py+ph):
            self.close()

    def update(self):
        if self.msg_timer > 0: self.msg_timer -= 1

    def draw(self, surf):
        if not self.active: return
        font_b = pygame.font.SysFont("Georgia", 26, bold=True)
        font_m = pygame.font.SysFont("Arial",   20, bold=True)
        font_s = pygame.font.SysFont("Arial",   18)
        font_t = pygame.font.SysFont("Arial",   14)
        pw, ph = 620, 460
        px, py = (SCREEN_W-pw)//2, (SCREEN_H-ph)//2
        draw_panel(surf, px, py, pw, ph, alpha=245, radius=14)

        # Header
        draw_text_shadow(surf, f"{self.npc.name}", font_b, GOLD, px+16, py+12, offset=2)
        draw_text_shadow(surf, f"🪙 {self.player.gold}gp", font_m, GOLD, px+pw-140, py+14, offset=1)
        pygame.draw.line(surf, DARK_GOLD, (px+14, py+46), (px+pw-14, py+46), 1)

        # Tabs
        for i, t in enumerate(["buy","sell"]):
            tx = px+14 + i*110
            is_active = (t == self.tab)
            bg = (60,50,10) if is_active else (22,24,40)
            draw_panel(surf, tx, py+52, 100, 32, col=bg,
                       edge=GOLD if is_active else PANEL_EDGE, alpha=220, radius=6)
            lbl_col = GOLD if is_active else GRAY
            lbl = font_m.render(t.upper(), True, lbl_col)
            surf.blit(lbl, (tx + 50 - lbl.get_width()//2, py+58))

        # Item list
        items = self._current_list()
        for i, item in enumerate(items[:12]):
            iy = py+94 + i*28
            is_sel = (i == self.cursor)
            bg = (60,55,15) if is_sel else (24,26,44)
            draw_panel(surf, px+10, iy, pw-20, 26, col=bg,
                       edge=GOLD if is_sel else PANEL_EDGE, alpha=215, radius=5)
            price = item.value*2 if self.tab=="buy" else max(1,item.value)
            qty   = f"  x{item.qty}" if self.tab=="sell" and item.qty>1 else ""
            bonus = f"  +{item.bonus}" if item.bonus else ""
            col   = GOLD if is_sel else WHITE
            draw_text_shadow(surf, f"{item.name}{qty}{bonus}", font_s, col, px+20, iy+4, offset=1)
            price_s = font_s.render(f"{price}gp", True, GOLD if is_sel else (160,160,100))
            surf.blit(price_s, (px+pw-price_s.get_width()-20, iy+4))

        # Message
        if self.msg_timer > 0:
            mc = NEON_GREEN if "Purchased" in self.message or "Sold" in self.message else CRIMSON
            draw_text_shadow(surf, self.message, font_s, mc, px+14, py+ph-54, offset=1)

        draw_text_shadow(surf, "[TAB] Switch   [↑↓] Navigate   [Enter] Confirm   [ESC] Close",
                         font_t, GRAY, px+14, py+ph-28, offset=1)
