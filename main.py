"""
pygame 提示：以右邊為 0 度
"""

import math
import random
import sys

import pygame

import button_obj
import config  # 所有的全域變數與初始化都在這裡
import data_handler
import old_to_new
import tool  # 載入你的工具包
import ui_handler

# 1. 取得 config 中已經初始化好的物件
screen = config.screen
clock = config.clock
is_pressing = config.is_pressing  # 引用 config 的列表
scroll_ys = config.scroll_ys

ui_manager = ui_handler.UIManager(screen)

# 確保工具包使用的 screen 是同一個
tool.set_screen(screen)


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
    # 優先權 3：完全沒檔案，指向預設路徑
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
data_handler.load_data(config.current_active_path)
config.load_resets()

# 補空位專區
leave_button = menu_button = restart_button = resume_button = lv_button = draw_button = levels_button = pygame.Rect(0, 0, 0, 0)
settings_button = upgrade_button = help_button = exit_button = player_rect = back_button = enemy_rect = pygame.Rect(0, 0, 0, 0)
next_world_button = pygame.Rect(0, 0, 0, 0)
level_button_color = tool.Colors.WHITE
config.target_y = 0
selected_save_name = ""
saved, loaded = False, False
loaded_data_success = False


def get_current_mouse_state():
    return pygame.mouse.get_pos(False), pygame.mouse.get_pressed()


current_time_sec = 0

# 隱藏滑鼠
pygame.mouse.set_visible(False)

# pygame.mixer.music.play(-1)  # 這裡決定要不要播放背景音樂

