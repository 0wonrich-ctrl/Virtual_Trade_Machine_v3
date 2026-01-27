import tkinter as tk
import threading

# --- 설정값 ---
SIZE = 4  # 점 크기 (지름)
COLOR = '#00FF00'  # 형광 초록
BLINK_SPEED = 500  # 깜빡임 속도 (ms) - 0.5초마다 켜짐/꺼짐
X_POS = 5  # 좌측 여백
Y_POS = 5  # 상단 여백

# --- 전역 변수 ---
_root = None
_stop_flag = False
_thread = None


def _blink(canvas, dot_id, is_visible):
    """점을 껐다 켰다 하는 함수"""
    global _root, _stop_flag

    # 1. 종료 신호 확인
    if _stop_flag:
        if _root:
            try:
                _root.quit()
                _root.destroy()
            except:
                pass
            _root = None
        return

    try:
        # 2. 깜빡임 처리
        if is_visible:
            # 점 숨기기 (색을 투명 배경색과 똑같이 바꿈)
            canvas.itemconfig(dot_id, fill='#000001', outline='#000001')
        else:
            # 점 보이기
            canvas.itemconfig(dot_id, fill=COLOR, outline=COLOR)

        # 3. 다음 프레임 예약
        _root.after(BLINK_SPEED, _blink, canvas, dot_id, not is_visible)

    except Exception:
        pass


def _create_window():
    global _root
    _root = tk.Tk()

    # 윈도우 설정 (투명, 항상 위)
    _root.overrideredirect(True)
    _root.attributes('-topmost', True)

    # 투명 배경 설정 트릭 (#000001 사용)
    bg_color = '#000001'
    _root.config(bg=bg_color)
    _root.attributes('-transparentcolor', bg_color)

    # [위치 변경] 좌측 상단 (X_POS, Y_POS)
    _root.geometry(f"{SIZE}x{SIZE}+{X_POS}+{Y_POS}")

    # 캔버스 생성
    canvas = tk.Canvas(_root, width=SIZE, height=SIZE,
                       bg=bg_color, highlightthickness=0)
    canvas.pack()

    # 원(점) 그리기 (초기 상태)
    # create_oval(x1, y1, x2, y2)
    dot_id = canvas.create_oval(0, 0, SIZE, SIZE, fill=COLOR, outline=COLOR)

    # 깜빡임 시작
    _blink(canvas, dot_id, False)
    _root.mainloop()


# --- 사용자 함수 ---
def start_loading():
    global _thread, _stop_flag, _root
    if _root is not None: return
    _stop_flag = False
    _thread = threading.Thread(target=_create_window)
    _thread.daemon = True
    _thread.start()


def stop_loading():
    global _stop_flag
    _stop_flag = True