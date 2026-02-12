"""
版本：v0.1.0
"""

import math
import os
import pathlib
import platform as plat
import subprocess as sub
import time
from math import cos, radians, sin

import pygame as p

# 初始化 Pygame (必須先初始化才能使用字體)
p.init()

# clock = p.time.Clock()
# 設定全域變數
W, H = 700, 600
T, F = True, False
s = p.display.set_mode((W, H))


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
    """提供各種顏色"""

    WHITE, PINK, BLUE, BLUE2, BROWN = (255, 255, 255), (255, 0, 255), (0, 0, 255), (0, 0, 200), (200, 100, 50)
    GREEN, DARK_GREEN, GRAY, ORANGE2 = (0, 255, 0), (0, 100, 0), (150, 150, 150), (200, 50, 0)
    RED, RED_2, ORANGE, BLACK, YELLOW = (255, 0, 0), (215, 0, 0), (255, 100, 0), (0, 0, 0), (255, 255, 0)
    GOLD, PURPLE, DARK_GRAY, CYAN = (255, 215, 0), (128, 0, 128), (90, 90, 90), (135, 206, 235)
    BLACK2, DARK_RED = (30, 30, 30), (180, 0, 0)


def draw_rect(color, x, y, width=100, height=50, center=False, show=True):
    """單純方塊"""
    if not center:
        button_rect = p.Rect(x, y, width, height)
    else:
        button_rect = p.Rect(W // 2 - width // 2, y, width, height)
    p.draw.rect(s, color, button_rect)
    if show:
        return button_rect


def show_text(text, text_color, x, y, size=24, center=F, screen_center=F, show=True, font_type=""):
    """單純文字"""
    root = pathlib.Path(__file__).parent.resolve()
    if font_type == "":
        font = p.font.Font(str(root / "Ubuntu.ttf"), size)
    elif font_type == "None":
        font = p.font.SysFont(None, size)
    else:
        font = p.font.SysFont(font_type, size)
    t_surf = font.render(text, T, text_color)
    t_rect = t_surf.get_rect()
    if center:
        t_rect.center = (x, y)
    elif screen_center:
        t_rect.center = (W // 2, y)
    else:
        t_rect.topleft = (x, y)
    if show:
        s.blit(t_surf, t_rect)
    return t_rect  # 建議回傳 rect，方便做點擊偵測


def text_button(
    text,
    text_color,
    color,
    x,
    y,
    width=100,
    height=50,
    t_x=None,
    t_y=None,
    t_center=False,
    b_center=False,
    size=28,
    show=True,
    font_type="",
):
    """包含文字以及方塊的物件，會回傳一個方塊，可以偵測碰撞"""
    if not b_center:
        button_rect = p.Rect(x, y, width, height)
    else:
        button_rect = p.Rect(W // 2 - width // 2, y, width, height)

    if show:
        p.draw.rect(s, color, button_rect)
        # 自動計算文字中心點（優化算法）
        text_x = t_x if t_x is not None else button_rect.centerx
        text_y = t_y if t_y is not None else button_rect.centery
        show_text(text, text_color, text_x, text_y - size // 5, center=T if t_x is None else t_center, size=size, font_type=font_type)

    return button_rect


# def invisible_button(color=Colors.BLUE2, x=0, y=0, width=100, height=50, t_x=None, t_y=None, t_center=False, b_center=False, size=32, show=False, text="", text_color=Colors.WHITE, ):
#     if not b_center:
#         button_rect = p.Rect(x, y, width, height)
#     else:
#         button_rect = p.Rect(W // 2 - width // 2, y, width, height)

#     if show:
#         p.draw.rect(s, color, button_rect)
#         # 自動計算文字中心點（優化算法）
#         text_x = t_x if t_x is not None else button_rect.centerx
#         text_y = t_y if t_y is not None else button_rect.centery
#         show_text(text, text_color, text_x, text_y, center=T if t_x is None else t_center, size=size)

#     return button_rect


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
    return max(start, min(num, end))


collision_time = None
start_time = None
elapsed_time = 0
paused_time = 0


def sec_timer(update=False):
    """只在遊玩時(update=True)才持續更新時間，否則保持暫停。"""
    global start_time, elapsed_time, paused_time

    if update:
        # 如果遊戲剛開始，初始化起始時間（扣除暫停過的時間）
        if start_time is None:
            start_time = time.time() - paused_time
        # 計算遊戲時間
        elapsed_time = time.time() - start_time
    else:
        # 暫停時，記錄目前經過時間（不繼續累加）
        if start_time is not None:
            paused_time = time.time() - start_time
        start_time = None
    return int(elapsed_time)


def reset_timer():
    global start_time, elapsed_time, paused_time
    start_time = None
    elapsed_time = 0
    paused_time = 0


def angle(angle):
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
    mins = seconds // 60  # type:ignore
    sec = seconds % 60
    return f"{mins}:" + ("0" if sec < 10 else "") + f"{sec}"  # type:ignore


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

    def __init__(self, text, start_x, start_y, color, size=20, time=60, speed=1.0):
        self.text = text
        # 確保文字至少離邊界 20 像素，且不超出右下角
        self.x = num_range(20, W - 60, start_x)
        self.y = num_range(20, H - 20, start_y)
        self.color = color
        self.timer = time  # 文字顯示多久
        self.max_time = time
        self.speed = speed

        root = pathlib.Path(__file__).parent.resolve()
        self.font = p.font.Font(str(root / "Ubuntu.ttf"), size)

    def update(self):
        self.y -= self.speed  # 文字慢慢往上飄
        self.timer -= 1

    def reset(self):
        self.timer = 0

    def draw(self, surface):
        if self.timer > 0:
            # 渲染文字
            text_surf = self.font.render(self.text, True, self.color)

            # ✨ 加入透明度：這會讓文字看起來像是在空氣中消散，感覺會變慢、變輕
            alpha = int((self.timer / self.max_time) * 255)

            # 建立一個支援透明度的 Surface
            temp_surf = p.Surface(text_surf.get_size(), p.SRCALPHA)
            temp_surf.blit(text_surf, (0, 0))
            temp_surf.set_alpha(alpha)

            surface.blit(temp_surf, (int(self.x), int(self.y)))
