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

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
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
    <div className="upload-panel">
      <div className="upload-panel-heading">
        <div>
          <p className="workspace-section-kicker">Add to workspace</p>
          <h2 id="document-upload-title">Upload document</h2>
          <p>
            Bring a PDF, DOCX, or TXT file into your document workspace.
          </p>
        </div>

        <span className="upload-supported">PDF · DOCX · TXT</span>
      </div>

      <label
        className={`upload-drop-area${
          selectedFile ? " has-file" : ""
        }`}
        htmlFor="document-file"
      >
        <span className="upload-drop-icon" aria-hidden="true">
          {selectedFile ? "✓" : "+"}
        </span>

        <span className="upload-drop-copy">
          <strong>
            {selectedFile
              ? selectedFile.name
              : "Choose a document to upload"}
          </strong>
          <span>
            {selectedFile
              ? `${selectedFile.type || "Document"} ready to upload`
              : "PDF, DOCX, or TXT files are supported"}
          </span>
        </span>

        <span className="upload-browse-button">
          {selectedFile ? "Change file" : "Choose file"}
        </span>

        <input
          id="document-file"
          type="file"
          aria-label="Choose a PDF, DOCX, or TXT file"
          accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
          onChange={handleChange}
          disabled={status === "uploading"}
        />
      </label>

      <div className="upload-panel-footer">
        <div className="upload-status-copy" aria-live="polite">
          {status === "success" ? (
            <p className="upload-success" role="status">
              Document uploaded successfully.
            </p>
          ) : status === "error" ? (
            <p className="upload-error" role="alert">
              {error}
            </p>
          ) : selectedFile ? (
            <p>
              Review the selected file, then upload it to your workspace.
            </p>
          ) : (
            <p>No document selected yet.</p>
          )}
        </div>

        <button
          type="button"
          className="primary upload-submit"
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
      </div>
    </div>
  );
}
