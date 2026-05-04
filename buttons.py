import pathlib

import pygame

import config
from tool import Colors

Color = tuple[int, int, int]
WIDTH, HEIGHT = 700, 600


class Button:
    def __init__(
        self,
        name: str,
        rect: pygame.Rect,
        normal_color: Color,
        pressing_color: Color | None = None,
        hover_color: Color | None = None,
        disabled_color: Color | None = None,
        border_radius=0,
        show=True,
    ):
        self.name = name
        self.rect = rect
        self.border_radius = border_radius
        self.active = True
        self.is_toggle = False
        self.is_hover = False
        self.is_pressed = False
        self.is_pressing = False
        self.is_clicked = False
        self.type = "normal"  # 可以做連點按鈕

        self.normal_color = normal_color
        self.hover_color = hover_color or normal_color
        # 如果沒設定按壓色，就先看有沒有懸停色；如果都沒有，才用原本底色
        self.pressing_color = pressing_color or self.hover_color
        self.disabled_color = disabled_color or Colors.GRAY
        self.is_visible = show

    def change_base_color(self, new_color, force=False):
        self.normal_color = new_color

        if force:
            # 如果是強制模式，全部洗掉（適合 record_level_display）
            self.hover_color = new_color
            self.pressing_color = new_color
            self.disabled_color = new_color
        else:
            # 如果是一般模式，保留原本的設計（適合 select 按鈕）
            self.hover_color = self.hover_color or self.normal_color
            self.pressing_color = self.pressing_color or self.hover_color

    def get_color(self):
        if not self.active:
            return self.disabled_color

        if self.is_pressing:
            return self.pressing_color

        if self.is_hover:
            return self.hover_color

        return self.normal_color

    def update(self, events, mouse_pos):
        if not self.is_visible or not self.active:
            self.is_hover = False
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
        pygame.draw.rect(surface, (*color, alpha), surface.get_rect(), border_radius=self.border_radius)
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
        #  4. 其他
        border_radius=0,
        font_type: str = "",
        r_alpha: int = 255,
        t_alpha: int = 255,
        screen_center=True,
        text_center=True,
        show=True,
    ):
        # 1. 初始化父類別按鈕背景
        super().__init__(name, rect, button_color, pressing_color, hover_color, disabled_color, border_radius, show)

        # 2. 文字內容與備份
        self.org_text = text
        self.current_text = text
        self.hover_text = hover_text or text
        self.pressing_text = pressing_text or self.hover_text
        self.disable_text = disable_text or text

        # 3. 文字顏色與備份 (若無設定則沿用原色)
        self.org_text_color = text_color
        self.current_text_color = text_color
        self.hover_text_color = hover_text_color or text_color
        self.pressing_text_color = pressing_text_color or self.hover_text_color
        self.disable_text_color = disable_text_color or text_color

        # 4. 其他屬性
        self.font_size = font_size
        self.font_type = font_type
        self.r_alpha = r_alpha
        self.t_alpha = t_alpha
        self.screen_center = screen_center
        self.text_center = text_center

    def change_base_text(self, new_text: str, force=False):
        self.org_text = new_text
        self.current_text = new_text
        if force:
            self.hover_text = new_text
            self.pressing_text = new_text
            self.disable_text = new_text
        else:
            self.hover_text = self.hover_text or new_text
            self.pressing_text = self.pressing_text or self.hover_text
            self.disable_text = self.disable_text or new_text

    def change_base_text_color(self, new_color: Color, force=False):
        self.org_text_color = new_color
        self.current_text_color = new_color
        if force:
            self.hover_text_color = new_color
            self.pressing_text_color = new_color
            self.disable_text_color = new_color
        else:
            self.hover_text_color = self.hover_text_color or new_color
            self.pressing_text_color = self.pressing_text_color or self.hover_text_color
            self.disable_text_color = self.disable_text_color or new_color

    def update(self, events, mouse_pos):
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

    def draw(self, screen):
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

    def update(self, events, mouse_pos):
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


