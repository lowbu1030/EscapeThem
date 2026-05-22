import config


def check_data_consistency(data_list):
    return sum((int(n) ^ (i + 1)) << 1 for i, n in enumerate(data_list))


def check_god_mode(enter_code):
    """
    🌟 改成傳入參數（enter_code），不要在函式裡面寫 input()！
    這樣未來不論你是從終端機拿到密碼，還是從 Pygame 的輸入框拿到密碼，都能通用！
    """
    enter_list = [ord(ch) for ch in enter_code]
    eln = check_data_consistency(enter_list)

    if eln == 6370:
        print("密碼正確，上帝模式啟動！")
        config.Invincible = True
        return True
    else:
        print("密碼錯誤，重置為正常模式。")
        config.Invincible = False
        config.FPS_Speed = 1
        config.Timer_Speed = 1
        return False
