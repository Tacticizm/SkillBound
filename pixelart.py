"""
pixelart.py — 8x8 pixel art tile patterns scaled 4x to 32x32
Each pattern is a 2D list (8 rows x 8 cols) of palette indices.
Palettes are tuples of RGB colors.
"""
import pygame
import random
from constants import (
    TILE_GRASS, TILE_WATER, TILE_TREE, TILE_ROCK, TILE_PATH,
    TILE_WALL, TILE_FLOOR, TILE_DOOR, TILE_BUSH, TILE_STUMP,
    TILE_ORE, TILE_SAND, TILE_SIZE
)

# ── Richer palette colors ─────────────────────────────────────────────────────
# Warm greens for grass
GRASS_PAL = [
    (34, 95, 34),    # 0 base warm green
    (28, 80, 28),    # 1 dark patch
    (42, 108, 32),   # 2 bright highlight
    (50, 115, 40),   # 3 lightest
    (22, 68, 22),    # 4 darkest shadow
]

# Deep forest greens for trees
TREE_PAL = [
    (15, 60, 15),    # 0 deep forest base
    (20, 80, 20),    # 1 mid green
    (10, 45, 10),    # 2 shadow
    (28, 95, 20),    # 3 highlight
    (100, 65, 30),   # 4 trunk brown
    (75, 48, 20),    # 5 dark trunk
]

# Warm stone gray for paths
PATH_PAL = [
    (120, 115, 105), # 0 main stone gray
    (100, 95,  88),  # 1 dark mortar
    (140, 135, 125), # 2 lighter stone
    (80,  75,  68),  # 3 shadow
    (155, 150, 140), # 4 highlight
]

# Rich brown for dirt
DIRT_PAL = [
    (100, 65, 30),   # 0 main brown
    (80,  50, 20),   # 1 dark
    (120, 80, 40),   # 2 lighter
    (60,  38, 15),   # 3 shadow
    (140, 95, 50),   # 4 highlight
]

# Cave / rock
CAVE_PAL = [
    (60,  45, 35),   # 0 cave brown
    (45,  33, 25),   # 1 dark
    (75,  58, 44),   # 2 lighter
    (30,  22, 16),   # 3 shadow
    (90,  72, 55),   # 4 highlight
]

WATER_PAL = [
    (20, 50, 140),   # 0 deep blue
    (25, 60, 160),   # 1 lighter
    (15, 42, 120),   # 2 dark
    (35, 80, 180),   # 3 wave highlight
    (10, 30, 100),   # 4 shadow
]

WALL_PAL = [
    (70,  72, 82),   # 0 stone block
    (50,  52, 60),   # 1 background
    (35,  37, 45),   # 2 mortar shadow
    (90,  92, 105),  # 3 highlight
    (55,  57, 67),   # 4 mid
]

FLOOR_PAL = [
    (90,  70, 50),   # 0 wood base
    (75,  55, 35),   # 1 dark plank
    (105, 82, 60),   # 2 lighter plank
    (60,  44, 28),   # 3 grain shadow
    (120, 95, 68),   # 4 highlight
]

SAND_PAL = [
    (210, 190, 120), # 0 main sand
    (195, 172, 105), # 1 shadow
    (228, 210, 140), # 2 highlight
    (180, 158, 90),  # 3 dark
    (240, 225, 155), # 4 bright
]

ORE_PAL = [
    (55,  50, 62),   # 0 rock base
    (40,  38, 48),   # 1 dark
    (75,  72, 88),   # 2 lighter rock
    (200, 140, 40),  # 3 gold ore vein
    (220, 170, 60),  # 4 bright ore
    (30,  28, 36),   # 5 deep shadow
]

STUMP_PAL = [
    (90,  55, 20),   # 0 wood brown
    (70,  40, 12),   # 1 dark bark
    (110, 70, 30),   # 2 lighter
    (34,  95, 34),   # 3 grass surround
    (130, 85, 40),   # 4 heartwood
]

