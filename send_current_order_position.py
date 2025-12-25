import pandas as pd
from config import POSITIONS_FILE
from utils import send_telegram_message
from utils import fmt_k

def get_position_message(position_file = POSITIONS_FILE):
    msg_parts = []

    # 取得倉位資料
    try:
        positions_df = pd.read_csv(position_file)
        positions_df["position_value"] = positions_df["amount"] * positions_df["entry_price"]
        positions_df["value_str"] = positions_df["position_value"].apply(fmt_k)

        msg_parts.append("━━━━━━━━━━━━━━\n<b>📊 目前倉位概況</b>\n━━━━━━━━━━━━━━")

        for wallet_name, group in positions_df.groupby("wallet_name"):
            msg_parts.append(f"💼 <b>{wallet_name}</b>")
            for _, row in group.iterrows():
                coin = row["coin"]
                side = "多" if row["side"].lower() == "long" else "空"
                amount = f"{row['amount']:.2f}"
                price = f"{row['entry_price']:.2f}"
                liq_price = f"{row['liquidation_price']:.2f}" if not pd.isna(row["liquidation_price"]) else "—"
                value = row["value_str"]

                msg_parts.append(
                    f"・{coin}({side}) @ {price} 價值:{value} USD\n"
                    f"　強平價: {liq_price}\n"
                    f"-----------"
                )
            msg_parts.append("")  # 每個錢包間空行

    except FileNotFoundError:
        msg_parts.append(f"⚠️ {position_file} 不存在")

    # ---------------- 傳送文字訊息 ----------------
    final_message = "\n".join(msg_parts)
    return final_message

    

# ---------------- 主程式 ----------------
if __name__ == "__main__":

    whale_message = get_position_message(position_file=POSITIONS_FILE)
    send_telegram_message(whale_message)

