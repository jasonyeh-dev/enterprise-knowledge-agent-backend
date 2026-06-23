# Enterprise Knowledge Base RAG System

*[Read this in Traditional Chinese (繁體中文版本請點此)](README.zh-TW.md)*

![Python](https://img.shields.io/badge/Python-3.11-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00.svg?logo=sqlalchemy&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791.svg?logo=postgresql&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Lint Check](https://github.com/108618026/Enterprise-Knowledge-Agent-backend/actions/workflows/lint.yml/badge.svg)

A document Q&A system designed for enterprise internal knowledge bases built with FastAPI, pgvector, and Gemini. It supports PDF uploads, semantic vector retrieval, and AI-generated responses.

## Table of Contents
- [Key Features and Demo](#key-features-and-demo)
- [Architecture](#architecture)
- [Performance Benchmark Report](#performance-benchmark-report)
- [Technical Challenges and Solutions](#technical-challenges-and-solutions)
- [Getting Started](#getting-started)
  - [Prerequisites and API Key Preparation](#prerequisites-and-api-key-preparation)
  - [Local Deployment](#local-deployment)
  - [API Documentation](#api-documentation)
- [Project Structure](#project-structure)


## Key Features and Demo

- **Asynchronous Processing:** PDF upload and asynchronous embedding processing (`BackgroundTasks`).
- **Semantic Vector Search:** Accurate retrieval using `pgvector` cosine distance.
- **RAG-based Q&A:** Generative answers powered by the Gemini API.
- **Security:** JWT authentication and IP rate limiting (using `SlowAPI` to prevent malicious requests).
- **Structured Logging (Observability):** Integrated with `loguru` + `ContextVar`. Utilizes async dependencies to ensure context is correctly passed, automatically injecting `request_id`, `client_ip`, and `user_account` into every log entry.

Watch how the Enterprise-Knowledge-Agent processes documents and answers questions in real-time. 
*(Note: The current demo and default system prompts are designed for Traditional Chinese. However, the core RAG workflow is language-agnostic. By simply adjusting the prompt templates, it can be seamlessly applied to English documents.)*

The demonstration below covers the complete workflow: Login → Upload a sample HR policy PDF → Ask a question based on the document → Receive answer with citation sources.

[![API Demo](https://img.youtube.com/vi/1GMBpakRmII/maxresdefault.jpg)](https://www.youtube.com/watch?v=1GMBpakRmII)

### Workflow Highlights:
1. **Authentication:** Secure user login and validation.
2. **Document Upload:** Upload PDFs for system parsing and vectorization.
3. **Natural Language Querying:** Ask questions based on the ingested document context.
4. **Answer Generation:** The system retrieves relevant chunks and generates accurate, context-aware responses.

## Architecture

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




### Workflow Highlight:
1. **Authentication:** Secure user login and validation.
2. **Document Upload:** Uploading a PDF for system ingestion and vectorization.
3. **Querying:** Asking natural language questions based on the document context.
4. **Response Generation:** The agent retrieves relevant data and generates an accurate response.

---


## Performance Benchmark Report

### 🧪 Test Scenarios & Environment Configuration

To eliminate external network volatility and isolate the performance differences in **I/O handling mechanisms (Sync vs. Async)**, this benchmark replaces the live LLM services with a Mock Client while strictly controlling hardware resources.

* **Application Hosting:** Cloud Run (1 vCPU / 512Mi / Concurrency 80)
  * Region: `asia-southeast1` (Singapore)
* **Database:** Neon PostgreSQL (1 Compute Unit ~ 4 GB RAM)
  * Region: `AWS ap-southeast-1` (Singapore)
* **Simulated Dependency Latency (Mock Gemini API):**
  * Embedding: 0.5s
  * LLM Inference: 3.0s
* **Warm-up Strategy:**
  * Prior to benchmarking, warm-up requests were dispatched to ensure Cloud Run instances were fully initialized and active, effectively eliminating Serverless cold start latency from the dataset.

### 📈 Benchmark Results

| Concurrent Users | Version | p50 (ms) | p95 (ms) | RPS | Failure Rate |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **20** | Sync | 3,600 | 3,900 | 3.20 | 0% |
| **20** | Async | 3,600 | 4,000 | 3.22 | 0% |
| **60** | Sync | 13,000 | 16,000 | 3.85 | 0% |
| **60** | Async | 9,800 | 11,000 | 4.75 | 0% |
| **120** | Sync | 32,000 | 44,000 | 1.49 | **28%** |
| **120** | Async | 20,000 | 23,000 | **4.80** | **0%** |

### 💡 Architectural Insights (Key Takeaways)

#### Baseline Validation (20 Users)
At low concurrency, the Sync and Async versions exhibit nearly identical p50, p95, and RPS, validating the environmental consistency and confirming the absence of external variables skewing the baseline.

#### High-Concurrency Bottleneck Analysis (120 Users)
* ❌ **Sync Version**
  * Threads remain blocked while waiting for external I/O operations to complete.
  * As concurrency scales, synchronous blocking rapidly exhausts available Worker resources.
  * At 120 users, the request failure rate reached **28%**.
  * The p95 latency spiked to **44 seconds**, indicating severe system saturation and resource starvation.

* ✅ **Async Version**
  * Leverages a non-blocking architecture, yielding control back to the Event Loop during I/O wait times to process other incoming requests.
  * Under identical hardware constraints (1 vCPU / 512Mi), it successfully maintained a **0% failure rate**.
  * Throughput (RPS) hit **4.80**, approximately **3.2x higher** than the Sync version.
  * The p95 latency was kept **under 23 seconds**, demonstrating superior horizontal scaling resilience and resource utilization efficiency.

### 🔍 Why Does the Async Architecture Perform Better?

In a synchronous (Sync) architecture, the Worker Thread remains occupied while waiting for a response from an external API:

```text
Request
   ↓
Worker Thread
   ↓
Wait for External API (3.5 seconds)
   ↓
Thread remains occupied
```

When a large number of requests come in simultaneously, the available Worker threads are gradually exhausted, leading to increased queue times, higher latency, and even request failures.

In contrast, an asynchronous (Async) architecture yields control back to the Event Loop while waiting for I/O operations:

```text
Request
   ↓
Coroutine
   ↓
Wait for External API (3.5 seconds)
   ↓
Control returns to Event Loop
   ↓
Process other requests
```

Therefore, under the same hardware resources, Async can handle more concurrent requests, improving overall throughput and system stability. It is particularly suitable for I/O bound application scenarios such as RAG, AI APIs, and database queries.


## Technical Challenges and Solutions

A key issue resolved during the development process:
- **ContextVar loss across async/sync contexts**: FastAPI synchronous route handlers are executed in a threadpool. This causes ContextVar values set in dependencies to become inaccessible in the service layer. The solution was to refactor them into async dependencies, ensuring the values are written to the correct context and successfully passed down the execution stack.

## Getting Started

### Prerequisites and API Key Preparation

Before getting started, please ensure that [Git](https://git-scm.com/) and [Docker](https://www.docker.com/) are installed in your development environment.

This project uses Google Gemini for both the LLM and Embedding models. Please prepare your API Key before starting:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) to create a free API Key.
2. If you are unfamiliar with the application process, you can refer to this [step-by-step guide](https://sfailabs.com/guides/how-to-get-google-gemini-api-key).
3. Once you have obtained the key, add it to the `.env` file in the following setup step.


### Local Deployment

```bash
git clone https://github.com/jasonyeh-dev/enterprise-knowledge-agent-backend.git
cd enterprise-knowledge-agent-backend
cp .env.example .env    # Fill in your Gemini API Key
docker compose up -d    # Auto-start the DB, run migrations, import default data, and boot the backend service
```

Default Administrator Account / Password: `demo1234` / `demo1234`

### API Documentation

Once the service is running successfully, open your browser and visit the following URL to view and test the API:
👉 http://localhost:8080/docs





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


