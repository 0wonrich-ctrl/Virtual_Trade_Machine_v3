import finplot as fplt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from pandas.plotting import register_matplotlib_converters
from pyprojroot import here
from scipy.stats import linregress

from MY연구실 import 설정


#=======================================================================================================================

def warn(txt: str):
    print(f"\033[38;2;255;210;0m⚠️ {txt}\033[0m")

def error(txt: str):
    print(f"\033[38;2;255;20;20m❌ {txt}\033[0m")

def long(time:str, txt: str):
    print(f"\033[38;2;220;255;220m[{time}] 롱진입 - {txt}\033[0m")

def short(time:str, txt: str):
    print(f"\033[38;2;255;220;220m[{time}] 숏진입 - {txt}\033[0m")

def win(time:str, txt: str):
    print(f"\033[38;2;255;255;220m[{time}] 익ㅡ절 - {txt}\033[0m")

def loss(time:str, txt: str):
    print(f"\033[38;2;220;220;255m[{time}] 손ㅡ절 - {txt}\033[0m")

def liquid(time:str, txt: str):
    print(f"\033[38;2;255;100;100m[{time}] 청ㅡ산 - {txt}\033[0m")

#=======================================================================================================================
# 한글 폰트 설정
register_matplotlib_converters()
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'Malgun Gothic' # 한글 폰트 (Windows 기준)
plt.rcParams['axes.unicode_minus'] = False   # 마이너스 부호 깨짐 방지

#=======================================================================================================================

result_path = here() / "MY연구실" / "결과"

def final_result(full_df, coin_name, leverage, initial_balance):

    trade_df = __trans_full_to_trade(full_df)

    b_1_f, b_1_t = __save_df_to_csv(full_df, trade_df, coin_name)
    b_2 = __make_analyze_img(trade_df,coin_name)
    b_3 = __analyze_report(full_df,coin_name, leverage, initial_balance) # 시작 관리자에서 종합보고서를 기준으로 [3]실행하므로 이 코드 마지막 실행

    print(f"전체기록 저장: {"✔" if b_1_f else "✖"} / 매매기록 저장: {"✔" if b_1_t else "✖"} / 분석 이미지 저장: {"✔" if b_2 else "✖"} / 보고서 추가: {"✔" if b_3 else "✖"}")
    if 설정.GRAPH_WINDOW:
        __view_chart(full_df, coin_name)

#=======================================================================================================================

def __trans_full_to_trade(full_df):
    trade_df = full_df.copy()

    if 'T_action' in trade_df.columns:
        trade_df = trade_df[trade_df['T_action'].notna()]
    else:
        trade_df = pd.DataFrame()
    return trade_df


def __save_df_to_csv(full_df, trade_df, coin_name):
    # 전체 기록
    return_1 = True
    if 설정.MAKE_FULL_CSV:
        try:
            full_path = result_path / "전체기록"
            full_path.mkdir(parents=True, exist_ok=True)
            full_df.to_csv(f"{full_path}/{coin_name}_full.csv", index=False, encoding='utf-8-sig')

        except Exception as e:
            error(f"{coin_name}_full.csv 저장 실패: {e}")
            return_1 = False
    else:
        return_1 = False

    # 매매 기록
    return_2 = True
    trade_path = result_path / "매매기록"
    trade_path.mkdir(parents=True, exist_ok=True)
    try:
        trade_df.to_csv(f"{trade_path}/{coin_name}_trade.csv", index=False, encoding='utf-8-sig')

    except Exception as e:
        error(f"{coin_name}_trade.csv 저장 실패: {e}")
        return_2 = False

    return return_1, return_2


