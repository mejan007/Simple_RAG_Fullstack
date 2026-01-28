# Simple RAG Fullstack

A simple, Dockerized RAG application using FastAPI, React, and Google Gemini.

## Project Structure
```text
.
├── backend/             # FastAPI + LangChain
│   ├── models/          # Schemas
│   ├── routers/         # API Routes
│   ├── services/        # Logic
├── frontend/            # React + Vite
└── docker-compose.yml   # Orchestration
```

## Setup

### 1. Environment
Create `.env` in root:
```env
GEMINI_API_KEY=your_key_here
```

### 2. Run with Docker (Recommended)
```bash
docker compose up --build
```
- Web: `http://localhost`
- API: `http://localhost:8090/docs`

### 3. Local Setup (Manual)
**Backend**:
```bash
cd backend
uv sync
uv run uvicorn main:app --port 8080
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## Features
- Hybrid PDF/Text Upload
- Real-time Streaming (WebSockets)
- Flashrank Reranking
- ChromaDB Persistence (`./chroma_data`)

## License
MIT
