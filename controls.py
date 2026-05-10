"""
controls.py — Floating virtual joystick + ghost action buttons

Movement zone  : entire left half of screen (below the HUD)
  • Tap anywhere in that zone → joystick ring appears at that exact point
  • Drag to steer; direction uses the angle from the spawn point
  • Release → joystick fades out and disappears
  • Invisible at rest — does NOT clutter the screen

Action buttons : right side, always in place but nearly invisible at rest
  • Opacity ~18 when idle → 255 when pressed, then fade back
"""
import pygame
import math
from constants import SCREEN_W, SCREEN_H

WHITE = (255, 255, 255)

# ── Joystick tuning ───────────────────────────────────────────────────────────
JOY_OUTER_R  = 56      # outer ring radius
JOY_INNER_R  = 26      # inner nub radius
JOY_DEADZONE = 14      # px from centre before direction registers
JOY_MAX_DIST = JOY_OUTER_R - JOY_INNER_R + 4  # how far the nub can travel
MOVE_ZONE_X  = SCREEN_W // 2   # left half = movement zone
MOVE_ZONE_Y_MIN = 130           # below top HUD

# ── Button layout ─────────────────────────────────────────────────────────────
BTN_R   = 36
BTN_E   = (SCREEN_W - 72,  SCREEN_H - 95)
BTN_I   = (SCREEN_W - 168, SCREEN_H - 62)
BTN_K   = (SCREEN_W - 252, SCREEN_H - 62)
BTN_Q   = (SCREEN_W - 336, SCREEN_H - 62)

ACTION_BTNS = {"E": BTN_E, "I": BTN_I, "K": BTN_K, "Q": BTN_Q}
BTN_INFO    = {
    "E": ("E", "Act",    (220,  80,  80)),
    "I": ("I", "Bag",    ( 80, 160, 220)),
    "K": ("K", "Skills", ( 80, 200, 120)),
    "Q": ("Q", "Quest",  (220, 180,  60)),
}

# ── Alpha levels ──────────────────────────────────────────────────────────────
BTN_IDLE_ALPHA   = 18     # ghost — barely there
BTN_ACTIVE_ALPHA = 220    # lit up on press
BTN_FADE_SPEED   = 12     # alpha steps per frame when fading back

JOY_FADE_IN_SPEED  = 40   # alpha per frame when joystick appears
JOY_FADE_OUT_SPEED = 30   # alpha per frame when joystick disappears


