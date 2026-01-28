import shutil
import winsound
from pyprojroot import here
import re
import time
from MY연구실 import 설정
from src.Start_Tool.win_loading_tool import start_loading, stop_loading

moon_idx = 0
def get_moon():
    global moon_idx
    moon_list = ["🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌑"]
    char = moon_list[moon_idx % len(moon_list)]
    moon_idx += 1
    return char

def rep_run():
    start_loading()

    # 1. 모든 결과 파일, 폴더 초기화
    result_path = here() / "MY연구실" / "결과"
    txt_path = result_path / "종합보고서.txt"
    txt_path.parent.mkdir(parents=True, exist_ok=True)

    img_path = result_path / "분석이미지"
    full_path = result_path / "전체기록"
    trade_path = result_path / "매매기록"

    try:
        if img_path.exists():
            shutil.rmtree(img_path)
            img_path.mkdir(parents=True, exist_ok=True)

        if full_path.exists():
            shutil.rmtree(full_path)
            #if 설정.MAKE_FULL_CSV:
            #    full_path.mkdir(parents=True, exist_ok=True)

        if trade_path.exists():
            shutil.rmtree(trade_path)
            # trade_path.mkdir(parents=True, exist_ok=True)

        with open(txt_path, 'w', encoding='utf-8') as f:
            print("[1] ✅ 결과 폴더 초기화 완료")

    except Exception as e:
        print(f"[1] ❌ 결과 폴더 초기화 실패 : {e}")
        exit(1)


    # 2. 종합보고서 내용 정렬
    TARGET_ORDER = ['BTC', 'ETH', 'XRP', 'BNB', 'SOL', 'DOGE']

    while True:
        try:

            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()

            pattern = r'(={30,}\n\s+([A-Z]+)USDT 백테스팅 보고서\n.*?={30,})'

            matches = re.findall(pattern, content, re.DOTALL)
            current_count = len(matches)

            # 아직 6개가 다 안 모였으면 대기 (로딩 효과)
            if current_count < len(TARGET_ORDER):
                print(f"\r[2] {get_moon()} 리포트 수집 중... ({current_count}/{len(TARGET_ORDER)})", end='', flush=True)
                time.sleep(0.3)  # 2초 대기
                continue

            elif current_count >= len(TARGET_ORDER):
                print(f"\r[2] 📝 리포트 정렬 중... ({current_count}/{len(TARGET_ORDER)})", end='', flush=True)

                # 1. 딕셔너리로 변환 { 'BTC': '...본문...', 'ETH': '...본문...' }
                report_dict = {}
                for full_block, coin_name in matches:
                    report_dict[coin_name.strip()] = full_block

                # 2. 순서대로 재조립
                sorted_content = ""
                missing_coins = []

                for coin in TARGET_ORDER:
                    if coin in report_dict:
                        sorted_content += report_dict[coin] + "\n\n"  # 블록 사이 공백 추가
                    else:
                        missing_coins.append(coin)

                # 3. 파일 덮어쓰기
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(sorted_content.strip())

                if missing_coins:
                    print(f"⚠️ 경고: 일부 코인({missing_coins})이 누락되었습니다.")

                print(f"\r[2] ✅ 종합보고서.txt 정렬 완료")
                break

        except Exception as e:
            print(f"\r[2] ❌ 리포트 정렬 중 오류 발생: {e}")
            break

    # 3. 폴더 내용 갯수 출력
    full_n = 0
    full_b = True

    img_n = len([f for f in img_path.iterdir() if f.is_file()])
    img_b = True if img_n == 6 else False

    """
    trade_n = len([f for f in trade_path.iterdir() if f.is_file()])
    trade_b = True if trade_n == 6 else False

    if 설정.MAKE_FULL_CSV:
        full_n = len([f for f in full_path.iterdir() if f.is_file()])
        full_b = True if full_n == 6 else False

    if img_b and trade_b and full_b:
        print(f"[3] ✅ 결과 자료 개수 정상 ( 분석이미지:{img_n} / 매매기록:{trade_n} {f"/ 전체기록: {full_n}" if 설정.MAKE_FULL_CSV else ""})")
    else:
        print(f"[3] ❌ 결과 자료 개수 비정상 ( 분석이미지:{img_n} / 매매기록:{trade_n} {f"/ 전체기록: {full_n}" if 설정.MAKE_FULL_CSV else ""})")

    """

    if img_b:
        print(f"[3] ✅ 결과 자료 개수 정상 ( 분석이미지:{img_n} )")
    else:
        print(f"[3] ❌ 결과 자료 개수 비정상 ( 분석이미지:{img_n} )")

    stop_loading()
    if 설정.FINISH_SOUND:
        winsound.Beep(500, 500)
        winsound.Beep(500, 500)