all_buttons = {
    "menu": [
        ImageButton(
            name="left",
            image=config.left_img_surface,
            pos=config.left_rect.center,
        ),
        ImageButton(
            name="right",
            image=config.right_img_surface,
            pos=config.right_rect.center,
        ),
        ImageButton(name="logo", image=config.title_img_surface, pos=config.title_rect.center),
        TextButton(
            name="start",
            text="START GAME",
            rect=pygame.Rect(0, 220, 300, 70),
            button_color=Colors.DARK_GREEN,
            text_color=Colors.WHITE,
            font_size=32,
            hover_color=Colors.CYAN,
            hover_text="READY?",
            hover_text_color=Colors.YELLOW,
            pressing_color=Colors.BLUE,
            pressing_text="GO!",
        ),
        TextButton(
            name="setting_p1",
            text="SETTINGS",
            rect=pygame.Rect(WIDTH // 2 - 150, 310, 140, 70),
            button_color=Colors.BLUE2,
            text_color=Colors.WHITE,
            font_size=28,
            hover_color=Colors.GREEN,
            hover_text_color=Colors.BLACK,
            screen_center=False,
        ),
        TextButton(
            name="upgrades",
            text="UPGRADES",
            rect=pygame.Rect(WIDTH // 2 + 10, 310, 140, 70),  # 統一用 pygame.Rect
            button_color=Colors.YELLOW,
            text_color=Colors.BLACK,
            font_size=28,
            hover_color=Colors.ORANGE,
            screen_center=False,
        ),
        TextButton(
            name="help",
            text="HELP",
            rect=pygame.Rect(0, 400, 300, 70),
            button_color=Colors.GRAY,
            text_color=Colors.WHITE,
            font_size=32,
        ),
        TextButton(
            name="quit",
            text="QUIT",
            rect=pygame.Rect(0, 490, 300, 70),  # 修正座標避免重疊
            button_color=Colors.RED,
            text_color=Colors.WHITE,
            font_size=32,
            hover_color=Colors.DARK_RED,
            hover_text="NNNOOOOOO!!!",
        ),
    ],
    "setting_p1": [
        # 範例
        # TextButton(
        #     name="???",
        #     text="???",
        #     rect=pygame.Rect(0, 0, 0, 0),
        #     button_color=Colors.RED,
        #     text_color=Colors.WHITE,
        #     font_size=32,
        #     hover_color=Colors.DARK_RED,
        #     hover_text="???",
        # ),
        TextButton(
            name="back",
            text="BACK TO MENU",
            rect=pygame.Rect(0, 520, 200, 60),
            button_color=Colors.ORANGE,
            text_color=Colors.WHITE,
            font_size=24,
            hover_color=Colors.BROWN,
        ),
        ImageButton(
            name="right",
            image=config.right_img_surface,
            pos=config.right_rect.center,
        ),
        ImageButton(name="crazy_lock", image=config.lock_img_surface, pos=(90, 430)),
        TextButton(
            name="record_level_display",
            text="",  # 初始文字留空，交給 sync 更新
            rect=pygame.Rect(0, 150, 180, 50),
            button_color=config.level_button_color,  # 或者你原本設定的 level_button_color
            disabled_color=Colors.YELLOW,
            text_color=Colors.BLACK,
            screen_center=True,
            font_size=30,
        ),
    ],
}


difficulty_settings = [
    ("easy", Colors.GREEN),
    ("normal", Colors.YELLOW),
    ("hard", Colors.ORANGE),
    ("super_hard", Colors.RED),
    ("crazy", Colors.PURPLE),
]


for i, (mode, color) in enumerate(difficulty_settings):
    # 計算 Y 座標：210, 270, 330...
    y_pos = 210 + (i * 60)

    # 處理 Crazy 難度的特殊文字
    display_text = "select"


    btn1 = TextButton(
        name=f"{mode}_info",
        text="info",
        rect=pygame.Rect(540, y_pos, 60, 50),
        button_color=Colors.BLUE3,
        text_color=Colors.WHITE,
        font_size=24,
        hover_text_color=Colors.GRAY,
        screen_center=False,
    )
    btn2 = TextButton(
        name=f"{mode}_select",
        text=display_text,
        rect=pygame.Rect(70, y_pos, 130, 50),
        button_color=color if not config.from_pause else Colors.GRAY,
        text_color=Colors.BLACK,
        font_size=28,
        screen_center=False,
    )
    btn3 = TextButton(
        name=f"show_{mode}",
        text="",
        rect=pygame.Rect(70, y_pos, 450, 50),
        button_color=color if not config.from_pause else Colors.GRAY,
        text_color=Colors.BLACK,
        font_size=0,
        screen_center=False,
        show=(config.game_mode == mode)
    )
    all_buttons["setting_p1"].append(btn3)
    all_buttons["setting_p1"].append(btn1)
    all_buttons["setting_p1"].append(btn2)
