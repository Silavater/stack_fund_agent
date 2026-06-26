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
    "watch": {"name": "Watch", "amount": 0},
    "pro": {"name": "Pro", "amount": 20},
    "desk": {"name": "Desk", "amount": 100},
}
CCY = "usd"  # Stripe currency for paid tiers — USD ($20 Pro / $100 Desk)
_EARNS: list[dict] = []  # in-memory record of paid sessions (demo)
TEAM = os.environ.get("SF_TEAM", "").strip()  # optional team name → " · <team>" in the wordmark

# Brand wordmark: a stacked-bars mark (stack + fund + growth) + "StackFund".
# Mark colour follows --accent so it adapts to light/dark. Team name is optional.
WORDMARK = (
    '<span style="display:inline-flex;align-items:center;gap:9px;line-height:1">'
    '<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true" style="color:var(--accent);flex:none">'
    '<rect x="1" y="13" width="5" height="8" rx="1.3" fill="currentColor" opacity=".55"/>'
    '<rect x="8.5" y="8" width="5" height="13" rx="1.3" fill="currentColor"/>'
    '<rect x="16" y="3" width="5" height="18" rx="1.3" fill="currentColor" opacity=".8"/></svg>'
    '<span style="font-weight:600;letter-spacing:-.01em;color:var(--tp)">StackFund</span>'
    + (
        f'<span style="color:var(--tt);font-weight:400;font-size:.62em"> · {TEAM}</span>'
        if TEAM
        else ""
    )
    + "</span>"
)


def _nav(active: str = "", lang: str = "zh") -> str:
    s = STR[lang]
    items = (
        ("/pricing", s["NAV_PRICING"], "pricing"),
        ("/", s["NAV_CHAT"], "chat"),
        ("/desk", s["NAV_DESK"], "desk"),
        ("/finops", s["NAV_FINOPS"], "finops"),
        ("/journal", s["NAV_JOURNAL"], "journal"),
    )
    links = "".join(
        f'<a class="navlink{" on" if k == active else ""}" href="{h}">{label}</a>'
        for h, label, k in items
    )
    # Language toggle — relative ?lang= href flips the current page; the cookie persists it.
    other, toglabel = ("en", "EN") if lang == "zh" else ("zh", "中")
    links += (
        f'<a class="navlink tog" href="?lang={other}" '
        f"onclick=\"document.cookie='lang={other};path=/;max-age=31536000';location.reload();return false\" "
        f'aria-label="switch language / 切換語言">{toglabel}</a>'
    )
    return (
        '<nav class="nav"><a class="navbrand" href="/pricing">__WORDMARK__</a>'
        f'<div class="navlinks">{links}</div></nav>'
    )


def _sub_banner(sub_key: str | None, lang: str) -> str:
    """A '✓ subscribed' banner for /pricing, from the sf_tier cookie set at checkout."""
    t = TIERS.get(sub_key or "")
    if not t or t["amount"] == 0:
        return ""
    s = STR[lang]
    return (
        f'<a href="/" class="subbanner">✓ {s["SUBBED"]} {t["name"]} · {s["ENTER_DESK"]}</a>'
        f'<a href="/signout" class="signout">{s["SIGNOUT"]}</a>'
    )


def desk_html(lang: str = "zh") -> str:
    """The visual research desk embedded in the site (engine output: rebalance cards +
    candlestick K-lines + the FinOps books + the walled-off crowd), with the shared nav."""
    from stackfund.cli import DEFAULT_SYMBOLS, build_pipeline_result
    from stackfund.report.desk import render_desk_html

    result = build_pipeline_result(DEFAULT_SYMBOLS, "升息", 42)
    return render_desk_html(result, nav="__NAV__", lang=lang)


_NOISE = ("plugins: Plugin", "registered:", "reconcile:", "cont-init", "s6-rc")


def ask_agent(message: str, lang: str = "zh") -> dict:
    """Run one agent turn in the container; return {reply} or {error}."""
    if lang == "en":
        message = (
            "[The user is on the English interface — answer ENTIRELY in English, using the "
            "English section labels (Plain-language takeaway / Why / Details) and the English "
            "disclaimer.]\n\n" + message
        )
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
            CCY,
            success_url=f"{base}/success?session_id={{CHECKOUT_SESSION_ID}}&tier={tier}",
            cancel_url=f"{base}/pricing",
        )
        return {"url": s["url"]}
    except Exception as exc:  # noqa: BLE001
        return {"url": f"/success?stub=1&tier={tier}", "note": type(exc).__name__}


def success_html(qs: dict) -> str:
    """Server-side verify a returned Checkout session, record the earn, render unlock."""
    session_id = (qs.get("session_id") or [None])[0]
    tier = (qs.get("tier") or ["pro"])[0]
    tier_name = TIERS.get(tier, {}).get("name", "Pro")
    amt = TIERS.get(tier, {}).get("amount", 20)
    if session_id and stripe_client is not None:
        try:
            r = stripe_client.retrieve_checkout_session(session_id)
            if r["paid"]:
                _EARNS.append({"amount": r["amount"], "id": r["id"]})
                return _success(int(r["amount"]), "MODE_PAID", tier_name, tier)
        except Exception:  # noqa: BLE001
            pass
    if (qs.get("stub") or [None])[0]:
        return _success(int(amt), "MODE_STUB", tier_name, tier)
    return FAIL_HTML


def _success(amt: int, mode_key: str, tier_name: str = "Pro", tier_key: str = "pro") -> str:
    return (
        SUCCESS_HTML.replace("__TIER__", tier_name)
        .replace("__AMT__", str(amt))
        .replace("__MODE__", f"__T_{mode_key}__")
        .replace("__SUBKEY__", tier_key)
    )


