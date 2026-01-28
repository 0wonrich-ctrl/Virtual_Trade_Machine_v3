# Virtual_Trade_Machine 가상 거래 머신
###### by 아그라드라

이 프로젝트는 내장된 여러 툴을 이용해서 복잡한 거래소 연동 없이 과거 데이터를 이용해 **가상 환경**에서 코인 선물 매매 전략을 시뮬레이션하고, 그 결과를 정밀하게 분석해줍니다.

1.  **백테스팅**: 바이비트 거래소와 유사한 주문 체결/청산/손절 시뮬레이션
2.  **데이터 시각화**: 수익금 분포, 요일/시간별 손익 히트맵, 거래 내역 차트 생성
3.  **상세 리포트**: MDD, K-Ratio, 승률, 포지션별 성과 등 20여 가지 핵심 지표 자동 산출

---
## 📁 프로젝트 구조
```yaml
프로젝트
├─📂 data    # 백테스팅용 코인 데이터 저장소
├─📂 MY연구실    # 사용자가 전략을 실험하고 분석하는 공간
│  ├─📂 결과    # 백테스팅 후 분석,가공된 여러 결과가 저장되는 폴더
│  │  ├─📂 매매기록    # 매매 기록(.csv) 저장 폴더 
│  │  ├─📂 분석이미지    # 시각화 그래프 이미지(.png) 저장 폴더 
│  │  ├─📂 전체기록    # 모든 분봉,매매,인디케이터 기록 (.csv) 저장 폴더
│  │  └─📄 종합보고서.txt    # 모든 코인들 결과 정리 보고서
│  ├─📂 시작    # 사용자가 백테스팅을 시작할 때 실행할 py들
│  ├─📄 데이터.py    # 데이터 다운로드 및 유효성 검증
│  ├─📄 설정.py    # 백테스팅 사용 편의성 관련 환경설정
│  └─📄 전략.py    # 사용자가 매매 전략을 작성하는 py
├─📂 src
├─📄 .gitignore
├─📄 README.md
└─📄 requirements.txt
```
---

## ⚙️ 환경 설정
1. **Python 3.13** 을 사용해야 합니다.
2. 패키지 충돌을 방지하기 위해 가상환경(.venv)을 사용하는 것을 권장합니다.
3. `pip install -r requirements.txt` 명령어를 사용하여 requirements.txt에 명시된 라이브러리들을 한 번에 설치합니다.
4. `MY연구실/데이터.py`를 실행하고 방향키를 눌러 원하는 작업을 수행합니다. (⬅️: 데이터 다운로드, ➡️: 데이터 유효성 검증)
5. `MY연구실/설정.py` 내에서 원하는 백테스팅 편의성 관련 원하는 설정값을 수정합니다. (백테스팅 결과엔 영향을 미치지 않음)

---
## 🧩 매매 전략 작성
### 1️⃣ `전략.py` 작성법

매매 전략은 `MY연구실/전략.py`에 작성합니다. 아래 코드는 `전략.py`의 가장 기초적인 뼈대 작성 예시입니다.

