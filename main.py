import streamlit as st
import random
import time
import json
import secrets
import requests
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title="몽글몽글 타운", page_icon="🏡", layout="wide")

# 별도 HTML 컴포넌트: 탐험 그래픽과 캐릭터 조작
explore_component = components.declare_component(
    "mongle_explorer", path="explore_component"
)

# ---------- Supabase 클라우드 저장 ----------
GAME_KEYS = [
    "coins", "day", "buildings", "pets", "happiness", "xp", "level",
    "claimed_quests", "daily_claimed", "last_tick", "log", "gift_opened",
    "town_name", "last_daily_day", "pet_care", "upgrade_levels", "berry_count",
    "gems", "gem_claimed_missions", "owned_characters", "active_character",
    "gacha_result"
]


def cloud_config():
    try:
        url = str(st.secrets.get("SUPABASE_URL", "")).strip().rstrip("/")
        key = str(st.secrets.get("SUPABASE_ANON_KEY", "")).strip()
        return url, key
    except Exception:
        return "", ""


def save_current_game(show_message=False):
    code = st.session_state.get("save_code", "")
    url, key = cloud_config()
    if not code or not url or not key:
        return False

    state = {
        k: st.session_state.get(k)
        for k in GAME_KEYS
        if k in st.session_state
    }

    try:
        response = requests.post(
            f"{url}/rest/v1/rpc/save_game",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={"p_code": code, "p_state": state},
            timeout=12,
        )
        response.raise_for_status()

        if show_message:
            st.success("☁️ 마을을 클라우드에 저장했어!")
        return True

    except Exception as exc:
        if show_message:
            st.error(
                f"저장에 실패했어. Supabase 설정을 확인해 줰. ({exc})"
            )
        return False


def load_game_from_cloud(code):
    url, key = cloud_config()

    if not url or not key:
        st.error(
            "먼저 Streamlit Settings → Secrets에 "
            "Supabase 주소와 키를 입력해 줘."
        )
        return False

    try:
        response = requests.post(
            f"{url}/rest/v1/rpc/load_game",
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={"p_code": code.strip()},
            timeout=12,
        )
        response.raise_for_status()
        state = response.json()

        if not isinstance(state, dict) or not state:
            st.error("저장 기록을 찾지 못했어. 저장 코드를 다시 확인해 줘.")
            return False

        for k, v in state.items():
            if k in GAME_KEYS:
                st.session_state[k] = v

        st.session_state.save_code = code.strip()
        st.session_state.last_tick = time.time()
        return True

    except Exception as exc:
        st.error(f"불러오기에 실패했어. Supabase 설정을 확인해 줘. ({exc})")
        return False