BUSH_PAL = [
    (25, 110, 25),   # 0 mid green
    (18,  85, 18),   # 1 shadow
    (35, 130, 30),   # 2 highlight
    (12,  62, 12),   # 3 deep shadow
    (45, 150, 35),   # 4 bright tip
]

DOOR_PAL = [
    (110, 75, 35),   # 0 frame wood
    (80,  50, 20),   # 1 dark door
    (60,  35, 10),   # 2 shadow
    (200, 170, 50),  # 3 handle gold
    (140, 95, 45),   # 4 lighter frame
]

# ── 8x8 Pixel art patterns (index into palette) ───────────────────────────────
# x = no draw (transparent / use previous layer), . = 0, numbers 0-9

GRASS_PATTERN = [
    [0, 0, 1, 0, 0, 2, 0, 0],
    [0, 2, 0, 0, 1, 0, 0, 3],
    [1, 0, 0, 3, 0, 0, 2, 0],
    [0, 0, 2, 0, 0, 1, 0, 0],
    [0, 3, 0, 0, 0, 0, 1, 0],
    [2, 0, 0, 1, 0, 3, 0, 0],
    [0, 0, 1, 0, 2, 0, 0, 2],
    [0, 1, 0, 0, 0, 0, 3, 0],
]

TREE_PATTERN = [
    [1, 2, 2, 3, 3, 2, 1, 1],
    [2, 3, 3, 3, 2, 3, 3, 1],
    [1, 3, 3, 2, 3, 3, 3, 2],
    [2, 2, 3, 3, 3, 2, 2, 1],
    [1, 3, 2, 3, 3, 3, 2, 2],
    [2, 2, 3, 3, 2, 3, 3, 1],
    [1, 4, 4, 5, 5, 4, 4, 1],  # trunk
    [1, 5, 4, 5, 4, 5, 4, 1],  # trunk base
]

PATH_PATTERN = [
    [1, 0, 0, 4, 0, 0, 1, 0],
    [0, 2, 0, 0, 2, 0, 0, 3],
    [1, 0, 3, 0, 0, 4, 0, 0],
    [0, 0, 0, 2, 0, 0, 3, 0],
    [0, 4, 0, 0, 0, 2, 0, 1],
    [1, 0, 2, 0, 3, 0, 0, 0],
    [0, 3, 0, 0, 0, 0, 2, 0],
    [0, 0, 1, 3, 0, 0, 0, 4],
]

DIRT_PATTERN = [
    [0, 1, 0, 2, 0, 1, 0, 0],
    [1, 0, 2, 0, 1, 0, 2, 0],
    [0, 2, 0, 0, 0, 2, 0, 1],
    [0, 0, 1, 2, 0, 0, 3, 0],
    [2, 0, 0, 0, 1, 0, 0, 2],
    [0, 1, 3, 0, 0, 2, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0],
    [0, 2, 0, 0, 2, 0, 0, 0],
]

WATER_PATTERN = [
    [0, 0, 3, 0, 0, 0, 3, 0],
    [0, 3, 0, 0, 3, 0, 0, 0],
    [1, 0, 0, 1, 0, 1, 0, 2],
    [0, 0, 3, 0, 0, 0, 0, 3],
    [0, 1, 0, 0, 3, 0, 1, 0],
    [3, 0, 0, 1, 0, 3, 0, 0],
    [0, 0, 1, 0, 0, 0, 3, 1],
    [0, 3, 0, 0, 1, 0, 0, 0],
]

WALL_PATTERN = [
    [1, 0, 0, 0, 1, 0, 0, 0],  # horizontal mortar top
    [0, 3, 0, 3, 0, 3, 0, 3],  # block face
    [0, 0, 3, 0, 0, 0, 3, 0],
    [2, 2, 2, 2, 2, 2, 2, 2],  # horizontal mortar
    [0, 0, 1, 0, 0, 0, 1, 0],  # block offset
    [3, 0, 0, 3, 0, 3, 0, 0],
    [0, 3, 0, 0, 3, 0, 0, 3],
    [2, 2, 2, 2, 2, 2, 2, 2],  # bottom mortar
]

