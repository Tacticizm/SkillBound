"""
combat.py — Real-time action combat (no battle screen)

Player and enemies auto-attack when in range.
Enemies chase the player when aggroed.
No overlay, no menu — everything happens live in the world.
"""
import math
import random
import pygame
from constants import *
from renderer import ParticleSystem, ScreenShake, GOLD, CRIMSON, NEON_GREEN

WHITE = (255, 255, 255)
GRAY  = (160, 160, 180)
BLACK = (0, 0, 0)

# Tuning knobs
PLAYER_ATTACK_CD = 42    # frames between player swings (~0.7 s at 60 fps)
ATTACK_RANGE     = 52    # pixel radius for melee contact
AGGRO_RANGE      = 160   # pixel radius enemies start chasing (default)
LEASH_RANGE      = 320   # pixel radius — enemy gives up and wanders back


class RealTimeCombat:
    """Manages all real-time combat: aggro, movement, auto-attacks, loot, quests."""

    # ── properties that old main.py code used ────────────────────────────────
    # Keep stubs so nothing in main.py needs to change for draw/event routing.
    active = False      # never blocks the main event loop
    phase  = "none"
    outcome= None

    def __init__(self):
        self.particles          = ParticleSystem()
        self.player_attack_timer= 0
        self._dead_this_frame   = []   # enemies killed this frame (for notify)

    # Legacy stubs so old call sites don't crash
    def reset(self): pass
    def start(self, player, enemy, world): pass
    def handle_event(self, event): pass

    # ── Core update ──────────────────────────────────────────────────────────
    def update(self, player, enemies, world, cam_x, cam_y,
               quest_mgr, notify, world_shake):
        """Call once per frame. Handles enemy AI, attacks, deaths."""
        self.particles.update()
        self._dead_this_frame.clear()

        if self.player_attack_timer > 0:
            self.player_attack_timer -= 1

        px = player.x + player.size // 2
        py = player.y + player.size // 2

        for e in enemies:
            if not e.alive:
                continue

            ex = e.px + TILE_SIZE // 2
            ey = e.py + TILE_SIZE // 2
            dist = math.hypot(px - ex, py - ey)

            # ── Aggro / movement ──
            if dist < e.aggro_range:
                e.aggroed = True
            if dist > LEASH_RANGE:
                e.aggroed = False
                e.wander_timer = 0          # snap back to idle

            if e.aggroed and dist > ATTACK_RANGE - 4:
                # Move toward player
                angle = math.atan2(py - ey, px - ex)
                step  = min(e.move_speed, dist - ATTACK_RANGE + 8)
                nx    = e.px + math.cos(angle) * step
                ny    = e.py + math.sin(angle) * step
                # Tile collision (check centre of enemy)
                ntx = int((nx + TILE_SIZE // 2) // TILE_SIZE)
                nty = int((ny + TILE_SIZE // 2) // TILE_SIZE)
                if not world.is_solid(ntx, nty):
                    e.px = nx
                    e.py = ny
                    e.tx = ntx
                    e.ty = nty
            else:
                # Idle wander
                e.wander_timer -= 1
                if e.wander_timer <= 0:
                    e.wander_dx = random.choice([-1, 0, 0, 1])
                    e.wander_dy = random.choice([-1, 0, 0, 1])
                    e.wander_timer = random.randint(40, 100)
                if e.wander_dx or e.wander_dy:
                    nx = e.px + e.wander_dx * 0.5
                    ny = e.py + e.wander_dy * 0.5
                    ntx = int((nx + TILE_SIZE // 2) // TILE_SIZE)
                    nty = int((ny + TILE_SIZE // 2) // TILE_SIZE)
                    if not world.is_solid(ntx, nty):
                        e.px = nx
                        e.py = ny
                        e.tx = ntx
                        e.ty = nty

            # ── Enemy attacks player ──
            if dist < ATTACK_RANGE:
                e.attack_timer -= 1
                if e.attack_timer <= 0:
                    e.attack_timer = e.attack_speed
                    dmg = self._enemy_damage(player, e)
                    player.hp = max(0, player.hp - dmg)
                    world_shake.shake(5, 12)
                    # Damage number at player screen pos
                    sx = int(player.x + player.size // 2 - cam_x)
                    sy = int(player.y - cam_y)
                    self.particles.damage_number(sx, sy - 24, dmg, is_player_hit=True)
                    self.particles.burst(sx, sy, CRIMSON, count=6, speed=2.0)

        # ── Player auto-attacks nearest enemy in range ──
        if self.player_attack_timer == 0:
            target = self._nearest_in_range(player, enemies)
            if target:
                self._player_attack(player, target, enemies, world,
                                    cam_x, cam_y, quest_mgr, notify, world_shake)
                self.player_attack_timer = PLAYER_ATTACK_CD

        # ── Player death → respawn ──
        if player.hp <= 0:
            player.hp = player.max_hp // 2
            player.x  = 30 * TILE_SIZE
            player.y  = 32 * TILE_SIZE
            notify("You were defeated... respawning at town!", CRIMSON, 200)
            world_shake.shake(10, 20)

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _nearest_in_range(self, player, enemies):
        px = player.x + player.size // 2
        py = player.y + player.size // 2
        best, best_d = None, ATTACK_RANGE
        for e in enemies:
            if not e.alive:
                continue
            ex = e.px + TILE_SIZE // 2
            ey = e.py + TILE_SIZE // 2
            d  = math.hypot(px - ex, py - ey)
            if d < best_d:
                best, best_d = e, d
        return best

    def _player_damage(self, player):
        hi  = max(1, player.attack_bonus)
        lo  = max(1, hi // 2)
        return random.randint(lo, hi)

    def _enemy_damage(self, player, enemy):
        hi  = max(1, enemy.atk)
        lo  = max(1, hi // 2)
        red = random.randint(0, max(0, player.defence_bonus // 2))
        return max(1, random.randint(lo, hi) - red)

    def _player_attack(self, player, enemy, enemies, world,
                       cam_x, cam_y, quest_mgr, notify, world_shake):
        dmg = self._player_damage(player)
        enemy.hp = max(0, enemy.hp - dmg)
        enemy.flash_timer = 8

        # Screen-space position of enemy centre
        sx = int(enemy.px + TILE_SIZE // 2 - cam_x)
        sy = int(enemy.py - cam_y)

        self.particles.damage_number(sx, sy - 20, dmg, is_player_hit=False)
        self.particles.burst(sx, sy, GOLD, count=8, speed=2.5)
        world_shake.shake(3, 6)

        if enemy.hp <= 0:
            self._kill(player, enemy, sx, sy, quest_mgr, notify)

    def _kill(self, player, enemy, sx, sy, quest_mgr, notify):
        enemy.alive = False

        # XP
        xp = enemy.xp
        player.add_xp(SK_ATK, xp // 2)
        player.add_xp(SK_DEF, xp // 4)
        player.add_xp(SK_HP,  xp // 4)

        # Loot
        gold_gained = 0
        loot_names  = []
        for name, qty in enemy.loot():
            if name == "Gold Coin":
                player.gold += qty
                gold_gained += qty
            else:
                player.inventory.add(name, qty)
                loot_names.append(f"{name} x{qty}")

        # Victory notification
        msg = f"⚔ {enemy.name} defeated!  +{xp} XP"
        if gold_gained:
            msg += f"  🪙+{gold_gained}gp"
        notify(msg, GOLD, 160)

        # Particle burst
        self.particles.burst(sx, sy, GOLD,          count=24, speed=5.0)
        self.particles.burst(sx, sy, (255, 255, 180), count=10, speed=3.0)
        self.particles.xp_text(sx, sy, "Combat", xp)

        # Quest kill tracking
        if quest_mgr:
            pre_status = {q.id: q.status for q in quest_mgr.quests.values()}
            pre_qty = {
                (q.id, i): obj["qty"]
                for q in quest_mgr.quests.values()
                for i, obj in enumerate(q.objectives)
                if obj["type"] == "kill"
                   and obj["target"] == enemy.name
                   and not obj["done"]
            }
            quest_mgr.notify("kill", enemy.name)
            quest_mgr.check_have(player)

            for q in quest_mgr.quests.values():
                for i, obj in enumerate(q.objectives):
                    if obj["type"] == "kill" and obj["target"] == enemy.name:
                        key = (q.id, i)
                        if key in pre_qty:
                            if obj["done"]:
                                notify(f"✦ Objective done: {obj['desc']}!", NEON_GREEN, 200)
                            elif obj["qty"] < pre_qty[key]:
                                notify(f"Quest: {obj['desc']}  ({obj['qty']} left)", GOLD, 140)
                if q.status == "ready" and pre_status.get(q.id) != "ready":
                    notify(f"✦ Quest complete! Talk to Quest Giver: {q.title}", GOLD, 260)

    # ── Draw (particles only — no overlay) ──────────────────────────────────
    def draw(self, surf):
        self.particles.draw(surf)
