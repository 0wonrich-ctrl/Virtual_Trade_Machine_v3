from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from typing import Optional

import numpy as np
import pandas as pd
from pyprojroot import here

# =======================================================================================================================
from MY연구실 import 설정
from src.VTM3 import View

LONG = "LONG"
SHORT = "SHORT"

MAKER_FEE = 0.0002  # 지정가 수수료 (0.02%)
TAKER_FEE = 0.00055  # 시장가 수수료 (0.055%)
MAINTENANCE_MARGIN_RATE = 0.03  # 유지 증거금 비율 (3%)

# 상수
#------------
# 변수

# 초기 변수
coin_name = None
coin_df = None
indicator_list = []
history_list = []

initial_balance = 0.0  # 초기 자본

# 거래용 변수
leverage = 100  # 레버리지
margin_balance = 1000.0 # 총 잔고
available_balance = 1000.0 # 사용 가능 잔고

time_index = 0

is_position = False
position = SimpleNamespace(
    side = None,  # str: LONG or SHORT
    price = None, # float: 진입가
    used_margin = None, # float: 초기 투자금
    position_equity = None, # float: 투자금 현황
    open_fee = None, # float: 포지션 열기 수수료
)

is_order = False
order = SimpleNamespace(
    action = None,  # str: OPEN or CLOSE
    side = None,  # str: LONG or SHORT
    price = None, # float: 진입가
    betting_rate = None, # float: 시드 대비 베팅 비율
)

#=======================================================================================================================

def set_coin(coin_symbol:str):
    global coin_name
    coin_name = f"{coin_symbol}USDT"

def setup(bal: float = 1000.0, lev: int = 100):
    global indicator_list, history_list
    indicator_list = []
    history_list = []

    global initial_balance, margin_balance, available_balance
    initial_balance = bal
    margin_balance = bal
    available_balance = bal

    global leverage
    leverage = lev

    global coin_df
    csv_path = here() / 'data' / f"{coin_name}_1m.csv"
    try:
        print(f"📂 ({coin_name})코인 데이터 불러오는 중... ")
        coin_df = pd.read_csv(csv_path)
    except FileNotFoundError:
        View.error(f"[setup] 코인 데이터를 찾을 수 없음 - ({csv_path})")
        exit()
    coin_df['timestamp'] = pd.to_datetime(coin_df['timestamp'])

    required_cols = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
    if not required_cols.issubset(coin_df.columns):
        missing = required_cols - set(coin_df.columns)
        View.error(f"[setup] 데이터 파일에 필수 컬럼이 없습니다: {missing}")
        exit()

    if coin_df[list(required_cols)].isnull().values.any():
        View.error("[setup] 데이터에 결측치(NaN)가 포함되어 있습니다")
        exit()

    if not coin_df['timestamp'].is_monotonic_increasing:
        View.error("[setup] 데이터가 시간 순서대로 정렬되어 있지 않습니다")
        exit()

    if 설정.RECENT_DAY:
        df_len = min(len(coin_df), 설정.RECENT_DAY * 60 * 24)
        coin_df = coin_df.tail(df_len).reset_index(drop=True)

    start_ts = coin_df['timestamp'].iloc[0]
    end_ts = coin_df['timestamp'].iloc[-1]
    print(f"📅 {start_ts.strftime('%Y-%m-%d %H:%M:%S')} → {end_ts.strftime('%Y-%m-%d %H:%M:%S')} ({(end_ts - start_ts).days + 1}일)")


def next_time():
    global time_index

    if time_index >= len(coin_df) - 1:
        print(f"[{coin_df['timestamp'].iloc[time_index]}] 백테스팅 완료 / 데이터 분석중...")
        View.final_result(__get_df_for_view(), coin_name, leverage, initial_balance)
        exit(0)

    time_index += 1

    if margin_balance <= (initial_balance * 설정.ACCOUNT_BLOWN) or margin_balance <= 1:
        print(f"[{coin_df['timestamp'].iloc[time_index]}] 계좌 청산으로 백테스팅 종료 / 데이터 분석중...")
        View.final_result(__get_df_for_view(),coin_name, leverage, initial_balance)
        exit(0)

    __update()


def now_info():
    curr_data = coin_df.iloc[time_index]
    return {
        "timestamp" : curr_data['timestamp'],
        "open": curr_data['open'],
        "high": curr_data['high'],
        "low": curr_data['low'],
        "close": curr_data['close'],
        "volume": curr_data['volume'],

        "margin_balance" : margin_balance,
        "available_balance" : available_balance,

        "is_position" : is_position,
        "position" : {
            "side" : position.side,
            "price": position.price,
            "used_margin": position.used_margin,
            "position_equity": position.position_equity,
            "open_fee": position.open_fee,
        },

        "is_order": is_order,
        "order": {
            "action": order.action,
            "side": order.side,
            "price": order.price,
            "betting_rate": order.betting_rate,
        }
    }


