# StackFund × Hermes — 整合報告 (Hermes Integration Report)

> 狀態(2026-06-22):**Hermes agent 端到端可跑**。模型走自架 gateway 的 `gpt-5.5`,
> 兩個 StackFund skill(`etf-analysis` / `crowd-scenario`)都能由 agent 自主執行確定性
> 引擎並解讀,且 agent 已被 `SOUL.md` 塑形成「StackFund 研究台」人設(守法規、分帳、拒絕越界)。

---

## 1. 一眼看懂:跑起來的這隻 agent

```
使用者 prompt
  │
  ▼
Hermes Agent harness  ──  模型: gpt-5.5  (provider=custom → 你的 gateway, OpenAI-wire)
  │                        身分: agent/SOUL.md(每則訊息逐字注入成 developer 角色)
  ▼
Agent Skills(/opt/data/skills/research/)
  ├─ stackfund-etf-analysis   → python -m stackfund pipeline   (L1→L2→L4→L5→L6)
  └─ stackfund-crowd-scenario → python -m stackfund crowd       (L3 FACE 側軌)
  │
  ▼
StackFund 確定性引擎(baked 進 image,/opt/stackfund)
  └─ 算出每個數字 → agent 只解讀、寫文字、守防火牆
```

實測:同一個「研究 0056 + 我該不該全押 30 萬」的 prompt,agent 會跑引擎拿真數字
(`REBALANCE +5.00pp`、target 37.4%、benefit 81 vs cost 19 bps、reason codes)、把它框成
**研究情境示意配置**、**拒絕**個別化買賣建議、**分開三本帳**、**標註資料新鮮度**、**聲明不下單**。

---

## 2. 模型接線(最花時間的部分,已解)

### 2.1 為什麼不是 opus
opus 4.7/4.8 走你 gateway 背後的 **Claude 訂閱(Max 20x)**。Anthropic 新政策把
**帶 agentic 工具的第三方 app 請求**改從「**extra usage**」額度池扣,而該帳號這個池是**關著的**
→ 回 `HTTP 400「Add more at claude.ai/settings/usage」`;Hermes 把它誤判成 format error → 空回應。
證據(對 64KB 真實請求做 bisect):拿掉 tools → 200;把工具**改名** `tool_0…` → 200;`gpt-5.5` + 工具 → 200。
**結論:這是 gateway 帳號的 billing 開關,不是 Hermes/設定問題。** 要用 opus 就把 Usage Credits 打開。

### 2.2 gpt-5.5 怎麼接成功(可重現)
| 卡點 | 解法 |
|---|---|
| `custom` provider 不讀 `CUSTOM_API_KEY` | key 放**憑證池**:`hermes auth add custom:y2k --api-key …`(寫進 `.hermes-data/auth.json`) |
| 憑證池要靠 base_url 對應 | config.yaml 加 `custom_providers: [{name: y2k, base_url: …:8317/v1, api_mode: chat_completions}]` |
| 模型名稱自動偵測會蓋掉 custom | 一定要**明確帶旗標** `-m gpt-5.5 --provider custom` |
| oneshot pre-flight 掃 `os.environ` 找 key | `docker run` 要加 `--env-file docker/agent.env` |
| Git Bash 把 `-v /c/…` 的 `/opt/data` 改寫壞掉 | 腳本加 `MSYS_NO_PATHCONV=1` + `cygpath -m`(→ `C:/…`) |

> 一鍵設定:`./docker/setup-custom-model.sh`(註冊 custom provider + key,key 從 `agent.env` 讀,不外露)。

---

## 3. Agent 身分(把 Hermes「訓練」成 StackFund)

不是訓練模型,而是用 **`agent/SOUL.md`**(Hermes 每則訊息**逐字注入**的 developer prompt;
此載入路徑由多代理 workflow 拿**真實 request dump** 驗證過)把行為定死:

