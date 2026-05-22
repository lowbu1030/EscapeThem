import json
import math
import pathlib
import random

import pygame

import asset_manager
import config
import tool

Color = tuple[int, int, int]
AlphaColor = tuple[int, int, int, int]
WIDTH, HEIGHT = 700, 600


class Line:
    def __init__(self, start_pos, end_pos, width, normal_color, hover_color=None, pressing_color=None, disabled_color=None, name="line"):
        self.name = name
        self.start_pos = list(start_pos)  # 轉成 list 方便之後動態修改座標
        self.end_pos = list(end_pos)
        self.width = width

        # 🌟 核心細節：記錄線條的原始 Y 軸起點與終點，供捲動公式使用
        self.base_start_y = start_pos[1]
        self.base_end_y = end_pos[1]

        # 顏色設定
        self.normal_color = normal_color
        self.hover_color = hover_color if hover_color is not None else normal_color
        self.pressing_color = pressing_color if pressing_color is not None else self.hover_color
        self.disabled_color = disabled_color if disabled_color is not None else tool.Colors.GRAY

        # 為了跟 UIManager 對接，必須預留的狀態基因
        self.active = True
        self.is_hover = False
        self.is_pressing = False
        self.is_clicked = False

    def get_color(self):
        if not self.active:
            return self.disabled_color
        if self.is_pressing:
            return self.pressing_color
        if self.is_hover:
            return self.hover_color
        return self.normal_color

    def draw(self, screen: pygame.Surface):
        if self.width <= 0:
            return
        pygame.draw.line(screen, self.get_color(), self.start_pos, self.end_pos, self.width)


