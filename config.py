import json
import math
import random
from pathlib import Path

import pygame

import tool  # 載入你的工具包

BASE_DIR = Path(__file__).parent

SAVE_PATH = BASE_DIR / "save_game.json"
current_active_path = SAVE_PATH
LEVELS_PATH = BASE_DIR / "levels"
SOUND_PATH = BASE_DIR / "sounds"
BGM_PATH = BASE_DIR / "BGM"

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
UPGRADE_SURVIVAL = {
    "upgrade_p1": {
        "title": "Player Speed",
        "costs": [150, 450, 820, 1050, 1840, 2510, 4560, 7000, 9680, 12570, 15000, 18000, 20540, 27000, 29400, 31200, 38700, 43500, 48800, 56000],
        "skills": [0, 1.5, 3, 4.5, 6, 7.5, 9, 10.5, 12, 13.5, 15, 16.5, 18, 19.5, 21, 22.5, 24, 25.5, 27, 28.5, 30],
        "skill_desc": "Speed +{}",  # 顯示文字格式
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
        ],
        "skills": [0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2, 4.8, 5.4, 6.0, 6.6, 7.2, 7.8, 8.4, 9.0, 9.6, 10.2, 10.8, 11.4, 12.0, 12.6, 13.2, 13.8, 14.4, 15.0, 15.6, 16.2, 16.8, 17.4, 18.0],
        "skill_desc": "Spawn time -{} sec",
    },
    "upgrade_p3": {
        "title": "Points Multiplier",
        "costs": [380, 570, 850, 1350, 2480, 3900, 5670, 8970, 11200, 17000, 25400, 35000, 45000, 55000, 63500, 69000, 74200, 79600, 84500, 90000, 96000, 102000, 107000],
        "skills": [1, 1.09, 1.19, 1.3, 1.42, 1.55, 1.69, 1.84, 2.01, 2.19, 2.39, 2.61, 2.84, 3.1, 3.38, 3.68, 4.01, 4.37, 4.76, 5.19, 5.66, 6.17, 6.73, 7.34],
        "skill_desc": "Point x{}",
    },
    "upgrade_p4": {
        "title": "Size",
        "costs": [200, 400, 700, 1200, 1800, 2400, 3700, 4500, 6000, 8050, 10500, 12500],
        "skills": [35, 33, 31, 29, 27, 25, 23, 21, 19, 17, 15, 13, 11],
        "skill_desc": "Size: {}px",
    },
    "upgrade_p5": {
        "title": "Enemy Spawn",
        "costs": [150, 380, 800, 1300, 2400, 3800, 5700, 7000, 10500],
        "skills": [0.1, 0.3, 0.5, 0.8, 1.0, 1.3, 1.6, 2.0, 2.3, 2.5],
        "skill_desc": "Spawn {}s",
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
        ],
        "skills": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 41, 43, 44, 45, 47, 49, 50, 51, 53, 54, 56, 57, 59, 60, 61, 63, 64, 66, 67, 69, 70],
        "skill_desc": "HP: {}",
    },
    "upgrade_p7": {
        "title": "Regen",
        "costs": [500, 800, 1200, 2000, 3500, 4700, 6500, 8300, 10500],
        # 這裡原本是 dict，建議也簡化，如果太複雜可以保持
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
        ],
        "skill_desc": "{}",
    },
    "upgrade_p8": {
        "title": "Invincible",
        "costs": [250, 700, 1000, 1200, 1400, 1700, 2300, 3700, 4500, 5700, 7600, 9800, 12000, 15800, 21400],
        "skills": [1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000],
        "skill_desc": "Time: {}ms",
    },
    "upgrade_p9": {
        "title": "Magnet",
        "costs": [800, 1500, 2400, 4500, 6800, 8600, 11000, 17000, 23500],
        "skills": [0, 30, 52, 74, 96, 118, 140, 162, 184, 200],  # 第一個為基礎值
        "skill_desc": "Range: {}px",
    },
    "upgrade_p10": {
        "title": "Magnet Strength",
        "costs": [700, 1500, 2400, 4700, 7000, 8800, 11500, 17800, 24000, 38700],
        "skills": [1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0],
        "skill_desc": "Magnet Strength x{}",
    },
    "upgrade_p11": {
        "title": "Luck",
        "costs": [500, 1000, 1600, 2300, 3100, 4000, 5000, 6200, 7500, 9000, 11400, 12500, 13600, 14800],
        "skills": [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 3.0, 3.2, 3.4, 3.6, 3.8, 4.0],
        "skill_desc": "Luck x{}",
    },
    "upgrade_p12": {
        "title": "Coin Multiplier",
        "costs": [500, 1240, 3870, 6800, 12450, 17500, 31200, 47800, 68000, 87000, 120300, 135100, 178000],
        "skills": [1.0, 1.2, 1.5, 1.7, 1.9, 2.1, 2.3, 2.6, 2.8, 3.0, 3.3, 3.5, 3.7, 4.0],
        "skill_desc": "Coins x{}",
    },
    "upgrade_p13": {
        "title": "Dodge Chance",
        "costs": [200, 600, 1200, 1900, 2500, 3800, 4500, 6400, 8700],
        "skills": [0, 5, 10, 14, 18, 23, 26, 28, 30, 33],  # %(機率)
        "skill_desc": "Chance: {}%",
    },
    "upgrade_p14": {
        "title": "Dodge Percent",
        "costs": [150, 340, 570, 800, 1200, 1800, 2400, 3700, 4800, 6000, 8000, 12000, 15450, 20000, 27800, 31000],
        "skills": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80],  # %(檢傷趴數)
        "skill_desc": "Damage - {}%",
    },
}

