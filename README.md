# AI Document RAG

AI Document RAG is a full-stack document question-answering application that lets authenticated users upload documents, process and index their content for semantic retrieval, and chat against the available document context.

The project combines a FastAPI backend, PostgreSQL persistence, persistent vector storage, provider-independent RAG services, local LLM integration through Ollama, and a React/TypeScript frontend.

## Current Verified Feature Set

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

Run the backend using the repository's FastAPI configuration and the environment in `.env`.

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

The current repository is a locally developed full-stack RAG application and is not documented as a production deployment.

Current limitations include:

- No production deployment configuration is documented.
- Production secret management is outside the repository.
- The application depends on local infrastructure such as PostgreSQL, vector storage, and Ollama.
- OCR and scanned-document processing are not part of the current verified feature set.
- Bulk document deletion, document search, and document pagination are not implemented.
- Conversation search and pagination are not implemented.
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