class Button:
    def __init__(
        self,
        name: str,
        rect: pygame.Rect,
        normal_color: Color | AlphaColor,
        pressing_color: Color | AlphaColor | None = None,
        hover_color: Color | AlphaColor | None = None,
        disabled_color: Color | AlphaColor | None = None,
        border_radius=5,
        border_width=None,
        normal_border_color: Color | AlphaColor = None,
        pressing_border_color: Color | AlphaColor | None = None,
        hover_border_color: Color | AlphaColor | None = None,
        disabled_border_color: Color | AlphaColor | None = None,
        show=True,
        color_wave: None | list[Color] = None,
    ):
        self.name = name
        self.rect = rect
        self.base_y = rect.y
        self.border_radius = border_radius
        self.border_width = border_width
        self.active = True
        self.is_toggle = False
        self.is_hover = False
        self.is_pressed = False
        self.is_pressing = False
        self.is_clicked = False
        self.type = "normal"

        # 按鈕顏色保底
        self.normal_color = normal_color
        self.hover_color = hover_color if hover_color is not None else normal_color
        self.pressing_color = pressing_color if pressing_color is not None else self.hover_color
        self.disabled_color = disabled_color if disabled_color is not None else tool.Colors.GRAY

        # 按鈕邊框顏色保底
        self.normal_border_color = normal_border_color if normal_border_color is not None else normal_color
        self.hover_border_color = hover_border_color if hover_border_color is not None else self.normal_border_color
        self.pressing_border_color = pressing_border_color if pressing_border_color is not None else self.hover_border_color
        self.disabled_border_color = disabled_border_color if disabled_border_color is not None else tool.Colors.GRAY

        self.is_visible = show
        self.color_wave = color_wave

    def change_base_color(self, new_color, force=False):
        self.normal_color = new_color
        if force:
            self.hover_color = new_color
            self.pressing_color = new_color
            self.disabled_color = new_color
        else:
            # 修改處
            self.hover_color = self.hover_color if self.hover_color is not None else self.normal_color
            self.pressing_color = self.pressing_color if self.pressing_color is not None else self.hover_color

    def change_base_border_color(self, new_color, force=False):
        self.normal_border_color = new_color
        if force:
            self.hover_border_color = new_color
            self.pressing_border_color = new_color
            self.disabled_border_color = new_color
        else:
            # 修改處
            self.hover_border_color = self.hover_border_color if self.hover_border_color is not None else self.normal_border_color
            self.pressing_border_color = self.pressing_border_color if self.pressing_border_color is not None else self.hover_border_color

    def get_color(self):
        if not self.active:
            return self.disabled_color

        if self.is_pressing:
            return self.pressing_color

        if self.is_hover:
            return self.hover_color

        return self.normal_color

    def get_border_color(self):
        if not self.active:
            return self.disabled_border_color

        if self.is_pressing:
            return self.pressing_border_color

        if self.is_hover:
            return self.hover_border_color

        return self.normal_border_color

    def handle_condition(self, condition: bool, value1, value2):
        return value1 if condition else value2

    def update(self, events, mouse_pos):
        if not self.is_visible or not self.active:
            self.is_pressed = False
            self.is_clicked = False
            return

        # 每幀重置（重要）
        self.is_clicked = False

        # hover
        self.is_hover = self.rect.collidepoint(mouse_pos)

        for event in events:
            # 按下
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.is_hover:
                    self.is_pressed = True
                    self.is_pressing = True
            # 放開
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.is_pressing = False
                if self.is_pressed and self.is_hover:
                    self.is_clicked = True

                self.is_pressed = False
        if self.type == "hold":
            if self.is_pressed and self.is_hover:
                self.is_clicked = True
        elif self.type == "toggle":
            if self.is_clicked:
                self.is_toggle = not self.is_toggle

    def draw(self, screen: pygame.Surface, alpha=255):
        if not self.is_visible:
            return

        # 建立支援透明度的臨時畫布
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        color = self.get_color()
        border_color = self.get_border_color()

        # --- 1. 處理底色 ---
        # 💡 檢查細節：如果顏色本質上就是完全透明 (例如長度為4且A為0)，就徹底跳過不畫底色！
        if len(color) == 4 and color[3] == 0:
            pass
        else:
            # 如果是正常顏色，我們把「顏色本身的透明度」與「外層傳入的動態 alpha」做相乘結合
            # 這樣如果按鈕本來有點半透明，套用閃爍特效時就會一起完美變淡！
            base_alpha = color[3] if len(color) == 4 else 255
            final_alpha = int(base_alpha * (alpha / 255))

            pygame.draw.rect(surface, (*color[:3], final_alpha), surface.get_rect(), border_radius=self.border_radius)

        # --- 2. 處理邊框 ---
        if self.border_width:
            if border_color is not None:
                # 💡 同理，邊框的透明度也要結合外層傳入的動態 alpha
                border_base_alpha = border_color[3] if len(border_color) == 4 else 255
                final_border_alpha = int(border_base_alpha * (alpha / 255))

            pygame.draw.rect(
                surface,
                (*border_color[:3], final_border_alpha),
                surface.get_rect(),
                border_radius=self.border_radius,
                width=self.border_width,  # 💡 傳入寬度使其變成「空心外框」
            )

        screen.blit(surface, self.rect.topleft)


