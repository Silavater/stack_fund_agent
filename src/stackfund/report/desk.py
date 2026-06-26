"""Static HTML 'research desk' view of a pipeline result (presentation only).

Pure presentation: takes the dict from ``stackfund.cli.build_pipeline_result`` and
returns a self-contained HTML document — inline CSS + an inlined, *vendored* candlestick
library (TradingView lightweight-charts, Apache-2.0; see NOTICE), so there is **no CDN
and zero egress**. A server-rendered SVG sparkline is the no-JS fallback. It belongs to
the ``report/`` presentation layer — firewalled out of L4/L5 like the rest of ``report/``.
Nothing is computed here; it only renders numbers the deterministic engine produced.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

_CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tp);line-height:1.5;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans TC","PingFang TC",sans-serif;
  -webkit-font-smoothing:antialiased}
:root{--bg:#f4f4f2;--card:#fff;--tp:#1c1c1a;--ts:#6e6e68;--tt:#9b9b93;
  --bd:rgba(0,0,0,.10);--bd2:rgba(0,0,0,.18);
  --info-bg:#e8f0fb;--info-tx:#16548f;--hold-bg:#efeee8;--hold-tx:#6e6e68;
  --ok-bg:#e3f4ed;--ok-tx:#0f6e56;--warn-bg:#fbeede;--warn-tx:#8a5210;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
@media (prefers-color-scheme:dark){:root{--bg:#19191a;--card:#242423;--tp:#ededeb;
  --ts:#a6a6a2;--tt:#74746d;--bd:rgba(255,255,255,.12);--bd2:rgba(255,255,255,.22);
  --info-bg:#16314c;--info-tx:#88b9ec;--hold-bg:#2d2d2b;--hold-tx:#a6a6a2;
  --ok-bg:#103e33;--ok-tx:#62cba6;--warn-bg:#3d2a0a;--warn-tx:#f1ca88}}
.wrap{max-width:940px;margin:0 auto;padding:30px 20px 44px}
.top{display:flex;align-items:baseline;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-bottom:6px}
.h1{font-size:21px;font-weight:600;letter-spacing:-.01em}
.meta{font-size:13px;color:var(--ts);margin-top:2px}
.pill{font-size:12px;color:var(--tt);border:1px solid var(--bd);border-radius:8px;padding:5px 11px;white-space:nowrap}
.sec{font-size:13px;font-weight:600;color:var(--ts);margin:24px 0 9px}
.sec span{color:var(--tt);font-weight:400}
.grid{display:grid;gap:13px}
.etfs{grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.two{grid-template-columns:repeat(auto-fit,minmax(320px,1fr));margin-top:13px}
.kchart{height:138px;margin:9px 0 2px}
.kchart svg{margin:0}
.card{background:var(--card);border:1px solid var(--bd);border-radius:14px;padding:16px 18px}
.etf.featured{border:1.5px solid var(--info-tx)}
.ehead{display:flex;align-items:center;justify-content:space-between;margin-bottom:11px}
.ticker{font-size:17px;font-weight:600}
.badge{font-size:12px;font-weight:500;padding:3px 10px;border-radius:8px;white-space:nowrap}
.act{background:var(--info-bg);color:var(--info-tx)}
.hold{background:var(--hold-bg);color:var(--hold-tx)}
.big{font-size:23px;font-weight:600;margin-bottom:5px}
.big .sub{font-size:13px;font-weight:400;color:var(--ts);margin-left:7px}
.line{font-size:14px;color:var(--ts)}
.line b{color:var(--tp);font-weight:600}
.note{font-size:13px;color:var(--ts);margin-top:5px}
.mono{font-family:var(--mono);font-size:12px;color:var(--ts)}
.code{color:var(--info-tx);margin-bottom:6px;overflow-wrap:anywhere}
.reasons{margin-top:5px}
.cardhead{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.cardhead .t{font-size:13px;font-weight:600;color:var(--ts)}
.fw{font-size:11px;color:var(--warn-tx);border:1px solid var(--warn-tx);border-radius:8px;padding:2px 8px}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.metric{background:var(--bg);border-radius:9px;padding:11px 13px}
.metric .ml{font-size:12px;color:var(--ts)}
.metric .mv{font-size:20px;font-weight:600;margin-top:2px}
.metric .mv.ok{color:var(--ok-tx)}
.refused{display:flex;align-items:center;gap:6px;margin-top:11px;font-size:12.5px;color:var(--warn-tx)}
.crow{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:13.5px;padding:3px 0}
.crow .ck{font-weight:600}
.crow .cv{color:var(--ts);flex:1;margin:0 10px}
.foot{display:flex;align-items:center;gap:8px;margin-top:22px;font-size:12.5px;color:var(--tt)}
.dot{width:6px;height:6px;border-radius:50%;background:var(--ok-tx);flex:none}
""".strip()