- **身分/使命**:自主台股 ETF 研究台 + 自負盈虧 micro-business。
- **硬規則(不可違反)**:① 研究/教育、非個別化投資建議、**全程不下證券委託單**
  ② 引擎算每個數字,模型**不得捏造**;③ L3 群眾層**非權威**、不決定數字、不回寫決策(L4 只吃
  `AuthoritativeState`);④ **三本帳分離**(模擬組合 / Stripe FinOps / Experiment);
  ⑤ value-mode `[A]–[E]` 評等只當「結構品質分類」,**不准**變成對個股的買/賣/避開指令。
- **SOP**:normalize → 先抓官方 TWSE 資料 → L2 評分 → L4 決策(NO_ACTION 一等公民)→ 報告(事實先行)。
- **免責 banner**、**講話風格**(謹慎、非絕對買賣)、**FinOps**(earn/spend/VoI 上限/拒付路徑)。

對抗式檢查抓到並修掉一個真漏洞:value-mode 評等原本會變成對個股的「找機會賣出/盡快避開」指令 → 已改為非個別化結構分類。
`agent/AGENTS.md` 為輔助參考(Hermes 只在 cwd 無 `.hermes.md` 時才載入,非主力)。

> 同場加映「drift fix」:`crowd-scenario` skill 描述 / references / `__init__.py` / README 殘留的舊
> `ContrarianSignal` / `contrarian_modifier ∈ [-1,+1]` 字眼,已全部更正為現行的
> `CrowdNarrative` / 類別型 `crowd_consensus` / `non_authoritative` 合約。

---

## 4. 怎麼跑(demo 三步)

```bash
# 1) 建 agent image(Hermes harness + 引擎 + skills)— 只需一次
docker build -f docker/Dockerfile.agent -t stackfund-agent:dev .

# 2) 註冊 custom provider + key — 只需一次
./docker/setup-custom-model.sh

# 3a) 一次性 demo(印出 agent 跑完的研究)
./docker/run-agent.sh
./docker/run-agent.sh "研究 0056,用 etf-analysis skill 給再平衡決策"

# 3b) 互動式「看著它跑」(TUI,在你自己的終端機)
./docker/run-chat.sh        # 打字、/exit 離開

# 健康檢查(只驗模型端點會回話)
./docker/verify-model.sh    # → HERMES OK
```
Windows 有對應的 `*.ps1`。模型可用 `HERMES_MODEL` / `HERMES_PROVIDER` 覆蓋。

---

## 5. 交付清單(都在 `feat/data-layer`)

| 檔案 | 作用 |
|---|---|
| `agent/SOUL.md` / `agent/AGENTS.md` | agent 身分/硬規則(SOUL = 每訊息逐字注入) |
| `docker/Dockerfile.agent` | Hermes + 引擎(`stackfund==0.1.0`)+ skills baked |
| `docker/setup-custom-model.sh` + `setup_custom_provider.py` | 一鍵註冊 custom provider + 憑證池 |
| `docker/run-agent.sh` / `.ps1` | 跑一個 prompt(自動刷新 SOUL、掛 skills、帶旗標) |
| `docker/run-chat.sh` | 互動 TUI |
| `docker/verify-model.sh` / `.ps1` | 模型端點健康檢查 |
| 機密(**gitignored,不入庫**) | `docker/agent.env`、`.hermes-data/`(config + `auth.json` 憑證池) |

---

## 6. 未解 / 建議

1. **opus**:要用就在 gateway 帳號開 `claude.ai/settings/usage` 的 **Usage Credits**;否則 `gpt-5.5` 已夠且不撞牆。
2. **deadline**:仍待向官方頻道確認;交付物是 1–3 分鐘 demo 影片。
3. **錄影建議**:用 `run-chat.sh` 現場問一題研究 + 一題「我該不該全押」,讓畫面同時呈現
   **引擎真數字 + 拒絕個別化建議 + 防火牆聲明** —— 這三點就是 StackFund 的核心賣點。
4. **(可選)** 把 `gateway run` 訊息服務 / web dashboard 接好(目前 demo 用 oneshot + chat,已足夠)。

> 相關設計細節見 [`doc/ARCHITECTURE.md`](ARCHITECTURE.md)。
