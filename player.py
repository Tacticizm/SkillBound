import math
import pygame
from constants import *
from renderer import GOLD, CRIMSON, NEON_GREEN, lerp_color

TAN    = (210,180,140)
WHITE  = (255,255,255)
BLACK  = (0,0,0)
BLUE   = (50,100,200)
LBROWN = (180,130,80)
YELLOW = (220,200,40)


class Skill:
    def __init__(self, name):
        self.name = name
        self.xp   = 0

    @property
    def level(self):
        return level_from_xp(self.xp)

    def add_xp(self, amount):
        old = self.level
        self.xp += amount
        return self.level > old

    def xp_to_next(self):
        lvl = self.level
        if lvl >= 99: return 0
        return XP_TABLE[lvl] - self.xp


class Item:
    ITEMS = {
        "Bronze Sword":   {"type":"weapon","bonus":3,  "value":10, "color":LBROWN},
        "Iron Sword":     {"type":"weapon","bonus":7,  "value":50, "color":(160,160,170)},
        "Steel Sword":    {"type":"weapon","bonus":14, "value":200,"color":(190,190,210)},
        "Bronze Shield":  {"type":"armour","bonus":2,  "value":15, "color":LBROWN},
        "Iron Shield":    {"type":"armour","bonus":5,  "value":60, "color":(160,160,170)},
        "Leather Armour": {"type":"armour","bonus":3,  "value":30, "color":(120,80,40)},
        "Logs":           {"type":"resource","bonus":0,"value":5,  "color":(120,70,30)},
        "Oak Logs":       {"type":"resource","bonus":0,"value":12, "color":(90,50,20)},
        "Copper Ore":     {"type":"resource","bonus":0,"value":8,  "color":(200,120,40)},
        "Iron Ore":       {"type":"resource","bonus":0,"value":20, "color":(150,150,160)},
        "Raw Fish":       {"type":"food","bonus":3,    "value":6,  "color":(60,200,220)},
        "Cooked Fish":    {"type":"food","bonus":8,    "value":15, "color":(220,180,80)},
        "Bread":          {"type":"food","bonus":4,    "value":8,  "color":(210,180,130)},
        "Gold Coin":      {"type":"currency","bonus":0,"value":1,  "color":(255,210,50)},
        "Goblin Bones":   {"type":"junk","bonus":0,   "value":1,  "color":WHITE},
        "Wolf Pelt":      {"type":"junk","bonus":0,   "value":15, "color":(130,130,140)},
        "Antidote":       {"type":"potion","bonus":0, "value":25, "color":(60,200,100)},
        "Health Potion":  {"type":"potion","bonus":10,"value":30, "color":(200,50,50)},
    }

    def __init__(self, name, qty=1):
        self.name = name
        self.qty  = qty
        data = self.ITEMS.get(name, {})
        self.type  = data.get("type","misc")
        self.bonus = data.get("bonus",0)
        self.value = data.get("value",1)
        self.color = data.get("color",WHITE)

    def heal_amount(self):
        return self.bonus if self.type in ("food","potion") else 0


class Inventory:
    SIZE = 28
    def __init__(self):
        self.slots = []

    def add(self, name, qty=1):
        for item in self.slots:
            if item.name == name and item.type not in ("weapon","armour"):
                item.qty += qty; return True
        if len(self.slots) < self.SIZE:
            self.slots.append(Item(name, qty)); return True
        return False

    def remove(self, name, qty=1):
        for item in self.slots:
            if item.name == name:
                item.qty -= qty
                if item.qty <= 0: self.slots.remove(item)
                return True
        return False

    def count(self, name):
        for item in self.slots:
            if item.name == name: return item.qty
        return 0

    def has(self, name, qty=1):
        return self.count(name) >= qty


