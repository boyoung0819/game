import streamlit as st
import random
import time
import json
import secrets
import requests
import streamlit.components.v1 as components
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
    "작은 집": {"emoji":"🏡","cost":80,"income":4,"happiness":2,"desc":"주민이 살 수 있는 포근한 집"},
    "꽃밭": {"emoji":"🌷","cost":120,"income":2,"happiness":6,"desc":"마을을 화사하게 만드는 꽃밭"},
    "빵집": {"emoji":"🥐","cost":220,"income":12,"happiness":4,"desc":"고소한 빵 냄새가 솔솔"},
    "카페": {"emoji":"☕","cost":350,"income":18,"happiness":7,"desc":"주민들의 인기 만점 쉼터"},
    "분수 광장": {"emoji":"⛲","cost":500,"income":8,"happiness":12,"desc":"모두가 모이는 마을 중심"},
    "마법 정원": {"emoji":"🪄","cost":800,"income":25,"happiness":18,"desc":"반짝이는 꽃이 피어나는 비밀 정원"},
}
PETS = [
    {"name":"구름이","emoji":"🐰","desc":"포근하고 다정한 토끼"},
    {"name":"콩떡이","emoji":"🐻","desc":"간식을 좋아하는 곰"},
    {"name":"별이","emoji":"🐱","desc":"밤마다 별을 세는 고양이"},
    {"name":"솜사탕","emoji":"🐶","desc":"산책을 좋아하는 강아지"},
    {"name":"푸딩이","emoji":"🐣","desc":"노래 부르기를 좋아하는 병아리"},
    {"name":"반짝이","emoji":"🦊","desc":"호기심 많은 여우"},
]
QUESTS = [
    {"id":"build3","title":"마을의 첫걸음","desc":"건물 3개 짓기","reward":120},
    {"id":"earn500","title":"알뜰한 마을","desc":"보유 코인 500개 모으기","reward":100},
    {"id":"pet1","title":"새로운 가족","desc":"펫 한 마리 입양하기","reward":90},
    {"id":"build6","title":"마을 확장","desc":"건물 6개 짓기","reward":220},
    {"id":"happy50","title":"행복한 마을","desc":"행복도 50 달성하기","reward":150},
]

