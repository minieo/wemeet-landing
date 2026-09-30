#!/usr/bin/env python3
"""위밋 주간 연령대 라인업 교체 스크립트.

사용법 (레포 루트에서):
    1) lineup/lineup.json 에 이번 주 토요일 날짜와 시간대별 연령대를 적는다.
    2) python3 lineup/update_lineup.py
       → lineup/lineup.jpg (카드 이미지)를 새로 만들고,
         index.html 의 이미지 버전과 노출 종료일(일요일)을 갱신한다.
    3) git add -A && git commit && git push

노출 종료일이 지나면(일요일 밤 12시 이후) 페이지에서 라인업 섹션은 자동으로 숨겨진다.
"""
import glob
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
LINEUP = ROOT / "lineup"

DEFAULTS = {
    "live_note": "현재까지 선별된 분들의 연령대예요 · 변동될 수 있어요",
    "age_note": "표기 연령 <b>±1~2살</b>까지 신청 가능해요",
    "footer_1": "선호 연령대 맞춤, 선별된 인원으로 6:6~8:8 소규모 진행",
    "footer_2": "지인과 이전 소개팅에서 만났던 분은 시스템상 자동으로 걸러져요",
}

CARD = """      <div class="card{special}">
        <div class="day-block">
          <div class="day-label">{day}</div>
          <div class="time-label">{time}</div>{badge}
        </div>
        <div class="divider-v"></div>
        <div class="genders">
          <div class="gender-row">
            <div class="gender-tag male">남</div>
            <div class="gender-text"><b>{man}</b>년생</div>
          </div>
          <div class="gender-row">
            <div class="gender-tag female">여</div>
            <div class="gender-text"><b>{woman}</b>년생</div>
          </div>
        </div>
      </div>
"""


def spacing_css(n):
    """템플릿은 카드 4개 기준. 개수가 다르면 여백 조정."""
    if n <= 3:
        return ".cards{gap:28px;} .card{padding:32px 40px;}"
    if n >= 5:
        return ".cards{gap:12px;} .card{padding:12px 36px;} .gender-row{gap:8px;}"
    return ""


def build_html(data):
    sat = date.fromisoformat(data["sat_date"])
    if sat.weekday() != 5:
        sys.exit(f"sat_date {sat} 는 토요일이 아니에요.")
    sun = sat + timedelta(days=1)
    cards = ""
    for s in data["slots"]:
        badge = s.get("badge")
        cards += CARD.format(
            special=" special" if badge else "",
            day=s["day"], time=s["time"], man=s["man"], woman=s["woman"],
            badge=f'\n          <div class="badge">{badge}</div>' if badge else "",
        )
    t = (LINEUP / "template.html").read_text(encoding="utf-8")
    rep = {
        "{{CARDS}}": cards.rstrip("\n"),
        "{{SAT_DATE}}": f"{sat.month} / {sat.day}",
        "{{SUN_DATE}}": f"{sun.month} / {sun.day}",
        "{{STATUS_TEXT}}": data.get("status", "실시간"),
        "{{LIVE_NOTE}}": data.get("live_note", DEFAULTS["live_note"]),
        "{{AGE_NOTE}}": data.get("age_note", DEFAULTS["age_note"]),
        "{{FOOTER_LINE_1}}": data.get("footer_1", DEFAULTS["footer_1"]),
        "{{FOOTER_LINE_2}}": data.get("footer_2", DEFAULTS["footer_2"]),
    }
    for k, v in rep.items():
        t = t.replace(k, v)
    extra = spacing_css(len(data["slots"]))
    if extra:
        t = t.replace("</style>", extra + "\n</style>")
    return t, sat, sun


def chromium_path():
    hits = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))
    return hits[-1] if hits else None


def render(html):
    build = LINEUP / "_build.html"
    png = LINEUP / "_build.png"
    build.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        exe = chromium_path()
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = b.new_page(viewport={"width": 1080, "height": 1350})
        page.goto(build.as_uri())
        page.wait_for_timeout(400)
        overflow = page.evaluate(
            "() => document.querySelector('.footer-note').getBoundingClientRect().bottom > 1350 - 36"
        )
        page.screenshot(path=str(png))
        b.close()
    Image.open(png).convert("RGB").save(
        LINEUP / "lineup.jpg", "JPEG", quality=90, optimize=True, progressive=True
    )
    build.unlink()
    png.unlink()
    if overflow:
        print("⚠️ 하단 문구가 프레임 밖으로 넘쳐요. 카드 수/문구 길이를 확인하세요.")


def update_index(sat, sun):
    idx = ROOT / "index.html"
    t = idx.read_text(encoding="utf-8")
    ver = sat.strftime("%Y%m%d")
    label = f"{sat.month}/{sat.day}(토) · {sun.month}/{sun.day}(일)"
    t, n1 = re.subn(r'data-lineup-until="[0-9-]*"', f'data-lineup-until="{sun.isoformat()}"', t)
    t, n2 = re.subn(r'lineup/lineup\.jpg\?v=[0-9]*', f"lineup/lineup.jpg?v={ver}", t)
    t, n3 = re.subn(r'(<span class="lineup-dates">)[^<]*(</span>)', rf"\g<1>{label}\g<2>", t)
    t = re.sub(r'(alt="위밋 )[^"]*( 연령대 라인업")', rf"\g<1>{label}\g<2>", t)
    if not (n1 and n2 and n3):
        # 2026-10부터 랜딩에는 라인업을 싣지 않음 — 이미지(인스타용)만 만들고 끝냄
        return None
    idx.write_text(t, encoding="utf-8")
    return label


if __name__ == "__main__":
    data = json.loads((LINEUP / "lineup.json").read_text(encoding="utf-8"))
    html, sat, sun = build_html(data)
    render(html)
    label = update_index(sat, sun)
    if label is None:
        print("완료: lineup/lineup.jpg (인스타용) 생성 — 랜딩페이지에는 라인업 섹션이 없어서 건드리지 않았어요")
    else:
        print(f"완료: {label} 라인업 ({len(data['slots'])}개 시간대), {sun.isoformat()} 까지 노출")
