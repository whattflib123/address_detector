from utils import load_previous_data
from utils import send_telegram_message
from config import CANCEL_COUNT
from utils import fmt_k, get_kline_data

def check_new_orders(prev_orders_file, current_orders_df, wallets):
    # 讀取之前的訂單資料
    prev_orders = load_previous_data(
        prev_orders_file, 
        ["wallet_name", "coin", "side", "amount", "price", "orderType", "order_time", "order_id"]
    )
    prev_orders['order_id'] = prev_orders['order_id'].astype(str)
    current_orders_df['order_id'] = current_orders_df['order_id'].astype(str)

    # 使用 merge 判斷新增訂單
    new_orders = current_orders_df.merge(
        prev_orders[['order_id']],
        on='order_id',
        how='left',
        indicator=True
    )
    new_orders = new_orders[new_orders['_merge'] == 'left_only']

    if new_orders.empty:
        return  # 沒有新掛單就結束

    # 以 (錢包名稱, 幣種, 方向) 分組
    grouped = new_orders.groupby(["wallet_name", "coin", "side"], as_index=False)

    for (wallet_name, coin, side), group in grouped:
        order_count = len(group)

        # 若同組訂單超過 10 筆 → 彙整發送
        if order_count > CANCEL_COUNT:
            min_price = group["price"].min()
            max_price = group["price"].max()
            # 總倉位價值 = Σ(數量 × 價格)
            total_value = (group["amount"] * group["price"]).sum()

            display_side = "做多📈" if side.lower() == "buy" else "做空📉"

            batch_msg = (
                f"📊 **巨鯨批量掛單** 📊\n"
                f"錢包名稱: {wallet_name}\n"
                f"地址: {wallets.get(wallet_name, '未知地址')}\n"
                f"幣種: {coin}\n"
                f"方向: {display_side}\n"
                f"---------------\n"
                f"訂單數量: {order_count} 筆\n"
                f"價格範圍: {min_price:.2f} ~ {max_price:.2f}\n"
                f"倉位總價值: {fmt_k(total_value)} USDC"
            )
            send_telegram_message(batch_msg)
            continue  # 不再逐筆通知這組

        # 否則逐筆發送單筆通知
        for _, o in group.iterrows():
            display_order_type = (
                "市價止損" if o['orderType'] == "Stop Market" else
                "限價單" if o['orderType'] == "Limit" else
                "市價止盈" if o['orderType'] == "Take Profit Market" else
                "限價止盈" if o['orderType'] == "Take Profit Limit" else
                "限價止損" if o['orderType'] == "Stop Limit" else
                o['orderType']
            )
            display_side = "做多📈" if o['side'].lower() == "buy" else "做空📉"

            # 取得當前價格
            try:
                symbol = o['coin'] + "USDC"
                kline_df = get_kline_data(symbol, interval="1m", limit=1)
                current_price = kline_df["close"].iloc[-1]
            except Exception as e:
                print(f"{o['coin']} 取得當前價格失敗:", e)
                current_price = o['price']

            # 計算倉位價值
            position_value = o['amount'] * current_price if current_price else 0

            new_msg = (
                f"💠 **巨鯨掛單新增** 💠\n"
                f"錢包名稱: {o['wallet_name']}\n"
                f"地址: {wallets.get(o['wallet_name'], '未知地址')}\n"
                f"幣種: {o['coin']}\n"
                f"方向: {display_side}\n"
                f"---------------\n"
                f"數量(顆): {o['amount']:.2f}\n"
                f"觸發價格: {o['price']}\n"
                f"訂單類型: {display_order_type}\n"
                f"---------------\n"
                f"倉位價值: {fmt_k(position_value)} USDC\n"
                f"當前價格: {current_price}"
            )
            send_telegram_message(new_msg)
    # 這裡放原本 main.py 的 check_new_orders 函式
    pass

