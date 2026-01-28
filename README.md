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
Create `.env` in the root directory:
```env
GEMINI_API_KEY=your_key_here
```

### 2. Run with Docker (Recommended)
```bash
docker compose up --build
```
- **Web**: `http://localhost:80` (or just `http://localhost`)
- **API Docs**: `http://localhost:8090/docs`
- **Internal Port**: The backend runs on **8080** inside the container, but is mapped to **8090** on your machine.

### 3. Local Setup (Manual)
**Backend**:
Run from the **root** folder:
```bash
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8080
```
- API Docs: `http://localhost:8080/docs`

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
