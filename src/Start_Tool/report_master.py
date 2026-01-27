import re
import shutil
import time
import winsound
from pyprojroot import here

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
    # 1. txt 파일 초기화
    txt_path = here() / "MY연구실" / "결과" / "종합보고서.txt"
    txt_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(txt_path, 'w', encoding='utf-8') as f:
            print("[1] ✅ 종합보고서.txt 초기화 완료")

    except Exception as e:
        print(f"[1] ❌ 종합보고서.txt 초기화 실패 : {e}")
        exit(1)

    # 정렬 목표 순서
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

    #
    if not 설정.MAKE_FULL_CSV:
        path = here() / "MY연구실" / "결과" / "전체기록"
        path.mkdir(parents=True, exist_ok=True)
        for item in path.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()  # 파일 삭제
                elif item.is_dir():
                    shutil.rmtree(item)  # 하위 폴더 삭제
            except Exception as e:
                print(f"[3] ❌ 전체기록 삭제 실패 ({item.name}): {e}")

    stop_loading()
    if 설정.FINISH_SOUND:
        winsound.Beep(500, 500)
        winsound.Beep(500, 500)
