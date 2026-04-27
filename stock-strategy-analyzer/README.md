# stock-strategy-analyzer

## 1) 專案目的
`stock-strategy-analyzer` 是一個 CLI 股票策略分析工具，依據歷史日 K 資料（OHLCV）與技術指標，評估股票在指定交易日的策略條件。第一版支援：

- `risk_reward`：低風險風報比分析
- `momentum`：飆股 / 強勢動能分析

第一版**不包含**：看跌模式、推播、AI 預測、自動下單、財報分析、新聞分析、回測系統。

---

## 2) 安裝方式
```bash
cd stock-strategy-analyzer
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 3) CLI 使用方式
```bash
python main.py --symbol <SYMBOL> --lookback <20|60|120|240> --mode <loose|standard|strict> --strategy <risk_reward|momentum> [--analysis-date YYYY-MM-DD]
```

### 參數說明
- `--symbol`：股票代號（例：`2330.TW`、`AAPL`、`TSLA`）
- `--lookback`：分析週期（僅允許 `20/60/120/240`）
- `--mode`：篩選模式（僅允許 `loose/standard/strict`）
- `--strategy`：策略模式（僅允許 `risk_reward/momentum`）
- `--analysis-date`：分析基準日（選填，格式 `YYYY-MM-DD`）

### CLI 範例
```bash
python main.py --symbol 2330.TW --lookback 60 --mode standard --strategy risk_reward
python main.py --symbol AAPL --lookback 120 --mode strict --strategy risk_reward --analysis-date 2025-10-01
python main.py --symbol 3661.TW --lookback 60 --mode standard --strategy momentum
python main.py --symbol TSLA --lookback 60 --mode strict --strategy momentum --analysis-date 2025-10-01
```

---

## 4) 日期與資料規則（避免 Future Leakage）
1. `analysis_date` 是分析基準日。
2. 若未提供 `analysis_date`，使用最新交易日。
3. 若 `analysis_date` 非交易日，回退到前一個最近交易日（`effective_analysis_date`）。
4. 所有指標僅能使用 `effective_analysis_date`（含）以前資料。
5. 不可使用 `effective_analysis_date` 之後資料。
6. `lookback` 是**交易日**，不是自然日。
7. `recent_high/recent_low` 以 `effective_analysis_date` 往前 `lookback` 個交易日計算。

---

## 5) 共用技術指標
系統會計算下列共用欄位：

- MA5 / MA10 / MA20 / MA60 / MA120
- ATR14
- Volume MA5 / Volume MA20
- recent_high / recent_low
- return_5d_pct / return_20d_pct / return_60d_pct
- distance_to_ma20_pct
- distance_to_recent_high_pct
- distance_to_recent_low_pct
- atr_pct = ATR14 / close * 100

ATR14 計算：
- `TR = max(High-Low, abs(High-PrevClose), abs(Low-PrevClose))`
- `ATR14 = 最近 14 日 TR 平均`

---

## 6) 共用輸出欄位說明
所有策略都會輸出下列欄位（數值四捨五入到小數點後 2 位）：

- `symbol`：股票代號
- `strategy`：策略名稱
- `analysis_date`：使用者輸入日期（可為 `null`）
- `effective_analysis_date`：實際分析交易日
- `close` / `volume`：分析日收盤價與成交量
- `lookback_days`：分析交易日區間
- `filter_mode`：`loose/standard/strict`
- `ma5/ma10/ma20/ma60/ma120`
- `volume_ma5/volume_ma20`
- `atr14/atr_pct`
- `recent_high/recent_low`
- `return_5d_pct/return_20d_pct/return_60d_pct`
- `distance_to_ma20_pct`
- `distance_to_recent_high_pct`
- `distance_to_recent_low_pct`
- `passed_filter`：是否通過模式篩選
- `reasons`：繁體中文理由陣列

---

## 7) 策略一：risk_reward（低風險風報比）
核心問題：如果現在進場，預估報酬是否大於預估虧損？風險是否可控？

### 7.1 主要邏輯摘要
- `target_price = recent_high`
- `expected_return_pct = (target_price - close) / close * 100`
- `structure_stop_price = recent_low`
- `volatility_stop_price = close - 2 * ATR14`
- `stop_loss_price = min(structure_stop_price, volatility_stop_price)`
- `expected_loss_pct = (close - stop_loss_price) / close * 100`
- `risk_reward_ratio = expected_return_pct / expected_loss_pct`

### 7.2 風險等級 risk_grade（A/B/C/D/E）完整條件
> 注意：`E` 優先權最高，符合即直接回傳 `E`。

#### E（最高風險）
符合任一：
- `trend == weak`
- `expected_loss_pct > 10`
- `atr_pct >= 8`
- `expected_return_pct <= 0`

#### A
需同時符合：
- `risk_reward_ratio >= 3`
- `trend == bullish`
- `expected_loss_pct <= 5`

#### B
需同時符合：
- `risk_reward_ratio >= 2`
- `trend in [bullish, neutral_bullish]`
- `expected_loss_pct <= 8`

#### C
- `risk_reward_ratio >= 1.2`

#### D
- `risk_reward_ratio < 1.2`

#### 波動限制
- 若 `volatility_level == extreme`，等級最高只能是 `C`（A/B 會降為 C）。
- 若 `atr_pct >= 8`，直接 `E`。

### 7.3 risk_reward 篩選條件（loose / standard / strict）

#### loose
- `risk_reward_ratio >= 1.5`
- `expected_loss_pct <= 10`
- `close > MA60`

#### standard
- `risk_reward_ratio >= 2`
- `expected_loss_pct <= 8`
- `close > MA20`
- `close > MA60`
- `volume >= volume_ma20 * 0.8`
- `volatility_level != extreme`

#### strict
- `risk_reward_ratio >= 3`
- `expected_loss_pct <= 5`
- `close > MA20`
- `MA20 > MA60`
- `volume >= volume_ma20`
- `volatility_level in [low, medium]`
- `distance_to_recent_high_pct >= 2`

### 7.4 risk_reward 額外輸出欄位
- `trend`
- `target_price`
- `structure_stop_price`
- `volatility_stop_price`
- `stop_loss_price`
- `expected_return_pct`
- `expected_loss_pct`
- `risk_reward_ratio`
- `stop_atr_multiple`
- `volatility_level`
- `risk_grade`

---

## 8) 策略二：momentum（飆股 / 強勢動能）
核心問題：是否正在轉強或加速？是否已過熱、追高、容易回殺？

> `momentum_grade` 代表動能，不代表低風險。

### 8.1 momentum_score 規則表（0 ~ 100）

#### 加分規則
| 類別 | 條件 | 分數 |
|---|---|---:|
| 價格突破 | `close > recent_high` | +25 |
| 接近突破 | `0 <= distance_to_recent_high_pct <= 3` | +10 |
| 量能放大 | `volume_ratio >= 2` | +20 |
| 量能放大 | `1.5 <= volume_ratio < 2` | +12 |
| 量能放大 | `1.0 <= volume_ratio < 1.5` | +5 |
| 量能趨勢 | `volume_ma5_ratio >= 1.5` | +10 |
| 量能趨勢 | `1.2 <= volume_ma5_ratio < 1.5` | +5 |
| 均線多頭 | `close > MA5 > MA10 > MA20 > MA60` | +20 |
| 偏多結構 | `close > MA20 > MA60` | +10 |
| 短線漲幅 | `8 <= return_5d_pct <= 20` | +10 |
| 短線漲幅 | `3 <= return_5d_pct < 8` | +5 |
| 中期漲幅 | `15 <= return_20d_pct <= 40` | +10 |
| 中期漲幅 | `8 <= return_20d_pct < 15` | +5 |
| 價格強度 | `close > MA20 且 close > MA60` | +5 |

#### 扣分規則
| 類別 | 條件 | 分數 |
|---|---|---:|
| 過熱 | `return_5d_pct > 30` | -15 |
| 過熱 | `return_20d_pct > 60` | -15 |
| 波動過大 | `atr_pct > 8` | -10 |
| 波動過大 | `atr_pct > 12`（額外） | -10 |

#### 限制規則
- 若 `close < MA20`，`momentum_score` 最高只能 `49`
- 若 `volume_ratio < 0.8`，`momentum_score` 最高只能 `59`
- 最終限制在 `0 ~ 100`

### 8.2 momentum_grade 分級條件
- `A`：`momentum_score >= 80`
- `B`：`65 <= momentum_score < 80`
- `C`：`50 <= momentum_score < 65`
- `D`：`35 <= momentum_score < 50`
- `E`：`momentum_score < 35`

### 8.3 risk_score（追高/過熱/波動/假突破/流動性）規則表（0 ~ 100）

| 類別 | 條件 | 分數 |
|---|---|---:|
| ATR 波動風險 | `atr_pct < 2` | +5 |
| ATR 波動風險 | `2 <= atr_pct < 4` | +15 |
| ATR 波動風險 | `4 <= atr_pct < 6` | +30 |
| ATR 波動風險 | `6 <= atr_pct < 8` | +45 |
| ATR 波動風險 | `atr_pct >= 8` | +60 |
| 離 MA20 過遠 | `distance_to_ma20_pct > 20` | +30 |
| 離 MA20 過遠 | `12 < distance_to_ma20_pct <= 20` | +20 |
| 離 MA20 過遠 | `6 < distance_to_ma20_pct <= 12` | +10 |
| 5 日過熱 | `return_5d_pct > 30` | +30 |
| 5 日過熱 | `20 < return_5d_pct <= 30` | +20 |
| 5 日過熱 | `12 < return_5d_pct <= 20` | +10 |
| 20 日過熱 | `return_20d_pct > 60` | +25 |
| 20 日過熱 | `40 < return_20d_pct <= 60` | +15 |
| 假突破風險 | `close > recent_high 且 volume_ratio < 1.5` | +25 |
| 接近突破但無量 | `接近 recent_high 且 volume_ratio < 1` | +15 |
| 上影線風險 | `upper_shadow_pct >= 5` | +20 |
| 上影線風險 | `3 <= upper_shadow_pct < 5` | +10 |
| 流動性風險 | `volume_ma20 < 500000` | +20 |
| 流動性風險 | `volume_ma20 < 100000` | +40 |

> 註：台股與美股成交量單位不同，此為第一版粗略規則，正式使用可依市場調整門檻。

### 8.4 risk_level 分級條件
- `low`：`risk_score < 30`
- `medium`：`30 <= risk_score < 60`
- `high`：`60 <= risk_score < 80`
- `extreme`：`risk_score >= 80`

### 8.5 momentum 篩選條件（loose / standard / strict）

#### loose
- `momentum_score >= 55`
- `risk_score < 80`
- `close > MA20`

#### standard
- `momentum_score >= 65`
- `risk_score < 70`
- `close > MA20`
- `volume_ratio >= 1.2`

#### strict
- `momentum_score >= 80`
- `risk_score < 60`
- `close > MA20`
- `close > MA60`
- `volume_ratio >= 1.5`
- `risk_level in [low, medium]`

### 8.6 momentum 額外輸出欄位
- `momentum_score`
- `momentum_grade`
- `risk_score`
- `risk_level`
- `final_decision`
- `volume_ratio`
- `volume_ma5_ratio`
- `upper_shadow_pct`
- `breakout_status`
- `volume_status`
- `trend_status`
- `overheat_status`

---

## 9) JSON 輸出範例

### 9.1 risk_reward 範例
```json
{
  "symbol": "2330.TW",
  "strategy": "risk_reward",
  "analysis_date": null,
  "effective_analysis_date": "2026-04-27",
  "close": 100.0,
  "volume": 1200000,
  "lookback_days": 60,
  "filter_mode": "standard",
  "ma5": 98.2,
  "ma10": 97.5,
  "ma20": 96.8,
  "ma60": 93.1,
  "ma120": 89.6,
  "volume_ma5": 1100000,
  "volume_ma20": 1000000,
  "atr14": 5.0,
  "atr_pct": 5.0,
  "recent_high": 115.0,
  "recent_low": 96.0,
  "return_5d_pct": 3.8,
  "return_20d_pct": 11.4,
  "return_60d_pct": 19.2,
  "distance_to_ma20_pct": 3.2,
  "distance_to_recent_high_pct": 15.0,
  "distance_to_recent_low_pct": 4.0,
  "trend": "bullish",
  "target_price": 115.0,
  "structure_stop_price": 96.0,
  "volatility_stop_price": 90.0,
  "stop_loss_price": 90.0,
  "expected_return_pct": 15.0,
  "expected_loss_pct": 10.0,
  "risk_reward_ratio": 1.5,
  "stop_atr_multiple": 2.0,
  "volatility_level": "high",
  "risk_grade": "C",
  "passed_filter": false,
  "reasons": [
    "股價位於 MA20 與 MA60 之上，趨勢偏多",
    "預估報酬率為 15.0%，預估虧損率為 10.0%，風報比為 1.5",
    "ATR 波動率為 5.0%，屬於高波動",
    "停損距離約為 2.0 倍 ATR，停損距離合理",
    "ATR 波動率偏高，需降低部位或提高風險控管",
    "不符合 standard 篩選條件"
  ]
}
```

### 9.2 momentum 範例
```json
{
  "symbol": "3661.TW",
  "strategy": "momentum",
  "analysis_date": null,
  "effective_analysis_date": "2026-04-27",
  "close": 100.0,
  "volume": 2300000,
  "lookback_days": 60,
  "filter_mode": "standard",
  "ma5": 95.0,
  "ma10": 92.0,
  "ma20": 89.0,
  "ma60": 80.0,
  "ma120": 75.0,
  "volume_ma5": 1600000,
  "volume_ma20": 1000000,
  "atr14": 5.6,
  "atr_pct": 5.6,
  "recent_high": 98.0,
  "recent_low": 70.0,
  "return_5d_pct": 18.2,
  "return_20d_pct": 24.1,
  "return_60d_pct": 53.3,
  "distance_to_ma20_pct": 11.0,
  "distance_to_recent_high_pct": -2.0,
  "distance_to_recent_low_pct": 30.0,
  "momentum_score": 82,
  "momentum_grade": "A",
  "risk_score": 58,
  "risk_level": "medium",
  "final_decision": "強勢動能，風險尚可控，可列入觀察",
  "volume_ratio": 2.3,
  "volume_ma5_ratio": 1.6,
  "upper_shadow_pct": 1.2,
  "breakout_status": "突破 lookback 區間高點",
  "volume_status": "成交量為 20 日均量 2.3 倍，量能明顯放大",
  "trend_status": "均線多頭排列",
  "overheat_status": "近 5 日漲幅偏大，追高風險升高",
  "passed_filter": true,
  "reasons": [
    "收盤價突破 lookback 區間高點，價格進入強勢區",
    "成交量為 20 日均量 2.3 倍，量能明顯放大",
    "MA5 > MA10 > MA20 > MA60，均線呈現多頭排列",
    "近 5 日漲幅為 18.2%，具備短線動能但仍需注意追高風險",
    "ATR 波動率為 5.6%，屬於高波動",
    "動能分數為 82，風險分數為 58",
    "符合 standard 篩選條件"
  ]
}
```

---

## 10) 錯誤輸出格式
統一使用：

```json
{
  "error": "錯誤訊息"
}
```

常見錯誤包含：
- symbol 抓不到資料
- `lookback/mode/strategy` 非允許值
- `analysis_date` 格式錯誤
- `analysis_date` 早於資料起始日
- 資料不足（MA120 / ATR14 / lookback）
- 指標出現 NaN

---

## 11) 重要提醒
- 本工具不是投資建議，僅根據歷史 K 線做量化分析。
- `yfinance` 資料可能延遲、缺漏或不完整，正式使用前請自行驗證資料來源品質。
