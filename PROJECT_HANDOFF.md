# Souler 專案交接文件（Project Handoff）

> 最後更新：2026-07-15（第二版：使用者 iPhone 實測回饋後的迭代）。

## 0-1. 聊天即時性收尾（2026-07-15 下午）
- 已讀/未讀完成：`Message.is_read`、`POST /chatrooms/<id>/read/`（標已讀+廣播 read 事件）、列表 `unread_count`、前端已讀標記與未讀徽章
- 聊天強韌化：聊天室標題旁連線狀態點（綠=WS 即時、橘=輪詢中）；WS 斷線自動改 5 秒輪詢（id 去重），訊息保證必達
- 使用者實測確認：即時訊息/已讀/時間戳全部正常；偶發 5-10 秒延遲=免費層特性（共享 CPU、Neon 休眠喚醒、WS 短暫掉線由輪詢補）— 使用者接受，非功能性優化留待後續驗收
- 曾發生的部署事故（供借鑑）：重建服務時 DATABASE_URL 沒設 → API 靜默退回 ephemeral sqlite（資料會隨部署消失）。診斷法：透過 API 寫入資料後直接查 Neon 看有沒有進去
- 下一步：AI 解盤功能（等使用者提供 ANTHROPIC_API_KEY 到 Render 環境變數）；已討論定價（合盤單點 ~US$3、個人盤低價/免費當鉤子）；樂觀渲染送訊（提過但暫緩）

## 0. 最新一輪變更（回應實測回饋）
- **lag 根因**：render.yaml 原漏設 region（預設 Oregon）與新加坡 Neon 跨太平洋 → 已改 `region: singapore`，**需在 Render 刪除 souler-api 與 souler-redis 後 Manual sync 重建**（region 不能原地改）；重建時要重貼 DATABASE_URL
- **聊天吃訊息**：發送改走 REST（失敗還原輸入框）、後端寫入後 channel layer 廣播、前端以訊息 id 去重；泡泡加 HH:mm 時間戳
- **註冊 onboarding**：註冊完直進出生資料頁（時間預設 12:00＋不確定提示）；出生資料前 3 次修改免費、之後 30 天一次（`chart_edit_count`/`last_chart_edit_at`）；配對頁有無星盤引導卡
- **星盤 v2**：natal-chart API 改回傳 `{planets, house_cusps}`（12 宮頭即時算）＋ `is_retrograde`；前端重繪含相位連線（120綠/60青/180藍/90紅）、宮位線/號碼、刻度環、中文星座、逆行 R
- **商業模式討論中**：單點解鎖優先（合盤=配對成功當下的付費觸發點、個人盤=低價或免費鉤子），月費後補；定價約 US$3 量級，詳見對話
- 待辦新增：聊天已讀/未讀（DB+WS 事件+未讀數）、動畫/畫面打磨（低優先）本文件記錄專案完整現況與開發歷程，供後續開發者（人類或 AI）接手。
> 使用者（專案擁有者）是程式初學者，偏好由協作者主導技術決策並解釋理由，且期望「每完成一段工作就 commit + push + 實測驗證」。

## 一、專案是什麼

**Souler**：占星交友 app。核心玩法 — 使用者填出生資料 → 計算本命星盤 → 以雙方星盤「相位計分」產生配對名單 → Tinder 式滑動 like/dislike → 互相喜歡自動開聊天室 → WebSocket 即時聊天。

## 二、程式碼與線上環境

| 項目 | 位置 |
|---|---|
| 後端 repo | github.com/Owenkuo3/souler（public）|
| 前端 repo | github.com/Owenkuo3/souler_fe（private）|
| 本機後端 | `~/Documents/souler-main`（repo 根目錄有 venv）|
| 本機前端 | `~/Documents/souler_fe-main` |
| **線上 API** | https://souler-api.onrender.com |
| **線上網頁版** | https://souler-web.onrender.com |
| 資料庫（雲端） | Neon PostgreSQL，region=Singapore，帳號在使用者的 Neon 上 |
| Redis（雲端） | Render Key-Value（free）|

部署方式：`render.yaml`（本 repo 根目錄）是 Render Blueprint。**push main 分支即自動部署**（souler repo → souler-api；souler_fe repo → souler-web 靜態站，build 時自行 clone Flutter SDK 並以 `--dart-define=API_HOST=souler-api.onrender.com --dart-define=API_SECURE=true` 編譯）。全部使用免費層，月費 $0。

