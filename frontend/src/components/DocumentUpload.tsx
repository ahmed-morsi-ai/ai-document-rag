import { useState, type ChangeEvent } from "react";
import { ApiError } from "../services/api";
import { documentsApi } from "../services/documents";
import type { DocumentItem } from "../types/documents";

const ACCEPTED_TYPES = new Set([
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
]);

interface DocumentUploadProps {
  token: string;
  onUploaded: (document: DocumentItem) => void;
}

export function DocumentUpload({
  token,
  onUploaded,
}: DocumentUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<
    "idle" | "uploading" | "success" | "error"
  >("idle");
  const [error, setError] = useState("");

  function handleChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0] ?? null;

    setSelectedFile(file);
    setError("");
    setStatus("idle");

    if (file && !ACCEPTED_TYPES.has(file.type)) {
      setSelectedFile(null);
      setStatus("error");
      setError(
        "Unsupported file type. Please choose a PDF, DOCX, or TXT file.",
      );
    }
  }

  async function handleUpload() {
    if (!selectedFile || status === "uploading") {
      return;
    }

    setStatus("uploading");
    setError("");

    try {
      const uploaded = await documentsApi.upload(
        token,
        selectedFile,
      );

      onUploaded(uploaded);
      setSelectedFile(null);
      setStatus("success");
    } catch (err) {
      setStatus("error");

      if (
        err instanceof ApiError &&
        (err.status === 401 || err.status === 403)
      ) {
        setError("Your session has expired. Please sign in again.");
      } else if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Upload failed. Please try again.");
      }
    }
  }

  return (
    <section aria-labelledby="document-upload-title">
      <h2 id="document-upload-title">Upload document</h2>

      <label htmlFor="document-file">
        Choose a PDF, DOCX, or TXT file
      </label>

      <input
        id="document-file"
        type="file"
        accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
        onChange={handleChange}
        disabled={status === "uploading"}
      />

      {selectedFile ? (
        <p>{selectedFile.name}</p>
      ) : null}

      <button
        type="button"
        onClick={handleUpload}
        disabled={
          !selectedFile ||
          status === "uploading"
        }
      >
        {status === "uploading"
          ? "Uploading…"
          : "Upload document"}
      </button>

      {status === "success" ? (
        <p role="status">
          Document uploaded successfully.
        </p>
      ) : null}

      {status === "error" ? (
        <p role="alert">{error}</p>
      ) : null}
    </section>
  );
}
