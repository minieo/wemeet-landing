# 위밋 랜딩페이지 (minieo/wemeet-landing)

- 실제 운영 사이트: https://minieo.github.io/wemeet-landing/ — `main` 브랜치에 푸시하면 1~2분 안에 바로 반영돼요. 인스타 프로필 링크에 걸려 있으니 `main`에 올리기 전에 폰 화면(390px)으로 렌더링해서 확인할 것.
- 후기 사진은 `images/review-XX.jpg`로 분리돼 있어요. 새 사진은 세로 1260px 이하, JPEG 품질 80으로 줄여서 넣고, 캐러셀 앞 2장을 뺀 나머지엔 `loading="lazy"`를 붙일 것. HTML 안에 base64로 넣지 말 것.

## 매주 연령대 라인업 교체

> **2026-10부터 랜딩페이지에는 연령대 라인업을 싣지 않아요.** 랜딩은 "가능한 일정 신청 → 잘 맞는 자리 생기면 연락" 방식이에요. 아래 절차는 인스타용 `lineup/lineup.jpg`를 만들 때만 쓰고, `update_lineup.py`는 이미지만 만들고 index.html은 건드리지 않아요. index.html에 라인업 섹션을 다시 넣지 말 것.

승민이 이번 주 시간대별 연령대(예: "토 2시 여 95~99 남 93~96 …")를 주면:

1. `lineup/lineup.json` 수정 — `sat_date`(이번 주 토요일, YYYY-MM-DD), `slots`(요일·시간·남/여 출생연도 범위). 특별 테마 회차는 해당 slot에 `"badge": "외모특집"` 추가 → 레드 카드로 표시. 마감이면 `"status": "마감"`.
   - 카톡 멘트는 "누구에게 보내는 멘트인지"와 "그 안에 적힌 상대 성별 연령대"를 헷갈리지 말 것.
2. `python3 lineup/update_lineup.py` 실행 → `lineup/lineup.jpg` 새로 생성 (인스타용).
3. `lineup/lineup.jpg`를 열어 육안 확인(글자 겹침, 하단 문구 잘림), 승민에게 미리보기로 보여주기.
4. `main`에 커밋·푸시.

- 디자인·문구는 `wemeet-weekly-schedule-card` 스킬과 같아요. 문구를 바꾸려면 `lineup.json`에 `live_note`, `age_note`, `footer_1`, `footer_2`를 넣으면 덮어써요.
- 페이지는 노출 종료일(한국시간 일요일)이 지나면 라인업 섹션을 자동으로 숨겨요. 새 주 라인업을 안 올려도 지난 라인업이 남아 있지 않게.
- 인스타용 이미지도 이 `lineup/lineup.jpg`를 그대로 쓰면 돼요 (1080×1350).
