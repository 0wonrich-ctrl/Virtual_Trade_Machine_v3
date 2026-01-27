from datetime import timedelta

import pandas as pd
from pyprojroot import here

COIN_LIST = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"]

def check():

    for i, coin_name in enumerate(COIN_LIST, start=1):

        csv_path = here() / 'data' / f"{coin_name}_1m.csv"
        if not csv_path.exists():
            print(f"[{i}] {coin_name}_1m.csv 파일을 찾을 수 없습니다.")
            continue

        print(f"[{i}] 📁 {coin_name}_1m.csv 분석 중...", end="", flush=True)
        df = pd.read_csv(csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # 3. 시작 시간과 끝 시간 확인
        start_time = df['timestamp'].iloc[0]
        end_time = df['timestamp'].iloc[-1]
        total_rows = len(df)

        # 이전 행과의 시간 차이 계산
        df['diff'] = df['timestamp'].diff()

        # 1분(60초)이 아닌 구간 필터링 (첫 번째 행은 NaN이므로 제외)
        gaps = df[df['diff'] != timedelta(minutes=1)].iloc[1:]

        if gaps.empty:
            print(f"\r[{i}] ✅ {coin_name}_1m.csv 분석 결과")
            print(f" ├─▶ 길이: {start_time} ~ {end_time} ({total_rows}개)")
            print(f" └─▶ 연속성: 문제없음")
        else:
            print(f"\r[{i}] ❌ {coin_name}_1m.csv 분석 결과:")
            print(f" ├─▶ 길이: {start_time} ~ {end_time} ({total_rows}개)")
            print(f" └─▶ 연속성: 총 {len(gaps)}개의 끊긴 구간 발견")

            for idx, row in gaps.iterrows():
                prev_time = df.loc[idx - 1, 'timestamp']
                curr_time = row['timestamp']
                gap_duration = row['diff']

                print(f"    [Gap 발생]")
                print(f"    - 끊긴 지점: {prev_time} ~ {curr_time}")
                print(f"    - 비어있는 시간: {gap_duration}")

        df.drop(columns=['diff'], inplace=True)