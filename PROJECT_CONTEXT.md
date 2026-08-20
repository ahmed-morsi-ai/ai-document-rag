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

## In Progress
- No implementation task is currently in progress after Task 7.

## Planned
- Add document file upload endpoints and storage flow.
- Add document parsing and chunking.
- Integrate embeddings and Chroma vector storage.
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
- Parsing, chunking, embeddings, vector storage, conversation model, chat endpoint, and RAG implementation do not exist yet.
- Test coverage currently consists of focused auth regression, document model/migration, document upload validation, and document upload endpoint checks rather than a comprehensive application test suite.
- Authentication tests emit an `InsecureKeyLengthWarning` because the JWT HMAC key used in the test environment is shorter than the recommended 32 bytes. This was not changed as part of Task 4.

## Completed Tasks
- Task 1: Inspect Configuration & Authentication Architecture — completed.
- Task 2: Fix JWT Settings Attribute Mismatch — completed in commit `c0d75c9` and pushed to `origin/main`.
- Task 3: Document Model + Alembic Migration — completed in commit `feat(db): add document model and migration`.
- Task 4: Add document upload request validation — completed in commit `3b8bdf6` and pushed to `origin/main`.
- Task 5: Add document upload endpoint skeleton — completed locally and verified with focused and full test suites.
- Task 6: Add local document storage service — completed and committed.

## Current Task
- Task 7: Persist uploaded document metadata and connect the upload flow to the Document model — completed and verified.

## Next Task
- Task 7: Persist uploaded document metadata and connect the upload flow to the Document model.
