
import json
from pathlib import Path

# 設定路徑
BASE_DIR = Path(__file__).parent
SAVE_FILE = BASE_DIR / "save_game.json"

def migrate_save_format():
    """
    存檔遷移工具 (Universal Save Migrator) \n
    功能：將舊版變數名稱 (sp_i, speed...) 轉換為新版統一格式 (upgrade_p1...)
    """
    if not SAVE_FILE.exists():
        print("❌ 找不到 save_game.json，無法進行更新。")
        return

    try:
        # 1. 讀取目前的存檔
        print(f"📂 正在讀取 {SAVE_FILE.name}...")
        with SAVE_FILE.open("r", encoding="utf-8") as f:
            old_data = json.load(f)

        # 2. 定義新舊鍵值對照表
        # 格式： "新鍵值": ["舊鍵值版本1", "舊鍵值版本2", "舊鍵值版本3"]
        # 程式會依序尋找，找到哪個用哪個
        mapping_rules = {
            "upgrade_p1": ["speed", "sp_i", "p1_i"],       # 速度
            "upgrade_p2": ["coin_spawn", "ph_i", "p2_i"],  # 金幣生成 (注意: ph_i 可能是你舊版變數)
            "upgrade_p3": ["multiplier", "pb_i", "p3_i"],  # 分數倍率
            "upgrade_p4": ["size", "si_i", "p4_i"],        # 玩家大小
            "upgrade_p5": ["spawn", "es_i", "co_i", "p5_i"], # 怪物生成 (這裡容錯 co_i 和 es_i)
            "upgrade_p6": ["max_hp", "mh_i", "p6_i"],      # 血量上限
            "upgrade_p7": ["regen", "phc_i", "p7_i"],      # 回血
            "upgrade_p8": ["invincible", "pi_i", "p8_i"]   # 無敵時間
        }

        # 3. 提取舊資料 (或是原本就存在的 upgrades 字典)
        # 有些版本資料直接散落在根目錄，有些在 "upgrades" 字典裡
        source_data = old_data
        if "upgrades" in old_data and isinstance(old_data["upgrades"], dict):
            # 如果已經有 upgrades 字典，優先從裡面找
            # 但也要保留根目錄的查找權限（防止混合格式）
            source_upgrades = old_data["upgrades"]
        else:
            source_upgrades = old_data

        # 4. 建立新的升級字典
        new_upgrades = {}
        
        for new_key, old_keys in mapping_rules.items():
            found_value = 0 # 預設值
            
            # 嘗試從所有可能的舊名稱中找值
            for key in old_keys:
                # 先找 upgrades 字典內
                if isinstance(source_upgrades, dict) and key in source_upgrades:
                    found_value = source_upgrades[key]
                    break
                # 再找根目錄
                if key in source_data:
                    found_value = source_data[key]
                    break
            
            new_upgrades[new_key] = found_value
            print(f"   🔄 轉換: {new_key} <- 值: {found_value}")

        # 5. 重新打包完整資料
        new_data = {
            # 餘額：相容 points_sum 或 balance
            "balance": old_data.get("balance", old_data.get("points_sum", 0)),
            
            # 升級：使用剛剛轉換好的字典
            "upgrades": new_upgrades,
            
            # 紀錄：保留原本的紀錄，如果沒有則初始化
            "records": old_data.get("records", {
                "easy": old_data.get("longest_survived_time", {}).get("easy", 0),
                "normal": old_data.get("longest_survived_time", {}).get("normal", 0),
                "hard": old_data.get("longest_survived_time", {}).get("hard", 0),
                "super_hard": old_data.get("longest_survived_time", {}).get("super_hard", 0),
                "crazy": old_data.get("longest_survived_time", {}).get("crazy", 0)
            }),
            
            # 皮膚：保留原本的皮膚資料
            "player_skins": old_data.get("player_skins", {}),

            # 保留目前使用的皮膚名稱
            "current_skin_name": old_data.get("current_skin_name", "red")
        }

        # 6. 寫回檔案
        # 為了安全，我們直接覆蓋 save_game.json，因為這是一次性遷移
        # 如果你擔心，可以先手動備份一個
        with SAVE_FILE.open("w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ 成功！ save_game.json 已更新為最新格式！")
        print("現在請執行 code_use.py，存檔應該可以正常載入了。")

    except Exception as e:
        print(f"🧨 轉換過程中出錯: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_save_format()