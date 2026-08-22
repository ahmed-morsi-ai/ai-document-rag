import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { DashboardPage } from "./pages/DashboardPage";
import { DocumentUpload } from "./components/DocumentUpload";
import type { DocumentItem } from "./types/documents";

const listMock = vi.fn();
const uploadMock = vi.fn();
const logoutMock = vi.fn();

vi.mock("./services/documents", () => ({
  documentsApi: {
    list: (...args: unknown[]) => listMock(...args),
    upload: (...args: unknown[]) => uploadMock(...args),
  },
}));

vi.mock("./auth/AuthContext", () => ({
  useAuth: () => ({
    user: {
      id: "user-1",
      email: "ahmed@example.com",
      is_active: true,
    },
    token: "test-token",
    logout: logoutMock,
  }),
}));

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  );
}

function makeDocument(
  overrides: Partial<DocumentItem> = {},
): DocumentItem {
  return {
    id: "doc-1",
    original_filename: "report.pdf",
    mime_type: "application/pdf",
    processing_status: "uploaded",
    created_at: "2026-08-22T20:00:00Z",
    updated_at: "2026-08-22T20:00:00Z",
    ...overrides,
  };
}

describe("DashboardPage", () => {
  beforeEach(() => {
    listMock.mockReset();
    uploadMock.mockReset();
    logoutMock.mockReset();
  });

  it("loads and renders the authenticated user's documents", async () => {
    listMock.mockResolvedValue([
      makeDocument(),
      makeDocument({
        id: "doc-2",
        original_filename: "notes.txt",
        mime_type: "text/plain",
      }),
    ]);

    renderDashboard();

    expect(
      screen.getByRole("heading", { name: "Dashboard" }),
    ).toBeInTheDocument();

    expect(
      await screen.findByText("report.pdf"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("notes.txt"),
    ).toBeInTheDocument();

    expect(listMock).toHaveBeenCalledWith("test-token");
  });

  it("provides a clear path from the dashboard to chat", async () => {
    listMock.mockResolvedValue([]);

    renderDashboard();

    await screen.findByText(
      "No documents uploaded yet. Use the upload area above to add your first document.",
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Open Chat" }),
    );

    expect(
      screen.getByRole("button", { name: "Open Chat" }),
    ).toBeInTheDocument();
  });

  it("shows a user-facing list error", async () => {
    listMock.mockRejectedValue(
      new Error("server unavailable"),
    );

    renderDashboard();

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent(
      "Unable to load documents.",
    );
  });

  it("shows the post-upload Continue to Chat action", async () => {
    listMock.mockResolvedValue([]);
    uploadMock.mockResolvedValue(makeDocument());

    renderDashboard();

    await screen.findByText(
      "No documents uploaded yet. Use the upload area above to add your first document.",
    );

    const input = screen.getByLabelText(
      "Choose a PDF, DOCX, or TXT file",
    );

    const file = new File(
      ["pdf"],
      "report.pdf",
      { type: "application/pdf" },
    );

    fireEvent.change(input, {
      target: { files: [file] },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Upload document",
      }),
    );

    await screen.findByRole("status");

    expect(
      screen.getByRole("button", {
        name: "Continue to Chat",
      }),
    ).toBeInTheDocument();
  });

  it("logout remains functional", async () => {
    listMock.mockResolvedValue([]);

    renderDashboard();

    await screen.findByText(
      "No documents uploaded yet. Use the upload area above to add your first document.",
    );

    fireEvent.click(
      screen.getByRole("button", {
        name: "Log out",
      }),
    );

    await waitFor(() => {
      expect(logoutMock).toHaveBeenCalledTimes(1);
    });
  });
});