def check_cancelled_orders(prev_orders_file, current_orders_df, wallets):
    # 讀取之前的訂單資料
    prev_orders = load_previous_data(
        prev_orders_file, 
        ["wallet_name", "coin", "side", "amount", "price", "orderType", "order_time", "order_id"]
    )

    prev_orders['order_id'] = prev_orders['order_id'].astype(str)
    current_orders_df['order_id'] = current_orders_df['order_id'].astype(str)

    # -------- 檢查取消的訂單 --------
    cancelled_orders = prev_orders.merge(
        current_orders_df[['order_id']],
        on='order_id',
        how='left',
        indicator=True
    )
    cancelled_orders = cancelled_orders[cancelled_orders['_merge'] == 'left_only']

    if cancelled_orders.empty:
        return  # 沒有取消掛單就結束

    # 以 (錢包名稱, 幣種, 方向) 為群組條件
    grouped = cancelled_orders.groupby(["wallet_name", "coin", "side"], as_index=False)

    for (wallet_name, coin, side), group in grouped:
        cancel_count = len(group)

        # 🔹 若同一錢包同一幣種同方向撤單超過10筆，批量彙總通知
        if cancel_count > CANCEL_COUNT:
            min_price = group["price"].min()
            max_price = group["price"].max()
            total_value = (group["amount"] * group["price"]).sum()
            display_side = "做多📈" if side.lower() == "buy" else "做空📉"

            batch_cancel_msg = (
                f"❌ **巨鯨批量撤單or成交** ❌\n"
                f"錢包名稱: {wallet_name}\n"
                f"地址: {wallets.get(wallet_name, '未知地址')}\n"
                f"幣種: {coin}\n"
                f"方向: {display_side}\n"
                f"---------------\n"
                f"撤單數量: {cancel_count} 筆\n"
                f"價格範圍: {min_price:.2f} ~ {max_price:.2f}\n"
                f"總倉位價值: {fmt_k(total_value)} USDC"
            )
            send_telegram_message(batch_cancel_msg)
            continue  # 不再逐筆通知這組

        # 🔸 否則逐筆發送取消通知
        for _, o in group.iterrows():
            order_type_map = {
                "Stop Market": "市價止損",
                "Limit": "限價單",
                "Take Profit Market": "市價止盈",
                "Take Profit Limit": "限價止盈",
                "Stop Limit": "限價止損"
            }
            display_order_type = order_type_map.get(o['orderType'], o['orderType'])
            display_side = "做多📈" if o['side'].lower() == "buy" else "做空📉"

            position_value = o['amount'] * o['price']  # 倉位價值
            cancel_msg = (
                f"❌ **巨鯨掛單撤銷or成交** ❌\n"
                f"錢包名稱: {o['wallet_name']}\n"
                f"地址: {wallets.get(o['wallet_name'], '未知地址')}\n"
                f"幣種: {o['coin']}\n"
                f"方向: {display_side}\n"
                f"---------------\n"
                f"數量(顆): {o['amount']:.2f}\n"
                f"觸發價格: {o['price']}\n"
                f"倉位價值: {fmt_k(position_value)} USDC\n"
                f"---------------\n"
                f"訂單類型: {display_order_type}\n"
                f"掛單時間: {o['order_time']}"
            )
            send_telegram_message(cancel_msg)



    # -------- 檢查修改的訂單（價格或數量或同時修改） --------
    merged_orders = prev_orders.merge(
        current_orders_df,
        on='order_id',
        suffixes=('_prev', '_curr')
    )

    for _, o in merged_orders.iterrows():
        order_type_map = {
            "Stop Market": "市價止損",
            "Limit": "限價單",
            "Take Profit Market": "市價止盈",
            "Take Profit Limit": "限價止盈",
            "Stop Limit": "限價止損"
        }
        display_order_type = order_type_map.get(o['orderType_curr'], o['orderType_curr'])
        display_side = "做多📈" if o['side_curr'].lower() == "buy" else "做空📉"

        price_changed = o['price_prev'] != o['price_curr']
        amount_changed = o['amount_prev'] != o['amount_curr']

        position_value_curr = o['amount_curr'] * o['price_curr']

        if price_changed:
            # 僅價格修改
            modify_msg = (
                f"✏️ **巨鯨掛單修改** ✏️\n"
                f"錢包名稱: {o['wallet_name_curr']}\n"
                f"地址: {wallets.get(o['wallet_name_curr'], '未知地址')}\n"
                f"幣種: {o['coin_curr']}\n"
                f"方向: {display_side}\n"
                f"訂單數量: {o['amount_curr']:2f}\n"
                f"---------------\n"
                f"舊觸發價格: {o['price_prev']}\n"
                f"新觸發價格: {o['price_curr']}\n"
                f"---------------\n"
                f"倉位價值: {fmt_k(position_value_curr)} USDC\n"
                f"訂單類型: {display_order_type}\n"
                f"掛單時間: {o['order_time_curr']}"
            )
            send_telegram_message(modify_msg)