UPGRADE_COMBAT = {
    "upgrade_p15": {
        "title": "Can Shoot",
        "costs": [5000],
        "skills": [0, 1],
        "skill_desc": "Can Shoot {}",
    },
    "upgrade_p16": {
        "title": "Shoot CD",
        "costs": [800, 2300, 4500, 5100, 7500, 12000, 15000],
        "skills": [500, 450, 400, 350, 300, 250, 200, 150],
        "skill_desc": "CD: {}s",
    },
    "upgrade_p17": {
        "title": "Bullet Speed",
        "costs": [900, 1400, 2000, 3100, 4500, 5700, 7000, 9500],
        "skills": [3, 5, 7, 9, 11, 13, 15, 17, 19],
        "skill_desc": "Speed: {}",
    },
    "upgrade_p18": {
        "title": "Bullet Size",
        "costs": [500, 700, 1000, 1500, 2000, 3100, 5000],
        "skills": [5, 6, 7, 8, 9, 10, 11, 12],
        "skill_desc": "Size: {}",
    },
    "upgrade_p19": {
        "title": "Shoot Get Points",
        "costs": [1000, 2000, 3000, 5000, 7000, 10200, 15000, 18500, 24000],
        "skills": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "skill_desc": "Points: {}",
    },
    "upgrade_p20": {
        "title": "Alto Shoot",
        "costs": [10000],
        "skills": [0, 1],
        "skill_desc": "Range: {}",
    },
}

# a = UPGRADE_COMBAT["upgrade_p20"]["costs"]
# b = UPGRADE_COMBAT["upgrade_p20"]["skills"]
# # c = 0

# print(len(a) + 1)  # 測試用，懶著計算
# print(len(b))  # 測試用，懶著計算
# print(len(a) + 1 <= len(b))


# # print([c := round(c + 0.6, 1) for _ in range(1, 40)])

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
        "growth": [0.2, 0.08],
        "draw_weight": 20,
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
    },
    "dark orange": {
        "rarity": "Epic",
        "level": 1,
        "exp": 0,
        "has_owned": False,
        "color": tool.Colors.ORANGE2,
        "effect": ["points_multiplier", "max_hp", "speed"],
        "base_power": [2.3, 0.7, 0.6],
        "growth": [0.2, 0.1, 0.05],
        "draw_weight": 8,
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
        "growth": [0.5, 0.2],
        "draw_weight": 2,
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
    },
}


current_levels = {f"upgrade_p{i}": 0 for i in range(1, len(UPGRADE_SURVIVAL) + len(UPGRADE_COMBAT) + 1)}

now_player_skin = tool.Colors.RED
current_player_color_name = "red"


def get_skill_val(p_key):
    # 先從生存字典找，找不到再去戰鬥字典找
    cfg = UPGRADE_SURVIVAL.get(p_key) or UPGRADE_COMBAT.get(p_key)

    if not cfg:
        print(f"Error: {p_key} 不存在於任何設定檔中")
        return 0

    lvl = current_levels.get(p_key, 0)
    return cfg["skills"][lvl]


def update_skill():
    global now_skills
    now_skills = {f"p{i}": get_skill_val(f"upgrade_p{i}") for i in range(1, len(UPGRADE_SURVIVAL) + len(UPGRADE_COMBAT) + 1)}


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

# 載入圖片
IMG_PATH = Path(__file__).parent
# 左箭頭
try:
    # 載入圖片
    left_img_surface = pygame.image.load(str(IMG_PATH) + "/images/Left_Arrow.png").convert_alpha()
    # 縮放大小（如果原圖太大）
    left_img_size = 50
    left_img_surface = pygame.transform.scale(left_img_surface, (left_img_size, left_img_size))

    # 獲取 Rect 並設定位置
    left_rect = left_img_surface.get_rect()
    upgrade_left_rect = left_rect.copy()
    left_rect.center = (80, 120)
    upgrade_left_rect.center = (70, 110)
    left_img_loaded = True
except Exception as e:
    print(f"無法載入右箭頭: {e}")
    left_img_loaded = False
    # 備案：如果圖掉載入失敗，給它一個虛擬的 Rect 避免 blit 噴錯
    left_rect = pygame.Rect(170, 520, 40, 40)
# 右箭頭
try:
    # 載入圖片
    right_img_surface = pygame.image.load(str(IMG_PATH) + "/images/Right_Arrow.png").convert_alpha()
    # 縮放大小（如果原圖太大）
    right_img_size = 50
    right_img_surface = pygame.transform.scale(right_img_surface, (right_img_size, right_img_size))

    # 獲取 Rect 並設定位置
    right_rect = right_img_surface.get_rect()
    upgrade_right_rect = right_rect.copy()
    right_rect.center = (WIDTH - 80, 120)  # (WIDTH - 120, 520)
    upgrade_right_rect.center = (WIDTH - 70, 110)
    right_img_loaded = True
except Exception as e:
    print(f"無法載入右箭頭: {e}")
    right_img_loaded = False
    # 備案：如果圖掉載入失敗，給它一個虛擬的 Rect 避免 blit 噴錯
    right_rect = pygame.Rect(530, 520, 40, 40)
