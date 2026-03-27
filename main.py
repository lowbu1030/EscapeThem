"""
pygame 提示：以右邊為 0 度
"""

import json
import math
import random
import sys
from pathlib import Path

import pygame

import tool  # 載入你的工具包
from config import UPGRADE_COMBAT, UPGRADE_SURVIVAL, player_skins
from old_to_new import migrate_save_format

WIDTH, HEIGHT = 700, 600

now_treasure = {}
shop_page = "survival"


class Enemy:
    def __init__(self, show_time, speed, slow_speed, color, angle_range=(10, 80), size=10, damage=10, type="normal"):
        self.show_time = show_time
        self.color = color
        self.type = type
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
        # 建立一個暫時的向量供 chaser 和 eat_coin 使用
        self_vec = pygame.math.Vector2(self.x + self.width / 2, self.y + self.height / 2)
        e_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.current_speed += (target_speed - self.current_speed) * 0.1
        if self.type == "normal":
            self.x += self.current_dx * self.current_speed * self.x_dir * mode_speed_buff
            self.y += self.current_dy * self.current_speed * self.y_dir * mode_speed_buff

        elif self.type == "zigzag":
            self.x += 2 * self.x_dir * mode_speed_buff * self.current_speed
            wave = math.sin(current_time_ms * 0.005) * 3
            self.y += wave * mode_speed_buff * self.current_speed

        elif self.type == "random":
            if current_time_ms - self.last_change_time > 2000:
                self.x_dir = random.choice([-1, 0, 1])
                self.y_dir = random.choice([-1, 0, 1])
                self.last_change_time = current_time_ms
            self.x += self.normal_speed * self.x_dir * mode_speed_buff * self.current_speed
            self.y += self.normal_speed * self.y_dir * mode_speed_buff * self.current_speed

        elif self.type == "random_angle":
            # 這裡要使用我們之前幫你存在 self 裡的隨機時間
            if current_time_ms - self.last_change_time > self.random_time_limit:
                self.random_time_limit = random.randint(800, 2300)
                self.angle = random.randint(0, 360)
                self.current_dx, self.current_dy = tool.get_direction(self.angle)
                self.last_change_time = current_time_ms
            self.x += self.current_dx * self.normal_speed * self.x_dir * mode_speed_buff * self.current_speed
            self.y += self.current_dy * self.normal_speed * self.y_dir * mode_speed_buff * self.current_speed

        elif self.type == "chaser":
            player_vec = pygame.math.Vector2(player_rect.center)
            direction = player_vec - self_vec
            if direction.length() > 5 and not e_rect.colliderect(player_rect):
                direction = direction.normalize()
                self.x += direction.x * self.normal_speed * mode_speed_buff * self.current_speed
                self.y += direction.y * self.normal_speed * mode_speed_buff * self.current_speed

        elif self.type == "sprint":
            sprint_boost = 1.0
            time_passed = current_time_ms - self.last_change_time
            if 4000 < time_passed <= (4000 + self.time_lasting):
                sprint_boost = 2.0

            self.x += self.current_dx * self.current_speed * self.x_dir * mode_speed_buff * sprint_boost
            self.y += self.current_dy * self.current_speed * self.y_dir * mode_speed_buff * sprint_boost

            if time_passed > 4000 + 1000:
                self.last_change_time = current_time_ms

        elif self.type == "eat_coin":
            if now_treasure["show"]:
                # 取得寶箱中心
                coin_vec = pygame.math.Vector2(now_treasure["x"] + 15, now_treasure["y"] + 15)
                direction = coin_vec - self_vec
                if direction.length() > 5:
                    direction = direction.normalize()
                    self.x += direction.x * self.normal_speed * mode_speed_buff * self.current_speed
                    self.y += direction.y * self.normal_speed * mode_speed_buff * self.current_speed
                    collide_player = False
            else:
                # 沒寶箱時，執行普通移動
                self.x += self.current_dx * self.normal_speed * self.x_dir * mode_speed_buff * self.current_speed
                self.y += self.current_dy * self.normal_speed * self.y_dir * mode_speed_buff * self.current_speed

    def _check_bounds(self):
        # 處理 X 軸邊界
        if self.x <= 0 or self.x >= WIDTH - self.width:
            self.x_dir *= -1  # 撞到左右牆壁，水平方向反轉
            self.x = tool.num_range(0, WIDTH - self.width, self.x)

        # 處理 Y 軸邊界
        if self.y <= 0 or self.y >= HEIGHT - self.height:
            self.y_dir *= -1  # 撞到上下牆壁，垂直方向反轉
            self.y = tool.num_range(0, HEIGHT - self.height, self.y)


BASE_DIR = Path(__file__).parent

SAVE_PATH = BASE_DIR / "save_game.json"
current_active_path = SAVE_PATH
ENEMY_PATH = BASE_DIR / "enemies"
SOUND_PATH = BASE_DIR / "sounds"
BGM_PATH = BASE_DIR / "BGM"

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


# 1. 初始化與基本設定
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
tool.set_screen(screen)
screen_rect = screen.get_rect()
screen_text = "Escape Them!"
pygame.display.set_caption(screen_text)
clock = pygame.time.Clock()

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
}
sounds["coin"].set_volume(0.5)
sounds["shoot"].set_volume(0.2)
sounds["fast_heart_beat"].set_volume(1.0)
sounds["slow_heart_beat"].set_volume(1.0)
shoot_channel = pygame.mixer.Channel(1)
heart_channel = pygame.mixer.Channel(2)
buy_channel = pygame.mixer.Channel(3)
current_heart = None
current_vol = 0.5
target_vol = 0.5


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


# 顯示專區
next_spawn_range = random.randint(14, 20)

# 遊戲模式
g_m = ["easy", "normal", "hard", "super_hard", "crazy"]
gm_i = 1
game_mode = g_m[gm_i]

level_costs = [0, 0, 1000, 3000, 7000, 12000, 20000, 35000, 50000]  # 解鎖關卡的價格，第一個是卡位用，第一關是0元

