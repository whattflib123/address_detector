import pandas as pd
from datetime import datetime
from hyperliquid import HyperliquidSync
from utils import load_previous_data
from config import ORDERS_FILE, POSITIONS_FILE

def sync_wallet_orders_positions(wallets):
    client = HyperliquidSync()  # API client

    # 讀取歷史資料
    previous_orders = load_previous_data(
        ORDERS_FILE,
        ["wallet_name", "coin", "side", "amount", "price", "orderType", "order_time", "order_id"]
    )
    previous_positions = load_previous_data(
        POSITIONS_FILE,
        ["wallet_name", "coin", "side", "amount", "entry_price", "liquidation_price"]
    )

    all_current_orders = []
    all_current_positions = []

    for wallet_name, wallet_address in wallets.items():
        # ---------------- 取得持倉 ----------------
        try:
            positions_raw = client.fetch_positions(params={"user": wallet_address})
            if positions_raw:
                for p in positions_raw:
                    liquidation_price = 0
                    try:
                        liquidation_price = float(p["info"]["position"].get("liquidationPx", 0))
                    except (TypeError, KeyError, ValueError):
                        liquidation_price = 0

                    all_current_positions.append({
                        "wallet_name": wallet_name,
                        "coin": p["info"]["position"]["coin"],
                        "side": p["side"],
                        "amount": float(p["contracts"]),
                        "entry_price": float(p["entryPrice"]),
                        "liquidation_price": liquidation_price,
                    })
        except Exception as e:
            print(f"{wallet_name} 查詢持倉失敗:", e)

        # ---------------- 取得掛單 ----------------
        try:
            orders_raw = client.fetch_open_orders(params={"user": wallet_address})
            if orders_raw:
                for o in orders_raw:
                    side = "buy" if o["info"]["side"] == "B" else "sell"
                    orderType = o["info"].get("orderType", "unknown")
                    trigger_condition = o["info"].get("triggerCondition", "N/A")
                    if trigger_condition != "N/A" and "Price" in trigger_condition:
                        price = float(trigger_condition.split()[-1])
                    else:
                        price = float(o["info"].get("limitPx", 0))

                    if "timestamp" in o:
                        order_time = datetime.fromtimestamp(int(o["timestamp"]) / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    elif "timestamp" in o.get("info", {}):
                        order_time = datetime.fromtimestamp(int(o["info"]["timestamp"]) / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    elif "datetime" in o:
                        order_time = o["datetime"]
                    else:
                        order_time = None

                    order_id = str(o["info"].get("oid", None))

                    all_current_orders.append({
                        "wallet_name": wallet_name,
                        "coin": o["info"]["coin"],
                        "side": side,
                        "amount": float(o["info"]["sz"]),
                        "price": price,
                        "orderType": orderType,
                        "order_time": order_time,
                        "order_id": order_id,
                    })
        except Exception as e:
            print(f"{wallet_name} 查詢掛單失敗:", e)

    # ---------------- 建立 DataFrame ----------------
    current_orders_df = pd.DataFrame(all_current_orders)
    current_positions_df = pd.DataFrame(all_current_positions)

    # 補齊缺失欄位
    for col in ["wallet_name", "coin", "side", "amount", "price", "orderType", "order_time", "order_id"]:
        if col not in current_orders_df.columns:
            current_orders_df[col] = None
    current_orders_df = current_orders_df[["wallet_name", "coin", "side", "amount", "price", "orderType", "order_time", "order_id"]]

    for col in ["wallet_name", "coin", "side", "amount", "entry_price", "liquidation_price"]:
        if col not in current_positions_df.columns:
            current_positions_df[col] = None
    current_positions_df = current_positions_df[["wallet_name", "coin", "side", "amount", "entry_price", "liquidation_price"]]

    return current_orders_df, current_positions_df, previous_positions, previous_orders