def __make_analyze_img(trade_df: pd.DataFrame, coin_name: str):
    path = result_path / "분석이미지"
    path.mkdir(parents=True, exist_ok=True)
    save_file = path / f"{coin_name}_analysis.png"

    if save_file.exists():
        save_file.unlink()

    # =========================================================
    # 1. 데이터 전처리
    # =========================================================
    df = trade_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 롱/숏 한글화
    df['T_side'] = df['T_side'].replace({'LONG': '롱 (Long)', 'SHORT': '숏 (Short)'})

    # 완료된 거래 추출
    closed_trades = df[df['T_pnl'].notna()].copy()

    if closed_trades.empty:
        return False

    # 보유 시간(분) 계산 (약식)
    durations = []
    last_open_time = {'롱 (Long)': None, '숏 (Short)': None}

    df_sorted = df.sort_values('timestamp')
    for _, row in df_sorted.iterrows():
        action = row['T_action']
        side = row['T_side']
        ts = row['timestamp']

        if action == 'OPEN':
            last_open_time[side] = ts
        elif action in ['CLOSE', 'LIQUIDATION']:
            if last_open_time[side] is not None:
                diff = (ts - last_open_time[side]).total_seconds() / 60
                durations.append(diff)
                last_open_time[side] = None
            else:
                durations.append(0)

    if len(durations) == len(closed_trades):
        closed_trades['duration_min'] = durations
    else:
        closed_trades['duration_min'] = 0

    # 요일/시간 정보 생성 (한글 요일)
    weekday_map = {
        'Monday': '월', 'Tuesday': '화', 'Wednesday': '수',
        'Thursday': '목', 'Friday': '금', 'Saturday': '토', 'Sunday': '일'
    }
    closed_trades['weekday'] = closed_trades['timestamp'].dt.day_name().map(weekday_map)
    closed_trades['hour'] = closed_trades['timestamp'].dt.hour

    # 요일 정렬 순서
    days_order = ['월', '화', '수', '목', '금', '토', '일']

    # =========================================================
    # 2. 캔버스 설정
    # =========================================================
    sns.set_theme(style="whitegrid", font=plt.rcParams['font.family'])  # 시본에도 폰트 적용

    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle(f'{coin_name} 전략 성과 분석 보고서', fontsize=26, fontweight='bold')

    # 색상 팔레트 (롱: 초록, 숏: 빨강)
    palette_colors = {'롱 (Long)': '#00E676', '숏 (Short)': '#FF1744'}

    # ---------------------------------------------------------
    # [1] 수익금 분포 (히스토그램)
    # ---------------------------------------------------------
    ax1 = axes[0, 0]

    # 1. KDE(곡선) 그리기 조건 체크
    # 데이터가 2개 이상이어야 하고, 모든 값이 똑같지 않아야(분산>0) 곡선을 그릴 수 있음
    data_count = len(closed_trades)
    unique_pnl_count = closed_trades['T_pnl'].nunique()

    # 조건: 데이터가 2개 이상 AND 값이 한 가지로 통일되지 않음
    can_draw_kde = (data_count > 1) and (unique_pnl_count > 1)

    # 2. 팔레트 안전하게 가져오기 (데이터에 있는 포지션만)
    unique_sides = closed_trades['T_side'].unique()
    safe_palette = {k: v for k, v in palette_colors.items() if k in unique_sides}
    if not safe_palette: safe_palette = None

    try:
        sns.histplot(
            data=closed_trades,
            x='T_pnl',
            kde=can_draw_kde,  # <--- 여기가 핵심 수정 (조건부 적용)
            hue='T_side',
            element="step",
            ax=ax1,
            palette=safe_palette
        )
    except Exception as e:
        # 혹시 모를 에러 발생 시 가장 단순한 형태로 그리기
        print(f"⚠️ 히스토그램 그리기 경고: {e} (단순 모드로 진행)")
        sns.histplot(data=closed_trades, x='T_pnl', kde=False, ax=ax1)

    ax1.axvline(0, color='black', linestyle='--', linewidth=0.5)
    ax1.set_title(f"수익금 분포 (총 {data_count}회 거래)", fontsize=18, fontweight='bold')
    ax1.set_xlabel("수익금 (USDT)", fontsize=14)
    ax1.set_ylabel("빈도 (횟수)", fontsize=14)

    if ax1.get_legend():
        ax1.get_legend().set_title("포지션")

    # ---------------------------------------------------------
    # [2] 요일별 수익 히트맵
    # ---------------------------------------------------------
    ax2 = axes[0, 1]
    weekly_pnl = closed_trades.pivot_table(index='T_side', columns='weekday', values='T_pnl', aggfunc='sum')
    weekly_pnl = weekly_pnl.reindex(columns=days_order).fillna(0)

    sns.heatmap(weekly_pnl, annot=True, fmt=".1f", cmap="RdYlGn", center=0, linewidths=1, ax=ax2,
                cbar_kws={'label': '총 수익금'})
    ax2.set_title("요일별 손익 히트맵", fontsize=18, fontweight='bold')
    ax2.set_xlabel("요일", fontsize=14)
    ax2.set_ylabel("포지션", fontsize=14)

    # ---------------------------------------------------------
    # [3] 시간별 수익 히트맵
    # ---------------------------------------------------------
    ax3 = axes[1, 0]
    hourly_pnl = closed_trades.pivot_table(index='T_side', columns='hour', values='T_pnl', aggfunc='sum')
    hourly_pnl = hourly_pnl.reindex(columns=range(24)).fillna(0)

    sns.heatmap(hourly_pnl, annot=False, cmap="RdYlGn", center=0, linewidths=1, ax=ax3, cbar_kws={'label': '총 수익금'})
    ax3.set_title("시간별 손익 히트맵 (0시 ~ 23시)", fontsize=18, fontweight='bold')
    ax3.set_xlabel("시간 (Hour)", fontsize=14)
    ax3.set_ylabel("포지션", fontsize=14)

    # [4] 보유 시간 vs 수익률 산점도
    ax4 = axes[1, 1]
    sns.scatterplot(
        data=closed_trades, x='duration_min', y='T_pnl', hue='T_side', style='T_side',
        palette=palette_colors, s=50, alpha=0.7, ax=ax4
    )
    ax4.axhline(0, color='black', linestyle='--', linewidth=1)
    ax4.set_title("보유 시간 vs 수익금 산점도", fontsize=18, fontweight='bold')
    ax4.set_xlabel("보유 시간 (분)", fontsize=14)
    ax4.set_ylabel("수익금 (USDT)", fontsize=14)
    # 범례 한글화
    ax4.legend(title='포지션')

    # 3. 구분선 추가 (검은 선)
    line_hor = Line2D([0.05, 0.95], [0.5, 0.5], transform=fig.transFigure, color="black", linewidth=3)
    line_ver = Line2D([0.5, 0.5], [0.05, 0.95], transform=fig.transFigure, color="black", linewidth=3)

    fig.add_artist(line_hor)
    fig.add_artist(line_ver)

    # 4. 저장
    plt.subplots_adjust(wspace=0.3, hspace=0.3, left=0.07, right=0.95, top=0.9, bottom=0.07)

    try:
        plt.savefig(save_file, dpi=300)  # 고해상도 저장
        plt.close(fig)  # 메모리 해제
    except Exception as e:
        error(f"{coin_name}_analysis.png 저장 실패: {e}")
        return False

    return True