def _finops_rows():
    """Build the earn/spend/refused receipts + P&L from the real L5 functions."""
    from stackfund.l5_finops import attempt_spend, operational_pnl, record_earn

    rcs = [
        record_earn("earn_001", 299.0),
        attempt_spend("spend_001", 120.0, 500.0),  # succeeded — under cap
        attempt_spend("spend_002", 999.0, 380.0),  # refused — over remaining headroom
    ]
    pnl = operational_pnl("2026-06", rcs)
    out = []
    for r in rcs:
        refused = r.type == "refused_spend"
        cls = "ref" if refused else "ok"
        idc = "__T_NO_STRIPE_ROW__" if refused else r.receipt_id
        out.append(
            f'<tr class="{cls}"><td>{r.type}</td><td>{r.status}</td>'
            f'<td class="r">${r.amount:.0f}</td><td class="r">{idc}</td></tr>'
        )
        if refused and r.reason:
            out.append(f'<tr class="ref"><td colspan="4" class="rsn">↳ {r.reason}</td></tr>')
    return "".join(out), pnl


def _pnl_chart_svg(rev: float, cost: float, margin: float) -> str:
    """Horizontal P&L bars (revenue / cost / margin), scaled to the largest value."""
    mx = max(rev, cost, margin, 1.0)
    x0, barw, w_total = 64, 372, 560
    rows = (
        ("營收", rev, "var(--accent)"),
        ("成本", cost, "var(--ban-tx)"),
        ("毛利", margin, "var(--ok)"),
    )
    parts = [
        f'<svg viewBox="0 0 {w_total} 116" width="100%" role="img" '
        f'aria-label="營收、成本、毛利長條圖 — 營收 {rev:.0f}、成本 {cost:.0f}、毛利 {margin:.0f}">'
    ]
    y = 12
    for label, val, color in rows:
        w = max(
            0, int(barw * max(val, 0.0) / mx)
        )  # clamp: negative margin → 0-width, never a negative rect
        parts.append(
            f'<text x="0" y="{y + 16}" style="fill:var(--ts);font-size:12px">{label}</text>'
        )
        parts.append(
            f'<rect x="{x0}" y="{y}" width="{barw}" height="24" rx="6" style="fill:var(--bd)"/>'
        )
        parts.append(
            f'<rect x="{x0}" y="{y}" width="{w}" height="24" rx="6" style="fill:{color}"/>'
        )
        parts.append(
            f'<text x="{x0 + barw + 8}" y="{y + 16}" '
            f'style="fill:var(--tp);font-size:12px;font-weight:600">${val:.0f}</text>'
        )
        y += 34
    parts.append("</svg>")
    return "".join(parts)


def finops_html() -> str:
    try:
        rows, pnl = _finops_rows()
    except Exception as exc:  # noqa: BLE001
        return f"<!DOCTYPE html><meta charset='utf-8'><p style='font-family:sans-serif;padding:2rem'>FinOps unavailable: {exc}</p>"
    return (
        FINOPS_HTML.replace("__ROWS__", rows)
        .replace("__REV__", f"{pnl.revenue:.0f}")
        .replace("__COST__", f"{pnl.cost:.0f}")
        .replace("__MARGIN__", f"{pnl.gross_margin:.0f}")
        .replace("__PNLCHART__", _pnl_chart_svg(pnl.revenue, pnl.cost, pnl.gross_margin))
    )


