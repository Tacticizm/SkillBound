import pygame
import random
from constants import *
from pixelart import get_tile_surf
from renderer import GOLD, CRIMSON, NEON_GREEN

WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY  = (160,160,180)


class Enemy:
    TEMPLATES = {
        "Goblin":    {"hp":18,"atk":4, "def":2, "xp":25, "gold":(1,5),  "color":(60,160,60),  "drop":[("Goblin Bones",1,.9),("Logs",1,.3),("Gold Coin",3,.5)]},
        "Cow":       {"hp":22,"atk":3, "def":1, "xp":15, "gold":(0,2),  "color":(220,220,200),"drop":[("Raw Fish",1,.4),("Bread",1,.5)]},
        "Wolf":      {"hp":30,"atk":8, "def":4, "xp":45, "gold":(2,8),  "color":(100,100,120),"drop":[("Wolf Pelt",1,.7),("Raw Fish",1,.3)]},
        "Guard":     {"hp":40,"atk":10,"def":8, "xp":80, "gold":(5,15), "color":(60,80,180),  "drop":[("Iron Ore",1,.3),("Health Potion",1,.2)]},
        "Dark Mage": {"hp":55,"atk":14,"def":6, "xp":120,"gold":(8,20), "color":(120,30,160), "drop":[("Health Potion",2,.6),("Iron Ore",2,.4)]},
    }

    def __init__(self, name, tx, ty):
        self.name = name
        d = self.TEMPLATES[name]
        self.max_hp  = d["hp"]; self.hp = self.max_hp
        self.atk     = d["atk"]; self.defense = d["def"]
        self.xp      = d["xp"]; self.gold_range = d["gold"]
        self.drops   = d["drop"]; self.color = d["color"]
        self.tx = tx; self.ty = ty
        self.alive   = True
        self._bob    = random.uniform(0, 6.28)

    def loot(self):
        items = []
        gold = random.randint(*self.gold_range)
        if gold: items.append(("Gold Coin", gold))
        for name, qty, chance in self.drops:
            if random.random() < chance:
                items.append((name, qty))
        return items

    def draw(self, surf, cam_x, cam_y, tick):
        if not self.alive: return
        import math
        bob = int(2 * math.sin(tick * 0.05 + self._bob))
        sx = self.tx * TILE_SIZE - cam_x
        sy = self.ty * TILE_SIZE - cam_y - bob
        sz = TILE_SIZE - 4  # slightly bigger than before

        c = self.color
        dark = tuple(max(0, v - 50) for v in c)
        light = tuple(min(255, v + 60) for v in c)

        # Shadow ellipse
        sh = pygame.Surface((sz + 6, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 70), (0, 0, sz + 6, 10))
        surf.blit(sh, (sx - 1, sy + sz - 3))

        # --- Pixel-art chunky body shapes per enemy type ---
        if self.name == "Goblin":
            # Squat green humanoid — head + stout body
            # Legs
            pygame.draw.rect(surf, dark,  (sx + 4,  sy + sz - 10, 6, 10))  # left
            pygame.draw.rect(surf, dark,  (sx + sz - 10, sy + sz - 10, 6, 10))  # right
            pygame.draw.rect(surf, (0,0,0), (sx + 4, sy + sz - 10, 6, 10), 1)
            pygame.draw.rect(surf, (0,0,0), (sx + sz - 10, sy + sz - 10, 6, 10), 1)
            # Body
            pygame.draw.rect(surf, c,     (sx + 3, sy + sz // 2, sz - 6, sz // 2 - 6), border_radius=3)
            pygame.draw.rect(surf, (0,0,0),(sx + 3, sy + sz // 2, sz - 6, sz // 2 - 6), 1, border_radius=3)
            # Belly highlight
            pygame.draw.rect(surf, light, (sx + 6, sy + sz // 2 + 3, sz - 12, 5), border_radius=2)
            # Head (larger than body, round)
            head_r = sz // 3 + 1
            hcx = sx + sz // 2
            hcy = sy + sz // 2 - head_r + 2
            pygame.draw.circle(surf, c,     (hcx, hcy), head_r)
            pygame.draw.circle(surf, (0,0,0),(hcx, hcy), head_r, 1)
            # Ears (pointed)
            pygame.draw.polygon(surf, c,     [(hcx - head_r, hcy - 4), (hcx - head_r - 6, hcy - 14), (hcx - head_r + 4, hcy - 6)])
            pygame.draw.polygon(surf, c,     [(hcx + head_r, hcy - 4), (hcx + head_r + 6, hcy - 14), (hcx + head_r - 4, hcy - 6)])
            # Eyes — big red pixels
            pygame.draw.rect(surf, (255, 50, 50),  (hcx - 7, hcy - 3, 5, 5))
            pygame.draw.rect(surf, (255, 50, 50),  (hcx + 2, hcy - 3, 5, 5))
            pygame.draw.rect(surf, (0,0,0), (hcx - 6, hcy - 2, 3, 3))
            pygame.draw.rect(surf, (0,0,0), (hcx + 3, hcy - 2, 3, 3))

        elif self.name == "Cow":
            # Blocky white/cream body, black spots
            pygame.draw.rect(surf, c,      (sx + 2, sy + sz // 3, sz - 4, sz * 2 // 3 - 4), border_radius=4)
            pygame.draw.rect(surf, (0,0,0),(sx + 2, sy + sz // 3, sz - 4, sz * 2 // 3 - 4), 1, border_radius=4)
            # Spots
            pygame.draw.rect(surf, dark,   (sx + 8,  sy + sz // 2,     8, 6), border_radius=2)
            pygame.draw.rect(surf, dark,   (sx + sz - 14, sy + sz // 2 + 4, 6, 5), border_radius=2)
            # Head
            pygame.draw.rect(surf, c,      (sx + sz // 4, sy + 4, sz // 2, sz // 3 + 2), border_radius=4)
            pygame.draw.rect(surf, (0,0,0),(sx + sz // 4, sy + 4, sz // 2, sz // 3 + 2), 1, border_radius=4)
            # Horns
            pygame.draw.rect(surf, dark,   (sx + sz // 4 + 2, sy,     3, 6))
            pygame.draw.rect(surf, dark,   (sx + sz * 3 // 4 - 5, sy, 3, 6))
            # Eyes — black pixels
            ey = sy + sz // 3 - 4
            pygame.draw.rect(surf, (0,0,0),(sx + sz // 4 + 5,  ey, 4, 4))
            pygame.draw.rect(surf, (0,0,0),(sx + sz * 3 // 4 - 9, ey, 4, 4))
            # White eye gleam
            pygame.draw.rect(surf, WHITE,  (sx + sz // 4 + 6,  ey, 2, 2))
            pygame.draw.rect(surf, WHITE,  (sx + sz * 3 // 4 - 8, ey, 2, 2))

        elif self.name == "Wolf":
            # Sleek grey body, triangle ears
            # Body
            pygame.draw.rect(surf, c,      (sx + 3, sy + sz // 3 + 2, sz - 6, sz * 2 // 3 - 4), border_radius=3)
            pygame.draw.rect(surf, (0,0,0),(sx + 3, sy + sz // 3 + 2, sz - 6, sz * 2 // 3 - 4), 1, border_radius=3)
            # Fur lighter stripe on back
            pygame.draw.rect(surf, light,  (sx + sz // 4, sy + sz // 3 + 4, sz // 2, 5))
            # Head
            hcx = sx + sz // 2
            hcy = sy + sz // 3
            pygame.draw.rect(surf, c,      (hcx - sz // 4, hcy - sz // 5, sz // 2, sz // 3), border_radius=3)
            pygame.draw.rect(surf, (0,0,0),(hcx - sz // 4, hcy - sz // 5, sz // 2, sz // 3), 1, border_radius=3)
            # Ears (triangles)
            pygame.draw.polygon(surf, dark, [(hcx - sz // 5, hcy - sz // 5),
                                              (hcx - sz // 5 - 6, hcy - sz // 5 - 10),
                                              (hcx - sz // 5 + 5, hcy - sz // 5 - 2)])
            pygame.draw.polygon(surf, dark, [(hcx + sz // 5, hcy - sz // 5),
                                              (hcx + sz // 5 + 6, hcy - sz // 5 - 10),
                                              (hcx + sz // 5 - 5, hcy - sz // 5 - 2)])
            # Eyes — yellow pixels
            ey = hcy - sz // 5 + 4
            pygame.draw.rect(surf, (240, 200, 0), (hcx - 8, ey, 5, 4))
            pygame.draw.rect(surf, (240, 200, 0), (hcx + 3, ey, 5, 4))
            pygame.draw.rect(surf, (0,0,0),       (hcx - 7, ey + 1, 3, 2))
            pygame.draw.rect(surf, (0,0,0),       (hcx + 4, ey + 1, 3, 2))
            # Snout
            pygame.draw.rect(surf, light,  (hcx - 5, hcy - sz // 5 + 8, 10, 5), border_radius=2)
            pygame.draw.rect(surf, dark,   (hcx - 2, hcy - sz // 5 + 8, 4, 3))

        elif self.name == "Guard":
            # Armoured blue humanoid — rectangular metal look
            # Legs
            pygame.draw.rect(surf, dark,   (sx + 4, sy + sz - 10, 7, 10))
            pygame.draw.rect(surf, dark,   (sx + sz - 11, sy + sz - 10, 7, 10))
            pygame.draw.rect(surf, (0,0,0),(sx + 4, sy + sz - 10, 7, 10), 1)
            pygame.draw.rect(surf, (0,0,0),(sx + sz - 11, sy + sz - 10, 7, 10), 1)
            # Armour body — rectangular with highlight
            pygame.draw.rect(surf, c,      (sx + 3, sy + sz // 3 + 2, sz - 6, sz // 2), border_radius=2)
            pygame.draw.rect(surf, (0,0,0),(sx + 3, sy + sz // 3 + 2, sz - 6, sz // 2), 1, border_radius=2)
            pygame.draw.rect(surf, light,  (sx + 5, sy + sz // 3 + 4, sz - 10, 5))  # armor sheen
            # Shield on left arm
            pygame.draw.rect(surf, (100, 100, 120), (sx, sy + sz // 3 + 4, 5, 12), border_radius=1)
            pygame.draw.rect(surf, (180, 180, 200), (sx, sy + sz // 3 + 4, 5, 12), 1, border_radius=1)
            # Helmet
            pygame.draw.rect(surf, c,      (sx + sz // 4 - 1, sy + 2, sz // 2 + 2, sz // 3 + 2), border_radius=3)
            pygame.draw.rect(surf, (0,0,0),(sx + sz // 4 - 1, sy + 2, sz // 2 + 2, sz // 3 + 2), 1, border_radius=3)
            # Visor slit
            pygame.draw.rect(surf, (30, 30, 80), (sx + sz // 4 + 3, sy + sz // 3 - 4, sz // 2 - 6, 5))
            pygame.draw.rect(surf, (100, 120, 220),(sx + sz // 4 + 3, sy + sz // 3 - 3, sz // 2 - 6, 2))

        elif self.name == "Dark Mage":
            # Robed purple figure with glowing eyes
            # Robe
            pygame.draw.polygon(surf, c, [
                (sx + sz // 2, sy + 6),
                (sx + 2, sy + sz - 2),
                (sx + sz - 2, sy + sz - 2),
            ])
            pygame.draw.polygon(surf, (0,0,0), [
                (sx + sz // 2, sy + 6),
                (sx + 2, sy + sz - 2),
                (sx + sz - 2, sy + sz - 2),
            ], 1)
            # Inner robe shading
            pygame.draw.polygon(surf, dark, [
                (sx + sz // 2, sy + 12),
                (sx + 6, sy + sz - 4),
                (sx + sz - 6, sy + sz - 4),
            ])
            # Hood/head
            hcx = sx + sz // 2
            hcy = sy + sz // 4 + 2
            pygame.draw.circle(surf, dark,    (hcx, hcy), sz // 4 + 2)
            pygame.draw.circle(surf, (0,0,0), (hcx, hcy), sz // 4 + 2, 1)
            # Glowing purple eyes
            eye_col = (200, 100, 255)
            glow_scale = int(2 + math.sin(tick * 0.08) * 1)
            pygame.draw.rect(surf, eye_col, (hcx - 8, hcy - 2, 5 + glow_scale, 4))
            pygame.draw.rect(surf, eye_col, (hcx + 3, hcy - 2, 5 + glow_scale, 4))
            pygame.draw.rect(surf, WHITE,   (hcx - 7, hcy - 1, 3, 2))
            pygame.draw.rect(surf, WHITE,   (hcx + 4, hcy - 1, 3, 2))
            # Floating orb
            orb_ox = int(10 * math.cos(tick * 0.06))
            orb_oy = int(6  * math.sin(tick * 0.09))
            pygame.draw.circle(surf, (180, 80, 255), (hcx + 20 + orb_ox, hcy - 8 + orb_oy), 5)
            pygame.draw.circle(surf, WHITE,           (hcx + 20 + orb_ox, hcy - 8 + orb_oy), 2)

        else:
            # Generic fallback: simple rectangle
            pygame.draw.rect(surf, c,      (sx + 3, sy + 3, sz, sz), border_radius=4)
            pygame.draw.rect(surf, (0,0,0),(sx + 3, sy + 3, sz, sz), 1, border_radius=4)
            pygame.draw.rect(surf, light,  (sx + 5, sy + 5, sz - 4, sz // 3), border_radius=2)
            pygame.draw.circle(surf, (255, 80, 80), (sx + 9,   sy + 10), 3)
            pygame.draw.circle(surf, (255, 80, 80), (sx + sz - 5, sy + 10), 3)

        # HP bar (above sprite)
        bw = sz
        ratio = self.hp / max(1, self.max_hp)
        bar_col = NEON_GREEN if ratio > 0.5 else (GOLD if ratio > 0.25 else CRIMSON)
        pygame.draw.rect(surf, (40, 10, 10), (sx + 2, sy - 7, bw, 5), border_radius=2)
        pygame.draw.rect(surf, bar_col,      (sx + 2, sy - 7, max(2, int(bw * ratio)), 5), border_radius=2)
        pygame.draw.rect(surf, (0,0,0),      (sx + 2, sy - 7, bw, 5), 1, border_radius=2)

        # Name tag
        font = pygame.font.SysFont("Arial", 13, bold=True)
        lbl  = font.render(self.name, True, WHITE)
        sh2  = font.render(self.name, True, BLACK)
        surf.blit(sh2, (sx + sz // 2 - lbl.get_width() // 2 + 1, sy - 20))
        surf.blit(lbl, (sx + sz // 2 - lbl.get_width() // 2,     sy - 20))


class ResourceNode:
    def __init__(self, kind, tx, ty):
        self.kind  = kind
        self.tx    = tx; self.ty = ty
        self.depleted = False
        self.respawn_timer = 0
        RESPAWN = {"tree":300,"ore":450,"fish":200}
        self.respawn_max = RESPAWN.get(kind, 300)

    def update(self):
        if self.depleted:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.depleted = False

    def harvest(self, world, player):
        if self.depleted: return None, 0
        skill_map = {"tree":SK_WC,"ore":SK_MIN,"fish":SK_FISH}
        item_map  = {
            "tree": [("Logs",25),("Oak Logs",40)],
            "ore":  [("Copper Ore",17),("Iron Ore",35)],
            "fish": [("Raw Fish",20)],
        }
        sk_name = skill_map[self.kind]
        level   = player.skills[sk_name].level
        items   = item_map[self.kind]
        chosen  = items[min(len(items)-1, level//15)]
        item_name, xp = chosen
        if random.random() > min(0.9, 0.3 + level*0.03):
            return None, 0
        self.depleted = True
        self.respawn_timer = self.respawn_max
        if self.kind == "tree": world.set_tile(self.tx, self.ty, TILE_STUMP)
        elif self.kind == "ore": world.set_tile(self.tx, self.ty, TILE_ROCK)
        return item_name, xp


def _build_map():
    W, H = 60, 60
    tiles = [[TILE_GRASS]*W for _ in range(H)]
    rng = random.Random(42)
    for x in range(W):
        for y in range(H):
            if x<2 or x>=W-2 or y<2 or y>=H-2:
                tiles[y][x] = TILE_WATER
    for x in range(28,36):
        for y in range(10,16):
            tiles[y][x] = TILE_WATER
    for x in range(2,W-2): tiles[30][x] = TILE_PATH
    for y in range(2,H-2): tiles[y][30] = TILE_PATH
    for x in range(26,35):
        for y in range(26,35):
            if x in(26,34) or y in(26,34): tiles[y][x]=TILE_WALL
            else: tiles[y][x]=TILE_FLOOR
    tiles[26][30]=TILE_DOOR; tiles[34][30]=TILE_DOOR
    tiles[30][26]=TILE_DOOR; tiles[30][34]=TILE_DOOR
    for x in range(28,36):
        for y in range(16,19): tiles[y][x]=TILE_SAND
    trees=[]
    for (x1,y1,x2,y2) in [(5,5,20,25),(40,5,55,25),(5,35,20,55),(40,35,55,55)]:
        for x in range(x1,x2):
            for y in range(y1,y2):
                if tiles[y][x]==TILE_GRASS and rng.random()<0.4:
                    tiles[y][x]=TILE_TREE; trees.append((x,y))
    rocks=[]
    for (x1,y1,x2,y2) in [(5,35,20,55),(40,35,55,55)]:
        for x in range(x1,x2):
            for y in range(y1,y2):
                if tiles[y][x]==TILE_GRASS and rng.random()<0.15:
                    tiles[y][x]=TILE_ROCK; rocks.append((x,y))
    ores=[]
    for x in range(8,18):
        for y in range(38,50):
            if tiles[y][x]==TILE_ROCK and rng.random()<0.35:
                tiles[y][x]=TILE_ORE; ores.append((x,y))
    for x in range(2,W-2):
        for y in range(2,H-2):
            if tiles[y][x]==TILE_GRASS and rng.random()<0.04:
                tiles[y][x]=TILE_BUSH
    return tiles,W,H,trees,rocks,ores


class World:
    def __init__(self):
        self._tiles,self.width,self.height,tp,rp,op = _build_map()
        self.resource_nodes = []
        for tx,ty in tp: self.resource_nodes.append(ResourceNode("tree",tx,ty))
        for tx,ty in op: self.resource_nodes.append(ResourceNode("ore",tx,ty))
        for x in range(28,36): self.resource_nodes.append(ResourceNode("fish",x,16))
        rng=random.Random(7)
        self.enemies=[]
        spawns=[("Goblin",5,5,20,25),("Wolf",40,5,55,25),("Cow",20,35,40,55),
                ("Guard",40,35,55,55),("Dark Mage",5,35,15,50)]
        for ename,x1,y1,x2,y2 in spawns:
            for _ in range(6):
                for _ in range(20):
                    ex=rng.randint(x1,x2-1); ey=rng.randint(y1,y2-1)
                    if not self.is_solid(ex,ey):
                        self.enemies.append(Enemy(ename,ex,ey)); break
        self.tick = 0

    def tile(self,tx,ty):
        if 0<=tx<self.width and 0<=ty<self.height: return self._tiles[ty][tx]
        return TILE_WATER

    def set_tile(self,tx,ty,val):
        if 0<=tx<self.width and 0<=ty<self.height: self._tiles[ty][tx]=val

    def is_solid(self,tx,ty): return self.tile(tx,ty) in SOLID_TILES

    def get_node_at(self,tx,ty):
        for n in self.resource_nodes:
            if n.tx==tx and n.ty==ty and not n.depleted: return n
        return None

    def get_enemy_at(self,tx,ty):
        for e in self.enemies:
            if e.alive and e.tx==tx and e.ty==ty: return e
        return None

    def update(self):
        self.tick += 1
        for node in self.resource_nodes:
            node.update()
            if not node.depleted:
                if node.kind=="tree" and self.tile(node.tx,node.ty)==TILE_STUMP:
                    self.set_tile(node.tx,node.ty,TILE_TREE)
                elif node.kind=="ore" and self.tile(node.tx,node.ty)==TILE_ROCK:
                    self.set_tile(node.tx,node.ty,TILE_ORE)

    def draw(self, surf, cam_x, cam_y):
        t = self.tick
        sx0 = max(0, cam_x//TILE_SIZE)
        sy0 = max(0, cam_y//TILE_SIZE)
        ex0 = min(self.width,  sx0 + SCREEN_W//TILE_SIZE + 2)
        ey0 = min(self.height, sy0 + SCREEN_H//TILE_SIZE + 2)

        for ty in range(sy0, ey0):
            for tx in range(sx0, ex0):
                tid = self.tile(tx, ty)
                s   = get_tile_surf(tid, t)
                surf.blit(s, (tx*TILE_SIZE - cam_x, ty*TILE_SIZE - cam_y))

        for e in self.enemies:
            if e.alive:
                sx = e.tx*TILE_SIZE - cam_x
                sy = e.ty*TILE_SIZE - cam_y
                if -TILE_SIZE < sx < SCREEN_W and -TILE_SIZE < sy < SCREEN_H:
                    e.draw(surf, cam_x, cam_y, t)
