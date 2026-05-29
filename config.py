import random
from pathlib import Path

import pygame

import all_objs
import tool  # 載入你的工具包

BASE_DIR = Path(__file__).parent

SAVE_PATH = BASE_DIR / "save_game.json"
current_active_path = SAVE_PATH
LEVELS_PATH = BASE_DIR / "levels"
SOUND_PATH = BASE_DIR / "sounds"
BGM_PATH = BASE_DIR / "BGM"


def get_current_world_path(select_world):
    """根據當前選擇的世界，返回對應的資料夾路徑"""
    # select_world 可能是 1 或 2
    world_folder = f"world_{select_world}"
    return LEVELS_PATH / world_folder


WIDTH, HEIGHT = 700, 600
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
tool.set_screen(screen)
screen_rect = screen.get_rect()
screen_text = "Escape Them!"
pygame.display.set_caption(screen_text)
clock = pygame.time.Clock()

now_treasure = {}
shop_page = "survival"

trigger_damage = False


# 定義所有升級的詳細數據 (包含價格、技能數值、標題、說明)
# SURVIVAL [20, 29, 27, 12, 15, 36, 10, 15, 9, 10, 14, 13, 9, 16]
# SURVIVAL [20, 29, 27, 13, 15, 58, 12, 15, 9, 10, 14, 17, 9, 16]
# COMBAT [1, 7, 8, 7, 9, 1]
# COMBAT [1, 7, 8, 7, 9, 1]

