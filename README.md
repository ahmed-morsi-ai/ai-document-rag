# AI Document RAG

AI Document RAG is a full-stack document question-answering application that lets authenticated users upload documents, process and index their content for semantic retrieval, and chat against the available document context.

The project combines a FastAPI backend, PostgreSQL persistence, persistent vector storage, provider-independent RAG services, local LLM integration through Ollama, and a React/TypeScript frontend.

## Current Verified Feature Set


The current verified product includes:

**Backend:** authentication, document lifecycle, parsing, chunking, embeddings, owner-aware indexing, owner-scoped retrieval, RAG orchestration, Ollama integration, chat persistence, conversations, evaluation, reliability hardening, and security/tenant-isolation verification.

**Frontend:** authenticated application shell, dashboard, upload, document search and pagination, document deletion, conversation search and pagination, chat, source/citation display, themes, responsive behavior, and accessibility-oriented UI behavior.


The currently implemented and verified product includes:

- User registration and login with JWT authentication.
- Protected frontend routes and authenticated backend access.
- Ownership-aware access to user-owned documents and conversations.
- Upload and processing of PDF, DOCX, and TXT documents.
- Document validation and persistent document metadata.
- Document text extraction and deterministic chunking.
- Embedding generation through a provider abstraction and Sentence Transformers.
- Persistent vector storage with document-scoped deletion.
- Semantic retrieval with configurable top-k results.
- Provider-independent RAG context construction.
- Backend Chat/RAG responses expose deterministic, provider-independent source evidence derived from retrieval results.
- LLM answer generation through the LLM provider abstraction with an Ollama implementation.
- PostgreSQL-backed conversation and message persistence.
- Ordered conversation history.
- Deterministic titles for newly created conversations.
- Ownership-aware conversation deletion with associated message cleanup.
- Ownership-aware document deletion with file and vector cleanup.
- Frontend chat, conversation history, message sending, retry behavior, and deletion flows.
- Chat-side document availability visibility.
- A shared authenticated application shell with Chat/Documents navigation, New Chat, active states, logout, and responsive navigation.
- User-selectable Light and Dark themes with persisted preference.
- A redesigned Chat Workspace with a conversation sidebar, document-context area, conversation header, message presentation, and responsive composer.
- A polished Dashboard/Documents workspace with responsive document cards, upload presentation, explicit document states, deletion confirmation, and a clear Document-to-Chat path.
- Automated frontend and backend regression tests.

## High-Level Architecture

```text
React / TypeScript Frontend
            │
            │ HTTP
            ▼
      FastAPI Backend
            │
      ┌─────┼───────────────┐
      │     │               │
      ▼     ▼               ▼
 PostgreSQL  Document     RAG Services
             Processing        │
             + Storage         │
                                ▼
                         Retrieval Layer
                                │
                                ▼
                         Context Assembly
                                │
                                ▼
                         LLM Provider
                                │
                                ▼
                             Ollama
```

The frontend handles authentication state, protected navigation, document management, conversations, chat interaction, and presentation.

The backend owns persistence, document processing, retrieval, RAG orchestration, authentication, and LLM integration.

## Frontend

The frontend uses:

- React 19
- TypeScript
- Vite
- React Router
- Vitest
- Testing Library
- OXLint

The authenticated frontend is organized around a shared application shell. The shell provides the common navigation layer while the Dashboard and Chat pages render inside it.

Current frontend scripts:

```bash
npm run dev
npm run typecheck
npm test
npm run build
npm run lint
npm run preview
```

## Backend

The backend uses:

- Python
- FastAPI
- Async SQLAlchemy
- PostgreSQL
- Alembic
- JWT authentication
- Pydantic/FastAPI schemas

Backend responsibilities include:

- Authentication and current-user access control.
- Document validation and persistence.
- Document parsing and indexing orchestration.
- Conversation and message persistence.
- Ownership validation.
- Semantic retrieval.
- RAG context construction.
- LLM provider integration.
- Safe document and conversation deletion.