# 關卡
all_levels = ["level" + str(i + 1) for i in range(len(level_costs) - 1)]  # 自動新增關卡
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
    title_img_surface = pygame.image.load(str(IMG_PATH) + "/images/Escape Them.png").convert_alpha()
    title_img_surface = pygame.transform.scale(title_img_surface, (400, 180))
    title_img_loaded = True

    title_rect = title_img_surface.get_rect()
    title_rect.center = (WIDTH // 2, 120)
except FileNotFoundError as e:
    title_img_loaded = False
    title_rect.center = pygame.Rect(WIDTH // 2, 200, 400, 150)
    print(f"無法載入標題圖片{e}")
# 錢幣用木板
try:
    coin_wood_img_surface = pygame.image.load(str(IMG_PATH) + "/images/coin_wood.png").convert_alpha()
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
    orig_mouse_img_surface = pygame.transform.scale(orig_mouse_img_surface, (40, 40))
    mouse_img_surface = orig_mouse_img_surface
    mouse_img_loaded = True

    mouse_rect = orig_mouse_img_surface.get_rect()
    mouse_rect = (0, 0)
except FileNotFoundError as e:
    mouse_img_loaded = False
    mouse_rect = pygame.Rect(0, 0, 0, 0)
    print(f"無法載入錢幣用木板圖片{e}")
    print("滑鼠圖片炸掉啦！")

l_img_show, r_img_show = False, True

points = 0
total_points = 0

current_levels = {f"upgrade_p{i}": 0 for i in range(1, len(UPGRADE_SURVIVAL) + len(UPGRADE_COMBAT) + 1)}


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
    now_skills = {f"p{i}": get_skill_val(f"upgrade_p{i}") for i in range(1, 19)}


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
    global current_active_path, can_shoot

    try:
        target_path = file_path if file_path else SAVE_PATH
        current_active_path = target_path
        if target_path and target_path.exists():
            with target_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            print("❌ 沒有找到存檔檔案")

        longest_survived_time = data.get("records", longest_survived_time)

        # 1. 讀取金錢
        total_points = data.get("balance", 0)
        target_points = total_points

        # 2. 讀取升級數據 (核心修改)
        # 直接讀取 "upgrade_p1" 對應的值，並存入 current_levels
        saved_ups = data.get("upgrades", {})
        for i in range(1, len(UPGRADE_SURVIVAL) + 1):
            key = f"upgrade_p{i}"
            # 如果存檔裡有這個等級就讀取，沒有就預設 0
            current_levels[key] = saved_ups.get(key, 0)

        # 讀取其他資料 (保持不變)
        longest_survived_time = data.get("records", longest_survived_time)
        # 讀取皮膚資料
        load_player_skin_data = data.get("player_skins", {})  # 取得存檔中的皮膚字典

        for name, skin in player_skins.items():
            # 這裡可以先設定一個預設值，確保萬一存檔沒這筆資料，也不會壞掉
            if name in load_player_skin_data:
                saved_skin = load_player_skin_data[name]

                # 直接修改 skin，player_skins 本體會同步更新
                skin["has_owned"] = saved_skin.get("has_owned", saved_skin.get("has_bought", False))
                skin["level"] = saved_skin.get("level", 1)
                skin["exp"] = saved_skin.get("exp", 0)
            else:
                # 如果存檔裡沒這份皮膚，你可以在這裡決定要不要初始化它
                # 比如紅皮膚預設就是 True
                if name == "red":
                    skin["has_owned"] = True

        now_player_skin = data.get("now_player_skin", now_player_skin)
        current_player_color_name = data.get("current_skin_name", "red")
        gm_i = data.get("gm_i", 1)
        has_buy_crazy = data.get("has_buy_crazy", False)
        levels_unlocked = data.get("levels_unlocked", 1)

        print(f"✔️ 載入成功！當前等級: {current_levels}")

    except Exception as e:
        print(f"❌ 載入失敗: {e}")
        # 出錯時初始化為 0
        for i in range(1, 9):
            current_levels[f"upgrade_p{i}"] = 0
    update_skill()
    can_shoot = bool(now_skills["p15"])


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
    mode_speed_buff *= Let_Time_Go_Fast


color_map = {
    "RED": tool.Colors.RED,
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
        e_color = color_map.get(e["color"], tool.Colors.WHITE)

        # 2. 【關鍵改動】直接建立 Enemy 物件
        # 這裡傳入的參數要對應你 Enemy 類別 __init__ 的順序
        new_enemy = Enemy(
            show_time=e["show_time"], speed=e["speed"], slow_speed=e["slow_speed"], color=e_color, angle_range=a_range, size=e.get("size", 10), damage=e.get("damage", 10), type=e.get("type", "normal")
        )

        enemy_list.append(new_enemy)

    return enemy_list


def make_cannon_list(level):

    def make_cannon(x, y, angle, show_time, fire_rate=2000, bullet_speed=5, bom_range=100, color=tool.Colors.GRAY, move_speed=0, type="normal"):
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
        }

    json_path = ENEMY_PATH / f"level{level}.json"

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
            color=color_map.get(c["color"], tool.Colors.GRAY),  # 沒抓到就給灰色
            move_speed=c.get("move_speed", 0),
            type=c.get("type", "normal"),
        )

        cannon_list.append(cannon_data)
    return cannon_list


# 砲台的子彈生成函式，放在外面讓子彈生成時也能呼叫
def make_bullet(x, y, angle, speed, bom_range, color=tool.Colors.GRAY):
    return {
        "x": x,
        "y": y,
        "angle": angle,
        "speed": speed,
        "width": 25,  # 子彈通常比較小
        "height": 25,
        "color": color,
        "damage": 5,  # 大砲子彈的基礎傷害
        "bom_range": bom_range,
        "current_bom_radius": 0,  # 初始爆炸半徑
        "is_exploding": False,  # 是否正在爆炸
        "collide_player": False,  # 是否已經碰到玩家（用來控制爆炸後的傷害只計算一次）
        "has_dealt_bom_damage": False,  # 是否已經對玩家造成過爆炸傷害
    }


bullet_list = []  # 全局子彈列表，當砲台開火時會往裡面添加子彈
now_bom_range = 1


def reset_game():
    global player_rect, player_size, player_color, player_speed, current_player_speed, treasures, treasure_points, next_spawn_range, points, mode_speed_buff, gm_points_buff, maybe_cheat
    global from_pause, levels_button_color, levels_button_text, levels_button_text_color, level_button_color, last_hit_time, player_hp, player_max_hp, countdown_text, countdown, passed_time
    global coin_chance, now_treasure, treasure_config, last_cure_time, has_plus_points, has_save_survived_time, countdowning, trying_to_touch_player, invincible_duration, now_p8_skill
    global clicked_key, afk_timer, last_player_pos, AFK_LIMIT, change_dir_timer, lv_flash_timer, collide_player, bullet_damage, target_vol, shake_timer

    load_resets()
    apply_skin_effects()

    target_vol = 0.5

    shake_timer = 0

    lv_flash_timer = 0

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
draw_button_text = "Draw Skin ($500)"
last_draw_color = None


def coin_rect():
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


collide_player = True
click_pos = None

# pygame.mixer.music.play(-1)  # 這裡決定要不要播放背景音樂
pygame.mouse.set_visible(False)


def get_key(t, cfg):
    current_config = UPGRADE_SURVIVAL if shop_page == "survival" else UPGRADE_COMBAT
    return t in current_config and cfg == current_config[t]


upgrade_buttons = {}


while running:
    screen_text = f"Escape Them! v1.0.0 - {game_state.replace('_', ' ')}"
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    mouse = pygame.mouse
    mouse_pos = mouse.get_pos(False)  # 取得滑鼠座標
    mouse_button = mouse.get_pressed()

    if shake_timer > 0:
        offset_x = random.randint(-shake_range, shake_range)
        offset_y = random.randint(-shake_range, shake_range)
        shake_timer -= 1
    else:
        offset_x, offset_y = 0, 0

    # 主畫面
    if game_state == "menu":
        screen.fill(tool.Colors.BROWN)
        coin_rect()
        for i in range(2):
            alphas[i] = 255
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
                    reset_scroll_ys()
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
        easy_rect = tool.CR(pygame.Rect(70, 210, 450, 50), tool.Colors.GREEN if not from_pause else tool.Colors.GRAY, show=(game_mode == "easy"))
        easy_rect.draw(screen)
        normal_rect = tool.CR(
            pygame.Rect(70, 270, 450, 50),
            tool.Colors.YELLOW if not from_pause else tool.Colors.GRAY,
            show=(game_mode == "normal"),
        )
        normal_rect.draw(screen)
        hard_rect = tool.CR(
            pygame.Rect(70, 330, 450, 50),
            tool.Colors.ORANGE if not from_pause else tool.Colors.GRAY,
            show=(game_mode == "hard"),
        )
        hard_rect.draw(screen)
        super_hard_rect = tool.CR(
            pygame.Rect(70, 390, 450, 50),
            tool.Colors.RED if not from_pause else tool.Colors.GRAY,
            show=(game_mode == "super_hard"),
        )
        super_hard_rect.draw(screen)
        crazy_rect = tool.CR(
            pygame.Rect(70, 450, 450, 50),
            tool.Colors.PURPLE if not from_pause else tool.Colors.GRAY,
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
        easy_button = tool.text_button("select", tool.Colors.BLACK, tool.Colors.GREEN if not from_pause else tool.Colors.GRAY, 70, 210, 130, 50)
        normal_button = tool.text_button("select", tool.Colors.BLACK, tool.Colors.YELLOW if not from_pause else tool.Colors.GRAY, 70, 270, 130, 50)
        hard_button = tool.text_button("select", tool.Colors.BLACK, tool.Colors.ORANGE if not from_pause else tool.Colors.GRAY, 70, 330, 130, 50)
        super_hard_button = tool.text_button("select", tool.Colors.BLACK, tool.Colors.RED if not from_pause else tool.Colors.GRAY, 70, 390, 130, 50)
        crazy_button = tool.text_button(
            "select" if has_buy_crazy else crazy_btn_text,
            tool.Colors.BLACK,
            tool.Colors.PURPLE if not from_pause else tool.Colors.GRAY,
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
        scroll_ys[0] = tool.num_range(0, scroll_ys[0], max_scroll_y)  # 強制修正回合法範圍
        target_y = tool.num_range(0, target_y, max_scroll_y)  # 強制修正回合法範圍
        if scroll_ys[0] != target_y or not tool.in_range(0, scroll_ys[0], max_scroll_y):
            scroll_ys[0] += (target_y - scroll_ys[0]) * 0.3  # 每次移動剩下的 30%
        draw_y = 110
        for gm in modes_config:
            tool.text_button(
                f"{gm[0].title()} Mode",
                tool.Colors.BLACK if gm[0] == "easy" or gm[0] == "normal" else tool.Colors.WHITE,
                gm[1],
                0,
                draw_y - scroll_ys[0],
                270,
                60,
                size=34,
                b_center=True,
            )
            draw_y += 90
            for level in all_levels:
                tool.show_text(f"Level {level.replace('level', '')}: {tool.show_time_min(longest_survived_time[level][gm[0]])}", tool.Colors.WHITE, 0, draw_y - scroll_ys[0], screen_center=True)
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
        # pygame.draw.line(screen, tool.Colors.RED, (0, draw_y - scroll_ys[0]), (WIDTH, draw_y - scroll_ys[0]), 5)
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
            btn = tool.text_button(save.stem, tool.Colors.WHITE, tool.Colors.BLUE_2, 0, 150 + i * 70 - scroll_ys[1], 300, 60, b_center=True)
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
                scroll_ys[1] -= event.y * 30
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
                            current_active_path = BASE_DIR / selected_save_name if isinstance(selected_save_name, str) else selected_save_name

                            print(f"載入存檔: {current_active_path}")
                            game_state = "menu"  # 切換回選單
                            load_data(current_active_path)  # 傳入 Path 物件
                            load_resets()  # 重置遊戲狀態

                selected_save_name = None  # 重置
                reset_pressing()
        max_scroll_y = max(0, 150 + len(save_files) * 70 - HEIGHT + 110)  # 根據存檔數量計算最大捲動高度
        scroll_ys[1] = tool.num_range(0, scroll_ys[1], max_scroll_y)  # 強制修正回合法範圍
    # 玩家皮膚購買與更換
    elif game_state == "setting_p3":
        screen.fill(tool.Colors.DARK_GRAY)
        coin_rect()
        start_x = 100  # 左邊起始位置
        start_y = 180  # 列表上方起始位置 (空出標題跟金幣的位置)
        row_gap = 80  # 每排之間的垂直距離
        col_gap = 180  # 如果一排想放多個，左右距離
        skin_list = list(player_skins.keys())

        draw_button = tool.text_button(draw_button_text, tool.Colors.WHITE, draw_button_color, 180, 100, 190, 40, size=22)

        if draw_button.collidepoint(mouse_pos):
            draw_button_color = tool.Colors.GREEN if total_points >= 500 else tool.Colors.RED
            draw_button_text = "Draw Skin ($500)" if total_points >= 500 else "Not Enough Money!"
        else:
            draw_button_color = tool.Colors.GOLD
            draw_button_text = "Draw Skin ($500)"
        click_pos = None
        for event in events:
            # A. 處理滑鼠捲動
            if event.type == pygame.MOUSEWHEEL:
                scroll_ys[4] -= event.y * 30

            # B. 處理滑鼠按下 (is_pressing 紀錄)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 檢查固定 UI 按鈕
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if left_rect.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if draw_button.collidepoint(mouse_pos):
                    is_pressing[2] = True
                # 檢查列表區域 (這裡標記 3 代表準備點擊皮膚)
                is_pressing[3] = True

            # C. 處理滑鼠放開 (觸發動作)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 如果放開時還在按鈕上，且當初是從按鈕按下的
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    game_state = "pause" if from_pause else "menu"

                if left_rect.collidepoint(mouse_pos) and is_pressing[1]:
                    game_state = "setting_p2"

                if draw_button.collidepoint(mouse_pos) and is_pressing[2] and not from_pause:
                    if total_points >= 500:
                        total_points -= 500
                        # 1. 準備抽獎名單與權重
                        skin_names = list(player_skins.keys())
                        weights = [player_skins[name]["draw_weight"] for name in skin_names]

                        # 2. 執行抽獎 (k=1 代表抽一個，回傳的是 list，所以要加 [0])
                        picked_name = random.choices(skin_names, weights=weights, k=1)[0]

                        # 3. 處理抽獎結果
                        skin = player_skins[picked_name]
                        if not skin["has_owned"]:
                            skin["has_owned"] = True
                            print(f"🎉 獲得新皮膚：{picked_name}！")
                            buy_channel.play(sounds["buy_success"])
                        else:
                            # 重複抽到，增加經驗值
                            skin["exp"] += 50
                            print(f"♻️ 重複抽到 {picked_name}，轉化為 50 EXP！")

                            target_exp = get_upgrade_threshold(skin["level"])

                            if skin["exp"] >= target_exp:
                                skin["exp"] -= target_exp
                                skin["level"] += 1
                                print(f"🆙 {picked_name} 升級了！目前 Lv.{skin['level']}")
                            buy_channel.play(sounds["buy_success"])
                            last_draw_color = picked_name
                        save_data()
                    else:
                        buy_channel.play(sounds["buy_error"])
                    apply_skin_effects()
                # 重要：如果剛才是按在列表區，放開時紀錄座標供皮膚列表判定
                if is_pressing[3]:
                    click_pos = mouse_pos
                reset_pressing()  # 清空所有 is_pressing 狀態            if event.type == pygame.KEYDOWN:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    game_state = "setting_p2"

            # D. 處理鍵盤快捷鍵
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LEFT, pygame.K_a]:
                    game_state = "setting_p2"
        total_rows = (len(skin_list) + 1) // 2
        max_scroll = max(0, total_rows * row_gap - 300)
        scroll_ys[4] = tool.num_range(0, max_scroll, scroll_ys[4])

        for i, t in enumerate(skin_list):
            skin_val = player_skins[t]

            # --- 關鍵：動態計算 Y 座標 ---
            # 計算公式： 起始位置 + (第幾個 * 間距) - 捲動量
            # (i // 2) 代表一排兩個，如果你要一排一個就直接用 i
            calc_y = start_y + (i // 2) * row_gap - scroll_ys[4]
            calc_x = start_x + (i % 2) * col_gap

            # 3. 檢查「可視範圍」：只畫出在螢幕中間的按鈕，避免蓋到標題
            if 150 < calc_y < 500:
                # 決定按鈕顯示文字
                if skin_val["has_owned"]:
                    display_text = f"{t} Lv.{skin_val['level']}"
                    btn_color = skin_val["color"]
                else:
                    display_text = "???"
                    btn_color = tool.Colors.GRAY

                # 繪製按鈕並更新碰撞箱 (供點擊判定使用)
                # 注意：這裡把算好的 calc_y 傳進去
                btn_rect = tool.text_button(display_text, skin_unlocked_locks[t]["text_col"], btn_color, calc_x, calc_y, 150, 50, size=22)
                skin_unlocked_locks[t]["rect"] = btn_rect
                # print(skin_unlocked_locks[t])

                # 4. 繪製經驗條 (如果有擁有)
                if skin_val["has_owned"]:
                    bar_y = calc_y + 55
                    # 這裡呼叫剛剛定義的公式函數
                    max_needed = get_upgrade_threshold(skin_val["level"])

                    # 計算當前比例 (確保不超過 1.0)
                    ratio = min(1.0, skin_val["exp"] / max_needed)

                    # 繪製背景
                    pygame.draw.rect(screen, tool.Colors.BLACK, (calc_x, bar_y, 150, 5))
                    # 繪製綠色進度
                    pygame.draw.rect(screen, tool.Colors.GREEN, (calc_x, bar_y, 150 * ratio, 5))
                if click_pos and btn_rect.collidepoint(click_pos):
                    if skin_val["has_owned"]:
                        current_player_color_name = t
                        now_player_skin = skin_val["color"]
                        apply_skin_effects()
                if t == current_player_color_name:
                    # 在按鈕外面畫一個白色的空心框 (width=3)
                    pygame.draw.rect(screen, tool.Colors.WHITE, btn_rect, 3)
        tool.show_text("Player Skins", tool.Colors.WHITE, 0, 50, screen_center=True, size=30)
        if left_img_loaded:
            screen.blit(left_img_surface, left_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, left_rect)
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
        # 資料、皮膚顯示、預覽按鈕
        pygame.draw.line(screen, tool.Colors.BLACK, (450, 80), (450, HEIGHT - 100), 5)
        tool.show_text("Demo player:", tool.Colors.BLACK, 480, 80, size=30)
        show_rect = pygame.draw.rect(screen, now_player_skin, (560, 120, 30, 30))
        try_button = tool.text_button("Try to play", tool.Colors.BLACK, tool.Colors.PURPLE, 480, 400, 150, 40, size=20)
        pygame.draw.line(screen, tool.Colors.BLACK, (470, 460), (650, 460), 5)
        tool.show_text(
            f"You got 1 {last_draw_color} skin!", tool.Colors.get_color(last_draw_color) if last_draw_color is not None else tool.Colors.WHITE, 470, 475, size=20, show=(last_draw_color is not None)
        )
        # --- 右側：皮膚詳細資訊區 ---
        selected_name = current_player_color_name
        skin = player_skins[selected_name]

        # 1. 顯示皮膚大名
        tool.show_text(f"Skin: {selected_name.upper()}", tool.Colors.BLACK, 570, 170, size=26, center=True)

        # 2. 準備效果資料 (處理單一值或列表)
        effects = skin["effect"] if isinstance(skin["effect"], list) else [skin["effect"]]
        powers = skin["base_power"] if isinstance(skin["base_power"], list) else [skin["base_power"]]
        growths = skin["growth"] if isinstance(skin["growth"], list) else [skin["growth"]]
        level = skin["level"]

        # 3. 迴圈顯示每一項能力
        for i, (eff, base_p, grow) in enumerate(zip(effects, powers, growths, strict=False)):
            # 計算當前數值
            # print(f"[DEBUG]: {eff}")
            current_val = calculate_final_stat(eff, base_p, grow, level)

            # 格式化名稱 (例如 points_multiplier -> Points Multiplier)
            display_name = eff.replace("_", " ").title()

            # 繪製標題
            tool.show_text(f"• {display_name}:", tool.Colors.BLACK, 470, 210 + (i * 60), size=18)

            # 繪製數值 (保留兩位小數)
            val_text = f"{round(current_val, 2)}x"
            tool.show_text(val_text, tool.Colors.BLUE, 490, 235 + (i * 60), size=22)

            # 繪製成長率提示 (讓玩家知道升級加多少)
            if grow != 0:
                grow_text = f"(+{grow}/lv)" if grow > 0 else f"({grow}/lv)"
                tool.show_text(grow_text, tool.Colors.GRAY, 570, 238 + (i * 60), size=14)

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
        current_config = UPGRADE_SURVIVAL if shop_page == "survival" else UPGRADE_COMBAT
        screen.fill(tool.Colors.DARK_GREEN)
        update_upgrade_hub_layout()  # --- 繪製箭頭 ---
        if left_img_loaded:
            if l_img_show:
                screen.blit(left_img_surface, upgrade_left_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, upgrade_left_rect)
        if right_img_loaded:
            if r_img_show:
                screen.blit(right_img_surface, upgrade_right_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, upgrade_right_rect)

        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                scroll_ys[2] -= event.y * 40
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if upgrade_left_rect.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if upgrade_right_rect.collidepoint(mouse_pos):
                    is_pressing[2] = True
                for key, rect in upgrade_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        is_pressing[8] = True
                        target_key = key
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 這裡我們不處理列表點擊，只處理固定的返回按鈕
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    game_state = "menu"
                    scroll_ys[2] = 0
                if upgrade_left_rect.collidepoint(mouse_pos) and l_img_show and is_pressing[1]:
                    shop_page = "survival"
                    l_img_show, r_img_show = False, True
                    update_upgrade_hub_layout()
                    scroll_ys[2] = 0
                if upgrade_right_rect.collidepoint(mouse_pos) and r_img_show and is_pressing[2]:
                    shop_page = "combat"
                    l_img_show, r_img_show = True, False
                    update_upgrade_hub_layout()
                    scroll_ys[2] = 0
                if is_pressing[8]:
                    # 再次確認放開時滑鼠還在該按鈕上
                    if upgrade_buttons.get(target_key) and upgrade_buttons[target_key].collidepoint(mouse_pos):
                        game_state = target_key  # 🌟 成功切換畫面！
                        scroll_ys[2] = 0  # 換頁時重置捲軸
                reset_pressing()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            scroll_ys[2] -= 20
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            scroll_ys[2] += 20

        # 限制捲動範圍
        scroll_ys[2] = max(0, min(scroll_ys[2], len(upgrade_hub_layout) * 100 - 350))

        # [簡化] 用一個迴圈搞定繪製與點擊感
        upgrade_buttons.clear()
        for i, (key, info) in enumerate(upgrade_hub_layout.items()):
            y = 130 + i * 100 - scroll_ys[2]
            if -80 < y < HEIGHT:
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
                # 🌟 把產生的 rect 存起來，對應它的 key (例如 upgrade_p1)
                upgrade_buttons[key] = rect

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
        tool.text_button(f"now_mode: {shop_page}", tool.Colors.WHITE, tool.Colors.DARK_GREEN, 0, 90, 500, 40, size=35, b_center=True)
        coin_rect()
    # 這裡取代原本所有 upgrade_p1 ~ p8
    # ------------------------------------------------------------------
    # ✅ 通用升級頁面 (保留你的圖片、箭頭、按鈕樣式)
    # ------------------------------------------------------------------
    elif game_state in UPGRADE_SURVIVAL or game_state in UPGRADE_COMBAT:
        current_config = UPGRADE_SURVIVAL if shop_page == "survival" else UPGRADE_COMBAT
        if game_state in UPGRADE_COMBAT:
            current_data_source = UPGRADE_COMBAT
        else:
            current_data_source = UPGRADE_SURVIVAL
        # 1. 抓取當前頁面的數據
        cfg = current_data_source[game_state]
        lvl = current_levels[game_state]
        costs = cfg["costs"]

        all_configs = {**UPGRADE_SURVIVAL, **UPGRADE_COMBAT}
        current_p_num = int(game_state.replace("upgrade_p", ""))
        total_pages = len(all_configs)

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
        # 2. 判斷是否為定格式
        elif get_key("upgrade_p15", cfg):
            display_text = f"Can Shoot: {bool(now_val)}"

        # 3. 判斷是否為普通數字 (int/float) -> 針對 Speed, Size...
        else:
            if (get_key("upgrade_p16", cfg) or get_key("upgrade_p17", cfg)) and not can_shoot:
                display_text = "You Had Not Buy 'Can Shoot'"
            # 這裡我們配合設定檔裡的 skill_desc
            # 例如 Speed 的 skill_desc 是 "Speed +{}"，這裡只要給數字就好
            else:
                display_text = cfg["skill_desc"].format(now_val)

        # 3. 針對 Regen 的特殊補強
        # 因為 Regen 的 skill_desc 我們設成了 "{}"，所以上面的 else 跑不到格式化
        # 我們手動加上前綴，讓它跟其他屬性看起來比較像
        if "upgrade_p7" in UPGRADE_SURVIVAL and cfg == UPGRADE_SURVIVAL["upgrade_p7"]:
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
                        buy_channel.play(sounds["buy_success"])
                        can_shoot = bool(now_skills["p15"])
                    else:
                        buy_channel.play(sounds["buy_error"])

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
                scroll_ys[3] -= event.y * 40
                # 假設每個按鈕高度+間距是 80 像素
                total_content_height = (len(level_costs) + 1) * 80 + 100

                # 最大捲動距離 = 總長度 減去 畫面高度 (600)
                max_scroll = max(0, total_content_height - HEIGHT)

                # 限制 scroll_y 在 0 到 max_scroll 之間
                scroll_ys[3] = tool.num_range(0, max_scroll, scroll_ys[3])
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
                60 + i * 80 - scroll_ys[3],
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
                        60 + i * 80 + 25 - scroll_ys[3],
                        screen_center=True,
                        size=20,
                    )
            if draw_this_lock:
                # 圖層較高的鎖圖案
                if lock_img_loaded and is_locked:
                    screen.blit(lock_img_surface, (310, 60 + i * 80 - 20 - scroll_ys[3]))
                elif is_locked:
                    pygame.draw.rect(screen, tool.Colors.GRAY, (310, 60 + i * 80 - 20 - scroll_ys[3], 30, 30))
            # --- 3. 判斷點擊 ---
            if clicked_pos and level_button.collidepoint(clicked_pos):
                if not is_locked:
                    # 點擊成功的邏輯
                    selected_level = f"level{i}"
                    enemy_list = make_enemy_list(i)  # 載入對應關卡的 JSON
                    cannon_list = make_cannon_list(i)
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

        # 測試用
        if Invincible:
            current_time_ms = pygame.time.get_ticks() * Let_Time_Go_Fast

            current_time_sec = int(current_time_ms / 1000)  # 秒數也會跟著變快

        else:
            current_time_sec = tool.sec_timer(update=True) + 0

            current_time_ms = pygame.time.get_ticks()

        player_move()

        buffer_duration = now_skills["p5"] * buffer_duration_buff

        for enemy in enemy_list:
            e_rect = enemy.update(current_time_ms, current_time_sec, player_rect, mouse_pos, now_treasure, screen)
            # if (e_rect.colliderect(base_hp_rect) or e_rect.colliderect(coin_rect2)) and enemy.show:
            #     alphas[0] = 100
            # else:
            #     alphas[0] = 255

            if enemy.show and e_rect is not None:
                if enemy.mode == "attack" and player_rect.colliderect(e_rect) and current_time_sec - last_hit_time > invincible_duration:
                    damage_taken = int(enemy.damage * enemy_damage_buff * skin_enemy_damage_buff)
                    damage_multiplier, text_color, text_content, dodged = calculate_damage(damage_taken)

                    if not dodged:
                        shake_timer = 10
                        shake_range = damage_taken

                    # 統一計算最後傷害
                    final_damage = int(damage_taken * damage_multiplier)
                    player_hp -= max(1, final_damage)

                    # 更新時間與音效
                    last_hit_time = current_time_sec
                    sounds["hurt"].play()

                    # 顯示漂浮文字 (帶入剛才判斷好的內容)
                    floating_texts.append(tool.FloatingText(text_content, player_rect.x - 20 if dodged else player_rect.x, player_rect.y, text_color, speed=0.5, time=120))

                pygame.draw.rect(screen, enemy.color, e_rect)
        # 大砲邏輯（跟怪物類似，但沒有移動）
        for cannon in cannon_list:
            spawn_start_time = int(cannon["show_time"] * spawn_time_debuff)

            attack_start_time = spawn_start_time + buffer_duration
            if current_time_sec >= attack_start_time:
                cannon["mode"] = "attack"
                cannon["show"] = True
            elif current_time_sec >= spawn_start_time:
                cannon["mode"] = "spawning"
                cannon["show"] = True
            else:
                cannon["mode"] = "waiting"
                cannon["show"] = False
            if not cannon["show"]:
                continue

            c_rect = pygame.Rect(cannon["x"] - offset_x, cannon["y"] - offset_y, cannon["width"], cannon["height"])

            if cannon["mode"] == "spawning":
                if current_time_ms % 500 < 250:
                    pygame.draw.rect(screen, cannon["color"], c_rect)
                continue
            elif cannon["mode"] == "attack":
                if cannon["type"] == "X_move":
                    c_rect_dx = cannon["move_speed"] * mode_speed_buff * cannon["move_dir"]
                    cannon["x"] += c_rect_dx

                    c_rect.x = cannon["x"]
                    if c_rect.left <= 0:
                        cannon["move_dir"] *= -1
                        cannon["x"] = 2
                        c_rect.x = cannon["x"]
                    if c_rect.right >= WIDTH:
                        cannon["move_dir"] *= -1
                        cannon["x"] = WIDTH - cannon["width"] - 1
                        c_rect.x = cannon["x"]
                elif cannon["type"] == "Y_move":
                    c_rect_dy = cannon["move_speed"] * mode_speed_buff * cannon["move_dir"]
                    cannon["y"] += c_rect_dy

                    c_rect.y = cannon["y"]
                    if c_rect.top <= 0:
                        cannon["move_dir"] *= -1
                        cannon["y"] = 2
                        c_rect.y = cannon["y"]
                    if c_rect.bottom >= HEIGHT:
                        cannon["move_dir"] *= -1
                        cannon["y"] = HEIGHT - cannon["height"]
                        c_rect.y = cannon["y"]
                elif cannon["type"] == "track":
                    # 修正：應該是「加」offset，且修正變數名 centery
                    player_vec = pygame.math.Vector2(player_rect.center)
                    cannon_vec = pygame.math.Vector2(c_rect.center)
                    v = player_vec - cannon_vec
                    time_passed = current_time_ms - cannon["last_fire_time"]
                    total_cooldown = cannon["fire_rate"] / mode_speed_buff
                    if time_passed > (total_cooldown / 2):
                        # 算出剩下的時間比例 (0.0 到 0.5 之間)
                        # 越接近發射，閃爍頻率可以越快
                        flicker_speed = 100
                        if time_passed > (total_cooldown * 0.8):  # 最後 20% 時間閃超快
                            flicker_speed = 50

                        if (pygame.time.get_ticks() // flicker_speed) % 2 == 0:
                            pygame.draw.line(screen, tool.Colors.RED, cannon_vec, player_vec, 3)
                    dist, angle = v.as_polar()
                    cannon["angle"] = angle
                draw_c_rect = c_rect.copy()
                draw_c_rect.x += offset_x
                draw_c_rect.y += offset_y

                pygame.draw.rect(screen, cannon["color"], draw_c_rect)
                if (current_time_ms - cannon["last_fire_time"]) > cannon["fire_rate"] / mode_speed_buff:
                    bullet_x = c_rect.centerx - 12
                    bullet_y = c_rect.centery - 12
                    bullet_list.append(make_bullet(bullet_x, bullet_y, cannon["angle"], cannon["bullet_speed"], cannon["bom_range"], cannon["color"]))
                    shoot_channel.play(sounds["shoot"])
                    cannon["last_fire_time"] = current_time_ms
        # 砲彈
        for bullet in bullet_list[:]:
            b_rect = pygame.Rect(bullet["x"], bullet["y"], 25, 25)

            # --- 第一部分：判斷是否觸發爆炸 ---
            out_of_bounds = bullet["x"] < 0 or bullet["x"] > WIDTH or bullet["y"] < 0 or bullet["y"] > HEIGHT

            # 如果還沒撞到人，就檢查碰撞
            if not bullet["collide_player"] and player_rect.colliderect(b_rect):
                bullet["collide_player"] = True
                # 玩家受傷檢測
                if current_time_sec - last_hit_time > invincible_duration:
                    bullet_damage = max(1, int(10 * enemy_damage_buff * skin_enemy_damage_buff))  # 假設子彈固定傷害為 10
                    bullet_damage = max(1, bullet_damage)  # 確保至少扣 1

                    damage_multiplier, text_color, text_content, dodged = calculate_damage(bullet_damage)
                    final_damage = int(bullet_damage * damage_multiplier)
                    player_hp -= max(1, final_damage)
                    last_hit_time = current_time_sec
                    sounds["hurt"].play()
                    floating_texts.append(tool.FloatingText(text_content, player_rect.x - 20 if dodged else player_rect.x, player_rect.y, text_color, speed=0.5, time=120))

                    if not dodged:
                        shake_timer = 10
                        shake_range = final_damage

                    if player_hp >= player_max_hp:  # 滿血時重置回血計時
                        last_cure_time = current_time_sec
                dist = math.hypot(player_rect.centerx - bullet["x"], player_rect.centery - bullet["y"])
                knockback_force = dist * 0.5
                if player_rect.centerx < bullet["x"]:
                    player_rect.x -= knockback_force  # 往左炸飛
                else:
                    player_rect.x += knockback_force  # 往右炸飛
                if player_rect.centery < bullet["y"]:
                    player_rect.y -= knockback_force  # 往上炸飛
                else:
                    player_rect.y += knockback_force  # 往下炸飛
                player_rect.x = max(0, min(player_rect.x, WIDTH - player_rect.width))
                player_rect.y = max(0, min(player_rect.y, HEIGHT - player_rect.height))

            # --- 第二部分：行為分支 ---
            if out_of_bounds or bullet["collide_player"]:
                # 執行爆炸動畫
                if bullet["current_bom_radius"] <= bullet["bom_range"]:
                    # 畫爆炸圓
                    pygame.draw.circle(screen, tool.Colors.RED, (int(bullet["x"]) - offset_x, int(bullet["y"]) - offset_y), bullet["current_bom_radius"], 5)
                    bullet["current_bom_radius"] += 5
                    # --- 新增：爆炸傷害偵測 ---
                    # 1. 只有「還沒造成爆炸傷害」且「不在無敵時間」才計算
                    if not bullet.get("has_dealt_bom_damage", False):
                        # 2. 計算玩家中心與爆炸中心的距離
                        dist = math.hypot(player_rect.centerx - bullet["x"], player_rect.centery - bullet["y"])

                        # 3. 如果距離小於「當前半徑 + 玩家寬度的一半(緩衝)」，就判定受傷
                        if dist < (bullet["current_bom_radius"] + 15) and current_time_sec - last_hit_time > invincible_duration:
                            damage_multiplier, text_color, text_content, dodged = calculate_damage(bullet_damage)
                            final_damage = int(bullet_damage * damage_multiplier)
                            player_hp -= max(1, final_damage)
                            last_hit_time = current_time_sec
                            sounds["hurt"].play()
                            floating_texts.append(tool.FloatingText(text_content, player_rect.x - 20 if dodged else player_rect.x, player_rect.y, text_color, speed=0.5, time=120))
                            if not dodged:
                                shake_timer = 10
                                shake_range = final_damage

                            # 💡 關鍵：標記這顆子彈已經炸過人了，這顆子彈就不會再傷人第二次
                            bullet["has_dealt_bom_damage"] = True
                else:
                    # 動畫演完，移除子彈
                    bullet_list.remove(bullet)
                    continue

            else:
                # 正常飛行
                bullet_dx, bullet_dy = tool.get_direction(bullet["angle"])
                bullet["x"] += bullet_dx * bullet["speed"] * mode_speed_buff
                bullet["y"] += bullet_dy * bullet["speed"] * mode_speed_buff
                draw_b_rect = pygame.Rect(bullet["x"] - offset_x, bullet["y"] - offset_y, 25, 25)
                pygame.draw.rect(screen, bullet["color"], draw_b_rect)

        # 獲取目前的磁鐵範圍
        magnet_range = now_skills["p9"]  # 直接使用升級後的磁鐵範圍數值

        # 寶藏出現邏輯
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

        # 寶藏碰撞與繪製
        if now_treasure["show"]:
            # 1. 【磁鐵邏輯】放在這裡！錢幣顯示時才吸引
            magnet_range = now_skills["p9"]  # 直接使用升級後的磁鐵範圍數值

            player_vec = pygame.math.Vector2(player_rect.center)
            coin_vec = pygame.math.Vector2(now_treasure["x"] + 15, now_treasure["y"] + 15)
            distance = player_vec.distance_to(coin_vec)

            if distance < magnet_range:
                trying_to_touch_player = True
            if trying_to_touch_player:
                move_vec = player_vec - coin_vec
                if move_vec.length() > 0:
                    # 速度可以設為 5，或是根據玩家速度調整
                    now_treasure["x"] += move_vec.x * (0.05 * now_skills["p10"])
                    now_treasure["y"] += move_vec.y * (0.05 * now_skills["p10"])
                pygame.draw.line(
                    screen,
                    (*tool.Colors.GOLD, 150),  # 金色 (或是用 tool.Colors.GOLD)
                    player_vec,  # 玩家位置
                    coin_vec,  # 錢幣位置
                    2,  # 線條粗度
                )

            # 2. 繪製圖片 (使用更新後的 x, y)
            now_treasure_rarity = now_treasure["rarity"].lower()
            screen.blit(COIN_IMAGES[now_treasure_rarity], (now_treasure["x"] - offset_x, now_treasure["y"] - offset_y))

            # 3. 更新碰撞盒並偵測碰撞
            t_rect = COIN_IMAGES[now_treasure_rarity].get_rect(topleft=(now_treasure["x"], now_treasure["y"]))

            if player_rect.colliderect(t_rect):
                trying_to_touch_player = False  # 碰到玩家後重置，下一次出現才會再吸引
                # 播放音效
                if now_treasure_rarity in ["exotic", "divine"]:
                    sounds["epic_coin"].play()
                    shake_range = 10
                    shake_timer = 20
                else:
                    sounds["coin"].play()
                # 1. 計算分數
                min_p, max_p = (add * coin_multiplier * now_skills["p12"] for add in now_treasure["add_points"])
                base_val = random.uniform(min_p, max_p)

                treasure_points += base_val

                display_val = f"{round(base_val * gm_points_buff * now_skills['p3'], 1):g}"

                coin_text = tool.FloatingText(f"+${display_val}", player_rect.x, player_rect.y, tool.Colors.GOLD)
                floating_texts.append(coin_text)

                # 3. 消失並設定「下一次」出現的時間
                now_treasure["show"] = False
                cooldown = random.randint(*next_spawn_range)  # type: ignore
                reduction = now_skills["p2"]
                now_treasure["next_spawn_at"] = current_time_sec + max(2, int(cooldown - reduction))
            for enemy in enemy_list:
                if enemy.type == "eat_coin" and enemy.show:
                    cooldown = random.randint(*next_spawn_range)  # type: ignore
                    reduction = now_skills["p2"]
                    e_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                    if e_rect.colliderect(t_rect):
                        now_treasure["show"] = False
                        now_treasure["next_spawn_at"] = current_time_sec + max(1, int(cooldown - reduction))
                    enemy.x = tool.num_range(0, WIDTH - enemy.width, enemy.x)
                    enemy.y = tool.num_range(0, HEIGHT - enemy.height, enemy.y)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    game_state = "pause"

        # --- 玩家血量回復 ---
        # 1. 確保只有在血量未滿且玩家還活著時才計算
        if player_hp < player_max_hp and player_hp > 0:
            # 2. 改用 >= 判斷，確保每隔指定秒數觸發一次
            if current_time_sec - last_cure_time >= now_skills["p7"]["time"]:
                player_hp += now_skills["p7"]["hp"]

                # 3. 修正：為了讓計時更準確，last_cure_time 應該加上冷卻時間，而不是直接等於當前時間
                last_cure_time += now_skills["p7"]["time"]

                new_text = tool.FloatingText(
                    f"+{now_skills['p7']['hp']}hp" if player_max_hp >= player_hp else f"+{int(now_skills['p7']['hp'] - (player_hp - player_max_hp))}hp",
                    player_rect.x,
                    player_rect.y,
                    tool.Colors.GREEN,
                    speed=0.8,
                )
                floating_texts.append(new_text)

                # 4. 確保不溢出
                if player_hp > player_max_hp:
                    player_hp = player_max_hp
            if Invincible:
                player_hp += 1
        else:
            # 如果血量滿了，持續更新 last_cure_time 讓計時器「對齊」當前時間
            # 這樣受傷的一瞬間才會重新開始計時，而不是受傷後馬上秒回
            last_cure_time = current_time_sec

        # 心跳音效
        hp_percent = player_hp / player_max_hp
        if hp_percent <= 0.2:
            target_sound = sounds["fast_heart_beat"]
            target_vol = 0.05
        elif hp_percent <= 0.5:
            target_sound = sounds["slow_heart_beat"]
            target_vol = 0.3
        else:
            target_sound = None
            target_vol = 0.5
        if target_sound != current_heart:
            if target_sound:
                heart_channel.play(target_sound, loops=-1)
            else:
                heart_channel.stop()

            current_heart = target_sound

        # --- AFK 偵測邏輯 ---
        # 檢查玩家當前位置是否與上一幀相同
        player_pos = (player_rect.x, player_rect.y)
        if enemy_list[2].show:
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
        base_hp_rect = tool.text_button("", tool.Colors.WHITE, tool.Colors.DARK_RED, WIDTH - 110, 70, 100, 23, t_y=82, size=15, alpha=alphas[0])
        # 血條
        display_hp = math.ceil(player_hp)
        if display_hp < 0:
            display_hp = 0  # 防止負數
        hp_rect = tool.text_button("", tool.Colors.WHITE, tool.Colors.RED, WIDTH - 110, 70, int((display_hp / player_max_hp) * 100), 23, size=24, alpha=alphas[0])
        tool.show_text(f"hp:{int(display_hp)}/{int(player_max_hp)}", tool.Colors.WHITE, WIDTH - 60, 80, size=20, center=True, alpha=alphas[0])

        if Invincible:
            # 畫個紅色的字提醒自己
            tool.show_text("DEBUG: INVINCIBLE ON", tool.Colors.RED, 10, 60, size=15)

        # 判斷是否在無敵時間內
        is_invincible = (current_time_sec - last_hit_time) < invincible_duration * invincible_time_buff

        p_rect = pygame.Rect(player_rect.x - offset_x, player_rect.y - offset_y, player_rect.width, player_rect.height)

        if is_invincible:
            if current_time_ms % 300 < 150:  # 閃爍效果
                pygame.draw.rect(screen, player_color, p_rect)
        else:
            # 正常時：顯示原本皮膚顏色
            pygame.draw.rect(screen, player_color, p_rect)
        points = (current_time_sec * points_multiplier + treasure_points) * gm_points_buff * now_skills["p3"]
        if selected_level == "level 2":
            points *= 1.2  # 關卡加成
        if selected_level == "level 3" and game_mode == "crazy":
            points *= 0.5
        if selected_level == "level 5":
            points *= 1.5
        if selected_level == "level 6":
            points *= 1.7
        if selected_level == "level 7":
            points *= 2
        time_text = tool.show_text(f"Time: {tool.show_time_min(current_time_sec)}", tool.Colors.WHITE, 10, 10, size=24, alpha=alphas[1])
        display_points = tool.num_to_KMBT(round(points, 1))
        points_text = tool.show_text(f"Coins: ${display_points}$", tool.Colors.WHITE, 10, 40, size=24, alpha=alphas[1])

        if player_rect.colliderect(time_text) or player_rect.colliderect(points_text):
            alphas[1] = 100

        if alphas[1] == 255:
            for enemy in enemy_list:
                if not getattr(enemy, "show", True):
                    continue  # 沒出現的不算
                e_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)

                # 怪物碰到右上 OR 碰到左上，兩個一起變透明
                if e_rect.colliderect(time_text) or e_rect.colliderect(points_text):
                    alphas[1] = 100
                    break

        # 更新並繪製所有飄浮文字
        for ft in floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                floating_texts.remove(ft)
        if player_hp <= 0:
            for i in range(2):
                alphas[i] = 255
            # 1. 立即計算當局得分並加入總額
            if not Invincible:
                total_points += points
            # 2. 立即存檔
            save_data()

            # 3. 處理其他死亡標記
            tool.collision_time = current_time_ms

            game_state = "game_over"
        # 在畫面上印出座標
        # tool.py_text(f"Pos: {player_rect.x}, {player_rect.y}", tool.Colors.WHITE, 50, 550, size=20)
        tool.show_text(f"Spawn time: {tool.show_time_min(now_treasure['next_spawn_at'])}, Show: {now_treasure['show']}", tool.Colors.GOLD, 10, HEIGHT - 20, size=15)
    # 遊戲暫停
    elif game_state == "pause":
        screen.fill(tool.Colors.BLACK2)
        coin_rect()
        target_vol = 0.5
        tool.sec_timer(False)
        maybe_cheat = True
        from_pause = True
        for enemy in enemy_list:
            if enemy.show and not countdowning:
                pygame.draw.rect(screen, enemy.color, (enemy.x, enemy.y, enemy.width, enemy.height))
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
                    if not Invincible:
                        total_points += points
                    for i in range(2):
                        alphas[i] = 255
                    longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
                    reset_game()
                    game_state = "3!2!1!"
                if menu_button.collidepoint(mouse_pos) and is_pressing[3]:
                    tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool.reset_timer()
                    player_hp = player_max_hp
                    if not Invincible:
                        total_points += points
                    for i in range(2):
                        alphas[i] = 255
                    longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
                    reset_game()
                    game_state = "menu"
                if leave_button.collidepoint(mouse_pos) and is_pressing[4]:
                    player_hp = player_max_hp
                    if not Invincible:
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
                    if not Invincible:
                        total_points += points
                    longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
                    running = False

        for ft in floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                floating_texts.remove(ft)
    # 死亡
    elif game_state == "game_over":
        screen.fill(tool.Colors.BLACK2)
        coin_rect()
        for i in range(3):
            alphas[i] = 255
        target_vol = 0.5
        maybe_cheat = False
        from_pause = False
        for enemy in enemy_list:
            if enemy.show:
                enemy_rect = pygame.draw.rect(screen, enemy.color, (enemy.x, enemy.y, enemy.width, enemy.height))
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
        if not has_save_survived_time and not Invincible:
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
                    migrate_save_format(current_active_path)
                    load_data(current_active_path)
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
                    if not Invincible:
                        total_points += points
                    longest_survived_time[selected_level][game_mode] = max(longest_survived_time[selected_level][game_mode], current_time_sec)
                    save_data()
                    reset_game()
                    game_state = "menu"
                reset_pressing()

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        # if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        #     mouse_img_surface = pygame.transform.scale(orig_mouse_img_surface, (30, 30))
        # if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        #     mouse_img_surface = pygame.transform.scale(orig_mouse_img_surface, (40, 40))
    if mouse_img_loaded:
        blit_mouse_pos = (mouse_pos[0] - 5, mouse_pos[1])
        if pygame.mouse.get_pressed()[0]:
            # 點擊時，座標稍微 +2，會有往內按的感覺
            screen.blit(mouse_img_surface, (blit_mouse_pos[0] + 2, blit_mouse_pos[1] + 2))
        else:
            screen.blit(mouse_img_surface, blit_mouse_pos)

    if game_state != "start_game":
        heart_channel.stop()
    current_vol += (target_vol - current_vol) * 0.005
    pygame.mixer.music.set_volume(current_vol)  # 靜音：0, 開聲音：current_vol
    pygame.display.set_caption(screen_text)
    pygame.display.flip()
    clock.tick(60 * Time_Speed)
pygame.quit()
print("")
print("")

save_data()
print("已成功儲存檔案到:超級冒險遊戲v0.2.5.14\\save_game.json")
print()
sys.exit("掰掰!下次再玩!")
