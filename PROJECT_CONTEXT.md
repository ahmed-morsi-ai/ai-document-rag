# Project Context

## Implemented
- FastAPI application shell exists in `backend/app/main.py`.
- User auth routes exist in `backend/app/api/routes/auth.py`.
- JWT creation and password hashing exist in `backend/app/core/security/auth.py`.
- PostgreSQL async database configuration exists in `backend/app/db/database.py`.
- SQLAlchemy user model exists in `backend/app/db/models.py`.
- Alembic is configured and a user migration exists in `backend/alembic/versions/7c16b04319c9_create_users_table.py`.
- Docker Compose defines a PostgreSQL service and backend service in `docker-compose.yml`.
- The auth configuration mismatch regression was fixed in the repository by updating JWT and database settings references to use the uppercase configuration attributes.
- Commit `c0d75c9` contains the completed JWT configuration fix and is already pushed to `origin/main`.
- Document SQLAlchemy model exists in `backend/app/db/models.py`.
- Document Alembic migration exists in `backend/alembic/versions/b8e6d2f4a913_add_documents_table.py`.
- Focused document model and migration tests exist in `backend/tests/test_document_model_migration.py`.
- Document upload request validation exists in `backend/app/services/document_validation.py`.
- Validation supports PDF, DOCX, and TXT files and checks filename presence, length, path separators, invalid characters, file extension, and extension/content-type consistency.
- Focused document upload validation tests exist in `backend/tests/test_document_validation.py`.
- Authenticated document upload endpoint skeleton exists at `POST /documents/upload`.
- The endpoint reuses document upload validation and does not yet perform file storage, database persistence, parsing, or processing.
- Focused document upload endpoint tests exist in `backend/tests/test_document_upload_endpoint.py`.
- Local document storage service exists in `backend/app/services/document_storage.py`.
- Document storage paths are generated uniquely and scoped by document owner.
- The storage service creates owner directories, writes uploaded files locally, prevents overwriting existing files, and removes partial files when a write operation fails.
- Focused document storage tests exist in `backend/tests/test_document_storage.py`.
- Document parser abstraction exists in `backend/app/services/document_parsers/base.py`.
- Parser selection exists for PDF, DOCX, and TXT document types.
- Unsupported document types are rejected by the parser selector.
- Focused document parser abstraction, selection, and real-file text extraction tests exist in `backend/tests/test_document_parsers.py`.
- PDF text extraction is implemented using `pypdf`.
- DOCX text extraction is implemented using `python-docx`.
- TXT text extraction is implemented using UTF-8 file reading.
- Document text chunking is implemented in `backend/app/services/document_chunking.py`.
- Chunking uses deterministic character-based chunks with configurable chunk size and overlap.
- Invalid chunking configuration is rejected with `ValueError`.
- Focused document chunking tests exist in `backend/tests/test_document_chunking.py`.
- A provider-independent embedding abstraction exists in `backend/app/services/embeddings/base.py`.
- The embedding abstraction defines single-text and ordered batch embedding contracts.
- A local `sentence-transformers` embedding provider is implemented in `backend/app/services/embeddings/sentence_transformer.py`.
- The concrete provider accepts an explicit model name and does not define a default model or provider configuration yet.
- Focused embedding abstraction tests exist in `backend/tests/test_embeddings.py`.
- Focused sentence-transformers provider tests exist in `backend/tests/test_sentence_transformer_embeddings.py`.

## In Progress
- Task 11 — Embeddings and Vector Storage Integration is in progress.
- Task 12 — Document Indexing is in progress.
- Task 12 Batch 1 introduced the document indexing orchestration service.
- Task 12 Batch 2 integrates synchronous document indexing into the successful upload flow.
- The upload flow is validation → storage → document persistence → indexing.

## Planned
- Implement retrieval workflows on top of the vector-store query contract.
- Add conversation model and chat endpoint with retrieval support.
- Build frontend auth, dashboard, upload, and chat UI.
- Add production-grade configuration, tests, and project documentation.

## Unknown
- Exact final architecture for document storage and retrieval beyond the current database foundation.
- Target LLM provider and embedding model because no corresponding code or configuration exists.
- Full frontend framework and structure because the frontend folder is empty.

