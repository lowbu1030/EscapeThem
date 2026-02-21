import json
import math
import random
import sys
from pathlib import Path

import pygame

import tool  # 載入你的工具包
from old_to_new import migrate_save_format

BASE_DIR = Path(__file__).parent

# 使用 / 符號就能合併路徑，超級直覺！
SAVE_PATH = BASE_DIR / "save_game.json"
current_active_path = SAVE_PATH
ENEMY_PATH = BASE_DIR / "enemies"

save_files = list(BASE_DIR.glob("save_game*.json"))
selected_save_name = None

# 2. 遍歷這些檔案
for file_path in save_files:
    """
    file_path 是一個 Path 物件
    .name 會得到檔名(例如: save_game2.json)
    .stem 會得到不含副檔名的名字(例如: save_game2)
    """
    print(f"找到存檔：{file_path.name}")


# 1. 初始化與基本設定
pygame.init()
WIDTH, HEIGHT = 700, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
tool.set_screen(screen)
screen_rect = screen.get_rect()
screen_text = "Escape Them!"
pygame.display.set_caption(screen_text)
clock = pygame.time.Clock()


class AFKError(Exception):
    def __init__(self):
        super().__init__("Error code: 1011451 - Process terminated due to severe idling.")


# 按下偵測專區
is_pressing = []
for _ in range(20):
    is_pressing.append(False)


def reset_pressing():
    is_pressing[:] = [False] * len(is_pressing)


# 顯示專區
next_spawn_range = random.randint(14, 20)

# 遊戲模式
g_m = ["easy", "normal", "hard", "super_hard", "crazy"]
gm_i = 1
game_mode = g_m[gm_i]

# 關卡
all_levels = ["level1", "level2", "level3", "level4", "level5"]
lv_i = 0
current_level = all_levels[lv_i]