# ---------- 스타일 ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Noto+Sans+KR:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.stApp { background: linear-gradient(180deg, #fff8f0 0%, #fffdf8 55%, #f4fff4 100%); }
h1, h2, h3 { font-family: 'Jua', sans-serif !important; color: #5b536b; }
.hero {
  background: linear-gradient(135deg,#ffe3ec,#fff0c9,#dcf7e8);
  padding: 26px; border-radius: 24px; border: 2px solid #fff;
  box-shadow: 0 6px 18px #d8c8d533; text-align:center; margin-bottom: 12px;
}
.hero h1 { margin:0; font-size: 2.5rem; }
.hero p { color:#746b7b; margin:8px 0 0 0; }
.stat {
  background: #ffffffd9; border: 1px solid #f2e7e9; border-radius: 18px;
  padding: 14px; text-align:center; box-shadow: 0 3px 10px #bcaab522;
}
.stat .emoji { font-size: 1.5rem; }
.stat .value { font-size: 1.35rem; font-weight: 800; color:#62576e; }
.stat .label { color:#928696; font-size:.85rem; }
.tile {
  background:#fff; border:1px solid #f0e4e8; border-radius:18px;
  padding:14px; text-align:center; min-height:142px; box-shadow:0 3px 12px #bcaab51c;
}
.tile .big { font-size:2.2rem; }
.tile .name { font-weight:800; color:#62576e; }
.tile .desc { color:#938696; font-size:.82rem; }
.notice { background:#fff4d9; padding:12px 15px; border-radius:14px; color:#765e35; }
.small-muted { color:#938696; font-size:.85rem; }
div.stButton > button { border-radius: 14px; border: 1px solid #f0dfe6; font-weight:700; }
div.stButton > button[kind="primary"] { background:#ffb8cc; color:#583f52; border:0; }
</style>
""", unsafe_allow_html=True)


# ---------- 게임 데이터 ----------
BUILDINGS = {
    "작은 집": {
        "emoji": "🏡", "cost": 80, "income": 4, "happiness": 2,
        "desc": "주민이 살 수 있는 포근한 집"
    },
    "꽃밭": {
        "emoji": "🌷", "cost": 120, "income": 2, "happiness": 6,
        "desc": "마을을 화사하게 만드는 꽃밭"
    },
    "빵집": {
        "emoji": "🥐", "cost": 220, "income": 12, "happiness": 4,
        "desc": "고소한 빵 냄새가 솔솔"
    },
    "카페": {
        "emoji": "☕", "cost": 350, "income": 18, "happiness": 7,
        "desc": "주민들의 인기 만점 쉼터"
    },
    "분수 광장": {
        "emoji": "⛲", "cost": 500, "income": 8, "happiness": 12,
        "desc": "모두가 모이는 마을 중심"
    },
    "마법 정원": {
        "emoji": "🪄", "cost": 800, "income": 25, "happiness": 18,
        "desc": "반짝이는 꽃이 피어나는 비밀 정원"
    },
}

PETS = [
    {"name": "구름이", "emoji": "🐰", "desc": "포근하고 다정한 토끼"},
    {"name": "콩떡이", "emoji": "🐻", "desc": "간식을 좋아하는 곰"},
    {"name": "별이", "emoji": "🐱", "desc": "밤마다 별을 세는 고양이"},
    {"name": "솜사탕", "emoji": "🐶", "desc": "산책을 좋아하는 강아지"},
    {"name": "푸딩이", "emoji": "🐣", "desc": "노래 부르기를 좋아하는 병아리"},
    {"name": "반짝이", "emoji": "🦊", "desc": "호기심 많은 여우"},
]

CHARACTERS = [
    {
        "name": "몽글이", "emoji": "🐰", "rarity": "기본",
        "hair": "#76564f", "outfit": "#ffb7cf", "accent": "#ffe6a7",
        "desc": "처음부터 함께하는 다정한 친구"
    },
    {
        "name": "딸기 요정", "emoji": "🍓", "rarity": "일반",
        "hair": "#7d4d3f", "outfit": "#f47d9e", "accent": "#fff0f4",
        "desc": "딸기 향기를 따라 다니는 요정"
    },
    {
        "name": "민트 토끼", "emoji": "🐇", "rarity": "일반",
        "hair": "#806b62", "outfit": "#8ed8c3", "accent": "#eaffdf",
        "desc": "산들바람처럼 가벼운 산책 친구"
    },
    {
        "name": "복숭아 곰", "emoji": "🐻", "rarity": "희귀",
        "hair": "#9a6559", "outfit": "#f5b58e", "accent": "#fff0c9",
        "desc": "달콤한 간식을 좋아하는 포근한 곰"
    },
    {
        "name": "별빛 고양이", "emoji": "🐱", "rarity": "희귀",
        "hair": "#514a79", "outfit": "#a9a7f5", "accent": "#fff2a8",
        "desc": "밤하늘 별을 모으는 신비한 고양이"
    },
    {
        "name": "달빛 마법사", "emoji": "🪄", "rarity": "특별",
        "hair": "#443d70", "outfit": "#7779c9", "accent": "#f5e7ff",
        "desc": "작은 마법으로 마을을 반짝이게 해"
    },
]

GEM_MISSIONS = [
    {
        "id": "gem_berry3", "title": "첫 열매 수집",
        "desc": "탐험에서 몽글열매 3개 모으기",
        "reward": 3, "kind": "berry", "target": 3
    },
    {
        "id": "gem_berry8", "title": "열매 탐험가",
        "desc": "탐험에서 몽글열매 8개 모으기",
        "reward": 5, "kind": "berry", "target": 8
    },
    {
        "id": "gem_build2", "title": "마을 꾸미기",
        "desc": "건물 2개 짓기",
        "reward": 3, "kind": "build", "target": 2
    },
    {
        "id": "gem_pet1", "title": "새 친구 환영회",
        "desc": "펫 한 마리 입양하기",
        "reward": 3, "kind": "pet", "target": 1
    },
    {
        "id": "gem_level3", "title": "성장하는 마을",
        "desc": "마을 레벨 3 달성하기",
        "reward": 5, "kind": "level", "target": 3
    },
]

QUESTS = [
    {"id": "build3", "title": "마을의 첫걸음", "desc": "건물 3개 짓기", "reward": 120},
    {"id": "earn500", "title": "알뜰한 마을", "desc": "보유 코인 500개 모으기", "reward": 100},
    {"id": "pet1", "title": "새로운 가족", "desc": "펫 한 마리 입양하기", "reward": 90},
    {"id": "build6", "title": "마을 확장", "desc": "건물 6개 짓기", "reward": 220},
    {"id": "happy50", "title": "행복한 마을", "desc": "행복도 50 달성하기", "reward": 150},
    {"id": "berry10", "title": "몽글열매 수집가", "desc": "탐험에서 몽글열매 10개 모으기", "reward": 120},
]


def init_state():
    defaults = {
        "coins": 300,
        "day": 1,
        "buildings": [],
        "pets": [],
        "happiness": 20,
        "xp": 0,
        "level": 1,
        "claimed_quests": [],
        "daily_claimed": False,
        "last_tick": time.time(),
        "log": ["🌱 몽글몽글 타운에 온 걸 환영해! 작은 집부터 지어 보자."],
        "gift_opened": False,
        "town_name": "몽글마을",
        "last_daily_day": 0,
        "pet_care": {},
        "upgrade_levels": {},
        "berry_count": 0,
        "gems": 0,
        "gem_claimed_missions": [],
        "owned_characters": ["몽글이"],
        "active_character": "몽글이",
        "gacha_result": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def log(message):
    st.session_state.log.insert(0, message)
    st.session_state.log = st.session_state.log[:8]


def get_income():
    base = sum(BUILDINGS[b]["income"] for b in st.session_state.buildings)
    upgrades = sum(
        st.session_state.upgrade_levels.get(b, 0) * 3
        for b in st.session_state.buildings
    )
    return base + upgrades


def get_happiness():
    return min(
        100,
        20
        + sum(BUILDINGS[b]["happiness"] for b in st.session_state.buildings)
        + len(st.session_state.pets) * 5,
    )


def town_level():
    return 1 + st.session_state.xp // 100


def update_level():
    new_level = town_level()
    if new_level > st.session_state.level:
        st.session_state.level = new_level
        bonus = 100 * (new_level - 1)
        st.session_state.coins += bonus
        log(f"🎉 마을 레벨 {new_level} 달성! 축하 코인 {bonus}개를 받았어.")


def earn_passive():
    now = time.time()
    elapsed = now - st.session_state.last_tick
    ticks = min(int(elapsed // 15), 120)

    if ticks > 0:
        earned = ticks * get_income()
        st.session_state.coins += earned
        st.session_state.last_tick = now

        if earned:
            st.session_state.xp += ticks * 2
            update_level()


init_state()
earn_passive()
st.session_state.happiness = get_happiness()


# ---------- 상단 ----------
st.markdown(f"""
<div class="hero">
  <div style="font-size:2.6rem">🌷 🐰 🏡 🐻 🌷</div>
  <h1>몽글몽글 타운</h1>
  <p>작은 행복이 모여 커다란 마을이 되는 곳 · {st.session_state.town_name}</p>
</div>
""", unsafe_allow_html=True)


# ---------- 사이드바 ----------
with st.sidebar:
    st.markdown("## ☁️ 클라우드 저장")
    cloud_url, cloud_key = cloud_config()

    if not cloud_url or not cloud_key:
        st.caption(
            "클라우드 저장을 사용하려면 Streamlit의 Settings → Secrets 설정이 필요해."
        )
    else:
        if not st.session_state.get("save_code"):
            if st.button("새 저장 코드 만들기", use_container_width=True):
                st.session_state.save_code = secrets.token_urlsafe(12)
                save_current_game(show_message=True)
                save_current_game()
                st.rerun()

        if st.session_state.get("save_code"):
            st.text_input(
                "내 저장 코드 (따로 보관하기)",
                value=st.session_state.save_code,
                disabled=True,
            )

            if st.button("☁️ 지금 저장하기", use_container_width=True):
                save_current_game(show_message=True)

        code_to_load = st.text_input("기존 저장 코드로 불러오기", key="cloud_load_code")

        if st.button("📥 저장된 마을 불러오기", use_container_width=True):
            if code_to_load.strip() and load_game_from_cloud(code_to_load):
                st.success("마을을 불러왔어!")
                save_current_game()
                st.rerun()
            elif not code_to_load.strip():
                st.warning("저장 코드를 입력해 줘.")

    st.markdown("---")
    st.markdown("## 🏡 마을 안내")
    new_name = st.text_input(
        "마을 이름", value=st.session_state.town_name, max_chars=12
    )

    if new_name.strip() and new_name != st.session_state.town_name:
        st.session_state.town_name = new_name.strip()
        save_current_game()
        st.rerun()

    st.caption("마을을 꾸미고 주민과 펫을 돌봐 줘!")
    st.markdown("---")
    st.markdown("### 🎁 오늘의 선물")

    if not st.session_state.daily_claimed:
        if st.button("출석 보상 받기 🍓", use_container_width=True, type="primary"):
            reward = random.randint(40, 90)
            st.session_state.coins += reward
            st.session_state.daily_claimed = True
            st.session_state.xp += 10
            update_level()
            log(f"🎁 출석 보상으로 코인 {reward}개를 받았어!")
            save_current_game()
            st.rerun()
    else:
        st.success("오늘의 선물을 받았어! 💗")

    if st.button("🎲 랜덤 선물 상자", use_container_width=True):
        if st.session_state.gift_opened:
            st.info("선물 상자는 하루에 한 번 열 수 있어!")
        else:
            reward = random.choice([30, 50, 80, 120, 180])
            st.session_state.coins += reward
            st.session_state.gift_opened = True
            st.session_state.xp += 8
            update_level()
            log(f"🎀 선물 상자에서 코인 {reward}개가 나왔어!")
            save_current_game()
            st.rerun()

    st.markdown("---")
    st.markdown("### 🔄 게임 관리")

    if st.button("새 게임 시작", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.caption("※ 새 게임을 시작하면 현재 진행 상황이 초기화돼.")


# ---------- 지표 ----------
cols = st.columns(4)
stats = [
    ("🪙", f"{st.session_state.coins:,}", "보유 코인"),
    ("⭐", f"Lv. {st.session_state.level}", "마을 레벨"),
    ("😊", f"{st.session_state.happiness}/100", "행복도"),
    ("🏗️", f"{len(st.session_state.buildings)}개", "건물 수"),
]

for col, (emoji, value, label) in zip(cols, stats):
    with col:
        st.markdown(
            f'<div class="stat"><div class="emoji">{emoji}</div>'
            f'<div class="value">{value}</div>'
            f'<div class="label">{label}</div></div>',
            unsafe_allow_html=True,
        )

st.progress(
    min(1.0, (st.session_state.xp % 100) / 100),
    text=f"다음 레벨까지 경험치 {st.session_state.xp % 100}/100",
)

st.markdown(
    f'<div class="notice">💰 건물 수익: <b>{get_income()} 코인</b> / 15초 · '
    '건물을 짓고 마을을 발전시켜 보자!</div>',
    unsafe_allow_html=True,
)
st.write("")


# ---------- 메뉴 ----------
tab_explore, tab_town, tab_build, tab_pet, tab_quest, tab_gacha, tab_book = st.tabs(
    ["🕹️ 마을 탐험", "🌼 우리 마을", "🛠️ 건설하기", "🐾 펫 돌보기",
     "📜 퀘스트", "💎 캐릭터 뽑기", "🏆 도감·기록"]
)


# ---------- 탐험 ----------
with tab_explore:
    st.subheader("🌷 직접 걸어 다니는 몽글마을")
    st.caption(
        "방향키 또는 WASD로 이동해 봐! 주민 가까이 가면 E 키나 말걸기 버튼으로 대화할 수 있어."
    )

    if st.session_state.pets:
        pet_options = {f"{p['emoji']} {p['name']}": p for p in st.session_state.pets}
        selected_pet_label = st.selectbox(
            "산책할 펫 친구", list(pet_options.keys()), key="explore_pet_choice"
        )
        selected_pet = pet_options[selected_pet_label]
        pet_emoji, pet_name = selected_pet["emoji"], selected_pet["name"]
    else:
        pet_emoji, pet_name = "", ""
        st.info("🐾 펫 돌보기 메뉴에서 친구를 입양하면 탐험할 때 뒤를 졸졸 따라와!")

    active_character = next(
        (c for c in CHARACTERS if c["name"] == st.session_state.active_character),
        CHARACTERS[0],
    )

    explore_event = explore_component(
        pet_emoji=pet_emoji,
        pet_name=pet_name,
        berry_count=int(st.session_state.get("berry_count", 0)),
        active_character=active_character,
        key="mongle_explorer_main",
        default=None,
    )

    if isinstance(explore_event, dict) and explore_event.get("type") == "berry":
        event_id = str(explore_event.get("event_id", ""))

        if event_id and event_id != st.session_state.get("last_explore_event_id", ""):
            st.session_state.last_explore_event_id = event_id
            st.session_state.berry_count = (
                int(st.session_state.get("berry_count", 0)) + 1
            )
            reward = 10
            st.session_state.coins += reward
            st.session_state.xp += 3
            update_level()
            log(
                f"🍓 몽글열매를 주워 코인 {reward}개와 경험치 3을 얻었어! "
                f"(누적 {st.session_state.berry_count}개)"
            )
            save_current_game()
            st.rerun()

    st.markdown(
        f'<div class="notice">🍓 누적 몽글열매: '
        f'<b>{int(st.session_state.get("berry_count", 0))}개</b> · '
        f'열매 1개당 🪙 10코인 + ⭐ 경험치 3 · '
        f'함께 산책하는 친구: <b>{pet_name if pet_name else "아직 없음"}</b></div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "탐험 위치와 그래픽은 이 브라우저에 저장돼. 코인과 누적 열매 수는 "
        "마을 기록에 반영되고, 저장 코드를 설정하면 클라우드 저장도 가능해."
    )


# ---------- 마을 ----------
with tab_town:
    st.subheader("🌳 한눈에 보는 우리 마을")

    if not st.session_state.buildings:
        st.markdown("""
        <div class="hero">
          <div style="font-size:3rem">🌱 🪨 🌱</div>
          <h3>아직 작은 빈터야!</h3>
          <p>건설하기에서 작은 집을 지으면 마을이 시작돼.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        all_tiles = [("🌳", "큰 나무", "마을의 초록 친구")]

        for b in st.session_state.buildings:
            all_tiles.append((BUILDINGS[b]["emoji"], b, BUILDINGS[b]["desc"]))

        all_tiles.extend([(p["emoji"], p["name"], p["desc"]) for p in st.session_state.pets])
        all_tiles.extend([("🌼", "야생화", "길가에 핀 작은 꽃")] * 2)

        for start in range(0, len(all_tiles), 4):
            row = st.columns(4)
            for col, (emoji, name, desc) in zip(row, all_tiles[start:start + 4]):
                with col:
                    st.markdown(
                        f'<div class="tile"><div class="big">{emoji}</div>'
                        f'<div class="name">{name}</div>'
                        f'<div class="desc">{desc}</div></div>',
                        unsafe_allow_html=True,
                    )

    st.write("")
    left, right = st.columns(2)

    with left:
        st.markdown("### 🌈 마을 상태")
        st.write(f"**마을 이름:** {st.session_state.town_name}")
        st.write(f"**하루 수익(게임 기준):** {get_income() * 4:,} 코인")
        st.write(f"**입양한 펫:** {len(st.session_state.pets)}마리")
        st.write(f"**마을 경험치:** {st.session_state.xp} XP")

    with right:
        st.markdown("### 💌 마을 소식")
        for item in st.session_state.log[:5]:
            st.write("• " + item)

    if st.button("🌤️ 하루 보내기", type="primary", key="pass_day"):
        earned = get_income() * 4
        st.session_state.coins += earned
        st.session_state.day += 1
        st.session_state.xp += 15
        st.session_state.daily_claimed = False
        st.session_state.gift_opened = False
        update_level()
        log(f"🌤️ {st.session_state.day}일째! 마을이 코인 {earned}개를 벌었어.")
        save_current_game()
        st.rerun()


# ---------- 건설 ----------
with tab_build:
    st.subheader("🛠️ 건물을 지어 마을을 발전시키자")
    st.caption("건물을 지으면 수익과 행복도가 올라가. 같은 건물도 여러 개 지을 수 있어!")
    cards = st.columns(3)

    for i, (name, data) in enumerate(BUILDINGS.items()):
        with cards[i % 3]:
            st.markdown(
                f'<div class="tile"><div class="big">{data["emoji"]}</div>'
                f'<div class="name">{name}</div><div class="desc">{data["desc"]}</div>'
                f'<hr><div>🪙 {data["cost"]} 코인</div>'
                f'<div>💰 +{data["income"]}/15초</div>'
                f'<div>😊 행복도 +{data["happiness"]}</div></div>',
                unsafe_allow_html=True,
            )

            if st.button(
                f"{name} 짓기", key=f"build_{name}",
                use_container_width=True,
                disabled=st.session_state.coins < data["cost"],
            ):
                st.session_state.coins -= data["cost"]
                st.session_state.buildings.append(name)
                st.session_state.xp += 25
                update_level()
                log(f"{data['emoji']} {name}을(를) 지었어!")
                save_current_game()
                st.rerun()

    if st.session_state.buildings:
        st.markdown("---")
        st.markdown("### 🔧 건물 업그레이드")
        selected = st.selectbox(
            "업그레이드할 건물 선택", sorted(set(st.session_state.buildings))
        )
        level = st.session_state.upgrade_levels.get(selected, 0)
        cost = 150 * (level + 1)
        st.write(
            f"현재 업그레이드: Lv. {level} · 다음 비용: 🪙 {cost} · 수익 +3/15초"
        )

        if st.button(
            "✨ 업그레이드",
            disabled=st.session_state.coins < cost,
            key="upgrade",
        ):
            st.session_state.coins -= cost
            st.session_state.upgrade_levels[selected] = level + 1
            st.session_state.xp += 20
            update_level()
            log(f"✨ {selected} 업그레이드 완료!")
            save_current_game()
            st.rerun()


# ---------- 펫 ----------
with tab_pet:
    st.subheader("🐾 사랑스러운 펫 가족")
    st.write("펫은 마을의 행복도를 높여 줘. 마음에 드는 친구를 입양해 보자!")

    for p in PETS:
        owned = any(x["name"] == p["name"] for x in st.session_state.pets)
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{p['emoji']} {p['name']}** — {p['desc']}")

        with col2:
            if owned:
                st.button(
                    "가족이야 💗", key=f"owned_{p['name']}",
                    disabled=True, use_container_width=True,
                )
            elif st.button(
                "입양 🏡 (100)", key=f"adopt_{p['name']}",
                disabled=st.session_state.coins < 100,
                use_container_width=True,
            ):
                st.session_state.coins -= 100
                st.session_state.pets.append(p.copy())
                st.session_state.xp += 20
                update_level()
                log(f"🐾 {p['name']}가 마을 가족이 되었어!")
                save_current_game()
                st.rerun()

    if st.session_state.pets:
        st.markdown("---")
        st.markdown("### 🍓 간식 주기")
        pet_names = [p["name"] for p in st.session_state.pets]
        chosen = st.selectbox("간식을 줄 친구", pet_names)

        if st.button("간식 주기 (🪙 15)", disabled=st.session_state.coins < 15):
            st.session_state.coins -= 15
            st.session_state.pet_care[chosen] = (
                st.session_state.pet_care.get(chosen, 0) + 1
            )
            st.session_state.xp += 5
            log(f"🍓 {chosen}가 간식을 먹고 기뻐했어!")
            st.success(f"{chosen}: 냠냠! 행복한 표정으로 꼬리를 흔들어. 💕")
            save_current_game()
            st.rerun()

        for p in st.session_state.pets:
            st.caption(
                f"{p['emoji']} {p['name']} · "
                f"받은 간식 {st.session_state.pet_care.get(p['name'], 0)}개"
            )


# ---------- 퀘스트 ----------
with tab_quest:
    st.subheader("📜 마을 퀘스트")
    st.write("퀘스트를 완료하면 보상을 받을 수 있어!")

    for q in QUESTS:
        if q["id"] == "build3":
            done = len(st.session_state.buildings) >= 3
        elif q["id"] == "earn500":
            done = st.session_state.coins >= 500
        elif q["id"] == "pet1":
            done = len(st.session_state.pets) >= 1
        elif q["id"] == "build6":
            done = len(st.session_state.buildings) >= 6
        elif q["id"] == "happy50":
            done = st.session_state.happiness >= 50
        else:
            done = int(st.session_state.get("berry_count", 0)) >= 10

        claimed = q["id"] in st.session_state.claimed_quests

        with st.container(border=True):
            a, b = st.columns([3, 1])

            with a:
                st.markdown(f"**{'✅' if done else '🌱'} {q['title']}**")
                st.caption(q["desc"])
                st.caption(f"보상: 🪙 {q['reward']} 코인")

            with b:
                if claimed:
                    st.success("완료")
                elif done:
                    if st.button(
                        "보상 받기", key=f"quest_{q['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.coins += q["reward"]
                        st.session_state.claimed_quests.append(q["id"])
                        st.session_state.xp += 15
                        update_level()
                        log(f"📜 '{q['title']}' 퀘스트 보상을 받았어!")
                        save_current_game()
                        st.rerun()
                else:
                    st.button(
                        "진행 중", key=f"pending_{q['id']}",
                        disabled=True, use_container_width=True,
                    )


# ---------- 보석 미션과 캐릭터 뽑기 ----------
with tab_gacha:
    st.subheader("💎 반짝 캐릭터 연구소")
    st.markdown(
        f"<div class='hero'><div style='font-size:2.4rem'>💎 ✨ 🎀</div>"
        f"<h2>보석으로 새 친구 만나기</h2>"
        f"<p>보석은 아래 미션을 완료하면 무료로 얻을 수 있어!</p>"
        f"<div style='font-size:1.3rem;font-weight:800'>"
        f"💎 보유 보석: {int(st.session_state.gems)}</div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("### 🧭 보석 미션")
    st.caption("미션 보상은 한 번만 받을 수 있어. 탐험하거나 마을을 키우면서 보석을 모아 봐!")

    for mission in GEM_MISSIONS:
        if mission["kind"] == "berry":
            progress = int(st.session_state.berry_count)
        elif mission["kind"] == "build":
            progress = len(st.session_state.buildings)
        elif mission["kind"] == "pet":
            progress = len(st.session_state.pets)
        else:
            progress = int(st.session_state.level)

        done = progress >= mission["target"]
        claimed = mission["id"] in st.session_state.gem_claimed_missions

        with st.container(border=True):
            left, right = st.columns([3, 1])

            with left:
                st.markdown(f"**{'✅' if done else '🌱'} {mission['title']}**")
                st.caption(mission["desc"])
                st.progress(
                    min(1.0, progress / mission["target"]),
                    text=f"진행도 {min(progress, mission['target'])}/{mission['target']}",
                )
                st.caption(f"보상: 💎 {mission['reward']}개")

            with right:
                if claimed:
                    st.success("수령 완료")
                elif done:
                    if st.button(
                        "보석 받기", key=f"claim_{mission['id']}",
                        use_container_width=True,
                    ):
                        st.session_state.gems += mission["reward"]
                        st.session_state.gem_claimed_missions.append(mission["id"])
                        log(
                            f"💎 '{mission['title']}' 미션으로 "
                            f"보석 {mission['reward']}개를 얻었어!"
                        )
                        save_current_game()
                        st.rerun()
                else:
                    st.button(
                        "미션 중", key=f"pending_{mission['id']}",
                        disabled=True, use_container_width=True,
                    )

    st.markdown("---")
    st.markdown("### 🎁 캐릭터 뽑기")
    st.write("한 번에 보석 5개가 필요해. 게임 속에서 모은 보석만 사용해!")
    st.caption("일반 캐릭터 65%, 희귀 캐릭터 28%, 특별 캐릭터 7% 확률이야.")

    if st.button(
        "✨ 보석 5개로 캐릭터 뽑기",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.gems < 5,
    ):
        st.session_state.gems -= 5
        roll = random.random()

        if roll < 0.65:
            pool = [c for c in CHARACTERS if c["rarity"] in ("기본", "일반")]
        elif roll < 0.93:
            pool = [c for c in CHARACTERS if c["rarity"] == "희귀"]
        else:
            pool = [c for c in CHARACTERS if c["rarity"] == "특별"]

        won = random.choice(pool)

        if won["name"] in st.session_state.owned_characters:
            st.session_state.gems += 1
            st.session_state.gacha_result = (
                f"중복! {won['emoji']} {won['name']}이(가) 또 나왔어. "
                "대신 보석 1개를 돌려받았어."
            )
        else:
            st.session_state.owned_characters.append(won["name"])
            st.session_state.gacha_result = (
                f"새 친구 등장! {won['emoji']} {won['name']} "
                f"({won['rarity']})을(를) 만났어!"
            )
            st.session_state.active_character = won["name"]

        log(st.session_state.gacha_result)
        save_current_game()
        st.rerun()

    if st.session_state.get("gacha_result"):
