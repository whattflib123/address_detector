from utils import load_previous_data
from utils import send_telegram_message
from utils import fmt_k, get_kline_data
import pandas as pd


def check_decreased_positions(prev_positions_file, current_positions_df, wallets):
    prev_positions = load_previous_data(
        prev_positions_file,
        ["wallet_name", "coin", "side", "amount", "entry_price", "liquidation_price"]
    )

    merged = pd.merge(
        prev_positions, current_positions_df,
        on=["wallet_name", "coin", "side"],
        how="outer",
        suffixes=("_prev", "_curr"),
        indicator=True
    )

    # 找出有變化的倉位
    changed_positions = merged[
        (merged["_merge"] == "left_only") |
        ((merged["_merge"] == "both") & (
            (merged["amount_curr"].fillna(0) != merged["amount_prev"].fillna(0))
        ))
    ]

    wallet_coin_map = {}

    for _, row in changed_positions.iterrows():
        wallet_name = row["wallet_name"]
        coin = row["coin"]
        side = row["side"]
        wallet_address = wallets.get(wallet_name, "未知地址")
        display_side = "做多📈" if str(side).lower() == "long" else "做空📉"

        prev_amount = row["amount_prev"] if not pd.isna(row["amount_prev"]) else 0
        curr_amount = row["amount_curr"] if not pd.isna(row["amount_curr"]) else 0
        prev_price = row["entry_price_prev"] if not pd.isna(row.get("entry_price_prev")) else 0
        curr_price = row["entry_price_curr"] if not pd.isna(row.get("entry_price_curr")) else prev_price

        # ✅ 新增強平價格欄位（前後持倉）
        prev_liq = row.get("liquidation_price_prev", None)
        curr_liq = row.get("liquidation_price_curr", None)

        try:
            prev_liq = round(float(prev_liq), 2) if not pd.isna(prev_liq) else None
        except:
            prev_liq = None
        try:
            curr_liq = round(float(curr_liq), 2) if not pd.isna(curr_liq) else prev_liq
        except:
            curr_liq = prev_liq


        # 取得當前幣價
        try:
            symbol = row["coin"] + "USDC"
            kline_df = get_kline_data(symbol, interval="1m", limit=1)
            close_price = kline_df["close"].iloc[-1]
        except Exception as e:
            print(f"{coin} 取得當前價格失敗:", e)
            close_price = curr_price or prev_price

        prev_value = prev_amount * prev_price
        curr_value = curr_amount * curr_price

        # 🟢 平倉
        if curr_amount == 0:
            msg_title = "⚠️ **巨鯨平倉** ⚠️"
            msg_body = (
                f"---------------\n"
                f"開倉數量(顆): {prev_amount:.2f}\n"
                f"減少數量(顆): {prev_amount:.2f}\n"
                f"當前數量(顆): 0\n"
                f"---------------\n"
                f"進場價格: {prev_price}\n"
                f"倉位價值: {fmt_k(prev_value)} USDC\n"
            )

        # 🟡 減倉
        elif curr_amount < prev_amount:
            decreased_amount = prev_amount - curr_amount
            msg_title = "🔻 **巨鯨減倉** 🔻"
            msg_body = (
                f"---------------\n"
                f"原持倉數(顆): {prev_amount:.2f}\n"
                f"減少數量(顆): {decreased_amount:.2f}\n"
                f"當前數量(顆): {curr_amount:.2f}\n"
                f"---------------\n"
                f"進場價格: {prev_price}\n"
                f"剩餘倉位價值: {fmt_k(curr_value)} USDC\n"
                f"強平價格: {curr_liq if curr_liq else 0} USDC\n"
            )

        # 🟢 加倉
        elif curr_amount > prev_amount:
            increased_amount = curr_amount - prev_amount
            new_avg_price = ((prev_amount * prev_price) + (increased_amount * curr_price)) / (prev_amount + increased_amount) if prev_amount > 0 else curr_price
            msg_title = "💹 **巨鯨加倉** 💹"
            msg_body = (
                f"---------------\n"
                f"原持倉數(顆): {prev_amount:.2f}\n"
                f"增加數量(顆): {increased_amount:.2f}\n"
                f"當前數量(顆): {curr_amount:.2f}\n"
                f"---------------\n"
                f"持倉均價: {new_avg_price:.6f}\n"
                f"總持倉價值: {fmt_k(curr_value)} USDC\n"
                f"強平價格: {curr_liq if curr_liq else 0} USDC\n"
            )
        else:
            continue

        msg = (
            f"{msg_title}\n"
            f"錢包名稱: {wallet_name}\n"
            f"地址: {wallet_address}\n"
            f"幣種: {coin}\n"
            f"方向: {display_side}\n"
            f"{msg_body}"
            f"當前價格: {close_price}"
        )

        send_telegram_message(msg)

        if wallet_name not in wallet_coin_map:
            wallet_coin_map[wallet_name] = []
        wallet_coin_map[wallet_name].append({"coin": coin, "side": side})

    return wallet_coin_map

def check_new_positions(prev_positions_file, current_positions_df, wallets, changed_wallets_coins):
    prev_positions = load_previous_data(
        prev_positions_file,
        ["wallet_name", "coin", "side", "amount", "entry_price", "liquidation_price"]
    )

    merged = pd.merge(
        current_positions_df, prev_positions,
        on=["wallet_name", "coin", "side"],
        how="left",
        suffixes=("_curr", "_prev"),
        indicator=True
    )
    
    new_positions = merged[merged["_merge"] == "left_only"]

    for _, row in new_positions.iterrows():
        wallet_name = row["wallet_name"]
        coin = row["coin"]
        side = row["side"]

        # 避免重複通知（如果該錢包該幣別已在變化列表中）
        if wallet_name in changed_wallets_coins and coin in changed_wallets_coins[wallet_name] and side in changed_wallets_coins[wallet_name]:
            continue

        wallet_address = wallets.get(wallet_name, "未知地址")
        display_side = "做多📈" if str(side).lower() == "long" else "做空📉"

        amount = row["amount_curr"]
        entry_price = row["entry_price_curr"]

        # ✅ 取得強平價格並四捨五入
        liquidation_price = row.get("liquidation_price_curr", None)
        try:
            liquidation_price = round(float(liquidation_price), 2) if not pd.isna(liquidation_price) else None
        except:
            liquidation_price = None

        # ✅ 取得即時市場價格
        try:
            symbol = coin + "USDC"
            kline_df = get_kline_data(symbol, interval="1m", limit=1)
            close_price = kline_df["close"].iloc[-1]
        except Exception as e:
            print(f"{coin} 取得當前價格失敗:", e)
            close_price = entry_price

        position_value = amount * entry_price

        msg = (
            f"🚀 **巨鯨開倉** 🚀\n"
            f"錢包名稱: {wallet_name}\n"
            f"地址: {wallet_address}\n"
            f"幣種: {coin}\n"
            f"方向: {display_side}\n"
            f"---------------\n"
            f"數量(顆): {amount:.2f}\n"
            f"進場價格: {entry_price}\n"
            f"倉位價值: {fmt_k(position_value)} USDC\n"
            f"強平價格: {liquidation_price if liquidation_price else '0'} USDC\n"
            f"當前價格: {close_price}"
        )

        send_telegram_message(msg)
