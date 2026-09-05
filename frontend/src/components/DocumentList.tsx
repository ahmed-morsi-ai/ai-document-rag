import type { DocumentItem } from "../types/documents";

interface DocumentListProps {
  documents: DocumentItem[];
  totalCount: number;
  currentPage: number;
  pageSize: number;
  search: string;
  isLoading: boolean;
  error: string;
  deleteTargetDocumentId: string | null;
  deletingDocumentId: string | null;
  deleteError: string;
  onDeleteRequest: (documentId: string) => void;
  onDeleteCancel: () => void;
  onDeleteConfirm: (documentId: string) => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Date unavailable";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
  }).format(date);
}

function formatType(document: DocumentItem) {
  const extension = document.original_filename.includes(".")
    ? document.original_filename.split(".").pop()?.toUpperCase()
    : null;

  if (extension) {
    return extension;
  }

  return document.mime_type.split("/").pop()?.toUpperCase() || "FILE";
}

function DocumentIcon({ type }: { type: string }) {
  return (
    <div className={`document-type-icon document-type-${type.toLowerCase()}`}>
      <span>{type === "PDF" ? "PDF" : type}</span>
    </div>
  );
}

export function DocumentList({
  documents,
  totalCount,
  currentPage,
  pageSize,
  search,
  isLoading,
  error,
  deleteTargetDocumentId,
  deletingDocumentId,
  deleteError,
  onDeleteRequest,
  onDeleteCancel,
  onDeleteConfirm,
  onPreviousPage,
  onNextPage,
}: DocumentListProps) {
  const isLastPage = currentPage * pageSize >= totalCount;

  return (
    <section
      className="document-workspace"
      aria-labelledby="document-list-title"
    >
      <div className="document-workspace-header">
        <div>
          <p className="workspace-section-kicker">Library</p>
          <h2 id="document-list-title">Your documents</h2>
        </div>

        {!isLoading && !error ? (
          <span className="document-count">
            {totalCount} {totalCount === 1 ? "document" : "documents"}
          </span>
        ) : null}
      </div>

      {isLoading ? (
        <div className="document-state document-state-loading" role="status">
          <div className="document-state-icon" aria-hidden="true">…</div>
          <div>
            <strong>Loading your documents</strong>
            <p>Your workspace is being refreshed.</p>
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="document-state document-state-error" role="alert">
          <div className="document-state-icon" aria-hidden="true">!</div>
          <div>
            <strong>We couldn't load your documents</strong>
            <p>{error}</p>
          </div>
        </div>
      ) : null}

      {deleteError ? (
        <div className="document-inline-alert" role="alert">
          {deleteError}
        </div>
      ) : null}

      {!isLoading && !error && documents.length === 0 ? (
        <div className="document-state document-state-empty">
          <div className="document-state-icon" aria-hidden="true">+</div>
          <div>
            <strong>
              {search ? "No matching documents" : "No documents yet"}
            </strong>
            <p>
              {search
                ? "Try a different filename."
                : "Upload a document to get started with your workspace."}
            </p>
          </div>
        </div>
      ) : null}

      {!isLoading && !error && documents.length > 0 ? (
        <div className="document-list">
          {documents.map((document) => {
            const isTarget = deleteTargetDocumentId === document.id;
            const isDeleting = deletingDocumentId === document.id;
            const type = formatType(document);

            return (
              <article
                className={`document-card${
                  isDeleting ? " document-card-deleting" : ""
                }`}
                key={document.id}
              >
                <div className="document-card-main">
                  <DocumentIcon type={type} />

                  <div className="document-card-copy">
                    <strong className="document-filename">
                      {document.original_filename}
                    </strong>

                    <div className="document-metadata">
                      <span>{type}</span>
                      <span>Uploaded {formatDate(document.created_at)}</span>
                      <span>{document.processing_status}</span>
                    </div>
                  </div>
                </div>

                <div className="document-card-actions">
                  {isDeleting ? (
                    <span className="document-delete-progress" role="status">
                      Deleting…
                    </span>
                  ) : isTarget ? (
                    <div className="document-confirmation">
                      <span>Delete this document?</span>
                      <button
                        type="button"
                        className="secondary document-confirm-cancel"
                        onClick={onDeleteCancel}
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        className="danger-button"
                        onClick={() => onDeleteConfirm(document.id)}
                      >
                        Confirm delete
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      className="document-delete-button"
                      onClick={() => onDeleteRequest(document.id)}
                      disabled={Boolean(deletingDocumentId)}
                    >
                      Delete
                    </button>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      ) : null}

      {!isLoading && !error && documents.length > 0 ? (
        <nav aria-label="Document pagination">
          <button
            type="button"
            onClick={onPreviousPage}
            disabled={currentPage === 1}
            aria-label="Previous page"
          >
            Previous
          </button>
          <span aria-current="page">Page {currentPage}</span>
          <button
            type="button"
            onClick={onNextPage}
            disabled={isLastPage}
            aria-label="Next page"
          >
            Next
          </button>
        </nav>
      ) : null}
    </section>
  );
}
