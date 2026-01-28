from MY연구실 import 설정
from src.VTM3 import View


def vld_run():
    # 최근 며칠 : int(0 ~ 양수) or None
    if 설정.RECENT_DAY is not None:
        if not isinstance(설정.RECENT_DAY, int):
            View.error("RECENT_DAY 설정 오류: 정수(int) 또는 None 값만 허용됩니다.")
            exit(1)
        if 설정.RECENT_DAY < 0:
            View.error("RECENT_DAY 설정 오류: 0 이상의 값만 사용할 수 있습니다.")
            exit(1)

    # 그래프 윈도우 생성 여부 : Bool
    if not isinstance(설정.GRAPH_WINDOW, bool):
        View.error("GRAPH_WINDOW 설정 오류: True 또는 False 값만 허용됩니다.")
        exit(1)

    # 백테스팅 완료 시 소리 발생 여부 : Bool
    if not isinstance(설정.FINISH_SOUND, bool):
        View.error("FINISH_SOUND 설정 오류: True 또는 False 값만 허용됩니다.")
        exit(1)

    # 첫 시드 대비 잔고 감소 비율 (계좌 청산 기준) : float(0 ~ 1 미만)
    if not isinstance(설정.ACCOUNT_BLOWN, (float, int)):
        View.error(
            "ACCOUNT_BLOWN 설정 오류: 0 이상 1 미만의 실수(float) 값을 입력해야 합니다."
        )
        exit(1)

    if not (0 <= 설정.ACCOUNT_BLOWN < 1):
        View.error("ACCOUNT_BLOWN 설정 오류: 값은 0 이상 1 미만이어야 합니다. ")
        exit(1)

    '''
    if not isinstance(설정.MAKE_FULL_CSV, bool):
        View.error("MAKE_FULL_CSV 설정 오류: True 또는 False 값만 허용됩니다.")
        exit(1)
    '''