class Player:
    MOVE_SPEED = 3
    WALK_FRAMES = 4

    def __init__(self, x, y):
        self.x = float(x * TILE_SIZE)
        self.y = float(y * TILE_SIZE)
        self.size = 22
        self.direction = 0
        self.walk_tick = 0
        self.moving    = False

        self.skills  = {s: Skill(s) for s in SKILLS}
        self.skills[SK_HP].xp  = XP_TABLE[9]
        self.skills[SK_ATK].xp = XP_TABLE[4]
        self.skills[SK_DEF].xp = XP_TABLE[4]

        self.max_hp = self._calc_max_hp()
        self.hp     = self.max_hp
        self.gold   = 50

        self.inventory = Inventory()
        self.inventory.add("Bronze Sword")
        self.inventory.add("Health Potion", 3)
        self.inventory.add("Bread", 5)

        self.equipment = {"weapon": None, "armour": None}
        self._equip_default()

        self.level_up_msg = []
        self.resource_cooldown = 0

    def _equip_default(self):
        for item in self.inventory.slots:
            if item.name == "Bronze Sword":
                self.equipment["weapon"] = item

    def _calc_max_hp(self):
        return 10 + self.skills[SK_HP].level * 5

    @property
    def attack_bonus(self):
        base = self.skills[SK_ATK].level
        w = self.equipment.get("weapon")
        return base + (w.bonus if w else 0)

    @property
    def defence_bonus(self):
        base = self.skills[SK_DEF].level
        a = self.equipment.get("armour")
        return base + (a.bonus if a else 0)

    def equip(self, item):
        slot = item.type if item.type in ("weapon","armour") else None
        if slot:
            self.equipment[slot] = item; return True
        return False

    def use_consumable(self, item):
        heal = item.heal_amount()
        if heal > 0:
            self.hp = min(self.max_hp, self.hp + heal)
            self.inventory.remove(item.name)
            return heal
        return 0

    def add_xp(self, skill_name, amount):
        sk     = self.skills[skill_name]
        leveled = sk.add_xp(amount)
        if leveled:
            if skill_name == SK_HP:
                self.max_hp = self._calc_max_hp()
                self.hp = min(self.hp, self.max_hp)
            self.level_up_msg.append(f"{skill_name} → Level {sk.level}!")
        return leveled

    def get_tile_pos(self):
        cx = self.x + self.size//2
        cy = self.y + self.size//2
        return int(cx//TILE_SIZE), int(cy//TILE_SIZE)

    def move(self, dx, dy, world):
        self.moving = (dx != 0 or dy != 0)
        if self.moving:
            self.walk_tick += 1
        speed = self.MOVE_SPEED
        nx = self.x + dx*speed
        ny = self.y + dy*speed
        for corner in [(nx+2,self.y+2),(nx+self.size-2,self.y+2),
                       (nx+2,self.y+self.size-2),(nx+self.size-2,self.y+self.size-2)]:
            if world.is_solid(int(corner[0]//TILE_SIZE), int(corner[1]//TILE_SIZE)):
                nx = self.x; break
        for corner in [(nx+2,ny+2),(nx+self.size-2,ny+2),
                       (nx+2,ny+self.size-2),(nx+self.size-2,ny+self.size-2)]:
            if world.is_solid(int(corner[0]//TILE_SIZE), int(corner[1]//TILE_SIZE)):
                ny = self.y; break
        self.x = max(0, min(nx, (world.width-1)*TILE_SIZE))
        self.y = max(0, min(ny, (world.height-1)*TILE_SIZE))
        if dx > 0:   self.direction = 0
        elif dx < 0: self.direction = 180
        elif dy > 0: self.direction = 270
        elif dy < 0: self.direction = 90

    def draw(self, surf, cam_x, cam_y):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        s  = 26           # slightly larger sprite
        t  = self.walk_tick

        # Shadow ellipse beneath feet
        sh = pygame.Surface((s + 6, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 90), (0, 0, s + 6, 10))
        surf.blit(sh, (sx - 3, sy + s - 4))

        # --- Legs (walking animation — chunky pixel art rectangles) ---
        leg_off = int(4 * math.sin(t * 0.28)) if self.moving else 0
        leg_col  = (35, 50, 130)
        leg_col2 = (50, 70, 170)
        # Left leg
        pygame.draw.rect(surf, leg_col,  (sx + 2,     sy + s - 10, 8, 10 + leg_off),  border_radius=2)
        pygame.draw.rect(surf, (0,0,0),  (sx + 2,     sy + s - 10, 8, 10 + leg_off),  1, border_radius=2)
        # Shoe
        pygame.draw.rect(surf, (40, 30, 20), (sx + 1, sy + s + leg_off - 1, 9, 3), border_radius=1)
        # Right leg
        pygame.draw.rect(surf, leg_col,  (sx + s - 10, sy + s - 10, 8, 10 - leg_off), border_radius=2)
        pygame.draw.rect(surf, (0,0,0),  (sx + s - 10, sy + s - 10, 8, 10 - leg_off), 1, border_radius=2)
        pygame.draw.rect(surf, (40, 30, 20), (sx + s - 11, sy + s - leg_off - 1, 9, 3), border_radius=1)

        # --- Backpack bump (right side) ---
        pygame.draw.rect(surf, (110, 70, 30), (sx + s - 2, sy + 12, 6, 10), border_radius=2)
        pygame.draw.rect(surf, (80,  50, 20), (sx + s - 2, sy + 12, 6, 10), 1, border_radius=2)
        # Backpack strap accent
        pygame.draw.rect(surf, (90, 60, 25), (sx + s + 1, sy + 13, 2, 8))

        # --- Body / armour ---
        armour = self.equipment.get("armour")
        body_col = (55, 95, 195) if not armour else {
            "Leather Armour": (95, 65, 35),
            "Bronze Shield":  (55, 95, 195),
            "Iron Shield":    (85, 88, 108),
        }.get(armour.name, (55, 95, 195))
        body_light = tuple(min(255, c + 45) for c in body_col)
        body_dark  = tuple(max(0,   c - 40) for c in body_col)

        # Main torso rectangle
        pygame.draw.rect(surf, body_col,   (sx,     sy + 10, s, s - 10), border_radius=3)
        pygame.draw.rect(surf, (0, 0, 0),  (sx,     sy + 10, s, s - 10), 1, border_radius=3)
        # Chest highlight stripe
        pygame.draw.rect(surf, body_light, (sx + 3, sy + 12, s - 6, 5),  border_radius=2)
        # Belt line
        pygame.draw.rect(surf, body_dark,  (sx + 1, sy + s - 12, s - 2, 3))

        # --- Arms ---
        arm_col = body_col
        # Left arm (hangs at side, swings when walking)
        arm_off = int(3 * math.sin(t * 0.28)) if self.moving else 0
        pygame.draw.rect(surf, arm_col,  (sx - 4,   sy + 12 + arm_off, 5, 10), border_radius=2)
        pygame.draw.rect(surf, (0,0,0),  (sx - 4,   sy + 12 + arm_off, 5, 10), 1, border_radius=2)
        # Right arm
        pygame.draw.rect(surf, arm_col,  (sx + s - 1, sy + 12 - arm_off, 5, 10), border_radius=2)
        pygame.draw.rect(surf, (0,0,0),  (sx + s - 1, sy + 12 - arm_off, 5, 10), 1, border_radius=2)

        # --- Head ---
        hcx = sx + s // 2
        hcy = sy + 7
        head_r = 9
        # Skin
        pygame.draw.circle(surf, TAN,           (hcx, hcy), head_r)
        pygame.draw.circle(surf, (180, 140, 100),(hcx, hcy), head_r, 1)
        # Hair (top arc — dark brown)
        hair_rect = pygame.Rect(hcx - head_r, hcy - head_r, head_r * 2, head_r)
        pygame.draw.ellipse(surf, (80, 50, 20), hair_rect)
        pygame.draw.ellipse(surf, (0, 0, 0),    hair_rect, 1)
        # Eyes — pixel squares
        pygame.draw.rect(surf, BLACK, (hcx - 5, hcy - 1, 3, 3))
        pygame.draw.rect(surf, BLACK, (hcx + 2, hcy - 1, 3, 3))
        # White glint
        pygame.draw.rect(surf, WHITE, (hcx - 5, hcy - 1, 1, 1))
        pygame.draw.rect(surf, WHITE, (hcx + 2, hcy - 1, 1, 1))
        # Mouth (tiny line)
        pygame.draw.rect(surf, (160, 90, 70), (hcx - 3, hcy + 3, 6, 2))

        # --- Weapon (drawn prominently) ---
        weapon = self.equipment.get("weapon")
        if weapon:
            wcol = {
                "Bronze Sword": (180, 130, 60),
                "Iron Sword":   (170, 170, 180),
                "Steel Sword":  (200, 200, 220),
            }.get(weapon.name, YELLOW)
            # Blade
            if self.direction == 0:   # facing right
                # Blade (vertical bar to the right)
                pygame.draw.rect(surf, wcol,         (sx + s + 3, sy + 9,  4, 18), border_radius=1)
                pygame.draw.rect(surf, (0, 0, 0),    (sx + s + 3, sy + 9,  4, 18), 1, border_radius=1)
                # Guard (horizontal)
                pygame.draw.rect(surf, (220, 200, 80),(sx + s,     sy + 9,  10, 3))
                pygame.draw.rect(surf, (0,0,0),       (sx + s,     sy + 9,  10, 3), 1)
                # Tip
                pygame.draw.rect(surf, WHITE,         (sx + s + 4, sy + 9,  2, 3))
            else:
                pygame.draw.rect(surf, wcol,          (sx - 7, sy + 9,  4, 18), border_radius=1)
                pygame.draw.rect(surf, (0, 0, 0),     (sx - 7, sy + 9,  4, 18), 1, border_radius=1)
                pygame.draw.rect(surf, (220, 200, 80),(sx - 10, sy + 9, 10, 3))
                pygame.draw.rect(surf, (0,0,0),       (sx - 10, sy + 9, 10, 3), 1)
                pygame.draw.rect(surf, WHITE,         (sx - 7, sy + 9,  2, 3))

        # --- HP bar (thin, above head) ---
        bw = s + 6
        ratio = self.hp / max(1, self.max_hp)
        col_hp = NEON_GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else CRIMSON)
        pygame.draw.rect(surf, (40, 10, 10), (sx - 3, sy - 10, bw, 5), border_radius=2)
        pygame.draw.rect(surf, col_hp,       (sx - 3, sy - 10, max(2, int(bw * ratio)), 5), border_radius=2)
        pygame.draw.rect(surf, (0, 0, 0),    (sx - 3, sy - 10, bw, 5), 1, border_radius=2)
