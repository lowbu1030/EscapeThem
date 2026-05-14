import pathlib

import pygame

from tool import Colors

Color = tuple[int, int, int]
WIDTH, HEIGHT = 700, 600


# buttons.py


class Button:
    def __init__(
        self,
        name: str,
        rect: pygame.Rect,
        normal_color: Color,
        pressing_color: Color | None = None,
        hover_color: Color | None = None,
        disabled_color: Color | None = None,
        border_radius=5,
        border_width=None,
        normal_border_color: Color = None,
        pressing_border_color: Color | None = None,
        hover_border_color: Color | None = None,
        disabled_border_color: Color | None = None,
        show=True,
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
        self.disabled_color = disabled_color if disabled_color is not None else Colors.GRAY

        # 按鈕邊框顏色保底
        self.normal_border_color = normal_border_color if normal_border_color is not None else normal_color
        self.hover_border_color = hover_border_color if hover_border_color is not None else self.normal_border_color
        self.pressing_border_color = pressing_border_color if pressing_border_color is not None else self.hover_border_color
        self.disabled_border_color = disabled_border_color if disabled_border_color is not None else Colors.GRAY

        self.is_visible = show

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
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        color = self.get_color()
        border_color = self.get_border_color()
        pygame.draw.rect(surface, (*color, alpha), surface.get_rect(), border_radius=self.border_radius)
        if self.border_width:
            pygame.draw.rect(surface, (*border_color, alpha), surface.get_rect(), border_radius=self.border_radius, width=self.border_width)
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
        self.save_path = None

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
            self.current_text_color = self.disable_text_color
        elif self.is_pressing:
            self.current_text = self.pressing_text or self.org_text
            self.current_text_color = self.pressing_text_color
        elif self.is_hover:
            self.current_text = self.hover_text or self.org_text
            self.current_text_color = self.hover_text_color
        else:
            self.current_text = self.org_text
            self.current_text_color = self.org_text_color

    def draw(self, screen: pygame.Surface):
        if not self.is_visible:
            return

        if self.screen_center:
            self.rect.centerx = screen.get_rect().w // 2

        t_x = self.rect.centerx if self.text_center else self.rect.x + 10
        t_y = self.rect.centery if self.text_center else self.rect.y + 10

        # 先畫背景，再畫文字
        super().draw(screen, self.r_alpha)
        show_text(
            screen,
            self.current_text,
            self.current_text_color,
            t_x,
            t_y,
            self.font_size,
            font_type=self.font_type,
            alpha=self.t_alpha,
            center=True,
        )


class ImageButton:
    def __init__(self, name: str, image: pygame.Surface, pos: list[int], visible: bool = True):
        self.name = name
        self.surface = image
        self.rect = self.surface.get_rect()
        self.rect.center = pos
        # 點擊事件屬性
        self.is_clicked = False
        self.visible = visible

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
        if self.surface and self.visible:
            screen.blit(self.surface, self.rect)
        elif self.visible:
            pygame.draw.rect(screen, Colors.RED, self.rect)


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
    for i, surf in enumerate(surfaces):
        # 複製一份矩形來做位置偏移計算
        draw_rect = relative_rects[i].copy()

        # 根據外部傳入的 x, y 進行偏移
        if center:
            draw_rect.center = (x, y + relative_rects[i].top)
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
