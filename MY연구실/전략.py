from src import VirtualTradeMachine as vtm


# --- 지표 계산 헬퍼 함수 ---
def calculate_ema(data, window):
    if len(data) < window: return None
    alpha = 2 / (window + 1)
    ema = sum(data[:window]) / window
    for price in data[window:]:
        ema = (price * alpha) + (ema * (1 - alpha))
    return ema


def calculate_atr(highs, lows, closes, period=14):
    if len(closes) < period + 1: return None
    tr_list = []
    for i in range(1, len(closes)):
        h = highs[i]
        l = lows[i]
        pc = closes[i - 1]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_list.append(tr)
    return sum(tr_list[-period:]) / period


def calculate_rsi(data, period=14):
    if len(data) < period + 1: return None
    deltas = [data[i + 1] - data[i] for i in range(len(data) - 1)]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def strategy():
    # 1. 초기 세팅 (안정성을 위해 레버리지 3배로 하향 조정)
    # MDD -78%는 실전에서 파산입니다. 3배로 낮춰도 복리로 충분히 큽니다.
    vtm.setup(bal=1000.0, lev=3)

    # 2. 리샘플링 변수 (4시간 봉)
    temp_candles = {'close': [], 'high': [], 'low': []}
    resampled = {'close': [], 'high': [], 'low': []}

    macd_history = []
    RESAMPLE_PERIOD = 240  # 4시간 봉

    # 전략 상태 변수
    highest_price_since_entry = 0
    lowest_price_since_entry = 0
    current_atr = 0

    # 좀비 주문 방지
    open_order_wait_time = 0
    MAX_WAIT_TIME = 240

    while True:
        vtm.next_time()
        info = vtm.now_info()

        c_price = info['close']
        c_high = info['high']
        c_low = info['low']

        # --- [관리] 좀비 주문 방지 ---
        if info['is_order']:
            open_order_wait_time += 1
            if open_order_wait_time > MAX_WAIT_TIME:
                vtm.cancel_order()
                open_order_wait_time = 0
            continue
        else:
            open_order_wait_time = 0

        # --- [데이터] 가상 4시간 봉 생성 ---
        temp_candles['close'].append(c_price)
        temp_candles['high'].append(c_high)
        temp_candles['low'].append(c_low)

        is_candle_closed = False

        # 4시간이 지났으면 봉 마감 처리
        if len(temp_candles['close']) >= RESAMPLE_PERIOD:
            resampled['close'].append(temp_candles['close'][-1])
            resampled['high'].append(max(temp_candles['high']))
            resampled['low'].append(min(temp_candles['low']))

            # 메모리 관리 (최근 300개만 유지)
            if len(resampled['close']) > 300:
                for k in resampled: resampled[k].pop(0)

            # 임시 버퍼 초기화
            for k in temp_candles: temp_candles[k] = []
            is_candle_closed = True

        # --- [전략 판단] 4시간 봉 마감 시 ---
        if is_candle_closed and len(resampled['close']) >= 120:
            closes = resampled['close']

            # 지표 계산
            ema_trend = calculate_ema(closes, 120)
            ema12 = calculate_ema(closes, 12)
            ema26 = calculate_ema(closes, 26)
            rsi = calculate_rsi(closes, 14)
            atr_val = calculate_atr(resampled['high'], resampled['low'], closes, 14)

            # 전역 변수 업데이트 (청산 로직용)
            if atr_val: current_atr = atr_val

            if ema12 and ema26 and ema_trend and rsi and atr_val:
                macd_val = ema12 - ema26
                macd_history.append(macd_val)
                if len(macd_history) > 50: macd_history.pop(0)

                macd_signal = calculate_ema(macd_history, 9)

                # 시각화 등록
                vtm.register_indicator("EMA120", ema_trend)
                vtm.register_indicator("RSI", rsi, sub_chart=True)
                if macd_signal:
                    vtm.register_indicator("MACD", macd_val, sub_chart=True)

                # 매매 로직 진입
                if macd_signal is not None:
                    # 포지션 없을 때 진입 로직
                    if not info['is_position']:
                        # [LONG 조건]
                        # 1. 정배열 (가격 > EMA120)
                        # 2. MACD 골든크로스 (MACD > Signal)
                        # 3. RSI 과열 아님 (RSI < 70) -> 고점 추격 매수 방지
                        if c_price > ema_trend and macd_val > macd_signal and rsi < 70:
                            vtm.open_order(side=vtm.LONG, price=c_price, betting_rate=0.5)
                            highest_price_since_entry = c_price  # 고점 초기화

                        # [SHORT 조건] - 신규 추가!
                        # 1. 역배열 (가격 < EMA120)
                        # 2. MACD 데드크로스 (MACD < Signal)
                        # 3. RSI 침체 아님 (RSI > 30) -> 저점 추격 매도 방지
                        elif c_price < ema_trend and macd_val < macd_signal and rsi > 30:
                            vtm.open_order(side=vtm.SHORT, price=c_price, betting_rate=0.5)
                            lowest_price_since_entry = c_price  # 저점 초기화

                    # 포지션 있을 때 스위칭/청산 로직 (추세 반전 시)
                    else:
                        side = info['position']['side']
                        # 롱인데 하락 추세 확정 시 청산
                        if side == vtm.LONG and (c_price < ema_trend or macd_val < macd_signal):
                            vtm.close_order(price=c_price)
                        # 숏인데 상승 추세 확정 시 청산
                        elif side == vtm.SHORT and (c_price > ema_trend or macd_val > macd_signal):
                            vtm.close_order(price=c_price)

        # -----------------------------------------------------------
        # [청산] 1분 단위 실시간 모니터링 (샹들리에 청산 + 손절)
        # -----------------------------------------------------------
        if info['is_position']:
            pos = info['position']
            entry_price = pos['price']
            side = pos['side']

            # ATR 없으면 진입가의 1%로 임시 설정
            safe_atr = current_atr if current_atr > 0 else entry_price * 0.01

            # --- LONG 포지션 관리 ---
            if side == vtm.LONG:
                if c_price > highest_price_since_entry:
                    highest_price_since_entry = c_price

                # 수익률에 따른 탄력적 ATR 적용 (수익이 클수록 타이트하게)
                roi = (c_price - entry_price) / entry_price
                atr_mult = 3.5 if roi < 0.05 else 2.0  # 5% 수익 넘으면 2 ATR로 조임

                stop_price = highest_price_since_entry - (safe_atr * atr_mult)
                # 비상 손절: 진입가 대비 -3% (레버리지 3배 시 -9%)
                emergency = entry_price * 0.97

                final_stop = max(stop_price, emergency)

                if c_price <= final_stop:
                    if info['is_order']: vtm.cancel_order()
                    vtm.close_order(price=c_price)

            # --- SHORT 포지션 관리 ---
            elif side == vtm.SHORT:
                if c_price < lowest_price_since_entry or lowest_price_since_entry == 0:
                    lowest_price_since_entry = c_price

                roi = (entry_price - c_price) / entry_price
                atr_mult = 3.5 if roi < 0.05 else 2.0

                stop_price = lowest_price_since_entry + (safe_atr * atr_mult)
                # 비상 손절: 진입가 대비 +3%
                emergency = entry_price * 1.03

                final_stop = min(stop_price, emergency)

                if c_price >= final_stop:
                    if info['is_order']: vtm.cancel_order()
                    vtm.close_order(price=c_price)