UPGRADE_SURVIVAL = {
    "upgrade_p1": {
        "title": "Player Speed",
        "costs": [
            150,
            450,
            820,
            1050,
            1840,
            2510,
            4560,
            7000,
            9680,
            12570,
            15000,
            18000,
            20540,
            27000,
            29400,
            31200,
            38700,
            43500,
            48800,
            56000,
        ],  # costs 長度為 20 元素
        "skills": [0, 1.5, 3, 4.5, 6, 7.5, 9, 10.5, 12, 13.5, 15, 16.5, 18, 19.5, 21, 22.5, 24, 25.5, 27, 28.5, 30],
        "skill_desc": "Speed +{}",
        "limits": {
            1: 12,
            2: 20,  # 🌟 絕對滿等為 20，世界 2 的上限自動安全緊縮至 20
        },
    },
    "upgrade_p2": {
        "title": "Coin Spawn Speed",
        "costs": [
            300,
            600,
            1000,
            1800,
            2350,
            3500,
            5000,
            7500,
            9000,
            13400,
            16700,
            20000,
            24800,
            29800,
            37500,
            45000,
            56200,
            68400,
            80000,
            10200,
            12400,
            15600,
            18000,
            21300,
            25400,
            29450,
            34580,
            40100,
            46700,
        ],  # costs 長度為 29 元素
        "skills": [
            0.6,
            1.2,
            1.8,
            2.4,
            3.0,
            3.6,
            4.2,
            4.8,
            5.4,
            6.0,
            6.6,
            7.2,
            7.8,
            8.4,
            9.0,
            9.6,
            10.2,
            10.8,
            11.4,
            12.0,
            12.6,
            13.2,
            13.8,
            14.4,
            15.0,
            15.6,
            16.2,
            16.8,
            17.4,
            18.0,
        ],
        "skill_desc": "Coin spawn time -{} sec",
        "limits": {
            1: 17,
            2: 29,
        },
    },
    "upgrade_p3": {
        "title": "Points Multiplier",
        "costs": [
            380,
            570,
            850,
            1350,
            2480,
            3900,
            5670,
            8970,
            11200,
            17000,
            25400,
            35000,
            45000,
            55000,
            63500,
            69000,
            74200,
            79600,
            84500,
            90000,
            96000,
            102000,
            107000,
            120000,
            135000,
            152400,
            187000,
        ],
        "skills": [
            1,
            1.09,
            1.19,
            1.3,
            1.42,
            1.55,
            1.69,
            1.84,
            2.01,
            2.19,
            2.39,
            2.61,
            2.84,
            3.1,
            3.38,
            3.68,
            4.01,
            4.37,
            4.76,
            5.19,
            5.66,
            6.17,
            6.73,
            7.34,
            8.01,
            8.73,
            9.51,
            10.36,
        ],
        "skill_desc": "Point x{}",
        "limits": {
            1: 12,
            2: 23,
        },
    },
    "upgrade_p4": {
        "title": "Size",
        "costs": [200, 400, 700, 1200, 1800, 2400, 3700, 4500, 6000, 8050, 10500, 12500],  # costs 長度為 12 元素
        "skills": [35, 33, 31, 29, 27, 25, 23, 21, 19, 17, 15, 13, 11, 8],
        "skill_desc": "Size: {}px",
        "limits": {
            1: 8,
            2: 12,
        },
    },
    "upgrade_p5": {
        "title": "Enemy Spawn",
        "costs": [150, 380, 800, 1300, 2400, 3800, 5700, 7000, 10500, 12400, 13800, 15000, 18000, 23100, 30000],
        "skills": [0.1, 0.3, 0.5, 0.8, 1.0, 1.3, 1.6, 2.0, 2.3, 2.5, 2.8, 3.0, 3.2, 3.5, 3.7, 4.0],
        "skill_desc": "Spawn {}s",
        "limits": {
            1: 9,  # 🌟 這個技能天花板只有 9 等，世界 1 就可以直接點滿它
            2: 15,
        },
    },
    "upgrade_p6": {
        "title": "Max HP",
        "costs": [
            50,
            300,
            500,
            780,
            1500,
            2300,
            4200,
            7300,
            9500,
            10100,
            11800,
            12500,
            15700,
            18700,
            20000,
            23400,
            25100,
            30000,
            37500,
            45100,
            57800,
            67800,
            78900,
            89000,
            100500,
            110200,
            125000,
            137800,
            157890,
            168000,
            189000,
            204500,
            234500,
            278400,
            310000,
            345700,
        ],  # costs 長度為 36 元素
        "skills": [
            10,
            12,
            14,
            16,
            18,
            20,
            22,
            24,
            26,
            28,
            30,
            32,
            34,
            36,
            38,
            40,
            41,
            43,
            44,
            45,
            47,
            49,
            50,
            51,
            53,
            54,
            56,
            57,
            59,
            60,
            61,
            63,
            64,
            66,
            67,
            69,
            70,
            71,
            73,
            74,
            76,
            77,
            79,
            80,
            80,
            81,
            83,
            84,
            86,
            87,
            89,
            90,
            91,
            93,
            94,
            96,
            97,
            99,
            100,
        ],
        "skill_desc": "HP: {}",
        "limits": {
            1: 16,
            2: 30,  # 🌟 血量上限很高，完美契合你的 1 世界 12 等、2 世界 21 等規範！
        },
    },
    "upgrade_p7": {
        "title": "Regen",
        "costs": [500, 800, 1200, 2000, 3500, 4700, 6500, 8300, 10500, 12000],
        "skills": [
            {"time": 10, "hp": 0},
            {"time": 10, "hp": 1},
            {"time": 8, "hp": 1},
            {"time": 8, "hp": 2},
            {"time": 7, "hp": 2},
            {"time": 7, "hp": 3},
            {"time": 6, "hp": 3},
            {"time": 5, "hp": 3},
            {"time": 5, "hp": 4},
            {"time": 4, "hp": 4},
            {"time": 3, "hp": 4},
            {"time": 3, "hp": 5},
            {"time": 2, "hp": 5},
        ],
        "skill_desc": "{}",
        "limits": {
            1: 7,  # 🌟 總共只有 9 級，直接安全拉滿
            2: 10,
        },
    },
    "upgrade_p8": {
        "title": "Invincible",
        "costs": [250, 700, 1000, 1200, 1400, 1700, 2300, 3700, 4500, 5700, 7600, 9800, 12000, 15800, 21400],  # costs 長度為 15 元素
        "skills": [1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000],
        "skill_desc": "Time: {}ms",
        "limits": {
            1: 10,
            2: 15,  # 🌟 總共 15 級，世界 2 自動防禦封頂在 15 等
        },
    },
    "upgrade_p9": {
        "title": "Magnet",
        "costs": [800, 1500, 2400, 4500, 6800, 8600, 11000, 17000, 23500],  # costs 長度為 9 元素
        "skills": [0, 30, 52, 74, 96, 118, 140, 162, 184, 200],
        "skill_desc": "Range: {}px",
        "limits": {
            1: 9,
            2: 9,
        },
    },
    "upgrade_p10": {
        "title": "Magnet Strength",
        "costs": [700, 1500, 2400, 4700, 7000, 8800, 11500, 17800, 24000, 38700],  # costs 長度為 10 元素
        "skills": [1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0],
        "skill_desc": "Magnet Strength x{}",
        "limits": {
            1: 10,  # 🌟 總共 10 級，小於 12，因此兩世界皆定為 10
            2: 10,
        },
    },
    "upgrade_p11": {
        "title": "Luck",
        "costs": [500, 1000, 1600, 2300, 3100, 4000, 5000, 6200, 7500, 9000, 11400, 12500, 13600, 14800],  # costs 長度為 14 元素
        "skills": [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 3.0, 3.2, 3.4, 3.6, 3.8, 4.0],
        "skill_desc": "Luck x{}",
        "limits": {
            1: 12,
            2: 14,  # 🌟 絕對上限 14 級
        },
    },
    "upgrade_p12": {
        "title": "Coin Multiplier",
        "costs": [500, 1240, 3870, 6800, 12450, 17500, 31200, 47800, 68000, 87000, 120300, 135100, 178000],  # costs 長度為 13 元素
        "skills": [1.0, 1.2, 1.5, 1.7, 1.9, 2.1, 2.3, 2.6, 2.8, 3.0, 3.3, 3.5, 3.7, 4.0, 4.3, 4.5, 4.7, 5.0],
        "skill_desc": "Coins x{}",
        "limits": {
            1: 10,
            2: 13,  # 🌟 絕對上限 13 級
        },
    },
    "upgrade_p13": {
        "title": "Dodge Chance",
        "costs": [200, 600, 1200, 1900, 2500, 3800, 4500, 6400, 8700],  # costs 長度為 9 元素
        "skills": [0, 5, 10, 14, 18, 23, 26, 28, 30, 33],
        "skill_desc": "Chance: {}%",
        "limits": {
            1: 9,
            2: 9,
        },
    },
    "upgrade_p14": {
        "title": "Dodge Percent",
        "costs": [150, 340, 570, 800, 1200, 1800, 2400, 3700, 4800, 6000, 8000, 12000, 15450, 20000, 27800, 31000],  # costs 長度為 16 元素
        "skills": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80],
        "skill_desc": "Damage - {}%",
        "limits": {
            1: 12,
            2: 16,  # 🌟 絕對上限 16 級
        },
    },
}

