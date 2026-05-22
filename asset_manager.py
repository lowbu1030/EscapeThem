"""把所有的檔案(圖片、音效)載入放在這個檔案"""
from pathlib import Path

import pygame

import config

BASE_DIR = Path(__file__).parent
IMG_PATH = BASE_DIR / "images"

# 左箭頭
try:
    # 載入圖片
    left_img_surface = pygame.image.load(str(IMG_PATH / "Left_Arrow.png")).convert_alpha()
    # 縮放大小（如果原圖太大）
    left_img_size = 50
    left_img_surface = pygame.transform.scale(left_img_surface, (left_img_size, left_img_size))

    # 獲取 Rect 並設定位置
    left_rect = left_img_surface.get_rect()
    upgrade_left_rect = left_rect.copy()
    left_rect.center = (80, 120)
    upgrade_left_rect.center = (70, 110)
    left_img_loaded = True
except Exception as e:
    print(f"無法載入右箭頭: {e}")
    left_img_loaded = False
    # 備案：如果圖掉載入失敗，給它一個虛擬的 Rect 避免 blit 噴錯
    left_rect = pygame.Rect(170, 520, 40, 40)
# 右箭頭
try:
    # 載入圖片
    right_img_surface = pygame.image.load(str(IMG_PATH / "Right_Arrow.png")).convert_alpha()
    # 縮放大小（如果原圖太大）
    right_img_size = 50
    right_img_surface = pygame.transform.scale(right_img_surface, (right_img_size, right_img_size))

    # 獲取 Rect 並設定位置
    right_rect = right_img_surface.get_rect()
    upgrade_right_rect = right_rect.copy()
    right_rect.center = (config.WIDTH - 80, 120)
    upgrade_right_rect.center = (config.WIDTH - 70, 110)
    right_img_loaded = True
except Exception as e:
    print(f"無法載入右箭頭: {e}")
    right_img_loaded = False
    # 備案：如果圖掉載入失敗，給它一個虛擬的 Rect 避免 blit 噴錯
    right_rect = pygame.Rect(530, 520, 40, 40)
# --- 鎖的圖片載入 ---
try:
    lock_img_surface = pygame.image.load(str(IMG_PATH / "Lock.png")).convert_alpha()
    lock_img_surface = pygame.transform.scale(lock_img_surface, (90, 90))
    lock_rect = lock_img_surface.get_rect()
    lock_img_loaded = True
except FileNotFoundError as e:
    lock_img_loaded = False
    print(f"無法載入鎖圖案{e}")
