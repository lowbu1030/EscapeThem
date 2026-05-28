import json
import math
import random

import pygame

import all_buttons
import all_objs
import asset_manager
import config
import data_handler
import tool


class UIManager:
    def __init__(self, screen):
        # 接收主程式傳入的畫布，確保全域唯一
        self.screen = screen
        self.DIFFICULTY_MAP = {
            "easy": tool.Colors.GREEN,
            "normal": tool.Colors.YELLOW,
            "hard": tool.Colors.ORANGE,
            "super_hard": tool.Colors.RED,
            "crazy": tool.Colors.PURPLE,
        }
        self.MODES = ["easy", "normal", "hard", "super_hard", "crazy"]
        self.setting_page = 1
        self.MAX_SETTING_PAGE = 3
        self.skin_display_idx = 0
        self.any_clicked = False  # 有沒有按鈕被點擊（用來控制點擊後的行為只觸發一次）
        self.upgrade_total_pages = len({**config.UPGRADE_SURVIVAL, **config.UPGRADE_COMBAT})

    def clear_all_btn_clicked(self):
        """清除當前頁面所有按鈕的 is_clicked 狀態，確保點擊事件只觸發一次"""
        search_state = config.game_state
        if search_state.startswith("upgrade_p"):
            search_state = "upgrade_p"
        current_objects = all_buttons.buttons.get(search_state, [])
        for obj in current_objects:
            if hasattr(obj, 'is_clicked'):
                obj.is_clicked = False

    def update_max_scroll_height(self):
        """專門用來預算 more_survived_time 頁面的總高度"""
        draw_y = 110
        for _ in config.modes_config:
            draw_y += 90  # 難度標題的高度
            for _ in config.all_levels:
                draw_y += 60  # 關卡資訊的高度
            draw_y -= 25  # 調整間距

        # 算完後存入 config
        config.max_scroll_y = max(0, draw_y - config.HEIGHT + 80)

    def _handle_color_wave(self, obj: all_buttons.Button | all_buttons.TextButton | all_buttons.ImageButton | all_buttons.Line):
        wave_color = tool.Colors.two_color_wave(obj.color_wave[0], obj.color_wave[1], obj.color_wave[2])
        obj.change_base_color(wave_color, force=True)

    def clean_up_current_level_run(self):
        """專門負責玩家中途重來或離開關卡時的結算、重置與清理"""
        tool.collision_time = None
        tool.reset_timer()
        config.player_hp = config.player_max_hp

        if not config.Invincible:
            config.total_points += config.points

        for i in range(2):
            config.alphas[i] = 255

        # 紀錄最高生存時間
        config.longest_survived_time[config.current_world_key][config.selected_level][config.game_mode] = max(
            config.longest_survived_time[config.current_world_key][config.selected_level][config.game_mode], config.current_time_sec
        )

        # 徹底清空關卡資料
        config.reset_game()
        config.player_bullets.clear()

    def _sync_ui_state(self, obj: all_buttons.Button | all_buttons.TextButton | all_buttons.ImageButton | all_buttons.Line):
        if hasattr(obj, "color_wave") and obj.color_wave is not None:
            self._handle_color_wave(obj)

        if config.game_state.startswith("setting_p"):
            if obj.name == "back":
                obj.change_base_text("Back to Pause" if config.from_pause else "Back to Menu")

        if config.game_state == "setting_p1":

            # 處理 Crazy 難度的特殊文字
            if obj.name == "crazy_select":
                obj.current_text = obj.handle_condition(config.has_buy_crazy, "Select", config.crazy_btn_text)
                obj.active = not config.from_pause
                if config.has_buy_crazy:
                    # 已購買：固定顯示 select 並啟用
                    obj.change_base_text("Select")
                    obj.active = True
                    obj.draw_lock = False  # 隱形鎖頭
                else:
                    # 未購買：根據懸停狀態顯示價格或鎖定文字
                    new_text = obj.handle_condition(obj.is_hover, "$10000", config.crazy_btn_text)
                    obj.draw_lock = not obj.is_hover
                    obj.change_base_text(new_text)
                    if config.total_points >= 10000:
                        obj.hover_color = tool.Colors.GREEN
                        obj.pressing_color = tool.Colors.PARIS_GREEN

            if obj.name == "record_level_display":
                # 將 config 中的 level1 轉換為 Lv. 1
                display_text = config.selected_level.replace("level", "Lv. ")
                obj.change_base_text(display_text)
                target_color = self.DIFFICULTY_MAP.get(config.game_mode, tool.Colors.GRAY)

                config.level_button_color = target_color
                obj.change_base_color(target_color, force=True)
                # print(f"[DEBUG]: from 'ui_handler.py':  {obj.normal_color}")

            if obj.name.endswith("_select"):
                mode_name = obj.name.split("_select")[0]
                if config.from_pause:
                    # 🌟 核心修正：如果我是從暫停切過來的，根據你的設計，把特定的按鈕外觀染成灰色！
                    obj.change_base_color(tool.Colors.GRAY)
                else:
                    # 如果是正常從主選單進來的，恢復它原本斑斕的難度彩色
                    obj.change_base_color(self.DIFFICULTY_MAP.get(mode_name, tool.Colors.WHITE))
                if config.game_mode == mode_name:
                    obj.change_base_text("Selected")
                else:
                    obj.change_base_text("Select")
                obj.active = not config.from_pause

            if obj.name.startswith("show_"):
                mode = obj.name[5:]
                # 找到對應的 select 按鈕
                select_btn = next((b for b in all_buttons.buttons["setting_p1"] if b.name == f"{mode}_select"), None)

                if select_btn:
                    # 只要其中一個被懸停，兩個都進入 hover 狀態
                    is_any_hover = obj.is_hover or select_btn.is_hover
                    obj.is_hover = is_any_hover
                    select_btn.is_hover = is_any_hover

                # 顯示與顏色更新
                obj.is_visible = mode == config.game_mode
                # 同步顏色，確保在 from_pause 等狀態下顏色一致
                target_color = tool.Colors.GRAY if config.from_pause else self.DIFFICULTY_MAP.get(mode, tool.Colors.GRAY)
                obj.change_base_color(target_color, force=True)

        if config.game_state == "more_survived_time":
            if obj.name.startswith("info_"):
                obj.rect.y = obj.base_y - config.scroll_ys[0]

                # 檢查是否超出螢幕，超出則隱藏
                obj.is_visible = -50 < obj.rect.y < config.HEIGHT - 80

        if config.game_state == "setting_p2":
            if obj.name == "draw_skin":
                obj.hover_text = obj.handle_condition(config.total_points >= 500, "Draw Skin ($500)", "Not Enough Money!")
                obj.hover_color = obj.handle_condition(config.total_points >= 500, tool.Colors.GREEN, tool.Colors.RED)
                obj.pressing_color = obj.handle_condition(config.total_points >= 500, tool.Colors.PARIS_GREEN, tool.Colors.DARK_RED)
                obj.pressing_text = obj.handle_condition(config.total_points >= 500, "Draw Skin ($500)", "Not Enough Money!")
                obj.active = config.total_points >= 500

            # 1. 取得捲動量與基礎座標
            start_x = 100  # 左邊起始位置
            start_y = 180  # 列表上方起始位置 (空出標題跟金幣的位置)
            row_gap = 80  # 每排之間的垂直距離
            col_gap = 180  # 如果一排想放多個，左右距離
            skin_list = list(config.player_skins.keys())
            total_rows = (len(skin_list) + 1) // 2
            config.max_scroll_y = max(0, total_rows * row_gap - 300)

            # 為了方便抓取，我們找出可見皮膚的名字清單 (對應你生成按鈕時的順序)
            # visible_skin_names = [name for name, data in config.player_skins.items() if config.select_world >= data["can_get_world"]]

            if obj.name == "draw_skin":
                can_afford = config.total_points >= 500
                obj.active = not config.from_pause  # 暫停時禁用

                # 使用 handle_condition 決定顏色與文字
                obj.hover_color = obj.handle_condition(can_afford, tool.Colors.GREEN, tool.Colors.RED)
                obj.change_base_text(obj.handle_condition(can_afford, "Draw Skin ($500)", "Not Enough Money!"))

            if obj.name.startswith("skin_"):
                # 1. 取得該皮膚的原始名稱
                skin_name = obj.name.replace("skin_", "")
                skin_data = config.player_skins.get(skin_name)

                # 2. 檢查是否在當前世界可見 (過濾邏輯)
                if not skin_data or config.worlds_unlocked < skin_data.get("can_get_world", 1):
                    obj.is_visible = False
                    return  # 直接跳過，不累加 skin_display_idx，避免空格

                # 3. 定義基礎座標參數 (這些也可以提早定義在 method 開頭)
                start_x, start_y = 100, 180
                row_gap, col_gap = 80, 180

                # 4. 重新計算座標 (使用手動累加的 self.skin_display_idx)
                # 這樣即便中間有皮膚被隱藏，後面的皮膚也會自動遞補上來排好
                obj.rect.x = start_x + (self.skin_display_idx % 2) * col_gap
                obj.rect.y = start_y + (self.skin_display_idx // 2) * row_gap - config.scroll_ys[4]

                # 5. 設定顯示區域判定 (捲動裁切)
                obj.is_visible = 150 < obj.rect.y < 450

                # 6. 確定要顯示，計數器才 +1
                self.skin_display_idx += 1

                # 7. 準備狀態資料
                is_owned = skin_data["has_owned"]
                is_selected = skin_name == config.current_player_color_name

                # 8. 更新外觀邏輯 (整合 handle_condition)
                # 文字：擁有則顯示名字與等級，否則顯示問號
                display_text = f"{skin_name} Lv.{skin_data['level']}"
                obj.change_base_text(obj.handle_condition(is_owned, display_text, "???"))

                # 顏色：擁有則顯示皮膚顏色，否則顯示灰色
                obj.change_base_color(obj.handle_condition(is_owned, skin_data["color"], tool.Colors.GRAY))

                # 邊框：選中時白色加厚，否則黑色普通
                obj.normal_border_color = obj.handle_condition(is_selected, tool.Colors.WHITE, tool.Colors.BLACK)
                obj.border_width = obj.handle_condition(is_selected, 4, 2)

                # 9. 互動狀態同步
                # 暫停中或是未擁有都不可點擊 (或是你可以自訂未擁有也可以點來跳出提示)
                obj.active = not config.from_pause and is_owned
                # ... (前面的座標計算與 skin_display_idx 累加) ...

                # 新增：繪製經驗條
                if is_owned:  # 利用你剛才定義好的狀態變數
                    bar_y = obj.rect.y + 55  # 直接用 obj.rect.y，舒舒服服
                    max_needed = config.get_upgrade_threshold(skin_data["level"])
                    ratio = min(1.0, skin_data["exp"] / max_needed)

                    # 只有按鈕可見時才畫條
                    if obj.is_visible:
                        pygame.draw.rect(self.screen, tool.Colors.BLACK, (obj.rect.x, bar_y, 150, 5))
                        pygame.draw.rect(self.screen, tool.Colors.GREEN, (obj.rect.x, bar_y, 150 * ratio, 5))
            # print(all_buttons.buttons["setting_p2"][1].rect.x, all_buttons.buttons["setting_p2"][1].rect.y)

        if config.game_state == "choose_file":
            if obj.name.startswith("save_"):
                obj.rect.y = obj.base_y - config.scroll_ys[1]

        if config.game_state == "upgrade_hub":
            if obj.name.startswith("upgrade_p"):
                obj.rect.y = obj.base_y - config.scroll_ys[2]
                obj.is_visible = 0 < obj.rect.y < config.HEIGHT
            if obj.name == "left":
                l_show = config.shop_page == "combat"
                obj.is_visible = l_show
                obj.active = l_show
            if obj.name == "right":
                r_show = config.shop_page == "survival"
                obj.is_visible = r_show
                obj.active = r_show
            if obj.name == "now_mode":
                obj.change_base_text(f"now_mode: {config.shop_page}")

        if config.game_state.startswith("upgrade_p"):
            if obj.name == "upgrade":
                # 1. 💡 抓取數據：先判定當前分頁，拿取正確的設定檔數據
                if config.game_state in config.UPGRADE_COMBAT:
                    cfg = config.UPGRADE_COMBAT[config.game_state]
                else:
                    cfg = config.UPGRADE_SURVIVAL[config.game_state]

                lvl = config.current_levels[config.game_state]
                costs = cfg["costs"]

                # 2. 💡 狀態動態判定：分成「未滿等」與「滿等」兩大路線
                if lvl < cfg["limits"][config.select_world]:
                    cost = costs[lvl]

                    if obj.is_hover:
                        if config.total_points >= cost:
                            # 錢夠，顯示購買後的剩餘金額
                            obj.change_base_text(f"Buy! Left ${tool.num_to_KMBT(round(config.total_points - cost, 1))}")
                            obj.normal_color = tool.Colors.YELLOW
                            obj.hover_color = tool.Colors.GREEN
                            obj.pressing_color = tool.Colors.PARIS_GREEN
                        else:
                            # 錢不夠，警告還差多少錢
                            obj.change_base_text(f"Need: ${tool.num_to_KMBT(round(cost - config.total_points, 1))}")
                            obj.hover_color = tool.Colors.RED
                            obj.pressing_color = tool.Colors.RED
                    else:
                        # 滑鼠沒移上去時，顯示正常的成本價格
                        obj.normal_color = tool.Colors.YELLOW
                        obj.change_base_text(f"Cost: ${tool.num_to_KMBT(cost)}")
                else:
                    # 3. 💡 滿等特殊處理
                    if lvl >= cfg["limits"][config.select_world] and config.select_world < len(config.all_worlds_unlocked):
                        obj.change_base_text(f"Locked: Reach World {config.select_world + 1}")
                    else:
                        obj.change_base_text("MAX LEVEL")
                    obj.change_base_color(tool.Colors.GRAY, force=True)

            if obj.name == "left":
                obj.is_visible = config.current_p_num > 1
            if obj.name == "right":
                obj.is_visible = config.current_p_num < self.upgrade_total_pages

        if config.game_state == "level_select":
            if obj.name == "left":
                obj.is_visible = config.select_world != 1
            if obj.name == "right":
                obj.is_visible = config.select_world < config.worlds_unlocked
            if obj.name.startswith("level_"):
                idx = int(obj.name.split("_")[1])
                is_locked = idx > config.levels_unlocked
                obj.is_next_level = idx == config.levels_unlocked + 1

                # 1. 基礎功能放行
                obj.active = not is_locked or obj.is_next_level
                obj.rect.y = obj.base_y - config.scroll_ys[3]

                # 2. 🌟 實作你的懸停設計！
                if obj.is_next_level and obj.is_hover:
                    # 👉 狀況一：滑鼠移到下一關上面了，開啟「商店模式」
                    obj.draw_lock = False  # 隱形鎖頭

                    # 判斷錢夠不夠
                    cost = config.current_world_costs[idx]  # 注意原本是 i，新架構可以用 idx
                    money_enough = config.total_points >= cost

                    # 動態改寫按鈕內的文字與邊框顏色
                    obj.change_base_text(f"Unlock for ${tool.num_to_KMBT(cost)}")
                    obj.font_size = 18
                    obj.change_base_color(tool.Colors.GRAY)  # 填滿灰色背景
                    obj.hover_border_color = (tool.Colors.GREEN if config.select_world == 1 else tool.Colors.DARK_GREEN) if money_enough else tool.Colors.RED
                    obj.hover_text_color = (tool.Colors.GREEN if config.select_world == 1 else tool.Colors.DARK_GREEN) if money_enough else tool.Colors.RED
                # elif obj.is_next_level:
                #     obj.border_width = 0
                else:
                    # 👉 狀況二：滑鼠離開了，或是其他普通關卡，還原成「原始狀態」
                    obj.change_base_text(f"Level {idx}")  # 還原文字
                    obj.font_size = 26  # 還原字體大小
                    obj.draw_lock = is_locked  # 根據解鎖狀態決定要不要畫鎖
                    obj.change_base_border_color(tool.Colors.WHITE if not is_locked else tool.Colors.GRAY)
                    obj.hover_border_color = tool.Colors.YELLOW if not is_locked else tool.Colors.GRAY
                    obj.change_base_color(tool.Colors.GRAY if is_locked else tool.Colors.BLUE)
                    obj.hover_text_color = tool.Colors.WHITE
            if obj.name.startswith("lines_"):
                obj.start_pos[1] = obj.base_start_y - config.scroll_ys[3]
                obj.end_pos[1] = obj.base_end_y - config.scroll_ys[3]
            if obj.name in ["title", "mask1"]:
                obj.color_wave = [config.world_bgc[config.current_world_key][0], config.world_bgc[config.current_world_key][1], 1]
            if obj.name == "next_world":
                unlock_world_key = f"world{config.select_world + 1}"
                unlock_world = config.select_world + 1
                has_next_world = unlock_world_key in config.world_cost

                # 1. 基礎功能防行與捲軸位置同步
                obj.base_y = 60 + len(config.current_world_costs) * 80
                obj.rect.y = obj.base_y - config.scroll_ys[3]

                # 狀態 A：如果根本沒有下一個世界（全破了）
                if not has_next_world:
                    obj.change_base_text(["Stay tuned", " for new worlds!"])
                    obj.change_base_color(tool.Colors.GRAY)
                    obj.active = False
                    return

                # 抓取目前這個新世界的解鎖狀況與價錢
                is_target_world_locked = unlock_world > config.worlds_unlocked
                world_cost = config.world_cost[unlock_world_key]
                money_enough = config.total_points >= world_cost

                # 狀態 B：如果下一個世界其實早就買過了
                if not is_target_world_locked:
                    obj.change_base_text("Has Unlocked")
                    obj.change_base_color(tool.Colors.GRAY)
                    obj.active = False

                # 狀態 C：🌟 還沒買！發動動態炸裂商店按鈕邏輯！
                else:
                    obj.active = True

                    if obj.is_hover:
                        # 當滑鼠移上去（Collidepoint 邏輯已經被 obj.is_hover 處理好了！）
                        obj.hover_color = obj.handle_condition(config.total_points >= world_cost, tool.Colors.GREEN, tool.Colors.RED)
                        obj.font_size = 24  # 放大字體

                        # 根據錢夠不夠，抽換 hover 家族顏色與多行文字
                        if money_enough:
                            obj.change_base_text(["Buy!", f"(cost: ${tool.num_to_KMBT(world_cost)})"])
                        else:
                            need_money = world_cost - config.total_points
                            obj.change_base_text(["Need More $", f"(need: ${tool.num_to_KMBT(need_money)})"])
                    else:
                        # 當滑鼠離開時，還原成原本的亮綠色與預設多行字
                        obj.change_base_color(tool.Colors.CHARTREUSE)
                        obj.hover_color = obj.handle_condition(config.total_points >= world_cost, tool.Colors.GREEN, tool.Colors.RED)
                        obj.font_size = 22  # 還原字體大小
                        obj.change_base_text(["Next World ", f"(cost: ${tool.num_to_KMBT(world_cost)})"])

        if config.game_state == "playing":
            if obj.name == "hp_bar":
                display_hp = max(math.ceil(config.player_hp), 0)
                hp_ratio = display_hp / config.player_max_hp
                obj.rect.width = 100 * hp_ratio
                obj.change_base_color((*tool.Colors.RED, config.alphas[0]))
            if obj.name == "hp_bar_bg":
                obj.change_base_color((*tool.Colors.DARK_RED, config.alphas[0]))

    def handle_current_state(self, events, mouse_pos):
        self._handle_other_events(events)
        self._handle_scroll_ys()

        # 先用一個變數把要搜尋的 key 存起來
        search_state = config.game_state

        # 如果是 upgrade_p1 ~ p20 的任意子頁面，強行把搜尋 key 導向通用的 "upgrade_p"
        if search_state.startswith("upgrade_p"):
            search_state = "upgrade_p"

        # 這樣就能精準抓到你配置好的 upgrade 和 back 按鈕物件了！
        current_objects = all_buttons.buttons.get(search_state, [])

        self.skin_display_idx = 0  # 每次更新頁面時，皮膚按鈕的顯示索引都從 0 開始
        self.any_clicked = False
        self.clicked_btns = []
        for obj in current_objects[::-1]:  # 倒序繪製，確保後面生成的按鈕在前面（上層）
            if hasattr(obj, 'update'):
                obj.update(events, mouse_pos)

            if obj.name.startswith("skin_"):
                self._sync_ui_state(obj)  # 傳入目前的顯示索引，讓它知道自己是第幾個要顯示的皮膚按鈕
            else:
                self._sync_ui_state(obj)  # 一般按鈕不需要 idx

            if obj.is_clicked:
                self.clicked_btns.append(obj.name)

            # 4. 處理點擊
            if getattr(obj, 'is_clicked', False):
                self.any_clicked = True
                self._handle_actions(obj)
                self.clear_all_btn_clicked()
                break
        for obj in current_objects:
            obj.draw(self.screen)
        # if self.clicked_btns:
        #     print(self.clicked_btns)

    def _handle_scroll_ys(self):
        """專門負責處理各個頁面的 scroll_y 變數，讓它們平滑移動到 target_y"""

        if config.game_state == "more_survived_time":
            config.scroll_ys[0] = tool.update_scrolling(config.scroll_ys[0], config.target_y, smoth=0.1, max_val=config.max_scroll_y)
        if config.game_state == "setting_p2":
            config.target_y = tool.num_range(0, config.max_scroll_y, config.target_y)
            config.scroll_ys[4] = tool.update_scrolling(config.scroll_ys[4], config.target_y, smoth=0.3, max_val=config.max_scroll_y)
        if config.game_state == "choose_file":
            config.target_y = tool.num_range(0, config.max_scroll_y, config.target_y)
            config.scroll_ys[1] = tool.update_scrolling(config.scroll_ys[1], config.target_y, smoth=0.3, max_val=config.max_scroll_y)
        if config.game_state == "upgrade_hub":
            config.target_y = tool.num_range(0, config.max_scroll_y, config.target_y)
            config.scroll_ys[2] = tool.update_scrolling(config.scroll_ys[2], config.target_y, smoth=0.3, max_val=config.max_scroll_y)
        if config.game_state == "level_select":
            config.target_y = tool.num_range(0, config.max_scroll_y, config.target_y)
            config.scroll_ys[3] = tool.update_scrolling(config.scroll_ys[3], config.target_y, smoth=0.3, max_val=config.max_scroll_y)

    def _handle_actions(self, obj: all_buttons.Button | all_buttons.TextButton | all_buttons.ImageButton | all_buttons.Line):
        """專門負責處理按鈕按下後的行為"""
        # 主選單邏輯
        if config.game_state == "menu":
            if obj.name == "start":
                config.game_state = "level_select"
            elif obj.name in ["setting_p1", "left"]:
                config.game_state = "setting_p1"
                self.setting_page = 1
            elif obj.name in ["upgrades", "right"]:
                config.game_state = "upgrade_hub"
            elif obj.name == "quit":
                config.running = False
            elif obj.name == "left":
                config.game_state = "setting_p1"
                self.setting_page = 1
            elif obj.name == "right":
                config.game_state = "upgrade_hub"

        # 設定頁面邏輯
        elif config.game_state.startswith("setting"):
            if obj.name == "back":
                config.game_state = "pause" if config.from_pause else "menu"
            if obj.name == "left":
                self.setting_page = tool.num_range(1, self.MAX_SETTING_PAGE, self.setting_page - 1)
                config.game_state = f"setting_p{self.setting_page}"
            elif obj.name == "right":
                self.setting_page = tool.num_range(1, self.MAX_SETTING_PAGE, self.setting_page + 1)
                config.game_state = f"setting_p{self.setting_page}"
            if config.game_state == "setting_p1":
                for i, mode in enumerate(self.MODES):
                    # 1. 處理 Info 點擊 (這部分你寫得很棒，有 return)
                    if obj.name == f"{mode}_info":
                        config.game_state = "more_survived_time"
                        config.target_y = i * (config.one_mode_height) + 25
                        self.update_max_scroll_height()
                        return

                    # 2. 處理 難度選擇 點擊
                    if obj.name == f"{mode}_select" or obj.name == f"show_{mode}":

                        # 🌟 特殊防禦：如果是點到 crazy，先檢查購買門檻
                        if mode == "crazy":
                            if not config.has_buy_crazy:
                                if config.total_points >= 10000:
                                    config.has_buy_crazy = True
                                    config.total_points -= 10000
                                    asset_manager.buy_channel.play(asset_manager.sounds["buy_success"])
                                    # 💡 注意：這裡「不要」return！讓程式繼續往下走，
                                    # 這樣買完的當下才能順便把難度直接切換到 crazy！
                                else:
                                    asset_manager.buy_channel.play(asset_manager.sounds["buy_error"])
                                    config.floating_texts.append(
                                        tool.FloatingText(
                                            "Not enough points!", 0, config.HEIGHT - 50, tool.Colors.RED, center=True, time=300, size=50
                                        )
                                    )
                                    return  # 錢不夠才需要 return 攔截

                        # 🌟 大眾邏輯：不論是普通難度，還是剛扣完錢的 crazy，通通在這裡完成切換！
                        config.gm_i = i
                        config.game_mode = config.g_m[config.gm_i]
                        config.level_button_color = self.DIFFICULTY_MAP[mode]

                        # 🌟 終極防禦：切換完畢後，一定要「立刻 return」！
                        # 阻止 for 迴圈繼續跑下一圈，按鈕就不會發生靈異失效了！
                        return
            if config.game_state == "setting_p2":
                if obj.name == "draw_skin":
                    if config.total_points >= 500:
                        config.total_points -= 500

                        # 1. 準備抽獎名單與權重
                        skin_names = []
                        weights = []
                        for name, data in config.player_skins.items():
                            if config.worlds_unlocked >= data["can_get_world"]:
                                skin_names.append(name)
                                weights.append(data["draw_weight"])
                        # 2. 抽獎
                        picked_name = random.choices(skin_names, weights=weights)[0]
                        skin = config.player_skins[picked_name]
                        if not skin["has_owned"]:
                            skin["has_owned"] = True
                            config.floating_texts.append(
                                tool.FloatingText(
                                    f"You got a {picked_name} skin!",
                                    0,
                                    config.HEIGHT - 50,
                                    tool.Colors.GREEN,
                                    center=True,
                                    time=300,
                                    size=50,
                                )
                            )
                        else:
                            # 重複抽到，增加經驗值
                            skin["exp"] += 50

                            target_exp = config.get_upgrade_threshold(skin["level"])

                            if skin["exp"] >= target_exp:
                                skin["exp"] -= target_exp
                                skin["level"] += 1
                                config.floating_texts.append(
                                    tool.FloatingText(
                                        f"{picked_name} level_up! Lv.{skin['level']}",
                                        0,
                                        config.HEIGHT - 50,
                                        tool.Colors.BLUE,
                                        center=True,
                                        time=300,
                                        size=50,
                                    )
                                )
                            config.last_draw_color = picked_name
                        data_handler.save_data()
                        asset_manager.buy_channel.play(asset_manager.sounds["buy_success"])
                    else:
                        asset_manager.buy_channel.play(asset_manager.sounds["buy_error"])
                        config.floating_texts.append(
                            tool.FloatingText("Not enough points!", 0, config.HEIGHT - 50, tool.Colors.RED, center=True, time=300, size=50)
                        )
                if obj.name.startswith("skin_"):
                    skin_name = obj.name.replace("skin_", "")
                    if config.player_skins[skin_name]["has_owned"]:
                        config.current_player_color_name = skin_name
                        config.now_player_skin = config.player_skins[skin_name]["color"]
                        obj.normal_border_color = tool.Colors.WHITE
                        # print(f"[DEBUG]: from 'ui_handler.py:  {config.now_player_skin}")
                    else:
                        obj.normal_border_color = tool.Colors.BLACK
                        config.floating_texts.append(
                            tool.FloatingText(
                                "You don't own this skin!", 0, config.HEIGHT - 50, tool.Colors.RED, center=True, time=300, size=50
                            )
                        )
            if config.game_state == "setting_p3":
                if obj.name == "open_other_save":
                    config.game_state = "choose_file"
                if obj.name == "open_new_game":
                    try:
                        with open("save_game.json", "w", encoding="utf-8") as f:
                            json.dump(data_handler.initial_data, f, indent=4)

                        # 成功寫入後才執行讀取與重置
                        data_handler.load_data()
                        config.load_resets()

                        print("✔️ New game initialized!")
                        config.game_state = "menu"

                    except Exception as e:
                        print(f"Error creating new save: {e}")
                        config.floating_texts.append(
                            tool.FloatingText(
                                "Failed to create new save!", 0, config.HEIGHT - 50, tool.Colors.RED, center=True, time=300, size=50
                            )
                        )

                    print("存檔已建立！")
                    config.game_state = "menu"

        elif config.game_state == "more_survived_time":
            if obj.name == "back":
                config.game_state = "setting_p1"

        elif config.game_state == "choose_file":
            if obj.name == "back":
                config.game_state = "setting_p3"
            elif obj.name.startswith("save_"):
                # 點擊存檔按鈕後，讀取對應的存檔
                try:
                    data_handler.save_data()
                    data_handler.load_data(obj.save_path)
                    config.load_resets()
                    print(f"✔️ Loaded save from {obj.save_path}!")
                    config.game_state = "menu"
                except Exception as e:
                    print(f"Error loading save: {e}")
                    config.floating_texts.append(
                        tool.FloatingText("Failed to load save!", 0, config.HEIGHT - 50, tool.Colors.RED, center=True, time=300, size=50)
                    )

        elif config.game_state == "upgrade_hub":
            if obj.name == "left":
                config.shop_page = "survival"
                config.update_upgrade_hub_layout()
                self.handle_change_game_state()
                self._sync_ui_state(obj)  # 立即更新按鈕狀態，確保切換頁面時按鈕顯示正確
            if obj.name == "right":
                config.shop_page = "combat"
                config.update_upgrade_hub_layout()
                self.handle_change_game_state()
                self._sync_ui_state(obj)
            if obj.name == "back_upg_hub":
                config.game_state = "menu"
            if obj.name.startswith("upgrade_p"):
                config.game_state = obj.name
                config.current_p_num = int(obj.name.replace("upgrade_p", ""))

        elif config.game_state.startswith("upgrade_p"):

            if obj.name == "upgrade":

                # 撈取對應的數據
                if config.game_state in config.UPGRADE_COMBAT:
                    cfg = config.UPGRADE_COMBAT[config.game_state]
                else:
                    cfg = config.UPGRADE_SURVIVAL[config.game_state]

                lvl = config.current_levels[config.game_state]
                costs = cfg["costs"]
                if lvl < cfg["limits"][config.select_world]:
                    cost = costs[lvl]

                    if config.total_points >= cost:
                        # 扣錢、升級
                        config.total_points -= cost
                        config.current_levels[config.game_state] += 1
                        config.lv_flash_timer = 20  # 啟動文字閃爍

                        data_handler.save_data()  # 儲存

                        # 生成扣錢噴字
                        new_text = tool.FloatingText(
                            "-" + tool.num_to_KMBT(cost), config.WIDTH - 90, 20, tool.Colors.RED, speed=0.7, size=24
                        )
                        config.floating_texts.append(new_text)

                        # 音效與金閃閃特效
                        asset_manager.buy_channel.play(asset_manager.sounds["buy_success"])
                        config.now_flash_color = tool.Colors.GOLD
                        config.flash_timer = config.total_flash_time

                        # 重新計算技能
                        config.update_skill()

                        # 💡 讓按鈕原地自我重新整理（把 Buy! 變回正常的 Cost 或 MAX）
                        self._sync_ui_state(obj)

                    else:
                        # 錢不夠，播放錯誤音效
                        asset_manager.buy_channel.play(asset_manager.sounds["buy_error"])
                else:
                    # 滿等(或到達選擇世界的等級上限)還硬點，噴出滿等提示
                    if lvl >= cfg["limits"][config.select_world] and config.select_world < len(config.all_worlds_unlocked):
                        asset_manager.buy_channel.play(asset_manager.sounds["buy_error"])
                    new_text = tool.FloatingText(
                        (
                            f"Locked: Reach World {config.select_world + 1}"
                            if lvl >= cfg["limits"][config.select_world] and config.select_world < len(config.all_worlds_unlocked)
                            else "MAX LEVEL!"
                        ),
                        250,
                        config.HEIGHT - 200,
                        tool.Colors.RED,
                        speed=0.7,
                        size=24,
                    )
                    config.floating_texts.append(new_text)
            if obj.name == "back_upg":
                config.game_state = "upgrade_hub"

            if obj.name == "left":
                config.current_p_num = tool.num_range(1, self.upgrade_total_pages, config.current_p_num - 1)
                config.game_state = f"upgrade_p{config.current_p_num}"
            if obj.name == "right":
                config.current_p_num = tool.num_range(1, self.upgrade_total_pages, config.current_p_num + 1)
                config.game_state = f"upgrade_p{config.current_p_num}"

        elif config.game_state == "level_select":
            if obj.name == "back":
                config.game_state = "menu"
            if obj.name == "left":
                config.select_world = max(1, config.select_world - 1)
                config.update_current_world_data(config.select_world)
                config.scroll_ys[3] = 0  # 切換世界時重置捲軸位置
                self.handle_change_game_state()
            if obj.name == "right":
                config.select_world = min(config.worlds_unlocked, config.select_world + 1)
                config.update_current_world_data(config.select_world)
                config.scroll_ys[3] = 0  # 切換世界時重置捲軸位置
                self.handle_change_game_state()
            if obj.name.startswith("level_"):
                idx = int(obj.name.split("_")[1])
                if idx <= config.levels_unlocked:
                    config.selected_level = f"level{idx}"
                    config.lv_i = idx - 1
                    data = all_objs.get_level_data(idx, config.select_world)
                    config.current_setup = {
                        "enemies": data[0],
                        "cannons": data[1],
                        "obstacles": data[2],
                        "multiplier": data[3],
                        "name": data[4],
                    }
                    config.game_state = "countdown"
                    config.reset_game()
                    config.print_coin_chance()
                    config.update_skill()
                elif obj.is_next_level:
                    # 👉 狀況 B：是還可以挑戰的「下一關」，點擊觸發「商店解鎖邏輯」
                    cost = config.current_world_costs[idx]

                    if config.total_points >= cost:
                        # 錢夠，扣錢並正式宣告解鎖！
                        config.total_points -= cost
                        config.levels_unlocked = idx  # 關卡解鎖進度正式推進

                        # 生成扣錢的漂浮噴字（直接引用你原本設計的 FloatingText）
                        new_text = tool.FloatingText(
                            "-" + tool.num_to_KMBT(cost), config.WIDTH - 90, 20, tool.Colors.RED, speed=0.7, size=24
                        )
                        config.floating_texts.append(new_text)

                        # 播放成功的金幣音效
                        asset_manager.sounds["buy_success"].play()

                        # 儲存與重整世界資料，確保畫面原地刷新
                        config.update_world_data(config.select_world)
                    else:
                        # 錢不夠，無情噴出錯誤音效
                        asset_manager.sounds["buy_error"].play()
            if obj.name == "next_world":
                unlock_world_key = f"world{config.select_world + 1}"
                cost = config.world_cost[unlock_world_key]
                if config.total_points >= cost:
                    config.total_points -= cost
                    config.worlds_unlocked = config.select_world + 1  # 世界解鎖進度正式推進

                    new_text = tool.FloatingText("-" + tool.num_to_KMBT(cost), config.WIDTH - 90, 20, tool.Colors.RED, speed=0.7, size=24)
                    config.floating_texts.append(new_text)

                    asset_manager.sounds["buy_success"].play()
                    config.update_current_world_data(config.select_world)
                else:
                    asset_manager.sounds["buy_error"].play()

        elif config.game_state == "pause":
            if obj.name == "resume":
                if not config.countdowning:
                    config.game_state = "playing"
                else:
                    config.game_state = "countdown"
            if obj.name == "settings":
                config.from_pause = True
                config.game_state = f"setting_p{self.setting_page}"
            if obj.name == "restart":
                self.clean_up_current_level_run()
                config.game_state = "countdown"
            if obj.name == "menu":
                self.clean_up_current_level_run()
                config.from_pause = False
                config.game_state = "menu"
            if obj.name == "quit":
                config.player_hp = config.player_max_hp
                if not config.Invincible:
                    config.total_points += config.points
                config.longest_survived_time[config.current_world_key][config.selected_level][config.game_mode] = max(
                    config.longest_survived_time[config.current_world_key][config.selected_level][config.game_mode], config.current_time_sec
                )
                config.reset_game()
                config.running = False

        elif config.game_state == "game_over":
            if obj.name == "back":
                config.from_pause = False
                config.game_state = "menu"
                tool.collision_time = None
                tool.reset_timer()
                for ft in config.floating_texts[:]:
                    ft.reset()

        elif config.game_state == "afk_kick":
            if obj.name == "kick":
                raise config.AFKError()

        else:
            if obj.name == "back":
                config.player_hp = config.player_max_hp
                if not config.Invincible:
                    config.total_points += config.points
                config.longest_survived_time[config.current_world_key][config.selected_level][config.game_mode] = max(
                    config.longest_survived_time[config.current_world_key][config.selected_level][config.game_mode], config.current_time_sec
                )
                data_handler.save_data()
                config.reset_game()
                config.game_state = "menu"

    def _handle_other_events(self, events):
        # 處理單次按下的快速鍵
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    config.running = False

                if config.game_state.startswith("setting"):
                    if event.key in [pygame.K_LEFT, pygame.K_a]:
                        self.setting_page = tool.num_range(1, self.MAX_SETTING_PAGE, self.setting_page - 1)
                        config.game_state = f"setting_p{self.setting_page}"
                    if event.key in [pygame.K_RIGHT, pygame.K_d]:
                        self.setting_page = tool.num_range(1, self.MAX_SETTING_PAGE, self.setting_page + 1)
                        config.game_state = f"setting_p{self.setting_page}"
                    if event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                        config.game_state = "menu"

                if config.game_state in ["more_survived_time", "choose_file"]:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        # 返回到原本的 settings 頁面
                        config.game_state = f"setting_p{self.setting_page}"

                if config.game_state == "upgrade_hub":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        config.game_state = "menu"
                    if event.key in [pygame.K_LEFT, pygame.K_a] and config.shop_page == "combat":
                        config.shop_page = "survival"
                        config.update_upgrade_hub_layout()
                        self.handle_change_game_state()
                        for obj in all_buttons.buttons["upgrade_hub"]:
                            self._sync_ui_state(obj)
                    if event.key in [pygame.K_RIGHT, pygame.K_d] and config.shop_page == "survival":
                        config.shop_page = "combat"
                        config.update_upgrade_hub_layout()
                        self.handle_change_game_state()
                        for obj in all_buttons.buttons["upgrade_hub"]:
                            self._sync_ui_state(obj)

                if config.game_state.startswith("upgrade_p"):
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        config.game_state = "upgrade_hub"
                    if event.key in [pygame.K_LEFT, pygame.K_a]:
                        config.current_p_num = tool.num_range(1, self.upgrade_total_pages, config.current_p_num - 1)
                        config.game_state = f"upgrade_p{config.current_p_num}"
                    if event.key in [pygame.K_RIGHT, pygame.K_d]:
                        config.current_p_num = tool.num_range(1, self.upgrade_total_pages, config.current_p_num + 1)
                        config.game_state = f"upgrade_p{config.current_p_num}"
                    if event.key == pygame.K_SPACE:
                        # 撈取對應的數據
                        if config.game_state in config.UPGRADE_COMBAT:
                            cfg = config.UPGRADE_COMBAT[config.game_state]
                        else:
                            cfg = config.UPGRADE_SURVIVAL[config.game_state]

                        lvl = config.current_levels[config.game_state]
                        costs = cfg["costs"]
                        if lvl < cfg["limits"][config.select_world]:
                            cost = costs[lvl]

                            if config.total_points >= cost:
                                # 扣錢、升級
                                config.total_points -= cost
                                config.current_levels[config.game_state] += 1
                                config.lv_flash_timer = 20  # 啟動文字閃爍

                                data_handler.save_data()  # 儲存

                                # 生成扣錢噴字
                                new_text = tool.FloatingText(
                                    "-" + tool.num_to_KMBT(cost), config.WIDTH - 90, 20, tool.Colors.RED, speed=0.7, size=24
                                )
                                config.floating_texts.append(new_text)

                                # 音效與金閃閃特效
                                asset_manager.buy_channel.play(asset_manager.sounds["buy_success"])
                                config.now_flash_color = tool.Colors.GOLD
                                config.flash_timer = config.total_flash_time

                                # 重新計算技能
                                config.update_skill()

                                # 💡 讓按鈕原地自我重新整理（把 Buy! 變回正常的 Cost 或 MAX）
                                obj = next((b for b in all_buttons.buttons["upgrade_p"] if b.name == "upgrade"), None)
                                if obj is not None:
                                    self._sync_ui_state(obj)

                            else:
                                # 錢不夠，播放錯誤音效
                                asset_manager.buy_channel.play(asset_manager.sounds["buy_error"])
                        else:
                            # 滿等(或到達選擇世界的等級上限)還硬點，噴出滿等提示
                            if lvl >= cfg["limits"][config.select_world] and config.select_world < len(config.all_worlds_unlocked):
                                asset_manager.buy_channel.play(asset_manager.sounds["buy_error"])
                            new_text = tool.FloatingText(
                                (
                                    f"Locked: Reach World {config.select_world + 1}"
                                    if lvl >= cfg["limits"][config.select_world] and config.select_world < len(config.all_worlds_unlocked)
                                    else "MAX LEVEL!"
                                ),
                                250,
                                config.HEIGHT - 200,
                                tool.Colors.RED,
                                speed=0.7,
                                size=24,
                            )
                            config.floating_texts.append(new_text)

                if config.game_state == "level_select":
                    if event.key in [pygame.K_LEFT, pygame.K_a]:
                        config.select_world = max(1, config.select_world - 1)
                        config.update_current_world_data(config.select_world)
                        config.scroll_ys[3] = 0  # 切換世界時重置捲軸位置
                        self.handle_change_game_state()
                    if event.key in [pygame.K_RIGHT, pygame.K_d]:
                        config.select_world = min(config.worlds_unlocked, config.select_world + 1)
                        config.update_current_world_data(config.select_world)
                        config.scroll_ys[3] = 0  # 切換世界時重置捲軸位置
                        self.handle_change_game_state()

                if config.game_state == "pause":
                    if event.key == pygame.K_ESCAPE:
                        if not config.countdowning:
                            config.game_state = "playing"
                        else:
                            config.game_state = "countdown"
                    if event.key == pygame.K_r:
                        self.clean_up_current_level_run()
                        config.game_state = "countdown"
                    if event.key == pygame.K_c:
                        config.player_hp = config.player_max_hp
                        if not config.Invincible:
                            config.total_points += config.points
                        config.longest_survived_time[config.selected_level][config.game_mode] = max(
                            config.longest_survived_time[config.selected_level][config.game_mode], config.current_time_sec
                        )
                        config.running = False

                if config.game_state == "game_over":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        config.game_state = "menu"
                        tool.collision_time = None
                        tool.reset_timer()
                        for ft in config.floating_texts[:]:
                            ft.reset()

                if config.game_state == "afk_kick":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        raise config.AFKError()

            if event.type == pygame.MOUSEWHEEL:
                if config.game_state == "setting_p1":
                    config.lv_i += 1 if event.y < 0 else -1
                    config.lv_i %= len(config.all_levels)
                    config.selected_level = config.all_levels[config.lv_i]
                if config.game_state == "more_survived_time":
                    config.target_y -= event.y * 30
                if config.game_state == "setting_p2":
                    config.target_y -= event.y * 30
                if config.game_state == "choose_file":
                    config.target_y -= event.y * 30
                if config.game_state == "upgrade_hub":
                    config.target_y -= event.y * 30
                if config.game_state.startswith("upgrade_p"):
                    if event.y < 0 and config.current_p_num < self.upgrade_total_pages:
                        config.game_state = f"upgrade_p{config.current_p_num + 1}"
                    elif event.y > 0 and config.current_p_num > 1:
                        config.game_state = f"upgrade_p{config.current_p_num - 1}"
                if config.game_state == "level_select":
                    config.target_y -= event.y * 30

            if event.type == pygame.QUIT:
                if config.game_state == "afk_kick":
                    raise config.AFKError()

        # 處理長按或單次按下的方向鍵
        keys = pygame.key.get_pressed()
        if config.game_state == "menu":
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                config.game_state = "setting_p1"
                self.setting_page = 1
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                config.game_state = "upgrade_hub"
        if config.game_state == "upgrade_hub":
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                config.target_y -= 10
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                config.target_y += 10

        if config.game_state == "setting_p2":
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                config.target_y -= 8
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                config.target_y += 8

    def handle_change_game_state(self):
        config.target_y = 0
        # 這段處理每次「狀態切換」時動態更新
        for s in range(len(config.scroll_ys)):
            config.scroll_ys[s] = 0  # 切換頁面時重置捲動位置
        all_objs.text_cache.clear()
        if config.game_state.startswith("settings"):
            # 找到那個 back 按鈕
            current_btns = all_buttons.buttons.get(config.game_state, [])
            for btn in current_btns:
                if btn.name == "back":
                    new_text = "BACK TO PAUSE" if config.from_pause else "BACK TO MENU"
                    btn.change_base_text(new_text)  # 使用你寫的修改函式
        if config.game_state == "menu":
            for i in range(2):
                config.alphas[i] = 255
        if config.game_state == "more_survived_time":
            all_buttons.buttons["more_survived_time"] = [
                obj for obj in all_buttons.buttons["more_survived_time"] if not obj.name.startswith("info_")
            ]

            draw_y = 110
            for gm in config.modes_config:
                # 建立按鈕
                btn4 = all_buttons.TextButton(
                    name=f"info_{gm[0]}",
                    text=f"{gm[0].replace('_', ' ').title()} Mode",
                    # 注意：這裡存入的是「不帶捲動」的原始座標
                    rect=pygame.Rect(0, draw_y, 270, 60),
                    button_color=gm[1],
                    text_color=tool.Colors.BLACK if gm[0] in ["easy", "normal"] else tool.Colors.WHITE,
                    font_size=34,
                    screen_center=True,
                )
                all_buttons.buttons["more_survived_time"].insert(0, btn4)

                # 計算下一個項目的 Y (包含間距與關卡數)
                draw_y += 90 + (len(config.all_levels) * 60) - 25
        if config.game_state == "choose_file":
            all_buttons.buttons["choose_file"] = [obj for obj in all_buttons.buttons["choose_file"] if not obj.name.startswith("save_")]
            for i, save in enumerate(data_handler.save_files):
                btn = all_objs.TextButton(
                    name=f"save_{save.stem}",
                    text=save.stem,
                    button_color=tool.Colors.BLUE2,
                    text_color=tool.Colors.WHITE,
                    rect=pygame.Rect(0, 150 + i * 70, 300, 60),
                    font_size=26,
                    screen_center=True,
                )
                btn.save_path = save  # 把路徑存在按鈕物件裡，點擊時可以直接讀取
                btn.base_y = 150 + i * 70

                all_buttons.buttons["choose_file"].insert(0, btn)
            config.max_scroll_y = max(80, len(data_handler.save_files) * 70 - 300)
        if config.game_state == "upgrade_hub":
            self.upgrade_total_pages = len({**config.UPGRADE_SURVIVAL, **config.UPGRADE_COMBAT})
            # 1. 為了防重複堆疊，先清空舊的 upg_ 開頭按鈕
            all_buttons.buttons["upgrade_hub"] = [obj for obj in all_buttons.buttons["upgrade_hub"] if not obj.name.startswith("upgrade_p")]
            # current_config = config.UPGRADE_SURVIVAL if config.shop_page == "survival" else config.UPGRADE_COMBAT
            # 3. 用迴圈動態建立升級按鈕
            # 這裡需要一個計數器 i 來排 Y 座標
            config.update_upgrade_hub_layout()
            for i, (upg_key, val) in enumerate(config.upgrade_hub_layout.items()):
                # 計算每個升級按鈕的原始 Y 座標
                # 提示：你可以用 160 + i * 90 讓它們垂直整齊排列
                calc_y = 160 + i * 100
                btn = all_objs.TextButton(
                    name=upg_key,
                    text=val["title"],  # 初步將底線換成空格並大寫
                    button_color=val["color"],
                    text_color=tool.Colors.BLACK,
                    rect=pygame.Rect(0, calc_y, 500, 80),  # 這裡先傳絕對座標，捲動交給 _sync_ui_state 處理
                    font_size=25,
                    screen_center=True,
                )

                btn.base_y = calc_y

                all_buttons.buttons["upgrade_hub"].insert(0, btn)  # 插在前面，確保在 back 按鈕下面

            total_content_height = 160 + (len(config.upgrade_hub_layout) * 90) + 90

            bottom_mask_y = config.HEIGHT - 120

            config.max_scroll_y = max(0, total_content_height - bottom_mask_y + 30)
        if config.game_state == "level_select":
            config.update_current_world_data(config.select_world)
            all_buttons.buttons["level_select"] = [obj for obj in all_buttons.buttons["level_select"] if not obj.name.startswith("level_")]

            for i in range(1, len(config.current_world_costs)):
                is_locked = i > config.levels_unlocked  # 這裡使用剛剛取出的數字
                is_next_level = i == config.levels_unlocked + 1
                level_button = all_objs.TextButton(
                    name=f"level_{i}",
                    text=f"Level {i}",
                    button_color=tool.Colors.BLUE if not is_locked else tool.Colors.GRAY,
                    text_color=tool.Colors.WHITE,
                    rect=pygame.Rect(120, 60 + i * 80, 200, 60),
                    font_size=26,
                    border_width=2,
                    normal_border_color=tool.Colors.WHITE if not is_locked else None,
                    hover_border_color=tool.Colors.YELLOW if not is_locked else None,
                    screen_center=False,
                )
                level_button.base_y = 60 + i * 80
                level_button.active = (not is_locked) or is_next_level
                level_button.is_next_level = is_next_level  # 給按鈕一個屬性，讓它知道自己是不是下一關
                all_buttons.buttons["level_select"].insert(0, level_button)
            total_content_height = (len(config.current_world_costs) + 2) * 80 + 100

            # 最大捲動距離 = 總長度 減去 畫面高度 (600)
            config.max_scroll_y = max(0, total_content_height - config.HEIGHT)
            for i in range(1, len(config.current_world_costs)):
                btn = all_objs.Line(
                    name=f"lines_{i}",
                    start_pos=(50, 130 + i * 80),
                    end_pos=(600, 130 + i * 80),
                    width=2,
                    normal_color=tool.Colors.WHITE,
                )
                all_buttons.buttons["level_select"].insert(0, btn)


def coin_rect(player_rect=pygame.Rect(5000, 5000, 0, 0)):  # noqa: B008
    diff = config.total_points - config.target_points

    if abs(diff) < 0.1:
        config.target_points = config.total_points
    else:
        config.target_points += diff * 0.1
    final_text = "$" + tool.num_to_KMBT(config.target_points)

    new_alpha = 255
    config.coin_rect2 = pygame.Rect(config.WIDTH - 110, 0, 100, 100)

    if player_rect.colliderect(config.coin_rect2):
        new_alpha = 100

    if new_alpha == 255:
        for enemy in config.enemy_list:
            if not getattr(enemy, "show", True):
                continue  # 沒出現的不算
            e_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)

            # 怪物碰到右上 OR 碰到左上，兩個一起變透明
            if e_rect.colliderect(config.coin_rect2):
                new_alpha = 100
                break

    if config.game_state == "3!2!1!":
        new_alpha = 255

    # --- 4. 同步套用到所有相關圖片 ---
    config.alphas[0] = new_alpha if config.game_state == "start_game" else 255

    # 讓金幣框變透明
    asset_manager.coin_wood_img_surface.set_alpha(config.alphas[0])
    config.screen.blit(asset_manager.coin_wood_img_surface, asset_manager.coin_wood_rect)

    # 文字也要同步
    import all_objs

    all_objs.show_text(config.screen, final_text, tool.Colors.WHITE, config.WIDTH - 60, 32, size=22, alpha=config.alphas[0], center=True)
