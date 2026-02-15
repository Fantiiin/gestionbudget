import sqlite3
import json
from pathlib import Path
from datetime import datetime, date, timedelta

DB_PATH = Path(__file__).parent / "budget.db"

DEFAULT_CATEGORIES = [
    {"nom": "Alimentaire", "icon": "🛒", "color": "#22c55e", "mots_cles": "supermarché, carrefour, leclerc, auchan, lidl, monoprix, boulangerie, briocherie, boucherie, sodexo, café"},
    {"nom": "Hygiène & Soins", "icon": "🧴", "color": "#3b82f6", "mots_cles": "shampoing, savon, dentifrice, coiffeur, beauté"},
    {"nom": "Loisirs & Sorties", "icon": "🎉", "color": "#f59e0b", "mots_cles": "restaurant, bar, pub, club, boîte de nuit, cinéma, bowling, concert, burger, kebab, pizza"},
    {"nom": "Transport", "icon": "🚗", "color": "#ef4444", "mots_cles": "sncf, ratp, essence, parking, uber, taxi, péage, train, bus, métro"},
    {"nom": "Logement & Factures", "icon": "🏠", "color": "#8b5cf6", "mots_cles": "loyer, edf, free, orange, assurance, électricité, gaz, internet, téléphone"},
    {"nom": "Shopping", "icon": "🛍️", "color": "#ec4899", "mots_cles": "zara, h&m, amazon, fnac, vêtements, chaussures"},
    {"nom": "Santé", "icon": "💊", "color": "#06b6d4", "mots_cles": "pharmacie, médecin, docteur, hôpital, mutuelle"},
    {"nom": "Revenu", "icon": "💰", "color": "#10b981", "mots_cles": "salaire, freelance, virement, remboursement"},
]

