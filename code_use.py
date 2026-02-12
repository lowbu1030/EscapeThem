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
for _ in range(10):
    is_pressing.append(False)


def reset_pressing():
    is_pressing[:] = [False] * len(is_pressing)


# 顯示專區
next_spawn_range = random.randint(14, 20)

# 遊戲模式
g_m = ["easy", "normal", "hard", "super_hard", "crazy"]
gm_i = 1
game_mode = g_m[gm_i]

# 遊戲儲存模式
s_m = ["off", "die_save", "upgrade_save"]
sm_i = 0
save_mode = s_m[sm_i]

# 先建立一個空的矩形佔位
start_button = settings_button = upgrade_button = help_button = exit_button = player_rect = back_button = enemy_rect = pygame.Rect(0, 0, 0, 0)

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
has_plus_points = False
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
}

current_levels = {f"upgrade_p{i}": 0 for i in range(1, len(UPGRADE_CONFIG) + 1)}


def get_skill_val(p_key):
    lvl = current_levels[p_key]
    return UPGRADE_CONFIG[p_key]["skills"][lvl]


def update_skill():
    global now_p1_skill, now_p2_skill, now_p3_skill, now_p4_skill, now_p5_skill, now_p6_skill, now_p7_skill, now_p8_skill
    now_p1_skill = get_skill_val("upgrade_p1")
    now_p2_skill = get_skill_val("upgrade_p2")
    now_p3_skill = get_skill_val("upgrade_p3")
    now_p4_skill = get_skill_val("upgrade_p4")
    now_p5_skill = get_skill_val("upgrade_p5")
    now_p6_skill = get_skill_val("upgrade_p6")
    now_p7_skill = get_skill_val("upgrade_p7")
    now_p8_skill = get_skill_val("upgrade_p8")


update_skill()

player_max_hp = 10
player_hp = player_max_hp
last_hit_time = -10  # 上次受傷時間，預設負值確保開局能受傷
invincible_duration = now_p8_skill / 1000  # 無敵時間 1秒，可升級
has_save_survived_time = False

last_cure_time = 0
current_time_sec = 0

enemy_damage = 10
enemy_damage_buff = 1

# --- 資料區：定義多個鎖的位置 ---
# 你可以用列表存座標，想放幾個就寫幾個
unlocked_locks = {
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

player_skins = {  # 修正字典載入
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
        "color": tool.Colors.ORANGE2,
        "value": 1400,
        "has_bought": False,
        "effect": ["points_multiplier", "max_hp", "speed"],
        "power": [2.3, 0.7, 0.7],
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
        "value": 2500,
        "has_bought": False,
        "effect": ["enemy_spawn_speed", "max_hp"],
        "power": [1.7, 1.2],
    },
    "dark green": {
        "color": tool.Colors.DARK_GREEN,
        "value": 2100,
        "has_bought": False,
        "effect": ["max_hp", "speed"],
        "power": [2.0, 1.2],
    },
}

longest_survived_time = {
    "easy": 0,
    "normal": 0,
    "hard": 0,
    "super_hard": 0,
    "crazy": 0,
}
has_buy_crazy = False
crazy_btn_text = ""

B_WIDTH = 240
B_HEIGHT = 80
scroll_y = 0


# --- 依照要求順序排列的升級商店資料 ---
def update_upgrade_hub_layout():
    global upgrade_hub_layout
    upgrade_hub_layout = {}

    # 1. 這裡定義你原本 p1 ~ p8 的專屬顏色 (順序不能亂)
    # 對應: [速度, 金幣, 分數, 大小, 怪速, 血量, 回血, 無敵]
    p_colors = [
        tool.Colors.RED,  # p1
        tool.Colors.ORANGE,  # p2
        tool.Colors.YELLOW,  # p3
        tool.Colors.GREEN,  # p4
        tool.Colors.CYAN,  # p5
        tool.Colors.BLUE,  # p6
        tool.Colors.PURPLE,  # p7
        tool.Colors.PINK,  # p8
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
    }


saved = False


def save_data():
    try:
        # 準備要寫入的資料
        data = get_save_data()

        with SAVE_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # print("💾 存檔成功！")

    except Exception as e:
        print(f"❌ 存檔失敗: {e}")


loaded = False