# Injected only when the desk is embedded in the web app (render_desk_html(..., nav=...)).
# Styles the shared site nav using the desk's own theme vars, so it adapts light/dark.
_NAV_CSS = """
.nav{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;max-width:940px;margin:0 auto;padding:12px 20px;border-bottom:1px solid var(--bd)}
.nav a{text-decoration:none}.navlinks{display:flex;gap:2px;align-items:center}
.navlink{font-size:13px;color:var(--ts);padding:6px 11px;border-radius:8px}
.navlink:hover{background:var(--hold-bg);color:var(--tp)}
.navlink.on{color:var(--tp);font-weight:500;background:var(--hold-bg)}
.navlink.tog{border:1px solid var(--bd);font-weight:500}
""".strip()


def _esc(x: object) -> str:
    return html.escape(str(x))


# Brand wordmark: stacked-bars mark (stack + fund + growth) + "StackFund". The
# mark colour follows the desk accent (--info-tx) so it adapts to light/dark.
_WORDMARK = (
    '<span style="display:inline-flex;align-items:center;gap:9px;line-height:1">'
    '<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true" style="color:var(--info-tx);flex:none">'
    '<rect x="1" y="13" width="5" height="8" rx="1.3" fill="currentColor" opacity=".55"/>'
    '<rect x="8.5" y="8" width="5" height="13" rx="1.3" fill="currentColor"/>'
    '<rect x="16" y="3" width="5" height="18" rx="1.3" fill="currentColor" opacity=".8"/></svg>'
    '<span style="font-weight:600;letter-spacing:-.01em;color:var(--tp)">StackFund</span></span>'
)


def _price_chart_svg(series: object) -> str:
    """Server-rendered close-price sparkline (no JS, no CDN) — same pattern as the P&L bars.

    Presentation only: the series is illustrative market context, never a decision input.
    Green if the window closed up, amber if down.
    """
    pts = [float(x) for x in (series or []) if isinstance(x, (int, float))]
    if len(pts) < 2:
        return ""
    w, h, pad = 248, 46, 4
    lo, hi = min(pts), max(pts)
    rng = (hi - lo) or 1.0
    n = len(pts)
    xs = [pad + (w - 2 * pad) * i / (n - 1) for i in range(n)]
    ys = [pad + (h - 2 * pad) * (1 - (v - lo) / rng) for v in pts]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys, strict=True))
    col = "var(--ok-tx)" if pts[-1] >= pts[0] else "var(--warn-tx)"
    return (
        f'<svg viewBox="0 0 {w} {h}" width="100%" style="margin:9px 0 2px" role="img" '
        f'aria-label="close price · {n} sessions · last {pts[-1]:.2f}">'
        f'<polyline points="{poly}" fill="none" stroke="{col}" stroke-width="1.6" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="2.4" fill="{col}"/></svg>'
    )


# Interactive candlestick K-line via TradingView lightweight-charts (Apache-2.0),
# vendored + inlined so the desk stays a single self-contained file with NO CDN /
# zero egress. See NOTICE. The SVG sparkline above is the no-JS fallback.
_VENDOR = Path(__file__).resolve().parent / "vendor"
try:
    _LIGHTWEIGHT_JS = (_VENDOR / "lightweight-charts.standalone.production.js").read_text(
        encoding="utf-8"
    )
except OSError:  # vendored lib absent -> the SVG sparkline fallback stays
    _LIGHTWEIGHT_JS = ""