## RAG Pipeline

Document indexing follows this general flow:

```text
Document Upload
      │
      ▼
Validation
      │
      ▼
Text Extraction
      │
      ▼
Deterministic Chunking
      │
      ▼
Embedding Provider
      │
      ▼
Persistent Vector Store
```

Query processing follows:

```text
User Query
    │
    ▼
Retriever
    │
    ▼
Retrieved Results
    │
    ▼
Deterministic RAG Context
    │
    ▼
LLM Provider
    │
    ▼
Generated Answer
```

The current implementation uses deterministic 1,000-character chunks with 100-character overlap and the `all-MiniLM-L6-v2` embedding model.

The application-facing retrieval and generation boundaries remain provider-independent. The backend Chat/RAG response contract exposes source evidence derived directly from retrieved results using `text`, `document_id`, `chunk_index`, `distance`, and `metadata`. Source order follows retrieval order, and empty retrieval produces an empty `sources` collection.

The frontend Chat workspace displays retrieved RAG source evidence using only the verified backend source fields.

## Retrieval Evaluation

The repository includes a deterministic, chunk-level retrieval evaluation.

Evaluation set: `retrieval-v1`
Cases: 6
Controlled corpus: `backend/evaluation/corpus/`
Embedding model: `all-MiniLM-L6-v2`
Vector store: isolated temporary Chroma
Retriever: existing project `Retriever`

| Metric | @1 | @3 | @5 |
| --- | ---: | ---: | ---: |
| Recall | 0.75 | 0.8333333333333334 | 0.8333333333333334 |
| Precision | 0.8333333333333334 | 0.3333333333333333 | 0.20000000000000004 |
| Hit Rate | 0.8333333333333334 | 0.8333333333333334 | 0.8333333333333334 |

The evaluation is performed at chunk level using the stable `<document_id>:<chunk_index>` key. The controlled corpus is indexed through the existing parser, chunking, `DocumentIndexer`, embedding provider, Chroma implementation, and `Retriever`.

To reproduce the real retrieval evaluation:

```bash
cd ~/Projects/ai-document-rag
source backend/.venv/bin/activate
set -a && source .env && set +a

PYTHONPATH=backend python -m app.evaluation.runner --dataset backend/evaluation/retrieval_v1.json --k 1
PYTHONPATH=backend python -m app.evaluation.runner --dataset backend/evaluation/retrieval_v1.json --k 3
PYTHONPATH=backend python -m app.evaluation.runner --dataset backend/evaluation/retrieval_v1.json --k 5
```

The measurements are retrieval-quality measurements for this controlled repository-owned corpus only. They are not production accuracy or a universal benchmark. They do not measure answer correctness, factuality, hallucination rate, groundedness, or LLM answer quality.

## Grounding Evaluation

The repository includes a deterministic, provider-independent grounding evaluation to verify whether expected answer evidence is supported by supplied context passages.

Evaluation set: `backend/evaluation/grounding_v1.json`
Cases: 5
Evidence coverage: 0.70 (macro-average across cases; 4 of 6 expected evidence phrases matched)

To reproduce the grounding evaluation:

```bash
cd ~/Projects/ai-document-rag
source backend/.venv/bin/activate
set -a && source .env && set +a

PYTHONPATH=backend python -m app.evaluation.runner --mode grounding --dataset backend/evaluation/grounding_v1.json
```

The grounding evaluator normalizes whitespace, applies case-folding, and deterministically checks substring presence of expected evidence phrases against supplied source texts. It operates without external models, LLM judges, vector stores, or network calls. It measures deterministic evidence coverage for the controlled dataset and does not claim unconstrained semantic factuality or hallucination detection.

## Vector Ownership & Retrieval Isolation