describe("DocumentUpload", () => {
  beforeEach(() => {
    uploadMock.mockReset();
  });

  it("renders the upload area and accepts a PDF", () => {
    const onUploaded = vi.fn();

    render(
      <DocumentUpload
        token="test-token"
        onUploaded={onUploaded}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: "Upload document",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByLabelText(
        "Choose a PDF, DOCX, or TXT file",
      ),
    ).toBeInTheDocument();
  });

  it("rejects an unsupported file client-side", () => {
    const onUploaded = vi.fn();

    render(
      <DocumentUpload
        token="test-token"
        onUploaded={onUploaded}
      />,
    );

    const input = screen.getByLabelText(
      "Choose a PDF, DOCX, or TXT file",
    );

    const file = new File(
      ["malicious"],
      "malware.exe",
      {
        type: "application/octet-stream",
      },
    );

    fireEvent.change(input, {
      target: {
        files: [file],
      },
    });

    expect(
      screen.getByRole("alert"),
    ).toHaveTextContent(
      "Unsupported file type. Please choose a PDF, DOCX, or TXT file.",
    );

    expect(
      screen.getByRole("button", {
        name: "Upload document",
      }),
    ).toBeDisabled();

    expect(uploadMock).not.toHaveBeenCalled();
  });

  it("upload success exposes a clear next step to Chat", async () => {
    const uploaded = makeDocument();
    const onUploaded = vi.fn();

    uploadMock.mockResolvedValue(uploaded);

    render(
      <DocumentUpload
        token="test-token"
        onUploaded={onUploaded}
      />,
    );

    const input = screen.getByLabelText(
      "Choose a PDF, DOCX, or TXT file",
    );

    const file = new File(
      ["pdf"],
      "report.pdf",
      { type: "application/pdf" },
    );

    fireEvent.change(input, {
      target: { files: [file] },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Upload document",
      }),
    );

    expect(
      await screen.findByRole("status"),
    ).toHaveTextContent(
      "Document uploaded successfully.",
    );

    expect(onUploaded).toHaveBeenCalledWith(uploaded);
  });

  it("uploads a supported file and shows success", async () => {
    const uploaded = makeDocument();
    const onUploaded = vi.fn();

    uploadMock.mockResolvedValue(uploaded);

    render(
      <DocumentUpload
        token="test-token"
        onUploaded={onUploaded}
      />,
    );

    const input = screen.getByLabelText(
      "Choose a PDF, DOCX, or TXT file",
    );

    const file = new File(
      ["pdf"],
      "report.pdf",
      {
        type: "application/pdf",
      },
    );

    fireEvent.change(input, {
      target: {
        files: [file],
      },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Upload document",
      }),
    );

    expect(
      await screen.findByRole("status"),
    ).toHaveTextContent(
      "Document uploaded successfully.",
    );

    expect(uploadMock).toHaveBeenCalledTimes(1);
    expect(uploadMock).toHaveBeenCalledWith(
      "test-token",
      file,
    );
    expect(onUploaded).toHaveBeenCalledWith(
      uploaded,
    );
  });

  it("shows upload loading state and prevents duplicate submission", async () => {
    let resolveUpload:
      | ((value: DocumentItem) => void)
      | undefined;

    uploadMock.mockImplementation(
      () =>
        new Promise<DocumentItem>((resolve) => {
          resolveUpload = resolve;
        }),
    );

    render(
      <DocumentUpload
        token="test-token"
        onUploaded={vi.fn()}
      />,
    );

    const input = screen.getByLabelText(
      "Choose a PDF, DOCX, or TXT file",
    );

    const file = new File(
      ["pdf"],
      "report.pdf",
      {
        type: "application/pdf",
      },
    );

    fireEvent.change(input, {
      target: {
        files: [file],
      },
    });

    const button = screen.getByRole("button", {
      name: "Upload document",
    });

    fireEvent.click(button);

    expect(
      screen.getByRole("button", {
        name: "Uploading…",
      }),
    ).toBeDisabled();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Uploading…",
      }),
    );

    expect(uploadMock).toHaveBeenCalledTimes(1);

    resolveUpload?.(makeDocument());

    await waitFor(() => {
      expect(
        screen.getByRole("status"),
      ).toHaveTextContent(
        "Document uploaded successfully.",
      );
    });
  });

  it("shows backend validation errors", async () => {
    const onUploaded = vi.fn();

    uploadMock.mockRejectedValue(
      new Error("Unsupported document type"),
    );

    render(
      <DocumentUpload
        token="test-token"
        onUploaded={onUploaded}
      />,
    );

    const input = screen.getByLabelText(
      "Choose a PDF, DOCX, or TXT file",
    );

    const file = new File(
      ["txt"],
      "report.txt",
      {
        type: "text/plain",
      },
    );

    fireEvent.change(input, {
      target: {
        files: [file],
      },
    });

    fireEvent.click(
      screen.getByRole("button", {
        name: "Upload document",
      }),
    );

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent(
      "Upload failed. Please try again.",
    );
  });
});