# Render a candlestick per #k_<symbol> from SF_CANDLES. Taiwan convention = red up /
# green down (inverse of the West). Clears the SVG fallback first.
_CANDLE_INIT_JS = """
(function(){var lw=window.LightweightCharts;if(!lw||!lw.createChart)return;
var RED="#d4452e",GREEN="#0e9f6e";
for(var sym in SF_CANDLES){var data=SF_CANDLES[sym];var el=document.getElementById("k_"+sym);
if(!el||!data||data.length<2)continue;el.innerHTML="";
var chart=lw.createChart(el,{height:138,localization:{locale:SF_LOCALE},
layout:{background:{color:"transparent"},textColor:"#8a8a85",fontFamily:"system-ui",attributionLogo:false},
grid:{vertLines:{visible:false},horzLines:{color:"rgba(128,128,128,0.14)"}},
rightPriceScale:{borderVisible:false},timeScale:{borderVisible:false,fixLeftEdge:true,fixRightEdge:true},
handleScroll:false,handleScale:false,crosshair:{mode:0}});
var s=chart.addSeries(lw.CandlestickSeries,{upColor:RED,downColor:GREEN,borderUpColor:RED,
borderDownColor:GREEN,wickUpColor:RED,wickDownColor:GREEN});
s.setData(data);chart.timeScale().fitContent();}})();
""".strip()


def _weekday_dates(end_iso: str, n: int) -> list[str]:
    """``n`` ascending weekday ISO dates ending at ``end_iso`` (the chart x-axis)."""
    import datetime

    try:
        d = datetime.date.fromisoformat(end_iso[:10])
    except (ValueError, TypeError):
        d = datetime.date(2026, 6, 19)
    out: list[str] = []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= datetime.timedelta(days=1)
    return list(reversed(out))


def _ohlc_from_closes(closes: list[float], dates: list[str]) -> list[dict]:
    """Illustrative OHLC candles from a close series (open = prev close + a small wick).

    Presentation only — the demo's close series is itself illustrative; this shapes it
    into candlesticks. With --live the closes are real (the wicks stay illustrative).
    """
    out: list[dict] = []
    prev = closes[0]
    for i, (dt, c) in enumerate(zip(dates, closes, strict=True)):
        o = prev
        top, bot = max(o, c), min(o, c)
        wick = c * 0.004
        hi = round(top + wick * (1 + (i % 3) * 0.35), 2)
        lo = round(bot - wick * (1 + ((i + 1) % 3) * 0.35), 2)
        out.append({"time": dt, "open": round(o, 2), "high": hi, "low": lo, "close": round(c, 2)})
        prev = c
    return out


def _etf_card(e: dict) -> str:
    sym = _esc(e["symbol"])
    chart = f'<div class="kchart" id="k_{sym}">{_price_chart_svg(e.get("price_series"))}</div>'
    if "delta_pp" in e:  # REBALANCE
        badge = f"REBALANCE {e['delta_pp']:+.2f}pp"
        reasons = " · ".join(_esc(r) for r in e.get("reasons", []))
        return (
            f'<div class="card etf featured"><div class="ehead">'
            f'<span class="ticker">{sym}</span>'
            f'<span class="badge act">{_esc(badge)}</span></div>'
            f"{chart}"
            f'<div class="big">{e["target_weight_pct"]:.1f}%<span class="sub">target weight</span></div>'
            f'<div class="line">benefit <b>{_esc(e["benefit_bps"])} bps</b> '
            f"&gt; cost {_esc(e['cost_bps'])} bps</div>"
            f'<div class="mono reasons">{reasons}</div></div>'
        )
    code = _esc((e.get("reason_codes") or ["NO_ACTION"])[0])
    note = _esc(e.get("no_action_reason") or "")
    return (
        f'<div class="card etf"><div class="ehead">'
        f'<span class="ticker">{sym}</span>'
        f'<span class="badge hold">NO_ACTION</span></div>'
        f"{chart}"
        f'<div class="mono code">{code}</div>'
        f'<div class="note">{note}</div></div>'
    )


def _crowd(etfs: list[dict]) -> str:
    rows = "".join(
        f'<div class="crow"><span class="ck">{_esc(e["symbol"])}</span>'
        f'<span class="cv">crowd {_esc(e["crowd_consensus"])} · engine {_esc(e["engine_posture"])}</span>'
        f'<span class="badge hold">{_esc(e["divergence_bucket"])}</span></div>'
        for e in etfs
    )
    return (
        '<div class="card"><div class="cardhead"><span class="t">Crowd vs engine</span>'
        '<span class="fw">non-authoritative · firewalled</span></div>'
        f"{rows}"
        '<div class="note" style="margin-top:9px">scenario rehearsal · synthetic personas · '
        "never moves a number</div></div>"
    )


