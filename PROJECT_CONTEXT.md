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

## In Progress
- Completion of the authentication flow beyond the basic scaffold.
- Expansion from a user-only model into the full document and conversation architecture in the project roadmap.
- Full project build-out for file ingestion, RAG, chat, and frontend UI.

## Planned
- Add document model, file upload endpoints, and storage flow.
- Add document parsing and chunking.
- Integrate embeddings and Chroma vector storage.
- Add conversation model and chat endpoint with retrieval support.
- Build frontend auth, dashboard, upload, and chat UI.
- Add production-grade configuration, tests, and project documentation.

## Unknown
- Exact final architecture for document storage and retrieval because the codebase has not reached that phase yet.
- Target LLM provider and embedding model because no corresponding code or configuration exists.
- Full frontend framework and structure because the frontend folder is empty.

## Known Issues
- The project still does not implement the full roadmap beyond a minimal auth foundation.
- The frontend directory is empty.
- No document model, conversation model, or RAG implementation exists yet.
- No tests exist beyond the focused auth regression check created for this fix.
- No GitHub remote is configured beyond the repository URL already set in Git.

## Completed Tasks
- Task 1: Inspect Configuration & Authentication Architecture — completed.
- Task 2: Fix Settings Attribute Mismatch — completed after confirming the regression in the current repository state.

## Current Task
- Fix the current JWT settings regression and confirm the auth dependency works with the actual project configuration.

## Next Task
- Add the document model and migration for file uploads and document processing, then validate the schema with Alembic.
