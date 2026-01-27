# 최근 며칠 (365 넣으면 최근 1년, {None or 0 or 엄청 큰 숫자} 넣으면 그냥 전체 기간)
RECENT_DAY:int = 0

# 차트 윈도우 생성 여부 (False: 미생성, True: 생성)
GRAPH_WINDOW:bool = True

# 백테스팅 완료 시 소리 발생 여부 (False: 무음, True: 소리)
FINISH_SOUND:bool = True

# 첫 시드 대비 몇퍼센트까지 잔고가 줄어들면 계좌 청산이라 판단하고 백테스팅 종료할 지 (0 ~ 0.99)
ACCOUNT_BLOWN:float = 0.1

# 결과 / 전체기록 / full.csv파일 생성 여부 (False: 미생성, True: 생성) !!!큰 데이터라 보통은 False를 추천
MAKE_FULL_CSV = False