# --- 標題圖片載入 ---
title_rect = pygame.Rect(config.WIDTH // 2 - 200, 120, 400, 180)
try:
    title_img_surface = pygame.image.load(str(IMG_PATH / "Escape_Them.png")).convert_alpha()
    title_img_surface = pygame.transform.scale(title_img_surface, (400, 180))
    title_img_loaded = True

    title_rect = title_img_surface.get_rect()
    title_rect.center = (config.WIDTH // 2, 120)
except FileNotFoundError as e:
    title_img_loaded = False
    title_rect = pygame.Rect(0, 0, 400, 150)
    title_rect.center = (config.WIDTH // 2, 200)
    print(f"無法載入標題圖片{e}")
# 錢幣用圖片
try:
    coin_wood_img_surface = pygame.image.load(str(IMG_PATH / "coin_img.png")).convert_alpha()
    coin_wood_img_surface = pygame.transform.scale(coin_wood_img_surface, (100, 40))
    coin_wood_img_loaded = True

    coin_wood_rect = coin_wood_img_surface.get_rect()
    coin_wood_rect = (config.WIDTH - 110, 15)
except FileNotFoundError as e:
    coin_wood_img_loaded = False
    coin_wood_rect = pygame.Rect(config.WIDTH - 110, 15, 100, 40)
    print(f"無法載入錢幣用木板圖片{e}")
# 滑鼠
try:
    orig_mouse_img_surface = pygame.image.load(str(IMG_PATH / "mouse.png")).convert_alpha()
    orig_mouse_img_surface = pygame.transform.scale(orig_mouse_img_surface, (36, 45))
    mouse_img_surface = orig_mouse_img_surface
    mouse_img_loaded = True

    mouse_rect = orig_mouse_img_surface.get_rect()
    mouse_rect = (0, 0)
except FileNotFoundError as e:
    mouse_img_loaded = False
    mouse_rect = pygame.Rect(0, 0, 0, 0)
    print(f"無法載入錢幣用木板圖片{e}")
    print("滑鼠圖片炸掉啦！")

sounds = {}
shoot_channel = None
heart_channel = None
buy_channel = None

current_heart = None
current_vol = 0.5
target_vol = 0.5


# 🌟 建立一個一鍵初始化音效的防禦函式
def init_game_sounds():
    global sounds, shoot_channel, heart_channel, buy_channel

    try:
        # 核心防禦：確保這裡執行時，pygame.mixer.init() 已經在 main.py 跑過了
        sounds = {
            "buy_error": pygame.mixer.Sound(str(config.SOUND_PATH / "buy_error.wav")),
            "buy_success": pygame.mixer.Sound(str(config.SOUND_PATH / "buy_success.wav")),
            "coin": pygame.mixer.Sound(str(config.SOUND_PATH / "coin.wav")),
            "epic_coin": pygame.mixer.Sound(str(config.SOUND_PATH / "epic_coin.wav")),
            "shoot": pygame.mixer.Sound(str(config.SOUND_PATH / "shoot.wav")),
            "hurt": pygame.mixer.Sound(str(config.SOUND_PATH / "hurt.wav")),
            "slow_heart_beat": pygame.mixer.Sound(str(config.SOUND_PATH / "slow_heart_beat.wav")),
            "fast_heart_beat": pygame.mixer.Sound(str(config.SOUND_PATH / "fast_heart_beat.wav")),
            "steal": pygame.mixer.Sound(str(config.SOUND_PATH / "steal.wav")),
        }

        # 設定基礎音量
        sounds["coin"].set_volume(0.5)
        sounds["shoot"].set_volume(0.2)
        sounds["fast_heart_beat"].set_volume(1.0)
        sounds["slow_heart_beat"].set_volume(1.0)
        sounds["steal"].set_volume(1.0)

        # 🌟 混音聲道安全降落點：在這裡才真正建立聲道物件！
        shoot_channel = pygame.mixer.Channel(1)
        heart_channel = pygame.mixer.Channel(2)
        buy_channel = pygame.mixer.Channel(3)

        print("[DEBUG]: 遊戲音效與聲道系統初始化成功！")
    except Exception as e:
        print(f"[ERROR]: 音效載入或聲道建立失敗，原因: {e}")




def check_data_consistency(data_list):
    return sum((int(n) ^ (i + 1)) << 1 for i, n in enumerate(data_list))


def is_God():
    config.God = False

    if any([config.Invincible, config.FPS_Speed != 1, config.Timer_Speed != 1]):
        print("--- 檢測到作弊變數已更改 ---")
        enter = input("請輸入授權碼以繼續：")

        # 將輸入轉為 ASCII 列表
        enter_list = [ord(ch) for ch in enter]
        eln = check_data_consistency(enter_list)
        if eln == 6370:
            print("密碼正確，上帝模式啟動！")
            config.God = True  # 背景音樂
        else:
            print("密碼錯誤，重置為正常模式。")
            config.Invincible = False
            config.FPS_Speed = 1
            config.Timer_Speed = 1
            config.God = False


def init_BGMs():

    pygame.mixer.music.set_volume(0.5)  # 靜音：0, 正常：0.5
    if config.God:
        pygame.mixer.music.load(str(config.BGM_PATH / "God.mp3"))
    else:
        pygame.mixer.music.load(str(config.BGM_PATH / "Game_bgm 3.mp3"))
