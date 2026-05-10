import pygame
from constants import *


class Quest:
    def __init__(self, qid, title, description, objectives, rewards):
        self.id          = qid
        self.title       = title
        self.description = description
        self.objectives  = objectives   # list of {"desc", "type", "target", "qty", "done"}
        self.rewards     = rewards      # {"xp": {sk: amt}, "gold": n, "items": [(name,qty)]}
        self.status      = "available"  # available | active | complete

    def progress(self, event_type, target, qty=1):
        if self.status != "active":
            return False
        changed = False
        for obj in self.objectives:
            if obj["type"] == event_type and obj["target"] == target and not obj["done"]:
                obj["qty"] = max(0, obj["qty"] - qty)
                if obj["qty"] == 0:
                    obj["done"] = True
                    changed = True
        if all(o["done"] for o in self.objectives):
            self.status = "ready"
        return changed

    def is_complete(self):
        return self.status in ("complete",)

    def claim_reward(self, player):
        if self.status != "ready":
            return False
        r = self.rewards
        for sk, xp in r.get("xp", {}).items():
            player.add_xp(sk, xp)
        player.gold += r.get("gold", 0)
        for name, qty in r.get("items", []):
            player.inventory.add(name, qty)
        self.status = "complete"
        return True

    def summary(self):
        lines = [self.description, ""]
        for obj in self.objectives:
            mark = "[x]" if obj["done"] else f"[ ] ({obj['qty']} left)"
            lines.append(f"{mark} {obj['desc']}")
        return lines


def make_quests():
    return [
        Quest(
            "prove_yourself",
            "Prove Yourself",
            "The Elder wants you to prove your worth.",
            objectives=[
                {"desc": "Defeat 5 Goblins", "type": "kill",    "target": "Goblin", "qty": 5,  "done": False},
                {"desc": "Gather 5 Logs",     "type": "gather",  "target": "Logs",   "qty": 5,  "done": False},
                {"desc": "Mine 3 Copper Ore", "type": "gather",  "target": "Copper Ore", "qty": 3, "done": False},
            ],
            rewards={"xp": {SK_ATK: 200, SK_WC: 150, SK_MIN: 100}, "gold": 100,
                     "items": [("Iron Sword", 1), ("Health Potion", 3)]},
        ),
        Quest(
            "wolf_hunter",
            "Wolf Hunter",
            "Clear the northern woods of wolves.",
            objectives=[
                {"desc": "Defeat 3 Wolves", "type": "kill", "target": "Wolf", "qty": 3, "done": False},
                {"desc": "Collect 2 Wolf Pelts", "type": "have", "target": "Wolf Pelt", "qty": 2, "done": False},
            ],
            rewards={"xp": {SK_ATK: 400, SK_DEF: 200}, "gold": 200,
                     "items": [("Leather Armour", 1)]},
        ),
    ]


class QuestManager:
    def __init__(self):
        self.quests = {q.id: q for q in make_quests()}

    def notify(self, event_type, target, qty=1):
        for q in self.quests.values():
            q.progress(event_type, target, qty)

    def check_have(self, player):
        for q in self.quests.values():
            if q.status == "active":
                for obj in q.objectives:
                    if obj["type"] == "have" and not obj["done"]:
                        held = player.inventory.count(obj["target"])
                        if held >= obj["qty"]:
                            obj["qty"] = 0
                            obj["done"] = True
                if all(o["done"] for o in q.objectives):
                    q.status = "ready"

    def npc_interact(self, quest_id, player, npc_name):
        q = self.quests.get(quest_id)
        if not q:
            return [f"{npc_name}: Nothing for you right now."]
        if q.status == "available":
            q.status = "active"
            lines = [f"{npc_name}: I have a task for you!", f'Quest started: "{q.title}"', ""]
            lines += q.summary()
            return lines
        elif q.status == "active":
            lines = [f"{npc_name}: Keep at it!  Quest: {q.title}", ""]
            lines += q.summary()
            return lines
        elif q.status == "ready":
            q.claim_reward(player)
            r = q.rewards
            lines = [f'{npc_name}: Well done! Quest "{q.title}" complete!',
                     f'+{r.get("gold",0)}gp, XP rewards granted!']
            for name, qty in r.get("items", []):
                lines.append(f'  + {qty}x {name}')
            return lines
        else:
            return [f"{npc_name}: You've already proven yourself!", "Quest complete."]


class DialogBox:
    def __init__(self):
        self.active  = False
        self.lines   = []
        self.page    = 0
        self.per_page= 6

    def open(self, lines):
        self.active = True
        self.lines  = lines
        self.page   = 0

    def close(self):
        self.active = False
        self.lines  = []
        self.page   = 0

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_z, pygame.K_ESCAPE, pygame.K_SPACE):
            total_pages = max(1, (len(self.lines) + self.per_page - 1) // self.per_page)
            if self.page < total_pages - 1:
                self.page += 1
            else:
                self.close()

    def draw(self, surf):
        if not self.active:
            return
        font = pygame.font.SysFont(None, 24)
        bw, bh = 700, 200
        bx, by = (SCREEN_W - bw)//2, SCREEN_H - bh - 20
        pygame.draw.rect(surf, DGRAY, (bx, by, bw, bh), border_radius=8)
        pygame.draw.rect(surf, WHITE, (bx, by, bw, bh), 2, border_radius=8)
        start = self.page * self.per_page
        visible = self.lines[start:start + self.per_page]
        for i, line in enumerate(visible):
            surf.blit(font.render(line, True, WHITE), (bx+14, by+12+i*28))
        total_pages = max(1, (len(self.lines) + self.per_page - 1) // self.per_page)
        hint = f"[ENTER] {'next' if self.page < total_pages-1 else 'close'}"
        hs = pygame.font.SysFont(None, 18).render(hint, True, GRAY)
        surf.blit(hs, (bx + bw - hs.get_width() - 10, by + bh - 20))