def journal_html() -> str:
    """Render the standing research journal (the agent's long-term plan + memory)."""
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", ".hermes-data", "research-journal.jsonl"
    )
    entries = []
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except FileNotFoundError:
        pass
    rows = []
    for e in reversed(entries):  # newest first
        acts = ""
        for a in e.get("actions", []):
            if a.get("action") == "REBALANCE":
                acts += f'<span class="jbadge act">{a["symbol"]} REBALANCE {a.get("delta_pp", 0):+.2f}pp</span>'
            else:
                acts += f'<span class="jbadge hold">{a["symbol"]} NO_ACTION</span>'
        rows.append(
            f'<div class="je"><div class="jd">{e.get("date", "")}</div>'
            f'<div class="jb"><div class="ja">{acts}</div>'
            f'<div class="jmeta">__T_JE_SCENARIO__ {e.get("scenario", "")} · __T_JE_MARGIN__ ${e.get("margin", 0):.0f}</div></div></div>'
        )
    body = "".join(rows) or '<p style="color:var(--ts);padding:14px 0">__T_JOURNAL_EMPTY__</p>'
    return JOURNAL_HTML.replace("__ROWS__", body).replace("__N__", str(len(entries)))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_a):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cookie(self, name: str) -> str | None:
        for part in self.headers.get("Cookie", "").split(";"):
            part = part.strip()
            if part.startswith(name + "="):
                return part[len(name) + 1 :]
        return None

    def _subscribed(self) -> bool:
        """True if the browser carries a paid sf_tier cookie (set on /success)."""
        t = TIERS.get(self._cookie("sf_tier") or "")
        return bool(t and t.get("amount", 0) > 0)

    def _pick_lang(self) -> tuple[str, bool]:
        """(lang, should_set_cookie). ?lang= wins + persists via cookie; default zh."""
        q = (parse_qs(urlparse(self.path).query).get("lang") or [None])[0]
        if q in ("en", "zh"):
            return q, True
        c = self._cookie("lang")
        return (c, False) if c in ("en", "zh") else ("zh", False)

    def _html(self, html: str, active: str = "", lang: str = "zh", set_cookie: bool = False):
        html = html.replace("__NAV__", _nav(active, lang)).replace("__WORDMARK__", WORDMARK)
        html = _localize(html, lang)
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if set_cookie:
            self.send_header("Set-Cookie", f"lang={lang}; Path=/; Max-Age=31536000; SameSite=Lax")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = urlparse(self.path)
        lang, setc = self._pick_lang()
        if p.path in ("/", "/index.html"):
            page = INDEX_HTML if self._subscribed() else LOCKED_CHAT_HTML
            self._html(page, "chat", lang, setc)
        elif p.path == "/pricing":
            html = PRICING_HTML.replace("__SUBBANNER__", _sub_banner(self._cookie("sf_tier"), lang))
            self._html(html, "pricing", lang, setc)
        elif p.path == "/success":
            self._html(success_html(parse_qs(p.query)), "", lang, setc)
        elif p.path == "/desk":
            self._html(desk_html(lang), "desk", lang, setc)
        elif p.path == "/finops":
            self._html(finops_html(), "finops", lang, setc)
        elif p.path == "/journal":
            self._html(journal_html(), "journal", lang, setc)
        elif p.path == "/signout":  # clear the demo subscription cookie -> fresh state
            self.send_response(302)
            self.send_header("Location", "/pricing")
            self.send_header("Set-Cookie", "sf_tier=; Path=/; Max-Age=0; SameSite=Lax")
            self.end_headers()
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
            if not self._subscribed():
                self._send(
                    402,
                    json.dumps({"error": "subscribe to unlock"}, ensure_ascii=False).encode(
                        "utf-8"
                    ),
                    "application/json",
                )
                return
            msg = str(payload.get("message", "")).strip()
            if not msg:
                self._send(400, b'{"error":"empty message"}', "application/json")
                return
            lang = "en" if self._cookie("lang") == "en" else "zh"
            out = ask_agent(msg, lang)
            self._send(200, json.dumps(out, ensure_ascii=False).encode("utf-8"), "application/json")
            return
        self._send(404, b"not found", "text/plain")


_CSS = """*{box-sizing:border-box}
:root{--bg:#f4f4f2;--card:#fff;--tp:#1c1c1a;--ts:#6e6e68;--tt:#767670;--bd:rgba(0,0,0,.10);--bd2:rgba(0,0,0,.05);
  --u-bg:#16548f;--u-tx:#fff;--a-bg:#fff;--ban-bg:#fbeede;--ban-tx:#8a5210;--accent:#16548f;--ok:#0f6e56;--danger:#a32d2d}
@media (prefers-color-scheme:dark){:root{--bg:#19191a;--card:#242423;--tp:#ededeb;--ts:#a6a6a2;
  --tt:#9a9a93;--bd:rgba(255,255,255,.12);--bd2:rgba(255,255,255,.06);--u-bg:#2f6fb0;--a-bg:#242423;
  --ban-bg:#3d2a0a;--ban-tx:#f1ca88;--accent:#88b9ec;--ok:#62cba6;--danger:#e08585}}
.nav{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;max-width:960px;margin:0 auto;padding:12px 20px;border-bottom:1px solid var(--bd)}
.nav a{text-decoration:none}
.navlinks{display:flex;gap:2px;align-items:center}
.navlink{font-size:13px;color:var(--ts);padding:6px 11px;border-radius:8px;transition:background .15s,color .15s}
.navlink:hover{background:var(--bd2);color:var(--tp)}
.navlink.on{color:var(--tp);font-weight:500;background:var(--bd2)}
a,button{transition:background .15s,border-color .15s,opacity .15s,transform .1s}
button:hover{opacity:.92}button:active{transform:scale(.985)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (max-width:520px){.nav{padding:10px 14px}.navlink{padding:6px 8px}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition:none!important}}
.navlink.tog{border:1px solid var(--bd);font-weight:500}"""