AVATAR_LIST = ["😎", "🦊", "🐱", "🐶", "🦁", "🐼", "🦄", "🐸", "🦉", "🐧",
               "🌸", "🌊", "⚡", "🔥", "💎", "🎯", "🚀", "🎨", "🎸", "🌙",
               "👤", "👩", "👨", "🧑", "👸", "🤴", "🧙", "🦸", "🧛", "🤖"]


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            avatar TEXT NOT NULL DEFAULT '👤',
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            date TEXT NOT NULL,
            enseigne TEXT NOT NULL,
            montant_total REAL NOT NULL,
            categorie TEXT NOT NULL,
            chemin_image TEXT,
            articles TEXT,
            type TEXT NOT NULL DEFAULT 'depense',
            added_by INTEGER,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS recurring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            enseigne TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'depense',
            frequence TEXT NOT NULL,
            jour INTEGER NOT NULL,
            actif INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 0,
            nom TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '📁',
            color TEXT NOT NULL DEFAULT '#a78bfa',
            mots_cles TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS friendships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_a INTEGER NOT NULL,
            user_b INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            requested_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_a, user_b)
        )
    """)

    # Migrations
    user_cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "avatar" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT NOT NULL DEFAULT '👤'")

    tx_cols = [r[1] for r in conn.execute("PRAGMA table_info(transactions)").fetchall()]
    if "type" not in tx_cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN type TEXT NOT NULL DEFAULT 'depense'")
    if "user_id" not in tx_cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")
    if "added_by" not in tx_cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN added_by INTEGER")

    rec_cols = [r[1] for r in conn.execute("PRAGMA table_info(recurring)").fetchall()]
    if "user_id" not in rec_cols:
        conn.execute("ALTER TABLE recurring ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")

    cat_cols = [r[1] for r in conn.execute("PRAGMA table_info(categories)").fetchall()]
    if "user_id" not in cat_cols:
        conn.execute("ALTER TABLE categories ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")

    conn.commit()
    conn.close()


def seed_default_categories(user_id: int):
    conn = get_connection()
    existing = conn.execute("SELECT COUNT(*) as c FROM categories WHERE user_id = ?", (user_id,)).fetchone()["c"]
    if existing == 0:
        for cat in DEFAULT_CATEGORIES:
            conn.execute(
                "INSERT INTO categories (user_id, nom, icon, color, mots_cles, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, cat["nom"], cat["icon"], cat["color"], cat["mots_cles"], datetime.now().isoformat())
            )
    conn.commit()
    conn.close()


def ensure_user_has_categories(user_id: int):
    """Call this on each page load to fix the bug where users have no categories."""
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as c FROM categories WHERE user_id = ?", (user_id,)).fetchone()["c"]
    conn.close()
    if count == 0:
        seed_default_categories(user_id)


# ─── Users ───

def create_user(username: str, password_hash: str, display_name: str, avatar: str = "👤") -> int:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, display_name, avatar, created_at) VALUES (?, ?, ?, ?, ?)",
            (username.lower().strip(), password_hash, display_name.strip(), avatar, datetime.now().isoformat())
        )
        conn.commit()
        uid = cursor.lastrowid
    finally:
        conn.close()
    return uid


def get_user_by_username(username: str) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username.lower().strip(),)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT id, username, display_name, avatar FROM users ORDER BY display_name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Friendships ───

def send_friend_request(from_id: int, to_id: int) -> bool:
    if from_id == to_id:
        return False
    a, b = min(from_id, to_id), max(from_id, to_id)
    conn = get_connection()
    existing = conn.execute("SELECT * FROM friendships WHERE user_a = ? AND user_b = ?", (a, b)).fetchone()
    if existing:
        conn.close()
        return False
    conn.execute(
        "INSERT INTO friendships (user_a, user_b, status, requested_by, created_at) VALUES (?, ?, 'pending', ?, ?)",
        (a, b, from_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return True


def accept_friend_request(friendship_id: int):
    conn = get_connection()
    conn.execute("UPDATE friendships SET status = 'accepted' WHERE id = ?", (friendship_id,))
    conn.commit()
    conn.close()


def reject_friend_request(friendship_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM friendships WHERE id = ?", (friendship_id,))
    conn.commit()
    conn.close()


def remove_friend(friendship_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM friendships WHERE id = ?", (friendship_id,))
    conn.commit()
    conn.close()


def get_friends(user_id: int) -> list[dict]:
    """Return accepted friends with their user info."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT f.id as friendship_id, u.id, u.username, u.display_name, u.avatar
        FROM friendships f
        JOIN users u ON (u.id = CASE WHEN f.user_a = ? THEN f.user_b ELSE f.user_a END)
        WHERE (f.user_a = ? OR f.user_b = ?) AND f.status = 'accepted'
    """, (user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_requests_for_me(user_id: int) -> list[dict]:
    """Friend requests TO me that I haven't accepted."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT f.id as friendship_id, u.id as user_id, u.username, u.display_name, u.avatar
        FROM friendships f
        JOIN users u ON u.id = f.requested_by
        WHERE ((f.user_a = ? OR f.user_b = ?) AND f.requested_by != ? AND f.status = 'pending')
    """, (user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_requests_from_me(user_id: int) -> list[dict]:
    """Friend requests I sent that are still pending."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT f.id as friendship_id, u.id as user_id, u.username, u.display_name, u.avatar
        FROM friendships f
        JOIN users u ON (u.id = CASE WHEN f.user_a = ? THEN f.user_b ELSE f.user_a END)
        WHERE (f.user_a = ? OR f.user_b = ?) AND f.requested_by = ? AND f.status = 'pending'
    """, (user_id, user_id, user_id, user_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_friend_ids(user_id: int) -> list[int]:
    """Just the IDs of accepted friends."""
    return [f["id"] for f in get_friends(user_id)]


# ─── Categories (per user) ───

def get_all_categories(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories WHERE user_id = ? ORDER BY nom", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_names(user_id: int) -> list[str]:
    return [c["nom"] for c in get_all_categories(user_id)]


def get_category_map(user_id: int) -> dict:
    cats = get_all_categories(user_id)
    return {c["nom"]: {"icon": c["icon"], "color": c["color"], "mots_cles": c["mots_cles"]} for c in cats}


def insert_category(user_id: int, nom: str, icon: str, color: str, mots_cles: str) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO categories (user_id, nom, icon, color, mots_cles, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, nom, icon, color, mots_cles, datetime.now().isoformat())
    )
    conn.commit()
    cid = cursor.lastrowid
    conn.close()
    return cid


def delete_category(cat_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()


# ─── Transactions (per user) ───

def insert_transaction(user_id: int, date: str, enseigne: str, montant_total: float,
                       categorie: str, chemin_image: str, articles: list,
                       txn_type: str = "depense", added_by: int | None = None) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO transactions (user_id, date, enseigne, montant_total, categorie, chemin_image, articles, type, added_by, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, date, enseigne, montant_total, categorie, chemin_image,
         json.dumps(articles, ensure_ascii=False), txn_type, added_by, datetime.now().isoformat())
    )
    conn.commit()
    tid = cursor.lastrowid
    conn.close()
    return tid


def get_transactions_by_month(user_id: int, year: int, month: int) -> list[dict]:
    month_str = f"{year}-{month:02d}"
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? AND date LIKE ? ORDER BY date DESC",
        (user_id, f"{month_str}%")
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_all_transactions(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC", (user_id,)).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_monthly_totals(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT substr(date, 1, 7) as mois,
               SUM(CASE WHEN type = 'depense' THEN montant_total ELSE 0 END) as depenses,
               SUM(CASE WHEN type = 'revenu' THEN montant_total ELSE 0 END) as revenus
        FROM transactions WHERE user_id = ?
        GROUP BY mois ORDER BY mois
    """, (user_id,)).fetchall()
    conn.close()
    return [{"mois": r["mois"], "depenses": r["depenses"], "revenus": r["revenus"]} for r in rows]


