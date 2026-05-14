import json
import random

import pygame

import all_buttons
import button_obj
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
        self.skin_display_idx = 0

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

    def _sync_ui_state(self, obj: all_buttons.Button | all_buttons.TextButton | all_buttons.ImageButton):
        state = config.game_state

        if state == "setting_p1":

            # 處理 Crazy 難度的特殊文字
            if obj.name == "crazy_select":
                obj.current_text = obj.handle_condition(config.has_buy_crazy, "select", config.crazy_btn_text)
                obj.active = config.has_buy_crazy
                if config.has_buy_crazy:
                    # 已購買：固定顯示 select 並啟用
                    obj.change_base_text("select")
                    obj.active = True
                else:
                    # 未購買：根據懸停狀態顯示價格或鎖定文字，並禁用
                    new_text = obj.handle_condition(obj.is_hover, "$10000", config.crazy_btn_text)
                    obj.change_base_text(new_text)
                    obj.active = False

            elif obj.name == "crazy_lock":
                crazy_btn = next((b for b in all_buttons.buttons[state] if b.name == "crazy_select"), None)
                is_hovering_crazy = crazy_btn.is_hover if crazy_btn else False

                obj.visible = not config.has_buy_crazy and config.lock_img_loaded and not is_hovering_crazy
            elif obj.name == "record_level_display":
                # 將 config 中的 level1 轉換為 Lv. 1
                display_text = config.selected_level.replace("level", "Lv. ")
                obj.change_base_text(display_text)
                target_color = self.DIFFICULTY_MAP.get(config.game_mode, tool.Colors.GRAY)

                config.level_button_color = target_color
                obj.change_base_color(target_color, force=True)
                # print(f"[DEBUG]: from 'ui_handler.py':  {obj.normal_color}")

            elif obj.name.endswith("_select"):
                obj.active = not config.from_pause

            elif obj.name.startswith("show_"):
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
                target_color = self.DIFFICULTY_MAP.get(mode, tool.Colors.GRAY)
                obj.change_base_color(target_color, force=True)

        if state == "more_survived_time":
            if obj.name.startswith("info_"):
                obj.rect.y = obj.base_y - config.scroll_ys[0]

                # 檢查是否超出螢幕，超出則隱藏
                obj.is_visible = -50 < obj.rect.y < config.HEIGHT - 80

        if state == "setting_p2":
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
                if not skin_data or config.select_world < skin_data.get("can_get_world", 1):
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
                if is_owned: # 利用你剛才定義好的狀態變數
                    bar_y = obj.rect.y + 55  # 直接用 obj.rect.y，舒舒服服
                    max_needed = config.get_upgrade_threshold(skin_data["level"])
                    ratio = min(1.0, skin_data["exp"] / max_needed)

                    # 只有按鈕可見時才畫條
                    if obj.is_visible:
                        pygame.draw.rect(self.screen, tool.Colors.BLACK, (obj.rect.x, bar_y, 150, 5))
                        pygame.draw.rect(self.screen, tool.Colors.GREEN, (obj.rect.x, bar_y, 150 * ratio, 5))
            # print(all_buttons.buttons["setting_p2"][1].rect.x, all_buttons.buttons["setting_p2"][1].rect.y)

        if state == "choose_file":
            if obj.name.startswith("save_"):
                obj.rect.y = obj.base_y - config.scroll_ys[1]
                obj.is_visible = 80 < obj.rect.y < 450

    def handle_current_state(self, events, mouse_pos):
        self._handle_other_events(events)

        if config.game_state == "more_survived_time":
            config.scroll_ys[0] = tool.update_scrolling(config.scroll_ys[0], config.target_y, smoth=0.3, max_val=config.max_scroll_y)
        if config.game_state == "setting_p2":
            config.target_y = tool.num_range(0, config.target_y, config.max_scroll_y)
            config.scroll_ys[4] = tool.update_scrolling(config.scroll_ys[4], config.target_y, smoth=0.3, max_val=config.max_scroll_y)
        if config.game_state == "choose_file":
            config.target_y = tool.num_range(0, config.target_y, config.max_scroll_y)
            config.scroll_ys[1] = tool.update_scrolling(config.scroll_ys[1], config.target_y, smoth=0.3, max_val=config.max_scroll_y)

        # 1. 抓取物件清單
        current_objects = all_buttons.buttons.get(config.game_state, [])

        self.skin_display_idx = 0  # 每次更新頁面時，皮膚按鈕的顯示索引都從 0 開始

        for obj in current_objects:
            if hasattr(obj, 'update'):
                obj.update(events, mouse_pos)

            if obj.name.startswith("skin_"):
                self._sync_ui_state(obj)  # 傳入目前的顯示索引，讓它知道自己是第幾個要顯示的皮膚按鈕
            else:
                self._sync_ui_state(obj)  # 一般按鈕不需要 idx

            # 3. 繪製
            obj.draw(self.screen)

            # 4. 處理點擊
            if getattr(obj, 'is_clicked', False):
                self._handle_actions(obj)

    def _handle_actions(self, obj: all_buttons.Button | all_buttons.TextButton | all_buttons.ImageButton):
        """專門負責處理按鈕按下後的行為"""
        # 主選單邏輯
        if config.game_state == "menu":
            if obj.name == "start":
                config.game_state = "level_select"
            elif obj.name in ["setting_p1", "left"]:
                config.game_state = "setting_p1"
            elif obj.name in ["upgrades", "right"]:
                config.game_state = "upgrade_hub"
            elif obj.name == "quit":
                config.running = False
            elif obj.name == "left":
                config.game_state = "setting_p1"
            elif obj.name == "right":
                config.game_state = "upgrade_hub"

        # 設定頁面邏輯
        elif config.game_state.startswith("setting"):
            if obj.name == "back":
                config.game_state = "pause" if config.from_pause else "menu"
            if obj.name == "left":
                self.setting_page = tool.num_range(1, 4, self.setting_page - 1)
                config.game_state = f"setting_p{self.setting_page}"
            elif obj.name == "right":
                self.setting_page = tool.num_range(1, 4, self.setting_page + 1)
                config.game_state = f"setting_p{self.setting_page}"
            if config.game_state == "setting_p1":
                for i, mode in enumerate(self.MODES):
                    if obj.name == f"{mode}_info":
                        config.game_state = "more_survived_time"
                        # 根據 index (i) 計算目標高度
                        config.target_y = i * (config.one_mode_height) + 25
                        self.update_max_scroll_height()
                        return
                    elif obj.name == f"{mode}_select" or obj.name == f"show_{mode}":
                        config.game_mode = mode
                        config.level_button_color = self.DIFFICULTY_MAP[mode]
                        # print(f"[DEBUG]: from 'ui_handler.py:  {config.level_button_color}")
                        return
            if config.game_state == "setting_p2":
                if obj.name == "draw_skin":
                    if config.total_points >= 500:
                        config.total_points -= 500

                        # 1. 準備抽獎名單與權重
                        skin_names = []
                        weights = []
                        for name, data in config.player_skins.items():
                            if config.select_world >= data["can_get_world"]:
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
                        config.buy_channel.play(config.sounds["buy_success"])
                    else:
                        config.buy_channel.play(config.sounds["buy_error"])
                        config.floating_texts.append(
                            tool.FloatingText("Not enough points!", 0, config.HEIGHT - 50, tool.Colors.RED, center=True, time=300, size=50)
                        )
                if obj.name.startswith("skin_"):
                    skin_name = obj.name.replace("skin_", "")
                    if config.player_skins[skin_name]["has_owned"]:
                        config.current_player_color_name = skin_name
                        config.now_player_skin = config.player_skins[skin_name]["color"]
                        obj.border_color = tool.Colors.WHITE
                        # print(f"[DEBUG]: from 'ui_handler.py:  {config.now_player_skin}")
                    else:
                        obj.border_color = tool.Colors.BLACK
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
                            json.dump(config.initial_data, f, indent=4)

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
                        tool.FloatingText(
                            "Failed to load save!", 0, config.HEIGHT - 50, tool.Colors.RED, center=True, time=300, size=50
                        )
                    )

    def _handle_other_events(self, events):
        # 處理單次按下的快速鍵
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    config.running = False

                if config.game_state.startswith("setting"):
                    if event.key in [pygame.K_LEFT, pygame.K_a]:
                        self.setting_page = tool.num_range(1, 4, self.setting_page - 1)
                        config.game_state = f"setting_p{self.setting_page}"
                    if event.key in [pygame.K_RIGHT, pygame.K_d]:
                        self.setting_page = tool.num_range(1, 4, self.setting_page + 1)
                        config.game_state = f"setting_p{self.setting_page}"
                    if event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                        config.game_state = "menu"

                if config.game_state == "more_survived_time":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        # 返回到原本的 settings 頁面
                        config.game_state = f"setting_p{self.setting_page}"
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

        # 處理長按或單次按下的方向鍵
        keys = pygame.key.get_pressed()
        if config.game_state == "menu":
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                config.game_state = "setting_p1"
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                config.game_state = "upgrade_hub"

    def handle_change_game_state(self):
        # 這段處理每次「狀態切換」時動態更新
        for s in range(len(config.scroll_ys)):
            config.scroll_ys[s] = 0  # 切換頁面時重置捲動位置
        button_obj.text_cache.clear()
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
            for i, save in enumerate(config.save_files):
                btn = button_obj.TextButton(
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

                all_buttons.buttons["choose_file"].append(btn)
            config.max_scroll_y = max(80, len(config.save_files) * 70 - 300)
