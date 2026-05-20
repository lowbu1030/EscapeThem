import pygame

import config
from all_objs import Button, ImageButton, Line, TextButton
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
        Button(
            name="none_1",
            rect=pygame.Rect(0, config.HEIGHT - 80, config.WIDTH, 80),
            normal_color=Colors.BLUE3,
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
        ][::-1],
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
    "upgrade_hub": [
        TextButton(
            name="title",
            text="Upgrade Center",
            rect=pygame.Rect(0, 0, 500, 100),
            button_color=Colors.BLUE3,
            text_color=Colors.WHITE,
            font_size=50,
            screen_center=True,
            border_radius=0,
        ),
        TextButton(
            name="now_mode",
            text=f"now_mode: {config.shop_page}",
            rect=pygame.Rect(0, 90, 500, 40),
            button_color=Colors.BLUE3,
            text_color=Colors.WHITE,
            font_size=35,
            screen_center=True,
            border_radius=0,
        ),
        Button(
            name="mask1",
            rect=pygame.Rect(0, config.HEIGHT - 120, config.WIDTH, 120),
            normal_color=Colors.BLUE3,
        ),
        TextButton(
            name="back_upg_hub",
            text="BACK TO MENU",
            rect=pygame.Rect(0, 510, 300, 60),
            button_color=Colors.ORANGE,
            text_color=Colors.WHITE,
            font_size=24,
            hover_color=Colors.BROWN,
        ),
        ImageButton(
            name="left",
            image=config.left_img_surface,
            pos=config.upgrade_left_rect.center,
            visible=config.l_img_show and config.left_img_loaded,
        ),
        ImageButton(
            name="right",
            image=config.right_img_surface,
            pos=config.upgrade_right_rect.center,
            visible=config.r_img_show and config.right_img_loaded,
        ),
    ],
    "upgrade_p": [
        TextButton(
            name="upgrade",
            text="",  # 因應不同升級項目，文字會由 sync 更新
            rect=pygame.Rect(0, 300, 350, 60),
            button_color=Colors.YELLOW,
            text_color=Colors.BLACK,
            font_size=24,
            screen_center=True,
            border_width=2,
            normal_border_color=Colors.BLACK,
            hover_color=Colors.GREEN,  # 由錢判斷顏色(在ui_handler裡)，所以 hover_color 就先給一個預設值，反正會被覆蓋掉
            pressing_color=Colors.PARIS_GREEN,  # 同上，先給預設值
        ),
        TextButton(
            name="back_upg",
            text="BACK TO UPGRADE HUB",
            rect=pygame.Rect(0, 510, 300, 60),
            button_color=Colors.ORANGE,
            text_color=Colors.WHITE,
            font_size=24,
            hover_color=Colors.BROWN,
        ),
    ],
    "level_select": [
        # 讓它乾乾淨淨地誕生，座標算好，名字叫 "next_world"
        TextButton(
            name="next_world",
            text=["Next World", "(cost: $--)"],  # 預設文字
            button_color=Colors.CHARTREUSE,
            text_color=Colors.WHITE,
            rect=pygame.Rect(120, 60 + len(config.current_world_costs) * 80, 200, 60),
            font_size=22,
            screen_center=False,
        ),
        Button(
            name="mask1",
            rect=pygame.Rect(0, config.HEIGHT - 100, config.WIDTH, 100),
            normal_color=Colors.GRAY,
            color_wave=[config.world_bgc[config.current_world_key][0], config.world_bgc[config.current_world_key][1], 1],
        ),
        TextButton(
            name="back",
            text="BACK TO MENU",
            rect=pygame.Rect(0, 520, 300, 60),
            button_color=Colors.ORANGE,
            text_color=Colors.WHITE,
            font_size=24,
            hover_color=Colors.BROWN,
        ),
        TextButton(
            name="title",
            text="Level Select",
            rect=pygame.Rect(0, 0, config.WIDTH, 100),
            button_color=Colors.BLUE3,
            text_color=Colors.WHITE,
            font_size=50,
            color_wave=[config.world_bgc[config.current_world_key][0], config.world_bgc[config.current_world_key][1], 1],
        ),
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
        Line(name="line1", start_pos=(350, 100), end_pos=(350, 500), width=2, normal_color=Colors.WHITE),
    ],
    "playing": [
        Button(
            name="hp_bar_bg",
            rect=pygame.Rect(config.WIDTH - 110, 70, 100, 23),
            normal_color=(*Colors.DARK_RED, config.alphas[0]),
        ),
        Button(
            name="hp_bar",
            rect=pygame.Rect(config.WIDTH - 110, 70, 100, 23),  # 和血條重疊，當作血條的背景
            normal_color=(*Colors.RED, config.alphas[0]),
        ),
    ],
    "pause": [
        TextButton(
            name="resume",
            text="Resume",
            button_color=Colors.BROWN,
            text_color=Colors.WHITE,
            hover_color=Colors.ORANGE,
            rect=pygame.Rect(0, 170, 180, 60),
            font_size=28,
        ),
        TextButton(
            name="settings",
            text="Settings",
            button_color=Colors.GREEN,
            text_color=Colors.WHITE,
            hover_color=Colors.YELLOW,
            hover_text_color=Colors.BLACK,
            rect=pygame.Rect(0, 250, 180, 60),
            font_size=28,
        ),
        TextButton(
            name="restart",
            text="Restart",
            button_color=Colors.YELLOW,
            text_color=Colors.BLACK,
            hover_color=Colors.ORANGE,
            rect=pygame.Rect(0, 330, 180, 60),
            font_size=28,
        ),
        TextButton(
            name="menu",
            text="Back to Menu",
            button_color=Colors.PURPLE,
            text_color=Colors.BLACK,
            hover_color=Colors.BLUE3,
            rect=pygame.Rect(0, 410, 180, 60),
            font_size=28,
        ),
        TextButton(
            name="leave",
            text="Quit",
            button_color=Colors.RED,
            text_color=Colors.WHITE,
            hover_color=Colors.DARK_RED,
            rect=pygame.Rect(0, 490, 180, 60),
            font_size=28,
        ),
    ],
    "game_over": [
        TextButton(
            name="back",
            text="Back to Menu",
            button_color=Colors.ORANGE,
            text_color=Colors.WHITE,
            hover_color=Colors.BROWN,
            rect=pygame.Rect(0, 490, 300, 80),
            font_size=28,
        )
    ],
    "afk_kick": [
        TextButton(
            name="kick",
            text="TERMINATE PROCESS",
            button_color=Colors.RED,
            text_color=Colors.WHITE,
            hover_color=Colors.DARK_RED,
            rect=pygame.Rect(0, 400, 350, 60),
            font_size=28,
            font_type="None",
        )
    ],
    "game_state_error": [
        TextButton(
            name="back",
            text="Back To Menu",
            button_color=Colors.RED,
            text_color=Colors.WHITE,
            hover_color=Colors.DARK_RED,
            rect=pygame.Rect(0, 400, 350, 60),
            font_size=28,
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
