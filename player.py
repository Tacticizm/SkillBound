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
        s  = self.size
        t  = self.walk_tick

        # Shadow
        sh = pygame.Surface((s+4, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0,0,0,80), (0,0,s+4,8))
        surf.blit(sh, (sx-2, sy+s-4))

        # Legs (walking animation)
        leg_off = int(3 * math.sin(t * 0.3)) if self.moving else 0
        pygame.draw.rect(surf, (40,60,140), (sx+2,   sy+s-8, 7, 8+leg_off),  border_radius=2)
        pygame.draw.rect(surf, (40,60,140), (sx+s-9, sy+s-8, 7, 8-leg_off),  border_radius=2)

        # Armour / body
        armour = self.equipment.get("armour")
        body_col = (60,100,200) if not armour else {
            "Leather Armour": (100,70,40),
            "Bronze Shield":  (60,100,200),
            "Iron Shield":    (90,90,110),
        }.get(armour.name, (60,100,200))
        pygame.draw.rect(surf, body_col, (sx, sy+8, s, s-8), border_radius=4)
        # Chest highlight
        pygame.draw.rect(surf, tuple(min(255,c+40) for c in body_col),
                         (sx+3, sy+10, s-6, s//3-2), border_radius=3)

        # Head
        pygame.draw.circle(surf, TAN,  (sx+s//2, sy+7), 8)
        pygame.draw.circle(surf, (180,140,100), (sx+s//2, sy+7), 8, 1)
        # Eyes
        pygame.draw.circle(surf, BLACK, (sx+s//2-3, sy+6), 2)
        pygame.draw.circle(surf, BLACK, (sx+s//2+3, sy+6), 2)
        pygame.draw.circle(surf, WHITE, (sx+s//2-3, sy+5), 1)
        pygame.draw.circle(surf, WHITE, (sx+s//2+3, sy+5), 1)

        # Weapon
        weapon = self.equipment.get("weapon")
        if weapon:
            wcol = {
                "Bronze Sword": LBROWN,
                "Iron Sword":   (160,160,170),
                "Steel Sword":  (190,190,210),
            }.get(weapon.name, YELLOW)
            if self.direction == 0:   # facing right
                pygame.draw.rect(surf, wcol, (sx+s-2, sy+10, 3, 14), border_radius=1)
                pygame.draw.rect(surf, WHITE, (sx+s-4, sy+10, 7, 2))
            else:
                pygame.draw.rect(surf, wcol, (sx-1, sy+10, 3, 14), border_radius=1)
                pygame.draw.rect(surf, WHITE, (sx-3, sy+10, 7, 2))

        # HP bar (tiny, above head)
        bw = s + 4
        ratio = self.hp / max(1, self.max_hp)
        col_hp = NEON_GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else CRIMSON)
        pygame.draw.rect(surf, (40,10,10), (sx-2, sy-8, bw, 4), border_radius=2)
        pygame.draw.rect(surf, col_hp,    (sx-2, sy-8, max(2,int(bw*ratio)), 4), border_radius=2)