def load_data():
    # 宣告 global 變數 (注意這裡加入了 current_levels，移除了 p1_i 等舊變數)
    global total_points, target_points, current_levels, longest_survived_time, player_skins, now_player_skin, current_player_color_name, game_state, gm_i, has_buy_crazy

    try:
        if SAVE_PATH.exists():
            with SAVE_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # --- 安全檢查：如果還殘留舊格式，強制跳錯讓玩家修復 ---
            # 檢查 upgrades 內部是否有舊的鍵值 (如 "speed")
            up_check = data.get("upgrades", {})
            longest_survived_time = data.get("records", longest_survived_time)
            if "points_sum" in data or "speed" in up_check or "crazy" not in longest_survived_time:
                print("⚠️ 偵測到舊版存檔，進入修復模式。")
                game_state = "save_game_error"
                return

            # 1. 讀取金錢
            total_points = data.get("balance", 0)
            target_points = total_points

            # 2. 讀取升級數據 (核心修改)
            # 直接讀取 "upgrade_p1" 對應的值，並存入 current_levels
            saved_ups = data.get("upgrades", {})
            for i in range(1, 9):
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
        mode_button_color, \
        next_spawn_range, \
        mode_speed_buff, \
        gm_points_buff, \
        game_mode, \
        g_m, \
        gm_i, \
        save_mode, \
        s_m, \
        sm_i, \
        spawn_time_debuff, \
        now_p1_skill, \
        now_p2_skill, \
        now_p3_skill, \
        now_p4_skill, \
        now_p5_skill, \
        now_p6_skill, \
        now_p7_skill, \
        now_p8_skill, \
        enemy_damage_buff

    game_mode = g_m[gm_i]
    save_mode = s_m[sm_i]

    update_skill()

    # 遊戲模式設定
    if game_mode == "easy":
        mode_button_color = tool.Colors.GREEN
        next_spawn_range = (10, 13)
        mode_speed_buff = 0.5
        gm_points_buff = 0.7
        spawn_time_debuff = enemy_damage_buff = 1
    elif game_mode == "normal":
        mode_button_color = tool.Colors.YELLOW
        next_spawn_range = (14, 18)
        mode_speed_buff = 1
        gm_points_buff = 1
        spawn_time_debuff = enemy_damage_buff = 1
    elif game_mode == "hard":
        mode_button_color = tool.Colors.ORANGE
        next_spawn_range = (17, 21)
        mode_speed_buff = 1.3
        gm_points_buff = 1.7
        spawn_time_debuff = 0.8
        enemy_damage_buff = 1
    elif game_mode == "super_hard":
        mode_button_color = tool.Colors.RED
        next_spawn_range = (20, 24)
        mode_speed_buff = 2
        gm_points_buff = 2.2
        spawn_time_debuff = 0.6
        enemy_damage_buff = 1
    elif game_mode == "crazy":
        mode_button_color = tool.Colors.PURPLE
        next_spawn_range = (23, 27)
        mode_speed_buff = 3
        gm_points_buff = 2.7
        spawn_time_debuff = 0.4
        enemy_damage_buff = 1.5


