"""
Pro VPS Panel - Railway deployable (single file, no templates folder needed)
Owner: shappno / shappno_codex
"""
import os, json, time, shutil, subprocess, threading, secrets
from collections import deque
from pathlib import Path
from functools import wraps
from flask import (
    Flask, request, redirect, url_for, session,
    render_template_string, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"
PRICING_FILE = DATA_DIR / "pricing.json"
FILES_ROOT = APP_DIR / "user_files"
DATA_DIR.mkdir(exist_ok=True)
FILES_ROOT.mkdir(exist_ok=True)

OWNER_USER = "DARKxERA"
OWNER_PASS = "DARKxERA870"

DEFAULT_PRICING = {
    "currency": "₹",
    "contact": "Telegram: @DARKxERA",
    "plans": [
        {"name": "Starter", "duration": "24 Hours",  "price": "49",  "features": "1 file run, 512MB RAM, Real-time logs"},
        {"name": "Basic",   "duration": "7 Days",    "price": "199", "features": "Multi-file upload, pip/npm install, 24/7 uptime"},
        {"name": "Pro",     "duration": "30 Days",   "price": "599", "features": "Unlimited modules, Priority support, Auto-restart"},
        {"name": "Premium", "duration": "Lifetime",  "price": "1999","features": "All features, Custom domain, Dedicated help"},
    ],
}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024


# ============================================================
#                      UI (CSS + shell)
# ============================================================

CSS = """
:root{
  --bg:#05060a; --bg2:#0a0c14; --card:rgba(17,19,29,.78);
  --border:rgba(255,255,255,.07); --border-hi:rgba(255,255,255,.14);
  --txt:#e8ecf5; --txt-dim:#9aa2b8; --txt-mute:#646b82;
  --p1:#6d5cff; --p2:#12b8ff; --p3:#ff5cb1;
  --grad:linear-gradient(135deg,#6d5cff 0%,#12b8ff 55%,#ff5cb1 100%);
  --ok:#22c55e; --warn:#f59e0b; --err:#ef4444;
  --r:14px;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{min-height:100%}
body{
  font-family:'El Messiri',system-ui,-apple-system,"Segoe UI",sans-serif;
  background:var(--bg); color:var(--txt); line-height:1.6;
  min-height:100vh; overflow-x:hidden; display:flex; flex-direction:column;
  -webkit-font-smoothing:antialiased;
}
a{color:inherit;text-decoration:none}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.86em;
  background:rgba(109,92,255,.14);padding:2px 7px;border-radius:6px;color:#bcaeff}
em{font-style:normal}

/* Background */
.bg-orbs{position:fixed;inset:0;z-index:-1;overflow:hidden;pointer-events:none}
.orb{position:absolute;border-radius:50%;filter:blur(110px);opacity:.35;animation:float 22s ease-in-out infinite}
.orb-1{width:600px;height:600px;background:radial-gradient(circle,#6d5cff,transparent 70%);top:-200px;left:-180px}
.orb-2{width:520px;height:520px;background:radial-gradient(circle,#12b8ff,transparent 70%);bottom:-200px;right:-160px;animation-delay:-8s}
.orb-3{width:420px;height:420px;background:radial-gradient(circle,#ff5cb1,transparent 70%);top:45%;left:60%;animation-delay:-15s;opacity:.22}
@keyframes float{0%,100%{transform:translate(0,0) scale(1)}50%{transform:translate(50px,-40px) scale(1.07)}}

/* Navbar */
.navbar{position:sticky;top:0;z-index:50;backdrop-filter:blur(20px);
  background:rgba(5,6,10,.78);border-bottom:1px solid var(--border)}
.nav-inner{max-width:1200px;margin:0 auto;padding:16px 26px;
  display:flex;align-items:center;justify-content:space-between;gap:20px}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:1.28rem}
.brand-icon{font-size:1.45rem;filter:drop-shadow(0 0 14px rgba(109,92,255,.8))}
.brand-text em{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.nav-links{display:flex;align-items:center;gap:8px;font-weight:600}
.nav-links a{padding:8px 16px;border-radius:10px;color:var(--txt-dim);transition:.22s;font-size:.96rem}
.nav-links a:hover{color:var(--txt);background:rgba(255,255,255,.05)}
.btn-primary-sm{background:var(--grad);color:#05060a !important;padding:9px 20px !important;border-radius:10px;font-weight:700}
.btn-ghost{color:var(--txt-mute) !important}

/* Layout */
.main{flex:1;max-width:1200px;width:100%;margin:0 auto;padding:44px 26px}
.footer{text-align:center;padding:34px 20px;color:var(--txt-mute);font-size:.88rem;
  border-top:1px solid var(--border);margin-top:50px}
.footer strong{color:var(--txt-dim)}

/* Buttons */
.btn-primary{display:inline-flex;align-items:center;gap:8px;background:var(--grad);
  color:#05060a !important;font-weight:700;padding:14px 30px;border-radius:13px;
  border:none;cursor:pointer;font-family:inherit;font-size:1rem;
  box-shadow:0 12px 34px -12px rgba(109,92,255,.75);transition:.25s}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 18px 44px -12px rgba(109,92,255,.95)}
.btn-ghost-lg{display:inline-flex;align-items:center;gap:8px;padding:14px 28px;border-radius:13px;
  border:1px solid var(--border-hi);color:var(--txt);font-weight:600;
  background:rgba(255,255,255,.03);transition:.25s}
.btn-ghost-lg:hover{background:rgba(255,255,255,.07);border-color:var(--p1)}
.btn-sm{padding:8px 16px;font-size:.88rem;border-radius:10px;border:none;cursor:pointer;
  font-family:inherit;font-weight:700;transition:.2s}
.btn-ok{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff}
.btn-err{background:linear-gradient(135deg,#ef4444,#b91c1c);color:#fff}
.btn-warn{background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff}
.btn-info{background:linear-gradient(135deg,#6d5cff,#12b8ff);color:#05060a}
.btn-sm:hover{transform:translateY(-1px);filter:brightness(1.1)}

/* Cards */
.card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:28px;backdrop-filter:blur(16px);box-shadow:0 22px 55px -22px rgba(0,0,0,.65)}
.card h2{font-size:1.35rem;margin-bottom:6px}
.card-sub{color:var(--txt-mute);font-size:.9rem;margin-bottom:20px}

/* Hero */
.hero{text-align:center;padding:64px 0 30px}
.badge{display:inline-block;padding:8px 18px;border-radius:999px;
  background:rgba(109,92,255,.12);border:1px solid rgba(109,92,255,.32);
  color:#bcaeff;font-size:.86rem;font-weight:600;margin-bottom:22px}
.hero h1{font-size:clamp(2rem,5vw,3.5rem);font-weight:700;line-height:1.15;
  letter-spacing:-.02em;max-width:920px;margin:0 auto 20px}
.grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero-sub{color:var(--txt-dim);font-size:1.1rem;max-width:640px;margin:0 auto 34px}
.hero-cta{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}
.hero-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
  gap:16px;max-width:820px;margin:60px auto 0}
.hero-stats>div{background:var(--card);border:1px solid var(--border);
  border-radius:12px;padding:20px;backdrop-filter:blur(10px)}
.hero-stats strong{display:block;font-size:1.55rem;
  background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero-stats span{color:var(--txt-mute);font-size:.85rem}

/* Features */
.section-title{text-align:center;font-size:1.9rem;margin:74px 0 40px;font-weight:700}
.feature-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:22px}
.feature-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:30px;backdrop-filter:blur(16px);transition:.3s}
.feature-card:hover{transform:translateY(-5px);border-color:var(--border-hi);
  box-shadow:0 26px 55px -22px rgba(109,92,255,.45)}
.fc-icon{font-size:2.3rem;margin-bottom:14px}
.feature-card h3{font-size:1.15rem;margin-bottom:10px}
.feature-card p{color:var(--txt-dim);font-size:.93rem}

/* Pricing */
.pricing-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:22px;margin-top:30px}
.price-card{background:var(--card);border:1px solid var(--border);border-radius:20px;
  padding:32px 26px;backdrop-filter:blur(16px);position:relative;overflow:hidden;transition:.3s}
.price-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--grad)}
.price-card:hover{transform:translateY(-6px);border-color:var(--border-hi);
  box-shadow:0 32px 65px -22px rgba(109,92,255,.55)}
.price-card.popular{border-color:rgba(109,92,255,.5);transform:scale(1.03)}
.popular-tag{position:absolute;top:14px;right:-32px;background:var(--grad);color:#05060a;
  padding:5px 42px;font-size:.72rem;font-weight:700;transform:rotate(38deg);letter-spacing:.5px}
.price-name{font-size:1.22rem;font-weight:700;margin-bottom:4px}
.price-dur{color:var(--txt-mute);font-size:.86rem;margin-bottom:20px}
.price-amt{font-size:2.5rem;font-weight:700;line-height:1;
  background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.price-feat{list-style:none;margin:22px 0;padding:0}
.price-feat li{padding:8px 0;color:var(--txt-dim);font-size:.9rem;
  display:flex;gap:8px;align-items:flex-start}
.price-feat li::before{content:'✓';color:var(--ok);font-weight:700;flex-shrink:0}

/* Forms */
.form-row{display:flex;flex-direction:column;gap:8px;margin-bottom:18px}
.form-row label{font-size:.88rem;font-weight:600;color:var(--txt-dim)}
.input,select,textarea{width:100%;padding:13px 16px;border-radius:11px;
  border:1px solid var(--border);background:rgba(8,10,18,.75);
  color:var(--txt);font-family:inherit;font-size:.96rem;transition:.22s;outline:none}
.input:focus,select:focus,textarea:focus{border-color:var(--p1);
  box-shadow:0 0 0 3px rgba(109,92,255,.18)}
.input::placeholder{color:var(--txt-mute)}

/* Auth */
.auth-wrap{max-width:420px;margin:60px auto}
.auth-wrap .card{padding:38px 32px}
.auth-title{font-size:1.65rem;text-align:center;margin-bottom:6px}
.auth-sub{text-align:center;color:var(--txt-mute);margin-bottom:26px;font-size:.94rem}
.alert{padding:12px 16px;border-radius:10px;font-size:.9rem;margin-bottom:18px}
.alert-err{background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.35);color:#fca5a5}

/* Dashboard */
.dash-head{display:flex;flex-wrap:wrap;gap:16px;justify-content:space-between;
  align-items:center;margin-bottom:28px}
.dash-title{font-size:1.6rem;font-weight:700}
.dash-title span{font-size:.9rem;color:var(--txt-mute);font-weight:400;display:block}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media(max-width:860px){.grid-2{grid-template-columns:1fr}}
.pill{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:999px;
  font-size:.8rem;font-weight:600}
.pill-ok{background:rgba(34,197,94,.14);color:#4ade80;border:1px solid rgba(34,197,94,.3)}
.pill-off{background:rgba(107,114,128,.14);color:#9ca3af;border:1px solid rgba(107,114,128,.3)}
.pill-warn{background:rgba(245,158,11,.14);color:#fbbf24;border:1px solid rgba(245,158,11,.3)}
.dot{width:8px;height:8px;border-radius:50%;background:currentColor;
  box-shadow:0 0 8px currentColor;animation:pulse 1.8s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

/* File list */
.file-list{list-style:none;padding:0;margin:0}
.file-list li{display:flex;justify-content:space-between;align-items:center;
  padding:12px 14px;border-radius:10px;border:1px solid var(--border);
  background:rgba(255,255,255,.02);margin-bottom:8px;gap:10px;flex-wrap:wrap}
.file-list .fname{font-weight:600;word-break:break-all;font-size:.92rem}
.file-actions{display:flex;gap:8px;flex-wrap:wrap}

/* Terminal */
.terminal{background:#03040a;border:1px solid var(--border);border-radius:12px;
  padding:16px;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  font-size:.8rem;line-height:1.55;color:#b8f0c8;
  height:340px;overflow-y:auto;white-space:pre-wrap;word-break:break-word}
.terminal::-webkit-scrollbar{width:8px}
.terminal::-webkit-scrollbar-thumb{background:rgba(109,92,255,.4);border-radius:8px}

/* Toast */
.toast{position:fixed;bottom:26px;right:26px;padding:14px 22px;border-radius:12px;
  background:rgba(17,19,29,.97);border:1px solid var(--border-hi);color:var(--txt);
  font-weight:600;opacity:0;transform:translateY(12px);transition:.3s;z-index:200;
  box-shadow:0 22px 44px -12px rgba(0,0,0,.75);max-width:340px;font-size:.92rem}
.toast.show{opacity:1;transform:translateY(0)}
.toast-ok{border-color:rgba(34,197,94,.5)}
.toast-err{border-color:rgba(239,68,68,.5)}

/* Table */
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{padding:12px 10px;text-align:left;border-bottom:1px solid var(--border)}
th{color:var(--txt-mute);font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.4px}
td{color:var(--txt-dim)}
td strong{color:var(--txt)}

/* Tabs */
.tabs{display:flex;gap:6px;margin-bottom:22px;flex-wrap:wrap;border-bottom:1px solid var(--border)}
.tab{padding:11px 20px;border-radius:12px 12px 0 0;background:transparent;border:none;
  color:var(--txt-mute);font-family:inherit;font-weight:600;cursor:pointer;font-size:.94rem;transition:.2s}
.tab:hover{color:var(--txt)}
.tab.active{color:var(--txt);background:rgba(109,92,255,.12);border-bottom:2px solid var(--p1)}
.tab-panel{display:none}
.tab-panel.active{display:block;animation:fade .3s}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

@media(max-width:640px){
  .main{padding:26px 16px}
  .nav-inner{padding:14px 16px}
  .nav-links a{padding:7px 12px;font-size:.9rem}
  .card{padding:22px}
}
"""

NAV_TPL = """
<nav class="navbar">
  <div class="nav-inner">
    <a href="{{ url_for('home') }}" class="brand">
      <span class="brand-icon">⚡</span>
      <span class="brand-text">Pro<em>VPS</em></span>
    </a>
    <div class="nav-links">
      {% if session.get('role') == 'owner' %}
        <a href="{{ url_for('owner_dashboard') }}">Dashboard</a>
        <a href="{{ url_for('logout') }}" class="btn-ghost">Logout</a>
      {% elif session.get('role') == 'user' %}
        <a href="{{ url_for('user_dashboard') }}">My Server</a>
        <a href="{{ url_for('logout') }}" class="btn-ghost">Logout</a>
      {% else %}
        <a href="{{ url_for('landing') }}">Home</a>
        <a href="{{ url_for('pricing_page') }}">Pricing</a>
        <a href="{{ url_for('login') }}" class="btn-primary-sm">Login</a>
      {% endif %}
    </div>
  </div>
</nav>
"""

BASE_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=El+Messiri:wght@400;600;700&display=swap" rel="stylesheet">
<style>__CSS__</style>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>">
</head>
<body>
<div class="bg-orbs">
  <div class="orb orb-1"></div><div class="orb orb-2"></div><div class="orb orb-3"></div>
</div>
__NAV__
<main class="main">
__CONTENT__
</main>
<footer class="footer">
  <p>© 2025 Pro VPS Panel · Built for <strong>shappno / shappno_codex</strong></p>
</footer>
<script>
function toast(msg, type){
  type = type || 'info';
  var el = document.createElement('div');
  el.className = 'toast toast-' + type;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(function(){ el.classList.add('show'); }, 10);
  setTimeout(function(){
    el.classList.remove('show');
    setTimeout(function(){ el.remove(); }, 300);
  }, 2600);
}
</script>
__SCRIPTS__
</body>
</html>
"""


def render_page(title, content_tpl, extra_scripts="", **ctx):
    """Render a full page by rendering content + nav separately, then injecting into shell."""
    content = render_template_string(content_tpl, **ctx)
    nav = render_template_string(NAV_TPL)
    scripts = render_template_string(extra_scripts, **ctx) if extra_scripts else ""
    html = (BASE_SHELL
            .replace("__TITLE__", title)
            .replace("__CSS__", CSS)
            .replace("__NAV__", nav)
            .replace("__CONTENT__", content)
            .replace("__SCRIPTS__", scripts))
    return html


# ============================================================
#                    STORAGE
# ============================================================
_lock = threading.Lock()

def load_users():
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text())
    except Exception:
        return {}

def save_users(u):
    with _lock:
        USERS_FILE.write_text(json.dumps(u, indent=2))

def load_pricing():
    if not PRICING_FILE.exists():
        save_pricing(DEFAULT_PRICING)
        return DEFAULT_PRICING
    try:
        return json.loads(PRICING_FILE.read_text())
    except Exception:
        return DEFAULT_PRICING

def save_pricing(p):
    with _lock:
        PRICING_FILE.write_text(json.dumps(p, indent=2))

def user_dir(username):
    d = FILES_ROOT / username
    d.mkdir(parents=True, exist_ok=True)
    return d


# ============================================================
#                    PROCESS MANAGER
# ============================================================
PROCS = {}

def _reader(username, proc):
    buf = PROCS[username]["logs"]
    try:
        for line in iter(proc.stdout.readline, b""):
            try:
                txt = line.decode("utf-8", errors="replace").rstrip()
            except Exception:
                txt = str(line)
            buf.append(f"[{time.strftime('%H:%M:%S')}] {txt}")
    except Exception as e:
        buf.append(f"[reader-error] {e}")
    finally:
        buf.append(f"[exit] process ended with code {proc.poll()}")

def start_process(username, filename):
    stop_process(username)
    udir = user_dir(username)
    fpath = udir / filename
    if not fpath.exists():
        return False, "File not found"
    ext = fpath.suffix.lower()
    if ext == ".py":
        cmd = ["python", "-u", str(fpath)]
    elif ext in (".js", ".mjs", ".cjs"):
        cmd = ["node", str(fpath)]
    elif ext == ".sh":
        cmd = ["bash", str(fpath)]
    else:
        return False, f"Unsupported file type: {ext}"
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(udir),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1,
        )
    except FileNotFoundError as e:
        return False, f"Runtime not installed: {e}"
    logs = deque(maxlen=2000)
    logs.append(f"[start] {' '.join(cmd)}")
    PROCS[username] = {"proc": proc, "logs": logs, "file": filename}
    t = threading.Thread(target=_reader, args=(username, proc), daemon=True)
    t.start()
    PROCS[username]["thread"] = t
    return True, "started"

def stop_process(username):
    info = PROCS.get(username)
    if not info:
        return False
    p = info["proc"]
    if p.poll() is None:
        try:
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
        except Exception:
            pass
        info["logs"].append("[stop] process terminated")
    return True

def is_running(username):
    info = PROCS.get(username)
    return bool(info and info["proc"].poll() is None)

def get_logs(username):
    info = PROCS.get(username)
    return list(info["logs"]) if info else []


# ============================================================
#                    INSTALL MODULE
# ============================================================
INSTALL_LOGS = {}

def run_install(username, command):
    parts = command.strip().split()
    if not parts:
        return False, "empty command"
    if parts[0] not in ("pip", "pip3", "npm"):
        return False, "Only 'pip install <pkg>' or 'npm install <pkg>' allowed"
    if len(parts) < 3 or parts[1] != "install":
        return False, "Format: pip install <module>  OR  npm install <module>"
    if any(c in command for c in [";", "&", "|", "`", "$(", ">"]):
        return False, "Invalid characters"
    logs = INSTALL_LOGS.setdefault(username, deque(maxlen=1000))
    logs.append(f"[install] $ {command}")
    cwd = str(user_dir(username))
    def worker():
        try:
            p = subprocess.Popen(parts, cwd=cwd,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in iter(p.stdout.readline, b""):
                logs.append(line.decode("utf-8", errors="replace").rstrip())
            p.wait()
            logs.append(f"[install] finished with code {p.returncode}")
        except Exception as e:
            logs.append(f"[install-error] {e}")
    threading.Thread(target=worker, daemon=True).start()
    return True, "installing"


# ============================================================
#                       AUTH
# ============================================================
def is_owner():
    return session.get("role") == "owner"

def current_user():
    return session.get("username")

def user_valid(username):
    users = load_users()
    u = users.get(username)
    if not u:
        return False, "User not found"
    if u.get("expires_at") and time.time() > u["expires_at"]:
        del users[username]
        save_users(users)
        stop_process(username)
        return False, "Account expired"
    return True, u

def require_owner(f):
    @wraps(f)
    def w(*a, **kw):
        if not is_owner():
            return redirect(url_for("login"))
        return f(*a, **kw)
    return w

def require_user(f):
    @wraps(f)
    def w(*a, **kw):
        u = current_user()
        if not u or session.get("role") != "user":
            return redirect(url_for("login"))
        ok, _ = user_valid(u)
        if not ok:
            session.clear()
            return redirect(url_for("login"))
        return f(*a, **kw)
    return w


# ============================================================
#                    PAGE TEMPLATES
# ============================================================

LANDING_TPL = """
<section class="hero">
  <span class="badge">🚀 Premium VPS Hosting</span>
  <h1>Run your <span class="grad">Python</span>, <span class="grad">Node.js</span> &amp; <span class="grad">Shell</span> scripts 24/7</h1>
  <p class="hero-sub">A clean, powerful control panel with live logs, module installer, and instant deployment — all from your browser.</p>
  <div class="hero-cta">
    <a href="{{ url_for('pricing_page') }}" class="btn-primary">View Pricing</a>
    <a href="{{ url_for('login') }}" class="btn-ghost-lg">Client Login →</a>
  </div>
  <div class="hero-stats">
    <div><strong>99.9%</strong><span>Uptime</span></div>
    <div><strong>200MB</strong><span>Upload Limit</span></div>
    <div><strong>24/7</strong><span>Auto Restart</span></div>
    <div><strong>1-click</strong><span>Deploy</span></div>
  </div>
</section>

<section>
  <h2 class="section-title">Everything you need to <span class="grad">ship fast</span></h2>
  <div class="feature-grid">
    <div class="feature-card"><div class="fc-icon">🐍</div><h3>Multi-Runtime</h3>
      <p>Run <code>.py</code>, <code>.js</code>, and <code>.sh</code> files with a single click. Python, Node.js and Bash supported.</p></div>
    <div class="feature-card"><div class="fc-icon">📡</div><h3>Live Logs</h3>
      <p>Real-time stdout/stderr streaming so you always know exactly what your script is doing.</p></div>
    <div class="feature-card"><div class="fc-icon">📦</div><h3>Module Installer</h3>
      <p>Install Python packages with <code>pip</code> or Node modules with <code>npm</code> — right from the panel.</p></div>
    <div class="feature-card"><div class="fc-icon">🔐</div><h3>Per-User Isolation</h3>
      <p>Every client gets their own sandboxed directory, tokens, and process slot. No cross-access.</p></div>
    <div class="feature-card"><div class="fc-icon">⚡</div><h3>Instant Deploy</h3>
      <p>Upload, start, restart, or stop with one tap. Zero downtime workflow.</p></div>
    <div class="feature-card"><div class="fc-icon">🎛️</div><h3>Owner Control</h3>
      <p>Create users, set expiry, extend time, and edit pricing plans in real time.</p></div>
  </div>
</section>
"""

PRICING_TPL = """
<h1 class="section-title" style="margin-top:10px">Simple, <span class="grad">honest pricing</span></h1>
<p style="text-align:center;color:var(--txt-dim);max-width:600px;margin:0 auto 10px">
  Pick a plan and start hosting your scripts in minutes.
</p>
<div class="pricing-grid">
  {% for p in pricing.plans %}
  <div class="price-card {% if loop.index == 3 %}popular{% endif %}">
    {% if loop.index == 3 %}<div class="popular-tag">POPULAR</div>{% endif %}
    <div class="price-name">{{ p.name }}</div>
    <div class="price-dur">{{ p.duration }}</div>
    <div class="price-amt">{{ pricing.currency }}{{ p.price }}</div>
    <ul class="price-feat">
      {% for f in p.features.split(',') %}
        {% if f.strip() %}<li>{{ f.strip() }}</li>{% endif %}
      {% endfor %}
    </ul>
    <a href="{{ url_for('login') }}" class="btn-primary" style="width:100%;justify-content:center">Get Started</a>
  </div>
  {% endfor %}
</div>
<div style="text-align:center;margin-top:40px;color:var(--txt-mute)">
  Need help? <strong style="color:var(--txt-dim)">{{ pricing.contact }}</strong>
</div>
"""

LOGIN_TPL = """
<div class="auth-wrap">
  <div class="card">
    <h1 class="auth-title">Welcome back</h1>
    <p class="auth-sub">Sign in to access your VPS panel</p>
    {% if error %}<div class="alert alert-err">{{ error }}</div>{% endif %}
    <form method="post">
      <div class="form-row">
        <label>Username</label>
        <input class="input" name="username" placeholder="your username" required autofocus>
      </div>
      <div class="form-row">
        <label>Password</label>
        <input class="input" name="password" type="password" placeholder="••••••••" required>
      </div>
      <button class="btn-primary" style="width:100%;justify-content:center;margin-top:8px">Sign In →</button>
    </form>
    <p style="text-align:center;margin-top:20px;color:var(--txt-mute);font-size:.9rem">
      New here? <a href="{{ url_for('pricing_page') }}" style="color:#bcaeff">View plans</a>
    </p>
  </div>
</div>
"""

USER_TPL = """
<div class="dash-head">
  <div class="dash-title">
    Hey, <span class="grad">{{ username }}</span>
    <span>
      {% if running %}<span class="pill pill-ok"><span class="dot"></span>Running · {{ running_file }}</span>
      {% else %}<span class="pill pill-off">● Stopped</span>{% endif %}
    </span>
  </div>
  <div style="text-align:right;color:var(--txt-mute);font-size:.86rem">
    Expires: <strong style="color:var(--txt-dim)" id="expires-at" data-ts="{{ expires_at }}">—</strong>
  </div>
</div>

<div class="tabs">
  <button class="tab active" data-tab="files">📁 Files</button>
  <button class="tab" data-tab="control">🎛️ Control</button>
  <button class="tab" data-tab="logs">📡 Live Logs</button>
  <button class="tab" data-tab="install">📦 Install Modules</button>
</div>

<div class="tab-panel active" id="panel-files">
  <div class="card" style="margin-bottom:22px">
    <h2>Upload Files</h2>
    <p class="card-sub">Supported: .py, .js, .mjs, .cjs, .sh — max 200MB total</p>
    <form method="post" action="{{ url_for('upload') }}" enctype="multipart/form-data">
      <div class="form-row"><input class="input" type="file" name="files" multiple required></div>
      <button class="btn-primary">⬆ Upload</button>
    </form>
  </div>
  <div class="card">
    <h2>Your Files ({{ files|length }})</h2>
    <p class="card-sub">Click Run to start a file. Only one file runs at a time per user.</p>
    {% if files %}
    <ul class="file-list">
      {% for f in files %}
      <li>
        <span class="fname">📄 {{ f }}</span>
        <div class="file-actions">
          <button class="btn-sm btn-ok" onclick="startFile('{{ f }}')">▶ Run</button>
          <a class="btn-sm btn-info" href="{{ url_for('file_view', name=f) }}" target="_blank" style="text-decoration:none">👁 View</a>
          <form method="post" action="{{ url_for('file_delete', name=f) }}" style="display:inline" onsubmit="return confirm('Delete {{ f }}?')">
            <button class="btn-sm btn-err">🗑</button>
          </form>
        </div>
      </li>
      {% endfor %}
    </ul>
    {% else %}
    <p style="color:var(--txt-mute);padding:20px 0">No files yet. Upload your first script above.</p>
    {% endif %}
  </div>
</div>

<div class="tab-panel" id="panel-control">
  <div class="card">
    <h2>Process Control</h2>
    <p class="card-sub">Start, stop, or restart your running script.</p>
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      <button class="btn-sm btn-ok"   onclick="ctl('restart')">🔄 Restart</button>
      <button class="btn-sm btn-warn" onclick="ctl('stop')">⏹ Stop</button>
      <button class="btn-sm btn-err"  onclick="ctl('delete')">🗑 Kill &amp; Clear</button>
    </div>
    <div style="margin-top:26px">
      <strong>Status:</strong>
      <span id="status-text" style="color:var(--txt-dim);margin-left:6px">Loading…</span>
    </div>
  </div>
</div>

<div class="tab-panel" id="panel-logs">
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:10px">
      <h2 style="margin:0">📡 Live Output</h2>
      <span class="pill" id="log-status">—</span>
    </div>
    <div class="terminal" id="term">Waiting for logs…</div>
    <div style="margin-top:14px;color:var(--txt-mute);font-size:.82rem">Auto-refreshing every 1.5s · last 2000 lines kept</div>
  </div>
</div>

<div class="tab-panel" id="panel-install">
  <div class="card">
    <h2>📦 Install Modules</h2>
    <p class="card-sub">Allowed: <code>pip install &lt;pkg&gt;</code> or <code>npm install &lt;pkg&gt;</code></p>
    <form id="install-form" onsubmit="return doInstall(event)">
      <div class="form-row"><input class="input" id="install-cmd" placeholder="pip install requests" required></div>
      <button class="btn-primary">▶ Install</button>
    </form>
    <div class="terminal" id="install-term" style="margin-top:18px;height:260px;color:#bcaeff">Install log will appear here…</div>
  </div>
</div>
"""

USER_SCRIPTS = """
<script>
document.querySelectorAll('.tab').forEach(function(t){
  t.addEventListener('click', function(){
    document.querySelectorAll('.tab').forEach(function(x){ x.classList.remove('active'); });
    document.querySelectorAll('.tab-panel').forEach(function(x){ x.classList.remove('active'); });
    t.classList.add('active');
    document.getElementById('panel-' + t.dataset.tab).classList.add('active');
  });
});

var expEl = document.getElementById('expires-at');
if(expEl){
  var ts = parseFloat(expEl.dataset.ts);
  expEl.textContent = ts > 0 ? new Date(ts*1000).toLocaleString() : 'Lifetime';
}

async function startFile(name){
  var r = await fetch('{{ url_for("server_start") }}', {method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:'file=' + encodeURIComponent(name)});
  var j = await r.json();
  toast(j.msg, j.ok ? 'ok' : 'err');
  refresh();
}

async function ctl(action){
  if(action==='stop' && !confirm('Stop the running process?')) return;
  if(action==='delete' && !confirm('Kill process and clear logs?')) return;
  var map = {
    restart: '{{ url_for("server_restart") }}',
    stop: '{{ url_for("server_stop") }}',
    delete: '{{ url_for("server_delete") }}'
  };
  var rr = await fetch(map[action], {method:'POST'});
  var j = await rr.json();
  toast(j.msg || 'done', j.ok ? 'ok' : 'err');
  refresh();
}

async function doInstall(e){
  e.preventDefault();
  var cmd = document.getElementById('install-cmd').value;
  var r = await fetch('{{ url_for("install") }}', {method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:'command=' + encodeURIComponent(cmd)});
  var j = await r.json();
  toast(j.msg, j.ok ? 'ok' : 'err');
  return false;
}

var term = document.getElementById('term');
var installTerm = document.getElementById('install-term');
var logStatus = document.getElementById('log-status');
var statusText = document.getElementById('status-text');

async function refresh(){
  try{
    var r = await fetch('{{ url_for("logs_api") }}');
    var j = await r.json();
    logStatus.textContent = j.running ? '● Running' : '● Stopped';
    logStatus.className = 'pill ' + (j.running ? 'pill-ok' : 'pill-off');
    if(statusText) statusText.textContent = j.running ? ('Running: ' + j.file) : 'Stopped';
    if(term){ term.textContent = j.logs.length ? j.logs.join('\\n') : 'No logs yet.'; term.scrollTop = term.scrollHeight; }
    if(installTerm){
      installTerm.textContent = j.install.length ? j.install.join('\\n') : 'Install log will appear here…';
      installTerm.scrollTop = installTerm.scrollHeight;
    }
  } catch(e) {}
}
refresh();
setInterval(refresh, 1500);
</script>
"""

OWNER_TPL = """
<div class="dash-head">
  <div class="dash-title">Owner Panel <span>Full control over users, plans &amp; billing</span></div>
</div>

<div class="tabs">
  <button class="tab active" data-tab="users">👥 Users</button>
  <button class="tab" data-tab="create">➕ Create User</button>
  <button class="tab" data-tab="pricing">💰 Pricing</button>
</div>

<div class="tab-panel active" id="panel-users">
  <div class="card">
    <h2>Active Users ({{ users|length }})</h2>
    <p class="card-sub">Manage expiry and share auto-login links.</p>
    {% if users %}
    <div style="overflow-x:auto">
    <table>
      <thead><tr><th>Username</th><th>Status</th><th>Expires</th><th>Auto-Login Link</th><th>Actions</th></tr></thead>
      <tbody>
      {% for uname, info in users.items() %}
        {% set exp = info.expires_at or 0 %}
        {% set expired = exp > 0 and now > exp %}
        <tr>
          <td><strong>{{ uname }}</strong></td>
          <td>
            {% if expired %}<span class="pill pill-warn">Expired</span>
            {% elif exp == 0 %}<span class="pill pill-ok">Lifetime</span>
            {% else %}<span class="pill pill-ok"><span class="dot"></span>Active</span>{% endif %}
          </td>
          <td>{% if exp == 0 %}Never{% else %}<span data-ts="{{ exp }}" class="ts"></span>{% endif %}</td>
          <td><input class="input" readonly style="font-size:.76rem;padding:8px 10px;min-width:220px"
                value="{{ base_url }}/auto/{{ info.token }}" onclick="this.select()"></td>
          <td>
            <form method="post" action="{{ url_for('owner_extend', username=uname) }}" style="display:inline">
              <input class="input" name="hours" value="24" style="width:70px;padding:6px;display:inline-block;font-size:.82rem">
              <button class="btn-sm btn-info">+Extend</button>
            </form>
            <form method="post" action="{{ url_for('owner_delete', username=uname) }}" style="display:inline"
                  onsubmit="return confirm('Delete {{ uname }} and all files?')">
              <button class="btn-sm btn-err">🗑 Delete</button>
            </form>
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
    </div>
    {% else %}
    <p style="color:var(--txt-mute);padding:20px 0">No users yet. Create one from the "Create User" tab.</p>
    {% endif %}
  </div>
</div>

<div class="tab-panel" id="panel-create">
  <div class="card" style="max-width:560px">
    <h2>Create New User</h2>
    <p class="card-sub">Set duration in hours (0 = lifetime, 24 = 1 day, 168 = 7 days, 720 = 30 days)</p>
    <form method="post" action="{{ url_for('owner_create') }}">
      <div class="form-row"><label>Username</label>
        <input class="input" name="username" placeholder="e.g. client01" required></div>
      <div class="form-row"><label>Password</label>
        <input class="input" name="password" placeholder="strong password" required></div>
      <div class="form-row"><label>Duration (hours)</label>
        <input class="input" name="hours" type="number" value="24" min="0" step="1"></div>
      <button class="btn-primary">✨ Create User</button>
    </form>
  </div>
</div>

<div class="tab-panel" id="panel-pricing">
  <div class="card">
    <h2>Edit Pricing Plans</h2>
    <p class="card-sub">These plans show on the public /pricing page.</p>
    <form method="post" action="{{ url_for('owner_pricing') }}">
      <div class="grid-2" style="margin-bottom:14px">
        <div class="form-row"><label>Currency Symbol</label>
          <input class="input" name="currency" value="{{ pricing.currency }}"></div>
        <div class="form-row"><label>Contact Info</label>
          <input class="input" name="contact" value="{{ pricing.contact }}"></div>
      </div>
      {% for p in pricing.plans %}
      <div style="border:1px solid var(--border);border-radius:12px;padding:18px;margin-bottom:14px">
        <div class="grid-2" style="gap:12px">
          <div class="form-row"><label>Plan Name</label><input class="input" name="p_name" value="{{ p.name }}"></div>
          <div class="form-row"><label>Duration</label><input class="input" name="p_duration" value="{{ p.duration }}"></div>
          <div class="form-row"><label>Price</label><input class="input" name="p_price" value="{{ p.price }}"></div>
          <div class="form-row"><label>Features (comma-separated)</label><input class="input" name="p_features" value="{{ p.features }}"></div>
        </div>
      </div>
      {% endfor %}
      <div id="new-plans"></div>
      <button type="button" class="btn-ghost-lg" onclick="addPlan()" style="margin-right:10px">+ Add Plan</button>
      <button class="btn-primary">💾 Save Plans</button>
    </form>
  </div>
</div>
"""

OWNER_SCRIPTS = """
<script>
document.querySelectorAll('.tab').forEach(function(t){
  t.addEventListener('click', function(){
    document.querySelectorAll('.tab').forEach(function(x){ x.classList.remove('active'); });
    document.querySelectorAll('.tab-panel').forEach(function(x){ x.classList.remove('active'); });
    t.classList.add('active');
    document.getElementById('panel-' + t.dataset.tab).classList.add('active');
  });
});
document.querySelectorAll('.ts').forEach(function(el){
  el.textContent = new Date(parseFloat(el.dataset.ts)*1000).toLocaleString();
});
function addPlan(){
  var wrap = document.getElementById('new-plans');
  var div = document.createElement('div');
  div.style.cssText = 'border:1px dashed var(--border-hi);border-radius:12px;padding:18px;margin-bottom:14px';
  div.innerHTML = '<div class="grid-2" style="gap:12px">'
    + '<div class="form-row"><label>Plan Name</label><input class="input" name="p_name" placeholder="New Plan"></div>'
    + '<div class="form-row"><label>Duration</label><input class="input" name="p_duration" placeholder="30 Days"></div>'
    + '<div class="form-row"><label>Price</label><input class="input" name="p_price" placeholder="499"></div>'
    + '<div class="form-row"><label>Features</label><input class="input" name="p_features" placeholder="feature1, feature2"></div>'
    + '</div>';
  wrap.appendChild(div);
}
</script>
"""


# ============================================================
#                       ROUTES
# ============================================================
@app.route("/")
def home():
    if is_owner():
        return redirect(url_for("owner_dashboard"))
    if current_user():
        return redirect(url_for("user_dashboard"))
    return redirect(url_for("landing"))

@app.route("/home")
def landing():
    return render_page("Pro VPS Panel — Host Python, Node & Shell 24/7",
                       LANDING_TPL, pricing=load_pricing())

@app.route("/pricing")
def pricing_page():
    return render_page("Pricing — Pro VPS Panel",
                       PRICING_TPL, pricing=load_pricing())

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "")
        if u == OWNER_USER and p == OWNER_PASS:
            session.clear()
            session["role"] = "owner"
            session["username"] = u
            return redirect(url_for("owner_dashboard"))
        users = load_users()
        info = users.get(u)
        if info and info["password"] == p:
            ok, _ = user_valid(u)
            if not ok:
                error = "Account expired"
            else:
                session.clear()
                session["role"] = "user"
                session["username"] = u
                return redirect(url_for("user_dashboard"))
        else:
            error = "Invalid credentials"
    return render_page("Login — Pro VPS Panel", LOGIN_TPL, error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/auto/<token>")
def auto_login(token):
    users = load_users()
    for uname, info in users.items():
        if info.get("token") == token:
            ok, _ = user_valid(uname)
            if not ok:
                return "Account expired", 403
            session.clear()
            session["role"] = "user"
            session["username"] = uname
            return redirect(url_for("user_dashboard"))
    return "Invalid link", 404

# ---------- owner ----------
@app.route("/owner")
@require_owner
def owner_dashboard():
    users = load_users()
    now = time.time()
    changed = False
    for uname in list(users.keys()):
        if users[uname].get("expires_at") and now > users[uname]["expires_at"]:
            del users[uname]
            stop_process(uname)
            changed = True
    if changed:
        save_users(users)
    base = request.host_url.rstrip("/")
    return render_page("Owner Dashboard — Pro VPS Panel", OWNER_TPL,
                       extra_scripts=OWNER_SCRIPTS,
                       users=users, now=now, base_url=base, pricing=load_pricing())

@app.route("/owner/create", methods=["POST"])
@require_owner
def owner_create():
    u = request.form.get("username", "").strip()
    p = request.form.get("password", "").strip()
    try:
        hours = float(request.form.get("hours", "24"))
    except ValueError:
        hours = 24
    if not u or not p or u == OWNER_USER:
        return redirect(url_for("owner_dashboard"))
    users = load_users()
    users[u] = {
        "password": p,
        "created_at": time.time(),
        "expires_at": time.time() + hours * 3600 if hours > 0 else 0,
        "token": secrets.token_urlsafe(16),
    }
    save_users(users)
    user_dir(u)
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/delete/<username>", methods=["POST"])
@require_owner
def owner_delete(username):
    users = load_users()
    if username in users:
        stop_process(username)
        del users[username]
        save_users(users)
        d = FILES_ROOT / username
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/extend/<username>", methods=["POST"])
@require_owner
def owner_extend(username):
    try:
        hours = float(request.form.get("hours", "24"))
    except ValueError:
        hours = 24
    users = load_users()
    if username in users:
        base = max(users[username].get("expires_at") or time.time(), time.time())
        users[username]["expires_at"] = base + hours * 3600
        save_users(users)
    return redirect(url_for("owner_dashboard"))

@app.route("/owner/pricing", methods=["POST"])
@require_owner
def owner_pricing():
    pricing = load_pricing()
    pricing["currency"] = request.form.get("currency", "₹").strip() or "₹"
    pricing["contact"] = request.form.get("contact", "").strip()
    plans = []
    names = request.form.getlist("p_name")
    durs = request.form.getlist("p_duration")
    prices = request.form.getlist("p_price")
    feats = request.form.getlist("p_features")
    for i in range(len(names)):
        if not names[i].strip():
            continue
        plans.append({
            "name": names[i].strip(),
            "duration": durs[i].strip() if i < len(durs) else "",
            "price": prices[i].strip() if i < len(prices) else "0",
            "features": feats[i].strip() if i < len(feats) else "",
        })
    pricing["plans"] = plans
    save_pricing(pricing)
    return redirect(url_for("owner_dashboard"))

# ---------- user ----------
@app.route("/dashboard")
@require_user
def user_dashboard():
    u = current_user()
    users = load_users()
    info = users.get(u, {})
    udir = user_dir(u)
    files = sorted([f.name for f in udir.iterdir() if f.is_file()])
    return render_page("My Server — Pro VPS Panel", USER_TPL,
                       extra_scripts=USER_SCRIPTS,
                       username=u, info=info, files=files,
                       running=is_running(u),
                       running_file=(PROCS.get(u, {}).get("file") if is_running(u) else None),
                       expires_at=info.get("expires_at", 0),
                       now=time.time())

@app.route("/upload", methods=["POST"])
@require_user
def upload():
    u = current_user()
    udir = user_dir(u)
    for f in request.files.getlist("files"):
        if not f or not f.filename:
            continue
        name = secure_filename(f.filename)
        if name:
            f.save(udir / name)
    return redirect(url_for("user_dashboard"))

@app.route("/file/delete/<name>", methods=["POST"])
@require_user
def file_delete(name):
    u = current_user()
    name = secure_filename(name)
    p = user_dir(u) / name
    if p.exists() and p.is_file():
        p.unlink()
    return redirect(url_for("user_dashboard"))

@app.route("/file/view/<name>")
@require_user
def file_view(name):
    u = current_user()
    name = secure_filename(name)
    return send_from_directory(user_dir(u), name, as_attachment=False)

@app.route("/server/start", methods=["POST"])
@require_user
def server_start():
    u = current_user()
    fname = secure_filename(request.form.get("file", ""))
    ok, msg = start_process(u, fname)
    return jsonify({"ok": ok, "msg": msg})

@app.route("/server/stop", methods=["POST"])
@require_user
def server_stop():
    u = current_user()
    stop_process(u)
    return jsonify({"ok": True, "msg": "stopped"})

@app.route("/server/restart", methods=["POST"])
@require_user
def server_restart():
    u = current_user()
    info = PROCS.get(u)
    fname = info["file"] if info else secure_filename(request.form.get("file", ""))
    if not fname:
        return jsonify({"ok": False, "msg": "no file"})
    stop_process(u)
    time.sleep(0.3)
    ok, msg = start_process(u, fname)
    return jsonify({"ok": ok, "msg": msg})

@app.route("/server/delete", methods=["POST"])
@require_user
def server_delete():
    u = current_user()
    stop_process(u)
    PROCS.pop(u, None)
    return jsonify({"ok": True, "msg": "cleared"})

@app.route("/logs")
@require_user
def logs_api():
    u = current_user()
    return jsonify({
        "running": is_running(u),
        "file": PROCS.get(u, {}).get("file"),
        "logs": get_logs(u),
        "install": list(INSTALL_LOGS.get(u, [])),
    })

@app.route("/install", methods=["POST"])
@require_user
def install():
    u = current_user()
    cmd = request.form.get("command", "").strip()
    ok, msg = run_install(u, cmd)
    return jsonify({"ok": ok, "msg": msg})

@app.route("/healthz")
def health():
    return "ok"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)