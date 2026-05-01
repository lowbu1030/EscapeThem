"""
pygame 提示：以右邊為 0 度
"""

import json
import math
import random
import sys

import pygame

import config  # 所有的全域變數與初始化都在這裡
import old_to_new
import tool備用  # 載入你的工具包

# 1. 取得 config 中已經初始化好的物件
screen = config.screen
clock = config.clock
is_pressing = config.is_pressing  # 引用 config 的列表
scroll_ys = config.scroll_ys
buttons = config.buttons

# 確保工具包使用的 screen 是同一個
tool備用.set_screen(screen)


def load_data(file_path=None):
    # 注意：這裡不再需要 global，因為我們是透過 config.xxx 修改
    try:
        target_path = file_path if file_path else config.SAVE_PATH
        config.current_active_path = target_path

        if not target_path.exists():
            print("❌ 沒有找到存檔檔案")
            return  # 沒檔案就跳出，避免後面讀取報錯

        with target_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. 讀取金錢與基本數值
        config.total_points = data.get("balance", 0)
        config.target_points = config.total_points
        config.longest_survived_time = data.get("records", config.longest_survived_time)
        config.gm_i = data.get("gm_i", 1)
        config.has_buy_crazy = data.get("has_buy_crazy", False)
        config.select_world = data.get("select_world", 1)
        config.all_worlds_unlocked = data.get("levels_unlocked", {"world1": 1, "world2": 1})
        config.worlds_unlocked = data.get("worlds_unlocked", 1)
        print(f"DEBUG: 載入的字典內容是 {config.all_worlds_unlocked}")

        # 2. 讀取升級數據 (修正變數路徑)
        saved_ups = data.get("upgrades", {})
        # 這裡根據 config 裡的 UPGRADE_SURVIVAL 長度自動循環
        for i in range(1, len({**config.UPGRADE_SURVIVAL, **config.UPGRADE_COMBAT}) + 1):
            key = f"upgrade_p{i}"
            config.current_levels[key] = saved_ups.get(key, 0)

        # 3. 讀取皮膚資料
        load_player_skin_data = data.get("player_skins", {})
        for name, skin in config.player_skins.items():
            if name in load_player_skin_data:
                saved_skin = load_player_skin_data[name]
                # 注意：這裡直接修改 skin 字典內的內容，會同步到 config.player_skins
                skin["has_owned"] = saved_skin.get("has_owned", saved_skin.get("has_bought", False))
                skin["level"] = saved_skin.get("level", 1)
                skin["exp"] = saved_skin.get("exp", 0)
            elif name == "red":
                skin["has_owned"] = True

        # 4. 讀取當前使用的皮膚
        config.now_player_skin = data.get("now_player_skin", config.now_player_skin)
        config.current_player_color_name = data.get("current_skin_name", "red")

        print("✔️ 載入成功！")

    except Exception as e:
        print(f"❌ 載入失敗: {e}")
        # 出錯時的保險機制
        for i in range(1, 19):
            config.current_levels[f"upgrade_p{i}"] = 0

    # 5. 更新運算後的屬性
    config.update_skill()
    config.apply_skin_effects()  # 記得執行這個，讓皮膚加成生效
    config.can_shoot = bool(config.now_skills.get("p15", 0))


def save_data():
    config.update_world_data(config.select_world)
    try:
        # 準備要寫入的資料，全部指向 config
        data = {
            "balance": int(config.total_points),
            "upgrades": config.current_levels,
            "records": config.longest_survived_time,
            "player_skins": config.player_skins,
            "now_player_skin": config.now_player_skin,
            "current_skin_name": config.current_player_color_name,
            "gm_i": config.gm_i,
            "has_buy_crazy": config.has_buy_crazy,
            "levels_unlocked": config.all_worlds_unlocked,  # 存入完整的字典
            "save_game_version": 3,  # 標記存檔版本，方便未來升級
            "select_world": config.select_world,
            "worlds_unlocked": config.worlds_unlocked,
        }

        # 使用 config 裡面的路徑
        with config.current_active_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # print("💾 存檔成功！")
    except Exception as e:
        print(f"❌ 存檔失敗: {e}")


def reset_pressing():
    for i in range(len(config.is_pressing)):
        config.is_pressing[i] = False


# 1. 先找出所有符合格式的存檔
all_saves = sorted(config.BASE_DIR.glob("save_game*.json"))

# 2. 判定優先順序
if (config.BASE_DIR / "save_game.json").exists():
    # 優先權 1：標準存檔
    active_save = config.BASE_DIR / "save_game.json"
elif all_saves:
    # 優先權 2：其他編號存檔 (例如 save_game_1.json)
    active_save = all_saves[0]
else:
    # 優先權 3：完全沒檔案，指向預設路徑（load_data 內部應處理沒檔案的情況）
    active_save = config.BASE_DIR / "save_game.json"


def check_data(path):
    """檢查存檔版本，並在需要時進行遷移"""
    if old_to_new.cheak_version(path):
        print("⚠️ 發現舊版本存檔，正在嘗試遷移格式...")
        old_to_new.migrate_save_format(path)


check_data(active_save)

# --- 關鍵修正：同步給 config ---
config.current_active_path = active_save

# 執行讀取
load_data(config.current_active_path)
config.load_resets()

# 補空位專區
leave_button = menu_button = restart_button = resume_button = lv_button = draw_button = levels_button = pygame.Rect(0, 0, 0, 0)
settings_button = upgrade_button = help_button = exit_button = player_rect = back_button = enemy_rect = pygame.Rect(0, 0, 0, 0)
next_world_button = pygame.Rect(0, 0, 0, 0)
level_button_color = tool備用.Colors.WHITE
target_y = 0
selected_save_name = ""
saved, loaded = False, False
loaded_data_success = False


def get_current_mouse_state():
    return pygame.mouse.get_pos(False), pygame.mouse.get_pressed()


current_time_sec = 0

# 隱藏滑鼠
pygame.mouse.set_visible(False)

pygame.mixer.music.play(-1)  # 這裡決定要不要播放背景音樂