Authenticated retrieval is owner-scoped end to end. Indexed chunks carry the owning document/user identity, retrieval receives the authenticated owner identity, and the Chroma query applies the owner constraint at the vector-store boundary. There is no unrestricted authenticated retrieval fallback.

Ownerless vectors from older local vector-store data are not eligible for authenticated retrieval. The repository does not infer ownership for such vectors. When legacy local vectors need to be recovered, developers must explicitly rebuild/reindex the corresponding persisted documents or deliberately reset/re-upload according to the documented safe reset procedure.

## Authentication

Authentication is JWT-based.

The frontend uses the authenticated user and token to protect application routes and authenticated API requests. The backend validates the current user through its authentication dependency.

Ownership checks are applied before exposing or mutating user-owned documents and conversations.

## Document Lifecycle

The current document lifecycle is:

```text
Upload
  │
  ▼
Validate
  │
  ▼
Store Document File
  │
  ▼
Persist Metadata
  │
  ▼
Extract Text
  │
  ▼
Chunk Text
  │
  ▼
Generate Embeddings
  │
  ▼
Store Vectors
```

Document deletion cleans up the corresponding persistent resources according to the existing application deletion workflow, including document metadata and associated file/vector resources.

Supported document types:

- PDF
- DOCX
- TXT

## Chat and Conversation Capabilities

Authenticated users can:

- Start a new conversation.
- Continue an existing conversation.
- Send user messages.
- Receive persisted assistant answers.
- View ordered conversation history.
- View conversation titles.
- Delete conversations they own.
- Retry supported failed operations.
- See document availability inside Chat.

Conversation and message data are persisted in PostgreSQL.

New conversations derive a deterministic title from the first user query. Existing conversations keep their existing title.

Conversation deletion verifies ownership and removes the conversation together with its associated persisted messages.

## Current Tech Stack

### Backend
**Migration contract:** Docker backend startup currently launches Uvicorn directly and does not automatically run `alembic upgrade head`. The documented local startup workflow therefore treats database migrations as an explicit developer step. Task 42 Batch 2 verified this migration contract using fresh databases: migrations are functional and must be applied explicitly before starting a database-backed backend. This documentation does not claim automatic migrations.


- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Async Python
- JWT

### AI / RAG

- Retrieval-Augmented Generation
- Sentence Transformers
- `all-MiniLM-L6-v2`
- ChromaDB
- Semantic retrieval
- Provider-independent embedding boundary
- Provider-independent retrieval boundary
- Provider-independent LLM boundary
- Ollama

### Frontend

- React 19
- TypeScript
- Vite
- React Router
- Vitest
- Testing Library
- OXLint

### Infrastructure / Tooling

- Docker
- Docker Compose
- Git
- GitHub
- Linux
- Bash

## Local Development Setup

### Prerequisites

The current project expects a local development environment with:

- Python
- Node.js / npm
- PostgreSQL
- Docker / Docker Compose
- Ollama for local LLM generation

### Clone

```bash
git clone https://github.com/ahmed-morsi-ai/ai-document-rag.git
cd ai-document-rag
```

### Environment

Create a local environment file:

```bash
cp .env.example .env
```

Update the values for your machine before starting the application.

### Backend

Create and activate a virtual environment:

```bash
python -m venv backend/.venv
source backend/.venv/bin/activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

### Run Frontend

```bash
npm run dev
```

### Local Developer Startup

For a fresh clone, use this workflow:

1. Create the local environment file and adjust values for the machine:

```bash
cp .env.example .env
```

Do not commit real secrets or credentials.

2. PostgreSQL may be provided by the repository Compose setup:

```bash
docker compose up -d postgres
```

When the backend runs on the host and PostgreSQL runs through Docker Compose, `DATABASE_URL` must use the host-mapped PostgreSQL port, and that port must match `POSTGRES_PORT`. When the backend runs as a Compose service, use the PostgreSQL Compose service name as the hostname and container port `5432`, not the host-mapped port. Keep these values configurable rather than hardcoding a specific host port in the documentation.

From the repository root, activate the backend virtual environment, enter the backend directory, and run the existing Alembic migrations:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
cd ..
```

