import json

import config


def load_data(file_path=None):
    # 注意：這裡不再需要 global，因為我們是透過 config.xxx 修改
    try:
        target_path = file_path if file_path else config.SAVE_PATH
        config.current_active_path = target_path

        if not target_path.exists():
            print("❌ 沒有找到存檔檔案")
            return  # 沒檔案就跳出，避免後面讀取報錯

        with target_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # 1. 讀取金錢與基本數值
        config.total_points = data.get("balance", 0)
        config.target_points = config.total_points
        config.longest_survived_time = data.get("records", config.longest_survived_time)
        config.gm_i = data.get("gm_i", 1)
        config.has_buy_crazy = data.get("has_buy_crazy", False)
        config.select_world = data.get("select_world", 1)
        config.all_worlds_unlocked = data.get("levels_unlocked", {"world1": 1, "world2": 1})
        config.worlds_unlocked = data.get("worlds_unlocked", 1)
        print(f"DEBUG: 載入的字典內容是 {config.all_worlds_unlocked}")

        # 2. 讀取升級數據 (修正變數路徑)
        saved_ups = data.get("upgrades", {})
        # 這裡根據 config 裡的 UPGRADE_SURVIVAL 長度自動循環
        for i in range(1, len({**config.UPGRADE_SURVIVAL, **config.UPGRADE_COMBAT}) + 1):
            key = f"upgrade_p{i}"
            config.current_levels[key] = saved_ups.get(key, 0)

        # 3. 讀取皮膚資料
        load_player_skin_data = data.get("player_skins", {})
        for name, skin in config.player_skins.items():
            if name in load_player_skin_data:
                saved_skin = load_player_skin_data[name]
                # 注意：這裡直接修改 skin 字典內的內容，會同步到 config.player_skins
                skin["has_owned"] = saved_skin.get("has_owned", saved_skin.get("has_bought", False))
                skin["level"] = saved_skin.get("level", 1)
                skin["exp"] = saved_skin.get("exp", 0)
            elif name == "red":
                skin["has_owned"] = True

        # 4. 讀取當前使用的皮膚
        config.now_player_skin = data.get("now_player_skin", config.now_player_skin)
        config.current_player_color_name = data.get("current_skin_name", "red")

        print("✔️ 載入成功！")

    except Exception as e:
        print(f"❌ 載入失敗: {e}")
        # 出錯時的保險機制
        for i in range(1, 19):
            config.current_levels[f"upgrade_p{i}"] = 0

    # 5. 更新運算後的屬性
    config.update_skill()
    config.apply_skin_effects()  # 記得執行這個，讓皮膚加成生效
    config.can_shoot = bool(config.now_skills.get("p15", 0))


def save_data():
    config.update_world_data(config.select_world)
    try:
        # 準備要寫入的資料，全部指向 config
        data = {
            "balance": int(config.total_points),
            "upgrades": config.current_levels,
            "records": config.longest_survived_time,
            "player_skins": config.player_skins,
            "now_player_skin": config.now_player_skin,
            "current_skin_name": config.current_player_color_name,
            "gm_i": config.gm_i,
            "has_buy_crazy": config.has_buy_crazy,
            "levels_unlocked": config.all_worlds_unlocked,  # 存入完整的字典
            "save_game_version": 3,  # 標記存檔版本，方便未來升級
            "select_world": config.select_world,
            "worlds_unlocked": config.worlds_unlocked,
        }

        # 使用 config 裡面的路徑
        with config.current_active_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # print("💾 存檔成功！")
    except Exception as e:
        print(f"❌ 存檔失敗: {e}")