def reset_game():
    global \
        player_rect, \
        player_size, \
        player_color, \
        player_speed, \
        current_player_speed, \
        enemy_list, \
        treasures, \
        treasure_points, \
        next_spawn_range, \
        points, \
        mode_speed_buff, \
        gm_points_buff, \
        maybe_cheat, \
        from_pause, \
        start_button_color, \
        start_button_text, \
        start_button_text_color, \
        mode_button_color, \
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
        invincible_duration, \
        now_p8_skill, \
        clicked_key, \
        afk_timer, \
        last_player_pos, \
        AFK_LIMIT

    load_resets()
    apply_skin_effects()

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

    start_button_color = tool.Colors.DARK_GREEN
    start_button_text = "START"
    start_button_text_color = tool.Colors.WHITE

    player_max_hp = int(now_p6_skill * player_max_hp_buff)
    player_hp = player_max_hp

    # 定義一個幫忙產生敵人的小工具 (寫在 reset_game 裡面或外面都可以)
    def make_enemy(show_time, speed, slow_speed, color, angle_range=(10, 80)):
        return {
            "x": random.randint(50, WIDTH - 50),
            "y": random.randint(20, HEIGHT - 20),
            "angle": random.randint(*angle_range),
            "current_speed": speed,
            "normal_speed": speed,
            "slow_speed": slow_speed,
            "x_dir": random.choice([-1, 1]),
            "y_dir": random.choice([-1, 1]),
            "color": color,
            "show": False,
            "show_time": show_time,
            "mode": "waiting",
        }

    # 直接呼叫工具來生成列表
    enemy_list = [
        make_enemy(-10, 3, 1, tool.Colors.PURPLE),
        make_enemy(12, 5, 3, tool.Colors.RED_2, angle_range=(100, 150)),
        make_enemy(32, 7, 4, tool.Colors.GREEN, angle_range=(10, 20)),
        make_enemy(45, 9, 5, tool.Colors.CYAN, angle_range=(20, 50)),
        make_enemy(57, 2, 0.5, tool.Colors.BLACK),  # 黑色慢速
        make_enemy(57, 15, 10, tool.Colors.ORANGE2, angle_range=(30, 50)),  # 橘色快速
        make_enemy(77, 25, 18, tool.Colors.GRAY, angle_range=(30, 50)),  # 灰色超快
        make_enemy(100, 3, 1, tool.Colors.DARK_GREEN),
        make_enemy(100, 1, 0.2, tool.Colors.PINK),
        make_enemy(120, 2, 0.5, tool.Colors.YELLOW),
        make_enemy(120, 3, 1, tool.Colors.BLUE),
        make_enemy(120, 7, 5, tool.Colors.WHITE),
    ]

    treasure_points = 0

    # 1. 定義寶藏的配置表格 (稀有度, 顏色, 機率, 分數範圍)
    treasure_config = [
        ("Common", tool.Colors.WHITE, 140, (2, 5)),
        ("Uncommon", tool.Colors.GREEN, 140, (5, 9)),
        ("Rare", tool.Colors.BLUE, 80, (8, 12)),
        ("Epic", tool.Colors.PURPLE, 60, (11, 15)),
        ("Legendary", tool.Colors.ORANGE, 40, (15, 18)),
        ("Mythic", tool.Colors.RED, 24, (17, 20)),
        ("Exotic", tool.Colors.CYAN, 8, (20, 23)),
        ("Divine", tool.Colors.GOLD, 1, (23, 27)),
    ]

    # 2. 自動生成 treasures 列表
    treasures = []
    for name, color, chance, pts in treasure_config:
        treasures.append(
            {
                "rarity": name,
                "color": color,
                "chance": chance,
                "add_points": pts,
                # 下面這些是所有寶藏都一樣的設定，寫一次就好
                "x": random.randint(300, WIDTH - 30),
                "y": random.randint(100, HEIGHT - 100),
                "show": False,
                "can_spawn": True,
                "next_spawn_at": random.randint(*next_spawn_range),  # type:ignore
            }
        )

    now_treasure = treasures[0]

    coin_chance = []
    for t in treasures:
        for _ in range(t["chance"]):
            coin_chance.append(t["rarity"])


reset_game()


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


running = True
game_state = "menu"

load_data()
load_resets()

floating_texts = []  # 放在遊戲開始前，用來裝所有的漂浮文字

COIN_IMAGES = {}

