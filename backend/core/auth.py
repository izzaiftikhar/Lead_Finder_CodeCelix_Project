import hashlib, hmac, os, re, secrets, threading, time
from datetime import datetime, timedelta, timezone
from . import db
from .config import settings

ITER = 240_000
EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
SESSION_DAYS = 14


class AuthError(Exception):
    def __init__(self, msg, status=400):
        super().__init__(msg)
        self.status = status


def hash_password(pw):
    salt = os.urandom(16)
    return f"pbkdf2${ITER}${salt.hex()}${hashlib.pbkdf2_hmac('sha256', pw.encode(), salt, ITER).hex()}"


def verify_password(pw, stored):
    try:
        _, it, salt, dk = stored.split("$")
        cand = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(it)).hex()
        return hmac.compare_digest(cand, dk)
    except Exception:
        return False


def _public(u):
    return {"id": u["id"], "email": u["email"], "role": u["role"]}


def register(email, password):
    email = (email or "").strip().lower()
    if not EMAIL.match(email):
        raise AuthError("Enter a valid email address.")
    if len(password or "") < 10 or len(password) > 200:
        raise AuthError("Password must be 10-200 characters.")
    first = db.scalar("SELECT COUNT(*) FROM users") == 0
    if not first and not settings.ALLOW_REGISTRATION:
        raise AuthError("Registration is closed.", 403)
    if db.one("SELECT 1 AS x FROM users WHERE email=?", (email,)):
        raise AuthError("That email is already registered.", 409)
    role = "admin" if first or email in settings.ADMIN_EMAILS else "user"
    u = {"id": db.uid(), "email": email, "role": role}
    db.execute("INSERT INTO users(id,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
               (u["id"], email, hash_password(password), role, db.now()))
    return u


_fails, _fl = {}, threading.Lock()


def login(email, password, ip="?"):
    email = (email or "").strip().lower()
    key = f"{ip}|{email}"
    with _fl:
        n, t = _fails.get(key, (0, time.time()))
        if time.time() - t > 300:
            n, t = 0, time.time()
        if n >= 8:
            raise AuthError("Too many attempts. Try again in a few minutes.", 429)
    u = db.one("SELECT * FROM users WHERE email=?", (email,))
    ok = verify_password(password or "", u["password_hash"]) if u else (verify_password("x", hash_password("y")) and False)
    if not ok:
        with _fl:
            _fails[key] = (n + 1, t)
        raise AuthError("Incorrect email or password.", 401)
    with _fl:
        _fails.pop(key, None)
    token = secrets.token_urlsafe(32)
    exp = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat()
    db.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), u["id"], exp))
    return token, _public(u)


def user_from_token(token):
    if not token:
        return None
    h = hashlib.sha256(token.encode()).hexdigest()
    r = db.one("SELECT u.id,u.email,u.role,s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=?", (h,))
    if not r:
        return None
    if r["expires_at"] < datetime.now(timezone.utc).isoformat():
        db.execute("DELETE FROM sessions WHERE token_hash=?", (h,))
        return None
    return _public(r)


def logout(token):
    if token:
        db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