```python
from src import VirtualTradeMachine as vtm

ema_data = []
rsi_data = []

def ema(data):
    # ema를 계산해서 반환해주는 코드...
    vtm.register_indicator(name="EMA", value=ema_value)
    return ema_value

def rsi(data):
    # rsi를 계산해서 반환해주는 코드...
    vtm.register_indicator(name="rsi", value=rsi_value, sub_chart=True)
    return rsi_value

def strategy():
    vtm.setup(bal=1000, lev=10)
    
    while True:
        vtm.next_time()
        
        now_data = vtm.now_info()
        
        ema_value = ema(now_data)
        rsi_value = rsi(now_data)
        
        if not now_data['is_position']:
            if now_data['is_order']:
                vtm.cancel_order()
        
            if (원하는 롱 진입 조건):
                vtm.open_order(side = vtm.LONG, price = 123, betting_rate = 0.123)
                
            elif (원하는 숏 진입 조건):
                vtm.open_order(side = vtm.SHORT, price = 123, betting_rate = 0.123)
                
        else:
            if (원하는 롱 종료 조건):
                vtm.close_order(price = 123)
                
            elif (원하는 숏 종료 조건):
                vtm.close_order(price = 123)
```
**⚠️ `전략.py` 작성 시 주의할 점**
+ 반드시 `from src import VirtualTradeMachine as vtm`로 임포트 합니다.
+ 매매 전략은 반드시 `def strategy():` 내에 작성합니다.
+ `VirtualTradeMachine`은 Event-Driven 방식으로 작동하도록 설계되었습니다.
+ 무한 반복문 첫 코드로 `vtm.next_time()`을 실행하여 다음 1분봉으로 넘어갑니다.
+ `VirtualTradeMachine`이 내부적으로 계좌 청산 및 데이터 소진 시 자동 종료시키기에 사용자가 따로 무한 반복문 내에 정지코드를 추가하지 않아도 됩니다.
+ 본 엔진은 단방향(One-way) 모드만 지원하므로 동시에 2개 이상의 포지션이나 주문을 가질 수 없습니다. (1 포지션 / 1 주문 원칙)
+ `vtm.now_info()`는 현 시점 데이터만 반환합니다. 과거 데이터가 필요한 지표 계산 시, 사용자가 직접 가격 데이터를 누적/관리해야 합니다.

### 2️⃣ `VirtualTradeMachine` 상세 설명
VirtualTradeMachine은 백테스팅을 총괄하는 핵심 엔진입니다. 1분봉 데이터를 이용 및 제공하며 전략 작성 시 vtm 객체를 통해 데이터를 조회하고 주문을 실행합니다.

|                          메소드                           | 파라미터                                                                                                                                                                               | 반환값                                                                                            | 설명                                                        |
|:------------------------------------------------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------|:----------------------------------------------------------|
|                 `vtm.setup(bal, lev)`                  | • **bal (float) :** 초기 자본금 (USDT) <br/>• **lev (int) :** 레버리지 배율                                                                                                                   | 없음                                                                                             | 백테스팅 초기 설정값을 세팅합니다. `def strategy():`내 처음 딱 한번만 실행해야 합니다. |
|                   `vtm.next_time()`                    | 없음                                                                                                                                                                                 | 없음                                                                                             | 시뮬레이션 시간을 다음 캔들(1분봉)로 이동시킵니다.                             |
|                    `vtm.now_info()`                    | 없음                                                                                                                                                                                 | *아래 별도로 상세히 설명*                                                                                | 현재 시점의 시장 데이터와 내 계좌 상태를 딕셔너리(dict) 형태로 반환합니다.             |
|      `vtm.open_order(side, price, betting_rate)`       | • **side :** 포지션 방향 (vtm.LONG 또는 vtm.SHORT)<br/>• **price (float) :** 진입 희망 가격<br/>• **betting_rate (float) :** 현재 잔고 대비 베팅 비율 (0.0 ~ 0.8)                                         | • **True (bool) :** 주문 성공 시<br/>• **False (bool) :** 주문 실패 시 (베팅 비율이 제한값을 넘어가거나 이미 포지션이 있는 경우) | 신규 포지션 진입 주문을 넣습니다. 이미 진입 주문이 있는 경우 새 주문으로 덮어쓰기 합니다.      |
|                `vtm.close_order(price)`                | • **price (float) :** 종료 희망 가격                                                                                                                                                     | • **True (bool) :** 주문 성공 시<br/>• **False (bool) :** 주문 실패 시 (현재 포지션이 없는 경우)                   | 보유 중인 포지션 종료 주문을 넣습니다. 이미 종료 주문이 있는 경우 새 주문으로 덮어쓰기 합니다.   |
|                  `vtm.cancel_order()`                  | 없음                                                                                                                                                                                 | 없음                                                                                             | 아직 체결되지 않은 대기 주문을 취소합니다.                                  |
| `vtm.register_indicator(name, value, sub_chart=False)` | • **name (str) :** 지표 이름<br/>• **value (float) :** 현재 시점의 지표 값<br/>• **sub_chart (bool) :** 차트 그리는 방식[False (기본값): 오버레이 지표 (예: 이동평균선, 볼린저밴드) , True: 서브윈도우 지표 (예: RSI, MACD, 모멘텀)] | 없음                                                                                             | 백테스팅 결과 분석 차트에서 보조지표를 함께 그리고 싶을 때 사용합니다.                  |

