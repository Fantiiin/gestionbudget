import streamlit as st
from database import (
    init_db, get_all_users, get_user_by_username, get_friends,
    get_pending_requests_for_me, get_pending_requests_from_me,
    send_friend_request, accept_friend_request, reject_friend_request, remove_friend,
)
from auth import require_auth, get_current_user_id, get_current_user
from styles import inject_css

st.set_page_config(page_title="Social — Budget", page_icon="👥", layout="wide", initial_sidebar_state="collapsed")
init_db()
require_auth()
inject_css()

uid = get_current_user_id()
user = get_current_user()

st.markdown("# 👥 Social")

# ─── Add Friend ───
st.markdown("#### ➕ Ajouter un(e) ami(e)")
st.caption("Entrez le nom d'utilisateur de la personne à ajouter.")

add_username = st.text_input("Nom d'utilisateur", key="add_friend", placeholder="ex: mel")

if st.button("📩 Envoyer la demande", type="primary", use_container_width=True, key="send_req"):
    if not add_username:
        st.warning("⚠️ Entrez un nom d'utilisateur.")
    elif add_username.lower().strip() == user["username"]:
        st.warning("😅 Vous ne pouvez pas vous ajouter vous-même.")
    else:
        target = get_user_by_username(add_username)
        if not target:
            st.error(f"❌ L'utilisateur '@{add_username}' n'existe pas.")
        else:
            ok = send_friend_request(uid, target["id"])
            if ok:
                st.success(f"✅ Demande envoyée à {target.get('avatar','👤')} {target['display_name']} !")
            else:
                st.info("ℹ️ Une demande existe déjà ou vous êtes déjà amis.")

# ─── Pending Requests TO me ───
st.markdown("---")
st.markdown("#### 📬 Demandes reçues")

pending = get_pending_requests_for_me(uid)
if not pending:
    st.caption("Aucune demande en attente.")
else:
    for req in pending:
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            st.markdown(f"""<div class="user-card" style="margin:0">
                <div class="user-info">
                    <span class="user-avatar">{req.get('avatar','👤')}</span>
                    <div><div class="user-name">{req['display_name']}</div><div class="user-handle">@{req['username']}</div></div>
                </div>
                <span class="user-badge badge-pending">⏳ En attente</span>
            </div>""", unsafe_allow_html=True)
        with c2:
            if st.button("✅", key=f"accept_{req['friendship_id']}", help="Accepter"):
                accept_friend_request(req["friendship_id"])
                st.success(f"🎉 Vous êtes maintenant amis avec {req['display_name']} !")
                st.rerun()
        with c3:
            if st.button("❌", key=f"reject_{req['friendship_id']}", help="Refuser"):
                reject_friend_request(req["friendship_id"])
                st.rerun()

# ─── Pending Requests FROM me ───
sent = get_pending_requests_from_me(uid)
if sent:
    st.markdown("---")
    st.markdown("#### 📤 Demandes envoyées")
    for req in sent:
        st.markdown(f"""<div class="user-card">
            <div class="user-info">
                <span class="user-avatar">{req.get('avatar','👤')}</span>
                <div><div class="user-name">{req['display_name']}</div><div class="user-handle">@{req['username']}</div></div>
            </div>
            <span class="user-badge badge-pending">⏳ En attente</span>
        </div>""", unsafe_allow_html=True)

# ─── Friends List ───
st.markdown("---")
st.markdown("#### 🤝 Vos amis")

friends = get_friends(uid)
if not friends:
    st.info("Aucun ami pour le moment. Envoyez une demande ci-dessus !")
else:
    for f in friends:
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"""<div class="user-card" style="margin:0">
                <div class="user-info">
                    <span class="user-avatar">{f.get('avatar','👤')}</span>
                    <div><div class="user-name">{f['display_name']}</div><div class="user-handle">@{f['username']}</div></div>
                </div>
                <span class="user-badge badge-friend">✅ Ami(e)</span>
            </div>""", unsafe_allow_html=True)
        with c2:
            if st.button("🗑️", key=f"rm_{f['friendship_id']}", help="Retirer de mes amis"):
                remove_friend(f["friendship_id"])
                st.rerun()

    st.caption(f"{len(friends)} ami(e)(s)")

# ─── Info ───
st.markdown("---")
st.markdown("""
<div class="glass" style="padding:1rem">
    <div style="font-weight:600;color:#a78bfa;margin-bottom:0.3rem">💡 Que permet l'amitié ?</div>
    <div style="color:#94a3b8;font-size:0.82rem;line-height:1.6">
        • Voir le <b>dashboard</b> de votre ami(e) depuis la page 📊<br/>
        • Ajouter une <b>dépense au profil</b> de votre ami(e) depuis la page ➕<br/>
        • L'ami(e) verra que c'est vous qui avez ajouté la transaction
    </div>
</div>
""", unsafe_allow_html=True)
