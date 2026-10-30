"""
台灣證交所、櫃買中心的官方資料
------------------------------------------------
fetch_official()  收盤後的官方每日行情（用來補 Yahoo 漏掉的日子）
fetch_live(codes) 盤中即時成交價（證交所基本市況報導，約 5 秒更新）
"""

import json
import urllib.request

UA = {"User-Agent": "Mozilla/5.0"}


def _get_json(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8"))


def _roc_date(s):
    """民國日期 1151029 → 2026-10-29"""
    s = str(s).strip()
    return f"{int(s[:-4]) + 1911}-{s[-4:-2]}-{s[-2:]}"


def _num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except ValueError:
        return None


def fetch_official():
    """回傳 {代號: {"date", "open", "high", "low", "close", "volume"(股)}}，上市＋上櫃。"""
    out = {}
    try:
        for r in _get_json("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"):
            o, h, l, c = (_num(r.get(k)) for k in ("OpeningPrice", "HighestPrice", "LowestPrice", "ClosingPrice"))
            if c:
                out[r["Code"]] = {"date": _roc_date(r["Date"]), "open": o or c, "high": h or c, "low": l or c,
                                  "close": c, "volume": _num(r.get("TradeVolume")) or 0}
    except Exception as e:
        print("證交所每日行情抓取失敗：", e)
    try:
        for r in _get_json("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"):
            o, h, l, c = (_num(r.get(k)) for k in ("Open", "High", "Low", "Close"))
            if c:
                out.setdefault(r["SecuritiesCompanyCode"], {"date": _roc_date(r["Date"]), "open": o or c, "high": h or c,
                                                            "low": l or c, "close": c, "volume": _num(r.get("TradingShares")) or 0})
    except Exception as e:
        print("櫃買中心每日行情抓取失敗：", e)
    return out


def fetch_live(codes):
    """回傳 {代號: {"date", "time", "price", "prev", "open", "high", "low", "volume"(張)}}。"""
    out = {}
    codes = list(codes)
    for i in range(0, len(codes), 30):
        chunk = codes[i:i + 30]
        ex_ch = "|".join(f"tse_{c}.tw|otc_{c}.tw" for c in chunk)
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={ex_ch}&json=1&delay=0"
        try:
            data = _get_json(url)
        except Exception as e:
            print("即時行情抓取失敗：", e)
            continue
        for m in data.get("msgArray", []):
            price = _num(m.get("z"))
            if price is None:  # 這 5 秒內沒有成交，用最近一筆成交價，再沒有就用最佳買價
                price = _num((m.get("trade") or {}).get("z"))
            if price is None:
                price = _num((m.get("b") or "").split("_")[0])
            prev = _num(m.get("y"))
            if price is None or not prev:
                continue
            d = m.get("d", "")
            out[m["c"]] = {
                "date": f"{d[:4]}-{d[4:6]}-{d[6:8]}", "time": m.get("t", "")[:5], "price": price, "prev": prev,
                "open": _num(m.get("o")) or price, "high": _num(m.get("h")) or price, "low": _num(m.get("l")) or price,
                "volume": int(_num(m.get("v")) or 0),
            }
    return out