## Known Issues
- The project still does not implement the full roadmap beyond the auth foundation and document database foundation.
- The frontend directory is empty.
- The document upload flow now validates authenticated upload requests, stores files locally, persists document metadata, and removes stored files if database persistence fails.
- Document parser abstraction, parser selection, PDF, DOCX, and TXT text extraction, and deterministic character-based document chunking are implemented.
- A provider-independent embedding abstraction and local `sentence-transformers` concrete provider are implemented.
- No embedding model is configured as a project-wide default yet.
- A provider-independent vector-store abstraction exists in `backend/app/services/vector_store/base.py`.
- A local persistent Chroma vector-store implementation exists in `backend/app/services/vector_store/chroma.py`.
- The Chroma backend uses `chromadb==1.5.9` and stores vectors, source text, and generic string metadata.
- Vector queries return provider-independent `VectorQueryResult` objects.
- Document indexing orchestration is implemented in `backend/app/services/document_indexing.py`.
- Successful document uploads invoke indexing after file storage and document metadata persistence succeed.
- Indexing failures propagate to the upload caller rather than being silently ignored.
- Retrieval workflows, conversation model, chat endpoint, and RAG implementation do not exist yet.
- Test coverage currently consists of focused auth regression, document model/migration, document upload validation, and document upload endpoint checks rather than a comprehensive application test suite.
- Authentication tests emit an `InsecureKeyLengthWarning` because the JWT HMAC key used in the test environment is shorter than the recommended 32 bytes. This was not changed as part of Task 4.

## Completed Tasks
- Task 1: Inspect Configuration & Authentication Architecture — completed.
- Task 2: Fix JWT Settings Attribute Mismatch — completed in commit `c0d75c9` and pushed to `origin/main`.
- Task 3: Document Model + Alembic Migration — completed in commit `feat(db): add document model and migration`.
- Task 4: Add document upload request validation — completed in commit `3b8bdf6` and pushed to `origin/main`.
- Task 5: Add document upload endpoint skeleton — completed locally and verified with focused and full test suites.
- Task 6: Add local document storage service — completed and committed.
- Task 7: Persist uploaded document metadata and connect the upload flow to the Document model — completed in commit `34aaf4a` and pushed to `origin/main`.
- Task 8: Add document parser abstraction and parser selection — completed and verified.
- Task 9: Implement document text extraction using the parser abstraction — completed and verified with real TXT, PDF, and DOCX files.
- Task 10: Implement document text chunking for extracted document content — completed in commit `c7a1bb1` and pushed to `origin/main`.
- Task 11 Batch 1: Add provider-independent embedding abstraction — completed in commit `2f02c3c` and pushed to `origin/main`.
- Task 11 Batch 2: Implement local `sentence-transformers` embedding provider — completed and verified.
- Task 11 Batch 3: Add vector-store abstraction and local persistent Chroma backend — completed and verified.
- Task 12 Batch 1: Add document indexing orchestration service — completed in commit `f1563c7` and verified.
- Task 12 Batch 2: Integrate document indexing with document upload — completed and verified.
- Task 13 Batch 1: Add provider-independent retrieval service — completed and verified.
- Task 13 Batch 2: Add authenticated retrieval API endpoint — completed and verified.
- Task 14 Batch 1: Add provider-independent RAG context service — completed and verified.
- Task 14 Batch 2: Add provider-independent LLM provider abstraction — completed and verified.
- Task 14 Batch 3: Connect `RagService` to the `LLMProvider` boundary — completed and verified.
- Task 14 Batch 4: Implement concrete local Ollama LLM provider — completed and verified.
- Task 14 Batch 5: Wire Ollama provider into application-level `RagService` — completed and verified.
- Task 15: Add application-level `ChatService` — completed and verified.
- Task 16: Add authenticated `POST /chat` Chat API endpoint — completed and verified.
- Task 17: Add Conversation persistence model and Alembic migration — completed and verified.
- Task 18: Add Message persistence model and Alembic migration — completed and verified.
- Task 19: Add Chat Persistence Service for conversations and messages — completed and verified.
- Task 20: Persist chat interactions through `ChatService` — completed and verified.
- Task 21: Add authenticated conversation history endpoints — completed and verified.
- Task 22: Add frontend foundation and authentication — completed and verified.
- Task 23: Add dashboard and document upload — completed and verified.

