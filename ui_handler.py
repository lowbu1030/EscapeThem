import pygame

import buttons
import config
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

    def _sync_ui_state(self, obj: buttons.Button | buttons.TextButton | buttons.ImageButton):
        state = config.game_state

        if state == "setting_p1":

            # 處理 Crazy 難度的特殊文字
            if obj.name == "crazy_select":
                obj.current_text = "select" if config.has_buy_crazy else config.crazy_btn_text
                obj.active = config.has_buy_crazy
                if config.has_buy_crazy:
                    # 已購買：固定顯示 select 並啟用
                    obj.change_base_text("select")
                    obj.active = True
                else:
                    # 未購買：根據懸停狀態顯示價格或鎖定文字，並禁用
                    new_text = "$10000" if obj.is_hover else config.crazy_btn_text
                    obj.change_base_text(new_text)
                    obj.active = False

            elif obj.name == "crazy_lock":
                crazy_btn = next((b for b in buttons.all_buttons[state] if b.name == "crazy_select"), None)
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
                select_btn = next((b for b in buttons.all_buttons["setting_p1"] if b.name == f"{mode}_select"), None)

                if select_btn:
                    # 只要其中一個被懸停，兩個都進入 hover 狀態
                    is_any_hover = obj.is_hover or select_btn.is_hover
                    obj.is_hover = is_any_hover
                    select_btn.is_hover = is_any_hover

                # 顯示與顏色更新
                obj.is_visible = (mode == config.game_mode)
                # 同步顏色，確保在 from_pause 等狀態下顏色一致
                target_color = self.DIFFICULTY_MAP.get(mode, tool.Colors.GRAY)
                obj.change_base_color(target_color, force=True)

    def handle_current_state(self, events, mouse_pos):
        # 1. 抓取物件清單
        current_objects = buttons.all_buttons.get(config.game_state, [])

        for obj in current_objects:
            if hasattr(obj, 'update'):
                obj.update(events, mouse_pos)

            self._sync_ui_state(obj)

            # 3. 繪製
            obj.draw(self.screen)

            # 4. 處理點擊
            if getattr(obj, 'is_clicked', False):
                self._handle_actions(obj)

    def _handle_actions(self, obj: buttons.Button | buttons.TextButton | buttons.ImageButton):
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
            if config.game_state == "setting_p1":
                for i, mode in enumerate(self.MODES):
                    if obj.name == f"{mode}_info":
                        config.game_state = "more_survived_time"
                        # 根據 index (i) 計算目標高度
                        config.target_y = i * (config.one_mode_height + 30)
                        return
                    elif obj.name == f"{mode}_select" or obj.name == f"show_{mode}":
                        config.game_mode = mode
                        config.level_button_color = self.DIFFICULTY_MAP[mode]
                        # print(f"[DEBUG]: from 'ui_handler.py:  {config.level_button_color}")
                        return

    def _handle_keyboard(self, events):
        # 處理單次按下的 C
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    config.running = False

        # 處理長按或單次按下的方向鍵
        keys = pygame.key.get_pressed()
        if config.game_state == "menu":
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                config.game_state = "setting_p1"
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                config.game_state = "upgrade_hub"
        if config.game_state.startswith("setting"):
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.setting_page = tool.num_range(1, 4, self.setting_page - 1)
                config.game_state = f"setting_p{self.setting_page}"
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.setting_page = tool.num_range(1, 4, self.setting_page + 1)
                config.game_state = f"setting_p{self.setting_page}"