UPGRADE_COMBAT = {
    "upgrade_p15": {
        "title": "Can Shoot",
        "costs": [5000],  # costs 長度為 1 元素
        "skills": [0, 1],
        "skill_desc": "Can Shoot {}",
        "limits": {
            1: 1,  # 🌟 核心開關一級解鎖完畢
            2: 1,
        },
    },
    "upgrade_p16": {
        "title": "Shoot CD",
        "costs": [800, 2300, 4500, 5100, 7500, 12000, 15000],  # costs 長度為 7 元素
        "skills": [500, 450, 400, 350, 300, 250, 200, 150],
        "skill_desc": "CD: {}s",
        "limits": {
            1: 7,  # 🌟 絕對上限 7 級
            2: 7,
        },
    },
    "upgrade_p17": {
        "title": "Bullet Speed",
        "costs": [900, 1400, 2000, 3100, 4500, 5700, 7000, 9500],  # costs 長度為 8 元素
        "skills": [3, 5, 7, 9, 11, 13, 15, 17, 19],
        "skill_desc": "Speed: {}",
        "limits": {
            1: 8,  # 🌟 絕對上限 8 級
            2: 8,
        },
    },
    "upgrade_p18": {
        "title": "Bullet Size",
        "costs": [500, 700, 1000, 1500, 2000, 3100, 5000],  # costs 長度為 7 元素
        "skills": [5, 6, 7, 8, 9, 10, 11, 12],
        "skill_desc": "Size: {}",
        "limits": {
            1: 7,  # 🌟 絕對上限 7 級
            2: 7,
        },
    },
    "upgrade_p19": {
        "title": "Shoot Get Points",
        "costs": [1000, 2000, 3000, 5000, 7000, 10200, 15000, 18500, 24000],  # costs 長度為 9 元素
        "skills": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "skill_desc": "Points: {}",
        "limits": {
            1: 9,  # 🌟 絕對上限 9 級
            2: 9,
        },
    },
    "upgrade_p20": {
        "title": "Alto Shoot",
        "costs": [10000],  # costs 長度為 1 元素
        "skills": [0, 1],
        "skill_desc": "Range: {}",
        "limits": {
            1: 1,  # 🌟 自動射擊一級即滿等
            2: 1,
        },
    },
}


# a = UPGRADE_COMBAT["upgrade_p20"]["costs"]
# b = UPGRADE_COMBAT["upgrade_p20"]["skills"]

# print(len(a) + 1)  # 測試用，懶著計算
# print(len(b))
# print(len(a) + 1 <= len(b))

print("SURVIVAL", [len(v["costs"]) for _, v in UPGRADE_SURVIVAL.items()])
print("SURVIVAL", [len(v["skills"]) - 1 for _, v in UPGRADE_SURVIVAL.items()])
print("COMBAT", [len(v["costs"]) for _, v in UPGRADE_COMBAT.items()])
print("COMBAT", [len(v["skills"]) - 1 for _, v in UPGRADE_COMBAT.items()])

player_skins = {
    # --- Common (一般) ---
    "red": {
        "rarity": "Common",
        "level": 1,
        "exp": 0,
        "has_owned": True,
        "color": tool.Colors.RED,
        "effect": "none",
        "base_power": 1,
        "growth": 0,
        "draw_weight": 70,
        "can_get_world": 1,
    },
    "white": {
        "rarity": "Common",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.WHITE,
        "effect": ["speed", "points_multiplier"],
        "base_power": [1.3, 1.2],
        "growth": [0.05, 0.05],
        "draw_weight": 70,
        "can_get_world": 1,
    },
    "black": {
        "rarity": "Common",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.BLACK,
        "effect": ["points_coin_multiplier", "max_hp"],
        "base_power": [1.2, 1.1],
        "growth": [0.05, 0.1],
        "draw_weight": 70,
        "can_get_world": 1,
    },
    "gray": {
        "rarity": "Common",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.GRAY,
        "effect": ["invincible_time", "speed"],
        "base_power": [1.5, 1.1],
        "growth": [0.1, 0.05],
        "draw_weight": 70,
        "can_get_world": 1,
    },
    "olive": {
        "rarity": "Common",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.OLIVE,
        "effect": ["max_hp", "coin_multiplier"],
        "base_power": [1.3, 2.0],
        "growth": [0.08, 0.05],
        "draw_weight": 60,
        "can_get_world": 2,
    },
    # --- Rare (稀有) ---
    "green": {
        "rarity": "Rare",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.GREEN,
        "effect": ["max_hp", "speed"],
        "base_power": [1.2, 0.7],
        "growth": [0.05, 0.08],
        "draw_weight": 20,
        "can_get_world": 1,
    },
    "yellow": {
        "rarity": "Rare",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.YELLOW,
        "effect": ["points_multiplier", "speed"],
        "base_power": [1.7, 0.8],
        "growth": [0.1, 0.08],
        "draw_weight": 20,
        "can_get_world": 1,
    },
    "blue": {
        "rarity": "Rare",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.BLUE,
        "effect": "enemy_damage",
        "base_power": 0.7,
        "growth": -0.04,  # 傷害倍率越低越強
        "draw_weight": 20,
        "can_get_world": 1,
    },
    "purple": {
        "rarity": "Rare",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.PURPLE,
        "effect": "speed",
        "base_power": 1.2,
        "growth": 0.1,
        "draw_weight": 20,
        "can_get_world": 1,
    },
    "violet": {
        "rarity": "Rare",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.VIOLET,
        "effect": ["points_multiplier", "coin_multiplier"],
        "base_power": [3.0, 2.3],
        "growth": [0.1, 0.2],
        "draw_weight": 15,
        "can_get_world": 2,
    },
    # --- Epic (史詩) ---
    "orange": {
        "rarity": "Epic",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.ORANGE,
        "effect": "player_size",
        "base_power": 0.9,
        "growth": -0.01,  # 體型越小越強
        "draw_weight": 8,
        "can_get_world": 1,
    },
    "light blue": {
        "rarity": "Epic",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.CYAN,
        "effect": ["coin_multiplier", "player_size"],
        "base_power": [1.9, 0.8],
        "growth": [0.15, -0.02],
        "draw_weight": 8,
        "can_get_world": 1,
    },
    "pink": {
        "rarity": "Epic",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.PINK,
        "effect": ["speed", "points_coin_multiplier"],
        "base_power": [1.8, 0.9],
        "growth": [0.12, 0.1],
        "draw_weight": 8,
        "can_get_world": 1,
    },
    "dark orange": {
        "rarity": "Epic",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.ORANGE2,
        "effect": ["points_multiplier", "max_hp", "speed"],
        "base_power": [2.3, 0.7, 0.6],
        "growth": [0.2, 0, 0],
        "draw_weight": 4,
        "can_get_world": 1,
    },
    "chartreuse": {
        "rarity": "Epic",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.CHARTREUSE,
        "effect": ["max_hp", "coin_multiplier", "speed"],
        "base_power": [0.8, 5.0, 1.3],
        "growth": [0, 0.12, 0.1],
        "draw_weight": 4,
        "can_get_world": 2,
    },
    # --- Legendary (傳說) ---
    "gold": {
        "rarity": "Legendary",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.GOLD,
        "effect": ["coin_multiplier", "points_multiplier"],
        "base_power": [4, 1.5],
        "growth": [0.4, 0.2],
        "draw_weight": 2,
        "can_get_world": 1,
    },
    "brown": {
        "rarity": "Legendary",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.BROWN,
        "effect": ["enemy_spawn_speed", "max_hp"],
        "base_power": [2, 1.2],
        "growth": [0.1, 0.25],
        "draw_weight": 2,
        "can_get_world": 1,
    },
    "dark green": {
        "rarity": "Legendary",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.DARK_GREEN,
        "effect": ["max_hp", "speed"],
        "base_power": [2.0, 1.2],
        "growth": [0.5, 0.15],
        "draw_weight": 2,
        "can_get_world": 1,
    },
    "claret": {
        "rarity": "Legendary",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.CLARET,
        "effect": ["max_hp", "points_coin_multiplier"],
        "base_power": [2.0, 3.0],
        "growth": [0.7, 0.2],
        "draw_weight": 1,
        "can_get_world": 2,
    },
}