3. Ollama is an external local dependency. Make sure it is running and that the model configured by `OLLAMA_MODEL` is available. When the backend runs on the host, use `OLLAMA_BASE_URL=http://localhost:11434`; when the backend runs through Docker Compose, it uses `OLLAMA_BASE_URL=http://host.docker.internal:11434`. Ollama remains external to Compose.

4. Start the backend on the host:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

5. In another terminal, start the frontend with Vite:

```bash
cd frontend
npm install
npm run dev
```

The frontend uses `VITE_API_BASE_URL` to determine the backend API URL. Vite may use another port when its default port is already occupied.

The current `docker-compose.yml` provides PostgreSQL and a containerized backend only. It does not provide the frontend or Ollama, so Compose is not a self-contained full-application development environment.

### Initial Verification

Check the backend:

```bash
curl http://localhost:8000/health
```

Then open the URL reported by Vite and verify the normal application flow: register/login, upload a document, verify indexing/retrieval, use RAG chat and sources, verify conversation history, and verify document deletion.


## Environment / Configuration

The repository currently documents these environment variables in `.env.example`.

### Database

```text
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB
POSTGRES_PORT
DATABASE_URL
```

### Authentication

```text
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
```

JWT_SECRET_KEY must be at least 32 characters long.

### CORS

CORS_ORIGINS is a comma-separated list of allowed origins. Development defaults are http://localhost:5173 and http://127.0.0.1:5173. Wildcard (*) origins are rejected while credentialed CORS requests are enabled.

### Embeddings / Vector Storage

```text
EMBEDDING_MODEL
VECTOR_STORE_DIR
VECTOR_COLLECTION_NAME
```

### Local LLM

```text
OLLAMA_BASE_URL
OLLAMA_MODEL
OLLAMA_TIMEOUT_SECONDS
```

### Frontend

```text
VITE_API_BASE_URL
```

Do not commit real secrets or production credentials.

## Testing

### Frontend Type Checking

```bash
cd frontend
npm run typecheck
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Frontend Production Build

```bash
cd frontend
npm run build
```

### Backend Tests

From the repository root:

```bash
PYTHONPATH=backend python -m unittest discover \
  -s backend/tests \
  -p "test_*.py" \
  -v