class TextButton(Button):
    def __init__(
        self,
        name: str,
        text: str | list,
        rect: pygame.Rect,
        button_color: Color,
        text_color: Color,
        font_size: int,
        # --- 以下為選填參數，有預設值 ---
        #  1. 按鈕顏色
        hover_color: Color | None = None,
        pressing_color: Color | None = None,
        disabled_color: Color | None = None,
        #  2. 文字
        hover_text: str | None = None,
        pressing_text: str | None = None,
        disable_text: str | None = None,
        #  3. 文字顏色
        hover_text_color: Color | None = None,
        pressing_text_color: Color | None = None,
        disable_text_color: Color | None = None,
        #  4. 邊框、邊框顏色
        border_radius=5,
        border_width=0,
        normal_border_color: Color | None = None,
        pressing_border_color: Color | None = None,
        hover_border_color: Color | None = None,
        disabled_border_color: Color | None = None,
        #  5. 其他
        font_type: str = "",
        r_alpha: int = 255,
        t_alpha: int = 255,
        screen_center=True,
        text_center=True,
        show=True,
        color_wave: None | list[Color] = None,
    ):
        # 1. 初始化父類別按鈕背景
        super().__init__(
            name=name,
            rect=rect,
            normal_color=button_color,
            pressing_color=pressing_color,
            hover_color=hover_color,
            disabled_color=disabled_color,
            border_width=border_width,
            border_radius=border_radius,
            show=show,
            normal_border_color=normal_border_color,
            pressing_border_color=pressing_border_color,
            hover_border_color=hover_border_color,
            disabled_border_color=disabled_border_color,
            color_wave=color_wave,
        )

        # 2. 文字內容與備份
        self.org_text = text
        self.current_text = text
        self.hover_text = hover_text if hover_text is not None else text
        self.pressing_text = pressing_text if pressing_text is not None else self.hover_text
        self.disable_text = disable_text if disable_text is not None else text

        # 3. 文字顏色與備份 (若無設定則沿用原色)
        self.org_text_color = text_color
        self.current_text_color = text_color
        self.hover_text_color = hover_text_color if hover_text_color is not None else text_color
        self.pressing_text_color = pressing_text_color if pressing_text_color is not None else self.hover_text_color
        self.disable_text_color = disable_text_color if disable_text_color is not None else text_color

        # 4. 其他屬性
        self.font_size = font_size
        self.font_type = font_type
        self.r_alpha = r_alpha
        self.t_alpha = t_alpha
        self.screen_center = screen_center
        self.text_center = text_center
        self.draw_lock = False

    def get_text_color(self):
        if not self.active:
            return self.disable_text_color
        if self.is_pressing:
            return self.pressing_text_color
        if self.is_hover:
            return self.hover_text_color
        return self.org_text_color

    def change_base_text(self, new_text: str, force=False):
        self.org_text = new_text
        self.current_text = new_text
        if force:
            self.hover_text = new_text
            self.pressing_text = new_text
            self.disable_text = new_text
        else:
            # 修改處
            self.hover_text = self.hover_text if self.hover_text is not None else new_text
            self.pressing_text = self.pressing_text if self.pressing_text is not None else self.hover_text
            self.disable_text = self.disable_text if self.disable_text is not None else new_text

    def change_base_text_color(self, new_color: Color, force=False):
        self.org_text_color = new_color
        self.current_text_color = new_color
        if force:
            self.hover_text_color = new_color
            self.pressing_text_color = new_color
            self.disable_text_color = new_color
        else:
            # 修改處
            self.hover_text_color = self.hover_text_color if self.hover_text_color is not None else new_color
            self.pressing_text_color = self.pressing_text_color if self.pressing_text_color is not None else self.hover_text_color
            self.disable_text_color = self.disable_text_color if self.disable_text_color is not None else new_color

    def update(self, events, mouse_pos: tuple[int | float]):
        super().update(events, mouse_pos)

        # 狀態優先級：Disabled > Pressed > Hover > Normal
        if not self.active:
            self.current_text = self.disable_text or self.org_text
        elif self.is_pressing:
            self.current_text = self.pressing_text or self.org_text
        elif self.is_hover:
            self.current_text = self.hover_text or self.org_text
        else:
            self.current_text = self.org_text

    # 💡 提示：讓 TextButton.draw 也能接收外部傳入的動態 alpha 特效參數
    def draw(self, screen: pygame.Surface, alpha=255):
        if self.rect.width <= 0 or self.rect.height <= 0:
            print(f"💥 抓到你了！出事的按鈕名字叫: {self.name}, 它的 rect 是: {self.rect}")
        if not self.is_visible:
            return

        if self.screen_center:
            self.rect.centerx = screen.get_rect().w // 2

        t_x = self.rect.centerx if self.text_center else self.rect.x + 10
        t_y = self.rect.centery if self.text_center else self.rect.y + 10

        # 1. 💡 呼叫父類別繪製背景 (底色與邊框)：把動態 alpha 傳進去
        super().draw(screen, alpha)

        # 2. 💡 結合文字的基礎透明度與動態變化的 alpha 特效
        # 這樣當特效讓按鈕變淡時，文字也會跟著一起變淡！
        final_text_alpha = int(self.t_alpha * (alpha / 255))

        # 3. 繪製文字
        show_text(
            screen,
            self.current_text,
            self.get_text_color(),
            t_x,
            t_y,
            self.font_size,
            font_type=self.font_type,
            alpha=final_text_alpha,  # 💡 關鍵細節：改用計算後的動態文字透明度
            center=True,
        )
        if self.draw_lock:
            asset_manager.lock_rect.center = self.rect.center
            # 直接在按鈕的座標附近 blit 鎖頭圖案，它就會完美跟著按鈕一起移動、滾動！
            screen.blit(asset_manager.lock_img_surface, asset_manager.lock_rect)


