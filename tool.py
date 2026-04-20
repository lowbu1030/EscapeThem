"""
版本：v0.1.0
"""

import math
import os
import pathlib
import platform as plat
import subprocess as sub
from math import cos, radians, sin

import pygame as p

import config

# 初始化 Pygame (必須先初始化才能使用字體)
p.init()
p.mixer.init()

# clock = p.time.Clock()
# 設定全域變數
W, H = 700, 600
T, F = True, False
s = p.display.set_mode((W, H))


# class RangeError(Exception):
#     __module__ = "builtins"


def set_screen(screen: p.Surface):
    global W, H, s
    W, H = screen.get_size()
    s = screen


class CR:  # ColoredRect
    def __init__(self, rect, color, show=True, can_collide=True):
        self.rect = rect  # pygame.Rect
        self.color = color  # (R, G, B)
        self.show = show
        self.can_collide = can_collide

    def draw(self, surface):
        import pygame

        if self.show:
            pygame.draw.rect(surface, self.color, self.rect)


class Colors:
    """提供各種顏色 (依色相與色調排序)"""

    # 1. 基礎與深色系 (最適合當遊戲背景)
    # 這組顏色飽和度較低或亮度較暗，不會干擾玩家看清子彈或敵人。

    BLACK = (0, 0, 0)
    BLACK2 = (30, 30, 30)  # 推薦：World 1 背景
    BLACK_3 = (60, 60, 60)
    DARK_GRAY = (90, 90, 90)
    BLUE3 = (50, 0, 100)  # 推薦：神祕關卡背景
    TYRIAN_PURPLE = (102, 2, 60)  # 推薦：Boss 關背景

    # 2. 暖色調 (紅、橙、黃、金)
    # 這組適合當「警示」、「熔岩世界」或「解鎖按鈕」。

    RED = (255, 0, 0)
    RED_2 = (200, 0, 0)
    DARK_RED = (160, 0, 0)
    LIGHT_RED = (255, 80, 80)
    ORANGE = (255, 100, 0)
    ORANGE2 = (200, 50, 0)
    BROWN = (200, 100, 50)  # 推薦：荒漠世界
    GOLD = (255, 215, 0)
    YELLOW = (255, 255, 0)

    # 3. 綠色調 (森林、草地、毒液)
    DARK_GREEN = (0, 100, 0)  # 推薦：叢林背景
    OLIVE = (127, 127, 0)
    EMERALD = (80, 180, 130)
    PARIS_GREEN = (80, 200, 120)
    CHARTREUSE = (127, 255, 0)
    GREEN = (0, 255, 0)

    # 4. 冷色調 (青、藍、紫、粉)
    # 這組適合「水下世界」、「科技感」或「稀有皮膚」。
    BLUE2 = (0, 0, 170)
    BLUE = (0, 0, 255)
    CYAN = (135, 206, 235)  # 推薦：冰雪/水下世界背景
    VIOLET = (143, 0, 255)
    PURPLE = (128, 0, 128)
    FUCHSIA = (255, 50, 180)
    PINK = (255, 0, 255)
    CLARET = (191, 0, 64)

    # 5. 高亮度與特殊色
    # 適合文字、UI 邊框或發光特效。
    COSMIC_LATTE = (255, 248, 231)
    WHITE = (255, 255, 255)
    GRAY = (150, 150, 150)

    # 實驗中顏色
    TEST_COLOR = (127, 255, 0)

    @staticmethod
    def get_color(color_name: str, default=WHITE):
        # 將輸入轉為大寫，並嘗試從類別屬性中抓取
        if color_name.upper() == "DARK ORANGE":
            color_name = "ORANGE 2"
        if color_name.upper() == "LIGHT BLUE":
            color_name = "CYAN"
        return getattr(Colors, color_name.upper(), default)

    @staticmethod
    def two_color_gradient(color1, color2, ratio):
        """ratio 是 color1 的比例，回傳兩個顏色的漸層色"""
        r = int(color1[0] * ratio + color2[0] * (1 - ratio))
        g = int(color1[1] * ratio + color2[1] * (1 - ratio))
        b = int(color1[2] * ratio + color2[2] * (1 - ratio))
        return (r, g, b)

    @staticmethod
    def two_color_wave(color1, color2, speed, time_func=p.time.get_ticks):
        """根據時間在兩個顏色之間波動，\n time_func 是要用的時間函式，預設是 pygame 的 get_ticks()"""

        ratio = (sin(time_func() / 1000.0 * speed) + 1) / 2  # 產生 0 到 1 的波動
        return Colors.two_color_gradient(color1, color2, ratio)

    @staticmethod
    def two_color_change(color1, color2, condition):
        """condition 為 True 時回傳 color1, 為 False 時回傳 color2"""
        return color1 if condition else color2


