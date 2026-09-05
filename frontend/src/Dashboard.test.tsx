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
const deleteDocumentMock = vi.fn();
const logoutMock = vi.fn();

vi.mock("./services/documents", () => ({
  documentsApi: {
    list: (...args: unknown[]) => listMock(...args),
    upload: (...args: unknown[]) => uploadMock(...args),
    delete: (...args: unknown[]) => deleteDocumentMock(...args),
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

function makeDocumentListResponse(
  items: DocumentItem[] = [],
  overrides: Partial<{
    total_count: number;
    page: number;
    page_size: number;
  }> = {},
) {
  return {
    items,
    total_count: overrides.total_count ?? items.length,
    page: overrides.page ?? 1,
    page_size: overrides.page_size ?? 20,
  };
}

describe("DashboardPage", () => {
  beforeEach(() => {
    listMock.mockReset();
    uploadMock.mockReset();
    deleteDocumentMock.mockReset();
    logoutMock.mockReset();
  });

  it("loads and renders the authenticated user's documents", async () => {
    listMock.mockResolvedValue(
      makeDocumentListResponse([
        makeDocument(),
        makeDocument({
          id: "doc-2",
          original_filename: "notes.txt",
          mime_type: "text/plain",
        }),
      ]),
    );

    renderDashboard();

    expect(
      screen.getByRole("heading", { name: "Documents" }),
    ).toBeInTheDocument();

    expect(
      await screen.findByText("report.pdf"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("notes.txt"),
    ).toBeInTheDocument();

    expect(listMock).toHaveBeenCalledWith("test-token", {
      search: undefined,
      page: 1,
      page_size: 20,
    });
  });

  it("provides a clear path from the dashboard to chat", async () => {
    listMock.mockResolvedValue(makeDocumentListResponse());

    renderDashboard();

    await screen.findByText(
      "No documents yet",
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

  it("offers delete with inline confirmation and supports cancel", async () => {
    listMock.mockResolvedValue(
      makeDocumentListResponse([makeDocument()]),
    );

    renderDashboard();

    await screen.findByText("report.pdf");

    fireEvent.click(
      screen.getByRole("button", { name: "Delete" }),
    );

    expect(
      screen.getByText("Delete this document?"),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Cancel" }),
    );

    expect(
      screen.queryByText("Delete this document?"),
    ).not.toBeInTheDocument();

    expect(deleteDocumentMock).not.toHaveBeenCalled();
    expect(screen.getByText("report.pdf")).toBeInTheDocument();
  });

  it("shows real document metadata in the document workspace", async () => {
    listMock.mockResolvedValue(
      makeDocumentListResponse([
        makeDocument({
          original_filename: "contract.docx",
          mime_type:
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          processing_status: "indexed",
        }),
      ]),
    );

    renderDashboard();

    await screen.findByText("contract.docx");

    expect(screen.getAllByText("DOCX").length).toBeGreaterThan(0);
    expect(screen.getByText("indexed")).toBeInTheDocument();
    expect(screen.getByText("Uploaded Aug 22, 2026")).toBeInTheDocument();
  });

  it("shows a target-only deleting state while delete is pending", async () => {
    const first = makeDocument();
    const second = makeDocument({
      id: "doc-2",
      original_filename: "notes.txt",
      mime_type: "text/plain",
    });

    listMock
      .mockResolvedValueOnce(
        makeDocumentListResponse([first, second], { total_count: 2 }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([second], { total_count: 1 }),
      );

    let resolveDelete: ((value: null) => void) | undefined;

    deleteDocumentMock.mockImplementation(
      () =>
        new Promise<null>((resolve) => {
          resolveDelete = resolve;
        }),
    );

    renderDashboard();

    await screen.findByText("report.pdf");

    fireEvent.click(
      screen.getAllByRole("button", { name: "Delete" })[0],
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Confirm delete" }),
    );

    expect(
      screen.getByRole("status", { name: "" }),
    ).toHaveTextContent("Deleting…");

    expect(
      screen.getByText("notes.txt"),
    ).toBeInTheDocument();

    listMock.mockResolvedValueOnce(
      makeDocumentListResponse([], {
        total_count: 0,
        page: 1,
        page_size: 20,
      }),
    );

    resolveDelete?.(null);

    await waitFor(() =>
      expect(screen.queryByText("report.pdf")).not.toBeInTheDocument(),
    );
  });

  it("deletes only the confirmed document", async () => {
    const first = makeDocument();
    const second = {
      ...makeDocument(),
      id: "22222222-2222-4222-8222-222222222222",
      original_filename: "second.pdf",
    };

    listMock
      .mockResolvedValueOnce(
        makeDocumentListResponse([first, second], { total_count: 2 }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([second], { total_count: 1 }),
      );
    deleteDocumentMock.mockResolvedValue(null);

    renderDashboard();

    await screen.findByText("report.pdf");
    expect(screen.getByText("second.pdf")).toBeInTheDocument();

    fireEvent.click(
      screen.getAllByRole("button", { name: "Delete" })[0],
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Confirm delete" }),
    );

    await waitFor(() =>
      expect(deleteDocumentMock).toHaveBeenCalledWith(
        "test-token",
        first.id,
      ),
    );

    await waitFor(() =>
      expect(screen.queryByText("report.pdf")).not.toBeInTheDocument(),
    );

    expect(screen.getByText("second.pdf")).toBeInTheDocument();
  });

  it("keeps the document visible and allows retry after delete failure", async () => {
    const document = makeDocument();

    listMock.mockResolvedValue(
      makeDocumentListResponse([document]),
    );
    deleteDocumentMock.mockRejectedValueOnce(new Error("Delete unavailable"));

    renderDashboard();

    await screen.findByText("report.pdf");

    fireEvent.click(
      screen.getByRole("button", { name: "Delete" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Confirm delete" }),
    );

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Unable to delete document. Please try again.",
      ),
    );

    expect(screen.getByText("report.pdf")).toBeInTheDocument();

    deleteDocumentMock.mockResolvedValueOnce(null);
    listMock.mockResolvedValueOnce(
      makeDocumentListResponse([], {
        total_count: 0,
        page: 1,
        page_size: 20,
      }),
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Delete" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Confirm delete" }),
    );

    await waitFor(() =>
      expect(screen.queryByText("report.pdf")).not.toBeInTheDocument(),
    );
  });

  it("prevents duplicate delete requests while deletion is pending", async () => {
    const document = makeDocument();

    listMock.mockResolvedValue(
      makeDocumentListResponse([document]),
    );

    let resolveDelete: ((value: null) => void) | undefined;

    deleteDocumentMock.mockImplementation(
      () =>
        new Promise<null>((resolve) => {
          resolveDelete = resolve;
        }),
    );

    renderDashboard();

    await screen.findByText("report.pdf");

    fireEvent.click(
      screen.getByRole("button", { name: "Delete" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Confirm delete" }),
    );

    expect(deleteDocumentMock).toHaveBeenCalledTimes(1);

    listMock.mockResolvedValueOnce(
      makeDocumentListResponse([], {
        total_count: 0,
        page: 1,
        page_size: 20,
      }),
    );

    resolveDelete?.(null);

    await waitFor(() =>
      expect(screen.queryByText("report.pdf")).not.toBeInTheDocument(),
    );
  });

  it("shows the post-upload Continue to Chat action", async () => {
    listMock.mockResolvedValue(makeDocumentListResponse());
    uploadMock.mockResolvedValue(makeDocument());

    renderDashboard();

    await screen.findByText(
      "No documents yet",
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

  it("loads the initial page with pagination parameters and total count", async () => {
    const document = makeDocument();

    listMock.mockResolvedValueOnce(
      makeDocumentListResponse([document], {
        total_count: 21,
        page: 1,
        page_size: 20,
      }),
    );

    renderDashboard();

    expect(
      await screen.findByText(document.original_filename),
    ).toBeInTheDocument();

    expect(listMock).toHaveBeenCalledWith("test-token", {
      search: undefined,
      page: 1,
      page_size: 20,
    });

    expect(screen.getByText("21 documents")).toBeInTheDocument();
    expect(screen.getByText("Page 1")).toBeInTheDocument();
  });

  it("does not fetch while typing and resets to page 1 on search submit", async () => {
    const initial = makeDocument({
      original_filename: "initial.pdf",
    });
    const filtered = makeDocument({
      original_filename: "report.pdf",
    });

    listMock
      .mockResolvedValueOnce(
        makeDocumentListResponse([initial], {
          total_count: 21,
          page: 1,
          page_size: 20,
        }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([filtered], {
          total_count: 1,
          page: 1,
          page_size: 20,
        }),
      );

    renderDashboard();

    await screen.findByText("initial.pdf");

    const searchInput = screen.getByRole("searchbox", {
      name: "Search documents",
    });

    fireEvent.change(searchInput, {
      target: { value: "report" },
    });

    expect(listMock).toHaveBeenCalledTimes(1);

    fireEvent.submit(
      screen.getByRole("form", {
        name: "Search documents",
      }),
    );

    await screen.findByText("report.pdf");

    expect(listMock).toHaveBeenLastCalledWith("test-token", {
      search: "report",
      page: 1,
      page_size: 20,
    });
  });

  it("loads the next page", async () => {
    const pageOne = makeDocument({
      original_filename: "page-one.pdf",
    });
    const pageTwo = makeDocument({
      original_filename: "page-two.pdf",
    });

    listMock
      .mockResolvedValueOnce(
        makeDocumentListResponse([pageOne], {
          total_count: 21,
          page: 1,
          page_size: 20,
        }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([pageTwo], {
          total_count: 21,
          page: 2,
          page_size: 20,
        }),
      );

    renderDashboard();

    await screen.findByText("page-one.pdf");

    fireEvent.click(
      screen.getByRole("button", { name: "Next page" }),
    );

    await screen.findByText("page-two.pdf");

    expect(listMock).toHaveBeenLastCalledWith("test-token", {
      search: undefined,
      page: 2,
      page_size: 20,
    });
  });

  it("returns to the previous page", async () => {
    const pageOne = makeDocument({
      original_filename: "page-one.pdf",
    });
    const pageTwo = makeDocument({
      original_filename: "page-two.pdf",
    });

    listMock
      .mockResolvedValueOnce(
        makeDocumentListResponse([pageOne], {
          total_count: 21,
          page: 1,
          page_size: 20,
        }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([pageTwo], {
          total_count: 21,
          page: 2,
          page_size: 20,
        }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([pageOne], {
          total_count: 21,
          page: 1,
          page_size: 20,
        }),
      );

    renderDashboard();

    await screen.findByText("page-one.pdf");

    fireEvent.click(
      screen.getByRole("button", { name: "Next page" }),
    );

    await screen.findByText("page-two.pdf");

    fireEvent.click(
      screen.getByRole("button", { name: "Previous page" }),
    );

    await screen.findByText("page-one.pdf");

    expect(listMock).toHaveBeenLastCalledWith("test-token", {
      search: undefined,
      page: 1,
      page_size: 20,
    });
  });

  it("disables Next on the last page", async () => {
    listMock.mockResolvedValueOnce(
      makeDocumentListResponse([makeDocument()], {
        total_count: 20,
        page: 1,
        page_size: 20,
      }),
    );

    renderDashboard();

    await screen.findByText("report.pdf");

    expect(
      screen.getByRole("button", { name: "Next page" }),
    ).toBeDisabled();
  });

  it("refetches the server-backed page after delete", async () => {
    const document = makeDocument();

    listMock
      .mockResolvedValueOnce(
        makeDocumentListResponse([document], {
          total_count: 1,
          page: 1,
          page_size: 20,
        }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([], {
          total_count: 0,
          page: 1,
          page_size: 20,
        }),
      );

    deleteDocumentMock.mockResolvedValueOnce(null);

    renderDashboard();

    await screen.findByText(document.original_filename);

    fireEvent.click(
      screen.getByRole("button", { name: "Delete" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Confirm delete" }),
    );

    await screen.findByText("No documents yet");

    expect(listMock).toHaveBeenCalledTimes(2);
    expect(listMock).toHaveBeenLastCalledWith("test-token", {
      search: undefined,
      page: 1,
      page_size: 20,
    });
  });

  it("moves back to page 1 after deleting the only item on page 2", async () => {
    const pageOne = makeDocument({
      original_filename: "page-one.pdf",
    });
    const pageTwo = makeDocument({
      original_filename: "page-two.pdf",
      id: "doc-2",
    });

    listMock
      .mockResolvedValueOnce(
        makeDocumentListResponse([pageOne], {
          total_count: 21,
          page: 1,
          page_size: 20,
        }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([pageTwo], {
          total_count: 21,
          page: 2,
          page_size: 20,
        }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([pageOne], {
          total_count: 20,
          page: 1,
          page_size: 20,
        }),
      );

    deleteDocumentMock.mockResolvedValueOnce(null);

    renderDashboard();

    await screen.findByText("page-one.pdf");

    fireEvent.click(
      screen.getByRole("button", { name: "Next page" }),
    );

    await screen.findByText("page-two.pdf");

    fireEvent.click(
      screen.getByRole("button", { name: "Delete" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Confirm delete" }),
    );

    await screen.findByText("page-one.pdf");

    expect(listMock).toHaveBeenLastCalledWith("test-token", {
      search: undefined,
      page: 1,
      page_size: 20,
    });
  });

  it("refreshes the server-backed page after upload instead of prepending locally", async () => {
    const existing = makeDocument({
      original_filename: "existing.pdf",
    });
    const uploaded = makeDocument({
      id: "uploaded-id",
      original_filename: "uploaded.pdf",
    });
    const refreshed = makeDocument({
      id: "refreshed-id",
      original_filename: "server-order.pdf",
    });

    listMock
      .mockResolvedValueOnce(
        makeDocumentListResponse([existing], {
          total_count: 1,
          page: 1,
          page_size: 20,
        }),
      )
      .mockResolvedValueOnce(
        makeDocumentListResponse([refreshed, uploaded], {
          total_count: 2,
          page: 1,
          page_size: 20,
        }),
      );

    uploadMock.mockResolvedValueOnce(uploaded);

    renderDashboard();

    await screen.findByText("existing.pdf");

    const input = screen.getByLabelText(
      "Choose a PDF, DOCX, or TXT file",
    );

    const file = new File(
      ["pdf"],
      "uploaded.pdf",
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

    await screen.findByText("server-order.pdf");

    expect(listMock).toHaveBeenCalledTimes(2);
    expect(listMock).toHaveBeenLastCalledWith("test-token", {
      search: undefined,
      page: 1,
      page_size: 20,
    });
    expect(screen.getByText("uploaded.pdf")).toBeInTheDocument();
  });

  it("logout remains functional", async () => {
    listMock.mockResolvedValue(makeDocumentListResponse());

    renderDashboard();

    await screen.findByText(
      "No documents yet",
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
