        st.session_state.daily_claimed = False
        st.session_state.gift_opened = False
        update_level()
        log(f"🌤️ {st.session_state.day}일째! 마을이 코인 {earned}개를 벌었어.")
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
