import type { DocumentItem } from "../types/documents";

interface DocumentListProps {
  documents: DocumentItem[];
  isLoading: boolean;
  error: string;
}

export function DocumentList({
  documents,
  isLoading,
  error,
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

      {!isLoading &&
      !error &&
      documents.length === 0 ? (
        <p>No documents uploaded yet.</p>
      ) : null}

      {!isLoading && !error && documents.length > 0 ? (
        <ul>
          {documents.map((document) => (
            <li key={document.id}>
              <strong>{document.original_filename}</strong>
              <span>
                {" "}
                · {document.processing_status}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
