# 企業內部知識庫 RAG 系統

![Python](https://img.shields.io/badge/Python-3.11-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg?logo=postgresql&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Lint Check](https://github.com/108618026/Enterprise-Knowledge-Agent-backend/actions/workflows/lint.yml/badge.svg)

基於 FastAPI + pgvector + Gemini 建構的企業內部知識庫文件問答系統，
支援 PDF 上傳、語意向量檢索與 AI 生成回答。

## 目錄
- [主要功能與Demo](#主要功能與-demo)
- [技術架構](#技術架構)
- [效能壓測報告](#效能壓測報告)
- [技術挑戰與解決方案](#技術挑戰與解決方案)
- [快速啟動](#快速啟動)
  - [先決條件與API Key準備](#先決條件與api-key準備)
  - [本地部署](#本地部署)
  - [API 文件](#api-文件)
- [專案結構](#專案結構)



## 主要功能與 Demo

- PDF 上傳與非同步 embedding 處理（BackgroundTasks）
- 語意向量搜尋（pgvector cosine distance）
- RAG 問答（Gemini API）
- JWT 身份驗證
- 結構化 Log（loguru + ContextVar，搭配 async dependency 確保 context 正確傳遞，每筆 log 自動帶入 request_id / client_ip / user_account）
- IP 限流（SlowAPI，防止惡意請求） 

觀看 Enterprise-Knowledge-Agent 如何即時處理文件並回覆提問。 
*(註：目前的展示與預設系統提示詞是針對繁體中文。不過，核心的 RAG 流程與語言無關，只需調整提示詞模板，就能應用英文文件。)*

下方的展示涵蓋了完整流程：登入 → 上傳人事規章 PDF 範例 → 針對該文件提問 → 取得具備事實根據與引用來源的回答。

[![API Demo](https://img.youtube.com/vi/1GMBpakRmII/maxresdefault.jpg)](https://www.youtube.com/watch?v=1GMBpakRmII)

### 流程亮點：
1. **身分驗證：** 安全的使用者登入與驗證。
2. **文件上傳：** 上傳 PDF 進行系統匯入與向量化處理。
3. **提問查詢：** 基於文件上下文，使用自然語言進行提問。
4. **生成回覆：** 系統檢索相關資料並生成準確的回答。

---


## 技術架構

```text
Client
   │
   ▼
┌─────────────────────────────┐
│          FastAPI            │
├─────────────────────────────┤
│ Middleware                  │
│ • CORS                      │
│ • UUID Logging              │
│ • Client IP Logging         │
├─────────────────────────────┤
│ Security                    │
│ • JWT Authentication        │
│ • SlowAPI Rate Limiting     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         Router Layer        │
├─────────────────────────────┤
│ Account APIs                │
│ Document APIs               │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│        Service Layer        │
├─────────────────────────────┤
│ Document Workflow           │
│ RAG Workflow                │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      Repository Layer       │
├─────────────────────────────┤
│ SQLAlchemy ORM              │
│ PostgreSQL CRUD             │
│ pgvector Query              │
└───────┬─────────┬───────────┘
        │         │
        ▼         ▼

 PostgreSQL   pgvector
      │         │
      └────┬────┘
           ▼

      Gemini API
   • Embedding
   • Answer Generation
```


## 效能壓測報告

### 🧪 測試情境與環境設定

為了排除外部依賴服務的網路波動影響，本次測試以 Mock Client 模擬 LLM 服務，並比較同步（Sync）與非同步（Async）實作在高併發情境下的系統承載能力差異。測試期間維持相同硬體資源與資料庫配置，確保結果具備可比較性。

* **運算環境：** Cloud Run (1 vCPU / 512Mi / Concurrency 80)
  * 地區：`asia-southeast1`（新加坡）
* **資料庫：** Neon PostgreSQL (1 Compute Unit ~ 4 GB RAM)
  * 地區：`AWS ap-southeast-1`（新加坡）
* **模擬延遲（Mock Gemini API）：**
  * Embedding：0.5 秒
  * LLM Inference：3.0 秒
* **預熱機制（Warm-up）：**
  * 測試前先發送預熱請求（Warm-up Request），確保 Cloud Run 容器實例已完全啟動，排除 Cold Start 對測試結果的影響。

---

### 📈 測試結果比較表

| 併發用戶數 | 版本 | p50 (ms) | p95 (ms) | RPS | 失敗率 |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **20** | Sync | 3,600 | 3,900 | 3.20 | 0% |
| **20** | Async | 3,600 | 4,000 | 3.22 | 0% |
| **60** | Sync | 13,000 | 16,000 | 3.85 | 0% |
| **60** | Async | 9,800 | 11,000 | 4.75 | 0% |
| **120** | Sync | 32,000 | 44,000 | 1.49 | **28%** |
| **120** | Async | 20,000 | 23,000 | **4.80** | **0%** |

---

### 💡 架構結論

#### 基準驗證（20 Users）

在低併發情境下，Sync 與 Async 版本的 p50、p95 與 RPS 幾乎一致，顯示測試環境穩定且公平，無額外變因影響結果。

#### 高併發瓶頸分析（120 Users）

* ❌ **Sync 版本**
  * 每個請求在等待外部 I/O 完成前會持續佔用 Worker 資源。
  * 隨著併發量增加，同步阻塞導致可用 Worker 資源逐漸耗盡。
  * 在 120 Users 情境下，請求失敗率達 **28%**。
  * p95 延遲最高達 **44 秒**，系統已出現明顯飽和現象。

* ✅ **Async 版本**
  * 等待 I/O 期間可將控制權交還給 Event Loop，讓系統繼續處理其他請求。
  * 在相同的 Cloud Run（1 vCPU / 512Mi）配置下，仍維持 **0% 失敗率**。
  * 吞吐量（RPS）達到 **4.80**，約為 Sync 版本的 **3.2 倍**。
  * p95 延遲控制在 **23 秒以內**，展現較佳的高併發承載能力與資源利用效率。

---

### 🔍 為什麼非同步架構表現比較好呢?

同步架構（Sync）在等待外部服務回應期間，Worker Thread 仍會持續被佔用：

```text
Request
   ↓
Worker Thread
   ↓
等待外部 API（3.5 秒）
   ↓
Thread 持續被佔用
```

當大量請求同時進入時，可用 Worker 數量會逐漸被耗盡，導致排隊時間增加、延遲上升，甚至產生請求失敗。

非同步架構（Async）則會在等待 I/O 時將控制權交還給 Event Loop：

```text
Request
   ↓
Coroutine
   ↓
等待外部 API（3.5 秒）
   ↓
控制權返回 Event Loop
   ↓
處理其他請求
```

因此在相同硬體資源下，Async 能夠同時維持更多請求，提升整體吞吐量與系統穩定性，特別適合 RAG、AI API、資料庫查詢等 I/O 密集型應用場景。

## 技術挑戰與解決方案

開發過程中處理過的關鍵問題：
- **ContextVar 跨 async/sync context 遺失**：FastAPI 同步 route handler 會被丟進
  threadpool 執行，導致 dependency 裡 set 的 ContextVar 在 service layer 讀不到，
  改為 async dependency 確保值寫入正確的 context


## 快速啟動

### 先決條件與API Key準備
在開始之前，請確保您的開發環境已安裝 [Git](https://git-scm.com/) 與 [Docker](https://www.docker.com/)。


本專案使用 Google Gemini 作為 LLM 及 Embedding 模型。啟動前請先備妥 API Key：
1. 前往 [Google AI Studio](https://aistudio.google.com/app/apikey) 建立免費的 API Key。
2. 如果您不熟悉申請流程，可以參考這篇[詳細圖文教學](https://kuwaai.org/zh-Hant/blog/apply-gemini)。
3. 取得金鑰後，稍後將其填入專案的 `.env` 檔案中。



### 本地部署

```bash
git clone https://github.com/jasonyeh-dev/enterprise-knowledge-agent-backend.git
cd enterprise-knowledge-agent-backend
cp .env.example .env    # 填入 Gemini API Key 等設定
docker compose up -d    # 自動啟動 DB、執行 migration、載入預設資料、啟動後端服務
```

預設管理者帳號／密碼：`demo1234` / `demo1234`

### API 文件

服務啟動完成後，請打開瀏覽器前往以下網址查看並測試 API：
👉 http://localhost:8080/docs



## 專案結構

```text
app/
├── main.py             # 應用程式進入點：初始化 FastAPI 實例、掛載全域 Lifespan、SlowAPI限流
├── core/               # 核心基礎：全域環境變數、JWT 簽發、Logger 配置、上下文管理、資料庫引擎
├── api/                # 路由層：定義端點、解析 Request / Response 格式、簽章與效期驗證
├── services/           # 商業邏輯層：核心業務管線，RAG 檢索、文件流程與背景任務
├── crud/               # 資料存取層：封裝SQL語法、執行資料庫交易
└── models/             # 資料模型定義
    ├── models.py       # SQLAlchemy ORM 模型：對應 PostgreSQL 實體資料表、定義欄位、關聯屬性與向量欄位
    └── schemas.py      # Pydantic 驗證結構：定義 API 交互的數據契約
```