# --- 鎖的圖片載入 ---
try:
    lock_img_surface = pygame.image.load(str(IMG_PATH) + "/images/Lock.png").convert_alpha()
    lock_img_surface = pygame.transform.scale(lock_img_surface, (90, 90))
    lock_img_loaded = True
except FileNotFoundError as e:
    lock_img_loaded = False
    print(f"無法載入鎖圖案{e}")
# --- 標題圖片載入 ---
title_rect = pygame.Rect(WIDTH // 2 - 200, 120, 400, 180)
try:
    title_img_surface = pygame.image.load(str(IMG_PATH) + "/images/Escape_Them.png").convert_alpha()
    title_img_surface = pygame.transform.scale(title_img_surface, (400, 180))
    title_img_loaded = True

    title_rect = title_img_surface.get_rect()
    title_rect.center = (WIDTH // 2, 120)
except FileNotFoundError as e:
    title_img_loaded = False
    title_rect.center = pygame.Rect(WIDTH // 2, 200, 400, 150)
    print(f"無法載入標題圖片{e}")
# 錢幣用圖片
try:
    coin_wood_img_surface = pygame.image.load(str(IMG_PATH) + "/images/coin_img.png").convert_alpha()
    coin_wood_img_surface = pygame.transform.scale(coin_wood_img_surface, (100, 40))
    coin_wood_img_loaded = True

    coin_wood_rect = coin_wood_img_surface.get_rect()
    coin_wood_rect = (WIDTH - 110, 15)
except FileNotFoundError as e:
    coin_wood_img_loaded = False
    coin_wood_rect = pygame.Rect(WIDTH - 110, 15, 100, 40)
    print(f"無法載入錢幣用木板圖片{e}")
# 滑鼠
try:
    orig_mouse_img_surface = pygame.image.load(str(IMG_PATH) + "/images/mouse.png").convert_alpha()
    orig_mouse_img_surface = pygame.transform.scale(orig_mouse_img_surface, (36, 45))
    mouse_img_surface = orig_mouse_img_surface
    mouse_img_loaded = True

    mouse_rect = orig_mouse_img_surface.get_rect()
    mouse_rect = (0, 0)
except FileNotFoundError as e:
    mouse_img_loaded = False
    mouse_rect = pygame.Rect(0, 0, 0, 0)
    print(f"無法載入錢幣用木板圖片{e}")
    print("滑鼠圖片炸掉啦！")

# 音效專區
sounds = {
    # "click": pygame.mixer.Sound(str(SOUND_PATH / "click.wav")),
    # 升級頁面音效
    "buy_error": pygame.mixer.Sound(str(SOUND_PATH / "buy_error.wav")),
    "buy_success": pygame.mixer.Sound(str(SOUND_PATH / "buy_success.wav")),
    # 遊玩時音效
    "coin": pygame.mixer.Sound(str(SOUND_PATH / "coin.wav")),
    "epic_coin": pygame.mixer.Sound(str(SOUND_PATH / "epic_coin.wav")),
    "shoot": pygame.mixer.Sound(str(SOUND_PATH / "shoot.wav")),
    "hurt": pygame.mixer.Sound(str(SOUND_PATH / "hurt.wav")),
    "slow_heart_beat": pygame.mixer.Sound(str(SOUND_PATH / "slow_heart_beat.wav")),
    "fast_heart_beat": pygame.mixer.Sound(str(SOUND_PATH / "fast_heart_beat.wav")),
    "steal": pygame.mixer.Sound(str(SOUND_PATH / "steal.wav")),
}
sounds["coin"].set_volume(0.5)
sounds["shoot"].set_volume(0.2)
sounds["fast_heart_beat"].set_volume(1.0)
sounds["slow_heart_beat"].set_volume(1.0)
sounds["steal"].set_volume(1.0)

shoot_channel = pygame.mixer.Channel(1)
heart_channel = pygame.mixer.Channel(2)
buy_channel = pygame.mixer.Channel(3)
current_heart = None
current_vol = 0.5
target_vol = 0.5


class Enemy:
    def __init__(self, show_time, speed, slow_speed, color, angle_range=(10, 80), size=10, damage=10, types="normal"):
        self.show_time = show_time
        self.color = color
        self.types = [types] if isinstance(types, str) else types
        self.damage = damage

        # 座標與大小
        self.x = random.randint(50, WIDTH - 50)
        self.y = random.randint(20, HEIGHT - 20)
        self.width = int(size * 3)
        self.height = int(size * 1.5)

        # 速度相關
        self.normal_speed = speed
        self.slow_speed = slow_speed
        self.current_speed = speed

        # 方向與角度
        self.angle_range = angle_range
        self.angle = random.randint(*angle_range)
        self.x_dir = random.choice([-1, 1])
        self.y_dir = random.choice([-1, 1])

        self.current_dx, self.current_dy = tool.get_direction(self.angle)

        # 狀態與計時
        self.show = False
        self.mode = "waiting"
        self.last_change_time = 0
        self.time_lasting = 1000  # 要持續的時間
        self.random_time_limit = random.randint(800, 2300)  # 給 random_angle 用的

    def update(self, current_time_ms, current_time_sec, player_rect, mouse_pos, now_treasure, screen):
        # 1. 模式切換邏輯
        spawn_start_time = int(self.show_time * spawn_time_debuff)
        attack_start_time = spawn_start_time + buffer_duration

        if current_time_sec >= attack_start_time:
            self.mode = "attack"
            self.show = True
        elif current_time_sec >= spawn_start_time:
            self.mode = "spawning"
            self.show = True
        else:
            self.mode = "waiting"
            self.show = False

        if not self.show:
            return

        # 2. 建立碰撞盒
        e_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # 3. 處理「生成中」模式
        if self.mode == "spawning":
            if current_time_ms % 500 < 250:
                pygame.draw.rect(screen, self.color, e_rect)
            return

        # 4. 處理「攻擊中」模式
        if self.mode == "attack":
            if e_rect.collidepoint(mouse_pos):
                target_speed = self.slow_speed
            else:
                target_speed = self.normal_speed
            # --- 移動邏輯區 ---
            self._handle_movement(current_time_ms, target_speed, mode_speed_buff, player_rect, now_treasure)

            # --- 邊界反彈 ---
            self._check_bounds()

            # --- 繪製與碰撞 ---
            e_rect.topleft = (self.x - offset_x, self.y - offset_y)
            pygame.draw.rect(screen, self.color, e_rect)

            # 碰撞檢測 (受傷邏輯建議放在這裡，或回傳 e_rect 讓主程式判斷)
        return e_rect

    def _handle_movement(self, current_time_ms, target_speed, mode_speed_buff, player_rect, now_treasure):
        global collide_player
        self_vec = pygame.math.Vector2(self.x + self.width / 2, self.y + self.height / 2)
        e_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # 平滑調整當前速度
        self.current_speed += (target_speed - self.current_speed) * 0.1
        final_speed = self.current_speed * mode_speed_buff

        # --- 1. 優先權最高：衝刺模式 (Sprint) ---
        # 如果正在衝刺，強制執行衝刺位移並跳過其他邏輯
        if "sprint" in self.types:
            time_passed = current_time_ms - self.last_change_time
            if 4000 < time_passed <= (4000 + self.time_lasting):
                # 執行衝刺位移後直接 return，不執行後面的 eat_coin 或 chaser
                self.x += self.current_dx * final_speed * self.x_dir * 2.0
                self.y += self.current_dy * final_speed * self.y_dir * 2.0
                return
            elif time_passed > 4000 + self.time_lasting:
                self.last_change_time = current_time_ms

        # --- 2. 優先權中等：搶錢模式 (Eat Coin) ---
        if "eat_coin" in self.types and now_treasure.get("show", False):
            coin_vec = pygame.math.Vector2(now_treasure["x"] + 15, now_treasure["y"] + 15)
            direction = coin_vec - self_vec
            if direction.length() > 5:
                dir_norm = direction.normalize()
                self.x += dir_norm.x * final_speed
                self.y += dir_norm.y * final_speed
                collide_player = False
                pygame.draw.line(screen, self.color, self_vec, coin_vec, 1)
            return  # 鎖定錢幣時，不執行後續追蹤

        # --- 3. 優先權低：追蹤模式 (Chaser) ---
        elif "chaser" in self.types:
            player_vec = pygame.math.Vector2(player_rect.center)
            direction = player_vec - self_vec
            if direction.length() > 5 and not e_rect.colliderect(player_rect):
                dir_norm = direction.normalize()
                # 🌟 修正：這裡不要再乘 normal_speed * current_speed，統一用 final_speed
                self.x += dir_norm.x * final_speed
                self.y += dir_norm.y * final_speed
            return

        # --- 4. 其他基礎移動模式 (Zigzag, Random, etc.) ---
        elif "zigzag" in self.types:
            self.x += 2 * self.x_dir * final_speed
            wave = math.sin(current_time_ms * 0.005) * 3
            self.y += wave * final_speed

        elif "random" in self.types:
            if current_time_ms - self.last_change_time > 2000:
                self.x_dir = random.choice([-1, 0, 1])
                self.y_dir = random.choice([-1, 0, 1])
                self.last_change_time = current_time_ms
            self.x += self.x_dir * final_speed
            self.y += self.y_dir * final_speed

        elif "random_angle" in self.types:
            if current_time_ms - self.last_change_time > self.random_time_limit:
                self.random_time_limit = random.randint(800, 2300)
                self.angle = random.randint(0, 360)
                self.current_dx, self.current_dy = tool.get_direction(self.angle)
                self.last_change_time = current_time_ms
            self.x += self.current_dx * final_speed * self.x_dir
            self.y += self.current_dy * final_speed * self.y_dir

        else:
            # 預設普通移動
            self.x += self.current_dx * final_speed * self.x_dir
            self.y += self.current_dy * final_speed * self.y_dir

    def _check_bounds(self):
        # 處理 X 軸邊界
        if self.x <= 0 or self.x >= WIDTH - self.width:
            self.x_dir *= -1  # 撞到左右牆壁，水平方向反轉
            self.x = tool.num_range(0, WIDTH - self.width, self.x)

        # 處理 Y 軸邊界
        if self.y <= 0 or self.y >= HEIGHT - self.height:
            self.y_dir *= -1  # 撞到上下牆壁，垂直方向反轉
            self.y = tool.num_range(0, HEIGHT - self.height, self.y)


class Bullet:
    def __init__(self, x, y, color, angle, speed, bom_range, base_damage, type="normal"):
        self.x, self.y = x, y
        self.color = color
        self.angle = angle
        self.speed = speed
        self.bom_range = bom_range
        self.damage = base_damage
        self.type = type
        self.current_bom_radius = 0
        self.is_exploding = False
        self.collide_player = False
        self.has_dealt_bom_damage = False
        self.has_triggered_explosion = False

        # 預先計算方向向量
        self.dx, self.dy = tool.get_direction(self.angle)

    def update(self, player_rect):
        global player_hp, last_hit_time, shake_timer, shake_range, last_cure_time

        self.rect = pygame.Rect(self.x, self.y, 25, 25)
        out_of_bounds = self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT

        # 🌟 核心修改：如果已經被標記為爆炸（例如被打中），直接跳過飛行，進入爆炸動畫
        if self.is_exploding:
            if not self.has_triggered_explosion:
                self.has_triggered_explosion = True
                return "HIT", self.rect

            if self.current_bom_radius <= self.bom_range:
                self.current_bom_radius += 5
                return "EXPLODING", self.rect
            else:
                return "REMOVE", None

        # 正常飛行階段 (增加判斷：如果沒出界也沒撞人)
        if not (out_of_bounds or self.collide_player):
            # ... 原有的檢查撞玩家邏輯 ...
            if player_rect.colliderect(self.rect):
                self.collide_player = True
                self.is_exploding = True  # 撞到人也標記爆炸
                # (擊退邏輯保持不變)

            # 位移計算
            self.x += self.dx * self.speed * mode_speed_buff
            self.y += self.dy * self.speed * mode_speed_buff
            return "FLYING", self.rect

        else:
            # 這是原本的出界處理
            self.is_exploding = True
            return "FLYING", self.rect  # 這一幀先回傳飛行，下一幀會進入最上面的 is_exploding 判斷

    def draw(self, screen, offset_x, offset_y):
        if self.is_exploding:
            pygame.draw.circle(screen, self.color, (int(self.x) - offset_x, int(self.y) - offset_y), self.current_bom_radius, 5)
        else:
            draw_rect = pygame.Rect(self.x - offset_x, self.y - offset_y, 25, 25)
            pygame.draw.rect(screen, self.color, draw_rect)


class Player_Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.speed = now_skills["p17"]  # 子彈速度
        self.angle = angle  # 弧度 (Radians)
        self.radius = now_skills["p18"]  # 子彈大小
        self.active = True

    def update(self):
        # 根據角度計算 X 和 Y 的位移
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        # 如果超出螢幕就失效
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.active = False

        return pygame.draw.circle(screen, tool.Colors.YELLOW, (int(self.x), int(self.y)), self.radius)

    def draw(self, screen):
        pygame.draw.circle(screen, tool.Colors.YELLOW, (int(self.x), int(self.y)), self.radius)


player_bullets = []
last_shot_time = 0  # 用來控制射速 (Cooldown)


# 作弊變數
Invincible = False
Time_Speed = 1
Let_Time_Go_Fast = 1


def check_data_consistency(data_list):
    return sum((int(n) ^ (i + 1)) << 1 for i, n in enumerate(data_list))


God = False

if any([Invincible, Time_Speed != 1, Let_Time_Go_Fast != 1]):
    print("--- 檢測到作弊變數已更改 ---")
    enter = input("請輸入授權碼以繼續：")

    # 將輸入轉為 ASCII 列表
    enter_list = [ord(ch) for ch in enter]
    eln = check_data_consistency(enter_list)
    if eln == 6370:
        print("密碼正確，上帝模式啟動！")
        God = True  # 背景音樂
    else:
        print("密碼錯誤，重置為正常模式。")
        Invincible = False
        Time_Speed = 1
        Let_Time_Go_Fast = 1
        God = False
pygame.mixer.music.set_volume(0.5)  # 靜音：0, 正常：0.5
if God:
    pygame.mixer.music.load(str(BGM_PATH / "God.mp3"))
else:
    pygame.mixer.music.load(str(BGM_PATH / "Game_bgm 3.mp3"))


save_files = list(BASE_DIR.glob("save_game*.json"))
selected_save_name = None

# 遍歷這些檔案
for file_path in save_files:
    """
    file_path 是一個 Path 物件
    .name 會得到檔名(例如: save_game2.json)
    .stem 會得到不含副檔名的名字(例如: save_game2)
    """
    print(f"找到存檔：{file_path.name}")


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


buttons = []
for _ in range(20):
    buttons.append(pygame.Rect(0, 0, 0, 0))

# 顯示專區
next_spawn_range = random.randint(14, 20)

# 遊戲模式
g_m = ["easy", "normal", "hard", "super_hard", "crazy"]
gm_i = 1
game_mode = g_m[gm_i]

# 解鎖關卡的價格，第一個是卡位用，第一關是０元
level_costs = {
    "world1": [0, 0, 500, 1000, 5000, 15000, 35000, 50000, 75000, 100000, 130000],
    "world2": [0, 0]  # 目前還沒有關卡
}

# 下個關卡需要秒數，第一個卡位用
level_need_record = {
    "world1": [0, 0, 50, 60, 60, 70, 70, 80, 90, 90, 100],
    "world2": [0, 0]  # , 50, 60, 60, 70, 70, 80, 90, 90, 100
}
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
all_worlds_unlocked = {"world1": 1, "world2": 1} # 這是給存檔紀錄用的字典


def update_world_data(select_world):
    global current_world_costs, current_world_need_record
    world_key = f"world{select_world}"
    level_costs[world_key] = current_world_costs  # 確保第一個卡位是0元
    level_need_record[world_key] = current_world_need_record  # 確保第一個卡位是0秒
    all_worlds_unlocked[world_key] = levels_unlocked


select_world = 1
update_current_world_data(select_world)
lv_i = 0
current_level = all_levels[lv_i]


# 載入圖片
IMG_PATH = Path(__file__).parent

l_img_show, r_img_show = False, True

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

last_cure_time = 0
current_time_sec = 0

enemy_damage = 10
enemy_damage_buff = 1
random_time = 2000

# --- 資料區：定義多個鎖的位置 ---
# 你可以用列表存座標，想放幾個就寫幾個
skin_unlocked_locks = {
    "red": {"x": 70, "y": 150, "show": False, "text_col": tool.Colors.WHITE},
    "orange": {"x": 190, "y": 150, "show": True, "text_col": tool.Colors.BLACK},
    "dark orange": {"x": 310, "y": 150, "show": True, "text_col": tool.Colors.BLACK},
    "yellow": {"x": 430, "y": 150, "show": True, "text_col": tool.Colors.BLACK},
    "green": {"x": 550, "y": 150, "show": True, "text_col": tool.Colors.BLACK},
    "light blue": {"x": 70, "y": 230, "show": True, "text_col": tool.Colors.BLACK},
    "blue": {"x": 190, "y": 230, "show": True, "text_col": tool.Colors.WHITE},
    "purple": {"x": 310, "y": 230, "show": True, "text_col": tool.Colors.WHITE},
    "pink": {"x": 430, "y": 230, "show": True, "text_col": tool.Colors.WHITE},
    "white": {"x": 550, "y": 230, "show": True, "text_col": tool.Colors.BLACK},
    "gray": {"x": 70, "y": 310, "show": True, "text_col": tool.Colors.BLACK},
    "black": {"x": 190, "y": 310, "show": True, "text_col": tool.Colors.WHITE},
    # VIP皮膚區
    "gold": {"x": 190, "y": 430, "show": True, "text_col": tool.Colors.BLACK},
    "brown": {"x": 310, "y": 430, "show": True, "text_col": tool.Colors.WHITE},
    "dark green": {"x": 430, "y": 430, "show": True, "text_col": tool.Colors.WHITE},
}

longest_survived_time = {}
for i in range(1, 7):
    longest_survived_time.update({f"level{i}": dict.fromkeys(g_m, 0)})
print(longest_survived_time)

has_buy_crazy = False
crazy_btn_text = ""

B_WIDTH = 240
B_HEIGHT = 80
max_scroll_y = 1435


# --- 依照要求順序排列的升級商店資料 ---
# 假設你有一個變數控制分頁：shop_tab = "survival" (或是 "combat")


def update_upgrade_hub_layout():
    global upgrade_hub_layout
    upgrade_hub_layout = {}

    # 1. 根據目前分頁選擇資料源
    current_cfg = UPGRADE_SURVIVAL if shop_page == "survival" else UPGRADE_COMBAT

    p_colors = [tool.Colors.RED, tool.Colors.ORANGE, tool.Colors.YELLOW, tool.Colors.GREEN, tool.Colors.CYAN, tool.Colors.BLUE, tool.Colors.PURPLE, tool.Colors.PINK]

    # 2. 直接迭代字典，不用管數字編號了
    for i, (key, cfg) in enumerate(current_cfg.items()):
        lvl = current_levels.get(key, 0)
        costs = cfg["costs"]
        is_max = lvl >= len(costs)

        prefix = f"{cfg['title']}: Lv{lvl + 1} "
        if is_max:
            display_text = prefix + "Max Level"
            display_color = tool.Colors.GRAY
        else:
            display_text = prefix + f"Cost: ${tool.num_to_KMBT(costs[lvl])}"
            # 顏色根據當前分頁的順序跑循環
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
        spawn_time_debuff = enemy_damage_buff = 1
    elif game_mode == "normal":
        level_button_color = tool.Colors.YELLOW
        next_spawn_range = (14, 18)
        mode_speed_buff = 1
        gm_points_buff = 1
        spawn_time_debuff = enemy_damage_buff = 1
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
    mode_speed_buff *= Let_Time_Go_Fast
    update_current_world_data(select_world)


def make_enemy_list(level):
    json_path = LEVELS_PATH / f"level{level}.json"

    # 檢查檔案是否存在
    if not json_path.exists():
        print(f"找不到關卡檔案: {json_path}")
        # 直接回傳一個預設的 Enemy 物件
        return [Enemy(show_time=-10, speed=3, slow_speed=1, color=tool.Colors.WHITE)]

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    enemy_list = []
    for e in data["enemies"]:
        # 1. 處理參數 (維持你原本的預設值邏輯)
        a_range = tuple(e.get("angle_range", (10, 80)))
        e_color = tool.Colors.get_color(e["color"], tool.Colors.WHITE)

        # 2. 【關鍵改動】直接建立 Enemy 物件
        # 這裡傳入的參數要對應你 Enemy 類別 __init__ 的順序
        new_enemy = Enemy(
            show_time=e["show_time"],
            speed=e["speed"],
            slow_speed=e["slow_speed"],
            color=e_color,
            angle_range=a_range,
            size=e.get("size", 10),
            damage=e.get("damage", 10),
            types=e.get("type", "normal"),
        )

        enemy_list.append(new_enemy)

    return enemy_list


def make_cannon_list(level):

    def make_cannon(x, y, angle, show_time, fire_rate=2000, bullet_speed=5, bom_range=100, color=tool.Colors.GRAY, move_speed=0, type="normal", bullet_type="normal", damage=10):
        return {
            "x": tool.num_range(0, WIDTH - 30, x),
            "y": tool.num_range(0, HEIGHT - 30, y),
            "angle": angle,
            "fire_rate": fire_rate,
            "bullet_speed": bullet_speed,
            "bom_range": bom_range,
            "last_fire_time": 0,  # 初始開火冷卻
            "color": color,
            "show": False,
            "show_time": show_time,
            "mode": "waiting",
            "width": 30,  # 砲台可以設大一點
            "height": 30,
            "move_speed": move_speed,  # 砲台移動速度，0 表示不移動
            "move_dir": 1,  # 1 或 -1，控制移動方向  X、Y軸共用一個，因為不會同時有XY一起移動的大砲
            "type": type,
            "bullet_type": bullet_type,
            "damage": damage,
        }

    json_path = LEVELS_PATH / f"level{level}.json"

    if not json_path.exists():
        print(f"找不到檔案: {json_path}")
        return []

    with open(str(json_path), encoding="utf-8") as f:
        data = json.load(f)

    cannon_list = []
    for c in data["cannons"]:
        cannon_data = make_cannon(
            x=c["x"],
            y=c["y"],
            angle=c["angle"],
            show_time=c["show_time"],
            fire_rate=c.get("fire_rate", 2000),
            bullet_speed=c.get("bullet_speed", 5),
            color=tool.Colors.get_color(c["color"], tool.Colors.GRAY),  # 沒抓到就給灰色
            move_speed=c.get("move_speed", 0),
            type=c.get("type", "normal"),
            bullet_type=c.get("bullet_type", "normal"),
            damage=c.get("damage", 10),
        )

        cannon_list.append(cannon_data)
    return cannon_list


def get_level_data(level):
    enemy_list = make_enemy_list(level)
    cannon_list = make_cannon_list(level)
    with open(LEVELS_PATH / f"level{level}.json", encoding="utf-8") as f:
        data = json.load(f)
        level_mutiply = data.get("level_multiplier", 1)
        level_name = data.get("level_name")
    return enemy_list, cannon_list, level_mutiply, level_name


# 砲台的子彈生成函式，放在外面讓子彈生成時也能呼叫
def make_bullet(x, y, angle, speed, bom_range, color=tool.Colors.GRAY, base_damage=10, type="normal"):
    return Bullet(x, y, color, angle, speed, bom_range, base_damage, type)


bullet_list = []  # 全局子彈列表，當砲台開火時會往裡面添加子彈
now_bom_range = 1


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
                "next_spawn_at": random.randint(*next_spawn_range),  # type:ignore
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

    print("💰 金幣機率表:")
    total = len(coin_chance)
    for t in treasures:
        name = t["rarity"]
        count = coin_chance.count(name)
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"{name:10} : {count:2} ({percentage:4.1f}%)")
    bullet_list.clear()  # 確保子彈列表在重置時被清空
    bullet_damage = 10


reset_game()

now_flash_color = tool.Colors.RED


# config.py 內部


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
        tool.text_button("", tool.Colors.BLACK, color, 0, 0, WIDTH, HEIGHT, alpha=current_alpha, width_line=dynamic_width)

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
        # 如果是斜走 (dx, dy 都不為 0)，這裡除以 1.414 來修正速度
        if dx != 0 and dy != 0:
            dx *= 0.7071  # 1 / sqrt(2)
            dy *= 0.7071

        # 更新位置 (包含邊界檢查)
        player_rect.x += dx * player_speed * key_speed
        player_rect.y += dy * player_speed * key_speed
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

modes_config = [("easy", tool.Colors.GREEN), ("normal", tool.Colors.YELLOW), ("hard", tool.Colors.ORANGE), ("super_hard", tool.Colors.RED), ("crazy", tool.Colors.PURPLE)]

# 2. 設定起始位置與間隔
start_y = 150  # 起始 Y
line_height = 40  # 每一行的高度
section_gap = 20  # 難度標籤與上方內容的間隔
one_mode_height = 90 + (len(all_levels) * 60) - 25

floating_texts = []  # 放在遊戲開始前，用來裝所有的漂浮文字

target_points = 0

base_hp_rect = pygame.Rect(0, 0, 0, 0)

enemy_list = []
draw_button_color = tool.Colors.GOLD
last_draw_color = None


def coin_rect(player_rect=pygame.Rect(5000, 5000, 0, 0)):  # noqa: B008
    global total_points, target_points, WIDTH, alphas, coin_rect2
    diff = total_points - target_points

    if abs(diff) < 0.1:
        target_points = total_points
    else:
        target_points += diff * 0.1
    final_text = "$" + tool.num_to_KMBT(target_points)

    new_alpha = 255
    coin_rect2 = pygame.Rect(WIDTH - 110, 0, 100, 100)

    if player_rect.colliderect(coin_rect2):
        new_alpha = 100

    if new_alpha == 255:
        for enemy in enemy_list:
            if not getattr(enemy, "show", True):
                continue  # 沒出現的不算
            e_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)

            # 怪物碰到右上 OR 碰到左上，兩個一起變透明
            if e_rect.colliderect(coin_rect2):
                new_alpha = 100
                break

    if game_state == "3!2!1!":
        new_alpha = 255

    # --- 4. 同步套用到所有相關圖片 ---
    alphas[0] = new_alpha if game_state == "start_game" else 255

    # 讓金幣框變透明
    coin_wood_img_surface.set_alpha(alphas[0])
    screen.blit(coin_wood_img_surface, coin_wood_rect)

    # 文字也要同步
    tool.show_text(final_text, tool.Colors.WHITE, WIDTH - 60, 32, size=22, alpha=alphas[0], center=True)


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

initial_data = {
    "balance": 0,
    "upgrades": {
        "upgrade_p1": 0,
        "upgrade_p2": 0,
        "upgrade_p3": 0,
        "upgrade_p4": 0,
        "upgrade_p5": 0,
        "upgrade_p6": 0,
        "upgrade_p7": 0,
        "upgrade_p8": 0,
        "upgrade_p9": 0,
        "upgrade_p10": 0,
        "upgrade_p11": 0,
        "upgrade_p12": 0,
        "upgrade_p13": 0,
        "upgrade_p14": 0,
        "upgrade_p15": 0,
        "upgrade_p16": 0,
        "upgrade_p17": 0,
        "upgrade_p18": 0,
    },
    "records": {
        "level1": {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0},
        "level2": {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0},
        "level3": {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0},
        "level4": {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0},
        "level5": {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0},
        "level6": {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0},
        "level7": {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0},
        "level8": {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0},
        "level9": {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0},
    },
    "player_skins": {
        "red": {"rarity": "Common", "level": 1, "exp": 50, "has_owned": True, "color": [255, 0, 0], "effect": "none", "base_power": 1, "growth": 0, "draw_weight": 70},
        "white": {
            "rarity": "Common",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [255, 255, 255],
            "effect": ["speed", "points_multiplier"],
            "base_power": [1.3, 1.2],
            "growth": [0.05, 0.05],
            "draw_weight": 70,
        },
        "black": {
            "rarity": "Common",
            "level": 1,
            "exp": 50,
            "has_owned": False,
            "color": [0, 0, 0],
            "effect": ["points_coin_multiplier", "max_hp"],
            "base_power": [1.2, 1.1],
            "growth": [0.05, 0.1],
            "draw_weight": 70,
        },
        "gray": {
            "rarity": "Common",
            "level": 1,
            "exp": 50,
            "has_owned": False,
            "color": [150, 150, 150],
            "effect": ["invincible_time", "speed"],
            "base_power": [1.5, 1.1],
            "growth": [0.1, 0.05],
            "draw_weight": 70,
        },
        "green": {
            "rarity": "Rare",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [0, 255, 0],
            "effect": ["max_hp", "speed"],
            "base_power": [1.2, 0.7],
            "growth": [0.2, 0.08],
            "draw_weight": 20,
        },
        "yellow": {
            "rarity": "Rare",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [255, 255, 0],
            "effect": ["points_multiplier", "speed"],
            "base_power": [1.7, 0.8],
            "growth": [0.1, 0.08],
            "draw_weight": 20,
        },
        "blue": {"rarity": "Rare", "level": 1, "exp": 0, "has_owned": False, "color": [0, 0, 255], "effect": "enemy_damage", "base_power": 0.7, "growth": -0.04, "draw_weight": 20},
        "purple": {"rarity": "Rare", "level": 1, "exp": 0, "has_owned": False, "color": [128, 0, 128], "effect": "speed", "base_power": 1.2, "growth": 0.1, "draw_weight": 20},
        "orange": {
            "rarity": "Epic",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [255, 100, 0],
            "effect": "player_size",
            "base_power": 0.9,
            "growth": -0.01,
            "draw_weight": 8,
        },
        "light blue": {
            "rarity": "Epic",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [135, 206, 235],
            "effect": ["coin_multiplier", "player_size"],
            "base_power": [1.9, 0.8],
            "growth": [0.15, -0.02],
            "draw_weight": 8,
        },
        "pink": {
            "rarity": "Epic",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [255, 0, 255],
            "effect": ["speed", "points_coin_multiplier"],
            "base_power": [1.8, 0.9],
            "growth": [0.12, 0.1],
            "draw_weight": 8,
        },
        "dark orange": {
            "rarity": "Epic",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [200, 50, 0],
            "effect": ["points_multiplier", "max_hp", "speed"],
            "base_power": [2.3, 0.7, 0.6],
            "growth": [0.2, 0.1, 0.05],
            "draw_weight": 8,
        },
        "gold": {
            "rarity": "Legendary",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [255, 215, 0],
            "effect": ["coin_multiplier", "points_multiplier"],
            "base_power": [4, 1.5],
            "growth": [0.5, 0.2],
            "draw_weight": 2,
        },
        "brown": {
            "rarity": "Legendary",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [200, 100, 50],
            "effect": ["enemy_spawn_speed", "max_hp"],
            "base_power": [2, 1.2],
            "growth": [0.1, 0.25],
            "draw_weight": 2,
        },
        "dark green": {
            "rarity": "Legendary",
            "level": 1,
            "exp": 0,
            "has_owned": False,
            "color": [0, 100, 0],
            "effect": ["max_hp", "speed"],
            "base_power": [2.0, 1.2],
            "growth": [0.5, 0.15],
            "draw_weight": 2,
        },
    },
    "now_player_skin": [255, 0, 0],
    "current_skin_name": "red",
    "gm_i": 0,
    "has_buy_crazy": False,
    "levels_unlocked": 1,
    "save_version": 2,
}