def open_order(side, price:float, betting_rate:float):
    global is_order, order

    # 유효성
    if side != LONG and side != SHORT:
        View.error(f"[open_order] 잘못된 방향 : {side}")
        exit()
    elif 0 > price:
        View.error(f"[open_order] 잘못된 가격 : {price}")
        exit()
    elif 0 > betting_rate or betting_rate > 0.8:
        View.warn(f"[open_order] 잘못된 투자 비율 (0% 이상 ~ 80% 이하 가능) : {betting_rate}")
        return False
    elif is_position:
        View.warn("[open_order] 이미 포지션이 있는 상황에서 포지션 열기 주문을 시도함")
        return False
    else:
        is_order = True
        order.action = "OPEN"
        order.side = side
        order.price = price
        order.betting_rate = betting_rate
        return True

def close_order(price):
    global is_order, order
    # 유효성
    if 0 > price:
        View.error(f"[close_order] 잘못된 가격 : {price}")
        exit()
    elif not is_position:
        View.warn("[close_order] 가진 포지션이 없는 상황에서 포지션 닫기 주문을 시도함")
        return False
    else:
        is_order = True
        order.action = "CLOSE"
        order.side = None
        order.price = price
        order.betting_rate = None
        return True

def cancel_order():
    global is_order, order
    is_order = False
    order.action = None
    order.side = None
    order.price = None
    order.betting_rate = None


@dataclass
class CustomIndicator:
    timestamp: datetime
    name: str
    value: float = None
    sub_chart:bool = False

def register_indicator(name: str, value: float, sub_chart = False):
    global indicator_list
    indicator_list.append(
        CustomIndicator(
            coin_df.iloc[time_index]['timestamp'], name, value, sub_chart
        )
    )


# public 메소드
#=======================================================================================================================
# private 메소드

def __get_df_for_view():
    global coin_df, history_list, indicator_list, initial_balance

    merged_df = coin_df.iloc[:time_index + 1].copy()

    # 1 매매 기록 병합
    if history_list:
        history_data = [
            {
                "timestamp": h.timestamp,
                "T_balance": h.balance,
                "T_action": h.action,
                "T_side": h.side,
                "T_price": h.price,
                "T_pnl": h.pnl
            }
            for h in history_list
        ]
        history_df = pd.DataFrame(history_data)
        merged_df = pd.merge(merged_df, history_df, on="timestamp", how="left")
    else:
        # 거래 기록 없으면 빈 컬럼 생성
        for col in ['T_balance', 'T_action', 'T_side', 'T_price', 'T_pnl']:
            merged_df[col] = np.nan
        merged_df['T_balance'] = initial_balance

    # 2 지표 병합
    if indicator_list:
        ind_data = []
        for i in indicator_list:
            prefix = "IS" if i.sub_chart else "IO"
            ind_data.append({
                "timestamp": i.timestamp,
                "name": f"{prefix}_{i.name}",  # 예: IO_SMA, IS_RSI
                "value": i.value
            })

        ind_df = pd.DataFrame(ind_data)
        ind_wide_df = ind_df.pivot_table(index='timestamp', columns='name', values='value', aggfunc='last')
        merged_df = pd.merge(merged_df, ind_wide_df, on='timestamp', how='left')

    if 'T_balance' in merged_df.columns:
        merged_df['T_balance'] = merged_df['T_balance'].ffill().fillna(initial_balance)

    return merged_df


