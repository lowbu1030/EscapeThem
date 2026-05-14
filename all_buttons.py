import pygame

import config
from button_obj import ImageButton, TextButton  # Button, 之後用到再加
from tool import Colors

buttons = {
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
            text="LEVEL SELECT",
            rect=pygame.Rect(0, 220, 300, 70),
            button_color=Colors.DARK_GREEN,
            text_color=Colors.WHITE,
            font_size=32,
            hover_color=Colors.CYAN,
            hover_text_color=Colors.YELLOW,
        ),
        TextButton(
            name="setting_p1",
            text="SETTINGS",
            rect=pygame.Rect(config.WIDTH // 2 - 150, 310, 140, 70),
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
            rect=pygame.Rect(config.WIDTH // 2 + 10, 310, 140, 70),  # 統一用 pygame.Rect
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
    "more_survived_time": [
        TextButton(
            name="title",
            text="All Levels Survived Time",
            rect=pygame.Rect(0, 0, config.WIDTH, 70),
            button_color=Colors.BLUE3,
            text_color=Colors.WHITE,
            font_size=34,
            screen_center=True,
        ),
        TextButton(
            name="none_1",
            text="",
            rect=pygame.Rect(0, config.HEIGHT - 80, config.WIDTH, 80),
            button_color=Colors.BLUE3,
            text_color=Colors.WHITE,
            font_size=0,
        ),
        TextButton(
            name="back",
            text="BACK TO SETTINGS",
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
    ],
    "setting_p2": [
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
        TextButton(
            name="draw_skin",
            text="Draw Skin ($500)",
            rect=pygame.Rect(170, 100, 190, 40),
            button_color=Colors.GOLD,
            text_color=Colors.WHITE,
            font_size=22,
            hover_text="Draw Skin ($500)" if config.total_points >= 500 else "Not Enough Money!",
            hover_color=Colors.GREEN if config.total_points >= 500 else Colors.RED,
            pressing_color=Colors.PARIS_GREEN if config.total_points >= 500 else Colors.DARK_RED,
            pressing_text="Draw Skin ($500)" if config.total_points >= 500 else "Not Enough Money!",
            border_radius=5,
            border_width=2,
            normal_border_color=Colors.BLACK,
            screen_center=False,
        ),
        TextButton(
            name="back",
            text="BACK TO MENU",
            rect=pygame.Rect(0, 520, 200, 60),
            button_color=Colors.ORANGE,
            text_color=Colors.WHITE,
            font_size=24,
            hover_color=Colors.BROWN,
        ),
        *[
            TextButton(
                name=f"skin_{name}",
                text=name,
                rect=pygame.Rect(100, 180, 150, 50),  # 座標先隨便給，迴圈會改
                button_color=Colors.GRAY,
                text_color=config.skin_text_color[name],
                font_size=22,
                border_radius=10,
                border_width=2,
                hover_border_color=Colors.WHITE,
                screen_center=False,
            )
            for name in config.player_skins.keys()
        ],
    ],
    "setting_p3": [
        TextButton(
            name="open_other_save",
            text="Open Other Save",
            rect=pygame.Rect(0, 200, 250, 100),
            button_color=Colors.YELLOW,
            text_color=Colors.BLACK,
            font_size=30,
            hover_color=Colors.GREEN,
            pressing_color=Colors.PARIS_GREEN,
            hover_text_color=Colors.WHITE,
            normal_border_color=Colors.BLACK,
            hover_border_color=Colors.BLUE,
            border_radius=10,
            border_width=2,
        ),
        TextButton(
            name="open_new_game",
            text="Start New Game",
            rect=pygame.Rect(0, 350, 250, 70),
            button_color=Colors.LIGHT_RED,
            text_color=Colors.WHITE,
            font_size=30,
            hover_color=Colors.PINK,
        ),
        TextButton(
            name="back",
            text="BACK TO MENU",  # 初始文字，會由 sync 根據 from_pause 自動更新
            rect=pygame.Rect(0, 490, 200, 60),
            button_color=Colors.ORANGE,
            text_color=Colors.WHITE,
            font_size=24,
            hover_color=Colors.BROWN,
        ),
        ImageButton(
            name="left",
            image=config.left_img_surface,
            pos=config.left_rect.center,
        ),
    ],
    "choose_file": [
        TextButton(
            name="back",
            text="BACK TO SETTINGS",
            rect=pygame.Rect(0, 490, 200, 60),
            button_color=Colors.ORANGE,
            text_color=Colors.WHITE,
            font_size=24,
            hover_color=Colors.BROWN,
        )
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
        show=(config.game_mode == mode),
    )
    buttons["setting_p1"].append(btn3)
    buttons["setting_p1"].append(btn1)
    buttons["setting_p1"].append(btn2)
