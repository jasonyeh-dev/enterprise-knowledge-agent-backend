# 企業內部知識庫 RAG 系統

![Python](https://img.shields.io/badge/Python-3.11-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg?logo=postgresql&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Lint Check](https://github.com/108618026/Enterprise-Knowledge-Agent-backend/actions/workflows/lint.yml/badge.svg)

基於 FastAPI + pgvector + Gemini 建構的企業內部文件問答系統，
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
- 結構化 Log（loguru + ContextVar，每筆 log 自動帶入 request_id / user）
- IP 限流（SlowAPI，防止惡意請求） 