## Current Task
- Task 25 — Application Workflow: CLOSED.
- Batch 1 — Document-to-Chat Workflow Integration: CLOSED.
- Batch 2A — Provider-Independent Vector Deletion: CLOSED.
- Batch 2B1 — VectorStore Application Wiring: CLOSED.
- Batch 2B2 — Safe Backend Document Deletion: CLOSED.
- Batch 2B3 — Frontend Document Deletion Flow: CLOSED.
- Task 26 — Conversation Management: CLOSED.
- Batch 1 — Safe Backend Conversation Deletion: CLOSED.
- Batch 2 — Frontend Conversation Deletion Flow: CLOSED.
- Task 27 — Conversation Titles: CLOSED.
- Task 28 — Document Context Visibility: CLOSED.
- Chat now loads the authenticated user's existing documents independently from conversation loading.
- The chat UI shows document availability without blocking conversation/history/message interaction.
- Document availability has explicit loading, success, empty, and retryable error states.
- Empty document state provides a direct path back to the Dashboard for document upload.
- Existing typed documents API is reused; no new backend endpoint was added.
- No document selection, filtering, polling, RAG, retrieval, embedding, LLM, or backend workflow changes were introduced.
- Task 29 — UI Design System & Application Shell: CLOSED.
- The shared authenticated shell owns top-level application navigation, New Chat, authenticated user context, and logout.
- `/app` and `/app/chat` are rendered through the shared shell under the existing ProtectedRoute.
- The shell uses a centralized neutral design-token system with responsive sidebar behavior and accessible focus states.
- Task 30 — Dashboard & Documents Redesign: CLOSED.
- Task 31 — Chat Workspace Redesign: CLOSED.
- Chat redesign is presentation-only and preserves the existing conversation, history, deletion, document-context, send, loading, error, retry, logout, and navigation behavior.
- The Chat Workspace uses the shared light/dark theme and Task 29/30 design tokens.
- Dashboard/Documents visual redesign is presentation-only and reuses the existing document API/contracts.
- User-selectable Light and Dark themes are implemented through the shared frontend design-token system.
- Theme preference is persisted locally and initialized from the user's system preference when no saved preference exists.
- The redesign covers the Dashboard workspace, document list/cards, upload experience, document deletion presentation, empty/loading/error states, Document-to-Chat CTA presentation, and responsive behavior.
- Task 32 — Accessibility & Responsive QA: CLOSED.
- Task 33 — RAG Source Transparency: CLOSED.
- Batch 1 — RAG Source Contract: CLOSED.
- Batch 2 — Frontend RAG Source / Citation UI: CLOSED.
- The verified source pipeline is:
  RetrievalResult[]
      ↓
  RagContext.sources
      ↓
  RagResponse.sources
      ↓
  ChatResponse.sources
      ↓
  HTTP ChatResponse.sources
      ↓
  Frontend source display
- Frontend source display uses only the verified backend source fields: `text`, `document_id`, `chunk_index`, `distance`, and `metadata`.
- Source data is derived directly from actual retrieval results.
- No fabricated page numbers, URLs, or confidence scores are presented.
- No provider-specific source data is exposed to frontend consumers.
- Source order follows backend retrieval order.
- Empty retrieval produces an empty source collection with no fabricated source.
- Frontend source display is implemented in the Chat workspace.
- Task 34 — RAG Evaluation & Quality Measurement: CLOSED.
- Batch 1 — Evaluation Dataset & Retrieval Metrics: CLOSED.
- Batch 2 — Real Retrieval Evaluation & Results Reporting: CLOSED.
- Controlled evaluation corpus: `backend/evaluation/corpus/`.
- The corpus contains three repository-owned synthetic documents and is indexed using the existing parser, chunking, `DocumentIndexer`, embedding provider, and Chroma implementation.
- Evaluation is performed at chunk level using the stable `<document_id>:<chunk_index>` key.
- Evaluation dataset: `backend/evaluation/retrieval_v1.json`.
- The evaluation dataset contains 6 controlled cases whose relevance labels correspond to actual indexed chunks.
- Real retrieval execution uses the existing `Retriever` with the existing `all-MiniLM-L6-v2` embedding provider and an isolated temporary Chroma vector store.
- Evaluated K values: 1, 3, and 5.
- Recall@1 = 0.75, Recall@3 = 0.8333333333333334, Recall@5 = 0.8333333333333334.
- Precision@1 = 0.8333333333333334, Precision@3 = 0.3333333333333333, Precision@5 = 0.20000000000000004.
- HitRate@1 = 0.8333333333333334, HitRate@3 = 0.8333333333333334, HitRate@5 = 0.8333333333333334.
- Repeated real evaluation runs produced identical metric values for K=1, K=3, and K=5.
- The real evaluation uses an isolated temporary vector store and does not modify the normal project vector-store data.
- The evaluation framework remains lightweight and provider-independent at the metric layer.
- The reported measurements represent controlled retrieval quality only and are not production accuracy or a universal benchmark.
- LLM answer-quality evaluation is NOT implemented yet.
- Task 35 — RAG Grounding & Answer-Quality Evaluation: IN PROGRESS.
  - Batch 1A — Grounding Dataset Model, Loader & Unit Tests: CLOSED.
  - Batch 1B — Grounding Runner Integration & Evaluation Reporting: NOT STARTED.
  - Grounding evaluation calculates evidence coverage across normalized source texts.
  - Grounding dataset: `backend/evaluation/grounding_v1.json`.
  - All grounding evaluation logic and dataset parsing remain strictly provider-independent.