**📊 `vtm.now_info()` 반환 데이터 구조**

`now_info()`는 **현재 시점의 시장 데이터**와 **계좌 상태**를 딕셔너리(dict) 형태로 반환합니다. 
아래는 반환값의 키(Key)와 예시값이며, 주석을 통해 각 항목을 설명합니다.

```python
"timestamp" : datetime객체    # 현 시간 (예: 2024-01-01 09:00:00)
"open": 42000.52    # 시가
"high": 42100.01    # 고가
"low": 41950.02    # 저가
"close": 42050.02    # 종가 (현재가)
"volume": 120.5    # 거래량

"margin_balance" : 1050.0    # 현재 총 자산 평가액 (지갑 잔고 + 미실현 손익)
"available_balance" : 800.0    # 미실현 손익을 제외한 지갑 잔고

"is_position" : True    # 포지션 보유 여부 (True/False)
"position" : {    # 포지션 상세 정보 (없으면 전부 None)
    "side" : vtm.LONG    # 포지션 방향 (vtm.LONG/vtm.SHORT)
    "price": 41500.0    # 포지션 진입 가격
    "used_margin": 200.0    # 사용된 증거금
    "position_equity": 250.0     # 현재 포지션 평가 가치
    "open_fee": 1.5    # 진입 시 지불한 수수료
},

"is_order": True    # 미체결 대기 주문 존재 여부 (True/False)
"order": {    # 주문 상세 정보 (없으면 전부 None)
    "action": "CLOSE"    # 주문 종류 ("OPEN": 진입, "CLOSE": 청산)
    "side": None    # 주문 방향 (주문 종류가 CLOSE인 경우 None, OPEN인 경우 vtm.LONG/vtm.SHORT)
    "price": 43000.0    # 주문 가격 (주문 종류가 OPEN인 경우 진입 희망가, CLOSE인 경우 청산 희망가)
    "betting_rate": None    # 자본 투입 비율 (주문 종류가 CLOSE인 경우 None, OPEN인 경우 0.0 ~ 0.8)
}
```
---
## 🚀 백테스팅 실행 및 결과 분석
### 1️⃣ 백테스팅 실행
1. `MY연구실/시작` 폴더에 내 모든 py를 `Ctrl + Shift + F10`으로 실행시킵니다.
2. 파이참 상단 실행 구성에서 새 복합을 생성한 후 `MY연구실/시작`내 모든 실행 구성을 모아줍니다.
3. 앞으로 복합 실행만 하면 자동으로 여러 코인별로 `전략.py`를 실행해 줍니다.

### 2️⃣ 결과 확인
모든 코인 별 결과물은 `MY연구실/결과` 폴더 내에 자동으로 저장됩니다.
+ **📄종합보고서.txt :** 모든 코인 별 결과 분석 데이터가 텍스트로 깔끔하게 정리됩니다.
+ **📂분석 이미지/ :** 데이터를 시각화하여 전략의 성격을 한눈에 파악할 수 있는 그래프가 .png 형태로 저장됩니다
+ **📂전체 기록/ :** 모든 코인 정보,매매 내역이 .csv 파일로 저장됩니다.
+ **📂매매 기록/ :** 전체 기록 데이터 중 매매한 시점의 데이터만 필터링되어 .csv 파일로 저장됩니다.