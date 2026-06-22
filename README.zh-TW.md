# 企業內部知識庫 RAG 系統

![Python](https://img.shields.io/badge/Python-3.11-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg?logo=postgresql&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Lint Check](https://github.com/108618026/Enterprise-Knowledge-Agent-backend/actions/workflows/lint.yml/badge.svg)

基於 FastAPI + pgvector + Gemini 建構的企業內部知識庫文件問答系統，
支援 PDF 上傳、語意向量檢索與 AI 生成回答。

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


## 主要功能

- PDF 上傳與非同步 embedding 處理（BackgroundTasks）
- 語意向量搜尋（pgvector cosine distance）
- RAG 問答（Gemini API）
- JWT 身份驗證
- 結構化 Log（loguru + ContextVar，搭配 async dependency 確保 context 正確傳遞，每筆 log 自動帶入 request_id / client_ip / user_account）
- IP 限流（SlowAPI，防止惡意請求） 

## 🎥 範例影片

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

## 🛠️ 先決條件
在開始之前，請確保您的開發環境已安裝以下工具：
* [Git](https://git-scm.com/)
* [Docker](https://www.docker.com/)

## 🔑 準備 Gemini API Key

本專案使用 Google Gemini 作為 LLM 及 Embedding 模型。啟動前請先備妥 API Key：

1. 前往 [Google AI Studio](https://aistudio.google.com/app/apikey) 建立免費的 API Key。
2. 如果您不熟悉申請流程，可以參考這篇[詳細圖文教學](https://kuwaai.org/zh-Hant/blog/apply-gemini)。
3. 取得金鑰後，稍後將其填入專案的 `.env` 檔案中。

## 🚀 本地快速啟動

```bash
git clone https://github.com/jasonyeh-dev/enterprise-knowledge-agent-backend.git
cd enterprise-knowledge-agent-backend
cp .env.example .env    # 填入 Gemini API Key 等設定
docker compose up -d    # 自動啟動 DB、執行 migration、載入預設資料、啟動後端服務
```

預設管理者帳號／密碼：`demo1234` / `demo1234`



## 📖 API 文件

服務啟動完成後，請打開瀏覽器前往以下網址查看並測試 API：
👉 http://localhost:8080/docs


## 🧩 技術挑戰

開發過程中處理過的幾個關鍵問題：
- **ContextVar 跨 async/sync context 遺失**：FastAPI 同步 route handler 會被丟進
  threadpool 執行，導致 dependency 裡 set 的 ContextVar 在 service layer 讀不到，
  改為 async dependency 確保值寫入正確的 context