def __view_chart(df: pd.DataFrame, coin_name: str):

    # ============================================================
    # 2. 데이터 준비
    # ============================================================
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # 로그 자산 생성
    if 'T_balance' in df.columns:
        df['T_balance'] = df['T_balance'].ffill()
        df['Balance_Log'] = np.log(df['T_balance'].apply(lambda x: max(x, 1)))

    # -------------------------------------------------------
    # 3. 컬럼 분류 (IO_ vs IS_)
    # -------------------------------------------------------
    overlay_cols = [c for c in df.columns if c.startswith('IO_')]
    sub_cols = [c for c in df.columns if c.startswith('IS_')]

    # -------------------------------------------------------
    # 4. 동적 레이아웃 계산
    # -------------------------------------------------------
    # 기본 행: [메인차트] + [거래량] + [자산Linear] + [자산Log] = 4개
    # 추가 행: IS_ 지표 개수만큼
    base_rows = 4
    total_rows = base_rows + len(sub_cols)

    # 높이 비율 설정 (메인 차트를 크게)
    # 1000이 메인, 나머지는 200 정도의 높이
    row_heights = [1000] + [200] * (total_rows - 1)

    # 플롯 생성
    ax_list = fplt.create_plot(
        f'{coin_name} Analysis (Auto-Layout)',
        rows=total_rows,
        maximize=False
    )

    # -------------------------------------------------------
    # 5. 차트 그리기
    # -------------------------------------------------------

    # [Row 0] 메인 캔들 차트
    ax_main = ax_list[0]
    candlesticks = df[['open', 'close', 'high', 'low']]
    fplt.candlestick_ochl(candlesticks, ax=ax_main)

    # [Row 0] Overlay 지표 그리기 (IO_)
    colors = ['#FFD700', '#00BFFF', '#FF00FF', '#FFFFFF', '#FFA500']
    for i, col in enumerate(overlay_cols):
        clean_name = col.replace('IO_', '')
        fplt.plot(df[col], ax=ax_main, legend=clean_name, width=1.5, color=colors[i % len(colors)])

    # [Row 1] 거래량
    ax_vol = ax_list[1]
    volumes = df[['open', 'close', 'volume']]
    fplt.volume_ocv(volumes, ax=ax_vol)

    # [Row 2 ~ N] Sub 지표 그리기 (IS_) - 칸을 하나씩 차지함
    # sub_cols 개수만큼 ax_list의 2번 인덱스부터 사용
    current_ax_idx = 2
    for i, col in enumerate(sub_cols):
        ax_sub = ax_list[current_ax_idx]
        clean_name = col.replace('IS_', '')

        # 지표 그리기
        fplt.plot(df[col], ax=ax_sub, legend=clean_name, color=colors[i % len(colors)])

        fplt.add_line((df.index[0], 100), (df.index[-1], 100), color='#888888', style='--', ax=ax_sub)
        fplt.add_line((df.index[0], 75), (df.index[-1], 75), color='#666666', style='--', ax=ax_sub)
        fplt.add_line((df.index[0], 50), (df.index[-1], 50), color='#888888', style='--', ax=ax_sub)
        fplt.add_line((df.index[0], 25), (df.index[-1], 25), color='#666666', style='--', ax=ax_sub)
        fplt.add_line((df.index[0], 0), (df.index[-1], 0), color='#888888', style='--', ax=ax_sub)


        current_ax_idx += 1

    # [Last Rows] 자산 차트 (항상 맨 밑에 위치하도록)
    ax_lin = ax_list[current_ax_idx]
    ax_log = ax_list[current_ax_idx + 1]

    if 'T_balance' in df.columns:
        fplt.plot(df['T_balance'], ax=ax_lin, color='#00E676', legend='Equity(Lin)')

    if 'Balance_Log' in df.columns:
        fplt.plot(df['Balance_Log'], ax=ax_log, color='#FFA500', legend='Equity(Log)')

    # -------------------------------------------------------
    # 6. 매매 마킹 (메인 차트)
    # -------------------------------------------------------
    # 체결가가 캔들 밖으로 튀어나가는 현상 방지 (Clip)
    df['mark_price_long'] = df[['T_price', 'high']].min(axis=1)  # 고가보다 높으면 고가에
    df['mark_price_short'] = df[['T_price', 'low']].max(axis=1)  # 저가보다 낮으면 저가에

    # Long Entry
    longs = df[(df['T_action'] == 'OPEN') & (df['T_side'] == 'LONG')]
    if not longs.empty:
        fplt.plot(longs['mark_price_long'], ax=ax_main, style='^', color='#00E676', width=2, legend='L-Entry',
                  zoom_scale=False)

    # Short Entry
    shorts = df[(df['T_action'] == 'OPEN') & (df['T_side'] == 'SHORT')]
    if not shorts.empty:
        fplt.plot(shorts['mark_price_short'], ax=ax_main, style='v', color='#FF1744', width=2, legend='S-Entry',
                  zoom_scale=False)

    # Exits
    exits = df[df['T_action'].isin(['CLOSE', 'LIQUIDATION'])]
    if not exits.empty:
        exit_prices = exits['T_price'].fillna(exits['close'])
        fplt.plot(exit_prices, ax=ax_main, style='x', color='#E040FB', width=3, legend='Exit', zoom_scale=False)

    fplt.show()