def draw_rect(color, x, y, width=100, height=50, center=False, show=True):
    """單純方塊"""
    if not center:
        button_rect = p.Rect(x, y, width, height)
    else:
        button_rect = p.Rect(W // 2 - width // 2, y, width, height)
    p.draw.rect(s, color, button_rect)
    if show:
        return button_rect


text_cache = {}

root = pathlib.Path(__file__).parent.resolve()


def show_text(text, text_color, x, y, size=24, center=False, screen_center=False, show=True, font_type="", alpha=255, line_gap=5):
    # 1. 產生唯一的快取 Key (包含 alpha 也要放進去，因為 alpha 不同圖片就不同)
    # 如果 text 是清單，轉成字串來當 key
    text_str = "".join(text) if isinstance(text, list) else text
    key = f"{text_str}_{text_color}_{size}_{font_type}_{alpha}"

    # 2. 檢查快取：如果這組文字已經畫過了，直接拿出來 blit
    if key in text_cache:
        surfaces, relative_rects = text_cache[key]
    else:
        # --- 以下內容只有在「第一次畫這段字」時才會執行 ---
        surfaces = []
        relative_rects = []

        # 字體初始化 (這也很耗時，只有沒快取才做)
        if font_type == "":
            font = p.font.Font(str(root / "Ubuntu.ttf"), size)
        elif font_type == "None":
            font = p.font.SysFont(None, size)
        else:
            font = p.font.SysFont(font_type, size)

        text_list = [text] if isinstance(text, str) else text

        temp_y = 0
        for t in text_list:
            # 渲染並處理透明度
            t_surf = font.render(t, True, text_color)
            final_surf = p.Surface(t_surf.get_size(), p.SRCALPHA).convert_alpha()  # 記得加 convert_alpha
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
                draw_rect.centerx = W // 2
            else:
                draw_rect.x = x

        if i == 0:
            first_rect = draw_rect
        if show:
            s.blit(surf, draw_rect)

    return first_rect


def text_button(
    text: str,
    text_color: tuple[int, ...],
    color: tuple,
    x: int | float,
    y: int | float,
    width=100,
    height=50,
    t_x=None,
    t_y=None,
    t_center=F,
    b_center=F,
    size=28,
    show=T,
    font_type="",
    alpha=255,
    border_radius=0,
    width_line=0,
):
    """包含文字以及方塊的物件，會回傳一個方塊，可以偵測碰撞"""
    button_surf = p.Surface((width, height), p.SRCALPHA)
    # 2. 決定按鈕在主畫面上的位置 (Rect)
    if not b_center:
        button_rect = p.Rect(x, y, width, height)
    else:
        button_rect = p.Rect(W // 2 - width // 2, y, width, height)

    if show:
        draw_color = (*color, alpha) if len(color) == 3 else color
        p.draw.rect(button_surf, draw_color, (0, 0, width, height), border_radius=border_radius, width=width_line)

        s.blit(button_surf, (button_rect.x, button_rect.y))

        text_x = t_x if t_x is not None else button_rect.centerx
        text_y = t_y if t_y is not None else button_rect.centery

        show_text(text, text_color, text_x, text_y - size // 10, center=T if t_x is None else t_center, size=size, font_type=font_type, alpha=alpha)

    return button_rect


def screen_vague(vague):
    """要放在此函式上的物件才會被模糊"""
    snapshot = s.copy()

    small = p.transform.smoothscale(snapshot, (W // vague, H // vague))
    blurred = p.transform.smoothscale(small, (W, H))
    s.blit(blurred, (0, 0))

    overlay = p.Surface((W, H))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    s.blit(overlay, (0, 0))


def os_open_file(pt):
    if plat.system() == "Windows":
        os.startfile(pt)
    elif plat.system() == "Darwin":
        sub.call(["open", pt])
    else:
        sub.call(["xdg-open", pt])


def num_range(start, end, num):
    res = num
    if end is not None:
        res = min(res, end)
    if start is not None:  # 改成 if，確保下限也會被檢查
        res = max(res, start)
    return res


def in_range(start, end, num):
    # if start > end:
    #     raise RangeError("'start' can't less then 'end'")
    return start <= num <= end


collision_time = None
start_time = None
elapsed_time = 0
paused_time = 0


# 初始化
elapsed_time_ms = 0.0


def sec_timer(update=False, dt=0):
    """
    dt: 每一幀經過的真實時間 (秒)，通常由 clock.tick() 取得
    """
    global elapsed_time_ms

    if update:
        # 核心改動：真實時間差 * 你的作弊速度 = 虛擬的時間增量
        # 這樣 Timer_Speed = 2 時，時間就會跑得比現實快一倍
        elapsed_time_ms += (dt * 1000) * config.Timer_Speed

    return int(elapsed_time_ms / 1000), int(elapsed_time_ms)


def reset_timer():
    global start_time, elapsed_time_ms, paused_time
    start_time = None
    elapsed_time_ms = 0.0
    paused_time = 0
    text_cache.clear()


def get_direction(angle):
    """
    angle 是角度 \n
    輸入angle會回傳一組dx, dy \n
    要用兩個變數來接
    """
    a = radians(angle)
    dx = cos(a)
    dy = sin(a)
    return dx, dy


def show_time_hrs(seconds):
    """
    輸入：秒數 \n
    輸出："小時：分鐘：秒數"
    """
    hrs = seconds // 3600
    mins = seconds // 60
    sec = seconds % 60
    return f"{hrs}:" + ("0" if mins % 60 < 10 else "") + f"{mins % 60}:" + ("0" if sec < 10 else "") + f"{sec}"


def show_time_min(seconds: str | float):
    """
    輸入：秒數 \n
    輸出："分鐘：秒數"
    """
    mins = seconds // 60  # type: ignore
    sec = seconds % 60
    return f"{int(mins)}:" + ("0" if sec < 10 else "") + f"{int(sec)}"  # type: ignore


def num_to_KMBT(num):
    if num >= 1000000000000:
        text = f"{math.floor(num / 10000000000) / 100}T"
    elif num >= 1000000000:
        text = f"{math.floor(num / 10000000) / 100}B"
    elif num >= 1000000:
        text = f"{math.floor(num / 10000) / 100}M"
    elif num >= 1000:
        text = f"{math.floor(num / 10) / 100}K"
    else:
        text = f"{int(num)}"
    return text


class FloatingText:
    """顯示往上漂浮的文字"""

    def __init__(self, text, start_x, start_y, color, size=20, time=60, speed=1.0, center=F):
        self.text = text
        # 確保文字至少離邊界 20 像素，且不超出右下角
        self.x = num_range(20, W - 60, start_x)
        self.y = num_range(20, H - 20, start_y)
        self.color = color
        self.timer = time  # 文字顯示多久
        self.max_time = time
        self.speed = speed
        self.center = center

        root = pathlib.Path(__file__).parent.resolve()
        self.font = p.font.Font(str(root / "Ubuntu.ttf"), size)

    def update(self):
        self.y -= self.speed  # 文字慢慢往上飄
        self.timer -= 1

    def reset(self):
        self.timer = 0

    def draw(self, surface):
        if self.timer > 0:
            text_surf = self.font.render(self.text, True, self.color)

            # ✨ 建立支援透明度的暫存畫布
            temp_surf = p.Surface(text_surf.get_size(), p.SRCALPHA)
            temp_surf.blit(text_surf, (0, 0))

            # 設定透明度 (隨時間淡出)
            alpha = int((self.timer / self.max_time) * 255)
            temp_surf.set_alpha(alpha)

            # 使用 Rect 處理位置
            t_rect = temp_surf.get_rect()
            if self.center:
                t_rect.center = (int(self.x), int(self.y))
            else:
                t_rect.topleft = (int(self.x), int(self.y))

            # 邊界保護 (防止超出螢幕左側或右側)
            t_rect.left = max(10, t_rect.left)
            t_rect.right = min(W - 10, t_rect.right)

            surface.blit(temp_surf, t_rect)
