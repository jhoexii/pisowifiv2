import sqlite3, os, secrets, string
from datetime import datetime, timezone, timedelta

DB_PATH=os.environ.get("PISOWIFI_DB","/var/lib/pisowifi/pisowifi.db")

def conn():
    c=sqlite3.connect(DB_PATH)
    c.row_factory=sqlite3.Row
    return c

def init_db():
    os.makedirs(os.path.dirname(DB_PATH),exist_ok=True)
    with conn() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS vouchers(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          code TEXT UNIQUE NOT NULL, price INTEGER NOT NULL,
          plan TEXT NOT NULL, minutes INTEGER NOT NULL,
          speed_mbps REAL NOT NULL, data_mb INTEGER NOT NULL,
          created_at TEXT NOT NULL, used_at TEXT, expires_at TEXT,
          used_ip TEXT, used_mac TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ip TEXT NOT NULL, mac TEXT, voucher_id INTEGER,
          started_at TEXT NOT NULL, expires_at TEXT NOT NULL,
          data_limit_mb INTEGER NOT NULL, data_used_mb REAL DEFAULT 0,
          speed_mbps REAL NOT NULL, active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS coin_events(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          pulses INTEGER NOT NULL, pesos REAL NOT NULL,
          created_at TEXT NOT NULL
        );
        """)

def make_code():
    a=string.ascii_uppercase+string.digits
    return "-".join("".join(secrets.choice(a) for _ in range(4)) for _ in range(2))

def create_voucher(price,plan,minutes,speed_mbps,data_mb):
    for _ in range(20):
        code=make_code()
        try:
            with conn() as db:
                db.execute("""INSERT INTO vouchers
                (code,price,plan,minutes,speed_mbps,data_mb,created_at)
                VALUES(?,?,?,?,?,?,?)""",
                (code,price,plan,minutes,speed_mbps,data_mb,
                 datetime.now(timezone.utc).isoformat()))
            return code
        except sqlite3.IntegrityError:
            pass
    raise RuntimeError("Could not generate unique voucher")

def get_voucher(code):
    with conn() as db:
        return db.execute("SELECT * FROM vouchers WHERE code=?",(code,)).fetchone()

def activate(code,ip,mac):
    now=datetime.now(timezone.utc)
    with conn() as db:
        v=db.execute("SELECT * FROM vouchers WHERE code=? AND used_at IS NULL",
                     (code,)).fetchone()
        if not v: return None
        exp=now+timedelta(minutes=v["minutes"])
        db.execute("""UPDATE vouchers SET used_at=?,expires_at=?,used_ip=?,used_mac=?
                      WHERE id=?""",
                   (now.isoformat(),exp.isoformat(),ip,mac,v["id"]))
        db.execute("""INSERT INTO sessions
          (ip,mac,voucher_id,started_at,expires_at,data_limit_mb,speed_mbps)
          VALUES(?,?,?,?,?,?,?)""",
                   (ip,mac,v["id"],now.isoformat(),exp.isoformat(),
                    v["data_mb"],v["speed_mbps"]))
        return dict(v)|{"expires_at":exp.isoformat()}

def active_sessions():
    expire_sessions()
    with conn() as db:
        return db.execute("""SELECT s.*,v.code,v.price,v.plan
        FROM sessions s JOIN vouchers v ON v.id=s.voucher_id
        WHERE s.active=1 ORDER BY s.id DESC""").fetchall()

def session_for_ip(ip):
    expire_sessions()
    with conn() as db:
        return db.execute("""SELECT s.*,v.code,v.price,v.plan
        FROM sessions s JOIN vouchers v ON v.id=s.voucher_id
        WHERE s.ip=? AND s.active=1 ORDER BY s.id DESC LIMIT 1""",(ip,)).fetchone()

def expire_sessions():
    now=datetime.now(timezone.utc).isoformat()
    with conn() as db:
        db.execute("UPDATE sessions SET active=0 WHERE active=1 AND expires_at<=?",(now,))

def add_coin_event(pulses,pesos):
    with conn() as db:
        db.execute("INSERT INTO coin_events(pulses,pesos,created_at) VALUES(?,?,?)",
                   (pulses,pesos,datetime.now(timezone.utc).isoformat()))

def stats():
    with conn() as db:
        return {
          "vouchers":db.execute("SELECT COUNT(*) n FROM vouchers").fetchone()["n"],
          "used":db.execute("SELECT COUNT(*) n FROM vouchers WHERE used_at IS NOT NULL").fetchone()["n"],
          "active":db.execute("SELECT COUNT(*) n FROM sessions WHERE active=1").fetchone()["n"],
          "coins":db.execute("SELECT COALESCE(SUM(pesos),0) n FROM coin_events").fetchone()["n"]
        }
