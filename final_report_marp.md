---
marp: true
theme: default
paginate: true
size: 16:9
title: posture_alarm 期末進度報告
description: Raspberry Pi 姿態跌倒警報系統目前進度報告
style: |
  section {
    font-family: "Microsoft JhengHei", "Noto Sans TC", sans-serif;
    letter-spacing: 0.02em;
  }
  h1 { color: #1f4e79; }
  h2 { color: #2f75b5; }
  table { font-size: 0.74em; }
  code { font-family: "Cascadia Code", "Consolas", monospace; }
---

<!-- _class: lead -->

# Raspberry Pi 姿態跌倒警報系統

## 期末進度報告

`posture_alarm`

姓名：＿＿＿＿＿＿　班級：＿＿＿＿＿＿  
指導老師：＿＿＿＿＿＿　日期：＿＿＿＿＿＿

---

# 本次報告重點


- 軟體系統目前完成度
- Raspberry Pi 硬體與外殼整合
- 已完成的警報、通知、資料紀錄功能
- 測試驗證狀態
- 後續還需要補強的項目

---

# 目前整體進度

| 項目 | 狀態 | 說明 |
|---|---|---|
| 影像姿態偵測 | 已完成 | 使用 MediaPipe Pose 取得人體關鍵點 |
| 跌倒判斷流程 | 已完成 | 規則式分類 + 多幀平滑 + 事件窗 |
| 狀態機 | 已完成 | NORMAL / SUSPECT_FALL / FALLEN / SEDENTARY / LYING_SAFE |
| 現場警報 | 已完成 | 蜂鳴器與 LED GPIO 控制 |
| 遠端通知 | 已完成 | LINE Messaging API + Discord webhook |
| 資料紀錄 | 已完成 | SQLite 事件紀錄與 CSV 報表 |
| 3D 列印外殼 | 已完成 | 已為 Raspberry Pi 製作保護與固定用外殼 |
| 實地長時間測試 | 待進行 | 需累積場域資料與調整閾值 |

---

# 目前系統流程

```text
Camera
  ↓
MediaPipe Pose
  ↓
PersonDetector + FallClassifier
  ↓
PostureStateMachine
  ↓
Buzzer / LED / LINE / Discord / SQLite / Overlay
```

目前程式主流程已完成串接，可以從攝影機畫面一路進到跌倒判定、警報輸出、通知推播與事件紀錄。

---

# 完整系統流程圖

```text
攝影機
  ↓
OpenCV / Raspberry Pi Camera 讀取影像
  ↓
MediaPipe Pose 偵測 33 個人體關鍵點
  ↓
關鍵點可信度檢查
  ↓
姿態特徵計算：軀幹角度 / 肩髖高差 / 髖部速度 / 床區 ROI
  ↓
跌倒分類：正常 / 疑似跌倒 / 安全躺臥
  ↓
狀態機：NORMAL / SUSPECT_FALL / FALLEN / SEDENTARY / LYING_SAFE
  ↓
輸出：蜂鳴器 / LED / LINE / Discord / SQLite / Overlay
```

---

# 已完成：軟體架構

| 模組 | 目前進度 |
|---|---|
| `main.py` | 主迴圈、訊號處理、模組整合已完成 |
| `config.py` | 相機、閾值、通知、路徑等環境設定已完成 |
| `vision/` | Camera、MediaPipe Pose、人體存在判定、跌倒分類已完成 |
| `core/` | 狀態機、LYING_SAFE 分流、時間格式、中文警報訊息已完成 |
| `alert/` | GPIO 蜂鳴器/LED、LINE、Discord 已完成 |
| `storage/` | SQLite 事件資料庫與 CSV 報表已完成 |
| `ui/` | OpenCV 狀態文字、關鍵點、警報與床區 ROI 顯示已完成 |

---

# 已完成：硬體整合

目前硬體端已完成 Raspberry Pi 基本警報整合。

| 硬體 | 狀態 | 說明 |
|---|---|---|
| Raspberry Pi | 已整合 | 作為主要運算與 GPIO 控制平台 |
| Camera | 已支援 | 支援 Raspberry Pi Camera / OpenCV 後端 |
| Buzzer | 已完成 | BCM GPIO 17，預設使用 PWM 模式 |
| LED | 已完成 | BCM GPIO 27，用於現場警示 |
| 3D 列印外殼 | 已完成 | 用於固定與保護 Raspberry Pi，提高展示完整度 |

---

# 3D 列印外殼成果

除了軟體功能外，本專題也為 Raspberry Pi 製作了 3D 列印外殼。

外殼用途：

- 保護 Raspberry Pi 主板
- 讓展示時的硬體更完整、整齊
- 協助固定裝置位置，降低線材拉扯風險
- 讓系統從「程式 Demo」更接近實際裝置原型

展示時可搭配 Raspberry Pi、Camera、LED、蜂鳴器一起呈現完整系統。

---

# 已完成：跌倒判定

目前跌倒判定不是只看單一姿勢，而是結合多個條件。

判定依據：

- 軀幹角度
- 肩膀與髖部高度差
- 髖部移動速度
- 髖部短時間下降量
- 多幀平滑分數
- 跌倒事件時間窗

目前已完成第一輪保守化調參，用來降低「慢慢躺下」或「床上抬頭」造成的誤報。

---

# 跌倒判斷公式化

目前跌倒判斷可整理成以下規則，方便說明與報告呈現：

```text
fall_posture = trunk_angle >= angle_threshold
            and hip_shoulder_diff <= hip_shoulder_diff_threshold

fall_event = hip_speed >= speed_threshold
          or hip_drop >= min_hip_drop

fall_score = 最近 N 幀中 fall_event 或 fall_posture 的比例

if fall_score >= score_threshold:
    fall_detected = True
```

床區補充規則：若人在 BED ROI 內、沒有明確跌倒事件，則分流為 `LYING_SAFE`，不直接觸發跌倒警報。

---

# 關鍵點可信度判斷

MediaPipe 每個 landmark 都有 `visibility`，目前系統會用它判斷人體偵測是否可靠。

重要關鍵點包含：鼻子、左右肩、左右髖、左右膝、左右腳踝。

```text
if 可見關鍵點數量 < MIN_VISIBLE_KEYPOINTS:
    判定為無有效人體

if 重要關鍵點平均 visibility < POSE_VISIBILITY_THRESHOLD:
    判定為無有效人體

else:
    進入姿態與跌倒分析
```

這可以降低遮擋、光線不足、鏡頭角度不佳造成的誤報。

---

# 已完成：狀態機

目前系統狀態分成五種：

| 狀態 | 說明 |
|---|---|
| `NORMAL` | 正常狀態 |
| `SUSPECT_FALL` | 疑似跌倒，等待確認 |
| `FALLEN` | 確認跌倒，啟動警報與通知 |
| `SEDENTARY` | 長時間無明顯動作 |
| `LYING_SAFE` | 床區內安全躺臥，與真正跌倒分流 |

這讓系統不是一偵測到姿勢變化就立刻警報，而是會經過時間條件確認，降低誤判機率。

---

# 已完成：BED ROI 誤報抑制

病床區域容易出現「正常躺臥但像跌倒」的情況，因此目前已加入床區 ROI。

已完成內容：

- 矩形床區 ROI
- 四點多邊形床區 ROI
- 互動式床區標記工具 `mark_bed_roi.py`
- 主程式啟動時可先標記床區
- OpenCV 畫面可顯示床區範圍

如果人在床區內躺臥，但沒有明確跌倒事件，系統會抑制跌倒警報。

---

# 已完成：警報與通知

當狀態進入 `FALLEN` 後，目前會觸發：

- 蜂鳴器警報
- LED 警示
- LINE 推播通知
- Discord webhook 通知
- SQLite 寫入 fall event
- OpenCV 畫面顯示 `FALL DETECTED`

另外已加入 `ALERT_COOLDOWN_SECONDS`，避免同一次跌倒事件一直重複推播。

---

# 已完成：資料紀錄

目前事件資料會寫入 SQLite。

已完成內容：

- 自動建立 `data/events.db`
- 自動建立 events table
- 記錄 state change 與 fall event
- payload 使用 JSON 字串保存
- `Reporter` 可輸出每日 CSV 報表
- 時間統一使用 `APP_TIMEZONE`，預設為 `Asia/Taipei`

這讓後續可以累積資料，分析誤報率與事件發生時間。

---

# 已完成：展示與部署工具

目前已經準備好展示與部署輔助工具。

| 檔案 | 用途 |
|---|---|
| `setup_demo.py` | 互動式產生展示設定 `demo.env` |
| `run_demo.sh` | 載入 `demo.env` 並啟動主程式 |
| `test_bz_led.py` | 單獨測試蜂鳴器與 LED |
| `test_notify.py` | 單獨測試 LINE / Discord 通知 |
| `posture_alarm.service` | systemd 無頭部署範本 |
| `TUNING_GUIDE.md` | 跌倒參數調整指南 |

---

# 測試狀態

目前已建立硬體無關的單元測試。

| 測試檔案 | 驗證內容 |
|---|---|
| `test_state_machine.py` | 狀態轉換與恢復條件 |
| `test_fall_classifier.py` | 跌倒判定、多幀平滑、誤判回歸 |
| `test_db.py` | SQLite 寫入、讀取與報表 |
| `test_notifiers.py` | LINE / Discord 通知與失敗回傳 |
| `test_utils.py` | 台灣時區與中文告警訊息 |
| `test_config.py` | 通知設定值載入 |

執行方式：

```bash
python -m pytest tests -q
```

---

# 實測結果表格

以下表格可在實際 Demo 或場域測試後填入數據。

| 測試情境 | 測試次數 | 成功偵測 | 誤報 | 備註 |
|---|---:|---:|---:|---|
| 正常站立 | 10 | 待填 | 待填 | 驗證 NORMAL |
| 正常坐下 | 10 | 待填 | 待填 | 驗證不誤報 |
| 躺在床上 | 10 | 待填 | 待填 | 驗證 BED ROI / LYING_SAFE |
| 模擬跌倒 | 10 | 待填 | 待填 | 驗證 FALLEN |
| 翻身 | 10 | 待填 | 待填 | 驗證不誤判跌倒 |
| 彎腰撿東西 | 10 | 待填 | 待填 | 驗證瞬間動作不誤報 |
| 短暫遮擋 | 10 | 待填 | 待填 | 驗證 visibility 判斷 |
| 長時間不動 | 10 | 待填 | 待填 | 驗證 SEDENTARY |

---

# 目前可以展示的功能

目前展示時可以呈現：

1. Raspberry Pi 與 3D 列印外殼成品
2. 攝影機即時畫面
3. MediaPipe 人體關鍵點偵測
4. 畫面上的姿態狀態顯示
5. 床區 ROI 標記與顯示
6. 模擬跌倒後的蜂鳴器、LED、LINE、Discord 通知
7. SQLite 事件紀錄
8. pytest 測試結果

---

# Demo 截圖預留頁

建議匯出 PPT 後，把以下畫面截圖補到此頁或拆成多頁：

| 截圖位置 | 要證明的內容 |
|---|---|
| MediaPipe 骨架畫面 | 已成功偵測人體關鍵點 |
| NORMAL / LYING_SAFE 畫面 | 正常與安全躺臥狀態可區分 |
| FALLEN 警報畫面 | 跌倒時畫面顯示警告 |
| LINE / Discord 通知 | 遠端通知已送出 |
| SQLite / CSV 紀錄 | 系統有留下事件資料 |
| 蜂鳴器、LED、3D 外殼照片 | 硬體警報與實體裝置已完成 |

---

# 目前還沒完成 / 待驗證

目前主要不是功能缺少，而是需要實地資料驗證。

待完成項目：

- 在實際場域累積長時間測試資料
- 校正不同鏡頭角度下的跌倒閾值
- 驗證誤報率是否能達到目標
- 測試正式 LINE token / Discord webhook 長時間穩定度
- 確認 Raspberry Pi、Camera、GPIO、3D 列印外殼整體安裝穩定性
- 補充端到端整合測試

---

# 下一步規劃


1. 依現場鏡頭角度標記 BED ROI
2. 累積 8 小時以上測試資料
3. 依誤報與漏報調整 `FALL_EVENT_*`、`BED_ROI_*`
4. 補強通知失敗重試與長時間運行測試

---

# 結論

目前專案已完成第一版可展示系統：包含姿態偵測、跌倒判定、狀態機、`LYING_SAFE` 安全躺臥分流、蜂鳴器與 LED、LINE / Discord 通知、SQLite 紀錄、BED ROI 抑制、單元測試、部署工具，以及 Raspberry Pi 的 3D 列印外殼。

後續重點是把系統放到實際場域中長時間測試，依照資料調整閾值與狀態設計，讓系統更穩定、更接近可實際使用的照護輔助裝置。

---

<!-- _class: lead -->

# Q & A

謝謝聆聽