### 免費層已知限制
- 閒置 15 分鐘休眠，冷啟動約 30–60 秒
- 上傳的照片存本機磁碟，**重新部署會消失**（media 由 Django 直接服務，見 urls.py 註解；正式營運前應接 Cloudinary/S3）
- Email 仍是 console backend：**驗證碼要到 Render → souler-api → Logs 搜「驗證碼」**，或查 DB 的 `api_emailverificationcode` 表。接 SMTP 只需在 Render 設 `EMAIL_HOST/EMAIL_HOST_USER/EMAIL_HOST_PASSWORD` 環境變數（settings.py 已支援，寄信邏輯已用 send_mail 實作）

## 三、技術棧與架構

**後端**（Django 4.2）：
- `api/` app = 全部的 REST API（`/api/v1/`），其餘 app（accounts/users/astrology/matching/chat）只留 models 與服務邏輯 — **舊的 server-rendered views/templates 已全數刪除**
- 認證：SimpleJWT（access 7 天/refresh 30 天，`UPDATE_LAST_LOGIN=True`）+ email 六位數驗證碼註冊流程
- 星盤：pyswisseph（Placidus 宮位制、UTC+8 寫死、行星名存中文「太陽/月亮/...」+ 軸點「上升/下降/天頂/天底」，共 14 點存 `PlanetPosition`）
- 配對：`matching/service/aspect_matching.py` 相位計分（合相/六合/刑/拱/衝等 8 種相位 × 行星權重）；`matching_logic.py` 過濾（性別偏好、7 天內登入、有出生資料、排除已滑過）並快取進 `MatchScore`
- 聊天：Django Channels + Redis（channel layer 三段式：`REDIS_URL` > `REDIS_HOST` > InMemory），WebSocket 路由 `ws/chat/<room_id>/?token=<jwt>`（`JWTAuthMiddleware` 在 middleware.py）
- 設定全部環境變數化：`SECRET_KEY/DEBUG/ALLOWED_HOSTS/DATABASE_URL/REDIS_URL/CORS_ALLOWED_ORIGINS/CSRF_TRUSTED_ORIGINS/EMAIL_*`，本機無環境變數時退回開發預設（sqlite + InMemory + console email）

**前端**（Flutter，Dart ^3.8，Provider 狀態管理）：
- 畫面：登入、註冊（三步驟驗證碼流程）、主頁三分頁（配對滑動/訊息/個人）、出生資料輸入（日期+時間+城市下拉）、星盤頁（CustomPaint 手繪輪盤+星體列表）、聊天室（REST 歷史 + WebSocket 即時 + 指數退避重連）
- `lib/env.dart`：`--dart-define=API_HOST=...`（host）與 `API_SECURE=true`（https/wss）控制後端位址
- 啟動自動登入：`main.dart` 呼叫 `tryAutoLogin()`，token 未過期直接進主頁

**API 一覽**（`api/urls.py`）：
```
POST /api/v1/request-verification-code/  → 寄驗證碼
POST /api/v1/verify-code/                → 驗證
POST /api/v1/register/                   → 註冊（需先驗證 email）
POST /api/v1/token/  /token/refresh/     → JWT
GET/PATCH /api/v1/user/profile/          → 個人資料（photo 用 multipart PATCH）
GET/POST/PATCH /api/v1/birth-info/       → 出生資料（存檔即自動重算星盤）
GET  /api/v1/cities/                     → 支援城市清單（27 城，寫死座標表）
GET  /api/v1/natal-chart/                → 星盤 14 點 JSON
GET  /api/v1/candidates/                 → 配對卡片（user_id/nickname/bio/photo/age/sun_sign/match_score）
POST /api/v1/match/action/               → like/dislike，配對成功回 matched/room_id/matched_nickname
GET  /api/v1/chatrooms/                  → 聊天室列表（含 last_message/last_message_time）
GET/POST /api/v1/chatrooms/<id>/messages/ → 訊息（sender 為 user id 整數，timestamp ISO）
```
WebSocket 廣播格式與 REST 一致：`{id, sender, sender_nickname, content, timestamp}`。

## 四、這輪開發做了什麼（2026-07-14 ~ 07-15）

### 修掉的重大 bug（接手前就存在）
1. **相位計算全錯**：原本用 `correct_degree`（星座內度數 0–30）算相位，只可能判到合相/半六合且幾乎全誤判 → 改用完整黃道度數 `degree`（0–360）
2. **行星權重失效**：`PLANET_WEIGHTS` 鍵是英文（"Sun"）但 DB 存中文（「太陽」）→ 鍵改中文
3. **JWT 用戶永遠不會出現在配對名單**：候選過濾依賴 `last_login`，但 SimpleJWT 預設不更新 → 開 `UPDATE_LAST_LOGIN`
4. **聊天訊息全顯示在對方側**：REST 的 sender 是 email 字串、WS 是 `sender_id`，前端 parse 失敗 → 統一為 user id 整數
5. **前端 WebSocket 連兩次**（連線洩漏）→ 移除重複 connect
6. **驗證碼從未真正寄出**（只有 print）→ 改用 django send_mail
7. birth-info 重複 POST 撞 OneToOne 噴 500 → 回 400 提示用 PATCH
8. 候選名單不排除已滑過的人、不排除無星盤的人 → 補過濾
9. `db.sqlite3` 曾被 commit 到 public repo（含測試個資）→ 移出版控

