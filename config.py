import os

# ---------------- 錢包設定 ----------------
wallets = {
    "🔴 內幕哥 (精準打擊)": "0xb317d2bc2d3d2df5fa441b5bae0ab9d8b07283ae",
    "🟢 波段大師 (持倉時間極短)": "0xc2a30212a8ddac9e123944d6e29faddce994e5f2",
    "🔵 100%勝率 (低倍槓桿)": "0x4e8d91cb10b32ca351ac8f1962f33514a96797f4",
}

# ---------------- 檔案設定 ----------------
ORDERS_FILE = "data/orders.csv"
NEW_ORDERS_FILE = "data/orders_new.csv"
POSITIONS_FILE = "data/positions.csv"
NEW_POSITIONS_FILE = "data/positions_new.csv"

# ---------------- Telegram 設定 ----------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your_chat_id")


# ---------------- 批量通知 ----------------
CANCEL_COUNT = 5 # 若一次訂單超過這個數字，就會將訂單通知省略