def __analyze_report(df: pd.DataFrame, coin_name, leverage, initial_balance):
    # ==========================================
    # 1. 데이터 전처리 및 자산(Equity) 계산
    # ==========================================
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    start_date = df['timestamp'].iloc[0]
    end_date = df['timestamp'].iloc[-1]
    days = (end_date - start_date).days
    if days == 0: days = 1

    # 자산 커브
    equity_curve = df['T_balance'].ffill().fillna(initial_balance)
    final_balance = equity_curve.iloc[-1]

    total_return_usdt = final_balance - initial_balance
    total_return_rate = (total_return_usdt / initial_balance) * 100

    peak_capital = equity_curve.max()
    low_capital = equity_curve.min()

    # MDD 계산
    roll_max = equity_curve.cummax()
    drawdown = (equity_curve - roll_max) / roll_max * 100
    mdd = drawdown.min()

    # K-Ratio 계산
    try:
        log_equity = np.log(equity_curve.apply(lambda x: max(x, 1)))
        x = np.arange(len(log_equity))
        slope, intercept, r_value, p_value, std_err = linregress(x, log_equity.values)

        if std_err == 0:
            k_ratio = 0.0
        else:
            k_ratio = (slope / std_err) / np.sqrt(len(log_equity))
    except:
        k_ratio = 0.0

    # ==========================================
    # 2. 매매 기록 추출 (Trade Stats)
    # ==========================================
    trades = []
    temp_open = None
    last_close_time = start_date

    # T_action이 있는 행만 추출
    action_df = df.dropna(subset=['T_action'])

    for idx, row in action_df.iterrows():
        action = row['T_action']
        if action == 'OPEN':
            temp_open = row
        elif action in ['CLOSE', 'LIQUIDATION']:
            if temp_open is not None:
                pnl = row['T_pnl']
                entry_price = temp_open['T_price']
                exit_price = row['T_price']
                side = temp_open['T_side']

                # ROI 계산
                if side == 'LONG':
                    pos_roi = (exit_price - entry_price) / entry_price * leverage * 100
                else:
                    pos_roi = (entry_price - exit_price) / entry_price * leverage * 100

                balance_before = row['T_balance'] - pnl
                bal_roi = (pnl / balance_before * 100) if balance_before > 0 else 0

                trades.append({
                    "side": side,
                    "result": "WIN" if pnl > 0 else "LOSE",
                    "pnl": pnl,
                    "pos_roi": pos_roi,
                    "bal_roi": bal_roi,
                    "duration": row['timestamp'] - temp_open['timestamp'],
                    "wait_time": temp_open['timestamp'] - last_close_time
                })
                last_close_time = row['timestamp']
                temp_open = None

    trades_df = pd.DataFrame(trades)

    # ==========================================
    # 3. 통계 계산 헬퍼 함수
    # ==========================================

    def get_stats_str(series, is_pct=True):
        if len(series) == 0:
            return f"{0:.4f}", f"{0:.4f} / {0:.4f}", f"{0:.4f} / {0:.4f} / {0:.4f}"

        unit = "%" if is_pct else ""
        q1, q2, q3 = series.quantile([0.25, 0.50, 0.75])
        return (
            f"{series.mean():+.4f} {unit}",
            f"{series.min():+.4f} {unit} / {series.max():+.4f} {unit}",
            f"{q1:+.4f} {unit} / {q2:+.4f} {unit} / {q3:+.4f} {unit}"
        )

    def analyze_time(series):
        if series.empty: return "0분", "0분 / 0분", "0분 / 0분 / 0분"

        def fmt(td):
            h, rem = divmod(int(td.total_seconds()), 3600)
            m, _ = divmod(rem, 60)
            return f"{h}시간 {m}분"

        q1, q2, q3 = series.quantile([0.25, 0.50, 0.75])
        return (
            fmt(pd.Timedelta(seconds=series.mean().total_seconds())),
            f"{fmt(series.min())} / {fmt(series.max())}",
            f"{fmt(q1)} / {fmt(q2)} / {fmt(q3)}"
        )

    # [수정됨] 롱/숏 개별 분석 헬퍼 (잔고 기준 ROI 추가)
    def analyze_side(side_df, total_cnt):
        if side_df.empty:
            dummy_stats = ("0%", "0% / 0%", "0% / 0% / 0%")
            return 0, 0.0, 0.0, 0.0, dummy_stats, dummy_stats

        count = len(side_df)
        win_rate = len(side_df[side_df['result'] == 'WIN']) / count * 100

        return (
            count,
            count / total_cnt * 100,  # ratio
            win_rate,
            side_df['pnl'].sum(),
            get_stats_str(side_df['pos_roi']),  # 포지션 기준 통계
            get_stats_str(side_df['bal_roi'])  # 잔고 기준 통계 (추가됨)
        )

    # ==========================================
    # 4. 통계 계산 실행
    # ==========================================
    if not trades_df.empty:
        total_trades = len(trades_df)
        win_count = len(trades_df[trades_df['result'] == 'WIN'])
        lose_count = len(trades_df[trades_df['result'] == 'LOSE'])
        win_rate = (win_count / total_trades) * 100

        pos_roi_stats = get_stats_str(trades_df['pos_roi'])
        bal_roi_stats = get_stats_str(trades_df['bal_roi'])

        dur_mean, dur_mm, dur_q = analyze_time(trades_df['duration'])
        wait_mean, wait_mm, wait_q = analyze_time(trades_df['wait_time'])

        # [수정] 리턴값이 6개로 늘어남
        l_cnt, l_ratio, l_wr, l_pnl, l_pos_stats, l_bal_stats = analyze_side(trades_df[trades_df['side'] == 'LONG'],
                                                                             total_trades)
        s_cnt, s_ratio, s_wr, s_pnl, s_pos_stats, s_bal_stats = analyze_side(trades_df[trades_df['side'] == 'SHORT'],
                                                                             total_trades)

    else:
        # 거래 없음 초기화
        total_trades, win_count, lose_count, win_rate = 0, 0, 0, 0.0
        pos_roi_stats = ("0", "0 / 0", "0 / 0 / 0")
        bal_roi_stats = ("0", "0 / 0", "0 / 0 / 0")
        dur_mean, dur_mm, dur_q = "0분", "0분 / 0분", "0분 / 0분 / 0분"
        wait_mean, wait_mm, wait_q = "0분", "0분 / 0분", "0분 / 0분 / 0분"

        dummy_stats = ("0", "0 / 0", "0 / 0 / 0")
        l_cnt, l_ratio, l_wr, l_pnl, l_pos_stats, l_bal_stats = 0, 0.0, 0.0, 0.0, dummy_stats, dummy_stats
        s_cnt, s_ratio, s_wr, s_pnl, s_pos_stats, s_bal_stats = 0, 0.0, 0.0, 0.0, dummy_stats, dummy_stats

    # ==========================================
    # 5. 일일 통계 및 코인 분석
    # ==========================================
    daily_agg = df.set_index('timestamp').resample('D').agg({
        'T_balance': ['last', 'max', 'min'],
        'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
    }).dropna()

    if not daily_agg.empty:
        bals = daily_agg['T_balance']['last'].ffill().fillna(initial_balance)
        daily_ret_mean, daily_ret_mm, daily_ret_q = get_stats_str(bals.pct_change().dropna() * 100)

        b_max = daily_agg['T_balance']['max'].fillna(initial_balance)
        b_min = daily_agg['T_balance']['min'].fillna(initial_balance)
        b_first = daily_agg['T_balance']['last'].shift(1).fillna(initial_balance)
        volat = (b_max - b_min) / b_first * 100
        daily_vol_mean, daily_vol_mm, daily_vol_q = get_stats_str(volat)
    else:
        daily_ret_mean, daily_ret_mm, daily_ret_q = 0, "0 / 0", "0 / 0 / 0"
        daily_vol_mean, daily_vol_mm, daily_vol_q = 0, "0 / 0", "0 / 0 / 0"

    coin_open = df['open'].iloc[0]
    coin_close = df['close'].iloc[-1]
    coin_change = (coin_close - coin_open) / coin_open * 100
    coin_min, coin_max = df['low'].min(), df['high'].max()

    c_dd = (df['close'] - df['close'].cummax()) / df['close'].cummax() * 100
    c_mdd = c_dd.min()

    daily_vol = daily_agg['volume']['sum'] if not daily_agg.empty else pd.Series([])
    daily_val = daily_vol * daily_agg['close']['last'] if not daily_agg.empty else pd.Series([])

    def get_vol_str(s):
        if s.empty: return "0", "0 / 0 / 0"
        q = s.quantile([0.25, 0.5, 0.75])
        return f"{s.mean():,.0f}", f"{q[0.25]:,.0f} / {q[0.5]:,.0f} / {q[0.75]:,.0f}"

    vol_mean, vol_q = get_vol_str(daily_vol)
    val_mean, val_q = get_vol_str(daily_val)

    # ==========================================
    # 6. 보고서 작성 및 저장
    # ==========================================
    line = "-" * 80
    double_line = "=" * 80

    report = f"""{double_line}
 {coin_name} 백테스팅 보고서
{line}
▶ 기간                : {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} ({days:,}일)
▶ 초기 자본            : {initial_balance:,.2f} USDT
▶ 레버러지             : {leverage}
{line}
▶ 최종 자본            : {final_balance:,.2f} USDT
▶ 총 수익률            : {total_return_rate:+.2f} % ( {total_return_usdt:+.2f} USDT )
▶ 최고 자본            : {peak_capital:,.2f} USDT
▶ 최저 자본            : {low_capital:,.2f} USDT
▶ MDD                 : {mdd:.2f} %
▶ K-Ratio (K-레이쇼)   : {k_ratio:.2f}
{line}
▶ 총 거래 수           : {total_trades} 회
▶ 승 / 패             : {win_count} / {lose_count}
▶ 승률                : {win_rate:.2f} %
▶ 한 거래당 수익률 (포지션 기준)
    - mean           : {pos_roi_stats[0]}
    - min / max      : {pos_roi_stats[1]}
    - Q1 / Q2 / Q3   : {pos_roi_stats[2]}
▶ 한 거래당 수익률 (잔고 기준)
    - mean           : {bal_roi_stats[0]}
    - min / max      : {bal_roi_stats[1]}
    - Q1 / Q2 / Q3   : {bal_roi_stats[2]}
▶ 일일 수익률 (잔고 기준)
    - mean           : {daily_ret_mean}
    - min / max      : {daily_ret_mm}
    - Q1 / Q2 / Q3   : {daily_ret_q}
▶ 일일 변동성 (잔고 기준)
    - mean           : {daily_vol_mean}
    - min / max      : {daily_vol_mm}
    - Q1 / Q2 / Q3   : {daily_vol_q}
{line}
[LONG]
▶ 거래 수            : {l_cnt} 회 ({l_ratio:.1f} %)
▶ 승률               : {l_wr:.2f} %
▶ 누적 수익           : {l_pnl:,.2f} USDT
▶ ROI (포지션 기준)
    - mean           : {l_pos_stats[0]}
    - min / max      : {l_pos_stats[1]}
    - Q1 / Q2 / Q3   : {l_pos_stats[2]}
▶ ROI (잔고 기준)
    - mean           : {l_bal_stats[0]}
    - min / max      : {l_bal_stats[1]}
    - Q1 / Q2 / Q3   : {l_bal_stats[2]}
{line}
[SHORT]
▶ 거래 수            : {s_cnt} 회 ({s_ratio:.1f} %)
▶ 승률               : {s_wr:.2f} %
▶ 누적 수익           : {s_pnl:,.2f} USDT
▶ ROI (포지션 기준)
    - mean           : {s_pos_stats[0]}
    - min / max      : {s_pos_stats[1]}
    - Q1 / Q2 / Q3   : {s_pos_stats[2]}
▶ ROI (잔고 기준)
    - mean           : {s_bal_stats[0]}
    - min / max      : {s_bal_stats[1]}
    - Q1 / Q2 / Q3   : {s_bal_stats[2]}
{line}
▶ 포지션 유지 시간
    - mean           : {dur_mean}
    - min / max      : {dur_mm}
    - Q1 / Q2 / Q3   : {dur_q}
▶ 포지션 진입 대기 시간
    - mean           : {wait_mean}
    - min / max      : {wait_mm}
    - Q1 / Q2 / Q3   : {wait_q}
{line}
▶ {coin_name.replace('USDT', '')} 가격 변화
   - 상승률            : {coin_change:+.2f} % ( {coin_open:,.2f} → {coin_close:,.2f} USDT )
   - min / max        : {coin_min:,.2f} / {coin_max:,.2f} USDT
   - MDD              : {c_mdd:.2f} %
▶ {coin_name.replace('USDT', '')} 일 거래량
   - Mean             : {vol_mean}
   - Q1 / Q2 / Q3     : {vol_q}
▶ {coin_name.replace('USDT', '')} 일 거래대금 (USDT)
   - Mean             : {val_mean}
   - Q1 / Q2 / Q3     : {val_q}
{double_line}"""

    # 파일 저장
    txt_path = here() / "MY연구실" / "결과" / "종합보고서.txt"
    txt_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(txt_path, 'a', encoding='utf-8') as f:
            f.write(f"{report}\n\n")
            print("")
            print(report)
            return True
    except Exception as e:
        print(f"❌ 보고서 저장 실패: {e}")
        return False