while config.running:
    if config.freeze_timer > 0:
        config.freeze_timer -= 1
        dt = clock.tick(60 * config.FPS_Speed) / 1000.0
        continue  # 跳過這一次的移動和碰撞計算
    dt = clock.tick(60 * config.FPS_Speed) / 1000.0

    runed_time = pygame.time.get_ticks()
    # print(f"DEBUG: Current State = {config.game_state}")
    screen_text = f"Escape Them! v1.6.7 - {config.game_state.replace('_', ' ')}"
    if config.game_state.startswith("setting_p"):
        screen_text = f"Escape Them! v1.6.7 - setting p{config.game_state.replace('settings_p', '')} / 4"
    events = pygame.event.get()
    keys = pygame.key.get_pressed()
    mouse_pos, mouse_buttons = get_current_mouse_state()
    # 畫面震動
    if config.shake_timer > 0:
        config.current_range = int((config.shake_range * 2) * (config.shake_timer / config.total_shake_time))
        config.offset_x = random.randint(-config.current_range, config.current_range)
        config.offset_y = random.randint(-config.current_range, config.current_range)
        config.shake_timer -= 1
    else:
        config.offset_x, config.offset_y = 0, 0

    # 主畫面
    if config.game_state == "menu":
        screen.fill(tool備用.Colors.BLUE3)
        config.coin_rect()
        for i in range(2):
            config.alphas[i] = 255
        # if help_button.collidepoint(mouse_pos):
        #     help_button_color = tool.Colors.PINK
        # else:
        #     help_button_color = tool.Colors.PURPLE

        if config.title_img_loaded:
            screen.blit(config.title_img_surface, config.title_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.title_rect)

        if config.left_img_loaded:
            screen.blit(config.left_img_surface, config.left_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.left_rect)
        tool備用.show_text("settings", tool備用.Colors.WHITE, 40, 70, size=24, font_type="")
        if config.right_img_loaded:
            screen.blit(config.right_img_surface, config.right_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.right_rect)
        tool備用.show_text("upgrades", tool備用.Colors.WHITE, config.WIDTH - 120, 70, size=24, font_type="")

        levels_button = tool備用.text_button(
            "Press Me!" if levels_button.collidepoint(mouse_pos) else "Levels Select",
            tool備用.Colors.two_color_change(tool備用.Colors.BLACK, tool備用.Colors.WHITE, levels_button.collidepoint(mouse_pos)),
            tool備用.Colors.two_color_change(tool備用.Colors.GOLD, tool備用.Colors.DARK_GREEN, levels_button.collidepoint(mouse_pos)),
            0,
            220,
            300,
            70,
            b_center=True,
        )
        settings_button = tool備用.text_button(
            "Settings",
            tool備用.Colors.two_color_change(tool備用.Colors.BLACK, tool備用.Colors.WHITE, settings_button.collidepoint(mouse_pos)),
            tool備用.Colors.two_color_change(tool備用.Colors.GREEN, tool備用.Colors.BLUE2, settings_button.collidepoint(mouse_pos)),
            config.WIDTH // 2 - 150,
            310,
            140,
            70,
        )
        upgrade_button = tool備用.text_button(
            "Upgrades",
            tool備用.Colors.BLACK,
            tool備用.Colors.two_color_change(tool備用.Colors.ORANGE, tool備用.Colors.YELLOW, upgrade_button.collidepoint(mouse_pos)),
            config.WIDTH // 2 + 10,
            310,
            140,
            70,
        )
        help_button = tool備用.text_button("Help", tool備用.Colors.WHITE, tool備用.Colors.GRAY, 0, 400, 300, 70, b_center=True)
        # 做好時再改成紫色
        exit_button = tool備用.text_button(
            "Don't Leave!!!" if exit_button.collidepoint(mouse_pos) else "Leave",
            tool備用.Colors.WHITE,
            tool備用.Colors.two_color_change(tool備用.Colors.DARK_RED, tool備用.Colors.RED, exit_button.collidepoint(mouse_pos)),
            0,
            490,
            300,
            70,
            b_center=True,
        )
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if levels_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if settings_button.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if upgrade_button.collidepoint(mouse_pos):
                    is_pressing[2] = True
                if exit_button.collidepoint(mouse_pos):
                    is_pressing[3] = True
                if config.left_rect.collidepoint(mouse_pos):
                    is_pressing[4] = True
                if config.right_rect.collidepoint(mouse_pos):
                    is_pressing[5] = True

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 只有當先前「有在按鈕內按下」且「現在也在按鈕內放開」才觸發
                if levels_button.collidepoint(mouse_pos) and is_pressing[0]:
                    # reset_game()
                    config.game_state = "level_select"
                    config.reset_scroll_ys()
                if settings_button.collidepoint(mouse_pos) and is_pressing[1]:
                    config.game_state = "setting_p1"
                if upgrade_button.collidepoint(mouse_pos) and is_pressing[2]:
                    config.game_state = "upgrade_hub"
                if exit_button.collidepoint(mouse_pos) and is_pressing[3]:
                    config.running = False
                if config.left_rect.collidepoint(mouse_pos) and is_pressing[4]:
                    config.game_state = "setting_p1"
                if config.right_rect.collidepoint(mouse_pos) and is_pressing[5]:
                    config.game_state = "upgrade_hub"
                # 重置所有按鈕的按下狀態，確保下次點擊重新計算
                config.reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    config.running = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            config.game_state = "setting_p1"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            config.game_state = "upgrade_p1"
    # 難易度與最長存活時間
    elif config.game_state == "setting_p1":
        screen.fill(tool備用.Colors.BLUE3)
        config.coin_rect()
        current_world_key = f"world{config.select_world}"
        tool備用.show_text("Difficulty And Longest Served Time", tool備用.Colors.WHITE, 0, 60, size=34, screen_center=True)
        tool備用.show_text("Now Level:", tool備用.Colors.WHITE, 0, 110, size=30, screen_center=True)
        if config.from_pause:
            back_button_text = "back to pause"
        else:
            back_button_text = "back to menu"
        back_button = tool備用.text_button(back_button_text, tool備用.Colors.WHITE, tool備用.Colors.ORANGE, 0, 520, 200, 60, b_center=True)
        # 底色矩形
        # --- 難易度選擇框統一使用 tool.CR(pygame.Rect) 格式 ---
        easy_rect = tool備用.CR(
            pygame.Rect(70, 210, 450, 50),
            tool備用.Colors.GREEN if not config.from_pause else tool備用.Colors.GRAY,
            show=(config.game_mode == "easy"),
        )
        easy_rect.draw(screen)
        normal_rect = tool備用.CR(
            pygame.Rect(70, 270, 450, 50),
            tool備用.Colors.YELLOW if not config.from_pause else tool備用.Colors.GRAY,
            show=(config.game_mode == "normal"),
        )
        normal_rect.draw(screen)
        hard_rect = tool備用.CR(
            pygame.Rect(70, 330, 450, 50),
            tool備用.Colors.ORANGE if not config.from_pause else tool備用.Colors.GRAY,
            show=(config.game_mode == "hard"),
        )
        hard_rect.draw(screen)
        super_hard_rect = tool備用.CR(
            pygame.Rect(70, 390, 450, 50),
            tool備用.Colors.RED if not config.from_pause else tool備用.Colors.GRAY,
            show=(config.game_mode == "super_hard"),
        )
        super_hard_rect.draw(screen)
        crazy_rect = tool備用.CR(
            pygame.Rect(70, 450, 450, 50),
            tool備用.Colors.PURPLE if not config.from_pause else tool備用.Colors.GRAY,
            show=(config.game_mode == "crazy"),
        )
        crazy_rect.draw(screen)

        easy_info_btn = tool備用.text_button("info", tool備用.Colors.WHITE, tool備用.Colors.BLUE3, 540, 210, 60, 50)
        normal_info_btn = tool備用.text_button("info", tool備用.Colors.WHITE, tool備用.Colors.BLUE3, 540, 270, 60, 50)
        hard_info_btn = tool備用.text_button("info", tool備用.Colors.WHITE, tool備用.Colors.BLUE3, 540, 330, 60, 50)
        super_hard_info_btn = tool備用.text_button("info", tool備用.Colors.WHITE, tool備用.Colors.BLUE3, 540, 390, 60, 50)
        crazy_info_btn = tool備用.text_button("info", tool備用.Colors.WHITE, tool備用.Colors.BLUE3, 540, 450, 60, 50)
        # 顯示最長存活時間
        now_level_survived_time = config.longest_survived_time[current_world_key].get(config.selected_level, {})
        easy_time = now_level_survived_time.get("easy", 0)
        normal_time = now_level_survived_time.get("normal", 0)
        hard_time = now_level_survived_time.get("hard", 0)
        super_hard_time = now_level_survived_time.get("super_hard", 0)
        crazy_time = now_level_survived_time.get("crazy", 0)
        # print(f"DEBUG: now_level_survived_time = {now_level_survived_time}")

        # Easy Mode
        tool備用.show_text(
            f"easy mode: {tool備用.show_time_min(easy_time)}",
            tool備用.Colors.BLACK if config.game_mode == "easy" else tool備用.Colors.WHITE,
            0,
            220,
            screen_center=True,
        )
        # Normal Mode
        tool備用.show_text(
            f"normal mode: {tool備用.show_time_min(normal_time)}",
            tool備用.Colors.BLACK if config.game_mode == "normal" else tool備用.Colors.WHITE,
            0,
            280,
            screen_center=True,
        )
        # Hard Mode
        tool備用.show_text(
            f"hard mode: {tool備用.show_time_min(hard_time)}",
            tool備用.Colors.BLACK if config.game_mode == "hard" else tool備用.Colors.WHITE,
            0,
            340,
            screen_center=True,
        )
        # Super Hard Mode
        tool備用.show_text(
            f"super hard mode: {tool備用.show_time_min(super_hard_time)}",
            tool備用.Colors.BLACK if config.game_mode == "super_hard" else tool備用.Colors.WHITE,
            0,
            400,
            screen_center=True,
        )
        # Crazy Mode
        tool備用.show_text(
            f"crazy mode: {tool備用.show_time_min(crazy_time)}",
            tool備用.Colors.BLACK if config.game_mode == "crazy" else tool備用.Colors.WHITE,
            0,
            460,
            screen_center=True,
        )
        # select 按鈕
        easy_button = tool備用.text_button(
            "select", tool備用.Colors.BLACK, tool備用.Colors.GREEN if not config.from_pause else tool備用.Colors.GRAY, 70, 210, 130, 50
        )
        normal_button = tool備用.text_button(
            "select", tool備用.Colors.BLACK, tool備用.Colors.YELLOW if not config.from_pause else tool備用.Colors.GRAY, 70, 270, 130, 50
        )
        hard_button = tool備用.text_button(
            "select", tool備用.Colors.BLACK, tool備用.Colors.ORANGE if not config.from_pause else tool備用.Colors.GRAY, 70, 330, 130, 50
        )
        super_hard_button = tool備用.text_button(
            "select", tool備用.Colors.BLACK, tool備用.Colors.RED if not config.from_pause else tool備用.Colors.GRAY, 70, 390, 130, 50
        )
        crazy_button = tool備用.text_button(
            "select" if config.has_buy_crazy else config.crazy_btn_text,
            tool備用.Colors.BLACK,
            tool備用.Colors.PURPLE if not config.from_pause else tool備用.Colors.GRAY,
            70,
            450,
            130,
            50,
        )
        # --- 繪製箭頭 ---
        if config.right_img_loaded:
            screen.blit(config.right_img_surface, config.right_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.right_rect)
        if config.lock_img_loaded and not config.has_buy_crazy and not crazy_button.collidepoint(mouse_pos):
            screen.blit(config.lock_img_surface, (90, 430))
        if crazy_button.collidepoint(mouse_pos):
            crazy_btn_text = "$10000"
        else:
            crazy_btn_text = ""
        if config.maybe_cheat:
            level_button_color = tool備用.Colors.GRAY
        else:
            if config.game_mode == "easy":
                level_button_color = tool備用.Colors.GREEN
            elif config.game_mode == "normal":
                level_button_color = tool備用.Colors.YELLOW
            elif config.game_mode == "hard":
                level_button_color = tool備用.Colors.ORANGE
            elif config.game_mode == "super_hard":
                level_button_color = tool備用.Colors.RED
            elif config.game_mode == "crazy":
                level_button_color = tool備用.Colors.PURPLE
        lv_button = tool備用.text_button(
            config.selected_level.replace("level", "Lv. "), tool備用.Colors.BLACK, level_button_color, 0, 150, 180, b_center=True
        )
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if lv_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if back_button.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if config.right_rect.collidepoint(mouse_pos):
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
                if lv_button.collidepoint(mouse_pos) and not config.from_pause and is_pressing[0]:
                    # 1. 索引加 1
                    config.lv_i += 1

                    # 2. 循環邏輯
                    config.lv_i %= len(config.all_levels)

                    # 3. 更新當前選中的關卡字串
                    config.selected_level = config.all_levels[config.lv_i]
                if back_button.collidepoint(mouse_pos) and is_pressing[1]:
                    if config.from_pause:
                        config.game_state = "pause"
                    else:
                        config.game_state = "menu"
                if config.right_rect.collidepoint(mouse_pos) and is_pressing[2]:
                    config.game_state = "setting_p2"
                if (
                    (easy_button.collidepoint(mouse_pos) or easy_rect.rect.collidepoint(mouse_pos))
                    and not config.maybe_cheat
                    and is_pressing[3]
                ):
                    config.gm_i = 0
                    config.game_mode = "easy"
                if (
                    (normal_button.collidepoint(mouse_pos) or normal_rect.rect.collidepoint(mouse_pos))
                    and not config.maybe_cheat
                    and is_pressing[4]
                ):
                    config.gm_i = 1
                    config.game_mode = "normal"
                if (
                    (hard_button.collidepoint(mouse_pos) or hard_rect.rect.collidepoint(mouse_pos))
                    and not config.maybe_cheat
                    and is_pressing[5]
                ):
                    config.gm_i = 2
                    config.game_mode = "hard"
                if (
                    (super_hard_button.collidepoint(mouse_pos) or super_hard_rect.rect.collidepoint(mouse_pos))
                    and not config.maybe_cheat
                    and is_pressing[6]
                ):
                    config.gm_i = 3
                    config.game_mode = "super_hard"
                if (
                    (crazy_button.collidepoint(mouse_pos) or crazy_rect.rect.collidepoint(mouse_pos))
                    and not config.maybe_cheat
                    and is_pressing[7]
                ):
                    if config.has_buy_crazy:
                        config.gm_i = 4
                        config.game_mode = "crazy"
                    elif config.total_points >= 10000:
                        config.has_buy_crazy = True
                        config.total_points -= 10000
                if easy_info_btn.collidepoint(mouse_pos) and is_pressing[8]:
                    config.game_state = "more_survived_time"
                    target_y = 0 * config.one_mode_height
                if normal_info_btn.collidepoint(mouse_pos) and is_pressing[9]:
                    config.game_state = "more_survived_time"
                    target_y = 1 * config.one_mode_height + 30
                if hard_info_btn.collidepoint(mouse_pos) and is_pressing[10]:
                    config.game_state = "more_survived_time"
                    target_y = 2 * config.one_mode_height + 30
                if super_hard_info_btn.collidepoint(mouse_pos) and is_pressing[11]:
                    config.game_state = "more_survived_time"
                    target_y = 3 * config.one_mode_height + 30
                if crazy_info_btn.collidepoint(mouse_pos) and is_pressing[12]:
                    config.game_state = "more_survived_time"
                    target_y = 4 * config.one_mode_height + 30
                config.reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_s]:
                    config.game_state = "setting_p2"
            if event.type == pygame.MOUSEWHEEL:
                # 1. 索引加 1
                config.lv_i += 1 if event.y < 0 else -1

                # 2. 循環邏輯 (0 -> 1 -> 2 -> 3 -> 4 -> 0)
                config.lv_i %= len(config.all_levels)

                # 3. 更新當前選中的關卡字串
                config.selected_level = config.all_levels[config.lv_i]
    # 每關最長存活時間
    elif config.game_state == "more_survived_time":
        screen.fill(tool備用.Colors.BLUE3)
        config.coin_rect()
        current_world_key = f"world{config.select_world}"
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                target_y -= event.y * 30
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    config.game_state = "setting_p1"
                    config.reset_pressing()
        target_y = tool備用.num_range(0, target_y, config.max_scroll_y)  # 強制修正回合法範圍
        if config.scroll_ys[0] != target_y or not tool備用.in_range(0, config.scroll_ys[0], config.max_scroll_y):
            config.scroll_ys[0] += (target_y - config.scroll_ys[0]) * 0.1  # 每次移動剩下的 30%
        config.scroll_ys[0] = tool備用.num_range(0, config.scroll_ys[0], config.max_scroll_y)  # 強制修正回合法範圍
        draw_y = 110
        for gm in config.modes_config:
            if -10 < (draw_y - scroll_ys[0]) < config.HEIGHT + 10:
                tool備用.text_button(
                    f"{gm[0].replace('_', ' ').title()} Mode",
                    tool備用.Colors.BLACK if gm[0] == "easy" or gm[0] == "normal" else tool備用.Colors.WHITE,
                    gm[1],
                    0,
                    draw_y - config.scroll_ys[0],
                    270,
                    60,
                    size=34,
                    b_center=True,
                )
            draw_y += 90
            for level in config.all_levels:
                if -10 < (draw_y - scroll_ys[0]) < config.HEIGHT + 10:
                    tool備用.show_text(
                        f"Level {level.replace('level', '')}: {tool備用.show_time_min(config.longest_survived_time[current_world_key][level][gm[0]])}",
                        tool備用.Colors.WHITE,
                        0,
                        draw_y - config.scroll_ys[0],
                        screen_center=True,
                    )
                draw_y += 60
            draw_y -= 25

        config.max_scroll_y = max(0, draw_y - config.HEIGHT + 80)  # 計算最大可捲動範圍

        tool備用.text_button("All Levels Survived Time", tool備用.Colors.WHITE, tool備用.Colors.BLUE3, 0, 0, config.WIDTH, 70, size=34, b_center=True)
        pygame.draw.line(screen, tool備用.Colors.RED, (0, draw_y - config.scroll_ys[0]), (config.WIDTH, draw_y - config.scroll_ys[0]), 5)
        pygame.draw.rect(screen, tool備用.Colors.BLUE3, (0, config.HEIGHT - 70, config.WIDTH, 70))
        back_button = tool備用.text_button(
            "Back to Settings", tool備用.Colors.WHITE, tool備用.Colors.ORANGE, 0, config.HEIGHT - 65, 270, 60, size=28, b_center=True
        )
    # 存檔專區
    elif config.game_state == "setting_p2":
        screen.fill(tool備用.Colors.BLUE3)
        config.coin_rect()
        tool備用.show_text("Save and Load", tool備用.Colors.WHITE, 0, 80, size=50, screen_center=True)
        tool備用.show_text("We will save this file while you leave", tool備用.Colors.WHITE, 0, 140, size=24, screen_center=True)
        save_button = tool備用.text_button("Save File", tool備用.Colors.BLACK, tool備用.Colors.PINK, 0, 210, 200, 60, b_center=True)
        load_button = tool備用.text_button("Load File", tool備用.Colors.WHITE, tool備用.Colors.BLUE, 0, 290, 200, 60, b_center=True)
        open_other_button = tool備用.text_button("Open Other Save", tool備用.Colors.WHITE, tool備用.Colors.BLACK, 0, 370, 230, 60, b_center=True)
        if config.from_pause:
            back_button_text = "back to pause"
        else:
            back_button_text = "back to menu"
        back_button = tool備用.text_button(back_button_text, tool備用.Colors.WHITE, tool備用.Colors.ORANGE, 0, 490, 200, 60, b_center=True)
        # --- 繪製箭頭 ---
        if config.left_img_loaded:
            screen.blit(config.left_img_surface, config.left_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.left_rect)
        if config.right_img_loaded:
            screen.blit(config.right_img_surface, config.right_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.right_rect)
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
                if config.left_rect.collidepoint(mouse_pos):
                    is_pressing[4] = True
                if config.right_rect.collidepoint(mouse_pos):
                    is_pressing[5] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if save_button.collidepoint(mouse_pos) and is_pressing[0]:
                    saved = False
                    config.game_state = "saving_file"
                if load_button.collidepoint(mouse_pos) and is_pressing[1]:
                    loaded = False
                    config.game_state = "loading_file"
                if open_other_button.collidepoint(mouse_pos) and is_pressing[2]:
                    config.game_state = "choose_file"
                if back_button.collidepoint(mouse_pos) and is_pressing[3]:
                    if config.from_pause:
                        config.game_state = "pause"
                    else:
                        config.game_state = "menu"
                if config.left_rect.collidepoint(mouse_pos) and is_pressing[4]:
                    config.game_state = "setting_p1"
                if config.right_rect.collidepoint(mouse_pos) and is_pressing[5]:
                    config.game_state = "setting_p3"
                reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_w]:
                        config.game_state = "setting_p1"
                    if event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_s]:
                        config.game_state = "setting_p3"
    # 選擇其他存檔
    elif config.game_state == "choose_file":
        screen.fill(tool備用.Colors.BLUE3)
        config.coin_rect()
        # 列出所有存檔
        save_buttons = []
        for i, save in enumerate(config.save_files):
            btn = tool備用.text_button(
                save.stem, tool備用.Colors.WHITE, tool備用.Colors.BLUE2, 0, 150 + i * 70 - config.scroll_ys[1], 300, 60, b_center=True
            )
            save_buttons.append((btn, save))
        pygame.draw.rect(screen, tool備用.Colors.BLUE3, (0, config.HEIGHT - 110, config.WIDTH, 110))  # 擋住捲動後的檔案
        back_button = tool備用.text_button("Back to Settings", tool備用.Colors.WHITE, tool備用.Colors.ORANGE, 0, 510, 240, 60, b_center=True)
        pygame.draw.rect(screen, tool備用.Colors.BLUE3, (0, 0, config.WIDTH, 110))
        tool備用.show_text("Choose Save File", tool備用.Colors.WHITE, 0, 40, size=50, screen_center=True)
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
                # 回上一頁的邏輯
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    config.game_state = "setting_p2"

                # 處理存檔載入
                elif is_pressing[1] and selected_save_name:
                    # 檢查滑鼠是否還在對應的按鈕上 (避免按下去後滑開又觸發)
                    for btn, save in save_buttons:
                        if save == selected_save_name and btn.collidepoint(mouse_pos):
                            # 1. 確保它是 Path 物件，如果 save 本身已經是 Path 就不用包 Path()
                            # 但建議統一轉換成絕對路徑，最保險的做法是：
                            config.current_active_path = (
                                config.BASE_DIR / selected_save_name if isinstance(selected_save_name, str) else selected_save_name
                            )

                            check_data(config.current_active_path)

                            print(f"載入存檔: {config.current_active_path}")
                            config.game_state = "menu"  # 切換回選單
                            load_data(config.current_active_path)  # 傳入 Path 物件
                            config.load_resets()  # 重置遊戲狀態

                selected_save_name = None  # 重置
                reset_pressing()
        max_scroll_y = max(0, 150 + len(config.save_files) * 70 - config.HEIGHT + 110)  # 根據存檔數量計算最大捲動高度
        scroll_ys[1] = tool備用.num_range(0, scroll_ys[1], max_scroll_y)  # 強制修正回合法範圍
    # 玩家皮膚購買與更換
    elif config.game_state == "setting_p3":
        screen.fill(tool備用.Colors.BLUE3)
        config.coin_rect()
        start_x = 100  # 左邊起始位置
        start_y = 180  # 列表上方起始位置 (空出標題跟金幣的位置)
        row_gap = 80  # 每排之間的垂直距離
        col_gap = 180  # 如果一排想放多個，左右距離
        skin_list = list(config.player_skins.keys())

        draw_button = tool備用.text_button(
            "Not Enough Money!" if config.total_points <= 500 and draw_button.collidepoint(mouse_pos) else "Draw Skin ($500)",
            tool備用.Colors.WHITE,
            tool備用.Colors.two_color_change(tool備用.Colors.GRAY, config.draw_button_color, config.from_pause),
            180,
            100,
            190,
            40,
            size=22,
        )

        if draw_button.collidepoint(mouse_pos):
            config.draw_button_color = tool備用.Colors.GREEN if config.total_points >= 500 else tool備用.Colors.RED
        else:
            config.draw_button_color = tool備用.Colors.GOLD
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
                if config.left_rect.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if config.right_rect.collidepoint(mouse_pos):
                    is_pressing[2] = True
                if draw_button.collidepoint(mouse_pos):
                    is_pressing[3] = True
                # 檢查列表區域 (這裡標記 3 代表準備點擊皮膚)
                is_pressing[4] = True

            # C. 處理滑鼠放開 (觸發動作)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 如果放開時還在按鈕上，且當初是從按鈕按下的
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    config.game_state = "pause" if config.from_pause else "menu"

                if config.left_rect.collidepoint(mouse_pos) and is_pressing[1]:
                    config.game_state = "setting_p2"

                if config.right_rect.collidepoint(mouse_pos) and is_pressing[2]:
                    config.game_state = "setting_p4"

                if draw_button.collidepoint(mouse_pos) and is_pressing[3] and not config.from_pause:
                    if config.total_points >= 500:
                        config.total_points -= 500
                        # 1. 準備抽獎名單與權重
                        skin_names = []
                        weights = []
                        for name, data in config.player_skins.items():

                            if config.select_world >= data["can_get_world"]:
                                skin_names.append(name)
                                weights.append(data["draw_weight"])

                        # 2. 執行抽獎 (k=1 代表抽一個，回傳的是 list，所以要加 [0])
                        picked_name = random.choices(skin_names, weights=weights, k=1)[0]

                        # 3. 處理抽獎結果
                        skin = config.player_skins[picked_name]
                        if not skin["has_owned"]:
                            skin["has_owned"] = True
                            print(f"🎉 獲得新皮膚：{picked_name}！")
                            config.buy_channel.play(config.sounds["buy_success"])
                        else:
                            # 重複抽到，增加經驗值
                            skin["exp"] += 50
                            print(f"♻️ 重複抽到 {picked_name}，轉化為 50 EXP！")

                            target_exp = config.get_upgrade_threshold(skin["level"])

                            if skin["exp"] >= target_exp:
                                skin["exp"] -= target_exp
                                skin["level"] += 1
                                print(f"🆙 {picked_name} 升級了！目前 Lv.{skin['level']}")
                            config.buy_channel.play(config.sounds["buy_success"])
                            config.last_draw_color = picked_name
                        save_data()
                    else:
                        config.buy_channel.play(config.sounds["buy_error"])
                    config.apply_skin_effects()
                # 重要：如果剛才是按在列表區，放開時紀錄座標供皮膚列表判定
                if is_pressing[4]:
                    click_pos = mouse_pos
                reset_pressing()  # 清空所有 is_pressing 狀態
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_w]:
                    config.game_state = "setting_p2"
                if event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_s]:
                    config.game_state = "setting_p4"
        total_rows = (len(skin_list) + 1) // 2
        max_scroll = max(0, total_rows * row_gap - 300)
        scroll_ys[4] = tool備用.num_range(0, max_scroll, scroll_ys[4])
        # 繪製
        visible_skins = [name for name, data in config.player_skins.items() if config.select_world >= data["can_get_world"]]
        for i, t in enumerate(visible_skins):
            skin_val = config.player_skins[t]

            # --- 關鍵：動態計算 Y 座標 ---
            # 計算公式： 起始位置 + (第幾個 * 間距) - 捲動量
            # (i // 2) 代表一排兩個，如果你要一排一個就直接用 i
            calc_y = start_y + (i // 2) * row_gap - scroll_ys[4]
            calc_x = start_x + (i % 2) * col_gap

            # 3. 檢查「可視範圍」：只畫出在螢幕中間的按鈕，避免蓋到標題
            if 150 < calc_y < 500:
                # 決定按鈕顯示文字
                if config.from_pause:
                    display_text = f"{t} Lv.{skin_val['level']}"
                    btn_color = tool備用.Colors.GRAY
                elif skin_val["has_owned"]:
                    display_text = f"{t} Lv.{skin_val['level']}"
                    btn_color = skin_val["color"]
                else:
                    display_text = "???"
                    btn_color = tool備用.Colors.GRAY

                # 繪製按鈕並更新碰撞箱 (供點擊判定使用)
                # 注意：這裡把算好的 calc_y 傳進去
                btn_rect = tool備用.text_button(
                    display_text, config.skin_text_color[t]["text_col"], btn_color, calc_x, calc_y, 150, 50, size=22
                )
                # config.skin_unlocked_locks[t]["rect"] = btn_rect
                # print(config.skin_unlocked_locks[t])

                # 4. 繪製經驗條 (如果有擁有)
                if skin_val["has_owned"]:
                    bar_y = calc_y + 55
                    # 這裡呼叫剛剛定義的公式函數
                    max_needed = config.get_upgrade_threshold(skin_val["level"])

                    # 計算當前比例 (確保不超過 1.0)
                    ratio = min(1.0, skin_val["exp"] / max_needed)

                    # 繪製背景
                    pygame.draw.rect(screen, tool備用.Colors.BLACK, (calc_x, bar_y, 150, 5))
                    # 繪製綠色進度
                    pygame.draw.rect(screen, tool備用.Colors.GREEN, (calc_x, bar_y, 150 * ratio, 5))
                if click_pos and btn_rect.collidepoint(click_pos) and not config.from_pause:
                    if skin_val["has_owned"]:
                        config.current_player_color_name = t
                        config.now_player_skin = skin_val["color"]
                        config.apply_skin_effects()
                if t == config.current_player_color_name:
                    # 在按鈕外面畫一個白色的空心框 (width=3)
                    pygame.draw.rect(screen, tool備用.Colors.WHITE, btn_rect, 3)
        tool備用.show_text("Player Skins", tool備用.Colors.WHITE, 0, 50, screen_center=True, size=30)
        if config.left_img_loaded:
            screen.blit(config.left_img_surface, config.left_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.left_rect)
        if config.right_img_loaded:
            screen.blit(config.right_img_surface, config.right_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.right_rect)
        if config.from_pause:
            back_button_text = "back to pause"
        else:
            back_button_text = "back to menu"
        back_button = tool備用.text_button(back_button_text, tool備用.Colors.WHITE, tool備用.Colors.ORANGE, 0, 520, 200, 60, b_center=True)
        # 資料、皮膚顯示、預覽按鈕
        pygame.draw.line(screen, tool備用.Colors.WHITE, (450, 80), (450, config.HEIGHT - 100), 5)
        tool備用.show_text("Demo player:", tool備用.Colors.WHITE, 480, 60, size=30)
        show_rect = pygame.draw.rect(screen, config.now_player_skin, (560, 120, 30, 30))
        try_button = tool備用.text_button("Try to play", tool備用.Colors.WHITE, tool備用.Colors.PURPLE, 480, 400, 150, 40, size=20)
        pygame.draw.line(screen, tool備用.Colors.WHITE, (470, 460), (650, 460), 5)
        tool備用.show_text(
            f"You got 1 {config.last_draw_color} skin!",
            tool備用.Colors.get_color(config.last_draw_color) if config.last_draw_color is not None else tool備用.Colors.WHITE,
            470,
            475,
            size=20,
            show=(config.last_draw_color is not None),
        )
        # --- 右側：皮膚詳細資訊區 ---
        selected_name = config.current_player_color_name
        skin = config.player_skins[selected_name]

        # 1. 顯示皮膚大名
        tool備用.show_text(f"Skin: {selected_name.upper()}", tool備用.Colors.WHITE, 570, 170, size=26, center=True)

        # 2. 準備效果資料 (處理單一值或列表)
        effects = skin["effect"] if isinstance(skin["effect"], list) else [skin["effect"]]
        powers = skin["base_power"] if isinstance(skin["base_power"], list) else [skin["base_power"]]
        growths = skin["growth"] if isinstance(skin["growth"], list) else [skin["growth"]]
        level = skin["level"]

        # 3. 迴圈顯示每一項能力
        for i, (eff, base_p, grow) in enumerate(zip(effects, powers, growths, strict=False)):
            # 計算當前數值
            current_val = config.calculate_final_stat(eff, base_p, grow, level)

            # 格式化名稱 (例如 points_multiplier -> Points Multiplier)
            display_name = eff.replace("_", " ").title()

            # 繪製標題
            tool備用.show_text(f"• {display_name}:", tool備用.Colors.WHITE, 470, 210 + (i * 60), size=18)

            # 繪製數值 (保留兩位小數)
            val_text = f"{round(current_val, 2)}x"
            tool備用.show_text(val_text, tool備用.Colors.GREEN, 490, 235 + (i * 60), size=22)

            # 繪製成長率提示 (讓玩家知道升級加多少)
            if grow != 0:
                grow_text = f"(+{grow}/lv)" if grow > 0 else f"({grow}/lv)"
                tool備用.show_text(grow_text, tool備用.Colors.GRAY, 570, 238 + (i * 60), size=14)
    # 創新帳號
    elif config.game_state == "setting_p4":
        screen.fill(tool備用.Colors.BLUE3)
        tool備用.show_text("New File", tool備用.Colors.WHITE, 0, 50, screen_center=True, size=40)
        if config.left_img_loaded:
            screen.blit(config.left_img_surface, config.left_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.left_rect)
        if config.from_pause:
            back_button_text = "back to pause"
        else:
            back_button_text = "back to menu"
        back_button = tool備用.text_button(back_button_text, tool備用.Colors.WHITE, tool備用.Colors.ORANGE, 0, 520, 200, 60, b_center=True)
        new_button = tool備用.text_button("Open New File", tool備用.Colors.BLACK, tool備用.Colors.GREEN, 0, 150, 250, 60, b_center=True)
        tool備用.show_text(
            ["WARNING:", "If there is a file named 'save_game.json',", "then that file will be DELETED."],
            tool備用.Colors.RED,
            0,
            280,
            screen_center=True,
            size=30,
            line_gap=15,
        )
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
                if config.left_rect.collidepoint(mouse_pos):
                    is_pressing[1] = True
                # if config.right_rect.collidepoint(mouse_pos):
                #     is_pressing[2] = True
                if new_button.collidepoint(mouse_pos):
                    is_pressing[3] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    if config.from_pause:
                        config.game_state = "pause"
                    else:
                        config.game_state = "menu"
                if config.left_rect.collidepoint(mouse_pos) and is_pressing[1]:
                    config.game_state = "setting_p3"
                if new_button.collidepoint(mouse_pos) and is_pressing[3]:
                    # 2. 寫入檔案
                    try:
                        with open("save_game.json", "w", encoding="utf-8") as f:
                            json.dump(config.initial_data, f, indent=4)

                        # 成功寫入後才執行讀取與重置
                        load_data()
                        config.load_resets()

                        print("New game initialized successfully.")
                        config.game_state = "menu"

                    except Exception as e:
                        print(f"Error creating new save: {e}")
                        config.floating_texts.append(
                            tool備用.FloatingText(
                                "Failed to create new save!", 0, config.HEIGHT - 50, tool備用.Colors.RED, center=True, time=600, size=50
                            )
                        )

                    print("存檔已建立！")
                    config.game_state = "menu"
                reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_w]:
                    config.game_state = "setting_p3"
            for ft in config.floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
                ft.update()
                ft.draw(screen)
                if ft.timer <= 0:  # 如果文字壽命到了
                    config.floating_texts.remove(ft)

    # --------------------------遊戲資料儲存與匯入--------------------------------
    elif config.game_state == "saving_file":
        screen.fill(tool備用.Colors.PINK)
        cancel_button = tool備用.text_button(
            "Cancel",
            tool備用.Colors.WHITE,
            tool備用.Colors.RED_2,
            0,
            400,
            200,
            60,
            b_center=True,
            show=not saved,
        )
        # 確保有啟動計時器 (如果 collision_time 是 None)
        if tool備用.collision_time is None:
            tool備用.collision_time = runed_time
        current_time_sec = tool備用.sec_timer(update=True)
        passed_time = runed_time - tool備用.collision_time if tool備用.collision_time is not None else 0
        if passed_time < 4000:
            tool備用.show_text("Saving File...", tool備用.Colors.BLACK, 0, 150, 50, screen_center=True)
        elif 4000 <= passed_time < 7000:
            # 只在進入這個狀態的第一幀讀取一次檔案
            if not saved:
                save_data()
                saved = True
            tool備用.show_text("Successfully Saved!", tool備用.Colors.BLACK, 0, 150, 50, screen_center=True)
            tool備用.show_text(
                "File Name: save_game.json",
                tool備用.Colors.BLACK,
                0,
                200,
                50,
                screen_center=True,
            )
        elif passed_time > 7000:
            config.game_state = "setting_p2"
            tool備用.collision_time = None  # 重置，否則下次進遊戲會直接結束
            tool備用.reset_timer()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cancel_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if cancel_button.collidepoint(mouse_pos) and is_pressing[0]:
                    config.game_state = "setting_p2"
                    tool備用.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool備用.reset_timer()
    elif config.game_state == "loading_file":
        screen.fill(tool備用.Colors.BLUE)
        cancel_button = tool備用.text_button(
            "Cancel",
            tool備用.Colors.WHITE,
            tool備用.Colors.RED_2,
            0,
            400,
            200,
            60,
            b_center=True,
            show=not loaded,
        )
        # 確保有啟動計時器 (如果 collision_time 是 None)
        if tool備用.collision_time is None:
            tool備用.collision_time = runed_time
        current_time_sec = tool備用.sec_timer(update=True)
        passed_time = runed_time - tool備用.collision_time if tool備用.collision_time is not None else 0

        if passed_time < 3000:
            tool備用.show_text("Loading File...", tool備用.Colors.BLACK, 0, 150, 50, screen_center=True)
        elif 3000 <= passed_time < 6000:
            if not loaded:
                # 只在進入這個狀態的第一幀讀取一次檔案
                loaded_data_success = load_data()
                config.reset_game()
                loaded = True
            tool備用.show_text(
                "Successfully Loaded File" if loaded_data_success else "No Save File Found, Starting New Game.",
                tool備用.Colors.BLACK,
                0,
                150,
                50,
                screen_center=True,
            )
        elif passed_time >= 6000:  # 過了 5000 毫秒 (5秒)
            config.game_state = "settings_p"
            tool備用.collision_time = None  # 重置，否則下次進遊戲會直接結束
            tool備用.reset_timer()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if cancel_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if cancel_button.collidepoint(mouse_pos) and is_pressing[0]:
                    config.reset_game()
                    tool備用.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool備用.reset_timer()
                    if not config.from_pause:
                        config.game_state = "settings_p"
                    else:
                        config.game_state = "menu"
    # ----------------------------------------------------------------------------
    # 玩家升級：
    # 升級列表
    elif config.game_state == "upgrade_hub":
        current_config = config.UPGRADE_SURVIVAL if config.shop_page == "survival" else config.UPGRADE_COMBAT
        screen.fill(tool備用.Colors.BLUE3)
        config.update_upgrade_hub_layout()  # --- 繪製箭頭 ---
        if config.left_img_loaded:
            if config.l_img_show:
                screen.blit(config.left_img_surface, config.upgrade_left_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.upgrade_left_rect)
        if config.right_img_loaded:
            if config.r_img_show:
                screen.blit(config.right_img_surface, config.upgrade_right_rect)
        else:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.upgrade_right_rect)

        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                scroll_ys[2] -= event.y * 40
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if config.upgrade_left_rect.collidepoint(mouse_pos):
                    is_pressing[1] = True
                if config.upgrade_right_rect.collidepoint(mouse_pos):
                    is_pressing[2] = True
                for key, rect in config.upgrade_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        is_pressing[8] = True
                        target_key = key
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if config.upgrade_left_rect.collidepoint(mouse_pos) and config.l_img_show and is_pressing[1]:
                    config.shop_page = "survival"
                    config.l_img_show, config.r_img_show = False, True
                    config.update_upgrade_hub_layout()
                    scroll_ys[2] = 0
                if config.upgrade_right_rect.collidepoint(mouse_pos) and config.r_img_show and is_pressing[2]:
                    config.shop_page = "combat"
                    config.l_img_show, config.r_img_show = True, False
                    config.update_upgrade_hub_layout()
                    scroll_ys[2] = 0
                if is_pressing[8]:
                    # 再次確認放開時滑鼠還在該按鈕上
                    if config.upgrade_buttons.get(target_key) and config.upgrade_buttons[target_key].collidepoint(mouse_pos):
                        config.game_state = target_key  # 🌟 成功切換畫面！
                        scroll_ys[2] = 0  # 換頁時重置捲軸
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    config.game_state = "menu"
                    scroll_ys[2] = 0
                reset_pressing()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            scroll_ys[2] -= 20
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            scroll_ys[2] += 20

        # 限制捲動範圍
        scroll_ys[2] = max(0, min(scroll_ys[2], len(config.upgrade_hub_layout) * 100 - 350))

        # [簡化] 用一個迴圈搞定繪製與點擊感
        config.upgrade_buttons.clear()
        for i, (key, info) in enumerate(config.upgrade_hub_layout.items()):
            y = 130 + i * 100 - scroll_ys[2]
            if -80 < y < config.HEIGHT:
                rect = tool備用.text_button(
                    info["title"],
                    tool備用.Colors.BLACK,
                    info["color"],
                    0,
                    y,
                    500,
                    80,
                    size=26,
                    b_center=True,
                )
                # 🌟 把產生的 rect 存起來，對應它的 key (例如 upgrade_p1)
                config.upgrade_buttons[key] = rect

        # 全域重置：如果滑鼠放開了，不管在哪裡都要重置 pressing
        if not mouse_buttons[0]:
            is_pressing[8] = False

        # 固定底部的 BACK 按鈕
        pygame.draw.rect(screen, tool備用.Colors.BLUE3, (0, config.HEIGHT - 80, config.WIDTH, 80))
        back_button = tool備用.text_button("BACK TO MENU", tool備用.Colors.WHITE, tool備用.Colors.ORANGE, 0, config.HEIGHT - 70, 260, 50, b_center=True)
        tool備用.text_button("Upgrade Center", tool備用.Colors.WHITE, tool備用.Colors.BLUE3, 0, 0, 500, 100, size=50, b_center=True)
        tool備用.text_button(f"now_mode: {config.shop_page}", tool備用.Colors.WHITE, tool備用.Colors.BLUE3, 0, 90, 500, 40, size=35, b_center=True)
        config.coin_rect()
    # ✅ 通用升級頁面 (保留你的圖片、箭頭、按鈕樣式)
    elif config.game_state in config.UPGRADE_SURVIVAL or config.game_state in config.UPGRADE_COMBAT:
        current_config = config.UPGRADE_SURVIVAL if config.shop_page == "survival" else config.UPGRADE_COMBAT
        if config.game_state in config.UPGRADE_COMBAT:
            current_data_source = config.UPGRADE_COMBAT
        else:
            current_data_source = config.UPGRADE_SURVIVAL
        # 1. 抓取當前頁面的數據
        cfg = current_data_source[config.game_state]
        lvl = config.current_levels[config.game_state]
        costs = cfg["costs"]

        all_configs = {**config.UPGRADE_SURVIVAL, **config.UPGRADE_COMBAT}
        current_p_num = int(config.game_state.replace("upgrade_p", ""))
        total_pages = len(all_configs)

        # 2. 繪製背景與標題
        screen.fill(tool備用.Colors.BLUE3)

        # 偽代碼方向
        current_lv_color = tool備用.Colors.WHITE  # 預設白色

        if config.lv_flash_timer > 0:
            config.lv_flash_timer -= 1
            # 如果剩下偶數幀，就換個顏色（例如黃色或金色）
            if config.lv_flash_timer % 10 > 8:
                current_lv_color = tool備用.Colors.YELLOW

        # --- 標題文字 ---
        tool備用.show_text(cfg["title"], tool備用.Colors.WHITE, 0, 240, size=50, screen_center=True)
        tool備用.show_text(
            f"Level: Lv.{lvl + 1}",
            current_lv_color,
            0,
            300,
            size=40,
            screen_center=True,
        )
        tool備用.show_text(
            f"Balance: {tool備用.num_to_KMBT(round(config.total_points, 1))}$",
            tool備用.Colors.WHITE,
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
        elif config.get_key("upgrade_p15", cfg):
            display_text = f"Can Shoot: {bool(now_val)}"

        elif config.get_key("upgrade_p16", cfg):
            display_text = f"CD: {now_val / 1000}s"

        # 3. 判斷是否為普通數字 (int/float) -> 針對 Speed, Size...
        else:
            if (
                any([config.get_key("upgrade_p16", cfg), config.get_key("upgrade_p17", cfg), config.get_key("upgrade_p18", cfg)])
                and not config.can_shoot
            ):
                display_text = "You Had Not Buy 'Can Shoot'"
            # 這裡我們配合設定檔裡的 skill_desc
            # 例如 Speed 的 skill_desc 是 "Speed +{}"，這裡只要給數字就好
            else:
                display_text = cfg["skill_desc"].format(now_val)

        # 3. 針對 Regen 的特殊補強
        # 因為 Regen 的 skill_desc 我們設成了 "{}"，所以上面的 else 跑不到格式化
        # 我們手動加上前綴，讓它跟其他屬性看起來比較像
        if "upgrade_p7" in config.UPGRADE_SURVIVAL and cfg == config.UPGRADE_SURVIVAL["upgrade_p7"]:
            display_text = f"Regen: {display_text}"

        # 4. 最後畫在螢幕上
        # 注意：這裡直接顯示 display_text，不要再 format 一次了
        tool備用.show_text(f"Effect: {display_text}", tool備用.Colors.WHITE, 0, 400, size=25, screen_center=True)
        # --- 萬能數值顯示邏輯 (結束) ---

        if config.game_state == "upgrade_p20":
            tool備用.show_text("While you're playing, press 'T' to alto shoot!", tool備用.Colors.YELLOW, 0, 215, size=20, screen_center=True)

        # --- 保留你的圖片繪製邏輯 ---
        config.coin_rect()  # 繪製金幣圖示

        # 顯示標題圖片 (這裡假設你希望不同頁面顯示不同圖，或者共用一張)
        if config.title_img_loaded:
            screen.blit(config.title_img_surface, config.title_rect)

        # 3. 繪製左右箭頭 (邏輯簡化，樣式保留)
        # 左箭頭：不是第一頁才顯示
        if current_p_num > 1:
            if config.left_img_loaded:
                screen.blit(config.left_img_surface, config.left_rect)
            else:
                pygame.draw.rect(screen, tool備用.Colors.RED, config.left_rect)

        # 右箭頭：不是最後一頁才顯示
        if current_p_num < total_pages:
            if config.right_img_loaded:
                screen.blit(config.right_img_surface, config.right_rect)
            else:
                pygame.draw.rect(screen, tool備用.Colors.RED, config.right_rect)

        # 4. 購買按鈕邏輯 (計算價格與顏色)
        if lvl < len(costs):
            cost = costs[lvl]  # 取得當前等級價格

            # 判斷滑鼠是否懸停 & 錢夠不夠
            if upgrade_button.collidepoint(mouse_pos):
                if config.total_points >= cost:
                    btn_text = f"Buy! Left ${tool備用.num_to_KMBT(round(config.total_points - cost, 1))}"
                    btn_color = tool備用.Colors.GREEN
                else:
                    btn_text = f"Need: ${tool備用.num_to_KMBT(round(cost - config.total_points, 1))}"
                    btn_color = tool備用.Colors.RED
            else:
                btn_text = f"Cost: ${tool備用.num_to_KMBT(cost)}"
                btn_color = tool備用.Colors.YELLOW
        else:
            cost = None  # 滿級了
            btn_text = "MAX LEVEL"
            btn_color = tool備用.Colors.GRAY

        # 繪製按鈕 (Back 與 Upgrade) - 位置樣式不變
        if back_button.collidepoint(mouse_pos):
            back_btn_t_color, back_btn_color = tool備用.Colors.BLACK, tool備用.Colors.ORANGE2
        else:
            back_btn_t_color, back_btn_color = tool備用.Colors.WHITE, tool備用.Colors.ORANGE

        upgrade_button = tool備用.text_button(btn_text, tool備用.Colors.BLACK, btn_color, 0, 430, 350, 60, b_center=True)
        back_button = tool備用.text_button(
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
                if config.left_rect.collidepoint(mouse_pos):
                    is_pressing[2] = True
                if config.right_rect.collidepoint(mouse_pos):
                    is_pressing[3] = True

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                # 返回選單
                if is_pressing[0] and back_button.collidepoint(mouse_pos):
                    config.game_state = "menu"

                # 執行購買
                if upgrade_button.collidepoint(mouse_pos) and cost is not None and is_pressing[1]:
                    if config.total_points >= cost:
                        config.total_points -= cost
                        config.current_levels[config.game_state] += 1  # 🔥 更新等級字典
                        lv_flash_timer = 20  # 啟動閃爍計時器
                        save_data()  # 儲存
                        # print(f"Upgraded {config.game_state} to Lv.{current_levels[config.game_state] + 1}")
                        new_text = tool備用.FloatingText(
                            "-" + tool備用.num_to_KMBT(cost), config.WIDTH - 90, 20, tool備用.Colors.RED, speed=0.7, size=24
                        )
                        config.floating_texts.append(new_text)
                        config.buy_channel.play(config.sounds["buy_success"])
                        can_shoot = bool(config.now_skills["p15"])

                        config.now_flash_color = tool備用.Colors.GOLD
                        config.flash_timer = config.total_flash_time

                        config.update_skill()
                    else:
                        config.buy_channel.play(config.sounds["buy_error"])

                # 左切換
                if config.left_rect.collidepoint(mouse_pos) and current_p_num > 1 and is_pressing[2]:
                    config.game_state = f"upgrade_p{current_p_num - 1}"

                # 右切換
                if config.right_rect.collidepoint(mouse_pos) and current_p_num < total_pages and is_pressing[3]:
                    config.game_state = f"upgrade_p{current_p_num + 1}"

                reset_pressing()  # 重置按壓狀態
            if event.type == pygame.MOUSEWHEEL:
                if event.y < 0 and current_p_num < total_pages:
                    config.game_state = f"upgrade_p{current_p_num + 1}"
                elif event.y > 0 and current_p_num > 1:
                    config.game_state = f"upgrade_p{current_p_num - 1}"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT and current_p_num < total_pages:
                    config.game_state = f"upgrade_p{current_p_num + 1}"
                if event.key == pygame.K_LEFT and current_p_num > 1:
                    config.game_state = f"upgrade_p{current_p_num - 1}"
        # 鍵盤左右切換支援
        if keys[pygame.K_d] and current_p_num < total_pages:
            config.game_state = f"upgrade_p{current_p_num + 1}"
            pygame.time.delay(150)  # 防止切換太快
        if keys[pygame.K_a] and current_p_num > 1:
            config.game_state = f"upgrade_p{current_p_num - 1}"
            pygame.time.delay(150)
        for ft in config.floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                config.floating_texts.remove(ft)
    # ----------------------------------------------------------------------------
    # 關卡選擇
    elif config.game_state == "level_select":
        config.from_pause = False
        config.maybe_cheat = False
        current_world_key = f"world{config.select_world}"
        screen.fill(tool備用.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1))
        unlock_world_key = f"world{config.select_world + 1}"
        has_next_world = unlock_world_key in config.world_cost
        is_target_world_locked = config.levels_unlocked + 1 == len(config.current_world_costs)
        is_not_already_bought = config.select_world == config.worlds_unlocked
        clicked_pos = None
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_pos = event.pos
                if next_world_button.collidepoint(clicked_pos):
                    is_pressing[1] = True
                if config.left_rect.collidepoint(clicked_pos):
                    is_pressing[2] = True
                if config.right_rect.collidepoint(clicked_pos):
                    is_pressing[3] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if next_world_button.collidepoint(mouse_pos) and is_pressing[1]:
                    # 第一層保險：確保現在是「可購買」狀態（符合關卡進度）
                    if is_target_world_locked and is_not_already_bought:
                        unlock_world_key = f"world{config.select_world + 1}"
                        cost = config.world_cost.get(unlock_world_key, 999999999)

                        # 第二層保險：錢夠不夠
                        if config.total_points >= cost:
                            # 1. 扣錢
                            config.total_points -= cost
                            config.sounds["buy_success"].play()

                            # 2. 更新進度 (假設新世界解鎖後，解鎖關卡數要重置或累加)
                            # 這裡看你的設計，如果是世界跳轉，通常會解鎖下一大關
                            config.select_world = config.select_world + 1
                            config.worlds_unlocked += 1  # 更新已解鎖的世界數
                            config.update_current_world_data(config.select_world)
                            scroll_ys[3] = 0  # 切換世界時重置捲軸位置

                            # 3. 儲存進度 (非常重要，不然玩家重開遊戲會哭)
                            save_data()
                            game_state = "menu"
                        else:
                            # 錢不夠的處理 (例如播放錯誤音效)
                            config.sounds["buy_error"].play()
                if config.left_rect.collidepoint(mouse_pos) and is_pressing[2]:
                    config.select_world = max(1, config.select_world - 1)
                    config.update_current_world_data(config.select_world)
                    scroll_ys[3] = 0  # 切換世界時重置捲軸位置
                if config.right_rect.collidepoint(mouse_pos) and is_pressing[3]:
                    # 限制只能切換到已解鎖的世界
                    config.select_world = min(config.worlds_unlocked, config.select_world + 1)
                    config.update_current_world_data(config.select_world)
                    scroll_ys[3] = 0  # 切換世界時重置捲軸位置
            if event.type == pygame.MOUSEWHEEL:
                scroll_ys[3] -= event.y * 40
                # 假設每個按鈕高度+間距是 80 像素
                total_content_height = (len(config.current_world_costs) + 2) * 80 + 100

                # 最大捲動距離 = 總長度 減去 畫面高度 (600)
                max_scroll = max(0, total_content_height - config.HEIGHT)

                # 限制 scroll_y 在 0 到 max_scroll 之間
                scroll_ys[3] = tool備用.num_range(0, max_scroll, scroll_ys[3])
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    config.game_state = "menu"
                reset_pressing()
        config.update_current_world_data(config.select_world)
        for i in range(1, len(config.current_world_costs)):
            is_locked = i > config.levels_unlocked  # 這裡使用剛剛取出的數字
            is_next_level = i == config.levels_unlocked + 1
            level_button = tool備用.text_button(
                f"Level {i}",
                tool備用.Colors.WHITE,
                tool備用.Colors.BLUE if not is_locked else tool備用.Colors.GRAY,
                120,
                60 + i * 80 - scroll_ys[3],
                200,
                60,
            )
            pygame.draw.line(screen, tool備用.Colors.WHITE, (350, 100), (350, 500), 2)
            pygame.draw.line(screen, tool備用.Colors.WHITE, (50, 130 + i * 80 - scroll_ys[3]), (600, 130 + i * 80 - scroll_ys[3]), 2)
            prev_level_record = config.longest_survived_time[current_world_key].get(f"level{i - 1}", {}).get("normal", 0)
            required_time = config.current_world_need_record[i]
            tool備用.show_text(
                f"Need time: {tool備用.show_time_min(required_time)}",
                tool備用.Colors.two_color_change(tool備用.Colors.GREEN, tool備用.Colors.RED, prev_level_record >= required_time),
                380,
                80 + i * 80 - scroll_ys[3],
                size=18,
                show=is_locked,
            )

            draw_this_lock = is_locked
            if level_button.collidepoint(mouse_pos):
                if not is_locked:
                    pygame.draw.rect(screen, tool備用.Colors.GREEN, level_button, 3)
                elif is_next_level:
                    draw_this_lock = False
                    pygame.draw.rect(screen, tool備用.Colors.GRAY, level_button)
                    pygame.draw.rect(
                        screen,
                        tool備用.Colors.GREEN if config.total_points >= config.current_world_costs[i] else tool備用.Colors.RED,
                        level_button,
                        3,
                    )
                    # 顯示金額
                    display_cost = config.current_world_costs[i]
                    tool備用.show_text(
                        f"Unlock for ${tool備用.num_to_KMBT(display_cost)}",
                        tool備用.Colors.GREEN if config.total_points >= config.current_world_costs[i] else tool備用.Colors.RED,
                        220,
                        70 + i * 80 + 20 - scroll_ys[3],
                        center=True,
                        size=20,
                    )
            if draw_this_lock:
                # 圖層較高的鎖圖案
                if config.lock_img_loaded and is_locked:
                    screen.blit(config.lock_img_surface, (180, 60 + i * 80 - 20 - scroll_ys[3]))
                elif is_locked:
                    pygame.draw.rect(screen, tool備用.Colors.GRAY, (180, 60 + i * 80 - 20 - scroll_ys[3], 30, 30))
            # --- 3. 判斷點擊 ---
            if clicked_pos and level_button.collidepoint(clicked_pos):
                if not is_locked:
                    # 點擊成功的邏輯
                    config.selected_level = f"level{i}"
                    config.lv_i = i - 1
                    enemy_list, cannon_list, obstacle_list, level_multiplier, level_name = config.get_level_data(i, config.select_world)
                    config.reset_game()
                    config.game_state = "countdown"
                elif is_next_level and config.total_points >= config.current_world_costs[i] and prev_level_record >= required_time:
                    # 解鎖邏輯
                    config.total_points -= config.current_world_costs[i]
                    config.levels_unlocked = i  # 更新解鎖的關卡數
                    new_text = tool備用.FloatingText(
                        "-" + tool備用.num_to_KMBT(config.current_world_costs[i]), config.WIDTH - 90, 20, tool備用.Colors.RED, speed=0.7, size=24
                    )
                    config.floating_texts.append(new_text)
                    config.sounds["buy_success"].play()
                    config.update_world_data(config.select_world)  # 更新世界資料，確保下一次進入關卡選單時資料是最新的
                elif is_next_level:
                    config.sounds["buy_error"].play()
        if has_next_world and is_not_already_bought:
            next_world_button = tool備用.text_button(
                (
                    [
                        "Buy!" if config.total_points >= config.world_cost[unlock_world_key] else "Need More $",
                        f" ({"cost" if config.total_points >= config.world_cost[unlock_world_key] else "need"}: ${tool備用.num_to_KMBT(config.world_cost[unlock_world_key] - config.total_points)})",
                    ]
                    if next_world_button.collidepoint(mouse_pos) and is_target_world_locked and is_not_already_bought
                    else ["Next World ", f"(cost: ${tool備用.num_to_KMBT(config.world_cost[unlock_world_key])})"]
                ),
                tool備用.Colors.WHITE,
                (
                    tool備用.Colors.two_color_change(
                        tool備用.Colors.two_color_change(
                            tool備用.Colors.GREEN,
                            tool備用.Colors.RED,
                            config.total_points >= config.world_cost[unlock_world_key] and is_target_world_locked,
                        ),
                        tool備用.Colors.two_color_change(tool備用.Colors.CHARTREUSE, tool備用.Colors.GRAY, is_target_world_locked),
                        next_world_button.collidepoint(mouse_pos),
                    )
                    if is_target_world_locked or is_not_already_bought
                    else tool備用.Colors.GRAY
                ),
                120,
                60 + len(config.current_world_costs) * 80 - scroll_ys[3],
                200,
                60,
                t_y=(
                    85 + len(config.current_world_costs) * 80 - scroll_ys[3]
                    if next_world_button.collidepoint(mouse_pos)
                    and is_target_world_locked
                    and config.total_points >= config.world_cost[unlock_world_key]
                    else 80 + len(config.current_world_costs) * 80 - scroll_ys[3]
                ),  #
                size=(
                    24
                    if next_world_button.collidepoint(mouse_pos)
                    and is_target_world_locked
                    and config.total_points >= config.world_cost[unlock_world_key]
                    else 22
                ),
            )
        elif not has_next_world:
            next_world_button = tool備用.text_button(
                ["Stay tuned", " for new worlds!"],
                tool備用.Colors.WHITE,
                tool備用.Colors.GRAY,
                120,
                60 + len(config.current_world_costs) * 80 - scroll_ys[3],
                200,
                60,
                t_y=80 + len(config.current_world_costs) * 80 - scroll_ys[3],
                size=20,
            )
        else:
            next_world_button = tool備用.text_button(
                "Has Unlocked",
                tool備用.Colors.WHITE,
                tool備用.Colors.GRAY,
                120,
                60 + len(config.current_world_costs) * 80 - scroll_ys[3],
                200,
                60,
                size=26,
            )

        tool備用.show_text("Normal mode", tool備用.Colors.WHITE, 400, 160 - scroll_ys[3], size=20)
        pygame.draw.rect(
            screen,
            tool備用.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1),
            (0, 0, config.WIDTH, 100),
        )
        tool備用.show_text("Level Select", tool備用.Colors.WHITE, 0, 40, size=50, screen_center=True)

        config.coin_rect()

        pygame.draw.rect(
            screen,
            tool備用.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1),
            (0, config.HEIGHT - 100, config.WIDTH, 100),
        )

        if config.left_img_loaded and config.select_world > 1:
            screen.blit(config.left_img_surface, config.left_rect)
        elif not config.left_img_loaded:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.left_rect)
        if config.right_img_loaded and config.select_world < config.worlds_unlocked:
            screen.blit(config.right_img_surface, config.right_rect)
        elif not config.right_img_loaded:
            pygame.draw.rect(screen, tool備用.Colors.RED, config.right_rect)

        back_button = tool備用.text_button("Back to Menu", tool備用.Colors.WHITE, tool備用.Colors.ORANGE, 0, config.HEIGHT - 80, 200, 60, b_center=True)

        # 更新並繪製所有飄浮文字
        for ft in config.floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                config.floating_texts.remove(ft)
    # 倒數前五秒
    elif config.game_state == "countdown":
        screen.fill(tool備用.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1))

        config.coin_rect()
        passed_time, _ = tool備用.sec_timer(update=True, dt=dt)
        countdown = 3 - passed_time  # 倒數 3 秒

        config.player_move(keys)

        tool備用.show_text(level_name, tool備用.Colors.WHITE, 0, 80, screen_center=True, size=40)

        if countdown >= 1:
            countdown_text = str(int(countdown))
            screen_text = f"Escape Them! v1.6.7 - {countdown}!"
        elif countdown >= 0:
            countdown_text = "GO!"
            screen_text = "Escape Them! v1.6.7 - GO!"
        else:
            tool備用.sec_timer(update=False)
            tool備用.reset_timer()
            config.game_state = "start_game"

        player_rect = pygame.draw.rect(screen, config.player_color, config.player_rect)

        tool備用.show_text(countdown_text, tool備用.Colors.WHITE, 0, config.HEIGHT // 2 - 150, screen_center=True, size=300)

        for event in events:
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                countdowning = True
                config.game_state = "pause"
    # 主遊戲程式
    elif config.game_state == "start_game":
        screen_text = "Escape Them! v1.6.7 - Escaping"
        screen.fill(tool備用.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1))
        config.coin_rect(player_rect)
        countdowning = False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    config.game_state = "pause"
                if event.key == pygame.K_t and config.now_skills["p20"]:
                    config.alto_shoot = not config.alto_shoot
        should_update = config.freeze_timer <= 0
        current_time_sec, current_time_ms = tool備用.sec_timer(update=should_update, dt=dt)

        keys = pygame.key.get_pressed()
        player_rect.x, player_rect.y = config.player_move(keys)

        if mouse_buttons[0] or (config.alto_shoot and config.now_skills["p20"]):  # 如果按住左鍵或有自動射擊
            if runed_time - config.last_shot_time > config.now_skills["p16"] and config.can_shoot:
                # 計算玩家中心到滑鼠的角度
                dx = mouse_pos[0] - config.player_rect.centerx
                dy = mouse_pos[1] - config.player_rect.centery
                angle = math.atan2(dy, dx)

                # 產生新子彈
                new_bullet = config.Player_Bullet(config.player_rect.centerx, config.player_rect.centery, angle)
                config.player_bullets.append(new_bullet)
                config.last_shot_time = runed_time

        for p_bullet in config.player_bullets[:]:  # 使用 [:] 副本以便在迴圈中刪除
            pb_rect = p_bullet.update()
            if not p_bullet.active:
                config.player_bullets.remove(p_bullet)
            else:
                p_bullet.draw(screen)
            for enemy in enemy_list:  # 假設你的敵人清單叫 enemy_list
                e_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)

                if all([pb_rect.colliderect(e_rect), enemy.show, "chaser" not in enemy.types, enemy.mode == "attack"]):
                    # 撞到了！
                    if p_bullet in config.player_bullets:
                        config.player_bullets.remove(p_bullet)  # 子彈消失
                    config.shoot_point += config.now_skills["p19"]  # 加分
                    # print("shoot!")
                    break
            for e_bullet in config.bullet_list[:]:
                eb_rect = pygame.Rect(e_bullet.x - config.offset_x, e_bullet.y - config.offset_y, 25, 25)
                if pb_rect.colliderect(eb_rect) and not e_bullet.is_exploding:
                    if p_bullet in config.player_bullets:
                        config.player_bullets.remove(p_bullet)
                    # 標記敵人子彈「原地爆炸」
                    e_bullet.is_exploding = True
                    config.shoot_point += config.now_skills.get("p19", 0) * 2
                    break

        # 怪物特殊處理(包含怪物分裂)
        new_enemies = []
        for enemy in enemy_list[:]:
            if enemy.should_split and not enemy.is_split_enemy:
                if enemy.split_enemys > 1:
                    step = config.total_spread / (enemy.split_enemys - 1)
                else:
                    step = 0
                # 產生很多隻隻小怪
                for i in range(enemy.split_enemys):
                    # 讓小怪的角度稍微偏轉，看起來像彈開
                    offset = (i * step) - (config.total_spread / 2)
                    new_angle = (enemy.angle + offset) % 360

                    # 建立小怪實體
                    child = config.Enemy(
                        show_time=current_time_sec,  # 讓它立刻出現
                        speed=enemy.normal_speed * 1.2,  # 小怪動快一點點增加難度
                        slow_speed=enemy.slow_speed,
                        color=enemy.color,
                        angle_range=(int(new_angle), int(new_angle)),  # 固定它的初始角度
                        size=enemy.width / 4,  # 讓它變小 (原本 size 是傳入建構子算的)
                        damage=enemy.damage * 0.5,  # 傷害減半
                        types=enemy.types,  # 繼承原本的型態 (包含 "break")
                        is_split_enemy=True,  # 重要：標記它是小怪，避免再次分裂
                    )
                    # 繼承大怪的位置與方向感
                    child.x, child.y = enemy.x, enemy.y
                    child.x_dir, child.y_dir = enemy.x_dir, enemy.y_dir
                    if child.x <= 0:
                        child.x_dir = 1
                    if child.x >= config.WIDTH - child.width:
                        child.x_dir = -1

                    # 為了避免重疊，讓小怪出生位置往場內推一點
                    child.x = enemy.x + (15 * child.x_dir)
                    child.y = enemy.y + (15 * child.y_dir)
                    child.mode = "attack"  # 跳過 spawning 直接開打

                    new_enemies.append(child)
                enemy.should_split = False
                continue  # 下一位
            if enemy.is_dead:
                enemy_list.remove(enemy)
        enemy_list.extend(new_enemies)

        # 怪物碰撞
        config.buffer_duration = config.now_skills["p5"] * config.buffer_duration_buff
        for enemy in enemy_list:

            # 處理死亡移除
            if enemy.is_dead:
                enemy_list.remove(enemy)
                continue
            e_rect = enemy.update(current_time_ms, current_time_sec, config.player_rect, mouse_pos, config.now_treasure, screen)

            if enemy.show and e_rect is not None:
                if (
                    enemy.mode == "attack"
                    and config.player_rect.colliderect(e_rect)
                    and current_time_sec - config.last_hit_time > config.invincible_duration
                ):
                    damage_taken = int(enemy.damage * config.enemy_damage_buff * config.skin_enemy_damage_buff)
                    damage_multiplier, text_color, text_content, dodged = config.calculate_damage(damage_taken)

                    if not dodged:
                        config.shake_timer = 10
                        config.total_shake_time = 10
                        config.shake_range = damage_taken
                        config.max_alpha = min(255, 100 + damage_taken)

                    config.flash_timer = config.total_flash_time
                    config.freeze_timer = max(2, damage_taken // 1.5)
                    config.now_flash_color = tool備用.Colors.RED if not dodged else tool備用.Colors.YELLOW

                    # 統一計算最後傷害
                    final_damage = int(damage_taken * damage_multiplier)
                    config.player_hp -= max(1, final_damage)

                    # 更新時間與音效
                    config.last_hit_time = current_time_sec
                    config.sounds["hurt"].play()

                    # 顯示漂浮文字 (帶入剛才判斷好的內容)
                    config.floating_texts.append(
                        tool備用.FloatingText(
                            text_content, player_rect.x - 20 if dodged else player_rect.x, player_rect.y, text_color, speed=0.5, time=120
                        )
                    )

                pygame.draw.rect(screen, enemy.color, e_rect)
        # 大砲邏輯
        for cannon in cannon_list:
            spawn_start_time = int(cannon["show_time"] * config.spawn_time_debuff)

            attack_start_time = spawn_start_time + config.buffer_duration
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

            c_rect = pygame.Rect(cannon["x"] - config.offset_x, cannon["y"] - config.offset_y, cannon["width"], cannon["height"])

            if cannon["mode"] == "spawning":
                if current_time_ms % 500 < 250:
                    pygame.draw.rect(screen, cannon["color"], c_rect)
                continue
            elif cannon["mode"] == "attack":
                if cannon["type"] == "X_move":
                    c_rect_dx = cannon["move_speed"] * config.mode_speed_buff * cannon["move_dir"]
                    cannon["x"] += c_rect_dx

                    c_rect.x = cannon["x"]
                    if c_rect.left <= 0:
                        cannon["move_dir"] *= -1
                        cannon["x"] = 2
                        c_rect.x = cannon["x"]
                    if c_rect.right >= config.WIDTH:
                        cannon["move_dir"] *= -1
                        cannon["x"] = config.WIDTH - cannon["width"] - 1
                        c_rect.x = cannon["x"]
                elif cannon["type"] == "Y_move":
                    c_rect_dy = cannon["move_speed"] * config.mode_speed_buff * cannon["move_dir"]
                    cannon["y"] += c_rect_dy

                    c_rect.y = cannon["y"]
                    if c_rect.top <= 0:
                        cannon["move_dir"] *= -1
                        cannon["y"] = 2
                        c_rect.y = cannon["y"]
                    if c_rect.bottom >= config.HEIGHT:
                        cannon["move_dir"] *= -1
                        cannon["y"] = config.HEIGHT - cannon["height"]
                        c_rect.y = cannon["y"]
                elif cannon["type"] == "track":
                    # 修正：應該是「加」offset，且修正變數名 centery
                    player_vec = pygame.math.Vector2(player_rect.center)
                    cannon_vec = pygame.math.Vector2(c_rect.center)
                    v = player_vec - cannon_vec
                    time_passed = current_time_ms - cannon["last_fire_time"]
                    total_cooldown = cannon["fire_rate"] / config.mode_speed_buff
                    if time_passed > (total_cooldown / 2):
                        # 算出剩下的時間比例 (0.0 到 0.5 之間)
                        # 越接近發射，閃爍頻率可以越快
                        flicker_speed = 100
                        if time_passed > (total_cooldown * 0.8):  # 最後 20% 時間閃超快
                            flicker_speed = 50

                        if (runed_time // flicker_speed) % 2 == 0:
                            pygame.draw.line(screen, tool備用.Colors.RED, cannon_vec, player_vec, 3)
                    dist, angle = v.as_polar()
                    cannon["angle"] = angle
                draw_c_rect = c_rect.copy()
                draw_c_rect.x += config.offset_x
                draw_c_rect.y += config.offset_y

                pygame.draw.rect(screen, cannon["color"], draw_c_rect)
                if (current_time_ms - cannon["last_fire_time"]) > cannon["fire_rate"] / config.mode_speed_buff:
                    bullet_x = c_rect.centerx - 12
                    bullet_y = c_rect.centery - 12
                    config.bullet_list.append(
                        config.make_bullet(
                            bullet_x,
                            bullet_y,
                            cannon["angle"],
                            cannon["bullet_speed"],
                            cannon["bom_range"],
                            cannon["color"],  # 🌟 補上顏色
                            cannon["damage"],  # 🌟 補上傷害值
                            type=cannon["bullet_type"],  # 🌟 補上子彈類型
                        )
                    )
                    config.shoot_channel.play(config.sounds["shoot"])
                    cannon["last_fire_time"] = current_time_ms
        # 子彈更新與繪製
        for bullet in config.bullet_list[:]:
            status, b_rect = bullet.update(player_rect)

            if status == "REMOVE":
                config.bullet_list.remove(bullet)
                continue  # 跳過這顆子彈，不執行下方的 draw

            if not bullet.has_dealt_bom_damage:
                trigger_damage = False

                if status == "HIT" and bullet.collide_player:
                    # 🌟 撞擊瞬間：無視距離，直接觸發
                    trigger_damage = True

                elif bullet.is_exploding:
                    # 🌟 爆炸期間：偵測玩家是否「走進」紅圈
                    dist = math.hypot(player_rect.centerx - bullet.x, player_rect.centery - bullet.y)
                    if dist < (bullet.current_bom_radius + 20):  # +20 是緩衝範圍
                        trigger_damage = True

                # 4. 執行扣血與特效 (如果觸發成功且不在無敵時間)
                if trigger_damage and current_time_sec - config.last_hit_time > config.invincible_duration:
                    # 計算傷害 (根據你的公式)
                    damage_taken = int(bullet.damage * config.enemy_damage_buff * config.skin_enemy_damage_buff)
                    damage_multiplier, text_color, text_content, dodged = config.calculate_damage(damage_taken)

                    if not dodged:
                        config.shake_timer = 10
                        config.total_shake_time = 10
                        config.shake_range = damage_taken
                        config.player_hp -= max(1, int(damage_taken * damage_multiplier))
                        config.max_alpha = min(255, 100 + max(1, int(damage_taken * damage_multiplier)))

                    config.flash_timer = config.total_flash_time
                    config.freeze_timer = max(2, damage_taken // 1.5)
                    config.now_flash_color = tool備用.Colors.RED if not dodged else tool備用.Colors.YELLOW

                    config.sounds["hurt"].play()

                    # 產生漂浮文字
                    config.floating_texts.append(
                        tool備用.FloatingText(text_content, player_rect.x, player_rect.y, text_color, speed=0.5, time=120)
                    )

                    # 🌟 重要：標記這顆子彈已經傷過人了，這一顆就不會再觸發
                    bullet.has_dealt_bom_damage = True
                    config.last_hit_time = current_time_sec

            # 5. 繪製子彈 (不管是飛行中還是爆炸中)
            bullet.draw(screen, config.offset_x, config.offset_y)

        # 獲取目前的磁鐵範圍
        magnet_range = config.now_skills["p9"]  # 直接使用升級後的磁鐵範圍數值

        # 寶藏出現邏輯
        # 只有在「現在沒顯示」且「冷卻時間到了」才執行
        if not config.now_treasure["show"] and current_time_sec >= config.now_treasure["next_spawn_at"]:
            # [步驟 A] 抽籤：決定這次出現的稀有度
            rolled_rarity = random.choice(config.coin_chance)

            # [步驟 B] 變身：根據抽到的稀有度，去找模板來覆蓋 now_treasure
            template = next((t for t in config.treasures if t["rarity"] == rolled_rarity), config.treasures[0])

            config.now_treasure["rarity"] = template["rarity"]
            config.now_treasure["color"] = template["color"]
            config.now_treasure["add_points"] = template["add_points"]

            # [步驟 C] 定位並顯示
            config.now_treasure["x"] = random.randint(50, config.WIDTH - 50)
            config.now_treasure["y"] = random.randint(50, config.HEIGHT - 50)
            config.now_treasure["show"] = True

        # 寶藏碰撞與繪製
        if config.now_treasure["show"]:
            # 1. 【磁鐵邏輯】放在這裡！錢幣顯示時才吸引
            magnet_range = config.now_skills["p9"]  # 直接使用升級後的磁鐵範圍數值

            player_vec = pygame.math.Vector2(player_rect.center)
            coin_vec = pygame.math.Vector2(config.now_treasure["x"] + 15, config.now_treasure["y"] + 15)
            distance = player_vec.distance_to(coin_vec)

            if distance < magnet_range:
                config.trying_to_touch_player = True
            if config.trying_to_touch_player:
                move_vec = player_vec - coin_vec
                if move_vec.length() > 0:
                    # 速度可以設為 5，或是根據玩家速度調整
                    config.now_treasure["x"] += move_vec.x * (0.05 * config.now_skills["p10"])
                    config.now_treasure["y"] += move_vec.y * (0.05 * config.now_skills["p10"])
                pygame.draw.line(
                    screen,
                    (*tool備用.Colors.GOLD, 150),  # 金色 (或是用 tool.Colors.GOLD)
                    player_vec,  # 玩家位置
                    coin_vec,  # 錢幣位置
                    2,  # 線條粗度
                )

            # 2. 繪製圖片 (使用更新後的 x, y)
            now_treasure_rarity = config.now_treasure["rarity"].lower()
            screen.blit(
                config.COIN_IMAGES[now_treasure_rarity],
                (config.now_treasure["x"] - config.offset_x, config.now_treasure["y"] - config.offset_y),
            )

            # 3. 更新碰撞盒並偵測碰撞
            t_rect = config.COIN_IMAGES[now_treasure_rarity].get_rect(topleft=(config.now_treasure["x"], config.now_treasure["y"]))

            if player_rect.colliderect(t_rect):
                config.trying_to_touch_player = False  # 碰到玩家後重置，下一次出現才會再吸引
                # 播放音效
                if now_treasure_rarity in ["exotic", "divine"]:
                    config.sounds["epic_coin"].play()
                    config.shake_range = 10
                    config.shake_timer = 20
                    config.total_shake_time = 20
                    config.now_flash_color = tool備用.Colors.BLUE
                    config.flash_timer = config.total_flash_time
                else:
                    config.sounds["coin"].play()
                # 1. 計算分數
                min_p, max_p = (add * config.coin_multiplier * config.now_skills["p12"] for add in config.now_treasure["add_points"])
                base_val = random.uniform(min_p, max_p)

                config.treasure_points += base_val

                display_val = f"{round(base_val * config.gm_points_buff * config.now_skills['p3'] * level_multiplier, 1):g}"

                coin_text = tool備用.FloatingText(f"+${display_val}", player_rect.x, player_rect.y, tool備用.Colors.GOLD)
                config.floating_texts.append(coin_text)

                # 3. 消失並設定「下一次」出現的時間
                config.now_treasure["show"] = False
                cooldown = random.randint(*config.next_spawn_range)  # type: ignore
                reduction = config.now_skills["p2"]
                config.now_treasure["next_spawn_at"] = current_time_sec + max(2, int(cooldown - reduction))
            for enemy in enemy_list:
                if "eat_coin" in enemy.types and enemy.mode == "attack" and enemy.show:
                    cooldown = random.randint(*config.next_spawn_range)  # type: ignore
                    reduction = config.now_skills["p2"]
                    e_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                    if e_rect.colliderect(t_rect):
                        config.now_treasure["show"] = False
                        config.now_treasure["next_spawn_at"] = current_time_sec + max(1, int(cooldown - reduction))
                        config.trying_to_touch_player = False
                        config.sounds["steal"].play()
                    enemy.x = tool備用.num_range(0, config.WIDTH - enemy.width, enemy.x)
                    enemy.y = tool備用.num_range(0, config.HEIGHT - enemy.height, enemy.y)

        # --- 玩家血量回復 ---
        # 1. 確保只有在血量未滿且玩家還活著時才計算
        if config.player_hp < config.player_max_hp and config.player_hp > 0:
            # 2. 改用 >= 判斷，確保每隔指定秒數觸發一次
            if current_time_sec - config.last_cure_time >= config.now_skills["p7"]["time"]:
                config.player_hp += config.now_skills["p7"]["hp"]

                # 3. 修正：為了讓計時更準確，last_cure_time 應該加上冷卻時間，而不是直接等於當前時間
                config.last_cure_time += config.now_skills["p7"]["time"]

                new_text = tool備用.FloatingText(
                    (
                        f"+{config.now_skills['p7']['hp']}hp"
                        if config.player_max_hp >= config.player_hp
                        else f"+{int(config.now_skills['p7']['hp'] - (config.player_hp - config.player_max_hp))}hp"
                    ),
                    player_rect.x,
                    player_rect.y,
                    tool備用.Colors.GREEN,
                    speed=0.8,
                )
                config.floating_texts.append(new_text)
                config.now_flash_color = tool備用.Colors.GREEN
                config.flash_timer = config.total_flash_time
                # 4. 確保不溢出
                if config.player_hp > config.player_max_hp:
                    config.player_hp = config.player_max_hp
            if config.Invincible:
                config.player_hp += 1
        else:
            # 如果血量滿了，持續更新 last_cure_time 讓計時器「對齊」當前時間
            # 這樣受傷的一瞬間才會重新開始計時，而不是受傷後馬上秒回
            config.last_cure_time = current_time_sec

        # 心跳音效
        hp_percent = config.player_hp / config.player_max_hp
        if hp_percent <= 0.2:
            target_sound = config.sounds["fast_heart_beat"]
            target_vol = 0.05
        elif hp_percent <= 0.5:
            target_sound = config.sounds["slow_heart_beat"]
            target_vol = 0.3
        else:
            target_sound = None
            target_vol = 0.5
        if target_sound != config.current_heart:
            if target_sound:
                config.heart_channel.play(target_sound, loops=-1)
            else:
                config.heart_channel.stop()

            config.current_heart = target_sound

        # --- AFK 偵測邏輯 ---
        # 檢查玩家當前位置是否與上一幀相同
        player_pos = (player_rect.x, player_rect.y)
        if enemy_list[2].show:
            if player_pos == config.last_player_pos:
                # 位置沒變，累計時間（1 / FPS）
                config.afk_timer += 1 / 60
            else:
                # 位置變了，重置計時器
                config.afk_timer = 0
                config.last_player_pos = player_pos
            # 3. 如果發呆超過 10 秒
            if config.afk_timer >= config.AFK_LIMIT:
                config.reset_game()
                config.game_state = "afk_kick"

        # 更新畫面、繪製物件
        base_hp_rect = tool備用.text_button(
            "", tool備用.Colors.WHITE, tool備用.Colors.DARK_RED, config.WIDTH - 110, 70, 100, 23, t_y=82, size=15, alpha=config.alphas[0]
        )
        # 血條
        display_hp = math.ceil(config.player_hp)
        if display_hp < 0:
            display_hp = 0  # 防止負數
        hp_rect = tool備用.text_button(
            "",
            tool備用.Colors.WHITE,
            tool備用.Colors.RED,
            config.WIDTH - 110,
            70,
            int((display_hp / config.player_max_hp) * 100),
            23,
            size=24,
            alpha=config.alphas[0],
        )
        tool備用.show_text(
            f"hp:{int(display_hp)}/{int(config.player_max_hp)}",
            tool備用.Colors.WHITE,
            config.WIDTH - 60,
            80,
            size=20,
            center=True,
            alpha=config.alphas[0],
        )

        if config.Invincible:
            # 畫個紅色的字提醒自己
            tool備用.show_text("DEBUG: INVINCIBLE ON", tool備用.Colors.RED, 10, 60, size=15)

        # 判斷是否在無敵時間內
        is_invincible = (current_time_sec - config.last_hit_time) < config.invincible_duration * config.invincible_time_buff

        p_rect = pygame.Rect(player_rect.x - config.offset_x, player_rect.y - config.offset_y, player_rect.width, player_rect.height)
        # -- 繪製玩家 --
        if is_invincible:
            if current_time_ms % 300 < 150:  # 閃爍效果
                pygame.draw.rect(screen, config.player_color, p_rect)
        else:
            # 正常時：顯示原本皮膚顏色
            pygame.draw.rect(screen, config.player_color, p_rect)
        # -------------
        # 讓箭頭有一點點動態跳動效果 (current_time_ms 需從外部傳入或用 runed_time)
        bounce = math.sin(runed_time * 0.01) * 3

        if player_rect.y < 40:  # 稍微提高判定門檻，避免太貼邊界
            # y 座標計算：玩家底部 + 間距 + 跳動
            base_y = player_rect.bottom + config.padding + bounce - 15
            text_order = ["^", "You"]
        else:
            # y 座標計算：玩家頂部 - 間距 - 跳動
            base_y = player_rect.y - config.padding - bounce
            text_order = ["You", "v"]

        # 限制 X 軸不超出螢幕 (使用你原本的 num_range)
        safe_x = tool備用.num_range(15, config.WIDTH - 15, player_rect.centerx)

        # 繪製第一行 (箭頭或 "You")
        tool備用.show_text(text_order[0], tool備用.Colors.WHITE, safe_x, base_y, size=16, center=True)
        # 繪製第二行 (箭頭或 "You")，間距固定 15 像素
        tool備用.show_text(text_order[1], tool備用.Colors.WHITE, player_rect.centerx, base_y + 15, size=16, center=True)
        # 分數
        config.points = (current_time_sec * config.points_multiplier + config.treasure_points) * config.gm_points_buff * config.now_skills[
            "p3"
        ] * level_multiplier + config.shoot_point
        if config.selected_level == "level 3" and config.game_mode == "crazy":
            config.points *= 0.5
        time_text = tool備用.show_text(
            f"Time: {tool備用.show_time_min(current_time_sec)}", tool備用.Colors.WHITE, 10, 10, size=24, alpha=config.alphas[1]
        )
        display_points = tool備用.num_to_KMBT(round(config.points, 1))
        points_text = tool備用.show_text(f"Coins: ${display_points}$", tool備用.Colors.WHITE, 10, 40, size=24, alpha=config.alphas[1])

        config.alphas[1] = 255
        if player_rect.colliderect(time_text) or player_rect.colliderect(points_text):
            config.alphas[1] = 100

        if config.alphas[1] == 255:
            for enemy in enemy_list:
                if not getattr(enemy, "show", True):
                    continue  # 沒出現的不算
                e_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)

                # 怪物碰到右上 OR 碰到左上，兩個一起變透明
                if e_rect.colliderect(time_text) or e_rect.colliderect(points_text):
                    config.alphas[1] = 100
                    break

        # 更新並繪製所有飄浮文字
        for ft in config.floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                config.floating_texts.remove(ft)
        if config.player_hp <= 0:
            config.game_state = "game_over"
            last_color = tool備用.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1)

            for i in range(2):
                config.alphas[i] = 255
            # 1. 立即計算當局得分並加入總額
            if not config.Invincible:
                config.total_points += config.points
            # 2. 立即存檔
            save_data()

            # 3. 處理其他死亡標記
            tool備用.collision_time = runed_time

            tool備用.sec_timer(update=False)
        # 在畫面上印出座標
        # tool.py_text(f"Pos: {player_rect.x}, {player_rect.y}", tool.Colors.WHITE, 50, 550, size=20)
        tool備用.show_text(
            f"Spawn time: {tool備用.show_time_min(config.now_treasure['next_spawn_at'])}, Show: {config.now_treasure['show']}",
            tool備用.Colors.GOLD,
            10,
            config.HEIGHT - 20,
            size=15,
        )
        tool備用.show_text(
            f"Alto shoot: {'ON' if config.alto_shoot else 'OFF'}",
            tool備用.Colors.GOLD,
            config.WIDTH - 80,
            config.HEIGHT - 20,
            size=15,
            center=True,
        )
    # 遊戲暫停
    elif config.game_state == "pause":
        screen.fill(tool備用.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1))
        config.coin_rect()
        target_vol = 0.5
        tool備用.sec_timer(False)
        config.maybe_cheat = True
        config.from_pause = True
        for enemy in enemy_list:
            if enemy.show and not countdowning:
                pygame.draw.rect(screen, enemy.color, (enemy.x, enemy.y, enemy.width, enemy.height))
        for cannon in cannon_list:
            if cannon["show"] and not countdowning:
                pygame.draw.rect(
                    screen,
                    cannon["color"],
                    (cannon["x"] - config.offset_x, cannon["y"] - config.offset_y, cannon["width"], cannon["height"]),
                )
        for bullet in config.bullet_list:
            bullet.draw(screen, config.offset_x, config.offset_y)
        if config.now_treasure["show"] and not countdowning:
            t_rect = pygame.Rect(config.now_treasure["x"], config.now_treasure["y"], 20, 20)
            pygame.draw.rect(screen, config.now_treasure["color"], t_rect)
        pygame.draw.rect(screen, config.player_color, player_rect)
        tool備用.screen_vague(10)
        tool備用.show_text("Pause", tool備用.Colors.WHITE, 0, 80, 50, screen_center=True)
        display_points = tool備用.num_to_KMBT(round(config.points, 1))
        tool備用.show_text(f"Coins: {display_points}$", tool備用.Colors.WHITE, 0, 140, screen_center=True)
        resume_button = tool備用.text_button(
            "Resume",
            tool備用.Colors.WHITE,
            tool備用.Colors.two_color_change(tool備用.Colors.ORANGE, tool備用.Colors.BROWN, resume_button.collidepoint(mouse_pos)),
            0,
            170,
            180,
            60,
            b_center=True,
        )
        settings_button = tool備用.text_button(
            "Settings",
            tool備用.Colors.BLACK,
            tool備用.Colors.two_color_change(tool備用.Colors.YELLOW, tool備用.Colors.GREEN, settings_button.collidepoint(mouse_pos)),
            0,
            250,
            180,
            60,
            b_center=True,
        )
        restart_button = tool備用.text_button(
            "Restart",
            tool備用.Colors.BLACK,
            tool備用.Colors.two_color_change(tool備用.Colors.ORANGE, tool備用.Colors.YELLOW, restart_button.collidepoint(mouse_pos)),
            0,
            330,
            180,
            60,
            b_center=True,
        )
        menu_button = tool備用.text_button(
            "Back to Menu",
            tool備用.Colors.BLACK,
            tool備用.Colors.two_color_change(tool備用.Colors.BLUE3, tool備用.Colors.PURPLE, menu_button.collidepoint(mouse_pos)),
            0,
            410,
            180,
            60,
            b_center=True,
        )
        leave_button = tool備用.text_button(
            "Leave",
            tool備用.Colors.WHITE,
            tool備用.Colors.two_color_change(tool備用.Colors.DARK_RED, tool備用.Colors.RED, leave_button.collidepoint(mouse_pos)),
            0,
            490,
            180,
            60,
            b_center=True,
        )
        current_world_key = f"world{config.select_world}"
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
                        config.game_state = "start_game"
                    else:
                        config.game_state = "countdown"
                if settings_button.collidepoint(mouse_pos) and is_pressing[1]:
                    config.game_state = "setting_p1"
                if restart_button.collidepoint(mouse_pos) and is_pressing[2]:
                    tool備用.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool備用.reset_timer()
                    config.player_hp = config.player_max_hp
                    if not config.Invincible:
                        config.total_points += config.points
                    for i in range(2):
                        config.alphas[i] = 255
                    config.longest_survived_time[current_world_key][config.selected_level][config.game_mode] = max(
                        config.longest_survived_time[current_world_key][config.selected_level][config.game_mode], current_time_sec
                    )
                    config.reset_game()
                    config.game_state = "countdown"
                if menu_button.collidepoint(mouse_pos) and is_pressing[3]:
                    config.from_pause = False
                    tool備用.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool備用.reset_timer()
                    config.player_hp = config.player_max_hp
                    if not config.Invincible:
                        config.total_points += config.points
                    for i in range(2):
                        config.alphas[i] = 255
                    config.longest_survived_time[current_world_key][config.selected_level][config.game_mode] = max(
                        config.longest_survived_time[current_world_key][config.selected_level][config.game_mode], current_time_sec
                    )
                    config.reset_game()
                    config.game_state = "menu"
                if leave_button.collidepoint(mouse_pos) and is_pressing[4]:
                    config.player_hp = config.player_max_hp
                    if not config.Invincible:
                        config.total_points += config.points
                    config.longest_survived_time[current_world_key][config.selected_level][config.game_mode] = max(
                        config.longest_survived_time[current_world_key][config.selected_level][config.game_mode], current_time_sec
                    )
                    config.reset_game()
                    config.running = False
                reset_pressing()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                    if not countdowning:
                        config.game_state = "start_game"
                    else:
                        config.game_state = "countdown"
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_c:
                    config.player_hp = config.player_max_hp
                    if not config.Invincible:
                        config.total_points += config.points
                    config.longest_survived_time[config.selected_level][config.game_mode] = max(
                        config.longest_survived_time[config.selected_level][config.game_mode], current_time_sec
                    )
                    running = False

        for ft in config.floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                config.floating_texts.remove(ft)
    # 死亡
    elif config.game_state == "game_over":
        screen.fill(last_color)
        config.coin_rect()
        for i in range(3):
            config.alphas[i] = 255
        target_vol = 0.5
        maybe_cheat = False
        from_pause = False
        for enemy in enemy_list:
            if enemy.show:
                enemy_rect = pygame.draw.rect(screen, enemy.color, (enemy.x, enemy.y, enemy.width, enemy.height))
        for cannon in cannon_list:
            if cannon["show"] and not countdowning:
                pygame.draw.rect(
                    screen,
                    cannon["color"],
                    (cannon["x"] - config.offset_x, cannon["y"] - config.offset_y, cannon["width"], cannon["height"]),
                )
        for bullet in config.bullet_list:
            bullet.draw(screen, config.offset_x, config.offset_y)
        pygame.draw.rect(screen, config.player_color, config.player_rect)
        passed_time = runed_time - tool備用.collision_time if tool備用.collision_time is not None else 0
        countdown = 10 - (passed_time // 1000)  # 倒數 10 秒
        tool備用.show_text(
            f"You survive for {tool備用.show_time_min(current_time_sec)}",
            tool備用.Colors.WHITE,
            0,
            100,
            size=48,
            screen_center=True,
        )
        gm_text = config.game_mode.replace("_", " ")
        tool備用.show_text(
            f"in {gm_text} mode.",
            tool備用.Colors.WHITE,
            0,
            150,
            size=48,
            screen_center=True,
        )
        end_text = "Unbelievable!" if current_time_sec >= (50 / config.gm_points_buff) else "Better luck next time!"
        tool備用.show_text(
            end_text,
            tool備用.Colors.WHITE,
            0,
            230,
            size=48,
            screen_center=True,
        )
        display_points = tool備用.num_to_KMBT(round(config.points, 1))
        tool備用.show_text(f"points:{display_points}$", tool備用.Colors.WHITE, 0, 300, screen_center=True)
        tool備用.show_text(
            f"Back to Menu in {countdown} sec",
            tool備用.Colors.WHITE,
            0,
            410,
            size=40,
            screen_center=True,
        )
        back_button = tool備用.text_button(
            "Back to Menu",
            tool備用.Colors.WHITE,
            tool備用.Colors.ORANGE,
            0,
            490,
            150,
            size=24,
            b_center=True,
        )
        if not config.has_save_survived_time and not config.Invincible:
            new_text = tool備用.FloatingText(
                "+" + tool備用.num_to_KMBT(config.points), config.WIDTH - 90, 20, tool備用.Colors.GREEN, size=24, time=150, speed=0.5
            )
            config.floating_texts.append(new_text)
            config.longest_survived_time[current_world_key][config.selected_level][config.game_mode] = max(
                config.longest_survived_time[current_world_key][config.selected_level][config.game_mode], current_time_sec
            )
            config.has_save_survived_time = True
        for ft in config.floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
            ft.update()
            ft.draw(screen)
            if ft.timer <= 0:  # 如果文字壽命到了
                config.floating_texts.remove(ft)
        if passed_time >= 10000:  # 過了 10000 毫秒 (10秒)
            tool備用.collision_time = None  # 重置，否則下次進遊戲會直接結束
            tool備用.reset_timer()
            config.player_hp = config.player_max_hp
            config.game_state = "menu"
            for ft in config.floating_texts[:]:
                ft.reset()
        for event in events:
            # if event.type == pygame.KEYDOWN:
            #     if event.key == pygame.K_SPACE:
            #         config.game_state = "menu"
            #         tool.collision_time = None
            #         tool.reset_timer()
            #         for ft in config.floating_texts[:]:
            #             ft.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    config.game_state = "menu"
                    tool備用.collision_time = None
                    tool備用.reset_timer()
                    for ft in config.floating_texts[:]:
                        ft.reset()
    # bug頁面
    # 1.AFK_error
    elif config.game_state == "afk_kick":
        screen.fill(tool備用.Colors.BLACK)
        screen_text = "Escape Them! v1.6.7 - ERROR: 1011451"
        # 畫一個紅色的警告框
        pygame.draw.rect(screen, tool備用.Colors.RED, (config.WIDTH // 2 - 250, 100, 500, 400))
        pygame.draw.rect(screen, tool備用.Colors.BLACK2, (config.WIDTH // 2 - 245, 95, 500, 400))
        # 在顯示標題前，隨機切換顏色
        flash_color = tool備用.Colors.RED if runed_time % 500 < 250 else tool備用.Colors.GRAY
        tool備用.show_text(
            "CRITICAL ERROR",
            tool備用.Colors.RED,
            0,
            150,
            size=60,
            screen_center=True,
            font_type="None",
        )
        tool備用.show_text(
            "AFK_DETECTION_TIMEOUT",
            tool備用.Colors.WHITE,
            0,
            240,
            size=25,
            screen_center=True,
            font_type="None",
        )
        tool備用.show_text(
            "Error code: 1011451",
            tool備用.Colors.GRAY,
            0,
            280,
            size=25,
            screen_center=True,
            font_type="None",
        )

        # 返回主選單按鈕 - 改成亮紅色背景增加緊張感
        close_button = tool備用.text_button(
            "TERMINATE PROCESS",
            tool備用.Colors.WHITE,
            tool備用.Colors.RED,
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
                    raise config.AFKError()
            if event.type == pygame.QUIT:
                raise config.AFKError()
    # 2.game_state_error
    else:
        screen.fill(tool備用.Colors.BLACK)
        screen_text = "Escape Them! v1.6.7 - ERROR: 2487145"
        tool備用.draw_rect(tool備用.Colors.RED, 0, 100, 550, 450, center=True)
        pygame.draw.rect(screen, tool備用.Colors.BLACK2, (config.WIDTH // 2 - 270, 95, 550, 450))
        tool備用.show_text(
            "SOMTHING WENT WRONG",
            tool備用.Colors.RED,
            0,
            150,
            size=55,
            screen_center=True,
            font_type="None",
        )
        tool備用.show_text(
            "GAME_STATE_NOT_CORRECT",
            tool備用.Colors.WHITE,
            0,
            240,
            size=25,
            screen_center=True,
            font_type="None",
        )
        tool備用.show_text(
            "Error code: 2487145",
            tool備用.Colors.GRAY,
            0,
            280,
            size=25,
            screen_center=True,
            font_type="None",
        )
        menu_button = tool備用.text_button(
            "Back To Menu",
            tool備用.Colors.WHITE,
            tool備用.Colors.RED,
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
                    config.player_hp = config.player_max_hp
                    if not config.Invincible:
                        config.total_points += config.points
                    config.longest_survived_time[config.selected_level][config.game_mode] = max(
                        config.longest_survived_time[config.selected_level][config.game_mode], current_time_sec
                    )
                    save_data()
                    config.reset_game()
                    config.game_state = "menu"
                reset_pressing()

    for event in events:
        if event.type == pygame.QUIT:
            config.running = False

    # 畫面閃爍
    config.draw_screen_flash(config.now_flash_color, config.total_flash_time, config.max_alpha, 20)
    # 畫滑鼠
    if config.mouse_img_loaded:
        blit_mouse_pos = (mouse_pos[0] - 1, mouse_pos[1])
        if mouse_buttons[0]:
            # 點擊時，座標稍微 +3，會有往內按的感覺
            screen.blit(config.mouse_img_surface, (blit_mouse_pos[0] + 3, blit_mouse_pos[1] + 3))
        else:
            screen.blit(config.mouse_img_surface, blit_mouse_pos)

    if config.game_state != "start_game":
        config.heart_channel.stop()
    config.current_vol += (config.target_vol - config.current_vol) * 0.005
    pygame.mixer.music.set_volume(config.current_vol)  # 靜音：0, 開聲音：current_vol
    pygame.display.set_caption(screen_text)
    pygame.display.flip()
pygame.quit()
print("")
print("")

save_data()
print(f"已成功儲存檔案到:{active_save}")
print()
sys.exit("掰掰!下次再玩!")
