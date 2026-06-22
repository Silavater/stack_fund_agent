"""StackFund chat UI — a dependency-free (stdlib) web server.

Serves a branded chat page and, on each message, calls the running Hermes agent
(``docker exec <container> hermes -z "<msg>" -m <model> --provider <provider>``).
The agent runs the StackFund skills + deterministic engine and replies under its
SOUL persona. No web framework, no new deps — same spirit as the engine itself.

Run via ``docker/run-chat-ui.sh`` (it ensures the agent container is up), or:
    SF_AGENT_CONTAINER=stackfund-agent python ui/server.py
Then open the URL it prints (default http://localhost:5757; auto-picks a free
port, since Windows/Hyper-V reserves some ranges).
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CONTAINER = os.environ.get("SF_AGENT_CONTAINER", "stackfund-agent")
MODEL = os.environ.get("HERMES_MODEL", "gpt-5.5")
PROVIDER = os.environ.get("HERMES_PROVIDER", "custom")
HOST = os.environ.get("SF_UI_HOST", "127.0.0.1")
PORT = int(os.environ.get("SF_UI_PORT", "5757"))
TIMEOUT = int(os.environ.get("SF_UI_TIMEOUT", "180"))

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
        tail = err[-1] if err else "no response produced"
        return {"error": tail}
    return {"reply": reply}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_a):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif self.path == "/healthz":
            self._send(200, b"ok", "text/plain")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/chat":
            self._send(404, b"not found", "text/plain")
            return
        n = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(n) or b"{}")
            msg = str(payload.get("message", "")).strip()
        except Exception:
            self._send(400, b'{"error":"bad request"}', "application/json")
            return
        if not msg:
            self._send(400, b'{"error":"empty message"}', "application/json")
            return
        result = ask_agent(msg)
        self._send(200, json.dumps(result, ensure_ascii=False).encode("utf-8"), "application/json")


INDEX_HTML = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>StackFund — research desk</title>
<style>
*{box-sizing:border-box}
:root{--bg:#f4f4f2;--card:#fff;--tp:#1c1c1a;--ts:#6e6e68;--tt:#9b9b93;--bd:rgba(0,0,0,.10);
  --u-bg:#16548f;--u-tx:#fff;--a-bg:#fff;--ban-bg:#fbeede;--ban-tx:#8a5210;--accent:#16548f}
@media (prefers-color-scheme:dark){:root{--bg:#19191a;--card:#242423;--tp:#ededeb;--ts:#a6a6a2;
  --tt:#74746d;--bd:rgba(255,255,255,.12);--u-bg:#2f6fb0;--a-bg:#242423;--ban-bg:#3d2a0a;
  --ban-tx:#f1ca88;--accent:#88b9ec}}
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
.chip{font-size:13px;border:1px solid var(--bd);background:var(--card);color:var(--tp);border-radius:20px;
  padding:7px 13px;cursor:pointer}
.chip:hover{border-color:var(--accent)}
footer{border-top:1px solid var(--bd);padding:12px 18px}
form{display:flex;gap:9px;max-width:860px;margin:0 auto}
input{flex:1;font-size:15px;padding:11px 14px;border:1px solid var(--bd);border-radius:12px;
  background:var(--card);color:var(--tp);font-family:inherit}
input:focus{outline:none;border-color:var(--accent)}
button{font-size:15px;padding:0 18px;border-radius:12px;border:none;background:var(--accent);color:#fff;cursor:pointer}
button:disabled{opacity:.5;cursor:default}
.foot-note{text-align:center;font-size:11px;color:var(--tt);margin-top:7px}
</style></head><body>
<header><div><div class="t">StackFund — Taiwan ETF research desk</div>
<div class="s">gpt-5.5 · deterministic engine · 不下任何證券委託單</div></div>
<span class="pill">research / education only</span></header>
<div id="log"><div class="row a"><div><div class="who">StackFund</div>
<div class="bub">你好,我是 StackFund 自主台股 ETF 研究台。我會呼叫確定性引擎算出每個數字、再幫你解讀 —— 我不下任何證券委託單,也不給個別化投資建議。問我一檔 ETF 的研究或再平衡決策吧。</div></div></div></div>
<div class="chips" id="chips"></div>
<footer><form id="f"><input id="m" autocomplete="off"
  placeholder="例如:研究 0056,用 etf-analysis skill 給再平衡決策" />
<button id="b" type="submit">送出</button></form>
<div class="foot-note">每則回覆約需 15–25 秒(agent 正在跑引擎)· 研究/教育用途</div></footer>
<script>
const log=document.getElementById('log'),form=document.getElementById('f'),inp=document.getElementById('m'),btn=document.getElementById('b');
const SUG=["研究 0056,給再平衡決策","0050 現在該加碼嗎?","我該不該把存款全押 00878?","跑一次完整 pipeline,三檔都看"];
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
    print(f"StackFund chat UI -> http://localhost:{bound}")
    print(f"  agent container: {CONTAINER} · model: {MODEL} · provider: {PROVIDER}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
