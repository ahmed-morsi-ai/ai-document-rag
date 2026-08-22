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

  const [documents, setDocuments] = useState<
    DocumentItem[]
  >([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadDocuments = useCallback(async () => {
    if (!token) {
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      setDocuments(
        await documentsApi.list(token),
      );
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
    setDocuments((current) => [
      document,
      ...current,
    ]);
  }

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <main>
      <header>
        <div>
          <p>AI Document RAG</p>
          <h1>Dashboard</h1>
          <p>
            Signed in as <strong>{user?.email}</strong>
          </p>
        </div>

        <button
          type="button"
          onClick={handleLogout}
        >
          Log out
        </button>
      </header>

      <DocumentUpload
        token={token!}
        onUploaded={handleUploaded}
      />

      <DocumentList
        documents={documents}
        isLoading={isLoading}
        error={error}
      />
    </main>
  );
}