skin_text_color = {
    "red": tool.Colors.WHITE,
    "orange": tool.Colors.BLACK,
    "dark orange": tool.Colors.WHITE,
    "yellow": tool.Colors.BLACK,
    "chartreuse": tool.Colors.BLACK,
    "green": tool.Colors.BLACK,
    "olive": tool.Colors.WHITE,
    "light blue": tool.Colors.BLACK,
    "blue": tool.Colors.WHITE,
    "purple": tool.Colors.WHITE,
    "violet": tool.Colors.WHITE,
    "pink": tool.Colors.WHITE,
    "white": tool.Colors.BLACK,
    "gray": tool.Colors.BLACK,
    "black": tool.Colors.WHITE,
    # VIP皮膚區
    "gold": tool.Colors.BLACK,
    "brown": tool.Colors.WHITE,
    "dark green": tool.Colors.WHITE,
    "claret": tool.Colors.WHITE,
}


current_levels = {f"upgrade_p{i}": 0 for i in range(1, len(UPGRADE_SURVIVAL) + len(UPGRADE_COMBAT) + 1)}

now_player_skin = tool.Colors.RED
current_player_color_name = "red"


# 顯示專區
next_spawn_range = random.randint(14, 20)

# 遊戲模式
g_m = ["easy", "normal", "hard", "super_hard", "crazy"]
gm_i = 1
game_mode = g_m[gm_i]

# 解鎖關卡的價格，第一個是卡位用，第一關是０元
level_costs = {
    "world1": [0, 0, 500, 1000, 5000, 15000, 35000, 50000, 75000, 100000, 130000],
    "world2": [0, 0, 250000, 340000],  # , 400000, 500000, 650000, 700000, 840000, 950000, 1000000
}  # 目前還沒有關卡

# 下個關卡需要秒數，第一個卡位用
level_need_record = {
    "world1": [0, 0, 50, 60, 60, 70, 80, 90, 90, 100, 100],
    "world2": [0, 0, 110, 120],
}

MAX_WORLD = 2

# 說明：第二關需要第一關(普通模式)有超過八十秒的生存時間，以此類推


def update_current_world_data(select_world):
    global all_levels, current_world_costs, current_world_need_record, lv_i, current_level, levels_unlocked
    world_key = f"world{select_world}"
    all_levels = ["level" + str(i + 1) for i in range(len(level_costs[world_key]) - 1)]
    current_world_costs = level_costs[world_key]  # 確保第一個卡位是0元
    current_world_need_record = level_need_record[world_key]  # 確保第一個卡位是0秒
    levels_unlocked = all_worlds_unlocked.get(world_key, 1)  # 預設至少解鎖第一關
    lv_i = 0
    if all_levels:
        current_level = all_levels[lv_i]


levels_unlocked = 1  # 這是給遊戲邏輯用的數字
all_worlds_unlocked = {"world1": 1, "world2": 1}  # 這是給存檔紀錄用的字典


def update_world_data(select_world):
    global current_world_costs, current_world_need_record
    world_key = f"world{select_world}"
    level_costs[world_key] = current_world_costs  # 確保第一個卡位是0元
    level_need_record[world_key] = current_world_need_record  # 確保第一個卡位是0秒
    all_worlds_unlocked[world_key] = levels_unlocked


current_world_key = "world1"
select_world = 1
worlds_unlocked = 1
update_current_world_data(select_world)
lv_i = 0
current_level = all_levels[lv_i]
world_cost = {
    "world1": 0,
    "world2": 200000,
    # "world3": 500000
}
world_bgc = {
    "world1": [tool.Colors.BLACK2, tool.Colors.BLACK_3],
    "world2": [tool.Colors.VIOLET, tool.Colors.PURPLE],
    # "world3": [tool.Colors.DARK_GREEN, tool.Colors.PARIS_GREEN],
}


