import json
from pathlib import Path

# 設定路徑
BASE_DIR = Path(__file__).parent


def cheak_version(file_name):
    with open(file_name, encoding="utf-8") as f:
        data = json.load(f)
        return data.get("save_game_version", 1) < 2


def migrate_save_format(file_name):
    """
    存檔遷移工具 (Universal Save Migrator) \n
    功能：將舊版變數名稱、檔案格式轉換為新版統一格式
    """
    file_path = BASE_DIR / file_name
    if not file_path.exists():
        print(f"❌ 找不到 {file_name}，無法進行更新。")
        return

    try:
        # 1. 讀取目前的存檔
        print(f"📂 正在讀取 {file_name}...")
        with file_path.open("r", encoding="utf-8") as f:
            old_data = json.load(f)

        """因為現在已經是最新版，所以不需要判斷"""
        # 1. 檢查版本：如果已經是版本 3，直接結束
        save_version = old_data.get("save_version", 1)
        if save_version >= 2:
            print(f"✅ {file_name} 已經是最新版本，無需更新。")
            return

        # 4. 處理 Records (自動補齊 1-9)
        old_records = old_data.get("records", {})
        final_records = {}
        for i in range(1, 11):
            level_key = f"level{i}"
            # 如果舊存檔有這一關，就搬過來；沒有就給初始 0 分字典
            final_records[level_key] = old_records.get(level_key, {"easy": 0, "normal": 0, "hard": 0, "super_hard": 0, "crazy": 0})

        level_costs = [0, 0, 500, 1000, 5000, 15000, 35000, 50000, 75000, 100000, 130000]
        old_unlocked = old_data.get("levels_unlocked", 1)
        # 如果玩家以前解鎖到第 9 關，就要退還 2~9 關的所有花費
        if save_version == 1:
            # 版本 1 才要退錢，版本 2 已經不需要了
            total_refund = sum(level_costs[: old_unlocked + 1])

        # 5. 組合成新資料並加入版本號
        new_data = {
            "balance": old_data.get("balance", 0) + total_refund,  # 退還已解鎖關卡的花費
            "upgrades": old_data["upgrades"],
            "records": final_records,
            "player_skins": old_data.get("player_skins", {}),
            "now_player_skin": old_data.get("now_player_skin", [255, 0, 0]),
            "current_skin_name": old_data.get("current_skin_name", "red"),
            "levels_unlocked": {"world1": 1, "world2": 1},  # 重置解鎖關卡為 1，玩家需要重新解鎖
            "save_game_version": 2,  # 重要：標記為版本 2
            "gm_i": 1,
            "has_buy_crazy": old_data.get("has_buy_crazy", False),
        }
        with (BASE_DIR / file_name).open("w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=4, ensure_ascii=False)

        print(f"💰 退款完成：已退還 {total_refund} 元至餘額。")
        print("✅ 存檔已重置並遷移至 Version 2。玩家現在需手動解鎖關卡。")

    except Exception as e:
        print(f"🧨 轉換過程中出錯: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    migrate_save_format()