class ImageButton:
    def __init__(self, name: str, image: pygame.Surface, pos: list[int], visible: bool = True):
        self.name = name
        self.surface = image
        self.rect = self.surface.get_rect()
        self.rect.center = pos
        # 點擊事件屬性
        self.is_clicked = False
        self.is_visible = visible

    def update(self, events, mouse_pos: tuple[int | float]):
        self.is_clicked = False  # 每幀重置，確保點擊只觸發一次

        # 檢查滑鼠是否懸停在圖片上
        hover = self.rect.collidepoint(mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hover:
                    self.is_clicked = True  # 觸發點擊狀態

    def draw(self, screen: pygame.Surface):
        # 如果有圖片就畫圖片，沒有的話可以考慮畫個紅框作為保險
        if self.surface and self.is_visible:
            screen.blit(self.surface, self.rect)
        elif self.is_visible:
            pygame.draw.rect(screen, tool.Colors.RED, self.rect)


text_cache = {}

root = pathlib.Path(__file__).parent.resolve(strict=False)


def show_text(screen, text, text_color, x, y, size=24, center=False, screen_center=False, show=True, font_type="", alpha=255, line_gap=5):
    # 1. 產生唯一的快取 Key (包含 alpha 也要放進去，因為 alpha 不同圖片就不同)
    # 如果 text 是清單，轉成字串來當 key
    text_str = "".join(text) if isinstance(text, list) else text
    key = (text_str, text_color, size, font_type, alpha)

    # 2. 檢查快取：如果這組文字已經畫過了，直接拿出來 blit
    if key in text_cache:
        surfaces, relative_rects = text_cache[key]
    else:
        # --- 以下內容只有在「第一次畫這段字」時才會執行 ---
        surfaces = []
        relative_rects = []

        # 字體初始化 (這也很耗時，只有沒快取才做)
        if font_type == "":
            font = pygame.font.Font(str(root / "Ubuntu.ttf"), size)
        elif font_type == "None":
            font = pygame.font.SysFont(None, size)
        else:
            font = pygame.font.SysFont(font_type, size)

        text_list = [text] if isinstance(text, str) else text

        temp_y = 0
        for t in text_list:
            # 渲染並處理透明度
            t_surf = font.render(t, True, text_color)
            final_surf = pygame.Surface(t_surf.get_size(), pygame.SRCALPHA).convert_alpha()  # 記得加 convert_alpha
            final_surf.blit(t_surf, (0, 0))
            if alpha < 255:
                final_surf.set_alpha(alpha)

            # 儲存 Surface
            surfaces.append(final_surf)

            # 儲存相對位置 (以 y=0 為起點，方便後續根據傳入的 y 移動)
            t_rect = final_surf.get_rect()
            t_rect.top = temp_y
            relative_rects.append(t_rect)

            temp_y = t_rect.bottom + line_gap

        # 存入快取：把這一組 Surface 和它們的相對位置存起來
        text_cache[key] = (surfaces, relative_rects)

    # 3. 繪製邏輯 (這一部分每一幀都會跑，但現在只剩 blit，非常快)
    first_rect = None
    total_text_height = relative_rects[-1].bottom if relative_rects else 0
    for i, surf in enumerate(surfaces):
        # 複製一份矩形來做位置偏移計算
        draw_rect = relative_rects[i].copy()

        # 根據外部傳入的 x, y 進行偏移
        if center:
            line_center_offset_y = relative_rects[i].top + (draw_rect.height / 2) - (total_text_height / 2)
            draw_rect.center = (x, y + line_center_offset_y)
        else:
            draw_rect.top = y + relative_rects[i].top
            if screen_center:
                draw_rect.centerx = screen.get_rect().w // 2
            else:
                draw_rect.x = x

        if i == 0:
            first_rect = draw_rect
        if show:
            screen.blit(surf, draw_rect)

    return first_rect


total_spread = 90


class Enemy:
    def __init__(
        self,
        show_time,
        speed,
        slow_speed,
        color,
        angle_range=(10, 80),
        size=10,
        damage=10,
        types="normal",
        change_time=4000,
        is_split_enemy=False,
        split_enemies=2,
    ):
        self.show_time = show_time
        self.color = color
        self.types = [types] if isinstance(types, str) else types
        self.damage = damage
        self.is_dead = False
        self.is_split_enemy = is_split_enemy  # 用於標記是否為分裂後的小怪
        self.should_split = False  # 用於標記是否應該分裂（只對 break 類型有效）
        self.split_enemys = split_enemies
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
        self.change_time = change_time
        self.time_lasting = 1000  # 要持續的時間
        self.random_time_limit = random.randint(800, 2300)  # 給 random_angle 用的

    def update(self, current_time_ms, current_time_sec, player_rect, mouse_pos, now_treasure, screen):
        # 1. 模式切換邏輯
        spawn_start_time = int(self.show_time * config.spawn_time_debuff)
        attack_start_time = spawn_start_time + config.buffer_duration

        if self.is_split_enemy:
            self.mode = "attack"  # 小怪不需要等待，直接開戰
            self.show = True
        else:
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
            self._handle_movement(current_time_ms, target_speed, config.mode_speed_buff, player_rect, now_treasure)

            # --- 邊界反彈 ---
            self._check_bounds()

            # --- 繪製與碰撞 ---
            e_rect.topleft = (self.x - config.offset_x, self.y - config.offset_y)
            if not self.is_dead:
                pygame.draw.rect(screen, self.color, e_rect)

            # 碰撞檢測 (受傷邏輯建議放在這裡，或回傳 e_rect 讓主程式判斷)
        return e_rect

    def _handle_movement(self, current_time_ms, target_speed, mode_speed_buff, player_rect, now_treasure):
        global collide_player
        self_vec = pygame.math.Vector2(self.x + self.width / 2, self.y + self.height / 2)
        e_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # 平滑調整當前速度
        self.current_speed += (target_speed - self.current_speed) * 0.1
        final_speed = self.current_speed * config.mode_speed_buff

        if "split" in self.types:
            hit_wall = self._check_bounds()

            if hit_wall:
                if self.is_split_enemy:
                    self.is_dead = True  # 已經是小怪了，再撞就死掉
                    return  # 撞到了就不用再算移動了
                else:
                    self.should_split = True  # 讓主迴圈知道要生出小怪
                    if self.x <= 0 or self.x >= WIDTH - self.width:
                        self.x_dir *= -1
                    if self.y <= 0 or self.y >= HEIGHT - self.height:
                        self.y_dir *= -1

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
                pygame.draw.line(config.screen, self.color, self_vec, coin_vec, 1)
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
        return self.x <= 0 or self.x >= WIDTH - self.width or self.y <= 0 or self.y >= HEIGHT - self.height


# 砲台的子彈生成函式，放在外面讓子彈生成時也能呼叫
def make_bullet(x, y, angle, speed, bom_range, color=tool.Colors.GRAY, base_damage=10, type="normal"):
    return Bullet(x, y, color, angle, speed, bom_range, base_damage, type)


class Cannon:
    def __init__(
        self,
        show_time,
        color,
        x,
        y,
        angle,
        fire_rate,
        bullet_speed,
        bullet_type,
        bom_range,
        speed_buff,
        spawn_time_debuff,
        buffer_duration,
        move_speed=0,
        damage=10,
        cannon_type="normal",
        width=30,
        height=30,
    ):
        self.show_time = show_time
        self.color = color
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.angle = angle
        self.damage = damage
        self.cannon_type = cannon_type
        self.mode = "waiting"
        self.last_fire_time = 0
        self.fire_rate = fire_rate
        self.move_speed = move_speed
        self.bullet_speed = bullet_speed
        self.bullet_type = bullet_type
        self.bom_range = bom_range
        self.speed_buff, self.spawn_time_debuff, self.buffer_duration = speed_buff, spawn_time_debuff, buffer_duration

    def update(self, current_time_sec, current_time_ms, player_rect):
        spawn_start_time = int(self.show_time * self.spawn_time_debuff)
        attack_start_time = spawn_start_time + self.buffer_duration

        if current_time_sec >= attack_start_time:
            self.mode = "attack"
        elif current_time_sec >= spawn_start_time:
            self.mode = "spawning"
        else:
            self.mode = "waiting"
            return

        if self.mode != "attack":
            return

        self._update_behavior()
        self.rect.topleft = (self.x, self.y)
        new_bullet = self._try_fire(current_time_ms)
        return new_bullet

    def _try_fire(self, current_time_ms):
        if current_time_ms - self.last_fire_time > self.fire_rate / self.speed_buff:
            bullet = make_bullet(
                self.rect.centerx,
                self.rect.centery,
                self.angle,
                self.bullet_speed,
                self.bom_range,
                self.color,  # 🌟 補上顏色
                self.damage,  # 🌟 補上傷害值
                type=self.bullet_type,  # 🌟 補上子彈類型
            )
            self.last_fire_time = current_time_ms
            return bullet
        else:
            return None

    def _update_behavior(self):
        if self.cannon_type == "track":
            pass
        elif self.cannon_type == "X_move":
            pass
        elif self.cannon_type == "Y_move":
            pass
        else:
            pass
        # elif self.cannon_type == "":
        #     pass

    def draw(self, screen, offset_x, offset_y, current_time_ms):
        draw_rect = self.rect.copy()
        draw_rect.x -= offset_x
        draw_rect.y -= offset_y
        if self.mode == "spawning":
            if current_time_ms % 500 < 250:
                pygame.draw.rect(screen, self.color, draw_rect)
        elif self.mode == "attack":
            pygame.draw.rect(screen, self.color, draw_rect)


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
        out_of_bounds = self.x < 0 or self.x > WIDTH - 25 or self.y < 0 or self.y > HEIGHT - 25

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
            self.x += self.dx * self.speed * config.mode_speed_buff
            self.y += self.dy * self.speed * config.mode_speed_buff
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
        self.speed = config.now_skills["p17"]  # 子彈速度
        self.angle = angle  # 弧度 (Radians)
        self.radius = config.now_skills["p18"]  # 子彈大小
        self.active = True

    def update(self):
        # 根據角度計算 X 和 Y 的位移
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        # 如果超出螢幕就失效
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.active = False

        return pygame.draw.circle(config.screen, tool.Colors.YELLOW, (int(self.x), int(self.y)), self.radius)

    def draw(self, screen):
        pygame.draw.circle(screen, tool.Colors.YELLOW, (int(self.x), int(self.y)), self.radius)


class Obsticle:
    def __init__(self, x, y, width, height, color=tool.Colors.GRAY, type="normal"):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.type = type

    def draw(self, screen, offset_x, offset_y):
        draw_rect = self.rect.move(offset_x, offset_y)
        if self.type == "lava":
            pygame.draw.rect(screen, tool.Colors.RED, draw_rect)
        elif self.type != "invisible":
            pygame.draw.rect(screen, self.color, draw_rect)

    def _handle_type(self):
        pass


# 製造敵人、砲台、障礙物的函式，從關卡資料來
def _make_enemy_list(level_data):

    enemy_list = []
    for e in level_data:
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
            split_enemies=e.get("split_enemies", 2),
        )

        enemy_list.append(new_enemy)

    return enemy_list