# ── i18n ─────────────────────────────────────────────────────────────────────
# All user-facing copy lives here keyed by id; templates carry __T_<KEY>__ markers
# that _localize() swaps per request language. Default zh-Hant; ?lang=en toggles
# (persisted by a cookie). The dynamic renderers stay language-agnostic — they emit
# the same markers, localized once in _html().
STR = {
    "zh": {
        "NAV_PRICING": "訂閱",
        "NAV_CHAT": "對話",
        "NAV_DESK": "看板",
        "NAV_FINOPS": "帳本",
        "NAV_JOURNAL": "日誌",
        "TITLE_PRICING": "StackFund — 訂閱",
        "CHOOSE_PLAN": "選擇方案",
        "PRICING_SUB": "自主台股 ETF 研究台 · 訂閱即解鎖會自己跑確定性引擎的 agent。研究/教育 · 全程不下任何證券委託單。",
        "PRICE_FREE": "免費",
        "WATCH_BLURB": "公開摘要",
        "WATCH_BTN": "免費進入",
        "PRO_TAG": "最受歡迎",
        "PRICE_PRO": "$20<small>/月</small>",
        "PRO_BLURB": "群眾情境報告 + 研究台 — 這就是產品",
        "PRO_BTN": "訂閱 Pro",
        "PRICE_DESK": "$100<small>/月</small>",
        "DESK_BLURB": "Pro + 即時資料 + 優先排程",
        "DESK_BTN": "訂閱 Desk",
        "STRIPE_NOTE": "Stripe 測試模式 — 結帳用測試卡 <b>4242 4242 4242 4242</b> · 任意未來到期日 · 任意 CVC。",
        "TITLE_SUCCESS": "已解鎖",
        "UNLOCKED": "已解鎖",
        "SUCCESS_NOTE": "— 這筆會進 FinOps 帳本成為營收。",
        "MODE_PAID": "Stripe 測試模式 · 已付款",
        "MODE_STUB": "stub(無 Stripe key)· 已解鎖",
        "ENTER_DESK": "進入研究台 →",
        "SUBBED": "你已訂閱",
        "SIGNOUT": "登出",
        "LOCK_TITLE": "訂閱後解鎖研究對話",
        "LOCK_BODY": "免費方案可看公開的「看板」研究摘要。要和會自己跑確定性引擎的 agent 對話、請它給再平衡決策,需訂閱 Pro。",
        "LOCK_CTA": "查看方案 →",
        "DISCLAIMER": "研究/教育 · 非個別化投資建議 · 全程不下任何證券委託單",
        "TITLE_FAIL": "未付款",
        "NO_PAYMENT": "找不到已完成的付款。",
        "BACK_PRICING": "← 回訂閱頁",
        "TITLE_FINOPS": "StackFund — FinOps",
        "FINOPS_TITLE": "FinOps · 系統自己的帳本",
        "FINOPS_SUB": "authoritative · 系統會自己賺、自己花、超支就拒付 · 群眾無權觸發支出 · 本月累計",
        "REV_LABEL": "營收 · 客戶付進",
        "COST_LABEL": "成本 · 系統付出",
        "MARGIN_LABEL": "營運毛利",
        "PNL_CARD": "營運損益 · 自己賺 vs 自己花",
        "GATE_CARD": "花錢決策閘門(VoI gate)· 群眾被剪在門外",
        "GATE_ARIA": "支出閘門:重要性 AND 額度餘量 → 拒付(999 超過餘量 380,未呼叫 Stripe);群眾訊號在閘門前就被剪斷。",
        "GATE_MATERIALITY": "重要性 0.42",
        "GATE_THRESHOLD": "≥ 門檻 0.30",
        "GATE_HEADROOM": "額度餘量 $380",
        "GATE_CROWD": "群眾 / FACE 訊號",
        "GATE_FIREWALL": "非輸入 · 已隔離",
        "GATE_REFUSED": "已拒付",
        "GATE_OVER": "999 > 餘量 380",
        "GATE_NOSTRIPE": "未呼叫 Stripe · 0 動用",
        "GATE_CAP": "import-linter ·「L5 支出不得由群眾側軌觸發」· 機器強制",
        "RECEIPTS_CARD": "收據明細 · Stripe 測試模式",
        "TH_TYPE": "type",
        "TH_STATUS": "status",
        "TH_AMOUNT": "金額",
        "TH_RECEIPT": "收據編號",
        "NO_STRIPE_ROW": "— 未呼叫 Stripe",
        "TITLE_JOURNAL": "StackFund — 研究日誌",
        "JOURNAL_TITLE": "研究日誌",
        "JOURNAL_PLAN_A": "<b>長期規劃</b> — 這個研究台有一個<b>標準週排程</b>:每週自動跑一次 0050 / 0056 / 00878 研究,把決策寫進日誌(它的記憶)。目前",
        "JOURNAL_PLAN_B": "筆。排程方式見 <code>docker/setup-cron.sh</code>(Hermes cron)。",
        "JOURNAL_EMPTY": "尚無紀錄 — 執行 <code>python -m stackfund journal</code> 產生第一筆。",
        "JE_SCENARIO": "情境",
        "JE_MARGIN": "毛利",
        "JOURNAL_FOOT": "每筆都是確定性引擎的決策(非 LLM)· 沒變化就 NO_ACTION(紀律)· agent 不是被問才動,是自己持續經營。",
        "TITLE_CHAT": "StackFund — research desk",
        "CHAT_GREETING": "你好,我是 StackFund 自主台股 ETF 研究台。我會呼叫確定性引擎算出每個數字、再幫你解讀 —— 我不下任何證券委託單,也不給個別化投資建議。問我一檔 ETF 的研究或再平衡決策吧。",
        "WHO_USER": "你",
        "WHO_ASSISTANT": "StackFund",
        "CHAT_PLACEHOLDER": "例如:研究 0056,用 etf-analysis skill 給再平衡決策",
        "CHAT_INPUT_ARIA": "輸入給研究台的問題",
        "CHAT_SEND": "送出",
        "CHAT_FOOTNOTE": "每則回覆約需 15–25 秒(agent 正在跑引擎)· 研究/教育用途",
        "ERR_PREFIX": "出錯了:",
        "CONN_FAIL": "連線失敗:",
        "SUG_JSON": json.dumps(
            [
                "研究 0056,給再平衡決策",
                "0050 現在該加碼嗎?",
                "我該不該把存款全押 00878?",
                "群眾看多,把 0056 權重調高",
            ],
            ensure_ascii=False,
        ),
        "STAGES_JSON": json.dumps(
            [" 呼叫 agent…", " 跑確定性引擎(L1 → L2 → L4)…", " 整理白話結論…"], ensure_ascii=False
        ),
    },
    "en": {
        "NAV_PRICING": "Plans",
        "NAV_CHAT": "Chat",
        "NAV_DESK": "Board",
        "NAV_FINOPS": "FinOps",
        "NAV_JOURNAL": "Journal",
        "TITLE_PRICING": "StackFund — Plans",
        "CHOOSE_PLAN": "Choose a plan",
        "PRICING_SUB": "Autonomous Taiwan-ETF research desk · subscribe to unlock an agent that runs a deterministic engine itself. Research / education · never places any securities order.",
        "PRICE_FREE": "Free",
        "WATCH_BLURB": "Public summary",
        "WATCH_BTN": "Enter free",
        "PRO_TAG": "Most popular",
        "PRICE_PRO": "$20<small>/mo</small>",
        "PRO_BLURB": "Crowd-scenario report + the desk — this is the product",
        "PRO_BTN": "Subscribe to Pro",
        "PRICE_DESK": "$100<small>/mo</small>",
        "DESK_BLURB": "Pro + live data + priority scheduling",
        "DESK_BTN": "Subscribe to Desk",
        "STRIPE_NOTE": "Stripe test mode — pay with test card <b>4242 4242 4242 4242</b> · any future expiry · any CVC.",
        "TITLE_SUCCESS": "Unlocked",
        "UNLOCKED": "Unlocked",
        "SUCCESS_NOTE": "— this becomes revenue in the FinOps ledger.",
        "MODE_PAID": "Stripe test mode · paid",
        "MODE_STUB": "stub (no Stripe key) · unlocked",
        "ENTER_DESK": "Enter the desk →",
        "SUBBED": "You're subscribed to",
        "SIGNOUT": "Sign out",
        "LOCK_TITLE": "Subscribe to unlock the research chat",
        "LOCK_BODY": "The free plan shows the public Board research summary. Chatting with the agent that runs the deterministic engine — and asking it for a rebalance decision — needs a Pro subscription.",
        "LOCK_CTA": "See plans →",
        "DISCLAIMER": "Research / education · not individual investment advice · never places any securities order",
        "TITLE_FAIL": "Not paid",
        "NO_PAYMENT": "No completed payment found.",
        "BACK_PRICING": "← Back to plans",
        "TITLE_FINOPS": "StackFund — FinOps",
        "FINOPS_TITLE": "FinOps · the system's own books",
        "FINOPS_SUB": "authoritative · it earns, spends, and refuses to overspend · the crowd can't trigger spend · month-to-date",
        "REV_LABEL": "Revenue · paid in",
        "COST_LABEL": "Cost · paid out",
        "MARGIN_LABEL": "Operating margin",
        "PNL_CARD": "Operating P&L · earned vs spent",
        "GATE_CARD": "Spend gate (VoI) · the crowd is cut off outside",
        "GATE_ARIA": "Spend gate: materiality AND cap headroom → refused (999 over headroom 380, no Stripe call); the crowd signal is cut before the gate.",
        "GATE_MATERIALITY": "materiality 0.42",
        "GATE_THRESHOLD": "≥ threshold 0.30",
        "GATE_HEADROOM": "cap headroom $380",
        "GATE_CROWD": "crowd / FACE signal",
        "GATE_FIREWALL": "not an input · firewalled",
        "GATE_REFUSED": "REFUSED",
        "GATE_OVER": "999 > headroom 380",
        "GATE_NOSTRIPE": "no Stripe call · 0 moved",
        "GATE_CAP": "import-linter · “L5 spend must not be triggered by the crowd side-rail” · machine-enforced",
        "RECEIPTS_CARD": "Receipts · Stripe test mode",
        "TH_TYPE": "type",
        "TH_STATUS": "status",
        "TH_AMOUNT": "amount",
        "TH_RECEIPT": "receipt id",
        "NO_STRIPE_ROW": "— no Stripe call",
        "TITLE_JOURNAL": "StackFund — Research journal",
        "JOURNAL_TITLE": "Research journal",
        "JOURNAL_PLAN_A": "<b>Long-term plan</b> — this desk runs a <b>standing weekly schedule</b>: every week it researches 0050 / 0056 / 00878 and writes the decisions to its journal (its memory). So far",
        "JOURNAL_PLAN_B": "entries. See <code>docker/setup-cron.sh</code> (Hermes cron) for scheduling.",
        "JOURNAL_EMPTY": "No entries yet — run <code>python -m stackfund journal</code> to create the first.",
        "JE_SCENARIO": "scenario",
        "JE_MARGIN": "margin",
        "JOURNAL_FOOT": "Every entry is the deterministic engine's decision (not the LLM) · NO_ACTION when nothing changes (discipline) · the agent doesn't wait to be asked — it operates continuously.",
        "TITLE_CHAT": "StackFund — research desk",
        "CHAT_GREETING": "Hi — I'm StackFund, an autonomous Taiwan-ETF research desk. I call a deterministic engine to compute every number, then explain it. I never place any securities order and don't give individual investment advice. Ask me about an ETF's research or a rebalance decision.",
        "WHO_USER": "You",
        "WHO_ASSISTANT": "StackFund",
        "CHAT_PLACEHOLDER": "e.g. Research 0056 with the etf-analysis skill and give a rebalance decision",
        "CHAT_INPUT_ARIA": "Message to the research desk",
        "CHAT_SEND": "Send",
        "CHAT_FOOTNOTE": "Each reply takes ~15–25s (the agent is running the engine) · research / education",
        "ERR_PREFIX": "Error: ",
        "CONN_FAIL": "Connection failed: ",
        "SUG_JSON": json.dumps(
            [
                "Research 0056 and give a rebalance decision",
                "Should I add to 0050 now?",
                "Should I put all my savings into 00878?",
                "The crowd is bullish — bump 0056's weight",
            ]
        ),
        "STAGES_JSON": json.dumps(
            [
                " Calling the agent…",
                " Running the deterministic engine (L1 → L2 → L4)…",
                " Writing a plain-language takeaway…",
            ]
        ),
    },
}