def _finops(f: dict) -> str:
    refused = "".join(
        f'<div class="refused">refused spend · {_esc(r["reason"])}</div>'
        for r in f.get("refused", [])
    )
    return (
        '<div class="card"><div class="cardhead"><span class="t">FinOps — operational P&amp;L '
        '<span style="color:var(--tt);font-weight:400">· the business, not ETF P&amp;L</span>'
        "</span></div>"
        '<div class="metrics">'
        f'<div class="metric"><div class="ml">revenue</div><div class="mv">NT${_esc(f["revenue"])}</div></div>'
        f'<div class="metric"><div class="ml">cost</div><div class="mv">NT${_esc(f["cost"])}</div></div>'
        f'<div class="metric"><div class="ml">margin</div><div class="mv ok">NT${_esc(f["gross_margin"])}</div></div>'
        f"</div>{refused}</div>"
    )


# Scenario identifiers are Chinese data values; show an English gloss when lang=en.
_SCENARIO_EN = {
    "升息": "rate hike",
    "0056_cut": "0056 dividend cut",
    "電子權值回檔": "tech heavyweight pullback",
}


def render_desk_html(result: dict, nav: str = "", lang: str = "zh") -> str:
    m = result.get("meta", {})
    etfs = result.get("etfs", [])
    cards = "".join(_etf_card(e) for e in etfs)
    en = lang == "en"
    # Embedded in the web app, the shared nav carries the brand -> use a plain page title.
    h1_title = "Research desk" if en else "研究看板"
    h1 = _WORDMARK if not nav else f'<span style="font-weight:600">{h1_title}</span>'
    pill = (
        "Research / education · places no securities order"
        if en
        else "研究/教育 · 不下任何證券委託單"
    )
    scenario_raw = str(m.get("scenario", ""))
    scenario_disp = _SCENARIO_EN.get(scenario_raw, scenario_raw) if en else scenario_raw
    candles: dict[str, list[dict]] = {}
    for e in etfs:
        ser = [float(x) for x in (e.get("price_series") or []) if isinstance(x, (int, float))]
        if len(ser) >= 2:
            dates = _weekday_dates(str(m.get("as_of", "")), len(ser))
            candles[str(e["symbol"])] = _ohlc_from_closes(ser, dates)
    body = (
        '<div class="wrap"><div class="top"><div>'
        f'<div class="h1">{h1}</div>'
        f'<div class="meta">Taiwan ETF research desk · deterministic engine · scenario {_esc(scenario_disp)} · '
        f"seed {_esc(m.get('seed', ''))} · formula {_esc(m.get('formula_version', ''))} · "
        f"as of {_esc(m.get('as_of', ''))} · "
        f"{'live data' if m.get('live') else 'frozen fixtures'}</div></div>"
        f'<span class="pill">{_esc(pill)}</span></div>'
        '<div class="sec">Rebalance decisions <span>· engine (authoritative)</span></div>'
        f'<div class="grid etfs">{cards}</div>'
        f'<div class="grid two">{_finops(result.get("finops", {}))}{_crowd(etfs)}</div>'
        '<div class="foot"><span class="dot"></span>every number computed by the engine · '
        "the model only interprets · StackFund places no securities orders</div></div>"
    )
    scripts = ""
    if _LIGHTWEIGHT_JS and candles:
        scripts = (
            f"<script>{_LIGHTWEIGHT_JS}</script>"
            f"<script>const SF_CANDLES={json.dumps(candles, ensure_ascii=False)};"
            f"const SF_LOCALE={json.dumps('en-US' if en else 'zh-TW')};"
            f"{_CANDLE_INIT_JS}</script>"
        )
    css = _CSS if not nav else f"{_CSS}\n{_NAV_CSS}"
    return (
        f'<!DOCTYPE html><html lang="{"en" if en else "zh-Hant"}"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>StackFund — research desk</title>"
        f"<style>{css}</style></head><body>{nav}{body}{scripts}</body></html>"
    )
