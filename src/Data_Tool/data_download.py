import ccxt
import pandas as pd
from pyprojroot import here

# 설정
COIN_LIST = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]
END_TIME = "2026-01-23 00:00:00"
START_TIME = "2020-01-01 00:00:00"
TIMEFRAME = '1m'
LIMIT = 1000

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',  # 선물 데이터
    }
})
# 이모지 애니메이션 개선
moon_idx = 0

def get_moon():
    global moon_idx
    moon_list = ["🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌑"]
    char = moon_list[moon_idx % len(moon_list)]
    moon_idx += 1
    return char


def download_data(symbol, coin_num):
    start_ts = exchange.parse8601(START_TIME)
    end_ts = exchange.parse8601(END_TIME)
    now_time = start_ts
    total_range = end_ts - start_ts

    print(f"[{coin_num}] ⏳ {symbol} 데이터 탐색 및 검증 시작...", end="", flush=True)

    all_candles = []

    while now_time < end_ts:
        try:
            candles = exchange.fetch_ohlcv(symbol, TIMEFRAME, since=now_time, limit=LIMIT)
            if not candles:
                break

            if all_candles:
                expected_time = all_candles[-1][0] + 60000
                if candles[0][0] != expected_time:
                    print(f"\n❌ [GAP 발생] {symbol}: {exchange.iso8601(all_candles[-1][0])} 이후 데이터 누락!")
                    return

            for i in range(1, len(candles)):
                diff = candles[i][0] - candles[i - 1][0]
                if diff != 60000:
                    gap_time = exchange.iso8601(candles[i - 1][0])
                    print(f"\n❌ [배치 내 GAP] {symbol}: {gap_time} 구간에서 {diff / 60000}분 공백 발견!")
                    return

            all_candles.extend(candles)
            last_ts = candles[-1][0]
            progress = min(((last_ts - start_ts) / total_range) * 100, 100.0)
            print(f"\r[{coin_num}] {get_moon()} {symbol} 다운로드 중 ({progress:.1f}% : {pd.to_datetime(now_time, unit='ms').strftime('%Y-%m-%d %H:%M:%S')})", end="", flush=True)

            now_time = last_ts + 60000
            if now_time >= end_ts: break

        except Exception as e:
            print(f"\n❌ [ERROR] {e}")
            return

    # 저장
    if all_candles:
        print(f"\r[{coin_num}] 📄 {symbol} csv파일로 변환 및 저장중... ",end="", flush=True)
        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = df[df['timestamp'] < end_ts]
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        file_path = here() / 'data' / f"{symbol}_1m.csv"
        df.to_csv(file_path)
        print(f"\r[{coin_num}] ✅ [{symbol}] 저장 완료 ({df.index[0]} ~ {df.index[-1]})")


def make_data():
    print(f"\n[1] 📂 data 저장공간 준비중...", end="", flush=True)
    data_dir = here() / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"\r[1] ✅ data 폴더 준비 완료")

    for idx, symbol in enumerate(COIN_LIST, start=2):
        download_data(symbol, idx)