while config.running:
    config.last_game_state = config.game_state
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
        screen.fill(tool.Colors.BLUE3)
        config.coin_rect()

        button_obj.show_text(screen, "settings", tool.Colors.WHITE, 40, 70, size=24, font_type="")

        button_obj.show_text(screen, "upgrades", tool.Colors.WHITE, config.WIDTH - 120, 70, size=24, font_type="")

        ui_manager.handle_current_state(events, mouse_pos)
    # 難易度與最長存活時間
    elif config.game_state == "setting_p1":
        screen.fill(tool.Colors.BLUE3)
        config.coin_rect()
        current_world_key = f"world{config.select_world}"
        button_obj.show_text(screen, "Difficulty And Longest Served Time", tool.Colors.WHITE, 0, 60, size=34, screen_center=True)
        button_obj.show_text(screen, "Now Level:", tool.Colors.WHITE, 0, 110, size=30, screen_center=True)

        # 把背景的東西畫在這個前
        ui_manager.handle_current_state(events, mouse_pos)

        # 顯示最長存活時間
        now_level_survived_time = config.longest_survived_time[current_world_key].get(config.selected_level, {})
        easy_time = now_level_survived_time.get("easy", 0)
        normal_time = now_level_survived_time.get("normal", 0)
        hard_time = now_level_survived_time.get("hard", 0)
        super_hard_time = now_level_survived_time.get("super_hard", 0)
        crazy_time = now_level_survived_time.get("crazy", 0)
        # print(f"DEBUG: now_level_survived_time = {now_level_survived_time}")5

        # Easy Mode
        button_obj.show_text(
            screen,
            f"easy mode: {tool.show_time_min(easy_time)}",
            tool.Colors.BLACK if config.game_mode == "easy" else tool.Colors.WHITE,
            0,
            220,
            screen_center=True,
        )
        # Normal Mode
        button_obj.show_text(
            screen,
            f"normal mode: {tool.show_time_min(normal_time)}",
            tool.Colors.BLACK if config.game_mode == "normal" else tool.Colors.WHITE,
            0,
            280,
            screen_center=True,
        )
        # Hard Mode
        button_obj.show_text(
            screen,
            f"hard mode: {tool.show_time_min(hard_time)}",
            tool.Colors.BLACK if config.game_mode == "hard" else tool.Colors.WHITE,
            0,
            340,
            screen_center=True,
        )
        # Super Hard Mode
        button_obj.show_text(
            screen,
            f"super hard mode: {tool.show_time_min(super_hard_time)}",
            tool.Colors.BLACK if config.game_mode == "super_hard" else tool.Colors.WHITE,
            0,
            400,
            screen_center=True,
        )
        # Crazy Mode
        button_obj.show_text(
            screen,
            f"crazy mode: {tool.show_time_min(crazy_time)}",
            tool.Colors.BLACK if config.game_mode == "crazy" else tool.Colors.WHITE,
            0,
            460,
            screen_center=True,
        )
    # 每關最長存活時間
    elif config.game_state == "more_survived_time":
        screen.fill(tool.Colors.BLUE3)
        config.coin_rect()
        current_world_key = f"world{config.select_world}"
        config.target_y = tool.num_range(0, config.target_y, config.max_scroll_y)  # 強制修正回合法範圍
        if config.scroll_ys[0] != config.target_y or not tool.in_range(0, config.scroll_ys[0], config.max_scroll_y):
            config.scroll_ys[0] += (config.target_y - config.scroll_ys[0]) * 0.1  # 每次移動剩下的 30%
        config.scroll_ys[0] = tool.num_range(0, config.scroll_ys[0], config.max_scroll_y)  # 強制修正回合法範圍
        draw_y = 110
        for gm in config.modes_config:
            draw_y += 90
            for level in config.all_levels:
                if -10 < (draw_y - scroll_ys[0]) < config.HEIGHT + 10:
                    button_obj.show_text(
                        screen,
                        f"Level {level.replace('level', '')}: {tool.show_time_min(config.longest_survived_time[current_world_key][level][gm[0]])}",
                        tool.Colors.WHITE,
                        0,
                        draw_y - config.scroll_ys[0],
                        screen_center=True,
                    )
                draw_y += 60
            draw_y -= 25
        ui_manager.handle_current_state(events, mouse_pos)
    # 玩家皮膚購買與更換
    elif config.game_state == "setting_p2":
        screen.fill(tool.Colors.BLUE3)
        config.coin_rect()
        start_x = 100  # 左邊起始位置
        start_y = 180  # 列表上方起始位置 (空出標題跟金幣的位置)
        row_gap = 80  # 每排之間的垂直距離
        col_gap = 180  # 如果一排想放多個，左右距離
        skin_list = list(config.player_skins.keys())
        ui_manager.handle_current_state(events, mouse_pos)

        button_obj.show_text(screen, "Player Skins", tool.Colors.WHITE, 0, 50, screen_center=True, size=30)
        # 資料、皮膚顯示、預覽按鈕
        pygame.draw.line(screen, tool.Colors.WHITE, (450, 80), (450, config.HEIGHT - 100), 5)
        button_obj.show_text(screen, "Demo player:", tool.Colors.WHITE, 480, 60, size=30)
        show_rect = pygame.draw.rect(screen, config.now_player_skin, (560, 120, 30, 30))
        # try_button = tool.text_button(screen, "Try to play", tool.Colors.WHITE, tool.Colors.PURPLE, 480, 400, 150, 40, size=20)
        pygame.draw.line(screen, tool.Colors.WHITE, (470, 460), (650, 460), 5)
        button_obj.show_text(
            screen,
            f"You got 1 {config.last_draw_color} skin!",
            tool.Colors.get_color(config.last_draw_color) if config.last_draw_color is not None else tool.Colors.WHITE,
            470,
            475,
            size=20,
            show=(config.last_draw_color is not None),
        )
        # --- 右側：皮膚詳細資訊區 ---
        selected_name = config.current_player_color_name
        skin = config.player_skins[selected_name]

        # 1. 顯示皮膚大名
        button_obj.show_text(screen, f"Skin: {selected_name.upper()}", tool.Colors.WHITE, 570, 170, size=26, center=True)

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
            button_obj.show_text(screen, f"• {display_name}:", tool.Colors.WHITE, 470, 210 + (i * 60), size=18)

            # 繪製數值 (保留兩位小數)
            val_text = f"{round(current_val, 2)}x"
            button_obj.show_text(screen, val_text, tool.Colors.GREEN, 490, 235 + (i * 60), size=22)

            # 繪製成長率提示 (讓玩家知道升級加多少)
            if grow != 0:
                grow_text = f"(+{grow}/lv)" if grow > 0 else f"({grow}/lv)"
                button_obj.show_text(screen, grow_text, tool.Colors.GRAY, 570, 238 + (i * 60), size=14)

    # 存檔專區
    elif config.game_state == "setting_p3":
        screen.fill(tool.Colors.BLUE3)
        config.coin_rect()
        button_obj.show_text(screen, "System Settings", tool.Colors.WHITE, 0, 80, size=50, screen_center=True)
        button_obj.show_text(screen, "We will save this file while you leave", tool.Colors.WHITE, 0, 140, size=24, screen_center=True)
        ui_manager.handle_current_state(events, mouse_pos)
    # 選擇其他存檔
    elif config.game_state == "choose_file":
        screen.fill(tool.Colors.BLUE3)
        config.coin_rect()
        pygame.draw.rect(screen, tool.Colors.BLUE3, (0, config.HEIGHT - 110, config.WIDTH, 110))  # 擋住捲動後的檔案
        pygame.draw.rect(screen, tool.Colors.BLUE3, (0, 0, config.WIDTH, 110))
        button_obj.show_text(screen, "Choose Save File", tool.Colors.WHITE, 0, 40, size=50, screen_center=True)
        ui_manager.handle_current_state(events, mouse_pos)

    # 玩家升級：
    # 升級列表
    elif config.game_state == "upgrade_hub":
        current_config = config.UPGRADE_SURVIVAL if config.shop_page == "survival" else config.UPGRADE_COMBAT
        screen.fill(tool.Colors.BLUE3)
        config.update_upgrade_hub_layout()  # --- 繪製箭頭 ---
        if config.left_img_loaded:
            if config.l_img_show:
                screen.blit(config.left_img_surface, config.upgrade_left_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, config.upgrade_left_rect)
        if config.right_img_loaded:
            if config.r_img_show:
                screen.blit(config.right_img_surface, config.upgrade_right_rect)
        else:
            pygame.draw.rect(screen, tool.Colors.RED, config.upgrade_right_rect)

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
                rect = tool.text_button(
                    screen,
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
                config.upgrade_buttons[key] = rect

        # 全域重置：如果滑鼠放開了，不管在哪裡都要重置 pressing
        if not mouse_buttons[0]:
            is_pressing[8] = False

        # 固定底部的 BACK 按鈕
        pygame.draw.rect(screen, tool.Colors.BLUE3, (0, config.HEIGHT - 80, config.WIDTH, 80))
        back_button = tool.text_button(
            screen, "BACK TO MENU", tool.Colors.WHITE, tool.Colors.ORANGE, 0, config.HEIGHT - 70, 260, 50, b_center=True
        )
        tool.text_button(screen, "Upgrade Center", tool.Colors.WHITE, tool.Colors.BLUE3, 0, 0, 500, 100, size=50, b_center=True)
        tool.text_button(
            screen, f"now_mode: {config.shop_page}", tool.Colors.WHITE, tool.Colors.BLUE3, 0, 90, 500, 40, size=35, b_center=True
        )
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
        screen.fill(tool.Colors.BLUE3)

        # 偽代碼方向
        current_lv_color = tool.Colors.WHITE  # 預設白色

        if config.lv_flash_timer > 0:
            config.lv_flash_timer -= 1
            # 如果剩下偶數幀，就換個顏色（例如黃色或金色）
            if config.lv_flash_timer % 10 > 8:
                current_lv_color = tool.Colors.YELLOW

        # --- 標題文字 ---
        button_obj.show_text(screen, cfg["title"], tool.Colors.WHITE, 0, 240, size=50, screen_center=True)
        button_obj.show_text(
            screen,
            f"Level: Lv.{lvl + 1}",
            current_lv_color,
            0,
            300,
            size=40,
            screen_center=True,
        )
        button_obj.show_text(
            screen,
            f"Balance: {tool.num_to_KMBT(round(config.total_points, 1))}$",
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
        button_obj.show_text(screen, f"Effect: {display_text}", tool.Colors.WHITE, 0, 400, size=25, screen_center=True)
        # --- 萬能數值顯示邏輯 (結束) ---

        if config.game_state == "upgrade_p20":
            button_obj.show_text(
                screen, "While you're playing, press 'T' to alto shoot!", tool.Colors.YELLOW, 0, 215, size=20, screen_center=True
            )

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
                pygame.draw.rect(screen, tool.Colors.RED, config.left_rect)

        # 右箭頭：不是最後一頁才顯示
        if current_p_num < total_pages:
            if config.right_img_loaded:
                screen.blit(config.right_img_surface, config.right_rect)
            else:
                pygame.draw.rect(screen, tool.Colors.RED, config.right_rect)

        # 4. 購買按鈕邏輯 (計算價格與顏色)
        if lvl < len(costs):
            cost = costs[lvl]  # 取得當前等級價格

            # 判斷滑鼠是否懸停 & 錢夠不夠
            if upgrade_button.collidepoint(mouse_pos):
                if config.total_points >= cost:
                    btn_text = f"Buy! Left ${tool.num_to_KMBT(round(config.total_points - cost, 1))}"
                    btn_color = tool.Colors.GREEN
                else:
                    btn_text = f"Need: ${tool.num_to_KMBT(round(cost - config.total_points, 1))}"
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

        upgrade_button = tool.text_button(screen, btn_text, tool.Colors.BLACK, btn_color, 0, 430, 350, 60, b_center=True)
        back_button = tool.text_button(
            screen,
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
                        data_handler.save_data()  # 儲存
                        # print(f"Upgraded {config.game_state} to Lv.{current_levels[config.game_state] + 1}")
                        new_text = tool.FloatingText(
                            "-" + tool.num_to_KMBT(cost), config.WIDTH - 90, 20, tool.Colors.RED, speed=0.7, size=24
                        )
                        config.floating_texts.append(new_text)
                        config.buy_channel.play(config.sounds["buy_success"])
                        can_shoot = bool(config.now_skills["p15"])

                        config.now_flash_color = tool.Colors.GOLD
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
    # ----------------------------------------------------------------------------
    # 關卡選擇
    elif config.game_state == "level_select":
        config.from_pause = False
        config.maybe_cheat = False
        current_world_key = f"world{config.select_world}"
        screen.fill(tool.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1))
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
                            data_handler.save_data()
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
                scroll_ys[3] = tool.num_range(0, max_scroll, scroll_ys[3])
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
            level_button = tool.text_button(
                screen,
                f"Level {i}",
                tool.Colors.WHITE,
                tool.Colors.BLUE if not is_locked else tool.Colors.GRAY,
                120,
                60 + i * 80 - scroll_ys[3],
                200,
                60,
            )
            pygame.draw.line(screen, tool.Colors.WHITE, (350, 100), (350, 500), 2)
            pygame.draw.line(screen, tool.Colors.WHITE, (50, 130 + i * 80 - scroll_ys[3]), (600, 130 + i * 80 - scroll_ys[3]), 2)
            prev_level_record = config.longest_survived_time[current_world_key].get(f"level{i - 1}", {}).get("normal", 0)
            required_time = config.current_world_need_record[i]
            button_obj.show_text(
                screen,
                f"Need time: {tool.show_time_min(required_time)}",
                tool.Colors.two_color_change(tool.Colors.GREEN, tool.Colors.RED, prev_level_record >= required_time),
                380,
                80 + i * 80 - scroll_ys[3],
                size=18,
                show=is_locked,
            )

            draw_this_lock = is_locked
            if level_button.collidepoint(mouse_pos):
                if not is_locked:
                    pygame.draw.rect(screen, tool.Colors.GREEN, level_button, 3)
                elif is_next_level:
                    draw_this_lock = False
                    pygame.draw.rect(screen, tool.Colors.GRAY, level_button)
                    pygame.draw.rect(
                        screen,
                        tool.Colors.GREEN if config.total_points >= config.current_world_costs[i] else tool.Colors.RED,
                        level_button,
                        3,
                    )
                    # 顯示金額
                    display_cost = config.current_world_costs[i]
                    button_obj.show_text(
                        screen,
                        f"Unlock for ${tool.num_to_KMBT(display_cost)}",
                        tool.Colors.GREEN if config.total_points >= config.current_world_costs[i] else tool.Colors.RED,
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
                    pygame.draw.rect(screen, tool.Colors.GRAY, (180, 60 + i * 80 - 20 - scroll_ys[3], 30, 30))
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
                    new_text = tool.FloatingText(
                        "-" + tool.num_to_KMBT(config.current_world_costs[i]), config.WIDTH - 90, 20, tool.Colors.RED, speed=0.7, size=24
                    )
                    config.floating_texts.append(new_text)
                    config.sounds["buy_success"].play()
                    config.update_world_data(config.select_world)  # 更新世界資料，確保下一次進入關卡選單時資料是最新的
                elif is_next_level:
                    config.sounds["buy_error"].play()
        if has_next_world and is_not_already_bought:
            next_world_button = tool.text_button(
                screen,
                (
                    [
                        "Buy!" if config.total_points >= config.world_cost[unlock_world_key] else "Need More $",
                        f" ({"cost" if config.total_points >= config.world_cost[unlock_world_key] else "need"}: ${tool.num_to_KMBT(config.world_cost[unlock_world_key] - config.total_points)})",
                    ]
                    if next_world_button.collidepoint(mouse_pos) and is_target_world_locked and is_not_already_bought
                    else ["Next World ", f"(cost: ${tool.num_to_KMBT(config.world_cost[unlock_world_key])})"]
                ),
                tool.Colors.WHITE,
                (
                    tool.Colors.two_color_change(
                        tool.Colors.two_color_change(
                            tool.Colors.GREEN,
                            tool.Colors.RED,
                            config.total_points >= config.world_cost[unlock_world_key] and is_target_world_locked,
                        ),
                        tool.Colors.two_color_change(tool.Colors.CHARTREUSE, tool.Colors.GRAY, is_target_world_locked),
                        next_world_button.collidepoint(mouse_pos),
                    )
                    if is_target_world_locked or is_not_already_bought
                    else tool.Colors.GRAY
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
            next_world_button = tool.text_button(
                screen,
                ["Stay tuned", " for new worlds!"],
                tool.Colors.WHITE,
                tool.Colors.GRAY,
                120,
                60 + len(config.current_world_costs) * 80 - scroll_ys[3],
                200,
                60,
                t_y=80 + len(config.current_world_costs) * 80 - scroll_ys[3],
                size=20,
            )
        else:
            next_world_button = tool.text_button(
                screen,
                "Has Unlocked",
                tool.Colors.WHITE,
                tool.Colors.GRAY,
                120,
                60 + len(config.current_world_costs) * 80 - scroll_ys[3],
                200,
                60,
                size=26,
            )

        button_obj.show_text(screen, "Normal mode", tool.Colors.WHITE, 400, 160 - scroll_ys[3], size=20)
        pygame.draw.rect(
            screen,
            tool.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1),
            (0, 0, config.WIDTH, 100),
        )
        button_obj.show_text(screen, "Level Select", tool.Colors.WHITE, 0, 40, size=50, screen_center=True)

        config.coin_rect()

        pygame.draw.rect(
            screen,
            tool.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1),
            (0, config.HEIGHT - 100, config.WIDTH, 100),
        )

        if config.left_img_loaded and config.select_world > 1:
            screen.blit(config.left_img_surface, config.left_rect)
        elif not config.left_img_loaded:
            pygame.draw.rect(screen, tool.Colors.RED, config.left_rect)
        if config.right_img_loaded and config.select_world < config.worlds_unlocked:
            screen.blit(config.right_img_surface, config.right_rect)
        elif not config.right_img_loaded:
            pygame.draw.rect(screen, tool.Colors.RED, config.right_rect)

        back_button = tool.text_button(
            screen, "Back to Menu", tool.Colors.WHITE, tool.Colors.ORANGE, 0, config.HEIGHT - 80, 200, 60, b_center=True
        )
    # 倒數前五秒
    elif config.game_state == "countdown":
        screen.fill(tool.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1))

        config.coin_rect()
        passed_time, _ = tool.sec_timer(update=True, dt=dt)
        countdown = 3 - passed_time  # 倒數 3 秒

        config.player_move(keys)

        button_obj.show_text(screen, level_name, tool.Colors.WHITE, 0, 80, screen_center=True, size=40)

        if countdown >= 1:
            countdown_text = str(int(countdown))
            screen_text = f"Escape Them! v1.6.7 - {countdown}!"
        elif countdown >= 0:
            countdown_text = "GO!"
            screen_text = "Escape Them! v1.6.7 - GO!"
        else:
            tool.sec_timer(update=False)
            tool.reset_timer()
            config.game_state = "start_game"

        player_rect = pygame.draw.rect(screen, config.player_color, config.player_rect)

        button_obj.show_text(screen, countdown_text, tool.Colors.WHITE, 0, config.HEIGHT // 2 - 150, screen_center=True, size=300)

        for event in events:
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                countdowning = True
                config.game_state = "pause"
    # 主遊戲程式
    elif config.game_state == "start_game":
        screen_text = "Escape Them! v1.6.7 - Escaping"
        screen.fill(tool.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1))
        config.coin_rect(player_rect)
        countdowning = False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    config.game_state = "pause"
                if event.key == pygame.K_t and config.now_skills["p20"]:
                    config.alto_shoot = not config.alto_shoot
        should_update = config.freeze_timer <= 0
        current_time_sec, current_time_ms = tool.sec_timer(update=should_update, dt=dt)

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
                    config.now_flash_color = tool.Colors.RED if not dodged else tool.Colors.YELLOW

                    # 統一計算最後傷害
                    final_damage = int(damage_taken * damage_multiplier)
                    config.player_hp -= max(1, final_damage)

                    # 更新時間與音效
                    config.last_hit_time = current_time_sec
                    config.sounds["hurt"].play()

                    # 顯示漂浮文字 (帶入剛才判斷好的內容)
                    config.floating_texts.append(
                        tool.FloatingText(
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
                            pygame.draw.line(screen, tool.Colors.RED, cannon_vec, player_vec, 3)
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
                    config.now_flash_color = tool.Colors.RED if not dodged else tool.Colors.YELLOW

                    config.sounds["hurt"].play()

                    # 產生漂浮文字
                    config.floating_texts.append(
                        tool.FloatingText(text_content, player_rect.x, player_rect.y, text_color, speed=0.5, time=120)
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
                    (*tool.Colors.GOLD, 150),  # 金色 (或是用 tool.Colors.GOLD)
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
                    config.now_flash_color = tool.Colors.BLUE
                    config.flash_timer = config.total_flash_time
                else:
                    config.sounds["coin"].play()
                # 1. 計算分數
                min_p, max_p = (add * config.coin_multiplier * config.now_skills["p12"] for add in config.now_treasure["add_points"])
                base_val = random.uniform(min_p, max_p)

                config.treasure_points += base_val

                display_val = f"{round(base_val * config.gm_points_buff * config.now_skills['p3'] * level_multiplier, 1):g}"

                coin_text = tool.FloatingText(f"+${display_val}", player_rect.x, player_rect.y, tool.Colors.GOLD)
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
                    enemy.x = tool.num_range(0, config.WIDTH - enemy.width, enemy.x)
                    enemy.y = tool.num_range(0, config.HEIGHT - enemy.height, enemy.y)

        # --- 玩家血量回復 ---
        # 1. 確保只有在血量未滿且玩家還活著時才計算
        if config.player_hp < config.player_max_hp and config.player_hp > 0:
            # 2. 改用 >= 判斷，確保每隔指定秒數觸發一次
            if current_time_sec - config.last_cure_time >= config.now_skills["p7"]["time"]:
                config.player_hp += config.now_skills["p7"]["hp"]

                # 3. 修正：為了讓計時更準確，last_cure_time 應該加上冷卻時間，而不是直接等於當前時間
                config.last_cure_time += config.now_skills["p7"]["time"]

                new_text = tool.FloatingText(
                    (
                        f"+{config.now_skills['p7']['hp']}hp"
                        if config.player_max_hp >= config.player_hp
                        else f"+{int(config.now_skills['p7']['hp'] - (config.player_hp - config.player_max_hp))}hp"
                    ),
                    player_rect.x,
                    player_rect.y,
                    tool.Colors.GREEN,
                    speed=0.8,
                )
                config.floating_texts.append(new_text)
                config.now_flash_color = tool.Colors.GREEN
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
        base_hp_rect = tool.text_button(
            screen, "", tool.Colors.WHITE, tool.Colors.DARK_RED, config.WIDTH - 110, 70, 100, 23, t_y=82, size=15, alpha=config.alphas[0]
        )
        # 血條
        display_hp = math.ceil(config.player_hp)
        if display_hp < 0:
            display_hp = 0  # 防止負數
        hp_rect = tool.text_button(
            screen,
            "",
            tool.Colors.WHITE,
            tool.Colors.RED,
            config.WIDTH - 110,
            70,
            int((display_hp / config.player_max_hp) * 100),
            23,
            size=24,
            alpha=config.alphas[0],
        )
        button_obj.show_text(
            screen,
            f"hp:{int(display_hp)}/{int(config.player_max_hp)}",
            tool.Colors.WHITE,
            config.WIDTH - 60,
            80,
            size=20,
            center=True,
            alpha=config.alphas[0],
        )

        if config.Invincible:
            # 畫個紅色的字提醒自己
            button_obj.show_text(screen, "DEBUG: INVINCIBLE ON", tool.Colors.RED, 10, 60, size=15)

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
        safe_x = tool.num_range(15, config.WIDTH - 15, player_rect.centerx)

        # 繪製第一行 (箭頭或 "You")
        button_obj.show_text(screen, text_order[0], tool.Colors.WHITE, safe_x, base_y, size=16, center=True)
        # 繪製第二行 (箭頭或 "You")，間距固定 15 像素
        button_obj.show_text(screen, text_order[1], tool.Colors.WHITE, player_rect.centerx, base_y + 15, size=16, center=True)
        # 分數
        config.points = (current_time_sec * config.points_multiplier + config.treasure_points) * config.gm_points_buff * config.now_skills[
            "p3"
        ] * level_multiplier + config.shoot_point
        if config.selected_level == "level 3" and config.game_mode == "crazy":
            config.points *= 0.5
        time_text = button_obj.show_text(
            screen, f"Time: {tool.show_time_min(current_time_sec)}", tool.Colors.WHITE, 10, 10, size=24, alpha=config.alphas[1]
        )
        display_points = tool.num_to_KMBT(round(config.points, 1))
        points_text = button_obj.show_text(screen, f"Coins: ${display_points}$", tool.Colors.WHITE, 10, 40, size=24, alpha=config.alphas[1])

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
        if config.player_hp <= 0:
            config.game_state = "game_over"
            last_color = tool.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1)

            for i in range(2):
                config.alphas[i] = 255
            # 1. 立即計算當局得分並加入總額
            if not config.Invincible:
                config.total_points += config.points
            # 2. 立即存檔
            data_handler.save_data()

            # 3. 處理其他死亡標記
            tool.collision_time = runed_time

            tool.sec_timer(update=False)
        # 在畫面上印出座標
        # tool.py_text(f"Pos: {player_rect.x}, {player_rect.y}", tool.Colors.WHITE, 50, 550, size=20)
        button_obj.show_text(
            screen,
            f"Spawn time: {tool.show_time_min(config.now_treasure['next_spawn_at'])}, Show: {config.now_treasure['show']}",
            tool.Colors.GOLD,
            10,
            config.HEIGHT - 20,
            size=15,
        )
        button_obj.show_text(
            screen,
            f"Alto shoot: {'ON' if config.alto_shoot else 'OFF'}",
            tool.Colors.GOLD,
            config.WIDTH - 80,
            config.HEIGHT - 20,
            size=15,
            center=True,
        )
    # 遊戲暫停
    elif config.game_state == "pause":
        screen.fill(tool.Colors.two_color_wave(config.world_bgc[current_world_key][0], config.world_bgc[current_world_key][1], 1))
        config.coin_rect()
        target_vol = 0.5
        tool.sec_timer(False)
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
        tool.screen_vague(10)
        button_obj.show_text(screen, "Pause", tool.Colors.WHITE, 0, 80, 50, screen_center=True)
        display_points = tool.num_to_KMBT(round(config.points, 1))
        button_obj.show_text(screen, f"Coins: {display_points}$", tool.Colors.WHITE, 0, 140, screen_center=True)
        resume_button = tool.text_button(
            screen,
            "Resume",
            tool.Colors.WHITE,
            tool.Colors.two_color_change(tool.Colors.ORANGE, tool.Colors.BROWN, resume_button.collidepoint(mouse_pos)),
            0,
            170,
            180,
            60,
            b_center=True,
        )
        settings_button = tool.text_button(
            screen,
            "Settings",
            tool.Colors.BLACK,
            tool.Colors.two_color_change(tool.Colors.YELLOW, tool.Colors.GREEN, settings_button.collidepoint(mouse_pos)),
            0,
            250,
            180,
            60,
            b_center=True,
        )
        restart_button = tool.text_button(
            screen,
            "Restart",
            tool.Colors.BLACK,
            tool.Colors.two_color_change(tool.Colors.ORANGE, tool.Colors.YELLOW, restart_button.collidepoint(mouse_pos)),
            0,
            330,
            180,
            60,
            b_center=True,
        )
        menu_button = tool.text_button(
            screen,
            "Back to Menu",
            tool.Colors.BLACK,
            tool.Colors.two_color_change(tool.Colors.BLUE3, tool.Colors.PURPLE, menu_button.collidepoint(mouse_pos)),
            0,
            410,
            180,
            60,
            b_center=True,
        )
        leave_button = tool.text_button(
            screen,
            "Leave",
            tool.Colors.WHITE,
            tool.Colors.two_color_change(tool.Colors.DARK_RED, tool.Colors.RED, leave_button.collidepoint(mouse_pos)),
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
                    tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool.reset_timer()
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
                    tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
                    tool.reset_timer()
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
        passed_time = runed_time - tool.collision_time if tool.collision_time is not None else 0
        countdown = 10 - (passed_time // 1000)  # 倒數 10 秒
        button_obj.show_text(
            screen,
            f"You survive for {tool.show_time_min(current_time_sec)}",
            tool.Colors.WHITE,
            0,
            100,
            size=48,
            screen_center=True,
        )
        gm_text = config.game_mode.replace("_", " ")
        button_obj.show_text(
            screen,
            f"in {gm_text} mode.",
            tool.Colors.WHITE,
            0,
            150,
            size=48,
            screen_center=True,
        )
        end_text = "Unbelievable!" if current_time_sec >= (50 / config.gm_points_buff) else "Better luck next time!"
        button_obj.show_text(
            screen,
            end_text,
            tool.Colors.WHITE,
            0,
            230,
            size=48,
            screen_center=True,
        )
        display_points = tool.num_to_KMBT(round(config.points, 1))
        button_obj.show_text(screen, f"points:{display_points}$", tool.Colors.WHITE, 0, 300, screen_center=True)
        button_obj.show_text(
            screen,
            f"Back to Menu in {countdown} sec",
            tool.Colors.WHITE,
            0,
            410,
            size=40,
            screen_center=True,
        )
        back_button = tool.text_button(
            screen,
            "Back to Menu",
            tool.Colors.WHITE,
            tool.Colors.ORANGE,
            0,
            490,
            150,
            size=24,
            b_center=True,
        )
        if not config.has_save_survived_time and not config.Invincible:
            new_text = tool.FloatingText(
                "+" + tool.num_to_KMBT(config.points), config.WIDTH - 90, 20, tool.Colors.GREEN, size=24, time=150, speed=0.5
            )
            config.floating_texts.append(new_text)
            config.longest_survived_time[current_world_key][config.selected_level][config.game_mode] = max(
                config.longest_survived_time[current_world_key][config.selected_level][config.game_mode], current_time_sec
            )
            config.has_save_survived_time = True
        if passed_time >= 10000:  # 過了 10000 毫秒 (10秒)
            tool.collision_time = None  # 重置，否則下次進遊戲會直接結束
            tool.reset_timer()
            config.player_hp = config.player_max_hp
            config.game_state = "menu"
            for ft in config.floating_texts[:]:
                ft.reset()
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    config.game_state = "menu"
                    tool.collision_time = None
                    tool.reset_timer()
                    for ft in config.floating_texts[:]:
                        ft.reset()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(mouse_pos):
                    is_pressing[0] = True
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if back_button.collidepoint(mouse_pos) and is_pressing[0]:
                    config.game_state = "menu"
                    tool.collision_time = None
                    tool.reset_timer()
                    for ft in config.floating_texts[:]:
                        ft.reset()
    # bug頁面
    # 1.AFK_error
    elif config.game_state == "afk_kick":
        screen.fill(tool.Colors.BLACK)
        screen_text = "Escape Them! v1.6.7 - ERROR: 1011451"
        # 畫一個紅色的警告框
        pygame.draw.rect(screen, tool.Colors.RED, (config.WIDTH // 2 - 250, 100, 500, 400))
        pygame.draw.rect(screen, tool.Colors.BLACK2, (config.WIDTH // 2 - 245, 95, 500, 400))
        # 在顯示標題前，隨機切換顏色
        flash_color = tool.Colors.RED if runed_time % 500 < 250 else tool.Colors.GRAY
        button_obj.show_text(
            screen,
            "CRITICAL ERROR",
            tool.Colors.RED,
            0,
            150,
            size=60,
            screen_center=True,
            font_type="None",
        )
        button_obj.show_text(
            screen,
            "AFK_DETECTION_TIMEOUT",
            tool.Colors.WHITE,
            0,
            240,
            size=25,
            screen_center=True,
            font_type="None",
        )
        button_obj.show_text(
            screen,
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
            screen,
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
                    raise config.AFKError()
            if event.type == pygame.QUIT:
                raise config.AFKError()
    # 2.game_state_error
    else:
        screen.fill(tool.Colors.BLACK)
        screen_text = "Escape Them! v1.6.7 - ERROR: 2487145"
        pygame.draw.rect(screen, tool.Colors.RED, (0, 100, 550, 450))
        pygame.draw.rect(screen, tool.Colors.BLACK2, (config.WIDTH // 2 - 270, 95, 550, 450))
        button_obj.show_text(
            screen,
            "SOMTHING WENT WRONG",
            tool.Colors.RED,
            0,
            150,
            size=55,
            screen_center=True,
            font_type="None",
        )
        button_obj.show_text(
            screen,
            "GAME_STATE_NOT_CORRECT",
            tool.Colors.WHITE,
            0,
            240,
            size=25,
            screen_center=True,
            font_type="None",
        )
        button_obj.show_text(
            screen,
            "Error code: 2487145",
            tool.Colors.GRAY,
            0,
            280,
            size=25,
            screen_center=True,
            font_type="None",
        )
        menu_button = tool.text_button(
            screen,
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
                    config.player_hp = config.player_max_hp
                    if not config.Invincible:
                        config.total_points += config.points
                    config.longest_survived_time[config.selected_level][config.game_mode] = max(
                        config.longest_survived_time[config.selected_level][config.game_mode], current_time_sec
                    )
                    data_handler.save_data()
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
    for ft in config.floating_texts[:]:  # 使用 [:] 確保刪除時不會出錯
        ft.update()
        ft.draw(screen)
        if ft.timer <= 0:  # 如果文字壽命到了
            config.floating_texts.remove(ft)

    if config.game_state != "start_game":
        config.heart_channel.stop()
    config.current_vol += (config.target_vol - config.current_vol) * 0.005
    pygame.mixer.music.set_volume(config.current_vol)  # 靜音：0, 開聲音：current_vol
    pygame.display.set_caption(screen_text)
    pygame.display.flip()
    if config.last_game_state != config.game_state:
        ui_manager.handle_change_game_state()
pygame.quit()
print("")
print("")

data_handler.save_data()
print(f"已成功儲存檔案到:{active_save}")
print()
sys.exit("掰掰!下次再玩!")