def _localize(html: str, lang: str) -> str:
    html = html.replace("__HTMLLANG__", "zh-Hant" if lang == "zh" else "en")
    for k, v in STR[lang].items():
        html = html.replace(f"__T_{k}__", v)
    return html


PRICING_HTML = f"""<!DOCTYPE html><html lang="__HTMLLANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>__T_TITLE_PRICING__</title>
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
.note{{font-size:12px;color:var(--tt);margin-top:24px}}
.subbanner{{display:inline-block;text-decoration:none;background:var(--card);color:var(--ok);border:1px solid var(--ok);border-radius:11px;padding:9px 14px;font-size:14px;font-weight:500;margin:0 0 20px}}
.subbanner:hover{{background:var(--bd2)}}
.signout{{display:inline-block;margin-left:9px;color:var(--ts);font-size:13px;text-decoration:none;vertical-align:middle}}
.signout:hover{{color:var(--tp);text-decoration:underline}}</style></head><body>__NAV__
<div class="wrap" role="main"><h1 class="h1" style="margin:0">__T_CHOOSE_PLAN__</h1>
<div class="sub">__T_PRICING_SUB__</div>
__SUBBANNER__
<div class="grid">
  <div class="card"><div class="name">Watch</div><div class="price">__T_PRICE_FREE__</div>
    <div class="blurb">__T_WATCH_BLURB__</div><button class="ghost" onclick="buy('watch')">__T_WATCH_BTN__</button></div>
  <div class="card hot"><div class="tag">__T_PRO_TAG__</div><div class="name">Pro</div>
    <div class="price">__T_PRICE_PRO__</div>
    <div class="blurb">__T_PRO_BLURB__</div><button onclick="buy('pro')">__T_PRO_BTN__</button></div>
  <div class="card"><div class="name">Desk</div><div class="price">__T_PRICE_DESK__</div>
    <div class="blurb">__T_DESK_BLURB__</div><button class="ghost" onclick="buy('desk')">__T_DESK_BTN__</button></div>
</div>
<div class="note">__T_STRIPE_NOTE__</div></div>
<script>
async function buy(tier){{
  const r=await fetch('/api/checkout',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{tier}})}});
  const d=await r.json(); if(d.url){{location.href=d.url}} else {{alert(d.error||'error')}}
}}
</script></body></html>"""

