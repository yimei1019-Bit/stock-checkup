"""
盤中即時價格
------------------------------------------------
抓網頁上所有股票的盤中成交價，存成 live.json。網頁打開時會讀它，
用盤中價取代昨天的收盤價。GitHub 在交易時間每 20 分鐘跑一次。

用法：python live.py
"""

import json
import os
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from daily_report import TW
from official import fetch_live
from universe import build_universe

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    quotes = fetch_live(build_universe().keys())
    today = datetime.now(TW).strftime("%Y-%m-%d")
    quotes = {c: q for c, q in quotes.items() if q["date"] == today}
    if not quotes:
        print("今天沒有盤中資料（休市或還沒開盤），不更新")
        return
    latest = max(q["time"] for q in quotes.values())
    with open(os.path.join(HERE, "live.json"), "w", encoding="utf-8") as f:
        json.dump({"date": today, "time": latest, "quotes": quotes}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"盤中價格：{len(quotes)} 檔，時間 {today} {latest}")


if __name__ == "__main__":
    main()
