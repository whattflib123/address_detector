import os
from config import wallets, ORDERS_FILE, NEW_ORDERS_FILE, POSITIONS_FILE, NEW_POSITIONS_FILE
from positions import  check_decreased_positions, check_new_positions
from orders import check_new_orders, check_cancelled_orders
from wallet import sync_wallet_orders_positions


if __name__ == "__main__":

    current_orders_df, current_positions_df, previous_positions, previous_orders = sync_wallet_orders_positions(wallets)

    # ---------------- 儲存新的掛單檔 ----------------
    current_orders_df.to_csv(NEW_ORDERS_FILE, index=False)
    current_positions_df.to_csv(NEW_POSITIONS_FILE, index=False)  # 持倉直接覆蓋

    # ---------------- 發送掛單通知 ----------------
    check_cancelled_orders(ORDERS_FILE, current_orders_df, wallets)
    check_new_orders(ORDERS_FILE, current_orders_df, wallets)

    # ---------------- 發送持倉通知 ----------------
    changed_wallets_coins  = check_decreased_positions(POSITIONS_FILE, current_positions_df, wallets)
    check_new_positions(POSITIONS_FILE, current_positions_df, wallets, changed_wallets_coins )

    # ---------------- 覆蓋舊掛單 ----------------
    os.replace(NEW_ORDERS_FILE, ORDERS_FILE)
    os.replace(NEW_POSITIONS_FILE, POSITIONS_FILE)

