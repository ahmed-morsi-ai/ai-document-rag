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

## Current Task
- Task 14: Chat/RAG — Batch 2 completed and verified.
- A provider-independent `LLMProvider` abstraction exists in `backend/app/services/llm/base.py`.
- No concrete LLM provider is established or implemented; provider selection remains deferred.
- The current RAG flow remains query → retrieval → deterministic context assembly.
- RAG-to-LLM generation integration, chat endpoint, conversation persistence, and streaming do not exist yet.

## Next Task
- Next: Connect `RagService` to the chosen/provider-independent LLM boundary in a separate batch.