SUCCESS_HTML = f"""<!DOCTYPE html><html lang="__HTMLLANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>__T_TITLE_SUCCESS__</title>
<style>{_CSS}
body{{margin:0;background:var(--bg);color:var(--tp);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC",sans-serif;
  display:flex;flex-direction:column;min-height:100vh;text-align:center}}
.center{{flex:1;display:flex;align-items:center;justify-content:center;padding:24px}}
.box{{max-width:440px}}
.tick{{width:54px;height:54px;border-radius:50%;background:var(--ban-bg);color:var(--ok);display:flex;align-items:center;justify-content:center;font-size:26px;margin:0 auto 16px}}
.h{{font-size:21px;font-weight:600}}.m{{color:var(--ts);margin:8px 0 22px;font-size:14px}}
a.btn{{display:inline-block;font-size:15px;padding:12px 22px;border-radius:12px;background:var(--accent);color:#fff;text-decoration:none}}
.dis{{font-size:11px;color:var(--tt);margin-top:20px}}</style></head><body>__NAV__
<div class="center" role="main"><div class="box"><div class="tick">✓</div>
<h1 class="h" style="margin:0">__T_UNLOCKED__ __TIER__ · $__AMT__</h1>
<div class="m">__MODE__ __T_SUCCESS_NOTE__</div>
<a class="btn" href="/">__T_ENTER_DESK__</a>
<div class="dis">__T_DISCLAIMER__</div></div></div>
<script>document.cookie="sf_tier=__SUBKEY__;path=/;max-age=2592000;samesite=lax"</script></body></html>"""

FAIL_HTML = f"""<!DOCTYPE html><html lang="__HTMLLANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>__T_TITLE_FAIL__</title>
<style>{_CSS}body{{margin:0;background:var(--bg);color:var(--tp);font-family:-apple-system,"Noto Sans TC",sans-serif;
display:flex;flex-direction:column;min-height:100vh}}
a{{color:var(--accent)}}</style></head><body>__NAV__
<div style="flex:1;display:flex;align-items:center;justify-content:center;text-align:center;padding:24px">
<div><p>__T_NO_PAYMENT__</p><a href="/pricing">__T_BACK_PRICING__</a></div></div></body></html>"""