def delete_transaction(transaction_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


# ─── Recurring (per user) ───

def insert_recurring(user_id: int, enseigne: str, montant: float, categorie: str,
                     txn_type: str, frequence: str, jour: int) -> int:
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO recurring (user_id, enseigne, montant, categorie, type, frequence, jour, actif, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
        (user_id, enseigne, montant, categorie, txn_type, frequence, jour, datetime.now().isoformat())
    )
    conn.commit()
    rid = cursor.lastrowid
    conn.close()
    return rid


def get_all_recurring(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM recurring WHERE user_id = ? AND actif = 1 ORDER BY id", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_recurring(recurring_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM recurring WHERE id = ?", (recurring_id,))
    conn.commit()
    conn.close()


def apply_recurring_for_month(user_id: int, year: int, month: int):
    import calendar
    recurrings = get_all_recurring(user_id)
    if not recurrings:
        return 0
    conn = get_connection()
    count = 0
    _, last_day = calendar.monthrange(year, month)
    for rec in recurrings:
        dates = []
        if rec["frequence"] == "mensuel":
            d = date(year, month, min(rec["jour"], last_day))
            if d <= date.today(): dates.append(d)
        elif rec["frequence"] == "hebdomadaire":
            d = date(year, month, 1)
            while d.month == month:
                if d.weekday() == rec["jour"] and d <= date.today(): dates.append(d)
                d += timedelta(days=1)
        for d in dates:
            ds = d.strftime("%Y-%m-%d")
            ex = conn.execute(
                "SELECT id FROM transactions WHERE user_id=? AND date=? AND enseigne=? AND montant_total=? AND type=?",
                (user_id, ds, rec["enseigne"], rec["montant"], rec["type"])
            ).fetchone()
            if not ex:
                conn.execute(
                    "INSERT INTO transactions (user_id, date, enseigne, montant_total, categorie, chemin_image, articles, type, created_at) VALUES (?,?,?,?,?,'','[]',?,?)",
                    (user_id, ds, rec["enseigne"], rec["montant"], rec["categorie"], rec["type"], datetime.now().isoformat())
                )
                count += 1
    conn.commit()
    conn.close()
    return count


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    if d.get("articles"):
        try: d["articles"] = json.loads(d["articles"])
        except json.JSONDecodeError: d["articles"] = []
    else:
        d["articles"] = []
    if "type" not in d: d["type"] = "depense"
    return d
