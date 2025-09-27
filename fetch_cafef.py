import pandas as pd
import requests
from io import StringIO
from datetime import datetime


# ========== CONFIG ==========
urls = {
    "HSX": "https://cafef.vn/du-lieu-hsx.csv",
    "HNX": "https://cafef.vn/du-lieu-hnx.csv",
    "UPCOM": "https://cafef.vn/du-lieu-upcom.csv"
}
output_dir = "data_live/"

# Biên độ dao động giá trần/sàn (tham khảo: HSX/HNX ±7%, UPCOM ±15%)
ceiling_floor = {
    "HSX": 0.07,
    "HNX": 0.07,
    "UPCOM": 0.15
}

def fetch_and_process(exchange, url):
    print(f"📥 Đang tải dữ liệu {exchange} từ {url} ...")
    r = requests.get(url)
    r.encoding = "utf-8"
    if r.status_code != 200:
        print(f"❌ Lỗi tải {exchange}")
        return None
    
    df = pd.read_csv(StringIO(r.text))

    # Chuẩn hóa cột ngày
    date_col = None
    for col in df.columns:
        if col.lower() in ["date", "tradedate", "dtyyyymmdd"]:
            date_col = col
            break
    if not date_col:
        raise ValueError(f"Không tìm thấy cột Date trong {exchange}")

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce", format="%Y%m%d")
    df = df.rename(columns={date_col: "Date"})

    # Chuẩn hóa ticker
    for col in df.columns:
        if col.lower() == "ticker":
            df = df.rename(columns={col: "Ticker"})
            break

    # Thêm tên sàn
    df["Exchange"] = exchange

    # Thêm giá trần/sàn (dựa trên giá Close hôm qua)
    if "Close" in df.columns:
        band = ceiling_floor.get(exchange, 0.07)
        df["Ceiling"] = df["Close"] * (1 + band)
        df["Floor"] = df["Close"] * (1 - band)

    print(f"✅ {exchange}: {len(df)} dòng")
    return df

def main():
    all_df = []
    for exch, url in urls.items():
        try:
            df = fetch_and_process(exch, url)
            if df is not None:
                all_df.append(df)
                # Lưu file riêng từng sàn
                today = datetime.now().strftime("%Y%m%d")
                df.to_csv(f"{output_dir}{exch}_{today}.csv", index=False, encoding="utf-8-sig")
        except Exception as e:
            print(f"❌ Lỗi {exch}: {e}")

    if all_df:
        df_all = pd.concat(all_df, ignore_index=True)
        today = datetime.now().strftime("%Y%m%d")
        df_all.to_csv(f"{output_dir}ALL_{today}.csv", index=False, encoding="utf-8-sig")
        print(f"\n📊 Tổng cộng {len(df_all)} dòng dữ liệu (ALL_{today}.csv)")

if __name__ == "__main__":
    main()
