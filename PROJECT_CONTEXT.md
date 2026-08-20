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

## In Progress
- No implementation task is currently in progress after Task 3.

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
- No document upload endpoints, parsing, chunking, embeddings, vector storage, conversation model, chat endpoint, or RAG implementation exists yet.
- No tests exist beyond the focused auth regression and document model/migration checks.

## Completed Tasks
- Task 1: Inspect Configuration & Authentication Architecture — completed.
- Task 2: Fix JWT Settings Attribute Mismatch — completed in commit `c0d75c9` and pushed to `origin/main`.
- Task 3: Document Model + Alembic Migration — completed in commit `feat(db): add document model and migration`.

## Current Task
- Task 3: Document Model + Alembic Migration — completed.

## Next Task
- Add document file upload endpoints and storage flow backed by the Document model.