def _make_cannon_list(level_data):

    def make_cannon(
        x,
        y,
        angle,
        show_time,
        fire_rate=2000,
        bullet_speed=5,
        bom_range=100,
        color=tool.Colors.GRAY,
        move_speed=0,
        type="normal",
        bullet_type="normal",
        damage=10,
    ):
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

    cannon_list = []
    for c in level_data:
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


def _make_obstacle_list(level_data):

    obstacle_list = []
    for o in level_data:
        obstacle_data = Obsticle(
            x=o["x"],
            y=o["y"],
            width=o["width"],
            height=o["height"],
            type=o.get("type", "normal"),
            color=tool.Colors.get_color(o["color"], tool.Colors.GRAY),  # 沒抓到就給灰色
        )

        obstacle_list.append(obstacle_data)
    return obstacle_list


def get_level_data(level, world):
    current_path = config.get_current_world_path(world)
    json_path = current_path / f"level{level}.json"
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
        level_mutiply = data.get("level_multiplier", 1)
        level_name = data.get("level_name")
    enemy_list = _make_enemy_list(data["enemies"])
    cannon_list = _make_cannon_list(data["cannons"])
    obstacle_list = _make_obstacle_list(data.get("obstacles", []))  # 障礙物只有第二個世界有，如果沒有就給空列表
    return enemy_list, cannon_list, obstacle_list, level_mutiply, level_name
