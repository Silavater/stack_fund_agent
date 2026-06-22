"""StackFund web app — dependency-free (stdlib) buy → use → chat flow.

One small server gives the whole demo journey:
  /pricing      → pick a plan → Stripe TEST-mode Checkout (real cs_/pi_)
  /success      → server-verifies the session is paid → unlock
  /             → chat with the Hermes agent (runs skills + engine under SOUL)
Each chat message runs a real agent turn via
  ``docker exec <container> hermes -z "<msg>" -m <model> --provider <provider>``.

No web framework, no new deps. Stripe is optional + TEST-key-only (stripe_client
guards it); with no key, checkout falls back to an honest stub that still unlocks.

Run via ``docker/run-chat-ui.sh``, or for real Stripe:
    uv run --extra stripe python ui/server.py        # then open the printed URL
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

CONTAINER = os.environ.get("SF_AGENT_CONTAINER", "stackfund-agent")
MODEL = os.environ.get("HERMES_MODEL", "gpt-5.5")
PROVIDER = os.environ.get("HERMES_PROVIDER", "custom")
HOST = os.environ.get("SF_UI_HOST", "127.0.0.1")
PORT = int(os.environ.get("SF_UI_PORT", "5757"))
TIMEOUT = int(os.environ.get("SF_UI_TIMEOUT", "180"))

# Make the stackfund package importable when run as a plain script (src layout).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
try:
    from stackfund.l5_finops import stripe_client  # stripe SDK is imported lazily inside it
except Exception:  # noqa: BLE001
    stripe_client = None

TIERS = {
    "watch": {"name": "Watch", "amount": 0, "blurb": "免費 · 公開摘要"},
    "pro": {"name": "Pro", "amount": 299, "blurb": "群眾情境報告 + 研究台 — 這就是產品"},
    "desk": {"name": "Desk", "amount": 999, "blurb": "Pro + 即時資料 + 優先排程"},
}
_EARNS: list[dict] = []  # in-memory record of paid sessions (demo)

_NOISE = ("plugins: Plugin", "registered:", "reconcile:", "cont-init", "s6-rc")


def ask_agent(message: str) -> dict:
    """Run one agent turn in the container; return {reply} or {error}."""
    inner = (
        ". /opt/hermes/.venv/bin/activate 2>/dev/null; "
        "export HOME=/opt/data HERMES_HOME=/opt/data; "
        f"hermes -z {shlex.quote(message)} -m {shlex.quote(MODEL)} "
        f"--provider {shlex.quote(PROVIDER)}"
    )
    cmd = ["docker", "exec", CONTAINER, "sh", "-lc", inner]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"error": f"agent timed out after {TIMEOUT}s"}
    except FileNotFoundError:
        return {"error": "docker not found on PATH"}
    out = (proc.stdout or "").strip()
    reply = "\n".join(ln for ln in out.splitlines() if not any(n in ln for n in _NOISE)).strip()
    if not reply:
        err = (proc.stderr or "").strip().splitlines()
        return {"error": err[-1] if err else "no response produced"}
    return {"reply": reply}


def checkout(tier: str, base: str) -> dict:
    """Start a purchase. Returns {url} to redirect the browser to."""
    t = TIERS.get(tier)
    if not t:
        return {"error": "unknown tier"}
    if t["amount"] == 0:
        return {"url": "/"}  # free tier → straight into the desk
    if stripe_client is None or not stripe_client.is_configured():
        return {"url": f"/success?stub=1&tier={tier}"}  # honest stub: unlock, no charge
    try:
        s = stripe_client.create_checkout_session(
            t["name"],
            float(t["amount"]),
            "twd",
            success_url=f"{base}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/pricing",
        )
        return {"url": s["url"]}
    except Exception as exc:  # noqa: BLE001
        return {"url": f"/success?stub=1&tier={tier}", "note": type(exc).__name__}


def success_html(qs: dict) -> str:
    """Server-side verify a returned Checkout session, record the earn, render unlock."""
    session_id = (qs.get("session_id") or [None])[0]
    tier = (qs.get("tier") or ["pro"])[0]
    amt = TIERS.get(tier, {}).get("amount", 299)
    if session_id and stripe_client is not None:
        try:
            r = stripe_client.retrieve_checkout_session(session_id)
            if r["paid"]:
                _EARNS.append({"amount": r["amount"], "id": r["id"]})
                return _success(int(r["amount"]), "Stripe 測試模式 · 已付款")
        except Exception:  # noqa: BLE001
            pass
    if (qs.get("stub") or [None])[0]:
        return _success(int(amt), "stub(無 Stripe key)· 已解鎖")
    return FAIL_HTML


def _success(amt: int, mode: str) -> str:
    return SUCCESS_HTML.replace("__AMT__", str(amt)).replace("__MODE__", mode)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_a):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html: str):
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def do_GET(self):
        p = urlparse(self.path)
        if p.path in ("/", "/index.html"):
            self._html(INDEX_HTML)
        elif p.path == "/pricing":
            self._html(PRICING_HTML)
        elif p.path == "/success":
            self._html(success_html(parse_qs(p.query)))
        elif p.path == "/healthz":
            self._send(200, b"ok", "text/plain")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception:  # noqa: BLE001
            self._send(400, b'{"error":"bad request"}', "application/json")
            return
        if self.path == "/api/checkout":
            base = f"http://{self.headers.get('Host', f'localhost:{PORT}')}"
            out = checkout(str(payload.get("tier", "")), base)
            self._send(200, json.dumps(out, ensure_ascii=False).encode("utf-8"), "application/json")
            return
        if self.path == "/api/chat":
            msg = str(payload.get("message", "")).strip()
            if not msg:
                self._send(400, b'{"error":"empty message"}', "application/json")
                return
            out = ask_agent(msg)
            self._send(200, json.dumps(out, ensure_ascii=False).encode("utf-8"), "application/json")
            return
        self._send(404, b"not found", "text/plain")


_CSS = """*{box-sizing:border-box}
:root{--bg:#f4f4f2;--card:#fff;--tp:#1c1c1a;--ts:#6e6e68;--tt:#9b9b93;--bd:rgba(0,0,0,.10);
  --u-bg:#16548f;--u-tx:#fff;--a-bg:#fff;--ban-bg:#fbeede;--ban-tx:#8a5210;--accent:#16548f;--ok:#0f6e56}
@media (prefers-color-scheme:dark){:root{--bg:#19191a;--card:#242423;--tp:#ededeb;--ts:#a6a6a2;
  --tt:#74746d;--bd:rgba(255,255,255,.12);--u-bg:#2f6fb0;--a-bg:#242423;--ban-bg:#3d2a0a;
  --ban-tx:#f1ca88;--accent:#88b9ec;--ok:#62cba6}}"""

PRICING_HTML = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>StackFund — 訂閱</title>
<style>{_CSS}
body{{margin:0;background:var(--bg);color:var(--tp);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC",sans-serif;line-height:1.5}}
.wrap{{max-width:860px;margin:0 auto;padding:48px 20px}}
.h1{{font-size:24px;font-weight:600}}.sub{{color:var(--ts);margin:6px 0 28px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:20px}}
.card.hot{{border:2px solid var(--accent)}}
.tag{{font-size:11px;color:var(--accent);font-weight:500}}
.name{{font-size:17px;font-weight:600;margin-top:4px}}
.price{{font-size:28px;font-weight:600;margin:8px 0}}.price small{{font-size:14px;color:var(--ts);font-weight:400}}
.blurb{{font-size:13px;color:var(--ts);min-height:38px}}
button{{width:100%;margin-top:14px;font-size:15px;padding:11px;border-radius:11px;border:none;background:var(--accent);color:#fff;cursor:pointer}}
button.ghost{{background:transparent;border:1px solid var(--bd);color:var(--tp)}}
.note{{font-size:12px;color:var(--tt);margin-top:24px}}</style></head><body>
<div class="wrap"><div class="h1">StackFund — 自主台股 ETF 研究台</div>
<div class="sub">訂閱即解鎖會跑確定性引擎的 agent。研究/教育用途 · 全程不下任何證券委託單。</div>
<div class="grid">
  <div class="card"><div class="name">Watch</div><div class="price">免費</div>
    <div class="blurb">公開摘要</div><button class="ghost" onclick="buy('watch')">免費進入</button></div>
  <div class="card hot"><div class="tag">最受歡迎</div><div class="name">Pro</div>
    <div class="price">NT$299<small>/月</small></div>
    <div class="blurb">群眾情境報告 + 研究台 — 這就是產品</div><button onclick="buy('pro')">訂閱 Pro</button></div>
  <div class="card"><div class="name">Desk</div><div class="price">NT$999<small>/月</small></div>
    <div class="blurb">Pro + 即時資料 + 優先排程</div><button class="ghost" onclick="buy('desk')">訂閱 Desk</button></div>
</div>
<div class="note">Stripe 測試模式 — 結帳用測試卡 <b>4242 4242 4242 4242</b> · 任意未來到期日 · 任意 CVC。</div></div>
<script>
async function buy(tier){{
  const r=await fetch('/api/checkout',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{tier}})}});
  const d=await r.json(); if(d.url){{location.href=d.url}} else {{alert(d.error||'error')}}
}}
</script></body></html>"""

SUCCESS_HTML = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>已解鎖</title>
<style>{_CSS}
body{{margin:0;background:var(--bg);color:var(--tp);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC",sans-serif;
  display:flex;align-items:center;justify-content:center;height:100vh;text-align:center}}
.box{{max-width:440px;padding:24px}}
.tick{{width:54px;height:54px;border-radius:50%;background:var(--ban-bg);color:var(--ok);display:flex;align-items:center;justify-content:center;font-size:26px;margin:0 auto 16px}}
.h{{font-size:21px;font-weight:600}}.m{{color:var(--ts);margin:8px 0 22px;font-size:14px}}
a.btn{{display:inline-block;font-size:15px;padding:12px 22px;border-radius:12px;background:var(--accent);color:#fff;text-decoration:none}}
.dis{{font-size:11px;color:var(--tt);margin-top:20px}}</style></head><body>
<div class="box"><div class="tick">✓</div>
<div class="h">已解鎖 Pro · NT$__AMT__</div>
<div class="m">__MODE__ — 這筆會進 FinOps 帳本成為營收。</div>
<a class="btn" href="/">進入研究台 →</a>
<div class="dis">研究/教育 · 非個別化投資建議 · 全程不下任何證券委託單</div></div></body></html>"""

FAIL_HTML = f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><title>未付款</title>
<style>{_CSS}body{{margin:0;background:var(--bg);color:var(--tp);font-family:sans-serif;
display:flex;align-items:center;justify-content:center;height:100vh}}
a{{color:var(--accent)}}</style></head><body>
<div style="text-align:center"><p>找不到已完成的付款。</p><a href="/pricing">← 回訂閱頁</a></div></body></html>"""

INDEX_HTML = (
    """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>StackFund — research desk</title>
<style>"""
    + _CSS
    + """
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--tp);display:flex;flex-direction:column;height:100vh;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC","PingFang TC",sans-serif}
header{padding:14px 18px;border-bottom:1px solid var(--bd);display:flex;align-items:baseline;
  justify-content:space-between;gap:12px;flex-wrap:wrap}
header .t{font-size:16px;font-weight:600}
header .s{font-size:12px;color:var(--tt)}
header .pill{font-size:11px;color:var(--tt);border:1px solid var(--bd);border-radius:8px;padding:4px 9px}
#log{flex:1;overflow-y:auto;padding:20px;max-width:860px;width:100%;margin:0 auto}
.row{display:flex;margin:12px 0}
.row.u{justify-content:flex-end}
.bub{max-width:78%;padding:11px 14px;border-radius:14px;font-size:14.5px;line-height:1.6;white-space:pre-wrap;word-break:break-word}
.u .bub{background:var(--u-bg);color:var(--u-tx);border-bottom-right-radius:5px}
.a .bub{background:var(--a-bg);border:1px solid var(--bd);border-bottom-left-radius:5px}
.ban{background:var(--ban-bg);color:var(--ban-tx);font-size:12px;padding:7px 11px;border-radius:9px;margin-bottom:9px}
.who{font-size:11px;color:var(--tt);margin:0 4px 3px}
.dots span{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--ts);margin:0 2px;animation:b 1.2s infinite}
.dots span:nth-child(2){animation-delay:.2s}.dots span:nth-child(3){animation-delay:.4s}
@keyframes b{0%,60%,100%{opacity:.25}30%{opacity:1}}
.hint{font-size:12px;color:var(--tt);margin-top:4px}
.chips{display:flex;gap:8px;flex-wrap:wrap;max-width:860px;margin:0 auto;padding:0 20px}
.chip{font-size:13px;border:1px solid var(--bd);background:var(--card);color:var(--tp);border-radius:20px;padding:7px 13px;cursor:pointer}
.chip:hover{border-color:var(--accent)}
footer{border-top:1px solid var(--bd);padding:12px 18px}
form{display:flex;gap:9px;max-width:860px;margin:0 auto}
input{flex:1;font-size:15px;padding:11px 14px;border:1px solid var(--bd);border-radius:12px;background:var(--card);color:var(--tp);font-family:inherit}
input:focus{outline:none;border-color:var(--accent)}
button{font-size:15px;padding:0 18px;border-radius:12px;border:none;background:var(--accent);color:#fff;cursor:pointer}
button:disabled{opacity:.5;cursor:default}
.foot-note{text-align:center;font-size:11px;color:var(--tt);margin-top:7px}
</style></head><body>
<header><div><div class="t">StackFund — Taiwan ETF research desk</div>
<div class="s">gpt-5.5 · deterministic engine · 不下任何證券委託單</div></div>
<span class="pill">Pro · research / education only</span></header>
<div id="log"><div class="row a"><div><div class="who">StackFund</div>
<div class="bub">你好,我是 StackFund 自主台股 ETF 研究台。我會呼叫確定性引擎算出每個數字、再幫你解讀 —— 我不下任何證券委託單,也不給個別化投資建議。問我一檔 ETF 的研究或再平衡決策吧。</div></div></div></div>
<div class="chips" id="chips"></div>
<footer><form id="f"><input id="m" autocomplete="off"
  placeholder="例如:研究 0056,用 etf-analysis skill 給再平衡決策" />
<button id="b" type="submit">送出</button></form>
<div class="foot-note">每則回覆約需 15–25 秒(agent 正在跑引擎)· 研究/教育用途</div></footer>
<script>
const log=document.getElementById('log'),form=document.getElementById('f'),inp=document.getElementById('m'),btn=document.getElementById('b');
const SUG=["研究 0056,給再平衡決策","0050 現在該加碼嗎?","我該不該把存款全押 00878?","群眾看多,把 0056 權重調高"];
const chips=document.getElementById('chips');
SUG.forEach(s=>{const c=document.createElement('div');c.className='chip';c.textContent=s;c.onclick=()=>{inp.value=s;inp.focus()};chips.appendChild(c)});
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}
function add(role,html){const r=document.createElement('div');r.className='row '+role;
  const w=role==='u'?'你':'StackFund';
  r.innerHTML='<div><div class="who">'+w+'</div><div class="bub">'+html+'</div></div>';
  log.appendChild(r);log.scrollTop=log.scrollHeight;return r}
function renderReply(t){
  const lines=t.split('\\n');let out='';
  for(const ln of lines){
    if(/研究\\/教育|不下任何證券委託單|non-individualised|no securities orders/.test(ln) && ln.trim().length<160){
      out+='<div class="ban">'+esc(ln.trim())+'</div>';
    } else { out+=esc(ln)+'\\n'; }
  }
  return out.replace(/\\n+$/,'');
}
form.onsubmit=async e=>{
  e.preventDefault();const msg=inp.value.trim();if(!msg)return;
  add('u',esc(msg));inp.value='';btn.disabled=true;inp.disabled=true;
  const tr=add('a','<span class="dots"><span></span><span></span><span></span></span><span class="hint"> 正在跑引擎…</span>');
  try{
    const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
    const data=await res.json();
    tr.querySelector('.bub').innerHTML = data.reply ? renderReply(data.reply) : ('<span class="hint">出錯了:'+esc(data.error||'unknown')+'</span>');
  }catch(err){ tr.querySelector('.bub').innerHTML='<span class="hint">連線失敗:'+esc(String(err))+'</span>'; }
  btn.disabled=false;inp.disabled=false;inp.focus();
};
inp.focus();
</script></body></html>"""
)


def main() -> int:
    srv = None
    bound = PORT
    for p in range(PORT, PORT + 10):
        try:
            srv = ThreadingHTTPServer((HOST, p), Handler)
            bound = p
            break
        except (PermissionError, OSError):
            continue
    if srv is None:
        print(f"could not bind any port in {PORT}..{PORT + 9} on {HOST}")
        print("try another: SF_UI_PORT=5757 python ui/server.py")
        return 1
    stripe_state = (
        "configured" if (stripe_client and stripe_client.is_configured()) else "stub (no test key)"
    )
    print(f"StackFund app -> http://localhost:{bound}/pricing   (chat at /)")
    print(f"  agent: {CONTAINER} · model: {MODEL} · provider: {PROVIDER} · stripe: {stripe_state}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
