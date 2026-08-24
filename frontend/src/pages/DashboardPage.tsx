import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../services/api";
import { documentsApi } from "../services/documents";
import { DocumentList } from "../components/DocumentList";
import { DocumentUpload } from "../components/DocumentUpload";
import type { DocumentItem } from "../types/documents";

export function DashboardPage() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [showChatCta, setShowChatCta] = useState(false);
  const [deleteTargetDocumentId, setDeleteTargetDocumentId] = useState<string | null>(
    null,
  );
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(
    null,
  );
  const [deleteError, setDeleteError] = useState("");

  const loadDocuments = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      setDocuments(await documentsApi.list(token));
    } catch (err) {
      if (
        err instanceof ApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        logout();
        navigate("/login", { replace: true });
        return;
      }

      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to load documents.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [logout, navigate, token]);

  useEffect(() => {
    void loadDocuments();
  }, [loadDocuments]);

  function handleUploaded(document: DocumentItem) {
    setDocuments((current) => [document, ...current]);
    setShowChatCta(true);
  }

  function handleDeleteRequest(documentId: string) {
    if (deletingDocumentId) {
      return;
    }

    setDeleteError("");
    setDeleteTargetDocumentId(documentId);
  }

  function handleDeleteCancel() {
    if (deletingDocumentId) {
      return;
    }

    setDeleteTargetDocumentId(null);
    setDeleteError("");
  }

  async function handleDeleteConfirm(documentId: string) {
    if (
      !token ||
      deleteTargetDocumentId !== documentId ||
      deletingDocumentId
    ) {
      return;
    }

    setDeleteError("");
    setDeletingDocumentId(documentId);

    try {
      await documentsApi.delete(token, documentId);

      setDocuments((current) =>
        current.filter((document) => document.id !== documentId),
      );
      setDeleteTargetDocumentId(null);
    } catch (err) {
      setDeleteError(
        err instanceof ApiError
          ? err.message
          : "Unable to delete document. Please try again.",
      );
      setDeleteTargetDocumentId(null);
    } finally {
      setDeletingDocumentId(null);
    }
  }

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="workspace-page">
      <header className="workspace-page-header">
        <div className="workspace-page-heading">
          <p className="workspace-kicker">Document workspace</p>
          <h1>Documents</h1>
          <p className="workspace-description">
            Upload, review, and manage the documents available to your workspace.
          </p>
        </div>

        <div className="workspace-page-actions">
          <button
            type="button"
            className="primary"
            onClick={() => {
              document
                .getElementById("document-file")
                ?.click();
            }}
          >
            Upload Document
          </button>

          <button
            type="button"
            className="secondary"
            onClick={() => navigate("/app/chat")}
          >
            Open Chat
          </button>

          <button
            type="button"
            className="secondary workspace-logout-button"
            onClick={handleLogout}
          >
            Log out
          </button>
        </div>
      </header>

      <div className="workspace-welcome">
        <div className="workspace-avatar" aria-hidden="true">
          {user?.email?.slice(0, 1).toUpperCase() || "U"}
        </div>
        <div>
          <strong>{user?.email}</strong>
          <span>Your personal document workspace</span>
        </div>
      </div>

      <section
        className="workspace-summary"
        aria-label="Document summary"
      >
        <div>
          <span className="workspace-summary-label">Documents</span>
          <strong>{documents.length}</strong>
        </div>

        <div>
          <span className="workspace-summary-label">Supported</span>
          <strong>PDF · DOCX · TXT</strong>
        </div>

        <div>
          <span className="workspace-summary-label">Next step</span>
          <strong>{documents.length > 0 ? "Ask in Chat" : "Upload a file"}</strong>
        </div>
      </section>

      <section
        className="workspace-upload-section"
        aria-labelledby="document-upload-title"
      >
        <DocumentUpload
          token={token!}
          onUploaded={handleUploaded}
        />

        {showChatCta ? (
          <div className="workspace-post-upload">
            <div>
              <span className="workspace-post-upload-label">Ready</span>
              <strong>Your document is ready for the next step.</strong>
              <p>
                Continue to Chat to ask questions using your document context.
              </p>
            </div>

            <button
              type="button"
              className="primary"
              onClick={() => navigate("/app/chat")}
            >
              Continue to Chat
            </button>
          </div>
        ) : null}
      </section>

      <DocumentList
        documents={documents}
        isLoading={isLoading}
        error={error}
        deleteTargetDocumentId={deleteTargetDocumentId}
        deletingDocumentId={deletingDocumentId}
        deleteError={deleteError}
        onDeleteRequest={handleDeleteRequest}
        onDeleteCancel={handleDeleteCancel}
        onDeleteConfirm={handleDeleteConfirm}
      />
    </div>
  );
}