def init_state():
    defaults = {
        "coins": 300, "day": 1, "buildings": [], "pets": [], "happiness": 20,
        "xp": 0, "level": 1, "claimed_quests": [], "daily_claimed": False,
        "last_tick": time.time(), "log": ["🌱 몽글몽글 타운에 온 걸 환영해! 작은 집부터 지어 보자."],
        "gift_opened": False, "town_name": "몽글마을", "last_daily_day": 0,
        "pet_care": {}, "upgrade_levels": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def log(message):
    st.session_state.log.insert(0, message)
    st.session_state.log = st.session_state.log[:8]

def get_income():
    base = sum(BUILDINGS[b]["income"] for b in st.session_state.buildings)
    return base + sum(st.session_state.upgrade_levels.get(b, 0) * 3 for b in st.session_state.buildings)

def get_happiness():
    return min(100, 20 + sum(BUILDINGS[b]["happiness"] for b in st.session_state.buildings) + len(st.session_state.pets) * 5)

def town_level():
    xp = st.session_state.xp
    return 1 + xp // 100

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
    # 탭을 열어 둔 동안만 최대 30초치 수익 반영
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

# 사이드바
with st.sidebar:
    st.markdown("## ☁️ 클라우드 저장")
    cloud_url, cloud_key = cloud_config()
    if not cloud_url or not cloud_key:
        st.caption("클라우드 저장을 사용하려면 Streamlit의 Settings → Secrets 설정이 필요해.")
    else:
        if not st.session_state.get("save_code"):
            if st.button("새 저장 코드 만들기", use_container_width=True):
                st.session_state.save_code = secrets.token_urlsafe(12)
                save_current_game(show_message=True)
                save_current_game()
                st.rerun()
        if st.session_state.get("save_code"):
            st.text_input("내 저장 코드 (따로 보관하기)", value=st.session_state.save_code, disabled=True)
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
    new_name = st.text_input("마을 이름", value=st.session_state.town_name, max_chars=12)
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

# 지표
cols = st.columns(4)
stats = [
    ("🪙", f"{st.session_state.coins:,}", "보유 코인"),
    ("⭐", f"Lv. {st.session_state.level}", "마을 레벨"),
    ("😊", f"{st.session_state.happiness}/100", "행복도"),
    ("🏗️", f"{len(st.session_state.buildings)}개", "건물 수"),
]
for col, (emoji, value, label) in zip(cols, stats):
    with col:
        st.markdown(f'<div class="stat"><div class="emoji">{emoji}</div><div class="value">{value}</div><div class="label">{label}</div></div>', unsafe_allow_html=True)

st.progress(min(1.0, (st.session_state.xp % 100) / 100), text=f"다음 레벨까지 경험치 {st.session_state.xp % 100}/100")
st.markdown(f'<div class="notice">💰 건물 수익: <b>{get_income()} 코인</b> / 15초 · 건물을 짓고 마을을 발전시켜 보자!</div>', unsafe_allow_html=True)
st.write("")

tab_explore, tab_town, tab_build, tab_pet, tab_quest, tab_book = st.tabs(["🕹️ 마을 탐험", "🌼 우리 마을", "🛠️ 건설하기", "🐾 펫 돌보기", "📜 퀘스트", "🏆 도감·기록"])

with tab_explore:
    st.subheader("🌷 직접 걸어 다니는 몽글마을")
    st.caption("키보드 방향키 또는 WASD로 움직여 봐! 반짝이는 열매에 가까이 가면 자동으로 줍고, 주민 옆에서 E를 누르면 이야기를 나눌 수 있어.")
    game_html = r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;background:#fff8f2;font-family:system-ui,'Noto Sans KR',sans-serif;color:#62556d}.wrap{max-width:100%;margin:auto}.hud{display:flex;gap:8px;align-items:center;justify-content:space-between;flex-wrap:wrap;padding:8px 10px;background:#fffdf8;border:1px solid #f4e3e8;border-radius:14px 14px 0 0;font-size:13px}.pill{background:#ffedf2;padding:6px 10px;border-radius:999px}.stage{position:relative;border:2px solid #fff;border-radius:0 0 16px 16px;overflow:hidden;box-shadow:0 5px 18px #b99bb322;background:#ccefcf}canvas{display:block;width:100%;height:auto;image-rendering:auto;touch-action:none}.hint{font-size:12px;color:#8c7c91;padding:8px 2px}.controls{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;padding:4px}.controls button{border:1px solid #efd9e2;border-radius:12px;background:#fff;color:#6d5b74;padding:9px 14px;font-size:16px;font-weight:700;cursor:pointer}.controls button:active{background:#ffdce7}.msg{min-height:26px;background:#fff5dc;border-radius:10px;padding:7px 10px;font-size:13px;margin-top:6px}
</style></head><body><div class="wrap"><div class="hud"><span class="pill">🌼 몽글마을 산책</span><span id="berry">🍓 찾은 몽글열매: 0</span><span class="pill">이동: 방향키 / WASD · 말걸기: E</span></div><div class="stage"><canvas id="game" width="960" height="560" aria-label="몽글마을 탐험 게임"></canvas></div><div class="controls"><button data-move="up">▲</button><button data-move="left">◀</button><button data-move="down">▼</button><button data-move="right">▶</button><button id="talk">💬 E 말걸기</button><button id="reset">↺ 위치 초기화</button></div><div id="message" class="msg">안녕! 마을 곳곳을 걸어 다니며 반짝이는 몽글열매를 찾아봐.</div><div class="hint">※ 이 탐험 화면은 현재 브라우저 안에서 움직이는 미니게임이야. 찾은 열매와 위치는 이 브라우저에 저장되며, 코인·펫·퀘스트·클라우드 저장은 아래 마을 관리 메뉴에서 이용할 수 있어.</div></div>
<script>
(()=>{
const canvas=document.getElementById('game'),ctx=canvas.getContext('2d');
const W=960,H=560; let player={x:465,y:300}; let keys={}; let moving=false;
const msg=document.getElementById('message');
let saved={};try{saved=JSON.parse(localStorage.getItem('mongle_explore_v1')||'{}')}catch(e){}
if(saved.player&&Number.isFinite(saved.player.x)&&Number.isFinite(saved.player.y)) player=saved.player;
let berries=[{x:150,y:170},{x:340,y:110},{x:780,y:160},{x:835,y:360},{x:300,y:435},{x:610,y:455},{x:510,y:205},{x:115,y:365}].map((b,i)=>({...b,id:i,got:(saved.got||[]).includes(i)}));
const npcs=[{x:510,y:330,name:'토리',emoji:'🐰',line:'꽃밭 옆 열매는 달콤하대! 반짝이는 곳을 찾아봐.'},{x:740,y:285,name:'구름 할머니',emoji:'👵🏻',line:'산책할 때 나무와 꽃도 천천히 구경해 보렴.'},{x:250,y:285,name:'콩이',emoji:'🐻',line:'안녕! 오늘은 마을을 한 바퀴 돌아보는 게 어때?'}];
const trees=[{x:70,y:85},{x:200,y:90},{x:410,y:70},{x:620,y:90},{x:880,y:90},{x:90,y:270},{x:875,y:470},{x:420,y:490},{x:680,y:500},{x:180,y:500},{x:550,y:130},{x:350,y:360}];
function rounded(x,y,w,h,r,color){ctx.fillStyle=color;ctx.beginPath();ctx.roundRect(x,y,w,h,r);ctx.fill()}
function text(t,x,y,size=14,color='#675970',align='center'){ctx.font=`${size}px system-ui,'Noto Sans KR',sans-serif`;ctx.fillStyle=color;ctx.textAlign=align;ctx.fillText(t,x,y)}
function house(x,y,wall,roof,label){rounded(x-42,y-20,84,53,9,wall);ctx.fillStyle=roof;ctx.beginPath();ctx.moveTo(x-52,y-17);ctx.lineTo(x,y-58);ctx.lineTo(x+52,y-17);ctx.closePath();ctx.fill();rounded(x-9,y+2,18,31,5,'#b88776');rounded(x-32,y-7,18,17,4,'#c5e7f4');rounded(x+14,y-7,18,17,4,'#c5e7f4');text(label,x,y+49,13,'#65536b')}
function tree(x,y){ctx.fillStyle='#a9dba0';ctx.beginPath();ctx.arc(x,y-15,22,0,Math.PI*2);ctx.fill();ctx.fillStyle='#7fc68c';ctx.beginPath();ctx.arc(x-12,y-5,15,0,Math.PI*2);ctx.arc(x+12,y-5,15,0,Math.PI*2);ctx.fill();rounded(x-5,y+1,10,20,4,'#b98c72')}
function draw(){ctx.clearRect(0,0,W,H);ctx.fillStyle='#ccefcf';ctx.fillRect(0,0,W,H);
// meadow flecks
for(let i=0;i<100;i++){let x=(i*137+31)%W,y=(i*83+22)%H;ctx.fillStyle=i%2?'#bce6b7':'#d8f3ca';ctx.beginPath();ctx.arc(x,y,2,0,6.28);ctx.fill()}
// paths
ctx.lineCap='round';ctx.strokeStyle='#f6e5c8';ctx.lineWidth=72;ctx.beginPath();ctx.moveTo(-20,300);ctx.bezierCurveTo(220,300,250,350,440,300);ctx.bezierCurveTo(590,250,650,300,980,300);ctx.stroke();ctx.beginPath();ctx.moveTo(460,580);ctx.bezierCurveTo(460,440,430,400,440,300);ctx.stroke();ctx.beginPath();ctx.moveTo(180,300);ctx.bezierCurveTo(180,210,250,210,320,210);ctx.stroke();
// pond
ctx.fillStyle='#a8dce8';ctx.beginPath();ctx.ellipse(790,430,92,48,-.15,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#e7fbff';ctx.lineWidth=4;ctx.stroke();ctx.fillStyle='#c9eff2';ctx.beginPath();ctx.ellipse(770,418,26,8,-.2,0,Math.PI*2);ctx.fill();
// flower beds
rounded(65,390,135,60,16,'#f6c8d8');for(let i=0;i<12;i++){let x=77+(i%6)*21,y=405+Math.floor(i/6)*22;ctx.fillStyle=['#fff2a8','#fff','#e8b7ff'][i%3];ctx.beginPath();ctx.arc(x,y,6,0,6.28);ctx.fill();ctx.fillStyle='#f5d76c';ctx.beginPath();ctx.arc(x,y,2,0,6.28);ctx.fill()}
// buildings
house(310,160,'#fff0dc','#f3a9bd','🍞 빵집');house(680,175,'#fff5cf','#d9b6ed','☕ 포근 카페');house(465,425,'#ffe8ee','#e8a4b7','🏡 작은 집');
// trees and benches
for(const t of trees)tree(t.x,t.y);rounded(590,355,56,12,5,'#c79783');rounded(595,345,46,10,5,'#f3d5b5');
// berries
for(const b of berries){if(b.got)continue;ctx.fillStyle='#fff6b4';ctx.beginPath();ctx.arc(b.x,b.y,15,0,6.28);ctx.fill();text('🍓',b.x,b.y+7,20);}
// NPCs
for(const n of npcs){ctx.fillStyle='#ffffff';ctx.beginPath();ctx.ellipse(n.x,n.y+7,19,8,0,0,6.28);ctx.fill();text(n.emoji,n.x,n.y+4,27);text(n.name,n.x,n.y+26,12,'#65536b');}
// player shadow and sprite
ctx.fillStyle='#8ab58a66';ctx.beginPath();ctx.ellipse(player.x,player.y+11,17,7,0,0,6.28);ctx.fill();text('👧🏻',player.x,player.y+7,31);
// nearest NPC hint
let near=npcs.find(n=>Math.hypot(n.x-player.x,n.y-player.y)<48);if(near){rounded(near.x-42,near.y-45,84,23,10,'#fffdf5');text('E 말걸기',near.x,near.y-29,12,'#69556f')}
requestAnimationFrame(draw)}
function persist(){localStorage.setItem('mongle_explore_v1',JSON.stringify({player,got:berries.filter(b=>b.got).map(b=>b.id)}));document.getElementById('berry').textContent=`🍓 찾은 몽글열매: ${berries.filter(b=>b.got).length}`}
function interact(){let n=npcs.slice().sort((a,b)=>Math.hypot(a.x-player.x,a.y-player.y)-Math.hypot(b.x-player.x,b.y-player.y))[0];if(n&&Math.hypot(n.x-player.x,n.y-player.y)<58){msg.textContent=`${n.emoji} ${n.name}: “${n.line}”`;return}msg.textContent='주민 가까이에서 E를 누르면 이야기를 나눌 수 있어!';}
function step(dx,dy){let nx=Math.max(28,Math.min(W-28,player.x+dx)),ny=Math.max(35,Math.min(H-28,player.y+dy));player.x=nx;player.y=ny;moving=true;for(const b of berries){if(!b.got&&Math.hypot(b.x-player.x,b.y-player.y)<27){b.got=true;msg.textContent='✨ 몽글열매를 찾았어! 잘했어!';} }persist()}
window.addEventListener('keydown',e=>{let k=e.key.toLowerCase();if(['arrowup','arrowdown','arrowleft','arrowright',' '].includes(k))e.preventDefault();keys[k]=true;if(k==='e')interact()});window.addEventListener('keyup',e=>keys[e.key.toLowerCase()]=false);
function loop(){let dx=0,dy=0;if(keys.arrowleft||keys.a)dx-=2.7;if(keys.arrowright||keys.d)dx+=2.7;if(keys.arrowup||keys.w)dy-=2.7;if(keys.arrowdown||keys.s)dy+=2.7;if(dx||dy)step(dx,dy);requestAnimationFrame(loop)}
document.querySelectorAll('[data-move]').forEach(btn=>{let d=btn.dataset.move;let interval;const run=()=>{if(d==='up')step(0,-13);if(d==='down')step(0,13);if(d==='left')step(-13,0);if(d==='right')step(13,0)};btn.addEventListener('click',run);btn.addEventListener('touchstart',e=>{e.preventDefault();run();interval=setInterval(run,100)},{passive:false});['touchend','touchcancel','mouseup','mouseleave'].forEach(ev=>btn.addEventListener(ev,()=>clearInterval(interval)))});
document.getElementById('talk').onclick=interact;document.getElementById('reset').onclick=()=>{player={x:465,y:300};persist();msg.textContent='마을 광장으로 돌아왔어!';};persist();draw();loop();
})();
</script></body></html>'''
    components.html(game_html, height=700, scrolling=False)
    st.info("💡 지금은 혼자 탐험하는 버전이야. 다음에는 탐험에서 얻은 보상을 코인·퀘스트와 연결하고, 친구와 함께하는 온라인 기능을 추가할 수 있어.")

with tab_town:
    st.subheader("🌳 한눈에 보는 우리 마을")
    if not st.session_state.buildings:
        st.markdown("""
        <div class="hero">
          <div style="font-size:3rem">🌱 🪨 🌱</div>
          <h3>아직 작은 빈터야!</h3>
          <p>건설하기에서 작은 집을 지으면 마을이 시작돼.</p>
        </div>""", unsafe_allow_html=True)
    else:
        # 간단한 마을 타일 그리드
        all_tiles = [("🌳", "큰 나무", "마을의 초록 친구")]
        for b in st.session_state.buildings:
            all_tiles.append((BUILDINGS[b]["emoji"], b, BUILDINGS[b]["desc"]))
        all_tiles.extend([(p["emoji"], p["name"], p["desc"]) for p in st.session_state.pets])
        all_tiles.extend([("🌼","야생화","길가에 핀 작은 꽃")] * 2)
        for start in range(0, len(all_tiles), 4):
            row = st.columns(4)
            for col, (emoji, name, desc) in zip(row, all_tiles[start:start+4]):
                with col:
                    st.markdown(f'<div class="tile"><div class="big">{emoji}</div><div class="name">{name}</div><div class="desc">{desc}</div></div>', unsafe_allow_html=True)
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
with tab_build:
    st.subheader("🛠️ 건물을 지어 마을을 발전시키자")
    st.caption("건물을 지으면 수익과 행복도가 올라가. 같은 건물도 여러 개 지을 수 있어!")
    cards = st.columns(3)
    for i, (name, data) in enumerate(BUILDINGS.items()):
        with cards[i % 3]:
            st.markdown(f'<div class="tile"><div class="big">{data["emoji"]}</div><div class="name">{name}</div><div class="desc">{data["desc"]}</div><hr><div>🪙 {data["cost"]} 코인</div><div>💰 +{data["income"]}/15초</div><div>😊 행복도 +{data["happiness"]}</div></div>', unsafe_allow_html=True)
            if st.button(f"{name} 짓기", key=f"build_{name}", use_container_width=True, disabled=st.session_state.coins < data["cost"]):
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
        selected = st.selectbox("업그레이드할 건물 선택", sorted(set(st.session_state.buildings)))
        level = st.session_state.upgrade_levels.get(selected, 0)
        cost = 150 * (level + 1)
        st.write(f"현재 업그레이드: Lv. {level} · 다음 비용: 🪙 {cost} · 수익 +3/15초")
        if st.button("✨ 업그레이드", disabled=st.session_state.coins < cost, key="upgrade"):
            st.session_state.coins -= cost
            st.session_state.upgrade_levels[selected] = level + 1
            st.session_state.xp += 20
            update_level()
            log(f"✨ {selected} 업그레이드 완료!")
            save_current_game()
            st.rerun()
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
                st.button("가족이야 💗", key=f"owned_{p['name']}", disabled=True, use_container_width=True)
            elif st.button("입양 🏡 (100)", key=f"adopt_{p['name']}", disabled=st.session_state.coins < 100, use_container_width=True):
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
            st.session_state.pet_care[chosen] = st.session_state.pet_care.get(chosen, 0) + 1
            st.session_state.xp += 5
            log(f"🍓 {chosen}가 간식을 먹고 기뻐했어!")
            st.success(f"{chosen}: 냠냠! 행복한 표정으로 꼬리를 흔들어. 💕")
            save_current_game()
            st.rerun()
        for p in st.session_state.pets:
            st.caption(f"{p['emoji']} {p['name']} · 받은 간식 {st.session_state.pet_care.get(p['name'], 0)}개")

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
        else:
            done = st.session_state.happiness >= 50
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
                    if st.button("보상 받기", key=f"quest_{q['id']}", use_container_width=True):
                        st.session_state.coins += q["reward"]
                        st.session_state.claimed_quests.append(q["id"])
                        st.session_state.xp += 15
                        update_level()
                        log(f"📜 '{q['title']}' 퀘스트 보상을 받았어!")
                        save_current_game()
                        st.rerun()
                else:
                    st.button("진행 중", key=f"pending_{q['id']}", disabled=True, use_container_width=True)

with tab_book:
    st.subheader("🏆 도감과 마을 기록")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🏘️ 건물 도감")
        for name, data in BUILDINGS.items():
            count = st.session_state.buildings.count(name)
            st.write(f"{data['emoji']} **{name}** — {count}개 보유" if count else f"🔒 **???** — 아직 발견하지 못했어")
    with c2:
        st.markdown("### 🐾 펫 도감")
        owned_names = [p["name"] for p in st.session_state.pets]
        for p in PETS:
            st.write(f"{p['emoji']} **{p['name']}**" if p["name"] in owned_names else "🔒 **???** — 아직 만나지 못했어")
    st.markdown("---")
    st.markdown("### 🌟 업적")
    achievements = [
        ("첫 건설", len(st.session_state.buildings) >= 1, "건물을 처음으로 지었어"),
        ("건축가", len(st.session_state.buildings) >= 5, "건물 5개를 모았어"),
        ("펫 집사", len(st.session_state.pets) >= 3, "펫 3마리와 함께해"),
        ("행복 가득", st.session_state.happiness >= 60, "행복도 60을 달성했어"),
        ("마을 스타", st.session_state.level >= 5, "마을 레벨 5를 달성했어"),
    ]
    for title, done, desc in achievements:
        st.write(f"{'🏅' if done else '▫️'} **{title}** — {desc}")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#aa9aaa;font-size:.85rem">🌷 몽글몽글 타운 · 천천히 키워도 괜찮아. 오늘도 작은 행복을 모아 봐! 🌷</div>', unsafe_allow_html=True)
if st.session_state.get("save_code"):
    save_current_game()
st.caption("저장 코드를 만들면 클라우드 저장과 다른 기기에서 불러오기를 사용할 수 있어. 저장 코드는 안전하게 보관해 줘.")