FINOPS_HTML = f"""<!DOCTYPE html><html lang="__HTMLLANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>__T_TITLE_FINOPS__</title>
<style>{_CSS}
body{{margin:0;background:var(--bg);color:var(--tp);line-height:1.5;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC",sans-serif}}
.wrap{{max-width:780px;margin:0 auto;padding:24px 20px 44px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:10px}}
.h1{{font-size:20px;font-weight:600}} a.back{{font-size:13px;color:var(--accent);text-decoration:none}}
.sub{{color:var(--ts);font-size:13px;margin:4px 0 18px}}
.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}}
.m{{background:var(--card);border:1px solid var(--bd);border-radius:11px;padding:12px 14px}}
.m .l{{font-size:12px;color:var(--ts)}} .m .v{{font-size:22px;font-weight:600;margin-top:2px}} .m .v.ok{{color:var(--ok)}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px 18px;margin-bottom:13px}}
.ct{{font-size:13px;font-weight:600;color:var(--ts);margin-bottom:10px}}
table{{width:100%;border-collapse:collapse;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px}}
th{{text-align:left;color:var(--tt);font-weight:400;padding:4px 0}} td{{padding:5px 0}} .r{{text-align:right}}
tr.ok td{{color:var(--ok)}} tr.ref td{{color:var(--ban-tx);text-decoration:line-through}}
.rsn{{text-decoration:none!important;font-size:11.5px;padding-bottom:8px!important}}
.cap{{font-family:ui-monospace,Menlo,monospace;font-size:11px;color:var(--tt);margin-top:6px}}
</style></head><body>__NAV__<div class="wrap" role="main">
<div class="top"><h1 class="h1" style="margin:0">__T_FINOPS_TITLE__</h1></div>
<div class="sub">__T_FINOPS_SUB__</div>
<div class="cards">
  <div class="m"><div class="l">__T_REV_LABEL__</div><div class="v">$__REV__</div></div>
  <div class="m"><div class="l">__T_COST_LABEL__</div><div class="v">$__COST__</div></div>
  <div class="m"><div class="l">__T_MARGIN_LABEL__</div><div class="v ok">$__MARGIN__</div></div>
</div>
<div class="card"><div class="ct">__T_PNL_CARD__</div>__PNLCHART__</div>
<div class="card"><div class="ct">__T_GATE_CARD__</div>
<svg viewBox="0 0 620 184" width="100%" role="img" aria-label="__T_GATE_ARIA__">
  <rect x="6" y="48" width="186" height="38" rx="9" style="fill:rgba(15,110,86,.13)"/>
  <text x="18" y="65" style="fill:var(--ok);font-size:13px;font-weight:500">__T_GATE_MATERIALITY__</text>
  <text x="18" y="79" style="fill:var(--ok);font-size:11px">__T_GATE_THRESHOLD__</text>
  <rect x="6" y="100" width="186" height="38" rx="9" style="fill:rgba(15,110,86,.13)"/>
  <text x="18" y="117" style="fill:var(--ok);font-size:13px;font-weight:500">__T_GATE_HEADROOM__</text>
  <text x="18" y="131" style="fill:var(--ok);font-size:11px">&gt; 0</text>
  <line x1="192" y1="67" x2="288" y2="84" style="stroke:var(--bd);stroke-width:2"/>
  <line x1="192" y1="119" x2="288" y2="108" style="stroke:var(--bd);stroke-width:2"/>
  <path d="M288 66 L326 66 A32 32 0 0 1 326 128 L288 128 Z" style="fill:var(--card);stroke:var(--ts);stroke-width:1.5"/>
  <text x="298" y="101" style="fill:var(--tp);font-size:13px;font-weight:500">AND</text>
  <line x1="308" y1="4" x2="308" y2="34" style="stroke:var(--tt);stroke-width:2;stroke-dasharray:4 4"/>
  <line x1="299" y1="38" x2="317" y2="56" style="stroke:var(--danger);stroke-width:2.5"/>
  <line x1="317" y1="38" x2="299" y2="56" style="stroke:var(--danger);stroke-width:2.5"/>
  <text x="328" y="15" style="fill:var(--tt);font-size:12px">__T_GATE_CROWD__</text>
  <text x="328" y="52" style="fill:var(--danger);font-size:11px;font-weight:500">__T_GATE_FIREWALL__</text>
  <line x1="358" y1="97" x2="422" y2="97" style="stroke:var(--bd);stroke-width:2"/>
  <rect x="422" y="66" width="192" height="62" rx="10" style="fill:var(--ban-bg)"/>
  <text x="436" y="88" style="fill:var(--ban-tx);font-size:14px;font-weight:500">__T_GATE_REFUSED__</text>
  <text x="436" y="105" style="fill:var(--ban-tx);font-size:11px">__T_GATE_OVER__</text>
  <text x="436" y="121" style="fill:var(--ban-tx);font-size:11px;font-weight:500">__T_GATE_NOSTRIPE__</text>
</svg>
<div class="cap">__T_GATE_CAP__</div></div>
<div class="card"><div class="ct">__T_RECEIPTS_CARD__</div>
<table><thead><tr><th>__T_TH_TYPE__</th><th>__T_TH_STATUS__</th><th class="r">__T_TH_AMOUNT__</th><th class="r">__T_TH_RECEIPT__</th></tr></thead>
<tbody>__ROWS__</tbody></table></div>
</div></body></html>"""

JOURNAL_HTML = f"""<!DOCTYPE html><html lang="__HTMLLANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>__T_TITLE_JOURNAL__</title>
<style>{_CSS}
body{{margin:0;background:var(--bg);color:var(--tp);line-height:1.5;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC",sans-serif}}
.wrap{{max-width:760px;margin:0 auto;padding:24px 20px 44px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:10px}}
.h1{{font-size:20px;font-weight:600}} a.back{{font-size:13px;color:var(--accent);text-decoration:none}}
.plan{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:13px 15px;margin:12px 0 6px;font-size:13px;color:var(--ts)}}
.plan b{{color:var(--tp);font-weight:600}}
.je{{display:flex;gap:14px;padding:13px 2px;border-top:1px solid var(--bd)}}
.jd{{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--ts);min-width:84px;padding-top:3px}}
.jb{{flex:1}} .ja{{display:flex;gap:6px;flex-wrap:wrap}}
.jbadge{{font-size:12px;font-weight:500;padding:3px 9px;border-radius:8px}}
.jbadge.act{{background:rgba(22,84,143,.13);color:var(--accent)}}
.jbadge.hold{{background:var(--bg);color:var(--ts);border:1px solid var(--bd)}}
.jmeta{{font-size:12px;color:var(--tt);margin-top:6px}}
.cap{{font-size:12px;color:var(--tt);margin-top:16px}}
</style></head><body>__NAV__<div class="wrap" role="main">
<div class="top"><h1 class="h1" style="margin:0">__T_JOURNAL_TITLE__</h1></div>
<div class="plan">__T_JOURNAL_PLAN_A__ <b>__N__</b> __T_JOURNAL_PLAN_B__</div>
__ROWS__
<div class="cap">__T_JOURNAL_FOOT__</div>
</div></body></html>"""

