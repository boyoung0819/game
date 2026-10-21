import streamlit as st
import random
import time
import json
import secrets
import requests
from datetime import datetime

st.set_page_config(page_title="몽글몽글 타운", page_icon="🏡", layout="wide")

# ---------- Supabase 클라우드 저장 ----------
GAME_KEYS = [
    "coins", "day", "buildings", "pets", "happiness", "xp", "level",
    "claimed_quests", "daily_claimed", "last_tick", "log", "gift_opened",
    "town_name", "last_daily_day", "pet_care", "upgrade_levels"
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
    state = {k: st.session_state.get(k) for k in GAME_KEYS if k in st.session_state}
    try:
        response = requests.post(
            f"{url}/rest/v1/rpc/save_game",
            headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"p_code": code, "p_state": state}, timeout=12
        )
        response.raise_for_status()
        if show_message:
            st.success("☁️ 마을을 클라우드에 저장했어!")
        return True
    except Exception as exc:
        if show_message:
            st.error(f"저장에 실패했어. Supabase 설정을 확인해 줘. ({exc})")
        return False

def load_game_from_cloud(code):
    url, key = cloud_config()
    if not url or not key:
        st.error("먼저 Streamlit Settings → Secrets에 Supabase 주소와 키를 입력해 줘.")
        return False
    try:
        response = requests.post(
            f"{url}/rest/v1/rpc/load_game",
            headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"p_code": code.strip()}, timeout=12
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