```

### Backend Compile Check

```bash
python -m compileall backend
```

### Git Diff Check

```bash
git diff --check
```

The backend suite covers authentication, chat, conversations, persistence, document processing, document storage, embeddings, retrieval, RAG, LLM providers, vector storage, migrations, and API behavior.

## Current Limitations

### Project Scope vs. Future Production Evolution

The repository is a locally developed full-stack RAG application. The following are future production-evolution areas rather than missing core product features: production deployment configuration, production secret management, distributed/background processing, production observability, and large-scale operational infrastructure. Local Ollama usage and synchronous AI processing are also part of the current architecture.


The current repository is a locally developed full-stack RAG application and is not documented as a production deployment.

Current limitations include:

- No production deployment configuration is documented.
- Production secret management is outside the repository.
- The application depends on local infrastructure such as PostgreSQL, vector storage, and Ollama.
- OCR and scanned-document processing are not part of the current verified feature set.
- Bulk document deletion is not currently implemented. Document search and document pagination are implemented.
- Conversation search and conversation pagination are implemented.
- Production observability, distributed background processing, and large-scale operational infrastructure are outside the current scope.

## Repository Structure

```text
ai-document-rag/
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── .env.example
├── PROJECT_CONTEXT.md
└── README.md
```

## Project Status

The project is developed incrementally with focused implementation tasks and verification gates.

The current repository includes authenticated document workflows, semantic retrieval, RAG orchestration, local LLM integration, PostgreSQL-backed conversations and messages, document and conversation deletion, a shared authenticated frontend shell, and automated regression testing.

## Troubleshooting / Reset

### Normal Restart

Use the normal Compose workflow when you only need to restart the local services. This is non-destructive and preserves PostgreSQL, vector-store, and document-storage state.

Restart the existing Compose services without resetting persisted data.

### Database Reset

Compose PostgreSQL persists its state in the Docker named volume `ai-document-rag_postgres_data`.

A database reset is **destructive**: removing that volume destroys the PostgreSQL database state. Do not remove the volume as part of normal troubleshooting. Only perform a database reset deliberately when a fresh database is actually required.

### Vector-store Reset

The Chroma vector store is filesystem-backed. The repository currently contains both `./vector_store` and `./backend/vector_store`, so the relevant path depends on the runtime context in which the application is running.

Authenticated retrieval is always owner-scoped. Vectors without `owner_id` are not eligible for authenticated retrieval and must never be exposed through an unrestricted fallback.

Developers with Chroma data created before the owner-aware retrieval change may have stale ownerless vectors. Those vectors are fail-closed by the owner filter, so they are not returned to authenticated users, but they are not retrievable until they are rebuilt with ownership metadata.

The repository does not automatically migrate ownerless local vectors. Do not invent ownership from vector content, filenames, or document IDs. If a legacy vector can be safely rebuilt from a persisted application document, reindex that document through the normal owner-aware indexing path. If the corresponding persisted document cannot be resolved safely, treat the vector as stale local data and reset only the confirmed active local vector-store directory, then re-upload or reindex the source documents. Never add an unrestricted retrieval fallback to make ownerless vectors retrievable.

A vector-store reset is **destructive**: removing the relevant persisted vector-store directory removes indexed vectors and requires the affected documents to be indexed again. Do not use an ambiguous `rm -rf vector_store` command without first confirming which runtime path is active.

### Document-storage Reset

Document storage is also filesystem-backed, with both `./storage` and `./backend/storage` present in the repository. The correct path is context-sensitive and depends on how the backend is running.

A document-storage reset is **destructive**. Deleting stored document files independently can leave database metadata inconsistent with the filesystem. For ordinary cleanup, prefer deleting documents through the application rather than removing storage files directly.

### Full Local Reset

A full local reset is **destructive** and affects the local database, vector store, and document storage.

Treat it as a deliberate recovery operation, not a default troubleshooting step. Before removing any state, identify the active runtime paths, understand what will be lost, and back up anything that must be preserved. Do not use a blind multi-delete command or automated reset script.

### Common Runtime Problems

- **`rag_backend` container-name conflict:** A stale Compose backend container can keep the `rag_backend` name or host port occupied. Inspect the existing container and its Compose project before removing anything; do not automatically remove containers as part of normal startup troubleshooting.

- **PostgreSQL host vs. Compose addressing:** The host-native database URL uses the host-mapped PostgreSQL port, while the Compose backend reaches PostgreSQL through the Compose service name on port `5432`. Check which runtime is making the connection before changing `DATABASE_URL`.

- **Compose backend → host Ollama:** The Compose backend reaches host Ollama through `http://host.docker.internal:11434`. On the current Compose workflow, the `host.docker.internal` host-gateway mapping is configured for this connection.

- **Host backend → Ollama:** When the backend runs directly on the host, use `http://localhost:11434`.

- **Stale Docker image after dependency or Dockerfile changes:** Source-only changes do not require an image rebuild because Compose bind-mounts `./backend:/app`. Changes to `requirements.txt` or the Dockerfile do require rebuilding the backend image before restarting the container.

- **Docker build package-download/network timeout:** A Docker build can fail while downloading Python packages because of a package-index or network timeout. Treat this as a build/download problem first rather than changing application code or reset state.

- **Frontend Vite not running / port 5173 unavailable:** The frontend runs separately from the current Compose services. If nothing is listening on the documented Vite port `5173`, start the frontend development server and then retry the frontend check.