def get_skill_val(p_key):
    # 先從生存字典找，找不到再去戰鬥字典找
    cfg = UPGRADE_SURVIVAL.get(p_key) or UPGRADE_COMBAT.get(p_key)

    if not cfg:
        print(f"Error: {p_key} 不存在於任何設定檔中")
        return 0

    lvl = current_levels.get(p_key, 0)

    # 🌟 核心防禦：從 limits 字典裡，安全抓出玩家「當前正在遊玩的世界」的等級天花板
    # 提示：config.select_world 代表目前選單選中的世界（或者是你遊戲關卡內用的 current_playing_world）
    limits_dict = cfg.get("limits", {})
    world_max = limits_dict.get(select_world, len(cfg["costs"]))

    # 🌟 一擊必殺的 Level Sync：取兩者之間較小的那一個！
    # 如果買到 21 等，但世界 1 上限是 12 等 -> min(21, 12) 就會強制壓回 12！
    effective_level = min(lvl, world_max)

    # 🌟 最後，用這個被安全修正後的「有效等級」去查數值表！
    return cfg["skills"][effective_level]


def update_skill():
    global now_skills, can_shoot
    now_skills = {f"p{i}": get_skill_val(f"upgrade_p{i}") for i in range(1, len(UPGRADE_SURVIVAL) + len(UPGRADE_COMBAT) + 1)}
    can_shoot = now_skills["p15"]  # 這裡是為了方便後續判斷玩家是否有射擊能力


update_skill()


def apply_skin_effects():
    global player_speed_buff, points_multiplier, coin_multiplier, player_max_hp_buff, skin_enemy_damage_buff, buffer_duration_buff, invincible_time_buff, player_size_buff

    # 先重置為基礎數值 (避免效果無限疊加)
    player_speed_buff = 1.0
    points_multiplier = 1.0
    coin_multiplier = 1.0
    player_max_hp_buff = 1.0
    skin_enemy_damage_buff = 1.0
    buffer_duration_buff = 1.0
    invincible_time_buff = 1.0
    player_size_buff = 1.0

    # 取得當前皮膚資訊
    skin_info = player_skins.get(current_player_color_name, {})
    if not skin_info:
        return

    # 1. 取得原始資料 (可能是單個值，也可能是列表，或者 None)
    raw_effects = skin_info.get("effect", "none")
    raw_powers = skin_info.get("base_power", 1)
    raw_growths = skin_info.get("growth", 0)
    level = skin_info.get("level", 1)

    # 2. 統一轉成列表 (List) 以便迴圈處理
    # 如果原本就是 list (多重效果)，就保持原樣
    # 如果是單個字串/數字，就把它包進 list 變成 [值]
    if isinstance(raw_effects, list):
        effects = raw_effects
        powers = raw_powers
        growths = raw_growths
    else:
        effects = [raw_effects]
        powers = [raw_powers]
        growths = [raw_growths]

    for effect, base_p, grow in zip(effects, powers, growths, strict=False):
        final_power = base_p + (level - 1) * grow
        if effect == "speed":
            player_speed_buff *= final_power
        elif effect == "points_multiplier":
            points_multiplier *= final_power
        elif effect == "coin_multiplier":
            coin_multiplier *= final_power
        elif effect == "points_coin_multiplier":
            points_multiplier *= final_power
            coin_multiplier *= final_power
        elif effect == "max_hp":
            player_max_hp_buff *= final_power
        elif effect == "enemy_damage":
            skin_enemy_damage_buff *= final_power
            skin_enemy_damage_buff = tool.num_range(0.1, 1.0, skin_enemy_damage_buff)
        elif effect == "enemy_spawn_speed":
            buffer_duration_buff *= final_power
        elif effect == "invincible_time":
            invincible_time_buff *= final_power
        elif effect == "player_size":
            player_size_buff *= final_power
            player_size_buff = tool.num_range(0.5, 5, player_size_buff)
        # 格式
        # elif effect == "":
        #     pass


apply_skin_effects()

buffer_duration = now_skills["p5"] * buffer_duration_buff

offset_x, offset_y = 0, 0
target_y = 0


bullet_list = []  # 全局子彈列表，當砲台開火時會往裡面添加子彈
now_bom_range = 1


player_bullets = []
last_shot_time = 0  # 用來控制射速 (Cooldown)

God = False
Invincible = False
FPS_Speed = 1
Timer_Speed = 1


class AFKError(Exception):
    def __init__(self):
        super().__init__("Error code: 1011451 - Process terminated due to severe idling.")


# 按下偵測專區
is_pressing = []
for _ in range(20):
    is_pressing.append(False)


def reset_pressing():
    is_pressing[:] = [False] * len(is_pressing)


alphas = []
for _ in range(20):
    alphas.append(255)

scroll_ys = []
for _ in range(20):
    scroll_ys.append(0)


def reset_scroll_ys():
    scroll_ys[:] = [0] * len(scroll_ys)


points = 0
total_points = 0
shoot_points = 0


update_skill()
can_shoot = bool(now_skills["p15"])

trying_to_touch_player = False
player_max_hp = 10
player_hp = player_max_hp
last_hit_time = -10  # 上次受傷時間，預設負值確保開局能受傷
invincible_duration = now_skills["p8"] / 1000  # 無敵時間 1秒，可升級
has_save_survived_time = False
draw_this_lock = False
level_button_color = tool.Colors.YELLOW

last_cure_time = 0
current_time_sec = 0
current_time_ms = 0

enemy_damage = 10
enemy_damage_buff = 1
random_time = 2000

longest_survived_time = {}
for i in range(1, 7):
    longest_survived_time.update({f"level{i}": dict.fromkeys(g_m, 0)})
# print(longest_survived_time)

has_buy_crazy = False
crazy_btn_text = ""

B_WIDTH = 240
B_HEIGHT = 80
max_scroll_y = 1435


# --- 依照要求順序排列的升級商店資料 ---
# 假設你有一個變數控制分頁：shop_tab = "survival" (或是 "combat")

