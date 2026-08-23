import type { DocumentItem } from "../types/documents";

interface DocumentListProps {
  documents: DocumentItem[];
  isLoading: boolean;
  error: string;
  deletingDocumentId: string | null;
  deleteError: string;
  onDeleteRequest: (documentId: string) => void;
  onDeleteCancel: () => void;
  onDeleteConfirm: (documentId: string) => void;
}

export function DocumentList({
  documents,
  isLoading,
  error,
  deletingDocumentId,
  deleteError,
  onDeleteRequest,
  onDeleteCancel,
  onDeleteConfirm,
}: DocumentListProps) {
  return (
    <section aria-labelledby="document-list-title">
      <h2 id="document-list-title">Your documents</h2>

      {isLoading ? (
        <p role="status">Loading documents…</p>
      ) : null}

      {error ? (
        <p role="alert">{error}</p>
      ) : null}

      {deleteError ? (
        <p role="alert">{deleteError}</p>
      ) : null}

      {!isLoading && !error && documents.length === 0 ? (
        <div>
          <p>
            No documents uploaded yet. Use the upload area above to add your
            first document.
          </p>
          <p>
            After uploading, use Continue to Chat to start asking questions.
          </p>
        </div>
      ) : null}

      {!isLoading && !error && documents.length > 0 ? (
        <ul>
          {documents.map((document) => {
            const isDeleting = deletingDocumentId === document.id;

            return (
              <li key={document.id}>
                <strong>{document.original_filename}</strong>
                <span>{" "}· {document.processing_status}</span>

                {isDeleting ? (
                  <div>
                    <p>Delete this document?</p>
                    <button type="button" onClick={onDeleteCancel}>
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={() => onDeleteConfirm(document.id)}
                      disabled={!deletingDocumentId}
                    >
                      Confirm delete
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => onDeleteRequest(document.id)}
                    disabled={Boolean(deletingDocumentId)}
                  >
                    Delete
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      ) : null}
    </section>
  );
}
