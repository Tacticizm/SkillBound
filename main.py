import pygame
import sys
import asyncio
from constants import *
from player import Player
from world import World
from combat import CombatSystem
from npc import make_npcs
from quest import QuestManager
from ui import HUD, InventoryMenu, SkillsMenu, QuestMenu, DialogBox, ShopMenu, SkillBadgeBar
from titlescreen import TitleScreen
from controls import VirtualControls
from renderer import (ParticleSystem, ScreenShake, Transition,
                      draw_vignette, GOLD, CRIMSON, NEON_GREEN,
                      draw_text_shadow)

WHITE = (255,255,255)
GRAY  = (160,160,180)
BLACK = (0,0,0)


# ── Camera ────────────────────────────────────────────────────────────────────
def camera(player, world, shake):
    cx = int(player.x + player.size//2 - SCREEN_W//2)
    cy = int(player.y + player.size//2 - SCREEN_H//2)
    cx = max(0, min(cx, world.width  * TILE_SIZE - SCREEN_W))
    cy = max(0, min(cy, world.height * TILE_SIZE - SCREEN_H))
    ox, oy = shake.offset()
    return cx + ox, cy + oy


def tiles_adjacent(player):
    cx = int(player.x + player.size//2)
    cy = int(player.y + player.size//2)
    tx, ty = cx//TILE_SIZE, cy//TILE_SIZE
    return [(tx+dx, ty+dy) for dx,dy in [(0,0),(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,1),(1,-1),(-1,-1)]]


def try_interact(player, world, npcs, quest_mgr, dialog_box, shop_menu, combat):
    if player.resource_cooldown > 0:
        return None
    ptx, pty = player.get_tile_pos()
    # NPCs
    for npc in npcs:
        if abs(npc.tx - ptx) <= 1 and abs(npc.ty - pty) <= 1:
            if npc.role == "shop":
                shop_menu.open(npc, player); return "shop"
            else:
                lines = npc.interact(player, quest_mgr)
                dialog_box.open(lines); return "dialog"
    # Enemies
    for tx, ty in tiles_adjacent(player):
        e = world.get_enemy_at(tx, ty)
        if e and e.alive:
            combat.start(player, e, world); return "combat"
    # Resource nodes
    for tx, ty in tiles_adjacent(player):
        node = world.get_node_at(tx, ty)
        if node:
            item_name, xp = node.harvest(world, player)
            if item_name:
                player.inventory.add(item_name)
                player.add_xp({"tree":SK_WC,"ore":SK_MIN,"fish":SK_FISH}[node.kind], xp)
                quest_mgr.notify("gather", item_name)
                quest_mgr.check_have(player)
                player.resource_cooldown = 40
                return f"gathered:{item_name}:{xp}"
    return None


# ── Notification system ───────────────────────────────────────────────────────
class Notification:
    def __init__(self):
        self.queue  = []
        self.current= None
        self.timer  = 0

    def push(self, text, color=WHITE, duration=130):
        self.queue.append((text, color, duration))

    def update(self):
        if self.timer > 0:
            self.timer -= 1
        elif self.queue:
            self.current, col, dur = self.queue.pop(0)
            self._col   = col
            self.timer  = dur
        else:
            self.current = None

    def draw(self, surf):
        if not self.current or self.timer <= 0:
            return
        font = pygame.font.SysFont("Arial", 22, bold=True)
        alpha = min(255, self.timer * 6)
        lbl = font.render(self.current, True, self._col)
        tmp = pygame.Surface(lbl.get_size(), pygame.SRCALPHA)
        tmp.blit(lbl, (0,0))
        tmp.set_alpha(alpha)
        sx = SCREEN_W//2 - lbl.get_width()//2
        sy = SCREEN_H - 175
        # Backing pill
        pill = pygame.Surface((lbl.get_width()+24, 30), pygame.SRCALPHA)
        pygame.draw.rect(pill, (0,0,0,150), (0,0,lbl.get_width()+24,30), border_radius=8)
        surf.blit(pill, (sx-12, sy-4))
        surf.blit(tmp, (sx, sy))


# ── Main ──────────────────────────────────────────────────────────────────────
async def fade_to_black(clock, surf, draw_fn, speed=10):
    """Draw draw_fn each frame while overlaying a fade-to-black."""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H))
    overlay.fill(BLACK)
    for alpha in range(0, 256, speed):
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        draw_fn(surf)
        overlay.set_alpha(alpha)
        surf.blit(overlay, (0, 0))
        pygame.display.flip()
        await asyncio.sleep(0)
    surf.fill(BLACK)
    pygame.display.flip()
    await asyncio.sleep(0)


async def fade_from_black(clock, surf, speed=8):
    """Fade in from a black screen (call right after the scene is first drawn)."""
    overlay = pygame.Surface((SCREEN_W, SCREEN_H))
    overlay.fill(BLACK)
    for alpha in range(255, -1, -speed):
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        overlay.set_alpha(alpha)
        surf.blit(overlay, (0, 0))
        pygame.display.flip()
        await asyncio.sleep(0)


async def run_title(clock, surf):
    title = TitleScreen()
    surf.fill(BLACK)
    pygame.display.flip()
    faded_in = False

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            title.handle_event(event)

        title.update()
        title.draw(surf)
        pygame.display.flip()

        if not faded_in:
            await fade_from_black(clock, surf, speed=8)
            faded_in = True

        if title.done:
            if title.action == "quit":
                pygame.quit(); sys.exit()
            await fade_to_black(clock, surf, lambda s: title.draw(s), speed=10)
            return

        await asyncio.sleep(0)


async def run_game(clock, surf):
    world    = World()
    player   = Player(30, 32)
    npcs     = make_npcs()
    quest_mgr= QuestManager()

    dialog   = DialogBox()
    shop     = ShopMenu()
    combat   = CombatSystem()
    hud      = HUD()
    skill_bar= SkillBadgeBar()
    inv_menu = InventoryMenu()
    sk_menu  = SkillsMenu()
    q_menu   = QuestMenu()
    particles   = ParticleSystem()
    world_shake = ScreenShake()
    notif       = Notification()
    vpad        = VirtualControls()
    game_faded_in = False

    def notify(text, color=WHITE, dur=130):
        notif.push(text, color, dur)

    def do_interact():
        result = try_interact(player, world, npcs, quest_mgr, dialog, shop, combat)
        if result and result.startswith("gathered:"):
            parts = result.split(":")
            item  = parts[1]
            xp    = parts[2] if len(parts) > 2 else "?"
            notify(f"Gathered {item}  (+{xp} XP)", NEON_GREEN, 110)
            cam_x, cam_y = camera(player, world, world_shake)
            cx = int(player.x + player.size//2 - cam_x)
            cy = int(player.y - cam_y)
            particles.sparkle(cx, cy, GOLD, count=8)

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- Combat ---
            if combat.active:
                # Touch: tap anywhere on result screen to continue
                if combat.phase == "result":
                    dismiss = (
                        (event.type == pygame.KEYDOWN and
                         event.key in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE))
                        or event.type == pygame.MOUSEBUTTONDOWN
                        or event.type == pygame.FINGERDOWN
                    )
                    if dismiss:
                        outcome    = combat.outcome
                        enemy_name = combat.enemy.name if combat.enemy else None
                        if outcome == "lose":
                            player.x = 30 * TILE_SIZE
                            player.y = 32 * TILE_SIZE
                            notify("You respawn at town...", CRIMSON, 180)
                            world_shake.shake(8, 20)
                        elif outcome == "win" and enemy_name:
                            world_shake.shake(4, 10)
                            # Snapshot BEFORE applying the kill
                            pre_qty    = {
                                (q.id, i): obj["qty"]
                                for q in quest_mgr.quests.values()
                                for i, obj in enumerate(q.objectives)
                                if obj["type"] == "kill" and obj["target"] == enemy_name and not obj["done"]
                            }
                            pre_status = {q.id: q.status for q in quest_mgr.quests.values()}
                            # Apply kill
                            quest_mgr.notify("kill", enemy_name)
                            quest_mgr.check_have(player)
                            # Show progress notifications by comparing snapshots
                            for q in quest_mgr.quests.values():
                                for i, obj in enumerate(q.objectives):
                                    if obj["type"] == "kill" and obj["target"] == enemy_name:
                                        key = (q.id, i)
                                        if key in pre_qty:
                                            if obj["done"]:
                                                notify(f"✦ Objective done: {obj['desc']}!", NEON_GREEN, 200)
                                            elif obj["qty"] < pre_qty[key]:
                                                notify(f"Quest: {obj['desc']}  ({obj['qty']} left)", GOLD, 140)
                                # Only show "ready" banner the moment it transitions
                                if q.status == "ready" and pre_status.get(q.id) != "ready":
                                    notify(f"✦ Quest complete! Talk to Quest Giver: {q.title}", GOLD, 260)
                        combat.reset()
                        vpad.release_all()
                else:
                    combat.handle_event(event)
                continue

            # --- Open menus eat input ---
            if dialog.active:
                # Tap anywhere to advance dialog
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                    dialog.handle_event(pygame.event.Event(
                        pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode=""))
                else:
                    dialog.handle_event(event)
                continue
            if shop.active:
                shop.handle_event(event)
                # touch scroll in shop
                if event.type == pygame.MOUSEBUTTONDOWN:
                    shop.handle_click(event.pos)
                continue
            if inv_menu.active:
                inv_menu.handle_event(event, player)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    inv_menu.handle_click(event.pos, player)
                continue
            if sk_menu.active:
                sk_menu.handle_event(event)
                continue
            if q_menu.active:
                q_menu.handle_event(event, quest_mgr)
                continue

            # --- Virtual pad (world state only) ---
            if vpad.handle_event(event):
                continue

            # --- Keyboard ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:    inv_menu.toggle()
                elif event.key == pygame.K_k:  sk_menu.toggle()
                elif event.key == pygame.K_q:  q_menu.toggle()
                elif event.key == pygame.K_e:  do_interact()

        # --- Virtual button taps ---
        taps = vpad.consume_taps()
        if "E" in taps:  do_interact()
        if "I" in taps:  inv_menu.toggle()
        if "K" in taps:  sk_menu.toggle()
        if "Q" in taps:  q_menu.toggle()

        # --- Movement ---
        any_menu = any([combat.active, dialog.active, shop.active,
                        inv_menu.active, sk_menu.active, q_menu.active])
        if not any_menu:
            keys = pygame.key.get_pressed()
            kb_dx = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT]  or keys[pygame.K_a])
            kb_dy = int(keys[pygame.K_DOWN]  or keys[pygame.K_s]) - int(keys[pygame.K_UP]    or keys[pygame.K_w])
            dx = kb_dx or vpad.dx
            dy = kb_dy or vpad.dy
            if dx or dy:
                player.move(dx, dy, world)
                for e in world.enemies:
                    if e.alive:
                        if (abs(player.x - e.tx*TILE_SIZE) < TILE_SIZE-4 and
                                abs(player.y - e.ty*TILE_SIZE) < TILE_SIZE-4):
                            combat.start(player, e, world)
                            vpad.release_all()
                            break
            else:
                player.moving = False

        # Update
        world.update()
        combat.update()
        shop.update()
        inv_menu.update()
        particles.update()
        world_shake.update()
        notif.update()
        vpad.update()
        quest_mgr.check_have(player)
        if player.resource_cooldown > 0:
            player.resource_cooldown -= 1

        # Level-up particles
        if player.level_up_msg:
            cam_x, cam_y = camera(player, world, world_shake)
            px = int(player.x - cam_x + player.size//2)
            py = int(player.y - cam_y)
            particles.level_up_burst(px, py)

        # Draw world
        cam_x, cam_y = camera(player, world, world_shake)
        surf.fill((8,10,20))
        world.draw(surf, cam_x, cam_y)
        for npc in npcs:
            npc.draw(surf, cam_x, cam_y)
        player.draw(surf, cam_x, cam_y)
        particles.draw(surf)

        draw_vignette(surf, strength=120)

        # UI
        hud.draw(surf, player, world, cam_x, cam_y)

        # Detect nearby resource skill for badge highlight
        _nearby_skill = None
        for tx, ty in tiles_adjacent(player):
            node = world.get_node_at(tx, ty)
            if node:
                _nearby_skill = {
                    "tree": SK_WC,
                    "ore":  SK_MIN,
                    "fish": SK_FISH,
                }.get(node.kind)
                break
        # Show badge bar only when no overlay menu is open
        if not any([combat.active, dialog.active, shop.active,
                    inv_menu.active, sk_menu.active, q_menu.active]):
            skill_bar.draw(surf, player, nearby_skill=_nearby_skill)

        notif.draw(surf)

        # Virtual controls (hide when a menu is open to give menus full screen)
        if not any([combat.active, dialog.active, shop.active,
                    inv_menu.active, sk_menu.active, q_menu.active]):
            vpad.draw(surf)

        combat.draw(surf)
        dialog.draw(surf)
        shop.draw(surf)
        inv_menu.draw(surf, player)
        sk_menu.draw(surf, player)
        q_menu.draw(surf, quest_mgr)

        pygame.display.flip()

        # Fade in from black on the very first game frame
        if not game_faded_in:
            await fade_from_black(clock, surf, speed=8)
            game_faded_in = True

        await asyncio.sleep(0)


async def main():
    pygame.init()
    surf  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("SkillBound")
    clock = pygame.time.Clock()

    icon = pygame.Surface((32,32))
    icon.fill((30,20,60))
    pygame.draw.rect(icon, (255,210,50), (4,4,24,24), border_radius=4)
    pygame.draw.rect(icon, (200,30,50),  (10,10,12,12), border_radius=2)
    pygame.display.set_icon(icon)

    await run_title(clock, surf)
    await run_game(clock, surf)


if __name__ == "__main__":
    asyncio.run(main())
