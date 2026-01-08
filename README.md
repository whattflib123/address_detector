# 巨鯨交易監控系統 (Whale Tracker)

- 這是專門用於監控 Hyperliquid 指定錢包地址的持倉與掛單變化，並透過 Telegram 發送通知

---

## 安裝需求
python 套件：

```bash
pip install pandas requests numpy hyperliquid
```

##  主程式的使用方式: ```python main.py```


1. **Telegram Bot**

   * 用 [BotFather](https://t.me/botfather) 建立 Bot，取得 `BOT_TOKEN`
   * 找到你的 `CHAT_ID`（可用 `@userinfobot` 或寫程式測試）

2. 在 config.py 設定：

    - 欲監控的錢包地址 (需為hyperliquid上的錢包地址)
      ```python
      wallets = {
          "自定義錢包名": "錢包地址",
          # example
          "🟢 波段大師 (持倉時間極短)": "0xc2a30212a8ddac9e123944d6e29faddce994e5f2",
          "🔵 100%勝率 (低倍槓桿)": "0x4e8d91cb10b32ca351ac8f1962f33514a96797f4",
      }
      ```
    - Telegram Bot Token 與 Chat ID
    - CSV 檔案路徑（訂單與持倉）

3. 透過**排程**決定多久執行一次主程式： main.py

    - example: 我設定每分鐘檢測一次，確保不會漏看
    - ```python main.py```

4. 主程式會：
    - 取得錢包持倉與掛單資訊，與歷史資料比對
    - 發送 Telegram 通知
    - 更新本地的持倉資料 CSV 檔案



## 工具程式的使用方式: ```python send_current_order_position.py```

1. 工具程式會：
    - 取得錢包當下持倉
    - 發送 Telegram 通知

2. 透過**排程**決定多久執行一次工具程式： send_current_order_position.py

    - example: 我設定每8小時傳送一次當下巨鯨持倉
    - ```python send_current_order_position.py```




---

## 專案結構

    address_detector/
    │
    ├─ data/ # 存放當下訂單以及持倉
    │ └─ orders.csv
    │ └─ positions.csv 
    │
    ├─ utils/ # 工具函式
    │ └─ get_kline.py # 取得幣價k線相關資訊
    │ └─ load_csv_data.py # 讀data中的檔案
    │ └─ send_msg.py # 傳telegram 訊息
    │
    ├─ config.py # 全域設定
    ├─ main.py # 主程式
    ├─ orders.py # 處理掛單相關
    ├─ positions.py # 處理持倉相關
    ├─ send_current_order_position.py # 傳送當下持倉
    └─ wallet.py # 與 Hyperliquid API 互動、取得錢包資料

---

## 實際畫面
- 實時監控畫面: 
    <p align="center">
    <img src="pic/real_time.jpg" width="200">
    </p>

- #### 開倉相關訊息

    <p align="center">
    <img src="pic/position_open.jpg" width="300">
    <img src="pic/position_close.jpg" width="300">
    <img src="pic/position_add.jpg" width="300">
    <img src="pic/position_minus.jpg" width="300">
    </p>
- #### 掛單相關訊息

    <p align="center">
    <img src="pic/order_add.jpg" width="300">
    <img src="pic/order_minus.jpg" width="300">
    </p>

---

