import pygame
import math
from constants import *
from renderer import draw_text_shadow, GOLD, DARK_GOLD

WHITE = (255,255,255)
GRAY  = (160,160,180)
BLACK = (0,0,0)
TAN   = (210,180,140)


class NPC:
    def __init__(self, name, tx, ty, color, role="talk", shop_inv=None, quest_id=None):
        self.name     = name
        self.tx       = tx
        self.ty       = ty
        self.color    = color
        self.role     = role
        self.shop_inv = shop_inv or []
        self.quest_id = quest_id
        self._bob_off = hash(name) % 100 / 100 * 6.28

    def draw(self, surf, cam_x, cam_y):
        t    = pygame.time.get_ticks() / 1000.0
        bob  = int(2 * math.sin(t * 1.5 + self._bob_off))
        sx   = self.tx * TILE_SIZE - cam_x + 3
        sy   = self.ty * TILE_SIZE - cam_y + bob

        # Shadow
        sh = pygame.Surface((22, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0,0,0,70), (0,0,22,6))
        surf.blit(sh, (sx+1, sy+26))

        # Body (robe)
        pygame.draw.rect(surf, self.color, (sx+3, sy+10, 20, 18), border_radius=4)
        pygame.draw.rect(surf, tuple(min(255,c+50) for c in self.color),
                         (sx+5, sy+12, 16, 6), border_radius=3)

        # Head
        pygame.draw.circle(surf, TAN,  (sx+13, sy+9), 8)
        pygame.draw.circle(surf, (180,140,100), (sx+13, sy+9), 8, 1)

        # Hat / role indicator
        if self.role == "quest":
            pygame.draw.polygon(surf, GOLD, [(sx+13,sy-4),(sx+5,sy+2),(sx+21,sy+2)])
            pygame.draw.rect(surf, DARK_GOLD, (sx+4, sy+2, 18, 3), border_radius=1)
        elif self.role == "shop":
            pygame.draw.rect(surf, (200,160,40), (sx+6, sy-4, 14, 8), border_radius=3)
            pygame.draw.line(surf, BLACK, (sx+6,sy-1),(sx+20,sy-1),1)

        # Interaction indicator (floating !)
        if self.role in ("quest",):
            pulse = int(180 + 60*math.sin(t*3))
            font  = pygame.font.SysFont("Arial", 16, bold=True)
            lbl   = font.render("!", True, (255,pulse,0))
            surf.blit(lbl, (sx+10, sy-16))

        # Name
        font = pygame.font.SysFont("Arial", 13)
        lbl  = font.render(self.name, True, WHITE)
        draw_text_shadow(surf, self.name, font, WHITE, sx+13-lbl.get_width()//2, sy-26, offset=1)

    def interact(self, player, quest_mgr):
        if self.role == "quest":
            return quest_mgr.npc_interact(self.quest_id, player, self.name)
        return [
            f"{self.name}:",
            "Welcome to SkillBound, adventurer!",
            "The land is full of danger — and opportunity.",
            "Speak to the Quest Giver for your first task.",
            "Visit the Shop to gear up before venturing out.",
        ]


def make_npcs():
    return [
        NPC("Elder Bob",    29, 29, (200,140,60), role="talk"),
        NPC("Quest Giver",  31, 29, (60,200,200), role="quest", quest_id="prove_yourself"),
        NPC("Shop",         29, 31, (200,180,40), role="shop",
            shop_inv=["Bronze Sword","Iron Sword","Steel Sword",
                      "Bronze Shield","Iron Shield","Leather Armour",
                      "Health Potion","Bread","Antidote"]),
    ]