current_p_num = 1


def update_upgrade_hub_layout():
    global upgrade_hub_layout
    upgrade_hub_layout = {}

    # 1. 根據目前分頁選擇資料源
    current_cfg = UPGRADE_SURVIVAL if shop_page == "survival" else UPGRADE_COMBAT

    p_colors = [
        tool.Colors.RED,
        tool.Colors.ORANGE,
        tool.Colors.YELLOW,
        tool.Colors.GREEN,
        tool.Colors.CYAN,
        tool.Colors.BLUE,
        tool.Colors.PURPLE,
        tool.Colors.PINK,
    ]

    # 2. 直接迭代字典，不用管數字編號了
    for i, (key, cfg) in enumerate(current_cfg.items()):
        lvl = current_levels.get(key, 0)
        costs = cfg["costs"]
        is_world_max = lvl >= cfg["limits"][select_world]
        is_absolute_max = lvl >= len(costs)

        is_max = is_world_max or is_absolute_max

        prefix = f"{cfg['title']}: Lv{lvl + 1} "
        if is_max:
            display_text = prefix + "Max Level"
            display_color = tool.Colors.GRAY
        else:
            # 確保安全後，才大膽地讀取 costs[lvl]
            display_text = f"{cfg['title']}: Lv{lvl + 1} " + f"Cost: ${tool.num_to_KMBT(costs[lvl])}"
            display_color = p_colors[i % len(p_colors)]

        upgrade_hub_layout[key] = {"title": display_text, "color": display_color}


update_upgrade_hub_layout()


def calculate_final_stat(effect_type, base_p, grow, level):
    # 原始計算公式
    val = base_p + (level - 1) * grow

    # 根據不同效果套用不同的限制 (跟 apply_skin_effects 裡面的一樣)
    if effect_type == "enemy_damage":
        return tool.num_range(0.1, 1.0, val)
    elif effect_type == "player_size":
        return tool.num_range(0.5, 5.0, val)
    # 其他效果如果也有上限/下限，可以在這裡加 elif

    return val  # 沒有特殊限制的效果直接回傳


def get_upgrade_threshold(level):
    return 100 + (level - 1) * 50


def load_resets():
    global level_button_color, next_spawn_range, mode_speed_buff, gm_points_buff, game_mode, g_m, gm_i, spawn_time_debuff, enemy_damage_buff, levels_unlocked

    game_mode = g_m[gm_i]

    update_skill()

    # 遊戲模式設定
    if game_mode == "easy":
        level_button_color = tool.Colors.GREEN
        next_spawn_range = (10, 13)
        mode_speed_buff = 0.5
        gm_points_buff = 0.7
        spawn_time_debuff = 1
        enemy_damage_buff = 1
    elif game_mode == "normal":
        level_button_color = tool.Colors.YELLOW
        next_spawn_range = (14, 18)
        mode_speed_buff = 1
        gm_points_buff = 1
        spawn_time_debuff = 1
        enemy_damage_buff = 1
    elif game_mode == "hard":
        level_button_color = tool.Colors.ORANGE
        next_spawn_range = (17, 21)
        mode_speed_buff = 1.3
        gm_points_buff = 1.7
        spawn_time_debuff = 0.8
        enemy_damage_buff = 1
    elif game_mode == "super_hard":
        level_button_color = tool.Colors.RED
        next_spawn_range = (20, 24)
        mode_speed_buff = 2
        gm_points_buff = 2.2
        spawn_time_debuff = 0.6
        enemy_damage_buff = 1
    elif game_mode == "crazy":
        level_button_color = tool.Colors.PURPLE
        next_spawn_range = (23, 27)
        mode_speed_buff = 3
        gm_points_buff = 2.7
        spawn_time_debuff = 0.4
        enemy_damage_buff = 1.5
    mode_speed_buff *= Timer_Speed
    update_current_world_data(select_world)


