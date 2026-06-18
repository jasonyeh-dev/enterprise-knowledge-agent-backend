# Enterprise Knowledge Base RAG System

*[Read this in Traditional Chinese (繁體中文版本請點此)](README.zh-TW.md)*

![Python](https://img.shields.io/badge/Python-3.11-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg?logo=postgresql&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Lint Check](https://github.com/108618026/Enterprise-Knowledge-Agent-backend/actions/workflows/lint.yml/badge.svg)

A document Q&A system designed for enterprise internal knowledge bases built with FastAPI, pgvector, and Gemini. It supports PDF uploads, semantic vector retrieval, and AI-generated responses.


## System Architecture

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

## Project Structure

```text
app/
├── main.py             # Application entry point: FastAPI instance initialization, global Lifespan, and SlowAPI rate limiting.
├── core/               # Core foundations: Environment variables, JWT issuance, Logger configuration, context management, and database engine.
├── api/                # Routing layer: Defines endpoints, parses Request/Response formats, validates signatures and token expiration.
├── services/           # Business logic layer: Core pipelines, RAG retrieval, document workflows, and background tasks.
├── crud/               # Data access layer: Encapsulates SQL queries and executes database transactions.
└── models/             # Data models definition.
    ├── models.py       # SQLAlchemy ORM models: Maps to PostgreSQL tables, defines columns, relationships, and vector fields.
    └── schemas.py      # Pydantic validation schemas: Defines data contracts for API interactions.
```

## Key Features

- PDF upload and asynchronous embedding processing (BackgroundTasks).
- Semantic vector search (pgvector cosine distance).
- RAG Q&A generation (Gemini API).
- JWT Authentication.
- Structured Logging (loguru + ContextVar): automatically injects request_id, 
  client_ip, and user_account into every log entry, with correct context propagation 
  across async dependencies.
- IP Rate Limiting (SlowAPI to prevent malicious requests).

## 🎥 Demonstration

Watch how the Enterprise-Knowledge-Agent processes documents and answers queries in real-time. 
*(Note: The current demonstration and default system prompts are optimized for Traditional Chinese. However, the core RAG pipeline is language-agnostic and can be easily adapted for English documents by adjusting the prompt templates.)*

The demo below covers the full pipeline: login → upload a sample HR policy PDF → 
ask a question only answerable from that document → receive a grounded response with citations.

<p align="center">
  <video src="https://github.com/user-attachments/assets/ed10e144-55b6-4f62-8cc9-12670118dff8" width="85%" autoplay loop muted playsinline></video>
</p>

### Workflow Highlight:
1. **Authentication:** Secure user login and validation.
2. **Document Upload:** Uploading a PDF for system ingestion and vectorization.
3. **Querying:** Asking natural language questions based on the document context.
4. **Response Generation:** The agent retrieves relevant data and generates an accurate response.

---

## 🛠️ Prerequisites
Before you begin, ensure you have the following installed on your development environment:
* [Git](https://git-scm.com/)
* [Docker](https://www.docker.com/)

## 🔑 Gemini API Key Setup

This project uses Google Gemini for both the LLM and Embedding models. Please prepare your API Key before starting:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) to create a free API Key.
2. If you are unfamiliar with the application process, you can refer to this [step-by-step guide](https://sfailabs.com/guides/how-to-get-google-gemini-api-key).
3. Once you have obtained the key, add it to the `.env` file in the following setup step.


## 🚀 Quick Start (Local)

```bash
git clone https://github.com/jasonyeh-dev/enterprise-knowledge-agent-backend.git
cd enterprise-knowledge-agent-backend
cp .env.example .env    # Fill in your Gemini API Key
docker compose up -d    # Auto-starts the DB, runs migrations, import default data, and boots the backend service
```

Default Admin Account / Password: `demo1234` / `demo1234`

## 📖 API Documentation

Once the service is running successfully, open your browser and visit the following URL to view and test the API:
👉 http://localhost:8080/docs



## 🧩 Technical Challenges

A key issue resolved during the development process:
- **ContextVar loss across async/sync contexts**: FastAPI synchronous route handlers are executed in a threadpool. This causes ContextVar values set in dependencies to become inaccessible in the service layer. The solution was to refactor them into async dependencies, ensuring the values are written to the correct context and successfully passed down the execution stack.