### 新建的功能
- Flutter：註冊頁、個人資料頁（含照片上傳，Web 相容的 bytes 上傳）、出生資料頁、滑動配對頁（拖曳手勢+飛出動畫+配對成功彈窗直達聊天室）、星盤頁（CustomPaint：四元素配色星座環、行星依黃道度數定位、ASC 置左、四軸線、相近行星交錯、監聽 systemFonts 修 Web 字型懶載入方框問題）
- 後端：cities API、候選卡片 API 重整、聊天列表含最後訊息、部署設定
- 聊天列表友善時間（今天 HH:mm／昨天／M/d）、WebSocket 斷線指數退避重連

### 清理
- 刪除五個 app 的全部舊 template views/forms/templates（25 檔）與死碼（壞掉的 accounts/serializers.py、重複的 astrology/utils/chart.py、有 bug 的 coordinates.py、matplotlib chart_drawer）
- requirements 移除 matplotlib、加 dj-database-url + psycopg2-binary
- 修好 pytest（5 項全過：`cd astro_project && ../venv/bin/python -m pytest tests/`）

## 五、本機開發環境（這台 Mac 的特殊事項）

- **無 Docker**。後端：`cd astro_project && ../venv/bin/daphne -b 127.0.0.1 -p 8000 astro_project.asgi:application`（print 會 buffer，要看輸出加 `PYTHONUNBUFFERED=1`）
- Flutter SDK 3.44 在 `~/development/flutter`（已加入 .zshrc PATH）
- E2E 測試套路（重要，內建瀏覽器對 Flutter canvas 打字極不可靠）：
  1. `flutter build web`（**務必 release**，debug 模式在自動化瀏覽器會壞）
  2. build/web 複製到 scratchpad（preview 沙箱進不了 ~/Documents），用 `.claude/launch.json` 的 frontend 設定 + preview_start 服務
  3. **登入不要打字**：後端生成 JWT → JS 注入 localStorage（`flutter.token`/`flutter.refreshToken`/`flutter.expiryDate`/`flutter.userId`，值需 JSON.stringify）→ 重載即自動登入
  4. 點擊可用截圖座標；或啟用語意層（JS click `flt-semantics-placeholder`）後點 `role=button` 且有 `flt-tappable` 屬性的節點

## 六、測試帳號（密碼皆為對應表列值）

| 環境 | 帳號 | 密碼 | 備註 |
|---|---|---|---|
| 雲端 | cloud_a@test.com | cloudtest123 | 男，與 cloud_b 已配對，聊天室 room 1 |
| 雲端 | cloud_b@test.com | cloudtest123 | 女 |
| 本機 | e2e_owen@example.com | test123456 | 出生 2001/1/15 14:00 台北 |
| 本機 | seed_star/seed_moon/seed_sun@test.com | test123456 | 小星/小月/小辰，候選人 |

## 七、還沒做的事（依優先序）

1. **接寄信服務**（開放朋友測試前的唯一必要步驟）：Resend/Brevo 免費層，Render 設 EMAIL_* 環境變數即可，程式碼不用改
2. iPhone 實測回饋修 UX（使用者主力設備是 iPhone，走網頁版 + 加入主畫面）
3. 照片雲端儲存（Cloudinary 免費層）— 解決重新部署照片消失
4. 推播通知（Firebase FCM）— 原路線圖第四階段項目
5. **付費功能（產品核心變現，尚未設計）**：構想是「AI 詳細解盤」— 個人宮位/整體星盤解說 + 配對合盤解說。收費模式未定（月費制 vs 單點解鎖）。DB 已預留欄位：`MatchScore.ai_interpretation`（text）與 `is_ai_unlocked`（bool）
6. 已知技術債：geocoding 是寫死的 27 城市座標表（`users/utils.py`）、時區寫死 UTC+8（只適用台灣出生者）、`test_profile_api.py`/`test_match_api.py` 是空檔案、WS token 走 query string（上線加固時應改）、雲端 DATABASE_URL 曾在對話中傳遞過（必要時到 Neon reset password 並更新 Render 環境變數）

## 八、慣例

- Commit 訊息用繁體中文，結尾加 `Co-Authored-By: Claude <noreply@anthropic.com>`（作者 email 用 a74109876@gmail.com）
- 每段工作完成即 commit + push（push 即觸發自動部署，注意）
- 程式註解用繁體中文，與現有風格一致