for t in treasure_config:
    img_path = BASE_DIR / "images" / "treasures" / f"{t[0].lower()}.png"

    if img_path.exists():
        # 載入並轉換為帶有透明度的格式
        surface = pygame.image.load(str(img_path)).convert_alpha()
        # 根據你的遊戲需求縮放大小 (例如 30x30)
        target_width = 30

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
        if start_button.collidepoint(mouse_pos):
            start_button_color = tool.Colors.GOLD
            start_button_text_color = tool.Colors.BLACK
            start_button_text = "Press Me!"
        else:
            start_button_color = tool.Colors.DARK_GREEN
            start_button_text_color = tool.Colors.WHITE
            start_button_text = "Start"
        if settings_button.collidepoint(mouse_pos):
            settings_button_color = tool.Colors.GREEN
            settings_button_text_color = tool.Colors.BLACK
        else:
            settings_button_color = tool.Colors.BLUE2
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

        start_button = tool.text_button(
            start_button_text,
            start_button_text_color,
            start_button_color,
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
                if start_button.collidepoint(mouse_pos):
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
                if start_button.collidepoint(mouse_pos) and is_pressing[0]:
                    reset_game()
                    game_state = "3!2!1!"
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
                if event.key == pygame.K_SPACE:
                    reset_game()
                    game_state = "3!2!1!"
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            game_state = "setting_p1"
        if keys[pygame.K_LEFT] or keys[pygame.K_d]:
            game_state = "upgrade_p1"
    # 難易度與最長存活時間
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
        tool.show_text("Now Difficulty:", tool.Colors.WHITE, 0, 130, size=30, screen_center=True)
        gm_text = g_m[gm_i].replace("_", " ")
        mode_button = tool.text_button(gm_text, tool.Colors.BLACK, mode_button_color, 0, 150, 180, b_center=True)
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
        easy_rect = tool.CR(pygame.Rect(70, 210, 500, 50), tool.Colors.GREEN, show=(game_mode == "easy"))
        easy_rect.draw(screen)
        normal_rect = tool.CR(
            pygame.Rect(70, 270, 500, 50),
            tool.Colors.YELLOW,
            show=(game_mode == "normal"),
        )
        normal_rect.draw(screen)
        hard_rect = tool.CR(
            pygame.Rect(70, 330, 500, 50),
            tool.Colors.ORANGE,
            show=(game_mode == "hard"),
        )
        hard_rect.draw(screen)
        super_hard_rect = tool.CR(
            pygame.Rect(70, 390, 500, 50),
            tool.Colors.RED,
            show=(game_mode == "super_hard"),
        )
        super_hard_rect.draw(screen)
        crazy_rect = tool.CR(
            pygame.Rect(70, 450, 500, 50),
            tool.Colors.PURPLE,
            show=(game_mode == "crazy"),
        )
        crazy_rect.draw(screen)
        # 顯示最長存活時間
        tool.show_text(
            f"easy mode: {tool.show_time_min(longest_survived_time['easy'])}",
            tool.Colors.BLACK,
            0,
            230,
            screen_center=True,
        )
        tool.show_text(
            f"normal mode: {tool.show_time_min(longest_survived_time['normal'])}",
            tool.Colors.BLACK,
            0,
            290,
            screen_center=True,
        )
        tool.show_text(
            f"hard mode: {tool.show_time_min(longest_survived_time['hard'])}",
            tool.Colors.BLACK,
            0,
            350,
            screen_center=True,
        )
        tool.show_text(
            f"super hard mode: {tool.show_time_min(longest_survived_time['super_hard'])}",
            tool.Colors.BLACK,
            0,
            410,
            screen_center=True,
        )
        tool.show_text(
            f"crazy mode: {tool.show_time_min(longest_survived_time['crazy'])}",
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
            mode_button_color = tool.Colors.GRAY
        else:
            if game_mode == "easy":
                mode_button_color = tool.Colors.GREEN
            elif game_mode == "normal":
                mode_button_color = tool.Colors.YELLOW
            elif game_mode == "hard":
                mode_button_color = tool.Colors.ORANGE
            elif game_mode == "super_hard":
                mode_button_color = tool.Colors.RED
            elif game_mode == "crazy":
                mode_button_color = tool.Colors.PURPLE
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if mode_button.collidepoint(mouse_pos):
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
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if mode_button.collidepoint(mouse_pos) and not maybe_cheat and is_pressing[0]:
                    gm_i += 1
                    if has_buy_crazy:
                        gm_i %= 5
                    else:
                        gm_i %= 4
                    game_mode = g_m[gm_i]
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
                reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    game_state = "setting_p2"
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
            tool.Colors.BLUE2,
            0,
            290,
            200,
            60,
            b_center=True,
        )
        save_mode_button = tool.text_button(
            "Game Save Mode:",
            tool.Colors.WHITE,
            tool.Colors.BLACK,
            0,
            370,
            350,
            100,
            t_y=400,
            b_center=True,
        )
        sm_text = save_mode.replace("_", " ")
        tool.show_text(sm_text, tool.Colors.WHITE, 0, 440, screen_center=True)
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
                if save_mode_button.collidepoint(mouse_pos):
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
                if save_mode_button.collidepoint(mouse_pos) and is_pressing[2]:
                    sm_i += 1
                    sm_i %= len(s_m)
                    save_mode = s_m[sm_i]
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
        for t, info in unlocked_locks.items():
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
            for _, info in unlocked_locks.items():
                info["show"] = True

        tool.show_text("VIP Skins", tool.Colors.GOLD, 0, 400, screen_center=True)

        # 最後統一畫出所有鎖頭 (要在按鈕畫完之後才畫，才會蓋在上面)
        if lock_img_loaded:
            for info in unlocked_locks.values():
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
                for t, info in unlocked_locks.items():
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
        screen.fill(tool.Colors.BLACK)
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
        pygame.draw.rect(screen, tool.Colors.BLACK, (0, HEIGHT - 80, WIDTH, 80))
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
            tool.Colors.BLACK,
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
        total_pages = 8  # 總共有8種升級

        # 2. 繪製背景與標題
        screen.fill(tool.Colors.BLUE)

        # --- 標題文字 ---
        tool.show_text(cfg["title"], tool.Colors.WHITE, 0, 240, size=50, screen_center=True)
        tool.show_text(
            f"Level: Lv.{lvl + 1}",
            tool.Colors.WHITE,
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
            back_btn_t_color, back_btn_color = tool.Colors.BLACK, tool.Colors.ORANGE2
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
                        if save_mode == "upgrade_save":
                            save_data()  # 儲存
                        # print(f"Upgraded {game_state} to Lv.{current_levels[game_state] + 1}")

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
    # ----------------------------------------------------------------------------
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
                enemy["mode"] = "waiting"  # 或是你原本的狀態

        # 在 start game 模式中
        for enemy in enemy_list:
            if current_time_sec >= enemy["show_time"]:
                enemy["show"] = True
            # 判斷二：如果還在生成中（緩衝期）
            if enemy["show"] and enemy["mode"] == "spawning":
                # 繪製預告視覺（例如：閃爍效果）
                # 這裡只畫圖，不計算 enemy["x"] += ...，所以它會停在原地
                e_rect = pygame.Rect(enemy["x"], enemy["y"], 30, 15)

                # 視覺提示概念：利用時間戳讓它閃爍
                if pygame.time.get_ticks() % 1000 == 500:
                    pygame.draw.rect(screen, enemy["color"], e_rect)

                # 判斷三：檢查緩衝是否結束（例如：現身後過了2秒）
                # 你可以記錄一個 spawn_start_time，或者檢查 current_time_sec
                if current_time_sec >= enemy["show_time"] + buffer_duration:  # 2秒緩衝
                    enemy["mode"] = "attack"

                continue  # 重要：因為還在緩衝，直接跳過下面的移動與碰撞偵測
            if enemy["show"] and enemy["mode"] == "attack":
                # 1. 建立碰撞用的 Rect
                e_rect = pygame.Rect(enemy["x"], enemy["y"], 30, 15)

                # 2. 決定目標速度 (Target Speed)
                if e_rect.collidepoint(mouse_pos):
                    target_speed = enemy["slow_speed"]
                else:
                    target_speed = enemy["normal_speed"]

                # 3. 平滑過渡速度 (每次靠近目標速度 10%，創造阻力感)
                # 這會讓怪物碰到滑鼠時慢慢停下，離開時慢慢加速
                enemy["current_speed"] += (target_speed - enemy["current_speed"]) * 0.1

                # 4. 計算移動方向與位置更新
                enemy_dx, enemy_dy = tool.angle(enemy["angle"])

                # 更新座標
                enemy["x"] += enemy_dx * enemy["current_speed"] * enemy["x_dir"] * mode_speed_buff
                enemy["y"] += enemy_dy * enemy["current_speed"] * enemy["y_dir"] * mode_speed_buff

                # 5. 邊界反彈處理
                if enemy["x"] <= 0 or enemy["x"] >= WIDTH - 30:
                    enemy["x_dir"] *= -1
                if enemy["y"] <= 0 or enemy["y"] >= HEIGHT - 20:
                    enemy["y_dir"] *= -1

                # 6. 繪製怪物
                pygame.draw.rect(screen, enemy["color"], e_rect)

                # --- 怪物碰撞偵測 ---
                # for enemy in enemy_list:
                enemy_rect = pygame.Rect(enemy["x"], enemy["y"], 30, 15)
                if player_rect.colliderect(enemy_rect):
                    # 核心邏輯：如果現在時間 - 上次受傷時間 > 1秒，才准許受傷
                    if current_time_sec - last_hit_time > invincible_duration:
                        raw_damage = 10 * enemy_damage_buff * skin_enemy_damage_buff
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

        # --- 1. 寶藏出現邏輯 (改為只處理一個) ---
        # 只有在「現在沒顯示」且「冷卻時間到了」才執行
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

        # --- 2. 寶藏碰撞與繪製 (改為只處理一個) ---
        if now_treasure["show"]:
            # t_rect = pygame.Rect(now_treasure["x"], now_treasure["y"], 20, 20)
            # pygame.draw.rect(screen, now_treasure["color"], t_rect)

            now_treasure_rarity = now_treasure["rarity"].lower()
            screen.blit(COIN_IMAGES[now_treasure_rarity], (now_treasure["x"], now_treasure["y"]))
            t_rect = COIN_IMAGES[now_treasure_rarity].get_rect(topleft=(now_treasure["x"], now_treasure["y"]))

            if player_rect.colliderect(t_rect):
                # 1. 計算分數
                min_p, max_p = now_treasure["add_points"]
                base_val = random.randint(min_p, max_p)

                treasure_points += base_val * coin_multiplier

                display_val = f"{round(base_val * coin_multiplier * gm_points_buff * now_p3_skill, 1):g}"

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

        for enemy in enemy_list:
            if enemy["show"]:
                enemy_rect = pygame.draw.rect(screen, enemy["color"], (enemy["x"], enemy["y"], 30, 15))

        # 判斷是否在無敵時間內 (受傷後 1000 毫秒內)
        is_invincible = (current_time_sec - last_hit_time) < invincible_duration * invincible_time_buff

        if is_invincible:
            # 無敵時：顯示灰色 (確保你看得到玩家)
            player_rect = pygame.draw.rect(screen, tool.Colors.DARK_GRAY, player_rect)
        else:
            # 正常時：顯示原本皮膚顏色
            player_rect = pygame.draw.rect(screen, player_color, player_rect)
        points = (current_time_sec * points_multiplier + treasure_points) * gm_points_buff * now_p3_skill
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
            total_points += points  # 假設這是你這局賺的錢

            # 2. 立即存檔
            save_data()

            # 3. 處理其他死亡標記
            tool.collision_time = pygame.time.get_ticks()
            has_plus_points = True  # 標記為已加過錢，避免 game_over 重複加
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
                enemy_rect = pygame.draw.rect(screen, enemy["color"], (enemy["x"], enemy["y"], 30, 15))
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
                    longest_survived_time[game_mode] = max(longest_survived_time[game_mode], current_time_sec)
                    reset_game()
                    game_state = "3!2!1!"
                if menu_button.collidepoint(mouse_pos) and is_pressing[3]:
                    tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool.reset_timer()
                    player_hp = player_max_hp
                    total_points += points
                    longest_survived_time[game_mode] = max(longest_survived_time[game_mode], current_time_sec)
                    reset_game()
                    game_state = "menu"
                if leave_button.collidepoint(mouse_pos) and is_pressing[4]:
                    player_hp = player_max_hp
                    total_points += points
                    longest_survived_time[game_mode] = max(longest_survived_time[game_mode], current_time_sec)
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
                    longest_survived_time[game_mode] = max(longest_survived_time[game_mode], current_time_sec)
                    running = False
    # 死亡
    elif game_state == "game_over":
        screen.fill(tool.Colors.BLACK2)
        coin_rect()
        for ft in floating_texts[:]:
            ft.reset()
        maybe_cheat = False
        from_pause = False
        for enemy in enemy_list:
            if enemy["show"]:
                enemy_rect = pygame.draw.rect(screen, enemy["color"], (enemy["x"], enemy["y"], 30, 15))
        for treasure in treasures:
            if treasure["show"]:
                t_rect = pygame.Rect(treasure["x"], treasure["y"], 20, 20)
                pygame.draw.rect(screen, treasure["color"], t_rect)
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
        if not has_plus_points:
            total_points += points
            points = 0
            has_plus_points = True
            save_mode = s_m[sm_i]
            if save_mode == "die_save":
                save_data()
        if not has_save_survived_time:
            longest_survived_time[game_mode] = max(longest_survived_time[game_mode], current_time_sec)
            has_save_survived_time = True
        if passed_time >= 10000:  # 過了 10000 毫秒 (10秒)
            tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
            tool.reset_timer()
            player_hp = player_max_hp
            game_state = "menu"
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_state = "menu"
                    tool.collision_time = None
                    tool.reset_timer()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    game_state = "menu"
                    tool.collision_time = None
                    tool.reset_timer()
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
                    longest_survived_time[game_mode] = max(longest_survived_time[game_mode], current_time_sec)
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