# 先建立一個空的矩形佔位
levels_button = settings_button = upgrade_button = help_button = exit_button = player_rect = back_button = enemy_rect = pygame.Rect(0, 0, 0, 0)

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
    left_rect.center = (80, 120)  # 之後改好版面後改成(120, 520)
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
    right_rect.center = (WIDTH - 80, 120)  # (WIDTH - 120, 520)
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
# 先建立一個虛擬的 Rect 避免 blit 噴錯
title_rect = pygame.Rect(WIDTH // 2 - 200, 120, 400, 180)
try:
    title_img_surface = pygame.image.load(str(IMG_PATH) + "/images/Escape Them.png").convert_alpha()
    title_img_surface = pygame.transform.scale(title_img_surface, (400, 180))
    title_img_loaded = True

    # 獲取 Rect 並設定位置
    title_rect = title_img_surface.get_rect()
    title_rect.center = (WIDTH // 2, 120)
except FileNotFoundError as e:
    title_img_loaded = False
    title_rect.center = pygame.Rect(WIDTH // 2, 200, 400, 150)
    print(f"無法載入標題圖片{e}")

points = 0
total_points = 0
# 定義所有升級的詳細數據 (包含價格、技能數值、標題、說明)
UPGRADE_CONFIG = {
    "upgrade_p1": {
        "title": "Player Speed",
        "costs": [450, 820, 1050, 1840, 2510, 4560, 7000, 9680, 12570, 15000],
        "skills": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        "skill_desc": "Speed +{}",  # 顯示文字格式
    },
    "upgrade_p2": {
        "title": "Coin Spawn",
        "costs": [300, 600, 1000, 1800, 3500, 5000, 7500],
        "skills": [0, 0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2],
        "skill_desc": "Rate +{}",
    },
    "upgrade_p3": {
        "title": "Multiplier",
        "costs": [380, 570, 850, 1350, 2480, 3900, 5670, 8970, 11200, 17000, 25400],
        "skills": [1, 1.17, 1.36, 1.59, 1.86, 2.17, 2.53, 2.96, 3.46, 4.04, 4.72, 5.52],
        "skill_desc": "Point x{}",
    },
    "upgrade_p4": {
        "title": "Size",
        "costs": [200, 400, 700, 1200, 2500, 4500, 7500, 12500, 25700],
        "skills": [35, 33, 31, 28, 26, 23, 20, 17, 15, 12],
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
            300,
            500,
            780,
            1500,
            2450,
            4500,
            7500,
            9800,
            11000,
            13580,
            16050,
            20040,
            25100,
            30000,
            37500,
        ],
        "skills": [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40],
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
        "costs": [
            700,
            1000,
            1200,
            1400,
            1700,
            2300,
            3700,
            4500,
            5700,
            7600,
            9800,
            12000,
            15800,
            21400,
            25780,
        ],
        "skills": [
            1000,
            1200,
            1400,
            1600,
            1800,
            2000,
            2200,
            2400,
            2600,
            2800,
            3000,
            3200,
            3400,
            3600,
            3800,
            4000,
        ],
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
        "costs": [700, 1500, 2400, 4700, 7000, 8800, 11500, 17800, 24000],
        "skills": [1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8],
        "skill_desc": "Magnet Strength x{}",
    },
    "upgrade_p11": {
        "title": "Luck",
        "costs": [500, 1000, 1600, 2300, 3100, 4000, 5000, 6200, 7500, 9000],
        "skills": [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 3.0, 3.2],
        "skill_desc": "Luck x{}",
    },
    # "upgrade_p12": {
    #     "title": "Dash CD",
    #     "costs": [1200, 3000, 7000, 15000],
    #     "skills": [10, 8, 6, 4, 2.5],
    #     "skill_desc": "CD: {}s",
    # },
}

current_levels = {f"upgrade_p{i}": 0 for i in range(1, len(UPGRADE_CONFIG) + 1)}


def get_skill_val(p_key):
    lvl = current_levels[p_key]
    return UPGRADE_CONFIG[p_key]["skills"][lvl]


def update_skill():
    global now_p1_skill, now_p2_skill, now_p3_skill, now_p4_skill, now_p5_skill, now_p6_skill, now_p7_skill, now_p8_skill, now_p9_skill, now_p10_skill, now_p11_skill  # , now_p12_skill
    now_p1_skill = get_skill_val("upgrade_p1")
    now_p2_skill = get_skill_val("upgrade_p2")
    now_p3_skill = get_skill_val("upgrade_p3")
    now_p4_skill = get_skill_val("upgrade_p4")
    now_p5_skill = get_skill_val("upgrade_p5")
    now_p6_skill = get_skill_val("upgrade_p6")
    now_p7_skill = get_skill_val("upgrade_p7")
    now_p8_skill = get_skill_val("upgrade_p8")
    now_p9_skill = get_skill_val("upgrade_p9")
    now_p10_skill = get_skill_val("upgrade_p10")
    now_p11_skill = get_skill_val("upgrade_p11")
    # now_p12_skill = get_skill_val("upgrade_p12")


update_skill()

trying_to_touch_player = False
player_max_hp = 10
player_hp = player_max_hp
last_hit_time = -10  # 上次受傷時間，預設負值確保開局能受傷
invincible_duration = now_p8_skill / 1000  # 無敵時間 1秒，可升級
has_save_survived_time = False
draw_this_lock = False

last_cure_time = 0
current_time_sec = 0

enemy_damage = 10
enemy_damage_buff = 1

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

player_skins = {
    "red": {
        "color": tool.Colors.RED,
        "value": 0,
        "has_bought": True,
        "effect": "none",
        "power": 1,
    },
    "orange": {
        "color": tool.Colors.ORANGE,
        "value": 500,
        "has_bought": False,
        "effect": "player_size",
        "power": 0.9,
    },
    "dark orange": {
        "color": tool.Colors.ORANGE_2,
        "value": 1400,
        "has_bought": False,
        "effect": ["points_multiplier", "max_hp", "speed"],
        "power": [2.3, 0.7, 0.6],
    },
    "yellow": {
        "color": tool.Colors.YELLOW,
        "value": 900,
        "has_bought": False,
        "effect": ["points_multiplier", "speed"],
        "power": [1.7, 0.8],
    },
    "green": {
        "color": tool.Colors.GREEN,
        "value": 800,
        "has_bought": False,
        "effect": ["max_hp", "speed"],
        "power": [1.2, 0.7],
    },
    "light blue": {
        "color": tool.Colors.CYAN,
        "value": 1400,
        "has_bought": False,
        "effect": ["coin_multiplier", "player_size"],
        "power": [1.9, 0.8],
    },
    "blue": {
        "color": tool.Colors.BLUE,
        "value": 900,
        "has_bought": False,
        "effect": "enemy_damage",
        "power": 0.7,
    },
    "purple": {
        "color": tool.Colors.PURPLE,
        "value": 950,
        "has_bought": False,
        "effect": ["purple_enemy_damage", "speed"],
        "power": [0.2, 0.9],
    },
    "pink": {
        "color": tool.Colors.PINK,
        "value": 1200,
        "has_bought": False,
        "effect": ["speed", "points_coin_multiplier"],
        "power": [1.8, 0.9],
    },
    "white": {
        "color": tool.Colors.WHITE,
        "value": 720,
        "has_bought": False,
        "effect": ["speed", "points_multiplier"],
        "power": [1.3, 1.2],
    },
    "gray": {
        "color": tool.Colors.GRAY,
        "value": 750,
        "has_bought": False,
        "effect": ["invincible_time", "speed"],
        "power": [1.5, 1.1],
    },
    "black": {
        "color": tool.Colors.BLACK,
        "value": 700,
        "has_bought": False,
        "effect": ["black_enemy_damage", "speed"],
        "power": [0.2, 0.8],
    },
    "gold": {
        "color": tool.Colors.GOLD,
        "value": 3500,
        "has_bought": False,
        "effect": ["coin_multiplier", "points_multiplier"],
        "power": [4, 1.5],
    },
    "brown": {
        "color": tool.Colors.BROWN,
        "value": 2700,
        "has_bought": False,
        "effect": ["enemy_spawn_speed", "max_hp"],
        "power": [2, 1.2],
    },
    "dark green": {
        "color": tool.Colors.DARK_GREEN,
        "value": 2100,
        "has_bought": False,
        "effect": ["max_hp", "speed"],
        "power": [2.0, 1.2],
    },
}

longest_survived_time = {}
for i in range(1, 6):
    longest_survived_time.update({f"level{i}": dict.fromkeys(g_m, 0)})
print(longest_survived_time)

has_buy_crazy = False
crazy_btn_text = ""

B_WIDTH = 240
B_HEIGHT = 80
scroll_y = 0
max_scroll_y = 1435

level_costs = [0, 0, 1000, 3000, 6000, 9000]  # , 14000, 18500, 21400]  # 解鎖關卡的價格，第一個是卡位用，第一關是0元


# --- 依照要求順序排列的升級商店資料 ---
def update_upgrade_hub_layout():
    global upgrade_hub_layout
    upgrade_hub_layout = {}

    # 1. 這裡定義你原本 p1 ~ p8 的專屬顏色 (順序不能亂)
    # 對應: [速度, 金幣, 分數, 大小, 怪速, 血量, 回血, 無敵]
    p_colors = [
        tool.Colors.RED,  # p1 (速度)
        tool.Colors.ORANGE,  # p2 (金幣)
        tool.Colors.YELLOW,  # p3 (分數)
        tool.Colors.GREEN,  # p4 (大小)
        tool.Colors.CYAN,  # p5 (怪速)
        tool.Colors.BLUE,  # p6 (血量)
        tool.Colors.PURPLE,  # p7 (回血)
        tool.Colors.PINK,  # p8 (無敵)
        tool.Colors.RED,  # p9 (磁鐵)
        tool.Colors.ORANGE,  # p10 (磁鐵強度)
        tool.Colors.YELLOW,  # p11 (幸運)
        # tool.Colors.GREEN,  # p12 (衝刺)
    ]

    # 2. 自動生成 8 個按鈕的資料
    for i in range(1, len(UPGRADE_CONFIG) + 1):
        key = f"upgrade_p{i}"

        # 確保這個升級存在於設定檔中
        if key in UPGRADE_CONFIG:
            cfg = UPGRADE_CONFIG[key]  # 取得標題、價格表
            lvl = current_levels[key]  # 取得目前等級
            costs = cfg["costs"]

            # --- 判斷是否滿級 ---
            is_max = lvl >= len(costs)

            # --- 組合文字 (還原你原本的格式) ---
            # 格式範例: "Player Speed: Lv5 Cost: $2500"
            prefix = f"{cfg['title']}: Lv{lvl + 1} "

            if is_max:
                display_text = prefix + "Max Level"
                display_color = tool.Colors.GRAY  # 滿級變灰色
            else:
                display_text = prefix + f"Cost: ${tool.num_to_KMBT(costs[lvl])}"
                display_color = p_colors[i - 1]  # 沒滿級使用專屬顏色

            # --- 存入字典 ---
            upgrade_hub_layout[key] = {"title": display_text, "color": display_color}


update_upgrade_hub_layout()

now_player_skin = tool.Colors.RED
current_player_color_name = "red"

levels_unlocked = 1  # 這裡你可以根據玩家進度調整解鎖的關卡數量


def get_save_data():
    # 將所有遊戲變數打包成一個字典
    return {
        "balance": total_points,
        # 🔥 直接儲存 current_levels 字典 (裡面已經是 upgrade_p1: 5 的格式)
        "upgrades": current_levels,
        "records": longest_survived_time,
        "player_skins": player_skins,
        "now_player_skin": now_player_skin,
        "current_skin_name": current_player_color_name,
        "gm_i": gm_i,
        "has_buy_crazy": has_buy_crazy,
        "levels_unlocked": levels_unlocked,
    }


saved = False


def save_data():
    try:
        # 準備要寫入的資料
        data = get_save_data()

        with current_active_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # print("💾 存檔成功！")

    except Exception as e:
        print(f"❌ 存檔失敗: {e}")


loaded = False


def load_data(file_path=None):
    # 宣告 global 變數 (注意這裡加入了 current_levels，移除了 p1_i 等舊變數)
    global total_points, target_points, current_levels, longest_survived_time, player_skins, now_player_skin
    global current_player_color_name, game_state, gm_i, has_buy_crazy, levels_unlocked
    global current_active_path

    try:
        target_path = file_path if file_path else SAVE_PATH
        current_active_path = target_path
        if target_path and target_path.exists():
            with target_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            print("❌ 沒有找到存檔檔案")

        # --- 安全檢查：如果還殘留舊格式，強制跳錯讓玩家修復 ---
        # 檢查 upgrades 內部是否有舊的鍵值 (如 "speed")
        up_check = data.get("upgrades", {})
        longest_survived_time = data.get("records", longest_survived_time)
        if "points_sum" in data or "speed" in up_check or "level1" not in longest_survived_time:
            print("⚠️ 偵測到舊版存檔，進入修復模式。")
            game_state = "save_game_error"
            return

        # 1. 讀取金錢
        total_points = data.get("balance", 0)
        target_points = total_points

        # 2. 讀取升級數據 (核心修改)
        # 直接讀取 "upgrade_p1" 對應的值，並存入 current_levels
        saved_ups = data.get("upgrades", {})
        for i in range(1, len(UPGRADE_CONFIG) + 1):
            key = f"upgrade_p{i}"
            # 如果存檔裡有這個等級就讀取，沒有就預設 0
            current_levels[key] = saved_ups.get(key, 0)

        # 3. 讀取其他資料 (保持不變)
        longest_survived_time = data.get("records", longest_survived_time)
        load_player_skin = data.get("player_skins", player_skins)
        now_player_skin = data.get("now_player_skin", now_player_skin)
        current_player_color_name = data.get("current_skin_name", "red")
        gm_i = data.get("gm_i", 1)
        has_buy_crazy = data.get("has_buy_crazy", False)
        for name, skin in player_skins.items():
            skin["has_bought"] = load_player_skin[name]["has_bought"]
        levels_unlocked = data.get("levels_unlocked", 1)

        print(f"✔️ 載入成功！當前等級: {current_levels}")

    except Exception as e:
        print(f"❌ 載入失敗: {e}")
        # 出錯時初始化為 0
        for i in range(1, 9):
            current_levels[f"upgrade_p{i}"] = 0


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

    # 1. 取得原始資料 (可能是單個值，也可能是列表，或者 None)
    raw_effects = skin_info.get("effect", "none")
    raw_powers = skin_info.get("power", 1)

    # 2. 統一轉成列表 (List) 以便迴圈處理
    # 如果原本就是 list (多重效果)，就保持原樣
    # 如果是單個字串/數字，就把它包進 list 變成 [值]
    if isinstance(raw_effects, list):
        effects = raw_effects
        powers = raw_powers
    else:
        effects = [raw_effects]
        powers = [raw_powers]

    for effect, power in zip(effects, powers, strict=False):
        if effect == "speed":
            player_speed_buff *= power
        elif effect == "points_multiplier":
            points_multiplier *= power
        elif effect == "coin_multiplier":
            coin_multiplier *= power
        elif effect == "points_coin_multiplier":
            points_multiplier *= power
            coin_multiplier *= power
        elif effect == "max_hp":
            player_max_hp_buff *= power
        elif effect == "enemy_damage":
            skin_enemy_damage_buff *= power
        elif effect == "enemy_spawn_speed":
            buffer_duration_buff *= power
        elif effect == "invincible_time":
            invincible_time_buff *= power
        elif effect == "player_size":
            player_size_buff *= power
        # 格式
        # elif effect == "":
        #     pass


def load_resets():
    global \
        level_button_color, \
        next_spawn_range, \
        mode_speed_buff, \
        gm_points_buff, \
        game_mode, \
        g_m, \
        gm_i, \
        spawn_time_debuff, \
        now_p1_skill, \
        now_p2_skill, \
        now_p3_skill, \
        now_p4_skill, \
        now_p5_skill, \
        now_p6_skill, \
        now_p7_skill, \
        now_p8_skill, \
        enemy_damage_buff, \
        levels_unlocked

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


color_map = {
    "RED_2": tool.Colors.RED_2,
    "ORANGE": tool.Colors.ORANGE,
    "ORANGE_2": tool.Colors.ORANGE_2,
    "YELLOW": tool.Colors.YELLOW,
    "GREEN": tool.Colors.GREEN,
    "DARK_GREEN": tool.Colors.DARK_GREEN,
    "CYAN": tool.Colors.CYAN,
    "BLUE": tool.Colors.BLUE,
    "BLUE_2": tool.Colors.BLUE_2,
    "PURPLE": tool.Colors.PURPLE,
    "PINK": tool.Colors.PINK,
    "WHITE": tool.Colors.WHITE,
    "GRAY": tool.Colors.GRAY,
    "BLACK": tool.Colors.BLACK,
}


def make_enemy_list(level):

    json_path = ENEMY_PATH / f"level{level}.json"

    # 定義一個幫忙產生敵人的小工具 (寫在 reset_game 裡面或外面都可以)
    def make_enemy(show_time, speed, slow_speed, color, angle_range=(10, 80), size=10, damage=10, type="normal"):
        return {
            "x": random.randint(50, WIDTH - 50),
            "y": random.randint(20, HEIGHT - 20),
            "angle": random.randint(*angle_range),
            "current_speed": speed,
            "normal_speed": speed,
            "slow_speed": slow_speed,
            "x_dir": random.choice([-1, 1]),
            "y_dir": random.choice([-1, 1]),
            "last_change_time": 0,
            "color": color,
            "show": False,
            "show_time": show_time,
            "mode": "waiting",
            "width": int(size * 3),
            "height": int(size * 1.5),
            "damage": damage,  # 可以根據需要調整傷害值
            "type": type,  # 預設類型為 normal，後面可以根據顏色或其他條件改成 "fast"、"slow"、"boss" 等等
        }

    # 檢查檔案是否存在，如果不存在就給一個預設的怪物
    if not json_path.exists():
        print(f"找不到關卡檔案: {json_path}")
        return [make_enemy(-10, 3, 1, tool.Colors.WHITE)]

    with open(str(ENEMY_PATH / f"level{level}.json"), encoding="utf-8") as f:
        data = json.load(f)

    enemy_list = []
    for e in data["enemies"]:
        print(f"DEBUG: {e}")
        # 處理選擇性的 angle_range
        a_range = tuple(e.get("angle_range", (10, 80)))

        # 呼叫你的原始函式
        enemy_data = make_enemy(
            show_time=e["show_time"],
            speed=e["speed"],
            slow_speed=e["slow_speed"],
            color=color_map.get(e["color"], tool.Colors.WHITE),  # 沒抓到就給白色
            angle_range=a_range,
            size=e.get("size", 10),
            damage=e.get("damage", 10),
            type=e.get("type", "normal"),
        )
        enemy_list.append(enemy_data)
        print(f"Enemy size: {e.get('size')}")
    return enemy_list


def reset_game():
    global \
        player_rect, \
        player_size, \
        player_color, \
        player_speed, \
        current_player_speed, \
        treasures, \
        treasure_points, \
        next_spawn_range, \
        points, \
        mode_speed_buff, \
        gm_points_buff, \
        maybe_cheat, \
        from_pause, \
        levels_button_color, \
        levels_button_text, \
        levels_button_text_color, \
        level_button_color, \
        last_hit_time, \
        player_hp, \
        player_max_hp, \
        countdown_text, \
        countdown, \
        passed_time, \
        coin_chance, \
        now_treasure, \
        treasure_config, \
        last_cure_time, \
        has_plus_points, \
        has_save_survived_time, \
        countdowning, \
        trying_to_touch_player, \
        invincible_duration, \
        now_p8_skill, \
        clicked_key, \
        afk_timer, \
        last_player_pos, \
        AFK_LIMIT, \
        change_dir_timer, \
        lv_flash_timer

    load_resets()
    apply_skin_effects()

    lv_flash_timer = 0

    clicked_key = None

    invincible_duration = now_p8_skill / 1000

    # 玩家設定
    player_size = now_p4_skill * player_size_buff
    player_color, player_speed, current_player_speed = (
        now_player_skin,
        (5 + now_p1_skill) * player_speed_buff,
        (5 + now_p1_skill) * player_speed_buff,
    )
    player_rect = pygame.Rect(
        WIDTH // 2 - player_size // 2,
        HEIGHT // 2 - player_size // 2,
        player_size,
        player_size,
    )

    tool.reset_timer()
    passed_time = tool.sec_timer(True)
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

    levels_button_color = tool.Colors.DARK_GREEN
    levels_button_text = "START"
    levels_button_text_color = tool.Colors.WHITE

    player_max_hp = int(now_p6_skill * player_max_hp_buff)
    player_hp = player_max_hp

    change_dir_timer = 2  # 設定為兩秒

    treasure_points = 0

    # 1. 定義寶藏的配置表格 (稀有度, 顏色, 機率, 分數範圍)
    treasure_config = [
        ("Common", tool.Colors.WHITE, int(150 // (now_p11_skill * 3)), (2, 5)),
        ("Uncommon", tool.Colors.GREEN, int(140 // (now_p11_skill * 2)), (5, 9)),
        ("Rare", tool.Colors.BLUE, int(80 // now_p11_skill), (8, 12)),
        ("Epic", tool.Colors.PURPLE, int(60 * now_p11_skill), (11, 15)),
        ("Legendary", tool.Colors.ORANGE, int(40 * now_p11_skill), (15, 18)),
        ("Mythic", tool.Colors.RED, int(24 * now_p11_skill * 2), (17, 20)),
        ("Exotic", tool.Colors.CYAN, int(8 * now_p11_skill * 2), (20, 23)),
        ("Divine", tool.Colors.GOLD, int(1 * now_p11_skill * 3), (23, 27)),
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

    now_treasure = treasures[0]

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


reset_game()

selected_level = "level1"


def player_move():
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


def coin_rect():
    global total_points, target_points, WIDTH
    diff = total_points - target_points

    if abs(diff) < 0.1:
        target_points = total_points
    else:
        target_points += diff * 0.1
    final_text = "$" + tool.num_to_KMBT(target_points)
    # 把背景調成一個有釘釘子的木塊
    tool.text_button(
        final_text,
        tool.Colors.BLACK,
        tool.Colors.GOLD,
        WIDTH - 110,
        20,
        100,
        40,
        size=22,
        font_type="",
    )


# 1. 先找出所有符合格式的存檔
all_saves = sorted(BASE_DIR.glob("save_game*.json"))

# 2. 定義「真正要讀取的檔案」邏輯
if (BASE_DIR / "save_game.json").exists():
    # A 方案：如果有預設檔，就用預設檔
    active_save = BASE_DIR / "save_game.json"
elif all_saves:
    # B 方案：沒預設檔但有其他存檔，抓第一個 (all_saves[0])
    active_save = all_saves[0]
else:
    # C 方案：什麼都沒有，準備開新檔案
    active_save = BASE_DIR / "save_game.json"

# 3. 執行載入
# 這裡呼叫你寫好的 load_data，並傳入我們選好的路徑
load_data(file_path=active_save)

load_resets()

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

while running:
    screen_text = f"Escape Them! v1.0.0 - {game_state.replace('_', ' ')}"
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    mouse_pos = pygame.mouse.get_pos(False)  # 取得滑鼠座標

    # 主畫面
    if game_state == "menu":
        screen.fill(tool.Colors.BROWN)
        coin_rect()
        # 事件偵測
        if levels_button.collidepoint(mouse_pos):
            levels_button_color = tool.Colors.GOLD
            levels_button_text_color = tool.Colors.BLACK
            levels_button_text = "Press Me!"
        else:
            levels_button_color = tool.Colors.DARK_GREEN
            levels_button_text_color = tool.Colors.WHITE
            levels_button_text = "Levels Select"
        if settings_button.collidepoint(mouse_pos):
            settings_button_color = tool.Colors.GREEN
            settings_button_text_color = tool.Colors.BLACK
        else:
            settings_button_color = tool.Colors.BLUE_2
            settings_button_text_color = tool.Colors.WHITE
        if upgrade_button.collidepoint(mouse_pos):
            upgrade_button_color = tool.Colors.ORANGE
        else:
            upgrade_button_color = tool.Colors.YELLOW
        # if help_button.collidepoint(mouse_pos):
        #     help_button_color = tool.Colors.PINK
        # else:
        #     help_button_color = tool.Colors.PURPLE

        if title_img_loaded:
            screen.blit(title_img_surface, title_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, title_rect)

        if left_img_loaded:  # --|
            screen.blit(left_img_surface, left_rect)  # --|
        else:  # --|
            pygame.draw.rect(screen, tool.Colors.RED, left_rect)  # --|
        tool.show_text("settings", tool.Colors.WHITE, 40, 70, size=24, font_type="")
        if right_img_loaded:  # --|
            screen.blit(right_img_surface, right_rect)  # --|
        else:  # --|
            pygame.draw.rect(screen, tool.Colors.RED, right_rect)  # --|
        tool.show_text("upgrades", tool.Colors.WHITE, WIDTH - 120, 70, size=24, font_type="")

        levels_button = tool.text_button(
            levels_button_text,
            levels_button_text_color,
            levels_button_color,
            0,
            220,
            300,
            70,
            b_center=True,
        )
        settings_button = tool.text_button(
            "Settings",
            settings_button_text_color,
            settings_button_color,
            WIDTH // 2 - 150,
            310,
            140,
            70,
        )
        upgrade_button = tool.text_button(
            "Upgrades",
            tool.Colors.BLACK,
            upgrade_button_color,
            WIDTH // 2 + 10,
            310,
            140,
            70,
        )
        help_button = tool.text_button("Help", tool.Colors.WHITE, tool.Colors.GRAY, 0, 400, 300, 70, b_center=True)
        # 做好時再改成紫色
        exit_button = tool.text_button("Leave", tool.Colors.WHITE, tool.Colors.RED, 0, 490, 300, 70, b_center=True)
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            # --- 第一階段：滑鼠按下 (DOWN) ---
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if levels_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if settings_button.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if upgrade_button.collidepoint(mouse_pos):
                    is_pressing[2] = True
                if exit_button.collidepoint(mouse_pos):
                    is_pressing[3] = True
                if left_rect.collidepoint(mouse_pos):
                    is_pressing[4] = True
                if right_rect.collidepoint(mouse_pos):
                    is_pressing[5] = True

            # --- 第二階段：滑鼠放開 (UP) ---
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 只有當先前「有在按鈕內按下」且「現在也在按鈕內放開」才觸發
                if levels_button.collidepoint(mouse_pos) and is_pressing[0]:
                    # reset_game()
                    game_state = "level_select"
                if settings_button.collidepoint(mouse_pos) and is_pressing[1]:
                    game_state = "setting_p1"
                if upgrade_button.collidepoint(mouse_pos) and is_pressing[2]:
                    game_state = "upgrade_hub"
                if exit_button.collidepoint(mouse_pos) and is_pressing[3]:
                    running = False
                if left_rect.collidepoint(mouse_pos) and is_pressing[4]:
                    game_state = "setting_p1"
                if right_rect.collidepoint(mouse_pos) and is_pressing[5]:
                    game_state = "upgrade_hub"
                # 重置所有按鈕的按下狀態，確保下次點擊重新計算
                reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    running = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            game_state = "setting_p1"
        if keys[pygame.K_LEFT] or keys[pygame.K_d]:
            game_state = "upgrade_p1"
    # 難易度與最長存活時間    在這裡selected_level很重要
    elif game_state == "setting_p1":
        screen.fill(tool.Colors.DARK_GRAY)
        coin_rect()
        tool.show_text(
            "Difficulty And Longest Servided Time",
            tool.Colors.WHITE,
            0,
            80,
            size=34,
            screen_center=True,
        )
        tool.show_text("Now Level:", tool.Colors.WHITE, 0, 130, size=30, screen_center=True)
        lv_text = selected_level.replace("level", "Lv. ")
        lv_button = tool.text_button(lv_text, tool.Colors.BLACK, tool.Colors.BLUE, 0, 150, 180, b_center=True)
        if from_pause:
            back_button_text = "back to pause"
        else:
            back_button_text = "back to menu"
        back_button = tool.text_button(
            back_button_text,
            tool.Colors.WHITE,
            tool.Colors.ORANGE,
            0,
            520,
            200,
            60,
            b_center=True,
        )
        # 底色矩形
        # --- 難易度選擇框統一使用 tool.CR(pygame.Rect) 格式 ---
        easy_rect = tool.CR(pygame.Rect(70, 210, 450, 50), tool.Colors.GREEN, show=(game_mode == "easy"))
        easy_rect.draw(screen)
        normal_rect = tool.CR(
            pygame.Rect(70, 270, 450, 50),
            tool.Colors.YELLOW,
            show=(game_mode == "normal"),
        )
        normal_rect.draw(screen)
        hard_rect = tool.CR(
            pygame.Rect(70, 330, 450, 50),
            tool.Colors.ORANGE,
            show=(game_mode == "hard"),
        )
        hard_rect.draw(screen)
        super_hard_rect = tool.CR(
            pygame.Rect(70, 390, 450, 50),
            tool.Colors.RED,
            show=(game_mode == "super_hard"),
        )
        super_hard_rect.draw(screen)
        crazy_rect = tool.CR(
            pygame.Rect(70, 450, 450, 50),
            tool.Colors.PURPLE,
            show=(game_mode == "crazy"),
        )
        crazy_rect.draw(screen)

        easy_info_btn = tool.text_button("info", tool.Colors.WHITE, tool.Colors.DARK_GRAY, 540, 210, 60, 50)
        normal_info_btn = tool.text_button("info", tool.Colors.WHITE, tool.Colors.DARK_GRAY, 540, 270, 60, 50)
        hard_info_btn = tool.text_button("info", tool.Colors.WHITE, tool.Colors.DARK_GRAY, 540, 330, 60, 50)
        super_hard_info_btn = tool.text_button("info", tool.Colors.WHITE, tool.Colors.DARK_GRAY, 540, 390, 60, 50)
        crazy_info_btn = tool.text_button("info", tool.Colors.WHITE, tool.Colors.DARK_GRAY, 540, 450, 60, 50)
        # 顯示最長存活時間
        now_level_survived_time = longest_survived_time.get(selected_level, {})
        easy_time = now_level_survived_time.get("easy", 0)
        normal_time = now_level_survived_time.get("normal", 0)
        hard_time = now_level_survived_time.get("hard", 0)
        super_hard_time = now_level_survived_time.get("super_hard", 0)
        crazy_time = now_level_survived_time.get("crazy", 0)
        # print(f"DEBUG: now_level_survived_time = {now_level_survived_time}")
        tool.show_text(
            f"easy mode: {tool.show_time_min(easy_time)}",
            tool.Colors.BLACK,
            0,
            230,
            screen_center=True,
        )
        tool.show_text(
            f"normal mode: {tool.show_time_min(normal_time)}",
            tool.Colors.BLACK,
            0,
            290,
            screen_center=True,
        )
        tool.show_text(
            f"hard mode: {tool.show_time_min(hard_time)}",
            tool.Colors.BLACK,
            0,
            350,
            screen_center=True,
        )
        tool.show_text(
            f"super hard mode: {tool.show_time_min(super_hard_time)}",
            tool.Colors.BLACK,
            0,
            410,
            screen_center=True,
        )
        tool.show_text(
            f"crazy mode: {tool.show_time_min(crazy_time)}",
            tool.Colors.BLACK,
            0,
            470,
            screen_center=True,
        )
        easy_button = tool.text_button("select", tool.Colors.BLACK, tool.Colors.GREEN, 70, 210, 130, 50)
        normal_button = tool.text_button("select", tool.Colors.BLACK, tool.Colors.YELLOW, 70, 270, 130, 50)
        hard_button = tool.text_button("select", tool.Colors.BLACK, tool.Colors.ORANGE, 70, 330, 130, 50)
        super_hard_button = tool.text_button("select", tool.Colors.BLACK, tool.Colors.RED, 70, 390, 130, 50)
        crazy_button = tool.text_button(
            "select" if has_buy_crazy else crazy_btn_text,
            tool.Colors.BLACK,
            tool.Colors.PURPLE,
            70,
            450,
            130,
            50,
        )
        # --- 繪製箭頭 ---
        if right_img_loaded:
            screen.blit(right_img_surface, right_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, right_rect)
        if lock_img_loaded and not has_buy_crazy and not crazy_button.collidepoint(mouse_pos):
            screen.blit(lock_img_surface, (90, 430))
        if crazy_button.collidepoint(mouse_pos):
            crazy_btn_text = "$10000"
        else:
            crazy_btn_text = ""
        if maybe_cheat:
            level_button_color = tool.Colors.GRAY
        else:
            if game_mode == "easy":
                level_button_color = tool.Colors.GREEN
            elif game_mode == "normal":
                level_button_color = tool.Colors.YELLOW
            elif game_mode == "hard":
                level_button_color = tool.Colors.ORANGE
            elif game_mode == "super_hard":
                level_button_color = tool.Colors.RED
            elif game_mode == "crazy":
                level_button_color = tool.Colors.PURPLE
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if lv_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if back_button.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if right_rect.collidepoint(mouse_pos):
                    is_pressing[2] = True
                if easy_button.collidepoint(mouse_pos) or easy_rect.rect.collidepoint(mouse_pos):
                    is_pressing[3] = True
                if normal_button.collidepoint(mouse_pos) or normal_rect.rect.collidepoint(mouse_pos):
                    is_pressing[4] = True
                if hard_button.collidepoint(mouse_pos) or hard_rect.rect.collidepoint(mouse_pos):
                    is_pressing[5] = True
                if super_hard_button.collidepoint(mouse_pos) or super_hard_rect.rect.collidepoint(mouse_pos):
                    is_pressing[6] = True
                if crazy_button.collidepoint(mouse_pos) or crazy_rect.rect.collidepoint(mouse_pos):
                    is_pressing[7] = True
                if easy_info_btn.collidepoint(mouse_pos):
                    is_pressing[8] = True
                if normal_info_btn.collidepoint(mouse_pos):
                    is_pressing[9] = True
                if hard_info_btn.collidepoint(mouse_pos):
                    is_pressing[10] = True
                if super_hard_info_btn.collidepoint(mouse_pos):
                    is_pressing[11] = True
                if crazy_info_btn.collidepoint(mouse_pos):
                    is_pressing[12] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if lv_button.collidepoint(mouse_pos) and not from_pause and is_pressing[0]:
                    # 1. 索引加 1
                    lv_i += 1

                    # 2. 循環邏輯 (0 -> 1 -> 2 -> 3 -> 4 -> 0)
                    lv_i %= len(all_levels)

                    # 3. 更新當前選中的關卡字串
                    selected_level = all_levels[lv_i]
                if back_button.collidepoint(mouse_pos) and is_pressing[1]:
                    if from_pause:
                        game_state = "pause"
                    else:
                        game_state = "menu"
                if right_rect.collidepoint(mouse_pos) and is_pressing[2]:
                    game_state = "setting_p2"
                if (easy_button.collidepoint(mouse_pos) or easy_rect.rect.collidepoint(mouse_pos)) and not maybe_cheat and is_pressing[3]:
                    gm_i = 0
                    game_mode = "easy"
                if (normal_button.collidepoint(mouse_pos) or normal_rect.rect.collidepoint(mouse_pos)) and not maybe_cheat and is_pressing[4]:
                    gm_i = 1
                    game_mode = "normal"
                if (hard_button.collidepoint(mouse_pos) or hard_rect.rect.collidepoint(mouse_pos)) and not maybe_cheat and is_pressing[5]:
                    gm_i = 2
                    game_mode = "hard"
                if (super_hard_button.collidepoint(mouse_pos) or super_hard_rect.rect.collidepoint(mouse_pos)) and not maybe_cheat and is_pressing[6]:
                    gm_i = 3
                    game_mode = "super_hard"
                if (crazy_button.collidepoint(mouse_pos) or crazy_rect.rect.collidepoint(mouse_pos)) and not maybe_cheat and is_pressing[7]:
                    if has_buy_crazy:
                        gm_i = 4
                        game_mode = "crazy"
                    elif total_points >= 10000:
                        has_buy_crazy = True
                        total_points -= 10000
                if easy_info_btn.collidepoint(mouse_pos) and is_pressing[8]:
                    game_state = "more_survived_time"
                    target_y = 0 * one_mode_height
                if normal_info_btn.collidepoint(mouse_pos) and is_pressing[9]:
                    game_state = "more_survived_time"
                    target_y = 1 * one_mode_height + 30
                if hard_info_btn.collidepoint(mouse_pos) and is_pressing[10]:
                    game_state = "more_survived_time"
                    target_y = 2 * one_mode_height + 30
                if super_hard_info_btn.collidepoint(mouse_pos) and is_pressing[11]:
                    game_state = "more_survived_time"
                    target_y = 3 * one_mode_height + 30
                if crazy_info_btn.collidepoint(mouse_pos) and is_pressing[12]:
                    game_state = "more_survived_time"
                    target_y = 4 * one_mode_height + 30
                reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    game_state = "setting_p2"
            if event.type == pygame.MOUSEWHEEL:
                # 1. 索引加 1
                lv_i += 1 if event.y < 0 else -1

                # 2. 循環邏輯 (0 -> 1 -> 2 -> 3 -> 4 -> 0)
                lv_i %= len(all_levels)

                # 3. 更新當前選中的關卡字串
                selected_level = all_levels[lv_i]
    # 每關最長存活時間
    elif game_state == "more_survived_time":
        screen.fill(tool.Colors.DARK_GRAY)
        coin_rect()
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                target_y -= event.y * 30
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    game_state = "setting_p1"
                    reset_pressing()
        scroll_y = tool.num_range(0, scroll_y, max_scroll_y)  # 強制修正回合法範圍
        if scroll_y != target_y or not tool.in_range(0, scroll_y, max_scroll_y):
            scroll_y += (target_y - scroll_y) * 0.1  # 每次移動剩下的 10%
        draw_y = 110
        for gm in modes_config:
            tool.text_button(
                f"{gm[0].title()} Mode",
                tool.Colors.BLACK if gm[0] == "easy" or gm[0] == "normal" else tool.Colors.WHITE,
                gm[1],
                0,
                draw_y - scroll_y,
                270,
                60,
                size=34,
                b_center=True,
            )
            draw_y += 90
            for level in all_levels:
                tool.show_text(f"Level {level.replace('level', '')}: {tool.show_time_min(longest_survived_time[level][gm[0]])}", tool.Colors.WHITE, 0, draw_y - scroll_y, screen_center=True)
                draw_y += 60
            draw_y -= 25

        max_scroll_y = max(0, draw_y - HEIGHT + 50)  # 計算最大可捲動範圍

        tool.text_button(
            "All Levels Survived Time",
            tool.Colors.WHITE,
            tool.Colors.DARK_GRAY,
            0,
            0,
            WIDTH,
            70,
            size=34,
            b_center=True,
        )
        pygame.draw.rect(screen, tool.Colors.DARK_GRAY, (0, HEIGHT - 70, WIDTH, 70))
        back_button = tool.text_button("Back to Settings", tool.Colors.WHITE, tool.Colors.ORANGE, 0, HEIGHT - 65, 270, 60, size=28, b_center=True)
        # pygame.draw.line(screen, tool.Colors.RED, (0, draw_y - scroll_y), (WIDTH, draw_y - scroll_y), 5)
    # 存檔專區
    elif game_state == "setting_p2":
        screen.fill(tool.Colors.DARK_GRAY)
        coin_rect()
        tool.show_text("Save and Load", tool.Colors.WHITE, 0, 80, size=50, screen_center=True)
        tool.show_text(
            "We will save this file while you leave",
            tool.Colors.WHITE,
            0,
            140,
            size=24,
            screen_center=True,
        )
        save_button = tool.text_button(
            "Save File",
            tool.Colors.BLACK,
            tool.Colors.PINK,
            0,
            210,
            200,
            60,
            b_center=True,
        )
        load_button = tool.text_button(
            "Load File",
            tool.Colors.WHITE,
            tool.Colors.BLUE_2,
            0,
            290,
            200,
            60,
            b_center=True,
        )
        open_other_button = tool.text_button(
            "Open Other Save",
            tool.Colors.WHITE,
            tool.Colors.BLACK,
            0,
            370,
            230,
            60,
            b_center=True,
        )
        if from_pause:
            back_button_text = "back to pause"
        else:
            back_button_text = "back to menu"
        back_button = tool.text_button(
            back_button_text,
            tool.Colors.WHITE,
            tool.Colors.ORANGE,
            0,
            490,
            200,
            60,
            b_center=True,
        )
        # --- 繪製箭頭 ---
        if left_img_loaded:
            screen.blit(left_img_surface, left_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, left_rect)
        if right_img_loaded:
            screen.blit(right_img_surface, right_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, right_rect)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if save_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if load_button.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if open_other_button.collidepoint(mouse_pos):
                    is_pressing[2] = True
                if back_button.collidepoint(mouse_pos):
                    is_pressing[3] = True
                if left_rect.collidepoint(mouse_pos):
                    is_pressing[4] = True
                if right_rect.collidepoint(mouse_pos):
                    is_pressing[5] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if save_button.collidepoint(mouse_pos) and is_pressing[0]:
                    saved = False
                    game_state = "saving_file"
                if load_button.collidepoint(mouse_pos) and is_pressing[1]:
                    loaded = False
                    game_state = "loading_file"
                if open_other_button.collidepoint(mouse_pos) and is_pressing[2]:
                    game_state = "choose_file"
                if back_button.collidepoint(mouse_pos) and is_pressing[3]:
                    if from_pause:
                        game_state = "pause"
                    else:
                        game_state = "menu"
                if left_rect.collidepoint(mouse_pos) and is_pressing[4]:
                    game_state = "setting_p1"
                if right_rect.collidepoint(mouse_pos) and is_pressing[5]:
                    game_state = "setting_p3"
                reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    game_state = "setting_p1"
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    game_state = "setting_p3"
    # 選擇其他存檔
    elif game_state == "choose_file":
        screen.fill(tool.Colors.DARK_GRAY)
        coin_rect()
        # 列出所有存檔
        save_buttons = []
        for i, save in enumerate(save_files):
            btn = tool.text_button(save.stem, tool.Colors.WHITE, tool.Colors.BLUE_2, 0, 150 + i * 70 - scroll_y, 300, 60, b_center=True)
            save_buttons.append((btn, save))
        pygame.draw.rect(screen, tool.Colors.DARK_GRAY, (0, HEIGHT - 110, WIDTH, 110))  # 擋住捲動後的檔案
        back_button = tool.text_button(
            "Back to Settings",
            tool.Colors.WHITE,
            tool.Colors.ORANGE,
            0,
            510,
            240,
            60,
            b_center=True,
        )
        pygame.draw.rect(screen, tool.Colors.DARK_GRAY, (0, 0, WIDTH, 110))
        tool.show_text("Choose Save File", tool.Colors.WHITE, 0, 80, size=50, screen_center=True)
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                # 滑鼠滾輪向上滾動 (event.y > 0) 就往下移動列表 (scroll_y 增加)，反之則往上移動
                scroll_y -= event.y * 30
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True

                # 遍歷存檔按鈕，如果按下，記錄是哪個存檔
                for btn, save in save_buttons:
                    if btn.collidepoint(mouse_pos):
                        selected_save_name = save  # 存下檔名
                        is_pressing[1] = True  # 標記有人被按下

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 回上一頁邏輯
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    game_state = "setting_p2"

                # 處理存檔載入
                elif is_pressing[1] and selected_save_name:
                    # 檢查滑鼠是否還在對應的按鈕上 (避免按下去後滑開又觸發)
                    for btn, save in save_buttons:
                        if save == selected_save_name and btn.collidepoint(mouse_pos):
                            # 1. 確保它是 Path 物件，如果 save 本身已經是 Path 就不用包 Path()
                            # 但建議統一轉換成絕對路徑，最保險的做法是：
                            target_path = BASE_DIR / selected_save_name if isinstance(selected_save_name, str) else selected_save_name

                            print(f"載入存檔: {target_path}")
                            load_data(target_path)  # 傳入 Path 物件
                            load_resets()  # 重置遊戲狀態
                            game_state = "menu"  # 切換回選單

                selected_save_name = None  # 重置
                reset_pressing()
        max_scroll_y = max(0, 150 + len(save_files) * 70 - HEIGHT + 110)  # 根據存檔數量計算最大捲動高度
        scroll_y = tool.num_range(0, scroll_y, max_scroll_y)  # 強制修正回合法範圍
    # 玩家皮膚購買與更換
    elif game_state == "setting_p3":
        screen.fill(tool.Colors.DARK_GRAY)
        coin_rect()
        tool.show_text("Player Skins", tool.Colors.WHITE, 0, 80, size=50, screen_center=True)
        display_points = tool.num_to_KMBT(round(total_points, 1))
        tool.show_text(
            f"Coins:{display_points}$",
            tool.Colors.WHITE,
            10,
            120,
            size=28,
            screen_center=True,
        )
        if from_pause:
            back_button_text = "back to pause"
        else:
            back_button_text = "back to menu"
        back_button = tool.text_button(
            back_button_text,
            tool.Colors.WHITE,
            tool.Colors.ORANGE,
            0,
            490,
            200,
            60,
            b_center=True,
        )
        if left_img_loaded:
            screen.blit(left_img_surface, left_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, left_rect)
        # 遍歷 unlocked_locks 字典
        for t, info in skin_unlocked_locks.items():
            # 從 player_skins 抓取對應的資料
            skin_val = player_skins[t]

            # 建立碰撞偵測用的矩形
            btn_rect = pygame.Rect(info["x"], info["y"], 100, 50)

            # 邏輯判斷：決定按鈕文字
            display_text = t
            if btn_rect.collidepoint(mouse_pos) and not skin_val["has_bought"] and not from_pause:
                display_text = f"${skin_val['value']}"  # 顯示價錢
                info["show"] = False  # 滑鼠碰到時，隱藏鎖頭
            else:
                # 平時：如果沒買過，鎖頭就要顯示
                info["show"] = not skin_val["has_bought"]

            # 繪製按鈕，並將回傳的 Rect 存入 info["rect"] 給點擊事件用
            info["rect"] = tool.text_button(
                display_text,
                info["text_col"],
                skin_val["color"],
                info["x"],
                info["y"],
                100,
                50,
                size=25,
            )
        if from_pause:
            for _, info in skin_unlocked_locks.items():
                info["show"] = True

        tool.show_text("VIP Skins", tool.Colors.GOLD, 0, 400, screen_center=True)

        # 最後統一畫出所有鎖頭 (要在按鈕畫完之後才畫，才會蓋在上面)
        if lock_img_loaded:
            for info in skin_unlocked_locks.values():
                if info["show"]:
                    screen.blit(lock_img_surface, (info["x"] + 5, info["y"] - 20))

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if left_rect.collidepoint(mouse_pos):
                    is_pressing[1] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    if from_pause:
                        game_state = "pause"
                    else:
                        game_state = "menu"
                if left_rect.collidepoint(mouse_pos) and is_pressing[1]:
                    game_state = "setting_p2"
                # --- 新增：處理所有皮膚按鈕的點擊 ---
                for t, info in skin_unlocked_locks.items():
                    # 檢查滑鼠是否點擊到該皮膚的 Rect (剛才在繪製迴圈存好的)
                    if "rect" in info and info["rect"].collidepoint(mouse_pos) and not from_pause:
                        skin_val = player_skins[t]

                        # 情況 A：已經買過了 -> 直接切換皮膚顏色
                        if skin_val["has_bought"]:
                            now_player_skin = skin_val["color"]
                            current_player_color_name = t

                        # 情況 B：還沒買過 -> 判斷錢夠不夠購買
                        else:
                            if total_points >= skin_val["value"]:
                                total_points -= skin_val["value"]  # 扣錢
                                skin_val["has_bought"] = True  # 標記為已購買
                                now_player_skin = skin_val["color"]  # 買完直接換上
                                current_player_color_name = t  # <-- 這裡也要加，確保買完功能立刻生效
                            else:
                                # 如果錢不夠，可以加個音效或提示
                                print(f"錢不夠！需要 ${skin_val['value']}")
                reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    game_state = "setting_p2"
        tool.show_text("Demo:", tool.Colors.WHITE, WIDTH - 130, 350, size=22)
        show_rect = tool.CR(pygame.Rect(580, 380, 30, 30), now_player_skin)
        show_rect.draw(screen)

    # --------------------------遊戲資料儲存與匯入--------------------------------
    elif game_state == "saving_file":
        screen.fill(tool.Colors.PINK)
        cancal_button = tool.text_button(
            "Cancel",
            tool.Colors.WHITE,
            tool.Colors.RED_2,
            0,
            400,
            200,
            60,
            b_center=True,
            show=not saved,
        )
        # 確保有啟動計時器 (如果 collision_time 是 None)
        if tool.collision_time is None:
            tool.collision_time = pygame.time.get_ticks()
        current_time_sec = tool.sec_timer(update=True)
        passed_time = pygame.time.get_ticks() - tool.collision_time if tool.collision_time is not None else 0
        if passed_time < 4000:
            tool.show_text("Saving File...", tool.Colors.BLACK, 0, 150, 50, screen_center=True)
        elif 4000 <= passed_time < 7000:
            # 只在進入這個狀態的第一幀讀取一次檔案
            if not saved:
                save_data()
                saved = True
            tool.show_text("Successfully Saved!", tool.Colors.BLACK, 0, 150, 50, screen_center=True)
            tool.show_text(
                "File Name: save_game.json",
                tool.Colors.BLACK,
                0,
                200,
                50,
                screen_center=True,
            )
        elif passed_time > 7000:
            game_state = "setting_p2"
            tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
            tool.reset_timer()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cancal_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if cancal_button.collidepoint(mouse_pos) and is_pressing[0]:
                    game_state = "setting_p2"
                    tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool.reset_timer()
    elif game_state == "loading_file":
        screen.fill(tool.Colors.BLUE)
        cancal_button = tool.text_button(
            "Cancel",
            tool.Colors.WHITE,
            tool.Colors.RED_2,
            0,
            400,
            200,
            60,
            b_center=True,
            show=not loaded,
        )
        # 確保有啟動計時器 (如果 collision_time 是 None)
        if tool.collision_time is None:
            tool.collision_time = pygame.time.get_ticks()
        current_time_sec = tool.sec_timer(update=True)
        passed_time = pygame.time.get_ticks() - tool.collision_time if tool.collision_time is not None else 0

        if passed_time < 3000:
            tool.show_text("Loading File...", tool.Colors.BLACK, 0, 150, 50, screen_center=True)
        elif 3000 <= passed_time < 6000:
            if not loaded:
                # 只在進入這個狀態的第一幀讀取一次檔案
                loaded_data_success = load_data()
                reset_game()
                loaded = True
            tool.show_text(
                "Successfuly Loaded File" if loaded_data_success else "No Save File Found, Starting New Game.",
                tool.Colors.BLACK,
                0,
                150,
                50,
                screen_center=True,
            )
        elif passed_time >= 6000:  # 過了 5000 毫秒 (5秒)
            game_state = "settings_p"
            tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
            tool.reset_timer()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cancal_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if cancal_button.collidepoint(mouse_pos) and is_pressing[0]:
                    reset_game()
                    tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool.reset_timer()
                    if not from_pause:
                        game_state = "settings_p"
                    else:
                        game_state = "menu"
    # ----------------------------------------------------------------------------
    # 玩家升級：
    # 升級列表
    elif game_state == "upgrade_hub":
        screen.fill(tool.Colors.DARK_GREEN)
        update_upgrade_hub_layout()

        # [簡化] 統一處理事件 (捲動與返回)
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                scroll_y -= event.y * 40
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 這裡我們不處理列表點擊，只處理固定的返回按鈕
                if back_button.collidepoint(mouse_pos):
                    game_state = "menu"
                    scroll_y = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            scroll_y -= 20
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            scroll_y += 20

        # 限制捲動範圍
        scroll_y = max(0, min(scroll_y, len(upgrade_hub_layout) * 100 - 350))

        # [簡化] 用一個迴圈搞定繪製與點擊感
        for i, (key, info) in enumerate(upgrade_hub_layout.items()):
            y = 130 + i * 100 - scroll_y

            if -80 < y < HEIGHT:
                # 繪製按鈕
                rect = tool.text_button(
                    info["title"],
                    tool.Colors.BLACK,
                    info["color"],
                    0,
                    y,
                    500,
                    80,
                    size=26,
                    b_center=True,
                )

                # [核心簡化] 使用 mouse.get_pressed 仿造 is_pressing 效果
                mouse_click = pygame.mouse.get_pressed()[0]
                if rect.collidepoint(mouse_pos):
                    if mouse_click:
                        is_pressing[8] = True  # 在按鈕內按下
                    elif is_pressing[8]:  # 在按鈕內放開
                        # print(f"Switching to: {key}")
                        game_state = key
                        is_pressing[8] = False
                        reset_pressing()

        # 全域重置：如果滑鼠放開了，不管在哪裡都要重置 pressing
        if not pygame.mouse.get_pressed()[0]:
            is_pressing[8] = False

        # 固定底部的 BACK 按鈕
        pygame.draw.rect(screen, tool.Colors.DARK_GREEN, (0, HEIGHT - 80, WIDTH, 80))
        back_button = tool.text_button(
            "BACK TO MENU",
            tool.Colors.WHITE,
            tool.Colors.ORANGE,
            0,
            HEIGHT - 70,
            260,
            50,
            b_center=True,
        )
        tool.text_button(
            "Upgrade Center",
            tool.Colors.WHITE,
            tool.Colors.DARK_GREEN,
            0,
            0,
            500,
            100,
            size=50,
            b_center=True,
        )
        coin_rect()
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    game_state = "menu"
                    scroll_y = 0
            reset_pressing()
    # 這裡取代原本所有 upgrade_p1 ~ p8
    # ------------------------------------------------------------------
    # ✅ 通用升級頁面 (保留你的圖片、箭頭、按鈕樣式)
    # ------------------------------------------------------------------
    elif game_state in UPGRADE_CONFIG:
        # 1. 抓取當前頁面的數據
        cfg = UPGRADE_CONFIG[game_state]  # 取得靜態設定 (標題、價格表...)
        lvl = current_levels[game_state]  # 取得當前等級 (0, 1, 2...)
        costs = cfg["costs"]  # 價格表

        # 解析目前是第幾頁 (例如 "upgrade_p1" -> 1)
        current_p_num = int(game_state.replace("upgrade_p", ""))
        total_pages = len(UPGRADE_CONFIG)  # 總頁數

        # 2. 繪製背景與標題
        screen.fill(tool.Colors.DARK_GREEN)

        # 偽代碼方向
        current_lv_color = tool.Colors.WHITE  # 預設白色

        if lv_flash_timer > 0:
            lv_flash_timer -= 1
            # 如果剩下偶數幀，就換個顏色（例如黃色或金色）
            if lv_flash_timer % 10 > 8:
                current_lv_color = tool.Colors.YELLOW

        # --- 標題文字 ---
        tool.show_text(cfg["title"], tool.Colors.WHITE, 0, 240, size=50, screen_center=True)
        tool.show_text(
            f"Level: Lv.{lvl + 1}",
            current_lv_color,
            0,
            300,
            size=40,
            screen_center=True,
        )
        tool.show_text(
            f"Balance: {tool.num_to_KMBT(round(total_points, 1))}$",
            tool.Colors.WHITE,
            0,
            350,
            size=35,
            screen_center=True,
        )

        # --- 技能數值說明 ---
        # --- 🔥 萬能數值顯示邏輯 (開始) ---
        now_val = cfg["skills"][lvl]  # 取得當前等級數值

        # 準備顯示的字串變數
        display_text = ""

        # 1. 判斷是否為特殊格式 (字典 dict) -> 針對 Regen
        if isinstance(now_val, dict):
            hp = now_val.get("hp", 0)
            time = now_val.get("time", 10)

            if hp == 0:
                # Level 0 的顯示方式
                display_text = "No Regen"
            else:
                # Level 1+ 的顯示方式 (例如: +1 HP / 10s)
                display_text = f"+{hp} HP / {time}s"

        # 2. 判斷是否為普通數字 (int/float) -> 針對 Speed, Size...
        else:
            # 這裡我們配合設定檔裡的 skill_desc
            # 例如 Speed 的 skill_desc 是 "Speed +{}"，這裡只要給數字就好
            display_text = cfg["skill_desc"].format(now_val)

        # 3. 針對 Regen 的特殊補強
        # 因為 Regen 的 skill_desc 我們設成了 "{}"，所以上面的 else 跑不到格式化
        # 我們手動加上前綴，讓它跟其他屬性看起來比較像
        if "upgrade_p7" in UPGRADE_CONFIG and cfg == UPGRADE_CONFIG["upgrade_p7"]:
            display_text = f"Regen: {display_text}"

        # 4. 最後畫在螢幕上
        # 注意：這裡直接顯示 display_text，不要再 format 一次了
        tool.show_text(
            f"Effect: {display_text}",
            tool.Colors.WHITE,
            0,
            400,
            size=25,
            screen_center=True,
        )
        # --- 萬能數值顯示邏輯 (結束) ---

        # --- 保留你的圖片繪製邏輯 ---
        coin_rect()  # 繪製金幣圖示

        # 顯示標題圖片 (這裡假設你希望不同頁面顯示不同圖，或者共用一張)
        if title_img_loaded:
            screen.blit(title_img_surface, title_rect)

        # 3. 繪製左右箭頭 (邏輯簡化，樣式保留)
        # 左箭頭：不是第一頁才顯示
        if current_p_num > 1:
            if left_img_loaded:
                screen.blit(left_img_surface, left_rect)
            else:
                pygame.draw.rect(screen, tool.Colors.RED, left_rect)

        # 右箭頭：不是最後一頁才顯示
        if current_p_num < total_pages:
            if right_img_loaded:
                screen.blit(right_img_surface, right_rect)
            else:
                pygame.draw.rect(screen, tool.Colors.RED, right_rect)

        # 4. 購買按鈕邏輯 (計算價格與顏色)
        if lvl < len(costs):
            cost = costs[lvl]  # 取得當前等級價格

            # 判斷滑鼠是否懸停 & 錢夠不夠
            if upgrade_button.collidepoint(mouse_pos):
                if total_points >= cost:
                    btn_text = f"Buy! Left ${tool.num_to_KMBT(round(total_points - cost, 1))}"
                    btn_color = tool.Colors.GREEN
                else:
                    btn_text = f"Need: ${tool.num_to_KMBT(round(cost - total_points, 1))}"
                    btn_color = tool.Colors.RED
            else:
                btn_text = f"Cost: ${tool.num_to_KMBT(cost)}"
                btn_color = tool.Colors.YELLOW
        else:
            cost = None  # 滿級了
            btn_text = "MAX LEVEL"
            btn_color = tool.Colors.GRAY

        # 繪製按鈕 (Back 與 Upgrade) - 位置樣式不變
        if back_button.collidepoint(mouse_pos):
            back_btn_t_color, back_btn_color = tool.Colors.BLACK, tool.Colors.ORANGE_2
        else:
            back_btn_t_color, back_btn_color = tool.Colors.WHITE, tool.Colors.ORANGE

        upgrade_button = tool.text_button(btn_text, tool.Colors.BLACK, btn_color, 0, 430, 350, 60, b_center=True)
        back_button = tool.text_button(
            "Back to Menu",
            back_btn_t_color,
            back_btn_color,
            0,
            500,
            200,
            60,
            b_center=True,
        )

        # 5. 事件處理 (點擊與切換)
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if upgrade_button.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if left_rect.collidepoint(mouse_pos):
                    is_pressing[2] = True
                if right_rect.collidepoint(mouse_pos):
                    is_pressing[3] = True

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 返回選單
                if is_pressing[0] and back_button.collidepoint(mouse_pos):
                    game_state = "menu"

                # 執行購買
                if upgrade_button.collidepoint(mouse_pos) and cost is not None and is_pressing[1]:
                    if total_points >= cost:
                        total_points -= cost
                        current_levels[game_state] += 1  # 🔥 更新等級字典
                        lv_flash_timer = 20  # 啟動閃爍計時器
                        save_data()  # 儲存
                        # print(f"Upgraded {game_state} to Lv.{current_levels[game_state] + 1}")
                        new_text = tool.FloatingText(
                            "-" + tool.num_to_KMBT(cost),
                            WIDTH - 90,
                            20,
                            tool.Colors.RED,
                            speed=0.7,
                            size=24,
                        )
                        floating_texts.append(new_text)

                # 左切換
                if left_rect.collidepoint(mouse_pos) and current_p_num > 1 and is_pressing[2]:
                    game_state = f"upgrade_p{current_p_num - 1}"

                # 右切換
                if right_rect.collidepoint(mouse_pos) and current_p_num < total_pages and is_pressing[3]:
                    game_state = f"upgrade_p{current_p_num + 1}"

                reset_pressing()  # 重置按壓狀態
            if event.type == pygame.MOUSEWHEEL:
                if event.y < 0 and current_p_num < total_pages:
                    game_state = f"upgrade_p{current_p_num + 1}"
                elif event.y > 0 and current_p_num > 1:
                    game_state = f"upgrade_p{current_p_num - 1}"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and current_p_num < total_pages:
                    game_state = f"upgrade_p{current_p_num + 1}"
                if event.key == pygame.K_LEFT and current_p_num > 1:
                    game_state = f"upgrade_p{current_p_num - 1}"
        # 鍵盤左右切換支援
        if keys[pygame.K_d] and current_p_num < total_pages:
            game_state = f"upgrade_p{current_p_num + 1}"
            pygame.time.delay(150)  # 防止切換太快
        if keys[pygame.K_a] and current_p_num > 1:
            game_state = f"upgrade_p{current_p_num - 1}"
            pygame.time.delay(150)
        for ft in floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                floating_texts.remove(ft)
    # ----------------------------------------------------------------------------
    # 關卡選擇
    elif game_state == "level_select":
        screen.fill(tool.Colors.BLACK2)

        clicked_pos = None
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_pos = event.pos
            if event.type == pygame.MOUSEWHEEL:
                scroll_y -= event.y * 40
                # 假設每個按鈕高度+間距是 80 像素
                total_content_height = (len(level_costs) + 1) * 80 + 100

                # 最大捲動距離 = 總長度 減去 畫面高度 (600)
                max_scroll = max(0, total_content_height - HEIGHT)

                # 限制 scroll_y 在 0 到 max_scroll 之間
                scroll_y = tool.num_range(0, max_scroll, scroll_y)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    game_state = "menu"
                reset_pressing()

        for i in range(1, len(level_costs)):
            is_locked = i > levels_unlocked
            is_next_level = i == levels_unlocked + 1
            level_button = tool.text_button(
                f"Level {i}",
                tool.Colors.WHITE,
                tool.Colors.BLUE if not is_locked else tool.Colors.GRAY,
                0,
                60 + i * 80 - scroll_y,
                200,
                60,
                b_center=True,
            )

            draw_this_lock = is_locked
            if level_button.collidepoint(mouse_pos):
                if not is_locked:
                    pygame.draw.rect(screen, tool.Colors.GREEN, level_button, 3)
                elif is_next_level:
                    draw_this_lock = False
                    pygame.draw.rect(screen, tool.Colors.GRAY, level_button)
                    pygame.draw.rect(screen, tool.Colors.GREEN if total_points >= level_costs[i] else tool.Colors.RED, level_button, 3)
                    # 顯示金額
                    display_cost = level_costs[i]
                    tool.show_text(
                        f"Unlock for ${tool.num_to_KMBT(display_cost)}",
                        tool.Colors.GREEN if total_points >= level_costs[i] else tool.Colors.RED,
                        0,
                        60 + i * 80 + 25 - scroll_y,
                        screen_center=True,
                        size=20,
                    )
            if draw_this_lock:
                # 圖層較高的鎖圖案
                if lock_img_loaded and is_locked:
                    screen.blit(lock_img_surface, (310, 60 + i * 80 - 20 - scroll_y))
                elif is_locked:
                    pygame.draw.rect(screen, tool.Colors.GRAY, (310, 60 + i * 80 - 20 - scroll_y, 30, 30))
            # --- 3. 判斷點擊 ---
            if clicked_pos and level_button.collidepoint(clicked_pos):
                if not is_locked:
                    # 點擊成功的邏輯
                    selected_level = f"level{i}"
                    enemy_list = make_enemy_list(i)  # 載入對應關卡的 JSON
                    reset_game()
                    game_state = "3!2!1!"
                elif is_next_level and total_points >= level_costs[i]:
                    # 解鎖邏輯
                    total_points -= level_costs[i]
                    levels_unlocked = i  # 更新解鎖的關卡數
                    new_text = tool.FloatingText(
                        "-" + tool.num_to_KMBT(level_costs[i]),
                        WIDTH - 90,
                        20,
                        tool.Colors.RED,
                        speed=0.7,
                        size=24,
                    )
                    floating_texts.append(new_text)

        pygame.draw.rect(screen, tool.Colors.BLACK2, (0, 0, WIDTH, 100))
        tool.show_text("Level Select", tool.Colors.WHITE, 0, 80, size=50, screen_center=True)

        coin_rect()

        pygame.draw.rect(screen, tool.Colors.BLACK2, (0, HEIGHT - 100, WIDTH, 100))

        back_button = tool.text_button(
            "Back to Menu",
            tool.Colors.WHITE,
            tool.Colors.ORANGE,
            0,
            HEIGHT - 80,
            200,
            60,
            b_center=True,
        )

        # 更新並繪製所有飄浮文字
        for ft in floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                floating_texts.remove(ft)

    # 倒數前五秒
    elif game_state == "3!2!1!":
        screen.fill(tool.Colors.BLACK2)

        coin_rect()
        passed_time = tool.sec_timer(True)
        countdown = 3 - (passed_time)  # 倒數 3 秒

        player_move()

        if countdown >= 1:
            countdown_text = f"{countdown}"
            screen_text = f"Escape Them! v1.0.0 - {countdown}!"
        elif countdown >= 0:
            countdown_text = "GO!"
            screen_text = "Escape Them! v1.0.0 - GO!"
        else:
            tool.sec_timer(False)
            tool.reset_timer()
            game_state = "start_game"

        player_rect = pygame.draw.rect(screen, player_color, player_rect)

        tool.show_text(
            countdown_text,
            tool.Colors.WHITE,
            0,
            HEIGHT // 2,
            screen_center=True,
            size=300,
        )

        for event in events:
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                countdowning = True
                game_state = "pause"
    # 主遊戲程式
    elif game_state == "start_game":
        screen_text = "Escape Them! v1.0.0 - Escaping"
        screen.fill(tool.Colors.BLACK2)
        coin_rect()
        countdowning = False

        current_time_sec = tool.sec_timer(update=True) + 0

        player_move()

        # 緩衝時間
        buffer_duration = now_p5_skill * buffer_duration_buff
        # 敵人模式判斷
        for enemy in enemy_list:
            # 這裡考慮你的難易度 buff
            spawn_start_time = int(enemy["show_time"] * spawn_time_debuff)

            attack_start_time = spawn_start_time + buffer_duration

            # 1. 判斷是否進入 [攻擊模式] (最晚發生的先判斷)
            if current_time_sec >= attack_start_time:
                enemy["show"] = True
                enemy["mode"] = "attack"

            # 2. 判斷是否進入 [生成/預告模式] (中間時段)
            elif current_time_sec >= spawn_start_time:
                enemy["show"] = True
                enemy["mode"] = "spawning"

            # 3. 時間還沒到 (最早的階段)
            else:
                enemy["show"] = False
                enemy["mode"] = "waiting"
                # 敵人移動與碰撞偵測

        for enemy in enemy_list:
            if current_time_sec >= enemy["show_time"]:
                enemy["show"] = True

            # 判斷二：如果還在生成中（緩衝期）

            if enemy["show"] and enemy["mode"] == "spawning":
                # 繪製預告視覺（例如：閃爍效果）
                # 這裡只畫圖，不計算 enemy["x"] += ...，所以它會停在原地
                e_rect = pygame.Rect(enemy["x"], enemy["y"], enemy["width"], enemy["height"])
                if pygame.time.get_ticks() % 500 < 250:  # 每 500 毫秒閃爍一次
                    pygame.draw.rect(screen, enemy["color"], e_rect)

                # 判斷三：檢查緩衝是否結束
                if current_time_sec >= enemy["show_time"] + buffer_duration:
                    enemy["mode"] = "attack"
                continue  # 重要：因為還在緩衝，直接跳過下面的移動與碰撞偵測

            elif enemy["show"] and enemy["mode"] == "attack":
                # 1. 建立碰撞用的 Rect
                e_rect = pygame.Rect(enemy["x"], enemy["y"], enemy["width"], enemy["height"])

                # 2. 決定目標速度 (Target Speed)
                if e_rect.collidepoint(mouse_pos):
                    target_speed = enemy["slow_speed"]
                else:
                    target_speed = enemy["normal_speed"]

                # 3. 平滑過渡速度 (每次靠近目標速度 10%，創造阻力感)
                # 把這段找回來
                # 4. 計算移動方向與位置更新
                enemy_dx, enemy_dy = tool.angle(enemy["angle"])
                if enemy["type"] == "normal":
                    enemy["current_speed"] += (target_speed - enemy["current_speed"]) * 0.1
                    # 更新座標
                    enemy["x"] += enemy_dx * enemy["current_speed"] * enemy["x_dir"] * mode_speed_buff
                    enemy["y"] += enemy_dy * enemy["current_speed"] * enemy["y_dir"] * mode_speed_buff
                elif enemy["type"] == "zigzag":
                    # 簡單的 zigzag 移動邏輯
                    enemy["x"] += 2 * enemy["x_dir"] * mode_speed_buff
                    wave = math.sin(pygame.time.get_ticks() * 0.005) * 3
                    enemy["y"] += wave * mode_speed_buff
                elif enemy["type"] == "random":
                    current_ms = pygame.time.get_ticks()
                    if current_ms - enemy.get("last_change_time", 0) > 2000:  # 2000 毫秒 = 2 秒
                        enemy["x_dir"] = random.choice([-1, 0, 1])
                        enemy["y_dir"] = random.choice([-1, 0, 1])
                        enemy["last_change_time"] = current_ms
                    enemy["x"] += enemy["current_speed"] * enemy["x_dir"] * mode_speed_buff
                    enemy["y"] += enemy["current_speed"] * enemy["y_dir"] * mode_speed_buff

                elif enemy["type"] == "chaser":
                    player_vec = pygame.math.Vector2(player_rect.center)
                    # 建議直接拿 enemy_rect 的中心，或是統一用物件座標
                    enemy_vec = pygame.math.Vector2(enemy["x"] + enemy["width"] // 2, enemy["y"] + enemy["height"] // 2)
                    direction = player_vec - enemy_vec
                    dist = direction.length()
                    if dist > 5:  # 距離大於 5 像素才移動，防止抖動
                        direction = direction.normalize()
                        enemy["x"] += direction.x * enemy["normal_speed"] * mode_speed_buff
                        enemy["y"] += direction.y * enemy["normal_speed"] * mode_speed_buff

                # 5. 邊界反彈處理

                if enemy["x"] <= 0:
                    enemy["x"] = 0
                    enemy["x_dir"] *= -1
                if enemy["x"] >= WIDTH - enemy["width"]:
                    enemy["x"] = WIDTH - enemy["width"]
                    enemy["x_dir"] *= -1
                if enemy["y"] <= 0:
                    enemy["y"] = 0
                    enemy["y_dir"] *= -1
                if enemy["y"] >= HEIGHT - enemy["height"]:
                    enemy["y"] = HEIGHT - enemy["height"]
                    enemy["y_dir"] *= -1

                # 6. 繪製怪物

                pygame.draw.rect(screen, enemy["color"], e_rect)

                # --- 怪物碰撞偵測 ---

                enemy_rect = pygame.Rect(enemy["x"], enemy["y"], enemy["width"], enemy["height"])

                if player_rect.colliderect(enemy_rect):
                    # 核心邏輯：如果現在時間 - 上次受傷時間 > 1秒，才准許受傷

                    if current_time_sec - last_hit_time > invincible_duration:
                        raw_damage = enemy["damage"] * enemy_damage_buff * skin_enemy_damage_buff

                        enemy_damage = int(raw_damage)

                        if enemy_damage < 1:
                            enemy_damage = 1  # 確保最少扣 1 滴

                        if player_hp > enemy_damage:
                            new_text = tool.FloatingText(
                                f"-{int(enemy_damage)}hp",
                                player_rect.x,
                                player_rect.y,
                                tool.Colors.RED,
                                speed=0.8,
                            )

                            floating_texts.append(new_text)

                        player_hp -= enemy_damage

                        last_hit_time = current_time_sec  # 這一行很重要：受傷瞬間更新時間，開啟無敵

                        # print(f"受傷！剩餘血量: {player_hp}")  除錯用

                        if player_hp == player_max_hp:
                            last_cure_time = current_time_sec

        # --- 1. 寶藏出現邏輯 ---
        # 只有在「現在沒顯示」且「冷卻時間到了」才執行
        # 獲取目前的磁鐵範圍
        magnet_range = now_p9_skill  # 直接使用升級後的磁鐵範圍數值

        if not now_treasure["show"] and current_time_sec >= now_treasure["next_spawn_at"]:
            # [步驟 A] 抽籤：決定這次出現的稀有度
            rolled_rarity = random.choice(coin_chance)

            # [步驟 B] 變身：根據抽到的稀有度，去找模板來覆蓋 now_treasure
            template = next((t for t in treasures if t["rarity"] == rolled_rarity), treasures[0])

            now_treasure["rarity"] = template["rarity"]
            now_treasure["color"] = template["color"]
            now_treasure["add_points"] = template["add_points"]

            # [步驟 C] 定位並顯示
            now_treasure["x"] = random.randint(50, WIDTH - 50)
            now_treasure["y"] = random.randint(50, HEIGHT - 50)
            now_treasure["show"] = True

        # --- 2. 寶藏碰撞與繪製 ---
        if now_treasure["show"]:
            # 1. 【磁鐵邏輯】放在這裡！錢幣顯示時才吸引
            magnet_range = now_p9_skill  # 直接使用升級後的磁鐵範圍數值

            player_vec = pygame.math.Vector2(player_rect.center)
            coin_vec = pygame.math.Vector2(now_treasure["x"] + 15, now_treasure["y"] + 15)
            distance = player_vec.distance_to(coin_vec)

            if distance < magnet_range:
                trying_to_touch_player = True
            if trying_to_touch_player:
                move_vec = player_vec - coin_vec
                if move_vec.length() > 0:
                    # 速度可以設為 5，或是根據玩家速度調整
                    now_treasure["x"] += move_vec.x * (0.05 * now_p10_skill)
                    now_treasure["y"] += move_vec.y * (0.05 * now_p10_skill)

            # 2. 繪製圖片 (使用更新後的 x, y)
            now_treasure_rarity = now_treasure["rarity"].lower()
            screen.blit(COIN_IMAGES[now_treasure_rarity], (now_treasure["x"], now_treasure["y"]))

            # 3. 更新碰撞盒並偵測碰撞
            t_rect = COIN_IMAGES[now_treasure_rarity].get_rect(topleft=(now_treasure["x"], now_treasure["y"]))

            if player_rect.colliderect(t_rect):
                trying_to_touch_player = False  # 碰到玩家後重置，下一次出現才會再吸引
                # 1. 計算分數
                min_p, max_p = (add * coin_multiplier for add in now_treasure["add_points"])
                base_val = random.uniform(min_p, max_p)

                treasure_points += base_val

                display_val = f"{round(base_val * gm_points_buff * now_p3_skill, 1):g}"

                coin_text = tool.FloatingText(f"+${display_val}", player_rect.x, player_rect.y, tool.Colors.GOLD)
                floating_texts.append(coin_text)

                # 3. 消失並設定「下一次」出現的時間
                now_treasure["show"] = False
                cooldown = random.randint(*next_spawn_range)  # type: ignore
                reduction = now_p2_skill
                now_treasure["next_spawn_at"] = current_time_sec + max(1, int(cooldown - reduction))

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    game_state = "pause"

        # --- 玩家血量回復 ---
        # 1. 確保只有在血量未滿且玩家還活著時才計算
        if player_hp < player_max_hp and player_hp > 0:
            # 2. 改用 >= 判斷，確保每隔指定秒數觸發一次
            if current_time_sec - last_cure_time >= now_p7_skill["time"]:
                player_hp += now_p7_skill["hp"]

                # 3. 修正：為了讓計時更準確，last_cure_time 應該加上冷卻時間，而不是直接等於當前時間
                last_cure_time += now_p7_skill["time"]

                new_text = tool.FloatingText(
                    f"+{now_p7_skill['hp']}hp" if player_max_hp >= player_hp else f"+{int(now_p7_skill['hp'] - (player_hp - player_max_hp))}hp",
                    player_rect.x,
                    player_rect.y,
                    tool.Colors.GREEN,
                    speed=0.8,
                )
                floating_texts.append(new_text)

                # 4. 確保不溢出
                if player_hp > player_max_hp:
                    player_hp = player_max_hp
        else:
            # 如果血量滿了，持續更新 last_cure_time 讓計時器「對齊」當前時間
            # 這樣受傷的一瞬間才會重新開始計時，而不是受傷後馬上秒回
            last_cure_time = current_time_sec

        # --- AFK 偵測邏輯 ---
        # 檢查玩家當前位置是否與上一幀相同
        player_pos = (player_rect.x, player_rect.y)
        if enemy_list[2]["show"]:
            if player_pos == last_player_pos:
                # 位置沒變，累計時間（1 / FPS）
                afk_timer += 1 / 60
            else:
                # 位置變了，重置計時器
                afk_timer = 0
                last_player_pos = player_pos
            # 3. 如果發呆超過 10 秒
            if afk_timer >= AFK_LIMIT:
                reset_game()
                game_state = "afk_kick"

        # 更新畫面、繪製物件
        tool.text_button(
            "",
            tool.Colors.WHITE,
            tool.Colors.DARK_RED,
            WIDTH - 110,
            70,
            100,
            23,
            t_y=82,
            size=15,
        )
        # 血條
        display_hp = math.ceil(player_hp)
        if display_hp < 0:
            display_hp = 0  # 防止負數
        hp_rect = tool.text_button(
            "",
            tool.Colors.WHITE,
            tool.Colors.RED,
            WIDTH - 110,
            70,
            int((display_hp / player_max_hp) * 100),
            23,
            size=24,
        )
        tool.show_text(
            f"hp:{int(display_hp)}/{int(player_max_hp)}",
            tool.Colors.WHITE,
            WIDTH - 60,
            80,
            size=20,
            center=True,
        )

        # 判斷是否在無敵時間內 (受傷後 1000 毫秒內)
        is_invincible = (current_time_sec - last_hit_time) < invincible_duration * invincible_time_buff

        if is_invincible:
            # 無敵時：顯示灰色 (確保你看得到玩家)
            player_rect = pygame.draw.rect(screen, tool.Colors.DARK_GRAY, player_rect)
        else:
            # 正常時：顯示原本皮膚顏色
            player_rect = pygame.draw.rect(screen, player_color, player_rect)
        points = (current_time_sec * points_multiplier + treasure_points) * gm_points_buff * now_p3_skill
        if selected_level == "level 2":
            points *= 1.2  # 關卡加成
        if selected_level == "level 3":
            points *= 1.5
        if selected_level == "level 4":
            points *= 1.7
        tool.show_text(
            f"Time: {tool.show_time_min(current_time_sec)}",
            tool.Colors.WHITE,
            10,
            10,
            size=24,
        )
        display_points = tool.num_to_KMBT(round(points, 1))
        tool.show_text(f"Coins: ${display_points}$", tool.Colors.WHITE, 10, 40, size=24)
        # 更新並繪製所有飄浮文字
        for ft in floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                floating_texts.remove(ft)
        if player_hp <= 0:
            # 1. 立即計算當局得分並加入總額
            total_points += points
            # 2. 立即存檔
            save_data()

            # 3. 處理其他死亡標記
            tool.collision_time = pygame.time.get_ticks()

            game_state = "game_over"
        # 在畫面上印出座標
        # tool.py_text(f"Pos: {player_rect.x}, {player_rect.y}", tool.Colors.WHITE, 50, 550, size=20)
    # 遊戲暫停
    elif game_state == "pause":
        screen.fill(tool.Colors.BLACK2)
        coin_rect()
        tool.sec_timer(False)
        maybe_cheat = True
        from_pause = True
        for enemy in enemy_list:
            if enemy["show"] and not countdowning:
                enemy_rect = pygame.draw.rect(screen, enemy["color"], (enemy["x"], enemy["y"], enemy["width"], enemy["height"]))
        for treasure in treasures:
            if treasure["show"] and not countdowning:
                t_rect = pygame.Rect(treasure["x"], treasure["y"], 20, 20)
                pygame.draw.rect(screen, treasure["color"], t_rect)
        pygame.draw.rect(screen, player_color, player_rect)
        tool.screen_vague(10)
        tool.show_text("Pause", tool.Colors.WHITE, 0, 80, 50, screen_center=True)
        display_points = tool.num_to_KMBT(round(points, 1))
        tool.show_text(f"Coins: {display_points}$", tool.Colors.WHITE, 0, 140, screen_center=True)
        resume_button = tool.text_button(
            "Resume",
            tool.Colors.WHITE,
            tool.Colors.BROWN,
            0,
            170,
            180,
            60,
            b_center=True,
        )
        settings_button = tool.text_button(
            "Settings",
            tool.Colors.BLACK,
            tool.Colors.GREEN,
            0,
            250,
            180,
            60,
            b_center=True,
        )
        restart_button = tool.text_button(
            "Restart",
            tool.Colors.BLACK,
            tool.Colors.YELLOW,
            0,
            330,
            180,
            60,
            b_center=True,
        )
        menu_button = tool.text_button(
            "Back to Menu",
            tool.Colors.BLACK,
            tool.Colors.PURPLE,
            0,
            410,
            180,
            60,
            b_center=True,
        )
        leave_button = tool.text_button("Leave", tool.Colors.WHITE, tool.Colors.RED, 0, 490, 180, 60, b_center=True)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if resume_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if settings_button.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if restart_button.collidepoint(mouse_pos):
                    is_pressing[2] = True
                if menu_button.collidepoint(mouse_pos):
                    is_pressing[3] = True
                if leave_button.collidepoint(mouse_pos):
                    is_pressing[4] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if resume_button.collidepoint(mouse_pos) and is_pressing[0]:
                    if not countdowning:
                        game_state = "start_game"
                    else:
                        game_state = "3!2!1!"
                if settings_button.collidepoint(mouse_pos) and is_pressing[1]:
                    game_state = "setting_p1"
                if restart_button.collidepoint(mouse_pos) and is_pressing[2]:
                    tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool.reset_timer()
                    player_hp = player_max_hp
                    total_points += points
                    longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
                    reset_game()
                    game_state = "3!2!1!"
                if menu_button.collidepoint(mouse_pos) and is_pressing[3]:
                    tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool.reset_timer()
                    player_hp = player_max_hp
                    total_points += points
                    longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
                    reset_game()
                    game_state = "menu"
                if leave_button.collidepoint(mouse_pos) and is_pressing[4]:
                    player_hp = player_max_hp
                    total_points += points
                    longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
                    reset_game()
                    running = False
                reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                    if not countdowning:
                        game_state = "start_game"
                    else:
                        game_state = "3!2!1!"
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_c:
                    player_hp = player_max_hp
                    total_points += points
                    longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
                    running = False
    # 死亡
    elif game_state == "game_over":
        screen.fill(tool.Colors.BLACK2)
        coin_rect()
        maybe_cheat = False
        from_pause = False
        for enemy in enemy_list:
            if enemy["show"]:
                enemy_rect = pygame.draw.rect(screen, enemy["color"], (enemy["x"], enemy["y"], 30, 15))
        pygame.draw.rect(screen, player_color, player_rect)
        passed_time = pygame.time.get_ticks() - tool.collision_time if tool.collision_time is not None else 0
        countdown = 10 - (passed_time // 1000)  # 倒數 10 秒
        tool.show_text(
            f"You survive for {tool.show_time_min(current_time_sec)}",
            tool.Colors.WHITE,
            0,
            100,
            size=48,
            screen_center=True,
        )
        gm_text = game_mode.replace("_", " ")
        tool.show_text(
            f"in {gm_text} mode.",
            tool.Colors.WHITE,
            0,
            150,
            size=48,
            screen_center=True,
        )
        tool.show_text(
            "Congratulations!" if current_time_sec >= (50 / gm_points_buff) else "Try it again!",
            tool.Colors.WHITE,
            0,
            230,
            size=48,
            screen_center=True,
        )
        display_points = tool.num_to_KMBT(round(points, 1))
        tool.show_text(f"points:{display_points}$", tool.Colors.WHITE, 0, 300, screen_center=True)
        tool.show_text(
            f"Back to Menu in {countdown} sec",
            tool.Colors.WHITE,
            0,
            410,
            size=40,
            screen_center=True,
        )
        back_button = tool.text_button(
            "Back to Menu",
            tool.Colors.WHITE,
            tool.Colors.ORANGE,
            0,
            490,
            150,
            size=24,
            b_center=True,
        )
        if not has_save_survived_time:
            new_text = tool.FloatingText("+" + tool.num_to_KMBT(points), WIDTH - 90, 20, tool.Colors.GREEN, size=24, time=150, speed=0.5)
            floating_texts.append(new_text)
            longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
            has_save_survived_time = True
        for ft in floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                floating_texts.remove(ft)
        if passed_time >= 10000:  # 過了 10000 毫秒 (10秒)
            tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
            tool.reset_timer()
            player_hp = player_max_hp
            game_state = "menu"
            for ft in floating_texts[:]:
                ft.reset()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_state = "menu"
                    tool.collision_time = None
                    tool.reset_timer()
                    for ft in floating_texts[:]:
                        ft.reset()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    game_state = "menu"
                    tool.collision_time = None
                    tool.reset_timer()
                    for ft in floating_texts[:]:
                        ft.reset()
    # bug頁面
    # 1.AFK_error
    elif game_state == "afk_kick":
        screen.fill(tool.Colors.BLACK)
        screen_text = "Escape Them! v1.0.0 - ERROR: 1011451"
        # 畫一個紅色的警告框
        pygame.draw.rect(screen, tool.Colors.RED, (WIDTH // 2 - 250, 100, 500, 400))
        pygame.draw.rect(screen, tool.Colors.BLACK2, (WIDTH // 2 - 245, 95, 500, 400))
        # 在顯示標題前，隨機切換顏色
        flash_color = tool.Colors.RED if pygame.time.get_ticks() % 500 < 250 else tool.Colors.GRAY
        tool.show_text(
            "CRITICAL ERROR",
            tool.Colors.RED,
            0,
            150,
            size=60,
            screen_center=True,
            font_type="None",
        )
        tool.show_text(
            "AFK_DETECTION_TIMEOUT",
            tool.Colors.WHITE,
            0,
            240,
            size=25,
            screen_center=True,
            font_type="None",
        )
        tool.show_text(
            "Error code: 1011451",
            tool.Colors.GRAY,
            0,
            280,
            size=25,
            screen_center=True,
            font_type="None",
        )

        # 返回主選單按鈕 - 改成亮紅色背景增加緊張感
        close_button = tool.text_button(
            "TERMINATE PROCESS",
            tool.Colors.WHITE,
            tool.Colors.RED,
            0,
            400,
            350,
            60,
            b_center=True,
            font_type="None",
        )

        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if close_button.collidepoint(mouse_pos):
                    # 點下去那一刻，程式直接崩潰跳出
                    raise AFKError()
            if event.type == pygame.QUIT:
                raise AFKError()
    # 2.save_game_too_old_error
    elif game_state == "save_game_error":
        screen.fill(tool.Colors.BLACK)
        screen_text = "Escape Them! v1.0.0 - ERROR: 4215788"
        tool.draw_rect(tool.Colors.RED, 0, 100, 550, 450, center=True)
        pygame.draw.rect(screen, tool.Colors.BLACK2, (WIDTH // 2 - 270, 95, 550, 450))
        tool.show_text(
            "SAVE_FILE_ERROR",
            tool.Colors.RED,
            0,
            150,
            size=55,
            screen_center=True,
            font_type="None",
        )
        tool.show_text(
            "YOUR 'save_game.json' IS TOO OLD",
            tool.Colors.WHITE,
            0,
            240,
            size=25,
            screen_center=True,
            font_type="None",
        )
        tool.show_text(
            "Error code: 4215788",
            tool.Colors.GRAY,
            0,
            280,
            size=25,
            screen_center=True,
            font_type="None",
        )
        update_button = tool.text_button(
            "Update your 'save_game.json'",
            tool.Colors.WHITE,
            tool.Colors.RED,
            0,
            400,
            350,
            60,
            b_center=True,
            font_type="None",
        )
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if update_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if update_button.collidepoint(mouse_pos) and is_pressing[0]:
                    migrate_save_format()
                    load_data()
                    game_state = "menu"
    # 3.game_state_error
    else:
        screen.fill(tool.Colors.BLACK)
        screen_text = "Escape Them! v1.0.0 - ERROR: 2487145"
        tool.draw_rect(tool.Colors.RED, 0, 100, 550, 450, center=True)
        pygame.draw.rect(screen, tool.Colors.BLACK2, (WIDTH // 2 - 270, 95, 550, 450))
        tool.show_text(
            "SOMTHING WENT WRONG",
            tool.Colors.RED,
            0,
            150,
            size=55,
            screen_center=True,
            font_type="None",
        )
        tool.show_text(
            "GAME_STATE_NOT_CORRECT",
            tool.Colors.WHITE,
            0,
            240,
            size=25,
            screen_center=True,
            font_type="None",
        )
        tool.show_text(
            "Error code: 2487145",
            tool.Colors.GRAY,
            0,
            280,
            size=25,
            screen_center=True,
            font_type="None",
        )
        menu_button = tool.text_button(
            "Back To Menu",
            tool.Colors.WHITE,
            tool.Colors.RED,
            0,
            400,
            350,
            60,
            b_center=True,
            font_type="None",
        )
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if menu_button.collidepoint(mouse_pos) and is_pressing[0]:
                    player_hp = player_max_hp
                    total_points += points
                    longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
                    save_data()
                    reset_game()
                    game_state = "menu"
                reset_pressing()

    for event in events:
        if event.type == pygame.QUIT:
            running = False

    pygame.display.set_caption(screen_text)
    pygame.display.flip()
    clock.tick(60)
pygame.quit()
print("")
print("")

save_data()
print("已成功儲存檔案到:超級冒險遊戲v0.2.5.14\\save_game.json")
print()
sys.exit("掰掰!下次再玩!")
