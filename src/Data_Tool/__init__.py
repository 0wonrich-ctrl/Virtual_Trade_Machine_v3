import keyboard
from src.Data_Tool.data_check import check
from src.Data_Tool.data_download import make_data

def run():
    print("⌨️ 방향키를 누르세요: [◀] 데이터 다운로드 | 데이터 유효성 검증 [▶]", end="", flush=True)

    while True:
        key = keyboard.read_key()
        if key == 'left':
            print("\r⌨️ [◀] 데이터 다운로드 시작")
            make_data()
            exit(0)

        elif key == 'right':
            print("\r⌨️ [▶] 데이터 유효성 검증 시작")
            check()
            exit(0)