FLOOR_PATTERN = [
    [0, 3, 0, 0, 1, 3, 0, 0],
    [3, 2, 0, 3, 0, 0, 3, 1],  # plank lines
    [0, 0, 1, 0, 0, 1, 0, 0],
    [1, 3, 0, 2, 3, 0, 2, 0],
    [0, 0, 3, 0, 0, 3, 0, 3],
    [3, 1, 0, 0, 1, 0, 1, 0],
    [0, 0, 2, 3, 0, 0, 0, 2],
    [0, 3, 0, 0, 3, 1, 0, 0],
]

DOOR_PATTERN = [
    [0, 0, 2, 2, 2, 2, 0, 0],
    [0, 2, 1, 1, 1, 1, 2, 0],
    [0, 2, 1, 3, 3, 1, 2, 0],
    [0, 2, 1, 3, 3, 1, 2, 0],
    [0, 2, 1, 1, 1, 1, 2, 0],
    [0, 2, 1, 1, 3, 1, 2, 0],  # handle
    [0, 2, 1, 1, 1, 1, 2, 0],
    [0, 4, 4, 4, 4, 4, 4, 0],  # frame
]

STUMP_PATTERN = [
    [3, 3, 3, 3, 3, 3, 3, 3],
    [3, 1, 0, 0, 0, 1, 3, 3],
    [3, 0, 4, 2, 4, 0, 3, 3],
    [3, 0, 2, 0, 2, 0, 3, 3],
    [3, 1, 0, 2, 0, 1, 3, 3],
    [3, 1, 1, 1, 1, 1, 3, 3],
    [3, 3, 3, 3, 3, 3, 3, 3],
    [3, 3, 3, 3, 3, 3, 3, 3],
]

ORE_PATTERN = [
    [1, 0, 2, 0, 0, 2, 0, 1],
    [0, 2, 0, 1, 2, 0, 2, 0],
    [2, 0, 3, 3, 0, 3, 0, 2],
    [0, 1, 3, 4, 3, 3, 1, 0],
    [2, 0, 3, 3, 4, 3, 0, 2],
    [0, 2, 0, 3, 3, 0, 2, 0],
    [1, 0, 2, 0, 0, 2, 0, 1],
    [0, 5, 0, 1, 0, 0, 5, 0],
]

BUSH_PATTERN = [
    [3, 3, 1, 1, 1, 3, 3, 3],
    [3, 1, 2, 2, 1, 1, 3, 3],
    [3, 2, 2, 4, 2, 2, 1, 3],
    [1, 2, 4, 2, 4, 2, 2, 3],
    [1, 2, 2, 4, 2, 2, 2, 1],
    [3, 1, 2, 2, 2, 1, 1, 3],
    [3, 3, 1, 1, 1, 3, 3, 3],
    [3, 3, 3, 3, 3, 3, 3, 3],
]

SAND_PATTERN = [
    [0, 2, 0, 0, 4, 0, 0, 2],
    [2, 0, 0, 4, 0, 0, 2, 0],
    [0, 0, 2, 0, 0, 1, 0, 0],
    [0, 4, 0, 0, 2, 0, 0, 1],
    [2, 0, 0, 1, 0, 0, 4, 0],
    [0, 0, 4, 0, 0, 2, 0, 0],
    [0, 1, 0, 2, 0, 0, 0, 2],
    [2, 0, 0, 0, 1, 0, 2, 0],
]

CAVE_PATTERN = [
    [0, 1, 0, 2, 0, 1, 0, 0],
    [1, 0, 2, 0, 1, 0, 2, 0],
    [0, 2, 0, 0, 2, 0, 0, 1],
    [0, 0, 1, 2, 0, 0, 3, 0],
    [2, 0, 0, 0, 1, 0, 0, 2],
    [0, 1, 3, 0, 0, 2, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0],
    [0, 2, 0, 0, 2, 0, 0, 0],
]

