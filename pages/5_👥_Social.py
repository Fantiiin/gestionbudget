import streamlit as st
from database import (
    init_db, get_all_users, get_user_by_username, get_user_by_id, get_friends,
    get_pending_requests_for_me, get_pending_requests_from_me,
    send_friend_request, accept_friend_request, reject_friend_request, remove_friend,
    get_debt_balance, get_all_unsettled_debts, create_debt, settle_debt,
    create_challenge, join_challenge, get_active_challenges,
    get_challenge_scores, get_challenge_participants, delete_challenge,
    get_category_names,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Social — Budget", page_icon="👥", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()

st.markdown("# 👥 Social")

tab_friends, tab_debts, tab_challenges = st.tabs(["🤝 Amis", "💸 Dettes", "🏆 Challenges"])

# ═══ FRIENDS TAB ═══
with tab_friends:
    st.markdown("#### ➕ Ajouter un(e) ami(e)")
    add_username = st.text_input("Nom d'utilisateur", key="add_friend", placeholder="ex: mel")
    if st.button("📩 Envoyer la demande", type="primary", use_container_width=True, key="send_req"):
        if not add_username:
            st.warning("⚠️ Entrez un nom d'utilisateur.")
        elif add_username.lower().strip() == user["username"]:
            st.warning("😅 Vous ne pouvez pas vous ajouter vous-même.")
        else:
            target = get_user_by_username(add_username)
            if not target:
                st.error(f"❌ '@{add_username}' n'existe pas.")
            else:
                ok = send_friend_request(uid, target["id"])
                if ok:
                    st.success(f"✅ Demande envoyée à {target.get('avatar','👤')} {target['display_name']} !")
                else:
                    st.info("ℹ️ Demande existante ou déjà amis.")

    # Pending TO me
    st.markdown("---")
    pending = get_pending_requests_for_me(uid)
    if pending:
        st.markdown("#### 📬 Demandes reçues")
        for req in pending:
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1:
                st.markdown(f"""<div class="user-card" style="margin:0">
                    <div class="user-info"><span class="user-avatar">{req.get('avatar','👤')}</span>
                    <div><div class="user-name">{req['display_name']}</div><div class="user-handle">@{req['username']}</div></div></div>
                    <span class="user-badge badge-pending">⏳</span></div>""", unsafe_allow_html=True)
            with c2:
                if st.button("✅", key=f"a_{req['friendship_id']}"):
                    accept_friend_request(req["friendship_id"]); st.rerun()
            with c3:
                if st.button("❌", key=f"r_{req['friendship_id']}"):
                    reject_friend_request(req["friendship_id"]); st.rerun()

    # Sent
    sent = get_pending_requests_from_me(uid)
    if sent:
        st.markdown("#### 📤 Envoyées")
        for req in sent:
            st.markdown(f"""<div class="user-card"><div class="user-info"><span class="user-avatar">{req.get('avatar','👤')}</span>
                <div><div class="user-name">{req['display_name']}</div><div class="user-handle">@{req['username']}</div></div></div>
                <span class="user-badge badge-pending">⏳</span></div>""", unsafe_allow_html=True)

    # Friends
    st.markdown("---")
    st.markdown("#### 🤝 Vos amis")
    friends = get_friends(uid)
    if not friends:
        st.info("Aucun ami. Envoyez une demande ci-dessus !")
    else:
        for f in friends:
            bal = get_debt_balance(uid, f["id"])
            bal_label = ""
            if bal > 0: bal_label = f'<span style="color:#34d399;font-size:0.72rem"> te doit {bal:.2f}€</span>'
            elif bal < 0: bal_label = f'<span style="color:#f87171;font-size:0.72rem"> tu dois {abs(bal):.2f}€</span>'
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"""<div class="user-card" style="margin:0">
                    <div class="user-info"><span class="user-avatar">{f.get('avatar','👤')}</span>
                    <div><div class="user-name">{f['display_name']}{bal_label}</div><div class="user-handle">@{f['username']}</div></div></div>
                    <span class="user-badge badge-friend">✅</span></div>""", unsafe_allow_html=True)
            with c2:
                if st.button("🗑️", key=f"rm_{f['friendship_id']}"):
                    remove_friend(f["friendship_id"]); st.rerun()

    st.markdown("---")
    st.markdown("""<div class="glass" style="padding:0.8rem">
        <div style="font-weight:600;color:#a78bfa;margin-bottom:0.2rem">💡 Que permet l'amitié ?</div>
        <div style="color:#94a3b8;font-size:0.78rem;line-height:1.5">
            • Voir le dashboard de votre ami(e)<br/>• Ajouter une dépense au profil de votre ami(e)<br/>
            • Partager des dépenses et suivre les dettes<br/>• Créer des challenges
        </div></div>""", unsafe_allow_html=True)