class VirtualControls:
    def __init__(self):
        # Joystick state
        self._joy_active   = False    # finger is down in move zone
        self._joy_origin   = (0, 0)  # where the finger first landed
        self._joy_current  = (0, 0)  # current finger position
        self._joy_alpha    = 0        # current draw alpha (0=invisible)
        self._joy_fid      = None     # which finger/mouse controls it
        self._dx = 0
        self._dy = 0

        # Button state
        self._btn_alpha    = {k: BTN_IDLE_ALPHA for k in ACTION_BTNS}
        self._tapped       = set()
        self._btn_held     = set()   # for visual hold state

        self.visible = True

    # ── Public ────────────────────────────────────────────────────────────────
    @property
    def dx(self): return self._dx

    @property
    def dy(self): return self._dy

    def consume_taps(self):
        t = set(self._tapped)
        self._tapped.clear()
        return t

    def release_all(self):
        self._joy_active  = False
        self._joy_fid     = None
        self._dx = self._dy = 0
        self._btn_held.clear()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _in_move_zone(self, x, y):
        return x < MOVE_ZONE_X and y > MOVE_ZONE_Y_MIN

    def _action_at(self, x, y):
        for name, (bx, by) in ACTION_BTNS.items():
            if math.hypot(x - bx, y - by) < BTN_R + 8:
                return name
        return None

    def _calc_direction(self):
        ox, oy = self._joy_origin
        cx, cy = self._joy_current
        dx_raw = cx - ox
        dy_raw = cy - oy
        dist   = math.hypot(dx_raw, dy_raw)
        if dist < JOY_DEADZONE:
            self._dx = 0; self._dy = 0
            return
        # 8-direction snap
        angle = math.degrees(math.atan2(dy_raw, dx_raw))  # -180..180
        # Convert to nearest cardinal / diagonal
        sector = round(angle / 45) * 45   # snapped to 45° grid
        sector = sector % 360
        dx = round(math.cos(math.radians(sector)))
        dy = round(math.sin(math.radians(sector)))
        self._dx = dx
        self._dy = dy

    def _nub_pos(self):
        """Clamped nub screen position."""
        ox, oy = self._joy_origin
        cx, cy = self._joy_current
        dx_raw = cx - ox
        dy_raw = cy - oy
        dist   = math.hypot(dx_raw, dy_raw)
        if dist == 0:
            return ox, oy
        clamped = min(dist, JOY_MAX_DIST)
        nx = ox + dx_raw / dist * clamped
        ny = oy + dy_raw / dist * clamped
        return int(nx), int(ny)

    # ── Event handling ────────────────────────────────────────────────────────
    def _pos_from_event(self, event):
        if event.type in (pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP):
            return int(event.x * SCREEN_W), int(event.y * SCREEN_H)
        return event.pos

    def handle_event(self, event):
        if not self.visible:
            return False

        # ── Press ─────────────────────────────────────────────────────────────
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button != 1:
                return False
            x, y = self._pos_from_event(event)
            fid   = ("touch", event.finger_id) if event.type == pygame.FINGERDOWN else ("mouse", 1)

            # Action button?
            act = self._action_at(x, y)
            if act:
                self._tapped.add(act)
                self._btn_held.add(act)
                self._btn_alpha[act] = BTN_ACTIVE_ALPHA
                return True

            # Movement zone?
            if self._in_move_zone(x, y) and not self._joy_active:
                self._joy_active  = True
                self._joy_origin  = (x, y)
                self._joy_current = (x, y)
                self._joy_fid     = fid
                self._joy_alpha   = 0          # will fade in via update()
                self._dx = self._dy = 0
                return True

        # ── Move ──────────────────────────────────────────────────────────────
        elif event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
            fid = ("touch", event.finger_id) if event.type == pygame.FINGERMOTION else ("mouse", 1)
            if self._joy_active and fid == self._joy_fid:
                x, y = self._pos_from_event(event)
                self._joy_current = (x, y)
                self._calc_direction()
                return True

        # ── Release ───────────────────────────────────────────────────────────
        elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
            if event.type == pygame.MOUSEBUTTONUP and event.button != 1:
                return False
            fid = ("touch", event.finger_id) if event.type == pygame.FINGERUP else ("mouse", 1)

            if self._joy_active and fid == self._joy_fid:
                self._joy_active = False
                self._joy_fid    = None
                self._dx = self._dy = 0
                return True

            # Release held button
            x, y = self._pos_from_event(event)
            act = self._action_at(x, y)
            if act and act in self._btn_held:
                self._btn_held.discard(act)
                return True

        return False

    # ── Per-frame update (call every frame) ───────────────────────────────────
    def update(self):
        # Joystick alpha
        if self._joy_active:
            self._joy_alpha = min(200, self._joy_alpha + JOY_FADE_IN_SPEED)
        else:
            self._joy_alpha = max(0, self._joy_alpha - JOY_FADE_OUT_SPEED)

        # Button alpha fade-back
        for k in ACTION_BTNS:
            target = BTN_ACTIVE_ALPHA if k in self._btn_held else BTN_IDLE_ALPHA
            if self._btn_alpha[k] > target:
                self._btn_alpha[k] = max(target, self._btn_alpha[k] - BTN_FADE_SPEED)
            elif self._btn_alpha[k] < target:
                self._btn_alpha[k] = min(target, self._btn_alpha[k] + BTN_FADE_SPEED)

    # ── Drawing ───────────────────────────────────────────────────────────────
    def draw(self, surf):
        if not self.visible:
            return
        self._draw_joystick(surf)
        self._draw_action_buttons(surf)

    def _draw_joystick(self, surf):
        alpha = self._joy_alpha
        if alpha <= 0:
            return

        ox, oy = self._joy_origin
        nx, ny = self._nub_pos()

        # Outer ring
        ring = pygame.Surface((JOY_OUTER_R*2+4, JOY_OUTER_R*2+4), pygame.SRCALPHA)
        cx = cy = JOY_OUTER_R + 2
        pygame.draw.circle(ring, (255, 255, 255, int(alpha * 0.25)), (cx, cy), JOY_OUTER_R)
        pygame.draw.circle(ring, (255, 255, 255, int(alpha * 0.80)), (cx, cy), JOY_OUTER_R, 2)
        surf.blit(ring, (ox - cx, oy - cy))

        # Direction lines (cross hair — very subtle)
        cross = pygame.Surface((JOY_OUTER_R*2+4, JOY_OUTER_R*2+4), pygame.SRCALPHA)
        lc = (255, 255, 255, int(alpha * 0.18))
        pygame.draw.line(cross, lc, (cx - JOY_OUTER_R + 6, cy), (cx + JOY_OUTER_R - 6, cy), 1)
        pygame.draw.line(cross, lc, (cx, cy - JOY_OUTER_R + 6), (cx, cy + JOY_OUTER_R - 6), 1)
        surf.blit(cross, (ox - cx, oy - cy))

        # Inner nub
        nub = pygame.Surface((JOY_INNER_R*2+2, JOY_INNER_R*2+2), pygame.SRCALPHA)
        nc  = JOY_INNER_R + 1
        pygame.draw.circle(nub, (180, 200, 255, int(alpha * 0.55)), (nc, nc), JOY_INNER_R)
        pygame.draw.circle(nub, (220, 235, 255, int(alpha * 0.95)), (nc, nc), JOY_INNER_R, 2)
        surf.blit(nub, (nx - nc, ny - nc))

    def _draw_action_buttons(self, surf):
        font_b = pygame.font.SysFont("Arial", 20, bold=True)
        font_s = pygame.font.SysFont("Arial", 12)

        for key, (bx, by) in ACTION_BTNS.items():
            label, sublabel, col = BTN_INFO[key]
            alpha = self._btn_alpha[key]

            btn = pygame.Surface((BTN_R*2, BTN_R*2), pygame.SRCALPHA)
            pygame.draw.circle(btn, (*col, int(alpha * 0.55)), (BTN_R, BTN_R), BTN_R)
            pygame.draw.circle(btn, (*col, alpha),             (BTN_R, BTN_R), BTN_R, 2)
            surf.blit(btn, (bx - BTN_R, by - BTN_R))

            # Letter — scales with alpha
            txt_alpha = max(30, alpha)
            k = font_b.render(label, True, WHITE)
            k.set_alpha(txt_alpha)
            surf.blit(k, (bx - k.get_width()//2, by - k.get_height()//2 - 3))

            # Sub-label only when almost fully visible
            if alpha > 80:
                s = font_s.render(sublabel, True, (200, 200, 220))
                s.set_alpha(alpha)
                surf.blit(s, (bx - s.get_width()//2, by + BTN_R + 3))


# ── Click helpers ─────────────────────────────────────────────────────────────
def point_in_rect(px, py, rx, ry, rw, rh):
    return rx <= px <= rx + rw and ry <= py <= ry + rh

def point_in_circle(px, py, cx, cy, r):
    return math.hypot(px - cx, py - cy) <= r