LOCKED_CHAT_HTML = (
    """<!DOCTYPE html><html lang="__HTMLLANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__T_TITLE_CHAT__</title>
<style>"""
    + _CSS
    + """
body{margin:0;background:var(--bg);color:var(--tp);line-height:1.5;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC","PingFang TC",sans-serif;min-height:100vh}
.lockwrap{max-width:560px;margin:11vh auto 0;padding:0 20px;text-align:center}
.lockcard{background:var(--card);border:1px solid var(--bd);border-radius:16px;padding:36px 28px}
.lockcard .ico{font-size:32px;line-height:1}
.lockcard h1{font-size:20px;margin:14px 0 8px}
.lockcard p{color:var(--ts);font-size:14px;margin:0 auto 22px;line-height:1.65;max-width:42ch}
.lockcard a.cta{display:inline-block;background:var(--u-bg);color:var(--u-tx);text-decoration:none;padding:11px 22px;border-radius:11px;font-weight:500}
.lockcard a.cta:hover{opacity:.92}
.lockcard .dis{margin-top:24px;font-size:11px;color:var(--tt)}
</style></head><body>__NAV__
<div class="lockwrap"><div class="lockcard">
<div class="ico">🔒</div>
<h1>__T_LOCK_TITLE__</h1>
<p>__T_LOCK_BODY__</p>
<a class="cta" href="/pricing">__T_LOCK_CTA__</a>
<div class="dis">__T_DISCLAIMER__</div>
</div></div></body></html>"""
)


INDEX_HTML = (
    """<!DOCTYPE html><html lang="__HTMLLANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__T_TITLE_CHAT__</title>
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
.err{color:var(--danger);font-size:13px}
.chips{display:flex;gap:8px;flex-wrap:wrap;max-width:860px;margin:0 auto;padding:0 20px}
.chip{font-size:13px;border:1px solid var(--bd);background:var(--card);color:var(--tp);border-radius:20px;padding:7px 13px;cursor:pointer}
.chip:hover{border-color:var(--accent)}
footer{border-top:1px solid var(--bd);padding:12px 18px}
form{display:flex;gap:9px;max-width:860px;margin:0 auto}
input{flex:1;font-size:15px;padding:11px 14px;border:1px solid var(--bd);border-radius:12px;background:var(--card);color:var(--tp);font-family:inherit}
input:focus{border-color:var(--accent)}
button{font-size:15px;padding:0 18px;border-radius:12px;border:none;background:var(--accent);color:#fff;cursor:pointer}
button:disabled{opacity:.5;cursor:default}
.foot-note{text-align:center;font-size:11px;color:var(--tt);margin-top:7px}
</style></head><body>__NAV__
<div id="log" role="main"><div class="row a"><div><div class="who">__T_WHO_ASSISTANT__</div>
<div class="bub">__T_CHAT_GREETING__</div></div></div></div>
<div class="chips" id="chips"></div>
<footer><form id="f"><input id="m" autocomplete="off" aria-label="__T_CHAT_INPUT_ARIA__"
  placeholder="__T_CHAT_PLACEHOLDER__" />
<button id="b" type="submit">__T_CHAT_SEND__</button></form>
<div class="foot-note">__T_CHAT_FOOTNOTE__</div></footer>
<script>
const log=document.getElementById('log'),form=document.getElementById('f'),inp=document.getElementById('m'),btn=document.getElementById('b');
const SUG=__T_SUG_JSON__;
const STAGES=__T_STAGES_JSON__;
const chips=document.getElementById('chips');
SUG.forEach(s=>{const c=document.createElement('div');c.className='chip';c.textContent=s;c.onclick=()=>{inp.value=s;inp.focus()};chips.appendChild(c)});
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}
function add(role,html){const r=document.createElement('div');r.className='row '+role;
  const w=role==='u'?'__T_WHO_USER__':'__T_WHO_ASSISTANT__';
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
  const tr=add('a','<span class="dots"><span></span><span></span><span></span></span><span class="hint"></span>');
  const bub=tr.querySelector('.bub');bub.setAttribute('role','status');bub.setAttribute('aria-live','polite');bub.setAttribute('aria-busy','true');
  const hintEl=tr.querySelector('.hint');let si=0;hintEl.textContent=STAGES[0];
  const timer=setInterval(()=>{si=Math.min(si+1,STAGES.length-1);hintEl.textContent=STAGES[si]},4500);
  try{
    const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})});
    const data=await res.json();
    bub.innerHTML = data.reply ? renderReply(data.reply) : ('<span class="err">__T_ERR_PREFIX__'+esc(data.error||'unknown')+'</span>');
  }catch(err){ bub.innerHTML='<span class="err">__T_CONN_FAIL__'+esc(String(err))+'</span>'; }
  finally{clearInterval(timer);bub.setAttribute('aria-busy','false');}
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