def reset_game():
    global player_rect, player_size, player_color, player_speed, current_player_speed, treasures, treasure_points, next_spawn_range, points, mode_speed_buff, gm_points_buff, maybe_cheat, shoot_point
    global from_pause, level_button_color, last_hit_time, player_hp, player_max_hp, countdown, passed_time
    global coin_chance, now_treasure, treasure_config, last_cure_time, has_plus_points, has_save_survived_time, countdowning, trying_to_touch_player, invincible_duration
    global clicked_key, afk_timer, last_player_pos, AFK_LIMIT, change_dir_timer, lv_flash_timer, collide_player, bullet_damage, target_vol
    global shake_timer, flash_timer, total_flash_time, max_alpha, freeze_timer

    load_resets()
    apply_skin_effects()

    target_vol = 0.5

    shake_timer = 0

    flash_timer = 0  # 當前剩餘時間
    total_flash_time = 30  # 框框顯示的總影格數
    max_alpha = 150  # 紅框最亮時的透明度（0-255）

    freeze_timer = 0

    lv_flash_timer = 0

    shoot_point = 0

    clicked_key = None

    invincible_duration = now_skills["p8"] / 1000

    # 玩家設定
    player_size = now_skills["p4"] * player_size_buff
    player_color, player_speed, current_player_speed = (
        now_player_skin,
        (5 + now_skills["p1"]) * player_speed_buff,
        (5 + now_skills["p1"]) * player_speed_buff,
    )
    player_rect = pygame.Rect(
        WIDTH // 2 - player_size // 2,
        HEIGHT // 2 - player_size // 2,
        player_size,
        player_size,
    )

    tool.reset_timer()
    passed_time, _ = tool.sec_timer(True)
    countdown = 3 - (passed_time)  # 倒數 3 秒

    afk_timer = 0  # 累計閒置時間
    last_player_pos = [0, 0]  # 記錄上一次的位置
    AFK_LIMIT = 40

    points = 0

    maybe_cheat = from_pause = False

    has_plus_points = False
    has_save_survived_time = False

    last_hit_time = -10  # 上次受傷時間，預設負值確保開局能受傷

    last_cure_time = 0

    countdowning = True

    trying_to_touch_player = False

    player_max_hp = int(now_skills["p6"] * player_max_hp_buff)
    player_hp = player_max_hp

    change_dir_timer = 2  # 設定為兩秒

    treasure_points = 0

    # 1. 定義寶藏的配置表格 (稀有度, 顏色, 機率, 分數範圍)
    treasure_config = [
        ("Common", tool.Colors.WHITE, int(150 // (now_skills["p11"] * 3)), (2, 5)),
        ("Uncommon", tool.Colors.GREEN, int(140 // (now_skills["p11"] * 2)), (5, 9)),
        ("Rare", tool.Colors.BLUE, int(80 // now_skills["p11"]), (8, 12)),
        ("Epic", tool.Colors.PURPLE, int(60 * now_skills["p11"]), (11, 15)),
        ("Legendary", tool.Colors.ORANGE, int(40 * now_skills["p11"]), (15, 18)),
        ("Mythic", tool.Colors.RED, int(24 * now_skills["p11"] * 2), (17, 20)),
        ("Exotic", tool.Colors.CYAN, int(8 * now_skills["p11"] * 2), (20, 23)),
        ("Divine", tool.Colors.GOLD, int(1 * now_skills["p11"] * 3), (23, 27)),
    ]

    # 2. 自動生成 treasures 列表
    treasures = []
    for name, color, chance, pts in treasure_config:
        treasures.append(
            {
                "rarity": name,
                "color": color,
                "chance": max(1, chance),
                "add_points": pts,
                # 下面這些是所有寶藏都一樣的設定，寫一次就好
                "x": random.randint(300, WIDTH - 30),
                "y": random.randint(100, HEIGHT - 100),
                "show": False,
                "can_spawn": True,
                "next_spawn_at": random.randint(*next_spawn_range),  # type: ignore
                "scale": 1.3 if name in ["Divine", "Exotic", "Mythic"] else 1.0,
            }
        )

    # 這樣不會永遠固定是 treasures[0]
    now_treasure = random.choice(treasures)

    # 統一計算第一次出現的時間
    cooldown = random.randint(*next_spawn_range)  # type: ignore
    reduction = now_skills["p2"]

    # 設定目標時間：現在時間 + (隨機冷卻 - 技能減免)
    now_treasure["next_spawn_at"] = max(2, int(cooldown - reduction))
    collide_player = False

    coin_chance = []
    for t in treasures:
        for _ in range(t["chance"]):
            coin_chance.append(t["rarity"])
    bullet_list.clear()  # 確保子彈列表在重置時被清空
    bullet_damage = 10


reset_game()


def print_coin_chance():
    global coin_chance, treasures
    print("💰 金幣機率表:")
    total = len(coin_chance)
    for t in treasures:
        name = t["rarity"]
        count = coin_chance.count(name)
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"{name:10} : {count:2} ({percentage:4.1f}%)")


now_flash_color = tool.Colors.RED


flash_width = 20

def draw_screen_flash(color, total_time, max_alpha, flash_width):
    """
    專門處理受傷閃爍的函式
    不需要傳入 flash_timer，因為我們直接從全域拿
    """
    # 這裡要宣告 global，才拿得到外面那個 flash_timer 變數
    global flash_timer

    if not isinstance(color, (tuple, list)) or len(color) < 3:
        color = (255, 0, 0)
        print(f"[DEBUG]: 傳入的顏色格式錯誤({color})，已使用預設紅色。")

    if flash_timer > 0:
        # print("--- 閃爍偵錯 ---")
        # print(f"傳入顏色: {color} (型態: {type(color)})")
        # print(f"計時器值: {flash_timer}")
        # 計算進度比例
        ratio = flash_timer / total_time

        # 根據比例決定厚度與透明度
        dynamic_width = int(flash_width * ratio)
        current_alpha = int(ratio * max_alpha)

        # 呼叫你的按鈕工具畫出邊框
        # 注意：這裡直接用 WIDTH, HEIGHT，因為它們也在 config 裡
        all_objs.TextButton(
            name="none",
            text="",
            text_color=tool.Colors.BLACK,
            button_color=(0, 0, 0, 0),
            rect=pygame.Rect(0, 0, WIDTH, HEIGHT),
            font_size=0,
            border_width=dynamic_width,
            normal_border_color=color,
        ).draw(screen, alpha=current_alpha)

        # 🌟 這裡最重要：直接修改外面的 flash_timer
        flash_timer -= 1


selected_level = "level1"


def player_move(keys):
    global player_speed, player_rect
    # ---------------持續按住事件---------------
    key_speed = 1
    # 在 handle_input 或主迴圈內
    dx, dy = 0, 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx = -1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx = 1
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy = -1
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy = 1

    if keys[pygame.K_LALT] or keys[pygame.K_RALT]:  # 按住 Alt 鍵加速
        key_speed = 0.1
    if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]:  # 按住 Ctrl 鍵減速
        key_speed = 0.5
    if keys[pygame.K_SPACE]:  # 按住 空白鍵 加速
        key_speed = 2

    # 如果有移動
    if dx != 0 or dy != 0:
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        # 計算這一幀在 X 軸和 Y 軸總共「預計要走多少像素」
        total_move_x = dx * player_speed * key_speed
        total_move_y = dy * player_speed * key_speed

        # 🌟 設定每一步最多只走 4 像素（確保小於任何方塊與玩家尺寸）
        step_size = 4

        # ==========================================
        # 🌟 1. X 軸拆步移動與防護
        # ==========================================
        rem_x = abs(total_move_x)  # 還剩下多少 X 距離要走
        sign_x = 1 if total_move_x > 0 else -1

        while rem_x > 0:
            # 這一小步要走的距離（如果不夠一整步，就走剩下的）
            current_step = min(step_size, rem_x)
            player_rect.x += current_step * sign_x
            rem_x -= current_step

            # 每走一小步，立刻做一次全體方塊安檢
            hit_x = False
            for ob in current_setup.get("obstacles", []):
                if ob.mode == "attack" and ob.can_collide:
                    ob_rect = ob.get_rect()
                    if player_rect.colliderect(ob_rect):
                        # 撞到了！用中心點推出牆外
                        if player_rect.centerx < ob_rect.centerx:
                            player_rect.x = ob_rect.left - player_size
                        else:
                            player_rect.x = ob_rect.right
                        hit_x = True
                        break

            # 💡 只要這一小步撞到了，剩下的 X 距離就不用走了，直接收工
            if hit_x:
                break

        # ==========================================
        # 🌟 2. Y 軸拆步移動與防護
        # ==========================================
        rem_y = abs(total_move_y)  # 還剩下多少 Y 距離要走
        sign_y = 1 if total_move_y > 0 else -1

        while rem_y > 0:
            current_step = min(step_size, rem_y)
            player_rect.y += current_step * sign_y
            rem_y -= current_step

            hit_y = False
            for ob in current_setup.get("obstacles", []):
                if ob.mode == "attack" and ob.can_collide:
                    ob_rect = ob.get_rect()
                    if player_rect.colliderect(ob_rect):
                        # 撞到了！用中心點推出牆外
                        if player_rect.centery < ob_rect.centery:
                            player_rect.y = ob_rect.top - player_size
                        else:
                            player_rect.y = ob_rect.bottom
                        hit_y = True
                        break

            if hit_y:
                break
    # ------------------------------------------

    # -----------------邊界判斷------------------
    if player_rect.x <= 0:  # 左邊界線
        player_rect.x = 0
    if player_rect.x >= WIDTH - player_size:  # 右邊界線
        player_rect.x = WIDTH - player_size
    if player_rect.y <= 0:  # 上方邊界
        player_rect.y = 0
    if player_rect.y >= HEIGHT - player_size:  # 下方邊界
        player_rect.y = HEIGHT - player_size
    # -------------------------------------------
    return player_rect.x, player_rect.y


def calculate_damage(damage):
    # 執行受傷邏輯 (扣血、飄字、設為無敵)
    if random.random() * 100 > now_skills["p13"]:
        # --- 閃避失敗：全額傷害 ---
        damage_multiplier = 1.0
        text_color = tool.Colors.RED
        text_content = f"-{damage}hp"
        dodged = False
    else:
        # --- 閃避成功：減傷傷害 (擦邊球) ---
        # 假設 now_p14_skill 是 0.2 (代表只受 20% 傷害)
        if now_skills["p14"]:
            damage_multiplier = round(1 - now_skills["p14"] / 100, 2)
        else:
            damage_multiplier = 1.0
        dodged = True
        text_color = tool.Colors.BLUE
        text_content = f"Dodge! -{int(damage * damage_multiplier)}hp  ({now_skills['p14']}%)"
        # print("[DEBUG]: Dodge!")
    return damage_multiplier, text_color, text_content, dodged


shake_range = 0
current_range = 0
total_shake_time = 0

running = True
game_state = "menu"
last_game_state = "menu"

modes_config = [
    ("easy", tool.Colors.GREEN),
    ("normal", tool.Colors.YELLOW),
    ("hard", tool.Colors.ORANGE),
    ("super_hard", tool.Colors.RED),
    ("crazy", tool.Colors.PURPLE),
]

# 2. 設定起始位置與間隔
start_y = 150  # 起始 Y
line_height = 40  # 每一行的高度
section_gap = 20  # 難度標籤與上方內容的間隔
one_mode_height = 90 + (len(all_levels) * 60 - 25)

floating_texts = []  # 放在遊戲開始前，用來裝所有的漂浮文字

target_points = 0

base_hp_rect = pygame.Rect(0, 0, 0, 0)

enemy_list = []
draw_button_color = tool.Colors.GOLD
last_draw_color = None

coin_rect2 = pygame.Rect(WIDTH - 110, 0, 100, 100)


COIN_IMAGES = {}

for t in treasure_config:
    img_path = BASE_DIR / "images" / "treasures" / f"{t[0].lower()}.png"

    if img_path.exists():
        # 載入並轉換為帶有透明度的格式
        surface = pygame.image.load(str(img_path)).convert_alpha()
        # 根據你的遊戲需求縮放大小 (例如 30x30)
        s_val = 1.1 if t[0] in ["Divine", "Exotic", "Mythic"] else 0.8

        # 2. 計算目標尺寸
        target_size = int(30 * s_val)

        # 2. 計算目標尺寸
        target_width = target_size

        # 取得原始圖片的大小
        orig_rect = surface.get_rect()
        # 計算比例： 寬度 / 原始寬度
        ratio = target_width / orig_rect.width
        # 根據比例算出高度
        target_height = int(orig_rect.height * ratio)

        # 進行縮放
        COIN_IMAGES[t[0].lower()] = pygame.transform.scale(surface, (target_width, target_height))
    else:
        # 如果找不到圖，就印出警告，方便你除錯
        print(f"找不到圖片檔案: {img_path}")

# print(COIN_IMAGES)


collide_player = True
click_pos = None


def get_key(t, cfg):
    current_config = UPGRADE_SURVIVAL if shop_page == "survival" else UPGRADE_COMBAT
    return t in current_config and cfg == current_config[t]


upgrade_buttons = {}

alto_shoot = now_skills["p20"]

# 設定文字與玩家的間距
padding = 25

current_setup = {}

currnet_time_sec = 0
countdowning = False