# Map tile ID to (pattern, palette)
TILE_DATA = {
    TILE_GRASS:  (GRASS_PATTERN,  GRASS_PAL),
    TILE_WATER:  (WATER_PATTERN,  WATER_PAL),
    TILE_TREE:   (TREE_PATTERN,   TREE_PAL),
    TILE_ROCK:   (CAVE_PATTERN,   CAVE_PAL),
    TILE_PATH:   (PATH_PATTERN,   PATH_PAL),
    TILE_WALL:   (WALL_PATTERN,   WALL_PAL),
    TILE_FLOOR:  (FLOOR_PATTERN,  FLOOR_PAL),
    TILE_DOOR:   (DOOR_PATTERN,   DOOR_PAL),
    TILE_BUSH:   (BUSH_PATTERN,   BUSH_PAL),
    TILE_STUMP:  (STUMP_PATTERN,  STUMP_PAL),
    TILE_ORE:    (ORE_PATTERN,    ORE_PAL),
    TILE_SAND:   (SAND_PATTERN,   SAND_PAL),
}

# Water animation frames — shift wave highlights each frame
_WATER_WAVE_OFFSETS = [0, 1, 2, 1]  # 4-phase cycle

# ── Surface cache ─────────────────────────────────────────────────────────────
_surf_cache: dict = {}


def _render_8x8(pattern, palette, variation_seed=0) -> pygame.Surface:
    """Render an 8x8 pattern to a pygame.Surface at 1px per pixel."""
    tiny = pygame.Surface((8, 8))
    base_col = palette[0]
    tiny.fill(base_col)
    rng = random.Random(variation_seed)
    for row in range(8):
        for col in range(8):
            idx = pattern[row][col]
            if idx < len(palette):
                # Tiny random variation (+/- 8) per pixel for organic look
                r, g, b = palette[idx]
                jitter = rng.randint(-6, 6)
                col_px = (
                    max(0, min(255, r + jitter)),
                    max(0, min(255, g + jitter)),
                    max(0, min(255, b + jitter)),
                )
                tiny.set_at((col, row), col_px)
    return tiny


def _scale_to_tile(small: pygame.Surface) -> pygame.Surface:
    """Scale an 8x8 surface up to TILE_SIZE x TILE_SIZE (32x32) using nearest-neighbor."""
    return pygame.transform.scale(small, (TILE_SIZE, TILE_SIZE))


def get_tile_surf(tid: int, tick: int = 0) -> pygame.Surface:
    """Return a cached TILE_SIZE x TILE_SIZE surface for the given tile ID."""
    # Water animates in 4-frame cycles
    anim_frame = (tick // 15) % 4 if tid == TILE_WATER else 0
    cache_key = (tid, anim_frame)

    if cache_key in _surf_cache:
        return _surf_cache[cache_key]

    if tid in TILE_DATA:
        pattern, palette = TILE_DATA[tid]

        if tid == TILE_WATER:
            # Shift the wave highlight rows for animation
            shifted = [row[:] for row in pattern]
            wave_shift = anim_frame
            # Row 2 and 5 are the wave lines; shift their highlight pixel
            for wave_row in (2, 5):
                orig_row = pattern[wave_row]
                shifted[wave_row] = orig_row[wave_shift:] + orig_row[:wave_shift]
            pattern_to_use = shifted
        else:
            pattern_to_use = pattern

        tiny = _render_8x8(pattern_to_use, palette, variation_seed=tid * 31 + anim_frame)
        surf = _scale_to_tile(tiny)
    else:
        # Fallback: solid dark color
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill((10, 12, 30))

    _surf_cache[cache_key] = surf
    return surf


def clear_cache():
    """Clear the tile surface cache (call when reinitializing display mode)."""
    _surf_cache.clear()