# ═══ DEBTS TAB ═══
with tab_debts:
    st.markdown("#### 💸 Dettes")
    friends = get_friends(uid)

    if not friends:
        st.info("Ajoutez d'abord des amis pour gérer les dettes.")
    else:
        # Summary
        st.markdown("##### 📊 Soldes")
        for f in friends:
            bal = get_debt_balance(uid, f["id"])
            if bal == 0: continue
            if bal > 0:
                st.markdown(f"""<div class="glass" style="padding:0.5rem 0.8rem;margin-bottom:0.3rem">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <span>{f.get('avatar','👤')} {f['display_name']}</span>
                        <span class="green" style="font-weight:700">te doit {bal:.2f}€</span>
                    </div></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="glass" style="padding:0.5rem 0.8rem;margin-bottom:0.3rem">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <span>{f.get('avatar','👤')} {f['display_name']}</span>
                        <span class="red" style="font-weight:700">tu dois {abs(bal):.2f}€</span>
                    </div></div>""", unsafe_allow_html=True)

        # Manual debt
        st.markdown("---")
        st.markdown("##### ➕ Nouvelle dette")
        c1, c2 = st.columns(2)
        with c1:
            debt_friend = st.selectbox("Avec", [f"{f['avatar']} {f['display_name']}" for f in friends], key="debt_friend")
            debt_friend_id = friends[[f"{f['avatar']} {f['display_name']}" for f in friends].index(debt_friend)]["id"]
        with c2:
            debt_dir = st.selectbox("Direction", ["Il/elle me doit", "Je dois"], key="debt_dir")
        c3, c4 = st.columns(2)
        with c3:
            debt_amount = st.number_input("Montant €", value=0.0, min_value=0.0, step=0.01, format="%.2f", key="debt_amount")
        with c4:
            debt_desc = st.text_input("Description", key="debt_desc", placeholder="Restaurant du 14/02")

        if st.button("💾 Créer la dette", type="primary", use_container_width=True, key="debt_save"):
            if debt_amount <= 0 or not debt_desc:
                st.warning("⚠️ Montant et description requis.")
            else:
                if debt_dir == "Il/elle me doit":
                    create_debt(debt_friend_id, uid, debt_amount, debt_desc)
                else:
                    create_debt(uid, debt_friend_id, debt_amount, debt_desc)
                st.success("✅ Dette créée"); st.rerun()

        # Unsettled debts
        st.markdown("---")
        st.markdown("##### 📋 Dettes en cours")
        debts = get_all_unsettled_debts(uid)
        if not debts:
            st.caption("Aucune dette en cours. 🎉")
        else:
            for d in debts:
                other_id = d["to_user"] if d["from_user"] == uid else d["from_user"]
                other = get_user_by_id(other_id)
                if not other: continue
                is_mine = d["from_user"] == uid  # I owe
                c1, c2 = st.columns([5, 1])
                with c1:
                    if is_mine:
                        st.markdown(f"""<div class="glass" style="padding:0.4rem 0.8rem;margin-bottom:0.2rem">
                            <div style="display:flex;justify-content:space-between">
                                <span style="color:#e2e8f0;font-size:0.82rem">Tu dois à {other.get('avatar','')} {other['display_name']}</span>
                                <span class="red" style="font-weight:600">{d['montant']:.2f}€</span>
                            </div>
                            <div style="color:#64748b;font-size:0.7rem">{d['description']}</div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown(f"""<div class="glass" style="padding:0.4rem 0.8rem;margin-bottom:0.2rem">
                            <div style="display:flex;justify-content:space-between">
                                <span style="color:#e2e8f0;font-size:0.82rem">{other.get('avatar','')} {other['display_name']} te doit</span>
                                <span class="green" style="font-weight:600">{d['montant']:.2f}€</span>
                            </div>
                            <div style="color:#64748b;font-size:0.7rem">{d['description']}</div>
                        </div>""", unsafe_allow_html=True)
                with c2:
                    if st.button("✅", key=f"settle_{d['id']}", help="Marquer comme réglée"):
                        settle_debt(d["id"]); st.rerun()

# ═══ CHALLENGES TAB ═══
with tab_challenges:
    st.markdown("#### 🏆 Challenges")
    friends = get_friends(uid)
    cat_names = get_category_names(uid)

    if not friends:
        st.info("Ajoutez des amis pour créer des challenges.")
    else:
        # Create
        st.markdown("##### ➕ Nouveau challenge")
        ch_title = st.text_input("Titre", key="ch_title", placeholder="Moins de sorties ce mois !")
        c1, c2 = st.columns(2)
        with c1:
            ch_cat = st.selectbox("Catégorie (optionnel)", ["Toutes"] + cat_names, key="ch_cat")
            ch_cat_val = ch_cat if ch_cat != "Toutes" else ""
        with c2:
            ch_max = st.number_input("Plafond €", value=100.0, min_value=0.0, step=10.0, format="%.0f", key="ch_max")
        c3, c4 = st.columns(2)
        with c3:
            ch_start = st.date_input("Début", value=date.today(), key="ch_start")
        with c4:
            ch_end = st.date_input("Fin", value=date.today() + timedelta(days=30), key="ch_end")

        if st.button("🏆 Créer le challenge", type="primary", use_container_width=True, key="ch_create"):
            if not ch_title or ch_max <= 0:
                st.warning("⚠️ Titre et plafond requis.")
            else:
                cid = create_challenge(uid, ch_title, ch_cat_val, ch_max,
                                       ch_start.strftime("%Y-%m-%d"), ch_end.strftime("%Y-%m-%d"))
                st.success(f"✅ Challenge créé ! Partagez le code : **#{cid}**")
                st.rerun()

        # Join
        st.markdown("---")
        st.markdown("##### 🎫 Rejoindre un challenge")
        ch_join_id = st.number_input("Numéro du challenge (#)", min_value=1, step=1, key="ch_join_id")
        if st.button("🎫 Rejoindre", use_container_width=True, key="ch_join"):
            join_challenge(int(ch_join_id), uid)
            st.success("✅ Rejoint !"); st.rerun()

    # Active challenges
    st.markdown("---")
    st.markdown("##### 📋 Challenges actifs")
    challenges = get_active_challenges(uid)
    if not challenges:
        st.caption("Aucun challenge en cours.")
    else:
        for ch in challenges:
            with st.expander(f"🏆 {ch['title']} — #{ch['id']}", expanded=True):
                cat_label = ch["categorie"] if ch["categorie"] else "Toutes catégories"
                st.caption(f"📅 {ch['date_debut']} → {ch['date_fin']} · {cat_label} · Plafond: {ch['montant_max']:.0f}€")

                scores = get_challenge_scores(ch["id"])
                for i, s in enumerate(scores):
                    pct = min((s["total"] / s["max"] * 100), 100) if s["max"] > 0 else 0
                    over = s["total"] > s["max"]
                    medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else ""
                    bar_color = "#ef4444" if over else "#34d399" if pct < 50 else "#fbbf24"

                    st.markdown(f"""<div class="glass" style="padding:0.5rem 0.8rem;margin-bottom:0.2rem">
                        <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                            <span style="color:#e2e8f0;font-weight:600">{medal} {s.get('avatar','')} {s['display_name']}</span>
                            <span style="color:#e2e8f0;font-weight:600">{s['total']:.0f}€ / {s['max']:.0f}€</span>
                        </div>
                        <div class="cat-track" style="height:6px"><div class="cat-fill" style="width:{pct:.0f}%;background:{bar_color}"></div></div>
                    </div>""", unsafe_allow_html=True)

                if ch["creator_id"] == uid:
                    if st.button("🗑️ Supprimer", key=f"dch_{ch['id']}"):
                        delete_challenge(ch["id"]); st.rerun()
