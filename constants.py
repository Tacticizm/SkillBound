# Screen
SCREEN_W, SCREEN_H = 960, 640
TILE_SIZE = 32
FPS = 60

# Colors
BLACK   = (0, 0, 0)
WHITE   = (255, 255, 255)
GRAY    = (120, 120, 120)
DGRAY   = (60, 60, 60)
RED     = (200, 40, 40)
GREEN   = (40, 180, 40)
DGREEN  = (20, 120, 20)
BLUE    = (40, 100, 200)
YELLOW  = (220, 200, 40)
ORANGE  = (220, 130, 40)
BROWN   = (130, 80, 40)
DBROWN  = (90, 50, 20)
LBROWN  = (180, 130, 80)
CYAN    = (40, 200, 200)
PURPLE  = (140, 40, 200)
TAN     = (210, 180, 140)

# Tile IDs
TILE_GRASS  = 0
TILE_WATER  = 1
TILE_TREE   = 2
TILE_ROCK   = 3
TILE_PATH   = 4
TILE_WALL   = 5
TILE_FLOOR  = 6
TILE_DOOR   = 7
TILE_BUSH   = 8
TILE_STUMP  = 9
TILE_ORE    = 10
TILE_SAND   = 11

SOLID_TILES = {TILE_WATER, TILE_TREE, TILE_ROCK, TILE_WALL, TILE_BUSH}

# Skill IDs
SK_ATK  = "Attack"
SK_DEF  = "Defence"
SK_HP   = "Hitpoints"
SK_WC   = "Woodcutting"
SK_MIN  = "Mining"
SK_FISH = "Fishing"
SK_COOK = "Cooking"
SK_RANGE= "Ranged"
SKILLS  = [SK_ATK, SK_DEF, SK_HP, SK_WC, SK_MIN, SK_FISH, SK_COOK, SK_RANGE]

# Game states
STATE_WORLD  = "world"
STATE_COMBAT = "combat"
STATE_DIALOG = "dialog"
STATE_MENU   = "menu"
STATE_SHOP   = "shop"
STATE_SKILL  = "skill"

# XP table (level -> xp required total)
def xp_for_level(lvl):
    total = 0
    for i in range(1, lvl):
        total += int(i + 300 * (2 ** (i / 7)))
    return total // 4

XP_TABLE = [0] + [xp_for_level(i) for i in range(2, 100)]

def level_from_xp(xp):
    for lvl in range(98, 0, -1):
        if xp >= XP_TABLE[lvl]:
            return lvl + 1
    return 1