def __update():
    global margin_balance, available_balance, is_position, position, is_order, order

    # 현재 데이터
    curr_data = coin_df.iloc[time_index]
    timestamp = curr_data['timestamp']
    # open = curr_data['open']
    high = curr_data['high']
    low = curr_data['low']
    close = curr_data['close']
    # volume = curr_data['volume']

    now_history = History(timestamp)

    # 포지션 열기 주문 처리 -> 강제 청산 처리 -> 포지션 닫기 주문 처리 -> 수익률 처리

    # 1 : 포지션 열기 주문 처리
    if not is_position and is_order and order.action == "OPEN":
        is_executed = False

        # LONG 진입
        if order.side == LONG and low <= order.price:
            is_executed = True

        # SHORT 진입
        elif order.side == SHORT and high >= order.price:
            is_executed = True

        # 체결 로직
        if is_executed:
            used_margin = margin_balance * order.betting_rate  # 투자금 계산
            open_fee = used_margin * MAKER_FEE * leverage  # 수수료 계산

            margin_balance -= open_fee
            available_balance = margin_balance - used_margin

            is_position = True
            position.side = order.side
            position.price = order.price
            position.used_margin = used_margin
            position.position_equity = used_margin
            position.open_fee = open_fee

            now_history.action = "OPEN"
            now_history.side = position.side
            now_history.price = position.price

            cancel_order()

            if position.side == LONG:
                View.long(timestamp, f"b : {margin_balance:.2f} (price: {position.price:.2f})")
            else:
                View.short(timestamp, f"b : {margin_balance:.2f} (price: {position.price:.2f})")

    # 2 : 강제 청산 처리
    if is_position:
        worst_roe = 100 # 어차피 안고쳐지면 패스니까 그냥 큰 값

        # LONG 강제 청산
        if position.side == LONG:
            worst_roe = (low - position.price) / position.price * leverage

        # SHORT 강제 청산
        elif position.side == SHORT:
            worst_roe = (position.price - high) / position.price * leverage

        if worst_roe <= (MAINTENANCE_MARGIN_RATE * leverage) - 1:

            liq_price = 0
            if position.side == LONG:
                liq_price = position.price * (1 - (1 / leverage) + MAINTENANCE_MARGIN_RATE)
            elif position.side == SHORT:
                liq_price = position.price * (1 + (1 / leverage) - MAINTENANCE_MARGIN_RATE)

            # available_balance -= (position.used_margin * TAKER_FEE * leverage) 수수료 처리는 일단은 used_margin을 0으로 처리
            margin_balance = available_balance # 포지션 진입 금액은 그냥 0으로
            real_pnl = 0 - position.used_margin - position.open_fee

            # 기록
            now_history.action = "LIQUIDATION"
            now_history.side = position.side
            now_history.price = liq_price
            now_history.pnl = real_pnl

            is_position = False
            position.side = None
            position.price = None
            position.used_margin = None
            position.position_equity = None
            position.open_fee = None

            cancel_order()  # 걸려있던 익절/손절 주문도 다 취소

            View.liquid(timestamp, f"b : {margin_balance:.2f} (pnl: {real_pnl:.2f})")

    # 3 : 포지션 닫기 주문 처리
    if is_position and is_order and order.action == "CLOSE":
        is_executed = False

        if position.side == LONG and high >= order.price:
            is_executed = True

        elif position.side == SHORT and low <= order.price:
            is_executed = True

        # 체결 로직
        if is_executed:

            pnl_ratio = 0
            if position.side == LONG:
                pnl_ratio = (order.price - position.price) / position.price * leverage
            elif position.side == SHORT:
                pnl_ratio = (position.price - order.price) / position.price * leverage
            else:
                View.error(f"[__update] 잘못된 포지션 방향 감지 - {position.side}")
                exit(1)

            pnl = position.used_margin * pnl_ratio # 손익금
            close_fee = position.used_margin * leverage * MAKER_FEE # 수수료 계산

            available_balance = available_balance + position.used_margin + pnl - close_fee
            margin_balance = available_balance
            real_pnl = pnl - close_fee - position.open_fee

            # 기록
            now_history.action = "CLOSE"
            now_history.side = position.side
            now_history.price = order.price
            now_history.pnl = real_pnl

            is_position = False
            position.side = None
            position.price = None
            position.used_margin = None
            position.position_equity = None
            position.open_fee = None

            cancel_order()

            if real_pnl > 0:
                View.win(timestamp, f"b : {margin_balance:.2f} (pnl: {real_pnl:.2f})")
            else:
                View.loss(timestamp, f"b : {margin_balance:.2f} (pnl: {real_pnl:.2f})")

    # 4 : 수익률 처리
    if is_position:

        pnl_ratio = 0
        if position.side == LONG:
            pnl_ratio = (close - position.price) / position.price * leverage
        elif position.side == SHORT:
            pnl_ratio = (position.price - close) / position.price * leverage
        else:
            View.error(f"[__update] 잘못된 포지션 방향 감지 - {position.side}")
            exit(1)

        position_equity = position.used_margin + (position.used_margin * pnl_ratio)
        margin_balance = available_balance + position_equity

        position.position_equity = position_equity

    now_history.balance = margin_balance
    history_list.append(now_history)

# __update --끝--


@dataclass
class History:
    timestamp: datetime
    balance: float = 0.0 # 필수: 매분 기록되는 자산

    action: Optional[str] = None  # "OPEN", "CLOSE", "LIQUIDATION"
    side: Optional[str] = None  # "LONG", "SHORT"
    price: float = None  # 체결가
    pnl: float = None  # 실현 손익 (Realized PnL)



